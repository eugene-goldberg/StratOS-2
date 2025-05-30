#!/usr/bin/env python3
"""
Deploy North Star Agent with OpenAPI tool - Final implementation
Using the correct approach from Microsoft documentation
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


def deploy_agent():
    """Deploy North Star agent with OpenAPI tool for server-side execution."""
    
    print("=" * 70)
    print("NORTH STAR AGENT DEPLOYMENT - OPENAPI SERVER-SIDE EXECUTION")
    print("=" * 70)
    
    # Configuration
    agent_name = f"NorthStarAgentOpenAPI-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    model_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-35-turbo")
    connection_string = os.getenv("AZURE_AI_PROJECT_CONNECTION_STRING")
    
    # Agent instructions
    agent_instructions = """You are the North Star Agent for StratOS, responsible for defining and maintaining the organization's strategic foundation.

Use the ExecuteNorthStarOperation function to handle all North Star requests. The Azure AI Service will execute these calls directly without client intervention.

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
        
        # Load OpenAPI specification with jsonref to handle any $ref
        openapi_file = Path(__file__).parent / "north_star_openapi_v31.json"
        with open(openapi_file, "r") as f:
            openapi_spec = jsonref.loads(f.read())
        
        print(f"\nCreating agent: {agent_name}")
        print(f"Model: {model_name}")
        print(f"OpenAPI spec loaded: {openapi_file.name}")
        
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
            description="North Star operations API for managing strategic foundation elements",
            auth=auth
        )
        
        print(f"OpenAPI tool created with connection: NorthStarFunctionConnection")
        
        # Create agent with OpenAPI tool definitions
        agent = project_client.agents.create_agent(
            model=model_name,
            name=agent_name,
            instructions=agent_instructions,
            tools=openapi_tool.definitions
        )
        
        print(f"\n✅ North Star Agent deployed successfully!")
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
        
        existing_info["north_star_agent_openapi"] = deployment_info
        
        with open(main_deployment_file, 'w') as f:
            json.dump(existing_info, f, indent=2)
        
        print("\n" + "=" * 70)
        print("🎉 SERVER-SIDE EXECUTION ENABLED")
        print("=" * 70)
        print("✓ Agent uses OpenAPI tools with connection authentication")
        print("✓ Azure AI Service makes HTTP calls directly")
        print("✓ NO client-side function execution required")
        print("✓ Use create_and_process() for autonomous operation")
        print("\n✅ The agent is ready for:")
        print("  - Managing organizational purpose and vision")
        print("  - Defining and maintaining core values")
        print("  - Creating hierarchical strategic goals")
        print("  - Validating alignment with North Star")
        print("  - Providing comprehensive North Star summaries")
        print("\n⚡ ALL operations execute server-side autonomously")
        
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
    
    agent_id = deploy_agent()
    if agent_id:
        print(f"\n🚀 North Star Agent deployed with ID: {agent_id}")
        print("\n📝 Next: Run test_north_star_server_side.py to verify autonomous execution")