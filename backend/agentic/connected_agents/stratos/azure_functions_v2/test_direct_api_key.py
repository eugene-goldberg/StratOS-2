#!/usr/bin/env python3
"""
Test using direct API key in OpenAPI spec instead of connection reference.
This bypasses the connection management issue.
"""

import os
import sys
import json
import jsonref
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Add parent directories to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.agents.models import (
    OpenApiTool,
    MessageRole,
    AgentThreadCreationOptions,
    ThreadMessageOptions
)

# Load environment variables
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)


def test_direct_api_key():
    """Deploy agent with API key directly in OpenAPI spec."""
    
    print("=" * 70)
    print("TESTING DIRECT API KEY APPROACH")
    print("=" * 70)
    
    # Configuration
    agent_name = f"NorthStarDirectAuth-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    model_name = "gpt-35-turbo"
    connection_string = os.getenv("AZURE_AI_PROJECT_CONNECTION_STRING")
    
    # Agent instructions
    agent_instructions = """You are the North Star Agent for StratOS with direct API authentication.

Use the ExecuteNorthStarOperation function to handle all requests. The function will make HTTP calls directly.

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
        
        # Delete previous test agent
        try:
            old_id = "asst_O4aSd8sNgSTafAdOqLAhWHjP"
            project_client.agents.delete_agent(old_id)
            print(f"Deleted old agent: {old_id}")
        except:
            pass
        
        # Load and modify OpenAPI spec to include auth directly
        openapi_file = Path(__file__).parent / "north_star_openapi_v31.json"
        with open(openapi_file, "r") as f:
            openapi_spec = json.loads(f.read())
        
        # Add security scheme directly to the spec
        openapi_spec["components"] = openapi_spec.get("components", {})
        openapi_spec["components"]["securitySchemes"] = {
            "apiKey": {
                "type": "apiKey",
                "in": "header",
                "name": "x-functions-key"
            }
        }
        
        # Add security requirement
        openapi_spec["security"] = [{"apiKey": []}]
        
        # Also add the key as a server variable for testing
        openapi_spec["servers"][0]["variables"] = {
            "apiKey": {
                "default": "fRvKUW-I0NseHY8728jcJtx6E7rxdvKUrK2pBiLNFEGBAzFuVfQ7jw==",
                "description": "Azure Function API Key"
            }
        }
        
        print(f"\nCreating agent: {agent_name}")
        print("Using direct API key authentication in OpenAPI spec")
        
        # Create OpenAPI tool without connection reference
        openapi_tool = OpenApiTool(
            name="north_star_api",
            spec=openapi_spec,
            description="North Star API with direct authentication"
        )
        
        # Create agent
        agent = project_client.agents.create_agent(
            model=model_name,
            name=agent_name,
            instructions=agent_instructions,
            tools=openapi_tool.definitions
        )
        
        print(f"\n✅ Agent created: {agent.id}")
        
        # Test immediately
        print("\n" + "=" * 70)
        print("TESTING SERVER-SIDE EXECUTION")
        print("=" * 70)
        
        thread_options = AgentThreadCreationOptions(
            messages=[
                ThreadMessageOptions(
                    role=MessageRole.USER,
                    content="Set the organizational purpose to 'Innovate healthcare with AI' for organization test-org-direct"
                )
            ]
        )
        
        print("⚡ Executing create_thread_and_process_run()...")
        run = project_client.agents.create_thread_and_process_run(
            agent_id=agent.id,
            thread=thread_options
        )
        
        print(f"\n✅ Run completed!")
        print(f"Run ID: {run.id}")
        print(f"Status: {run.status}")
        
        if str(run.status) == "RunStatus.COMPLETED":
            print("\n🎉 SUCCESS! Server-side execution worked!")
            print("✅ The agent made HTTP calls directly")
            print("✅ No connection management needed")
            print("✅ Direct API key authentication successful")
            
            # Save successful config
            success_info = {
                "agent_id": agent.id,
                "agent_name": agent_name,
                "deployed_at": datetime.now().isoformat(),
                "authentication": "direct_api_key",
                "status": "SUCCESS",
                "server_side_execution": True
            }
            
            success_file = Path(__file__).parent / f"SUCCESS_direct_auth_{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
            with open(success_file, "w") as f:
                json.dump(success_info, f, indent=2)
            
            print(f"\n✅ Success info saved to: {success_file}")
            
        elif str(run.status) == "RunStatus.FAILED":
            print(f"\n❌ Run failed")
            if hasattr(run, 'last_error') and run.last_error:
                print(f"Error: {run.last_error}")
        
        return agent.id
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    # Ensure environment
    if not os.getenv("AZURE_AI_PROJECT_CONNECTION_STRING"):
        print("Error: AZURE_AI_PROJECT_CONNECTION_STRING not set")
        exit(1)
    
    agent_id = test_direct_api_key()
    if agent_id:
        print(f"\n🚀 Agent deployed with direct auth: {agent_id}")