"""
WebSocket endpoints for real-time agent streaming.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from typing import Dict, Any, Optional
import json
import asyncio
from datetime import datetime
from uuid import UUID, uuid4

from services.agent_client import StratOSAgentClient
from config.settings import get_settings

router = APIRouter()
settings = get_settings()


class ConnectionManager:
    """Manages WebSocket connections."""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str):
        """Accept and store a new connection."""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        
    def disconnect(self, client_id: str):
        """Remove a connection."""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
    
    async def send_json(self, client_id: str, data: Dict[str, Any]):
        """Send JSON data to a specific client."""
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_json(data)
    
    async def broadcast(self, data: Dict[str, Any], exclude: Optional[str] = None):
        """Broadcast to all connected clients."""
        for client_id, connection in self.active_connections.items():
            if client_id != exclude:
                await connection.send_json(data)


# Global connection manager
manager = ConnectionManager()


@router.websocket("/agent-stream")
async def agent_stream_endpoint(
    websocket: WebSocket,
    token: Optional[str] = Query(None)
):
    """
    WebSocket endpoint for streaming agent responses.
    
    Message format:
    {
        "type": "request|response|status|error",
        "data": {...},
        "metadata": {...}
    }
    """
    client_id = str(uuid4())
    
    # TODO: Validate token and get user context
    # For now, we'll skip authentication in development
    
    await manager.connect(websocket, client_id)
    
    try:
        # Send connection confirmation
        await manager.send_json(client_id, {
            "type": "connection",
            "data": {
                "client_id": client_id,
                "status": "connected"
            },
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Start heartbeat task
        heartbeat_task = asyncio.create_task(
            send_heartbeat(client_id)
        )
        
        # Handle incoming messages
        while True:
            # Receive message
            data = await websocket.receive_json()
            
            if data.get("type") == "ping":
                # Respond to ping
                await manager.send_json(client_id, {
                    "type": "pong",
                    "timestamp": datetime.utcnow().isoformat()
                })
                
            elif data.get("type") == "agent_request":
                # Stream agent response
                await handle_agent_request(
                    client_id,
                    data.get("data", {}),
                    data.get("request_id")
                )
                
            else:
                # Unknown message type
                await manager.send_json(client_id, {
                    "type": "error",
                    "data": {
                        "message": f"Unknown message type: {data.get('type')}"
                    }
                })
                
    except WebSocketDisconnect:
        manager.disconnect(client_id)
        heartbeat_task.cancel()
        
    except Exception as e:
        # Send error before disconnecting
        try:
            await manager.send_json(client_id, {
                "type": "error",
                "data": {
                    "message": f"WebSocket error: {str(e)}"
                }
            })
        except:
            pass
        
        manager.disconnect(client_id)
        if 'heartbeat_task' in locals():
            heartbeat_task.cancel()


async def send_heartbeat(client_id: str):
    """Send periodic heartbeat to keep connection alive."""
    try:
        while True:
            await asyncio.sleep(settings.ws_heartbeat_interval)
            await manager.send_json(client_id, {
                "type": "heartbeat",
                "timestamp": datetime.utcnow().isoformat()
            })
    except asyncio.CancelledError:
        pass


async def handle_agent_request(
    client_id: str,
    request_data: Dict[str, Any],
    request_id: Optional[str] = None
):
    """
    Handle agent request and stream response.
    
    Simulates streaming by sending multiple status updates
    and partial responses.
    """
    request_id = request_id or str(uuid4())
    
    try:
        # Send processing status
        await manager.send_json(client_id, {
            "type": "status",
            "request_id": request_id,
            "data": {
                "status": "processing",
                "message": "Routing to agent system..."
            }
        })
        
        # TODO: Implement actual agent invocation with streaming
        # For now, simulate streaming response
        
        # Simulate agent thinking
        await asyncio.sleep(0.5)
        await manager.send_json(client_id, {
            "type": "status",
            "request_id": request_id,
            "data": {
                "status": "agent_thinking",
                "agent": "StrategicContextRouter",
                "message": "Analyzing request..."
            }
        })
        
        # Simulate tool usage
        await asyncio.sleep(0.8)
        await manager.send_json(client_id, {
            "type": "tool_call",
            "request_id": request_id,
            "data": {
                "tool": "route_to_agent",
                "agent": "CEOLogAgent",
                "status": "calling"
            }
        })
        
        # Simulate partial response streaming
        response_text = "Based on your CEO log entry, I've identified several key strategic themes..."
        words = response_text.split()
        
        for i, word in enumerate(words):
            await manager.send_json(client_id, {
                "type": "partial_response",
                "request_id": request_id,
                "data": {
                    "content": word + " ",
                    "position": i
                }
            })
            await asyncio.sleep(0.1)  # Simulate typing delay
        
        # Send final response
        await manager.send_json(client_id, {
            "type": "response",
            "request_id": request_id,
            "data": {
                "content": response_text,
                "agent": "CEOLogAgent",
                "metadata": {
                    "tokens_used": 150,
                    "duration_ms": 2500,
                    "model": "gpt-4"
                }
            }
        })
        
    except Exception as e:
        await manager.send_json(client_id, {
            "type": "error",
            "request_id": request_id,
            "data": {
                "message": f"Agent request failed: {str(e)}"
            }
        })