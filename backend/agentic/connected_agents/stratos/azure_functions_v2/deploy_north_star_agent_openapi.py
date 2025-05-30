#!/usr/bin/env python3
"""
Deploy North Star Agent with OpenAPI tool for server-side HTTP execution
Following the Complete Implementation Guide
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
    agent_name = f"NorthStarAgentOpenAPI-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    model_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-35-turbo")
    connection_string = os.getenv("AZURE_AI_PROJECT_CONNECTION_STRING")
    
    # Agent instructions
    agent_instructions = """You are the North Star Agent for StratOS, responsible for defining and maintaining the organization's strategic foundation using server-side HTTP execution.

When users request North Star operations:
1. Use the executeNorthStarOperation tool to perform the requested action
2. The Azure AI Service will make HTTP calls directly to the Azure Function
3. No client intervention is required

## Available Operations:

### Purpose Management
- Get purpose: operation="managePurpose", action="get"
- Set purpose: operation="managePurpose", action="set", purpose="statement"

### Vision Management  
- Get vision: operation="manageVision", action="get"
- Set vision: operation="manageVision", action="set", vision="statement"

### Values Management
- List values: operation="manageValues", action="list"
- Add value: operation="manageValues", action="add", value="name", description="desc"
- Remove value: operation="manageValues", action="remove", value="name"

### Strategic Goals Management
- List goals: operation="manageStrategicGoals", action="list"
- Create goal: operation="manageStrategicGoals", action="create", title="title", description="desc"
- Update goal: operation="manageStrategicGoals", action="update", goalId="id", title="new title"
- Delete goal: operation="manageStrategicGoals", action="delete", goalId="id"
- Get goal: operation="manageStrategicGoals", action="get", goalId="id"

### Alignment Validation
- Validate: operation="validateAlignment", elementType="type", elementContent="content"

### North Star Summary
- Get summary: operation="getNorthStarSummary"

Always provide clear feedback about operation results and guide users in strategic planning."""
    
    # Load OpenAPI specification
    openapi_file = Path(__file__).parent / "north_star_openapi.json"
    with open(openapi_file, "r") as f:
        openapi_spec = json.load(f)
    
    # Define OpenAPI tool with authentication
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
        print("IMPORTANT: Server-side Execution Enabled")
        print("=" * 70)
        print("✓ Agent uses OpenAPI tools exclusively")
        print("✓ Azure AI Service makes HTTP calls directly") 
        print("✓ No client-side function execution required")
        print("✓ Use create_and_process() for autonomous operation")
        print("\n✅ The agent is now ready to:")
        print("  - Manage organizational purpose and vision")
        print("  - Define and maintain core values")
        print("  - Create hierarchical strategic goals")
        print("  - Validate alignment with North Star")
        print("  - Provide comprehensive North Star summaries")
        print("\n⚠️  ALL operations execute server-side without client intervention")
        
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
        print("\nSet them with:")
        for var in missing:
            print(f"export {var}='your-value'")
        exit(1)
    
    agent_id = deploy_agent()
    if agent_id:
        print(f"\n🎉 North Star Agent with OpenAPI tools deployed: {agent_id}")
        print("\n📝 Use test_north_star_openapi.py to verify server-side execution")