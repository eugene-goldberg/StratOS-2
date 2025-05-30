#!/usr/bin/env python3
"""Deploy with minimal OpenAPI spec to isolate issue"""

import os
import json
from pathlib import Path
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from datetime import datetime

# Load environment
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# Load minimal spec
with open("minimal_north_star_openapi.json", "r") as f:
    openapi_spec = json.load(f)

# Create client
credential = DefaultAzureCredential()
client = AIProjectClient(
    endpoint=os.getenv("AZURE_AI_PROJECT_CONNECTION_STRING"),
    credential=credential
)

print("Testing with minimal OpenAPI spec...")
print(f"Spec size: {len(json.dumps(openapi_spec))} characters")

# Try deployment
tools = [{
    "type": "openapi",
    "openapi": {
        "name": "north_star_minimal",
        "spec": openapi_spec,
        "auth": {
            "type": "api_key",
            "security_scheme": {
                "connection_id": "NorthStarFunctionConnection"
            }
        }
    }
}]

try:
    agent = client.agents.create_agent(
        model="gpt-35-turbo",
        name=f"MinimalTest-{datetime.now().strftime('%H%M%S')}",
        instructions="Test minimal OpenAPI",
        tools=tools
    )
    print(f"\n✅ SUCCESS! Agent ID: {agent.id}")
    
    # Get and display agent details
    retrieved = client.agents.get_agent(agent.id)
    print(f"\nAgent retrieved successfully")
    print(f"Tools configured: {len(retrieved.tools)}")
    
    # Keep this agent for testing
    print(f"\n🎉 Agent ready for testing: {agent.id}")
    
    # Save info
    with open("minimal_agent_id.txt", "w") as f:
        f.write(agent.id)
    
except Exception as e:
    print(f"\n❌ FAILED: {str(e)}")
    
    # Try even simpler
    print("\nTrying without security in spec...")
    simple_spec = {
        "openapi": "3.0.0",
        "info": {"title": "Test", "version": "1.0"},
        "servers": [{"url": "https://stratos-north-star-v2.azurewebsites.net"}],
        "paths": {
            "/api/north-star-operations": {
                "post": {
                    "operationId": "test",
                    "responses": {"200": {"description": "OK"}}
                }
            }
        }
    }
    
    tools2 = [{
        "type": "openapi",
        "openapi": {
            "name": "test",
            "spec": simple_spec,
            "auth": {
                "type": "api_key",
                "security_scheme": {
                    "connection_id": "NorthStarFunctionConnection"
                }
            }
        }
    }]
    
    try:
        agent2 = client.agents.create_agent(
            model="gpt-35-turbo",
            name=f"UltraMinimal-{datetime.now().strftime('%H%M%S')}",
            instructions="Test",
            tools=tools2
        )
        print(f"✅ Ultra-minimal worked! Agent ID: {agent2.id}")
    except Exception as e2:
        print(f"❌ Ultra-minimal also failed: {str(e2)}")