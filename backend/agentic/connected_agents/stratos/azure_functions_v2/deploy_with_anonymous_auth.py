#!/usr/bin/env python3
"""
Deploy North Star Agent with anonymous auth and API key in header.
Based on the reference example provided.
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
from azure.ai.agents.models import OpenApiTool, OpenApiAnonymousAuthDetails

# Load environment variables
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)


def deploy_with_anonymous_auth():
    """Deploy agent with anonymous auth following the reference example."""
    
    print("=" * 70)
    print("DEPLOYING WITH ANONYMOUS AUTH (REFERENCE APPROACH)")
    print("=" * 70)
    
    # Configuration
    agent_name = f"NorthStarAnonymousAuth-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    model_name = "gpt-35-turbo"
    connection_string = os.getenv("AZURE_AI_PROJECT_CONNECTION_STRING")
    
    # Agent instructions
    agent_instructions = """You are the North Star Agent for StratOS. Use the API to manage strategic foundation elements.

The API key is included in the OpenAPI spec as a default header value. When you call the API, it will automatically include the authentication.

Available operations:
- managePurpose: Get/set organizational purpose (action: get/set)
- manageVision: Get/set organizational vision (action: get/set)
- manageValues: Manage values (action: list/add/remove)
- manageStrategicGoals: Manage goals (action: create/update/delete/get/list)
- validateAlignment: Check alignment (requires elementType and elementContent)
- getNorthStarSummary: Get complete overview

Always include organizationId in your requests."""
    
    try:
        # Initialize client
        credential = DefaultAzureCredential()
        project_client = AIProjectClient(
            endpoint=connection_string,
            credential=credential
        )
        
        # Delete previous test agents
        try:
            for agent_id in ["asst_zbemwTtkBPnZNSWR5MNVQ0wq"]:
                project_client.agents.delete_agent(agent_id)
                print(f"Deleted agent: {agent_id}")
        except:
            pass
        
        # Load OpenAPI spec (v3.0.0)
        with open("north_star_openapi_v3.json", "r") as f:
            openapi_spec = json.load(f)
        
        print(f"\nCreating agent: {agent_name}")
        print("Using OpenAPI 3.0.0 spec with anonymous auth")
        print("API key is embedded in the spec as default header value")
        
        # Create anonymous auth (following reference)
        auth = OpenApiAnonymousAuthDetails()
        
        # Create OpenAPI tool (following reference)
        openapi_tool = OpenApiTool(
            name="north_star_api",
            spec=openapi_spec,
            description="North Star operations API",
            auth=auth
        )
        
        # Create agent with tool definitions
        agent = project_client.agents.create_agent(
            model=model_name,
            name=agent_name,
            instructions=agent_instructions,
            tools=openapi_tool.definitions  # Use definitions
        )
        
        print(f"\n✅ Agent created: {agent.id}")
        
        # Verify agent
        retrieved_agent = project_client.agents.get_agent(agent.id)
        print(f"Agent verified: {retrieved_agent.name}")
        
        # Save deployment info
        deployment_info = {
            "agent_id": agent.id,
            "agent_name": agent_name,
            "deployed_at": datetime.now().isoformat(),
            "model": model_name,
            "auth_type": "anonymous",
            "api_key_location": "header_default",
            "openapi_version": "3.0.0",
            "server_side_execution": True
        }
        
        deployment_file = Path(__file__).parent / f"anonymous_auth_deployment_{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
        with open(deployment_file, "w") as f:
            json.dump(deployment_info, f, indent=2)
        
        print(f"\nDeployment info saved: {deployment_file}")
        
        # Update main deployment info
        main_deployment_file = Path(__file__).parent.parent.parent / "stratos_deployment_info.json"
        try:
            with open(main_deployment_file, 'r') as f:
                existing_info = json.load(f)
        except:
            existing_info = {}
        
        existing_info["north_star_anonymous_auth"] = deployment_info
        
        with open(main_deployment_file, 'w') as f:
            json.dump(existing_info, f, indent=2)
        
        print("\n" + "=" * 70)
        print("🎉 DEPLOYMENT SUCCESSFUL")
        print("=" * 70)
        print("✓ Anonymous auth configured")
        print("✓ API key embedded in OpenAPI spec")
        print("✓ Ready for server-side execution")
        print(f"\n📝 Agent ID: {agent.id}")
        
        return agent.id
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    if not os.getenv("AZURE_AI_PROJECT_CONNECTION_STRING"):
        print("Error: AZURE_AI_PROJECT_CONNECTION_STRING not set")
        exit(1)
    
    agent_id = deploy_with_anonymous_auth()
    if agent_id:
        print(f"\n🚀 Ready to test with agent: {agent_id}")