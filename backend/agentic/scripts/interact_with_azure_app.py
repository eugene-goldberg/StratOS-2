#!/usr/bin/env python3
"""
Script to interact with the deployed StratOS FastAPI app on Azure Container Apps.
Provides various commands to test endpoints and agent functionality.
"""

import json
import sys
import argparse
import requests
from typing import Optional, Dict, Any
from pathlib import Path
import asyncio
import websockets
from datetime import datetime


class StratOSAzureClient:
    """Client for interacting with deployed StratOS API."""
    
    def __init__(self, base_url: Optional[str] = None):
        """Initialize client with base URL from deployment info or argument."""
        if base_url:
            self.base_url = base_url.rstrip('/')
        else:
            # Try to load from deployment info
            deployment_file = Path(__file__).parent.parent / "deployment_info_azure.json"
            if deployment_file.exists():
                with open(deployment_file) as f:
                    deployment_info = json.load(f)
                    self.base_url = deployment_info["app_url"].rstrip('/')
            else:
                raise ValueError("No base URL provided and deployment_info_azure.json not found")
        
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
    
    def health_check(self) -> Dict[str, Any]:
        """Check API health status."""
        response = self.session.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()
    
    def get_agents(self) -> Dict[str, Any]:
        """Get list of available agents."""
        response = self.session.get(f"{self.base_url}/api/v1/agents")
        response.raise_for_status()
        return response.json()
    
    def invoke_agent(self, agent_type: str, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Invoke a specific agent."""
        payload = {
            "agent_type": agent_type,
            "request": request_data
        }
        response = self.session.post(
            f"{self.base_url}/api/v1/agents/invoke",
            json=payload
        )
        response.raise_for_status()
        return response.json()
    
    def create_ceo_log_entry(self, content: str, category: str = "general") -> Dict[str, Any]:
        """Create a CEO log entry."""
        request_data = {
            "action": "create_entry",
            "data": {
                "text": content,
                "category": category,
                "is_voice": False
            }
        }
        return self.invoke_agent("ceo_log", request_data)
    
    def set_north_star_purpose(self, purpose: str) -> Dict[str, Any]:
        """Set organizational purpose."""
        request_data = {
            "element": "purpose",
            "action": "set",
            "data": {
                "content": purpose
            }
        }
        return self.invoke_agent("north_star", request_data)
    
    def get_north_star_summary(self) -> Dict[str, Any]:
        """Get North Star summary."""
        request_data = {
            "element": "summary",
            "action": "get"
        }
        return self.invoke_agent("north_star", request_data)
    
    async def test_websocket(self, message: str):
        """Test WebSocket connection for streaming."""
        ws_url = self.base_url.replace("https://", "wss://").replace("http://", "ws://")
        ws_url = f"{ws_url}/ws"
        
        async with websockets.connect(ws_url) as websocket:
            # Send a message
            await websocket.send(json.dumps({
                "type": "chat",
                "content": message
            }))
            
            # Receive responses
            print(f"Sent: {message}")
            print("Receiving responses...")
            
            async for response in websocket:
                data = json.loads(response)
                print(f"Received: {data}")
                
                # Break on completion
                if data.get("type") == "complete":
                    break


def main():
    """Main CLI interface."""
    parser = argparse.ArgumentParser(description="Interact with deployed StratOS API")
    parser.add_argument("--url", help="Base URL of the API (if not using deployment info)")
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Health check command
    subparsers.add_parser("health", help="Check API health")
    
    # List agents command
    subparsers.add_parser("agents", help="List available agents")
    
    # CEO log command
    ceo_log_parser = subparsers.add_parser("ceo-log", help="Create CEO log entry")
    ceo_log_parser.add_argument("content", help="Log entry content")
    ceo_log_parser.add_argument("--category", default="general", help="Entry category")
    
    # North Star commands
    purpose_parser = subparsers.add_parser("set-purpose", help="Set organizational purpose")
    purpose_parser.add_argument("purpose", help="Purpose statement")
    
    subparsers.add_parser("north-star", help="Get North Star summary")
    
    # WebSocket test
    ws_parser = subparsers.add_parser("websocket", help="Test WebSocket connection")
    ws_parser.add_argument("message", help="Message to send")
    
    # Generic agent invoke
    invoke_parser = subparsers.add_parser("invoke", help="Invoke agent with custom request")
    invoke_parser.add_argument("agent", help="Agent type")
    invoke_parser.add_argument("request", help="Request JSON")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        client = StratOSAzureClient(args.url)
        
        if args.command == "health":
            result = client.health_check()
            print(json.dumps(result, indent=2))
        
        elif args.command == "agents":
            result = client.get_agents()
            print(json.dumps(result, indent=2))
        
        elif args.command == "ceo-log":
            result = client.create_ceo_log_entry(args.content, args.category)
            print(json.dumps(result, indent=2))
        
        elif args.command == "set-purpose":
            result = client.set_north_star_purpose(args.purpose)
            print(json.dumps(result, indent=2))
        
        elif args.command == "north-star":
            result = client.get_north_star_summary()
            print(json.dumps(result, indent=2))
        
        elif args.command == "websocket":
            asyncio.run(client.test_websocket(args.message))
        
        elif args.command == "invoke":
            request_data = json.loads(args.request)
            result = client.invoke_agent(args.agent, request_data)
            print(json.dumps(result, indent=2))
    
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()