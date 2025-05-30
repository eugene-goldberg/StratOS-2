#!/usr/bin/env python3
"""Debug OpenAPI deployment with correct structure"""

import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient

# Load environment
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# Load OpenAPI spec
with open("north_star_openapi.json", "r") as f:
    openapi_spec = json.load(f)

# Create client
credential = DefaultAzureCredential()
client = AIProjectClient(
    endpoint=os.getenv("AZURE_AI_PROJECT_CONNECTION_STRING"),
    credential=credential
)

agent_name = "NorthStarOpenAPIDebug"
instructions = "You are the North Star Agent. Use executeNorthStarOperation to handle all requests."

print("Testing OpenAPI configurations with proper structure...\n")

# Test 1: With name and spec only
print("1. Testing with name and spec only...")
try:
    tools = [{
        "type": "openapi",
        "openapi": {
            "name": "north_star_api",
            "spec": openapi_spec
        }
    }]
    
    agent = client.agents.create_agent(
        model="gpt-35-turbo",
        name=f"{agent_name}-1",
        instructions=instructions,
        tools=tools
    )
    print(f"✅ SUCCESS: Basic with name - Agent ID: {agent.id}")
    # Clean up
    client.agents.delete_agent(agent.id)
except Exception as e:
    print(f"❌ FAILED: {str(e)}\n")

# Test 2: With connection authentication
print("2. Testing with connection authentication...")
try:
    tools = [{
        "type": "openapi",
        "openapi": {
            "name": "north_star_api",
            "spec": openapi_spec,
            "auth": {
                "type": "connection",
                "connection": {
                    "id": "NorthStarFunctionConnection"
                }
            }
        }
    }]
    
    agent = client.agents.create_agent(
        model="gpt-35-turbo",
        name=f"{agent_name}-2",
        instructions=instructions,
        tools=tools
    )
    print(f"✅ SUCCESS: With connection auth - Agent ID: {agent.id}")
    # Clean up
    client.agents.delete_agent(agent.id)
except Exception as e:
    print(f"❌ FAILED: {str(e)}\n")

# Test 3: With security_scheme
print("3. Testing with security_scheme...")
try:
    tools = [{
        "type": "openapi",
        "openapi": {
            "name": "north_star_api",
            "spec": openapi_spec,
            "auth": {
                "type": "security_scheme",
                "security_scheme": {
                    "connection_id": "NorthStarFunctionConnection"
                }
            }
        }
    }]
    
    agent = client.agents.create_agent(
        model="gpt-35-turbo",
        name=f"{agent_name}-3",
        instructions=instructions,
        tools=tools
    )
    print(f"✅ SUCCESS: With security_scheme - Agent ID: {agent.id}")
    # Clean up
    client.agents.delete_agent(agent.id)
except Exception as e:
    print(f"❌ FAILED: {str(e)}\n")

# Test 4: With api_key type
print("4. Testing with api_key auth type...")
try:
    tools = [{
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
    }]
    
    agent = client.agents.create_agent(
        model="gpt-35-turbo",
        name=f"{agent_name}-4",
        instructions=instructions,
        tools=tools
    )
    print(f"✅ SUCCESS: With api_key auth - Agent ID: {agent.id}")
    print("\n🎉 FOUND WORKING CONFIGURATION!")
    print(f"Agent ID: {agent.id}")
    # Don't clean up this one - keep it for testing
except Exception as e:
    print(f"❌ FAILED: {str(e)}\n")

# Test 5: With inline spec instead of file
print("5. Testing with inline minimal spec...")
try:
    inline_spec = {
        "openapi": "3.0.0",
        "info": {"title": "North Star API", "version": "1.0.0"},
        "servers": [{"url": "https://stratos-north-star-v2.azurewebsites.net"}],
        "paths": {
            "/api/north-star-operations": {
                "post": {
                    "operationId": "executeNorthStarOperation",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "operation": {"type": "string"},
                                        "organizationId": {"type": "string"}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {"200": {"description": "Success"}},
                    "security": [{"apiKey": []}]
                }
            }
        },
        "components": {
            "securitySchemes": {
                "apiKey": {
                    "type": "apiKey",
                    "name": "x-functions-key",
                    "in": "header"
                }
            }
        }
    }
    
    tools = [{
        "type": "openapi",
        "openapi": {
            "name": "north_star_api",
            "spec": inline_spec,
            "auth": {
                "type": "api_key",
                "security_scheme": {
                    "connection_id": "NorthStarFunctionConnection"
                }
            }
        }
    }]
    
    agent = client.agents.create_agent(
        model="gpt-35-turbo",
        name=f"{agent_name}-5",
        instructions=instructions,
        tools=tools
    )
    print(f"✅ SUCCESS: With inline spec - Agent ID: {agent.id}")
    # Keep this one too
except Exception as e:
    print(f"❌ FAILED: {str(e)}\n")

print("\n" + "="*70)
print("DEBUGGING COMPLETE")
print("="*70)