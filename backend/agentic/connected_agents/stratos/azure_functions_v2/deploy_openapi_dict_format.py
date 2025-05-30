#!/usr/bin/env python3
"""
Deploy North Star Agent with OpenAPI tool using dictionary format
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
    """Deploy North Star agent with OpenAPI tool using dict format."""
    
    print("=" * 70)
    print("NORTH STAR AGENT DEPLOYMENT - DICT FORMAT")
    print("=" * 70)
    
    # Configuration
    agent_name = f"NorthStarAgentOpenAPI-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    model_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-35-turbo")
    connection_string = os.getenv("AZURE_AI_PROJECT_CONNECTION_STRING")
    
    # Agent instructions
    agent_instructions = """You are the North Star Agent for StratOS, responsible for defining and maintaining the organization's strategic foundation.

When users request North Star operations, use the executeNorthStarOperation function. The Azure AI Service will execute these calls directly without client intervention.

Available operations:
- managePurpose: Get/set organizational purpose
- manageVision: Get/set organizational vision  
- manageValues: Add/remove/list organizational values
- manageStrategicGoals: Create/update/delete/list strategic goals
- validateAlignment: Check alignment with North Star
- getNorthStarSummary: Get complete North Star overview

Always include the organizationId parameter in your calls."""
    
    # Load OpenAPI specification
    openapi_file = Path(__file__).parent / "north_star_openapi.json"
    with open(openapi_file, "r") as f:
        openapi_spec = json.load(f)
    
    # Create tools as dictionary (not OpenApiTool object)
    tools = [{
        "type": "openapi",
        "openapi": {
            "name": "north_star_api",
            "spec": openapi_spec,
            "description": "North Star operations API for managing strategic foundation elements",
            "auth": {
                "type": "connection",
                "connection": {
                    "id": "NorthStarFunctionConnection"
                }
            }
        }
    }]
    
    try:
        # Initialize client
        credential = DefaultAzureCredential()
        client = AIProjectClient(
            endpoint=connection_string,
            credential=credential
        )
        
        print(f"\nCreating agent: {agent_name}")
        print(f"Model: {model_name}")
        print(f"Connection: NorthStarFunctionConnection")
        print(f"Auth type: connection")
        
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
        
        # Test retrieve to verify tools
        retrieved = client.agents.get_agent(agent.id)
        print(f"\nVerifying tools configuration:")
        print(f"Tools: {json.dumps(retrieved.tools, indent=2)}")
        
        # Save deployment info
        deployment_info = {
            "agent_id": agent.id,
            "agent_name": agent_name,
            "deployed_at": datetime.now().isoformat(),
            "model": model_name,
            "server_side_execution": True,
            "tool_type": "openapi",
            "auth_type": "connection",
            "connection": "NorthStarFunctionConnection",
            "function_app": "stratos-north-star-v2",
            "function_endpoint": "https://stratos-north-star-v2.azurewebsites.net/api/north-star-operations"
        }
        
        deployment_file = Path(__file__).parent / f"north_star_openapi_deployment_{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
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
        
        existing_info["north_star_agent_openapi"] = {
            "agent_id": agent.id,
            "agent_name": agent_name,
            "deployed_at": datetime.now().isoformat(),
            "server_side_execution": True
        }
        
        with open(main_deployment_file, 'w') as f:
            json.dump(existing_info, f, indent=2)
        
        print("\n" + "=" * 70)
        print("🎉 SERVER-SIDE EXECUTION ENABLED")
        print("=" * 70)
        print("✓ Agent uses OpenAPI tools with connection authentication")
        print("✓ Azure AI Service makes HTTP calls directly") 
        print("✓ NO client-side function execution required")
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
        print(f"\n🚀 Ready to test with test_north_star_server_side.py")