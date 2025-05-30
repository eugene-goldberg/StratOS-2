#!/usr/bin/env python3
"""Test minimal OpenAPI deployment"""

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

# Load minimal OpenAPI spec
with open("minimal_openapi.json", "r") as f:
    openapi_spec = json.load(f)

# Create client
credential = DefaultAzureCredential()
client = AIProjectClient(
    endpoint=os.getenv("AZURE_AI_PROJECT_CONNECTION_STRING"),
    credential=credential
)

# Simple agent configuration
agent_name = "TestMinimalOpenAPI"
instructions = "You are a test agent. Use executeOperation to handle requests."

# Try different tool configurations
print("Testing OpenAPI tool configurations...\n")

# Configuration 1: Basic openapi tool
print("1. Testing basic openapi tool...")
try:
    tools = [{
        "type": "openapi",
        "openapi": {
            "spec": openapi_spec
        }
    }]
    
    agent = client.agents.create_agent(
        model="gpt-35-turbo",
        name=f"{agent_name}-1",
        instructions=instructions,
        tools=tools
    )
    print(f"✅ SUCCESS: Basic openapi tool - Agent ID: {agent.id}")
except Exception as e:
    print(f"❌ FAILED: Basic openapi tool - {str(e)}")

# Configuration 2: With connection auth
print("\n2. Testing openapi with connection auth...")
try:
    tools = [{
        "type": "openapi",
        "openapi": {
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
    print(f"✅ SUCCESS: Connection auth - Agent ID: {agent.id}")
except Exception as e:
    print(f"❌ FAILED: Connection auth - {str(e)}")

# Configuration 3: With connection_id
print("\n3. Testing openapi with connection_id...")
try:
    tools = [{
        "type": "openapi",
        "openapi": {
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
        name=f"{agent_name}-3",
        instructions=instructions,
        tools=tools
    )
    print(f"✅ SUCCESS: Connection ID - Agent ID: {agent.id}")
except Exception as e:
    print(f"❌ FAILED: Connection ID - {str(e)}")

# Configuration 4: With name attribute
print("\n4. Testing openapi with name attribute...")
try:
    tools = [{
        "type": "openapi",
        "openapi": {
            "name": "north_star_api",
            "spec": openapi_spec,
            "auth": {
                "type": "api_key",
                "api_key": {
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
    print(f"✅ SUCCESS: With name - Agent ID: {agent.id}")
except Exception as e:
    print(f"❌ FAILED: With name - {str(e)}")