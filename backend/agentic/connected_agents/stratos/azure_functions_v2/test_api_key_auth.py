#!/usr/bin/env python3
"""
Test using API key authentication without connection reference.
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
    OpenApiConnectionSecurityScheme,
    MessageRole,
    AgentThreadCreationOptions,
    ThreadMessageOptions
)

# Load environment variables
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)


def test_api_key_auth():
    """Test with API key auth configuration."""
    
    print("=" * 70)
    print("TESTING API KEY AUTHENTICATION APPROACH")
    print("=" * 70)
    
    # First, let's create a new connection with a simpler approach
    print("\n1. Creating new API key connection...")
    
    # Create connection YAML with minimal config
    connection_yaml = """name: NorthStarAPIKey
type: custom
target: https://stratos-north-star-v2.azurewebsites.net
credentials:
  type: api_key
  key: fRvKUW-I0NseHY8728jcJtx6E7rxdvKUrK2pBiLNFEGBAzFuVfQ7jw==
"""
    
    # Save connection config
    connection_file = Path(__file__).parent / "api_key_connection.yml"
    with open(connection_file, "w") as f:
        f.write(connection_yaml)
    
    # Create the connection
    import subprocess
    result = subprocess.run([
        "az", "ml", "connection", "create",
        "--file", str(connection_file),
        "--resource-group", "semantic-kernel-multi-agent-rg",
        "--workspace-name", "sk-multi-agent-project"
    ], capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ Connection created successfully")
    else:
        print(f"⚠️  Connection creation output: {result.stderr}")
    
    # Configuration
    agent_name = f"NorthStarAPIKeyAuth-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    model_name = "gpt-35-turbo"
    connection_string = os.getenv("AZURE_AI_PROJECT_CONNECTION_STRING")
    
    agent_instructions = """You are the North Star Agent using API key authentication.

Use ExecuteNorthStarOperation to handle all requests. Include organizationId in all requests.

Operations: managePurpose, manageVision, manageValues, manageStrategicGoals, validateAlignment, getNorthStarSummary."""
    
    try:
        # Initialize client
        credential = DefaultAzureCredential()
        project_client = AIProjectClient(
            endpoint=connection_string,
            credential=credential
        )
        
        # Load OpenAPI spec
        openapi_file = Path(__file__).parent / "north_star_openapi_v31.json"
        with open(openapi_file, "r") as f:
            openapi_spec = jsonref.loads(f.read())
        
        # Update the spec to include API key security
        if "components" not in openapi_spec:
            openapi_spec["components"] = {}
        
        openapi_spec["components"]["securitySchemes"] = {
            "apiKeyAuth": {
                "type": "apiKey",
                "in": "header",
                "name": "x-functions-key"
            }
        }
        
        # Apply security globally
        openapi_spec["security"] = [{"apiKeyAuth": []}]
        
        print(f"\n2. Creating agent: {agent_name}")
        
        # Create auth with new connection
        auth = OpenApiConnectionAuthDetails(
            security_scheme=OpenApiConnectionSecurityScheme(
                connection_id="NorthStarAPIKey"  # New connection name
            )
        )
        
        # Create OpenAPI tool
        openapi_tool = OpenApiTool(
            name="north_star_api",
            spec=openapi_spec,
            description="North Star API with API key auth",
            auth=auth
        )
        
        # Create agent
        agent = project_client.agents.create_agent(
            model=model_name,
            name=agent_name,
            instructions=agent_instructions,
            tools=openapi_tool.definitions
        )
        
        print(f"✅ Agent created: {agent.id}")
        
        # Test execution
        print("\n3. Testing server-side execution...")
        
        thread_options = AgentThreadCreationOptions(
            messages=[
                ThreadMessageOptions(
                    role=MessageRole.USER,
                    content="Get the current organizational purpose for test-org-apikey"
                )
            ]
        )
        
        print("⚡ Creating thread and run...")
        run = project_client.agents.create_thread_and_process_run(
            agent_id=agent.id,
            thread=thread_options
        )
        
        print(f"\nRun ID: {run.id}")
        print(f"Status: {run.status}")
        
        if str(run.status) == "RunStatus.COMPLETED":
            print("\n🎉 SUCCESS! API key authentication worked!")
            print("✅ Server-side HTTP execution successful")
            
            # Save success
            success_info = {
                "agent_id": agent.id,
                "agent_name": agent_name,
                "connection_name": "NorthStarAPIKey",
                "status": "SUCCESS",
                "server_side_execution": True,
                "timestamp": datetime.now().isoformat()
            }
            
            with open("SUCCESS_api_key_auth.json", "w") as f:
                json.dump(success_info, f, indent=2)
                
        elif str(run.status) == "RunStatus.FAILED":
            if hasattr(run, 'last_error'):
                print(f"\n❌ Error: {run.last_error}")
                
                # Check if it's still a connection issue
                if "NorthStarAPIKey" in str(run.last_error):
                    print("\n4. Trying to understand connection visibility...")
                    
                    # List all connections
                    list_result = subprocess.run([
                        "az", "ml", "connection", "list",
                        "--resource-group", "semantic-kernel-multi-agent-rg",
                        "--workspace-name", "sk-multi-agent-project",
                        "--query", "[].name",
                        "-o", "json"
                    ], capture_output=True, text=True)
                    
                    if list_result.returncode == 0:
                        connections = json.loads(list_result.stdout)
                        print(f"Available connections: {connections}")
        
        # Clean up temp file
        if connection_file.exists():
            connection_file.unlink()
        
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
    
    agent_id = test_api_key_auth()