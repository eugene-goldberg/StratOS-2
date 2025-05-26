"""
Enhanced agent client with telemetry support.
"""

import os
import sys
from typing import Dict, Any, Optional, List
import json

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from core.telemetry import create_span_context, add_span_attributes, SpanNames
from services.agent_client import AgentClient as BaseAgentClient


class TelemetryAgentClient(BaseAgentClient):
    """Agent client with integrated telemetry."""
    
    def __init__(self):
        super().__init__()
        
        # Load telemetry configuration
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "deployment_configs",
            "telemetry_configuration.json"
        )
        
        with open(config_path, 'r') as f:
            self.telemetry_config = json.load(f)
    
    async def invoke_agent(
        self,
        agent_id: str,
        agent_name: str,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Invoke an agent with telemetry tracking."""
        
        # Get service name for this agent
        service_name = self.telemetry_config['agent_service_names'].get(
            agent_name, 
            f"stratos.agent.{agent_name.lower()}"
        )
        
        # Create telemetry span
        with create_span_context(f"agent.invoke.{agent_name}", {
            "agent.id": agent_id,
            "agent.name": agent_name,
            "agent.service_name": service_name,
            "message.length": len(message),
            "has_context": bool(context)
        }) as span:
            
            try:
                # Call the base implementation
                result = await super().invoke_agent(
                    agent_id, agent_name, message, context
                )
                
                # Add result attributes
                add_span_attributes(span, {
                    "response.length": len(result) if result else 0,
                    "response.success": True
                })
                
                return result
                
            except Exception as e:
                # Record exception
                add_span_attributes(span, {
                    "error": str(e),
                    "error.type": type(e).__name__,
                    "response.success": False
                })
                raise
    
    async def invoke_orchestrator(
        self,
        message: str,
        user_id: Optional[str] = None
    ) -> str:
        """Invoke the main orchestrator with telemetry."""
        
        with create_span_context(SpanNames.ORCHESTRATOR_PROCESS_REQUEST, {
            "user.id": user_id or "anonymous",
            "message.length": len(message),
            "orchestrator.type": "main"
        }) as span:
            
            try:
                # Call orchestrator
                result = await super().invoke_orchestrator(message, user_id)
                
                # Add result attributes
                add_span_attributes(span, {
                    "response.length": len(result) if result else 0,
                    "response.success": True
                })
                
                return result
                
            except Exception as e:
                # Record exception
                add_span_attributes(span, {
                    "error": str(e),
                    "error.type": type(e).__name__,
                    "response.success": False
                })
                raise
