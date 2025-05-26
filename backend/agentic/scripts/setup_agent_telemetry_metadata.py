#!/usr/bin/env python3
"""
Setup telemetry metadata for Azure AI Agent Service agents.
Since we can't modify the agent instructions directly through OpenAI API,
we'll document the telemetry setup and prepare integration for FastAPI.
"""

import os
import json
from datetime import datetime


def create_telemetry_config():
    """Create telemetry configuration for agents."""
    
    config = {
        "telemetry": {
            "enabled": True,
            "provider": "Azure Application Insights",
            "connection_string": os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING", ""),
            "instrumentation_key": "189923ab-6ad8-408f-b3f6-7ae4817a3988",
            "app_insights_name": "stratos-multi-agent-appinsights",
            "resource_group": "semantic-kernel-multi-agent-rg",
            "configuration_date": datetime.now().isoformat()
        },
        "agent_service_names": {
            "MainOrchestrator": "stratos.orchestrator.main",
            "StrategicContextRouter": "stratos.strategic.router",
            "CEOLogAgent": "stratos.strategic.ceo_log",
            "NorthStarAgent": "stratos.strategic.northstar",
            "MemoryRecallAgent": "stratos.strategic.memory",
            "PreferenceLearningAgent": "stratos.strategic.preference",
            "AnalysisOrchestrator": "stratos.analysis.orchestrator",
            "SWOTTOWSAgent": "stratos.analysis.swot",
            "RiskOpportunityAgent": "stratos.analysis.risk",
            "SOLinkageAgent": "stratos.analysis.linkage",
            "PlanningCoordinator": "stratos.planning.coordinator",
            "InitiativeGenerationAgent": "stratos.planning.initiative",
            "ResourceOptimizationAgent": "stratos.planning.resource",
            "CanvasVisualizationAgent": "stratos.planning.canvas",
            "AlignmentScoringAgent": "stratos.planning.alignment",
            "ActionPlanningAgent": "stratos.planning.action"
        },
        "trace_operations": {
            "orchestrator": [
                "process_request",
                "route_decision", 
                "invoke_specialist",
                "aggregate_response"
            ],
            "ceo_log": [
                "record_entry",
                "retrieve_entries",
                "analyze_sentiment",
                "categorize_entry"
            ],
            "strategic_planning": [
                "create_plan",
                "update_plan",
                "evaluate_progress",
                "generate_initiatives"
            ],
            "analysis": [
                "perform_swot",
                "identify_risks",
                "find_opportunities",
                "link_subjective_objective"
            ]
        },
        "integration_points": {
            "fastapi_middleware": "backend/agentic/api/middleware/telemetry.py",
            "agent_client": "backend/agentic/services/agent_client.py",
            "telemetry_module": "backend/agentic/core/telemetry.py"
        }
    }
    
    # Save configuration
    config_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "deployment_configs",
        "telemetry_configuration.json"
    )
    
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    print("📊 Telemetry Configuration Created")
    print("=" * 60)
    print(f"✅ Configuration saved to: {config_path}")
    print(f"📍 Application Insights: {config['telemetry']['app_insights_name']}")
    print(f"🔑 Instrumentation Key: {config['telemetry']['instrumentation_key']}")
    print()
    print("📝 Integration Steps:")
    print("1. FastAPI middleware will instrument all API calls")
    print("2. Agent client will add telemetry spans for agent invocations")
    print("3. Each agent operation will be traced with service name")
    print()
    print("🔍 View traces in Azure Portal:")
    print(f"   https://portal.azure.com > Application Insights > {config['telemetry']['app_insights_name']}")
    
    return config


def create_fastapi_telemetry_middleware():
    """Create FastAPI telemetry middleware."""
    
    middleware_code = '''"""
FastAPI telemetry middleware for StratOS agents.
Automatically instruments all API requests and agent invocations.
"""

from fastapi import Request
import time
from typing import Callable
import json
import os
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from core.telemetry import initialize_telemetry, create_span_context, add_span_attributes


class TelemetryMiddleware:
    """Middleware to add telemetry to all FastAPI requests."""
    
    def __init__(self, app):
        self.app = app
        
        # Initialize telemetry
        self.tracer = initialize_telemetry(
            service_name="StratOS.FastAPI",
            service_version="1.0.0"
        )
    
    async def __call__(self, request: Request, call_next: Callable):
        # Skip telemetry for health checks
        if request.url.path in ["/health", "/", "/docs", "/openapi.json"]:
            return await call_next(request)
        
        # Create span for the request
        span_name = f"http.{request.method} {request.url.path}"
        
        with create_span_context(span_name, {
            "http.method": request.method,
            "http.url": str(request.url),
            "http.path": request.url.path,
            "http.host": request.url.hostname,
            "user_agent": request.headers.get("user-agent", "unknown")
        }) as span:
            
            start_time = time.time()
            
            try:
                # Process request
                response = await call_next(request)
                
                # Add response attributes
                duration = time.time() - start_time
                add_span_attributes(span, {
                    "http.status_code": response.status_code,
                    "http.duration_ms": round(duration * 1000, 2),
                    "response.success": response.status_code < 400
                })
                
                return response
                
            except Exception as e:
                # Record exception
                duration = time.time() - start_time
                add_span_attributes(span, {
                    "http.status_code": 500,
                    "http.duration_ms": round(duration * 1000, 2),
                    "error": str(e),
                    "error.type": type(e).__name__
                })
                raise


def setup_telemetry_middleware(app):
    """Setup telemetry middleware on FastAPI app."""
    app.add_middleware(TelemetryMiddleware)
'''
    
    # Save middleware
    middleware_dir = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "api",
        "middleware"
    )
    os.makedirs(middleware_dir, exist_ok=True)
    
    middleware_path = os.path.join(middleware_dir, "telemetry.py")
    
    with open(middleware_path, 'w') as f:
        f.write(middleware_code)
    
    print(f"\n✅ FastAPI telemetry middleware created: {middleware_path}")
    
    return middleware_path


def update_agent_client_telemetry():
    """Create telemetry-enabled agent client."""
    
    client_code = '''"""
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
'''
    
    # Save enhanced client
    client_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "services",
        "telemetry_agent_client.py"
    )
    
    with open(client_path, 'w') as f:
        f.write(client_code)
    
    print(f"✅ Telemetry-enabled agent client created: {client_path}")
    
    return client_path


def main():
    """Main setup function."""
    print("🚀 Setting up Telemetry for Azure AI Agent Service")
    print("=" * 60)
    
    # Create telemetry configuration
    config = create_telemetry_config()
    
    # Create FastAPI middleware
    middleware_path = create_fastapi_telemetry_middleware()
    
    # Create enhanced agent client
    client_path = update_agent_client_telemetry()
    
    print("\n✅ Telemetry setup complete!")
    print("\n📋 Next Steps:")
    print("1. Update FastAPI main.py to use telemetry middleware:")
    print("   from api.middleware.telemetry import setup_telemetry_middleware")
    print("   setup_telemetry_middleware(app)")
    print()
    print("2. Use TelemetryAgentClient instead of AgentClient:")
    print("   from services.telemetry_agent_client import TelemetryAgentClient")
    print()
    print("3. Deploy updated FastAPI application")
    print()
    print("4. Run test script to generate traces:")
    print("   python scripts/test_telemetry_integration.py")


if __name__ == "__main__":
    main()