#!/usr/bin/env python3
"""
Deploy North Star Agent with OpenAPI tool - Final implementation
Following the exact structure from COMPLETE_IMPLEMENTATION_GUIDE.md
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Add parent directories to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient

# Load environment variables
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)


def deploy_agent():
    """Deploy North Star agent with OpenAPI specification for server-side execution."""
    
    print("=" * 70)
    print("NORTH STAR AGENT DEPLOYMENT - SERVER-SIDE HTTP EXECUTION")
    print("=" * 70)
    
    # Configuration
    agent_name = f"NorthStarAgent-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    model_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-35-turbo")
    connection_string = os.getenv("AZURE_AI_PROJECT_CONNECTION_STRING")
    
    # Agent instructions
    agent_instructions = """You are the North Star Agent for StratOS, responsible for defining and maintaining the organization's strategic foundation.

When users request North Star operations:
1. Use the executeNorthStarOperation tool to perform the requested action
2. The Azure AI Service will make HTTP calls directly to the Azure Function
3. No client intervention is required

For managePurpose: use operation="managePurpose" with action="get" or "set"
For manageVision: use operation="manageVision" with action="get" or "set"  
For manageValues: use operation="manageValues" with action="list", "add", or "remove"
For manageStrategicGoals: use operation="manageStrategicGoals" with appropriate action
For validateAlignment: use operation="validateAlignment" with elementType and elementContent
For getNorthStarSummary: use operation="getNorthStarSummary"

Always include organizationId in your requests."""
    
    # Load OpenAPI specification
    openapi_file = Path(__file__).parent / "north_star_openapi.json"
    with open(openapi_file, "r") as f:
        openapi_spec = json.load(f)
    
    # Define OpenAPI tool with authentication - EXACT structure from guide
    tools = [
        {
            "type": "openapi",
            "openapi": {
                "name": "north_star_api",
                "spec": openapi_spec,
                "auth": {
                    "type": "api_key",
                    "security_scheme": {
                        "connection_id": "NorthStarFunctionConnection"
                    }
                }
            }
        }
    ]
    
    try:
        # Initialize client
        credential = DefaultAzureCredential()
        client = AIProjectClient(
            endpoint=connection_string,
            credential=credential
        )
        
        print(f"\nCreating agent: {agent_name}")
        print(f"Model: {model_name}")
        print(f"Tools: OpenAPI specification (server-side execution)")
        print(f"Connection: NorthStarFunctionConnection")
        
        # Create the agent
        agent = client.agents.create_agent(
            model=model_name,
            name=agent_name,
            instructions=agent_instructions,
            tools=tools
        )
        
        print(f"\n✅ North Star Agent deployed successfully!")
        print(f"Agent ID: {agent.id}")
        print(f"Agent Name: {agent_name}")
        
        # Save deployment info
        deployment_info = {
            "agent_id": agent.id,
            "agent_name": agent_name,
            "deployed_at": datetime.now().isoformat(),
            "model": model_name,
            "server_side_execution": True,
            "tool_type": "openapi",
            "auth_type": "api_key",
            "connection": "NorthStarFunctionConnection",
            "function_app": "stratos-north-star-v2",
            "function_endpoint": "https://stratos-north-star-v2.azurewebsites.net/api/north-star-operations"
        }
        
        deployment_file = Path(__file__).parent / f"north_star_deployment_{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
        with open(deployment_file, "w") as f:
            json.dump(deployment_info, f, indent=2)
        
        print(f"\nDeployment info saved to: {deployment_file}")
        
        # Update main deployment info
        main_deployment_file = Path(__file__).parent.parent.parent / "stratos_deployment_info.json"
        try:
            with open(main_deployment_file, 'r') as f:
                existing_info = json.load(f)
        except:
            existing_info = {}
        
        existing_info["north_star_agent_openapi"] = deployment_info
        
        with open(main_deployment_file, 'w') as f:
            json.dump(existing_info, f, indent=2)
        
        print("\n" + "=" * 70)
        print("IMPORTANT: Server-side Execution Enabled")
        print("=" * 70)
        print("✓ Agent uses OpenAPI tools exclusively")
        print("✓ Azure AI Service makes HTTP calls directly")
        print("✓ No client-side function execution required")
        print("✓ Use create_and_process() for autonomous operation")
        
        return agent.id
        
    except Exception as e:
        print(f"\n❌ Deployment failed: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    agent_id = deploy_agent()
    if agent_id:
        print(f"\n🎉 North Star Agent with OpenAPI tools deployed: {agent_id}")
        print("\n📝 Next step: Run test_north_star_server_side.py to verify autonomous execution")