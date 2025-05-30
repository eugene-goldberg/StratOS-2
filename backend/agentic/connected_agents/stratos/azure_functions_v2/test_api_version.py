#!/usr/bin/env python3
"""Test with different API versions"""

import os
from pathlib import Path
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient

# Load environment
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# Test different API versions
api_versions = [
    "latest",
    "2024-12-01-preview", 
    "2024-07-01-preview",
    "2024-05-01-preview",
    "2024-02-15-preview"
]

connection_string = os.getenv("AZURE_AI_PROJECT_CONNECTION_STRING")
credential = DefaultAzureCredential()

print("Testing different API versions...\n")

for version in api_versions:
    print(f"Testing API version: {version}")
    try:
        # Create client with specific API version
        client = AIProjectClient(
            endpoint=connection_string,
            credential=credential,
            api_version=version
        )
        
        # Try simple agent creation without OpenAPI first
        agent = client.agents.create_agent(
            model="gpt-35-turbo",
            name=f"VersionTest-{version.replace('-', '')}",
            instructions="Test agent"
        )
        
        print(f"✅ API version {version} works! Agent ID: {agent.id}")
        
        # Clean up
        client.agents.delete_agent(agent.id)
        
        # Now try with OpenAPI
        print(f"   Testing OpenAPI with {version}...")
        tools = [{
            "type": "openapi",
            "openapi": {
                "name": "test",
                "spec": {
                    "openapi": "3.0.0",
                    "info": {"title": "Test", "version": "1.0"},
                    "paths": {}
                },
                "auth": {
                    "type": "api_key",
                    "security_scheme": {
                        "connection_id": "NorthStarFunctionConnection"
                    }
                }
            }
        }]
        
        agent2 = client.agents.create_agent(
            model="gpt-35-turbo",
            name=f"OpenAPITest-{version.replace('-', '')}",
            instructions="Test",
            tools=tools
        )
        print(f"   ✅ OpenAPI works with {version}! Agent ID: {agent2.id}")
        print(f"\n🎉 FOUND WORKING API VERSION: {version}")
        break
        
    except Exception as e:
        error_msg = str(e)
        if "api_version" in error_msg:
            print(f"❌ Invalid API version: {version}")
        elif "openapi" in error_msg.lower():
            print(f"❌ OpenAPI failed with {version}: {error_msg[:100]}...")
        else:
            print(f"❌ Failed with {version}: {error_msg[:100]}...")
    
    print()