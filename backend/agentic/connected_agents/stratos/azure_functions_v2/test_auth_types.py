#!/usr/bin/env python3
"""Test different auth type values"""

import os
import json
from pathlib import Path
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient

# Load environment
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# Create client
credential = DefaultAzureCredential()
client = AIProjectClient(
    endpoint=os.getenv("AZURE_AI_PROJECT_CONNECTION_STRING"),
    credential=credential
)

# Minimal spec
spec = {
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

# Test different auth type values
auth_types = [
    "none",
    "oauth2", 
    "bearer",
    "custom",
    "connection_string",
    "managed_identity",
    "service_principal"
]

print("Testing different auth type values...\n")

for auth_type in auth_types:
    print(f"Testing auth type: {auth_type}")
    try:
        tools = [{
            "type": "openapi",
            "openapi": {
                "name": "test_api",
                "spec": spec,
                "auth": {
                    "type": auth_type
                }
            }
        }]
        
        agent = client.agents.create_agent(
            model="gpt-35-turbo",
            name=f"TestAuth-{auth_type}",
            instructions="Test",
            tools=tools
        )
        print(f"✅ SUCCESS: {auth_type} - Agent ID: {agent.id}")
        client.agents.delete_agent(agent.id)
        break
    except Exception as e:
        error_msg = str(e)
        if "unknown_parameter" in error_msg or "invalid_value" in error_msg:
            print(f"❌ INVALID: {auth_type}")
        else:
            print(f"❌ ERROR: {error_msg[:100]}...")
    print()