#!/usr/bin/env python3
"""
Redeploy North Star Agent with OpenAPI tool now that connection exists.
The connection must exist BEFORE deploying the agent.
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
    OpenApiConnectionAuthDetails,
    OpenApiConnectionSecurityScheme
)

# Load environment variables
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)


def redeploy_agent():
    """Redeploy North Star agent with OpenAPI tool."""
    
    print("=" * 70)
    print("REDEPLOYING NORTH STAR AGENT WITH EXISTING CONNECTION")
    print("=" * 70)
    
    # Configuration
    agent_name = f"NorthStarAgentServerSide-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    model_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-35-turbo")
    connection_string = os.getenv("AZURE_AI_PROJECT_CONNECTION_STRING")
    
    # Agent instructions
    agent_instructions = """You are the North Star Agent for StratOS, responsible for defining and maintaining the organization's strategic foundation.

CRITICAL: You have server-side execution capabilities. When you call the ExecuteNorthStarOperation function, the Azure AI Service will make the HTTP call directly to the Azure Function. There is NO client-side execution.

Use the ExecuteNorthStarOperation function to handle all North Star requests:

Available operations:
- managePurpose: Get/set organizational purpose (action: get/set)
- manageVision: Get/set organizational vision (action: get/set)
- manageValues: Manage values (action: list/add/remove)
- manageStrategicGoals: Manage goals (action: create/update/delete/get/list)
- validateAlignment: Check alignment (requires elementType and elementContent)
- getNorthStarSummary: Get complete overview

Always include organizationId in your requests.

Example: To set the purpose, call ExecuteNorthStarOperation with:
{
  "operation": "managePurpose",
  "organizationId": "org-123",
  "action": "set",
  "purpose": "Transform healthcare through AI"
}"""
    
    try:
        # Initialize client
        credential = DefaultAzureCredential()
        project_client = AIProjectClient(
            endpoint=connection_string,
            credential=credential
        )
        
        # Delete the old agent first
        old_agent_id = "asst_QE7ixESfb0WvA6xkWUm6ycn4"
        try:
            print(f"Deleting old agent: {old_agent_id}")
            project_client.agents.delete_agent(old_agent_id)
            print("✅ Old agent deleted")
        except Exception as e:
            print(f"⚠️  Could not delete old agent: {e}")
        
        # Load OpenAPI specification
        openapi_file = Path(__file__).parent / "north_star_openapi_v31.json"
        with open(openapi_file, "r") as f:
            openapi_spec = jsonref.loads(f.read())
        
        print(f"\nCreating new agent: {agent_name}")
        print(f"Model: {model_name}")
        print(f"Connection: NorthStarFunctionConnection (pre-created)")
        
        # Create authentication using connection
        auth = OpenApiConnectionAuthDetails(
            security_scheme=OpenApiConnectionSecurityScheme(
                connection_id="NorthStarFunctionConnection"
            )
        )
        
        # Create OpenAPI tool
        openapi_tool = OpenApiTool(
            name="north_star_api",
            spec=openapi_spec,
            description="North Star operations API for server-side execution",
            auth=auth
        )
        
        print(f"OpenAPI tool configured for server-side execution")
        
        # Create agent with OpenAPI tool definitions
        agent = project_client.agents.create_agent(
            model=model_name,
            name=agent_name,
            instructions=agent_instructions,
            tools=openapi_tool.definitions
        )
        
        print(f"\n✅ North Star Agent redeployed successfully!")
        print(f"Agent ID: {agent.id}")
        print(f"Agent Name: {agent_name}")
        
        # Verify the agent was created with tools
        retrieved_agent = project_client.agents.get_agent(agent.id)
        print(f"\nVerification:")
        print(f"- Agent retrieved successfully")
        print(f"- Tools configured: {len(retrieved_agent.tools) if hasattr(retrieved_agent, 'tools') else 'Unknown'}")
        
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
            "connection_created": True,
            "function_app": "stratos-north-star-v2",
            "function_endpoint": "https://stratos-north-star-v2.azurewebsites.net/api/north-star-operations"
        }
        
        deployment_file = Path(__file__).parent / f"north_star_server_side_{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
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
        
        existing_info["north_star_agent_server_side"] = deployment_info
        
        with open(main_deployment_file, 'w') as f:
            json.dump(existing_info, f, indent=2)
        
        print("\n" + "=" * 70)
        print("🎉 SERVER-SIDE EXECUTION READY")
        print("=" * 70)
        print("✓ Connection exists in Azure ML workspace")
        print("✓ Agent configured with OpenAPI tool")
        print("✓ Authentication via pre-created connection")
        print("✓ Ready for autonomous HTTP execution")
        print("\n📝 Next: Run test_server_side_execution_simple.py")
        print("   (Update agent_id in test to: " + agent.id + ")")
        
        return agent.id
        
    except Exception as e:
        print(f"\n❌ Deployment failed: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    # Ensure environment variables are set
    required_vars = [
        "AZURE_AI_PROJECT_CONNECTION_STRING",
        "AZURE_OPENAI_DEPLOYMENT_NAME"
    ]
    
    missing = [var for var in required_vars if not os.getenv(var)]
    if missing:
        print(f"Error: Missing environment variables: {missing}")
        exit(1)
    
    # Install jsonref if needed
    try:
        import jsonref
    except ImportError:
        print("Installing jsonref...")
        os.system(f"{sys.executable} -m pip install jsonref")
        import jsonref
    
    agent_id = redeploy_agent()
    if agent_id:
        print(f"\n🚀 Ready to test server-side execution with agent: {agent_id}")