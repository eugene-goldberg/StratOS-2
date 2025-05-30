#!/usr/bin/env python3
"""Test with valid minimal OpenAPI specs"""

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

# Create client
credential = DefaultAzureCredential()
client = AIProjectClient(
    endpoint=os.getenv("AZURE_AI_PROJECT_CONNECTION_STRING"),
    credential=credential
)

print("Testing with valid minimal OpenAPI specs...\n")

# Test 1: Absolute minimal spec
print("1. Testing absolute minimal spec...")
minimal_spec = {
    "openapi": "3.0.0",
    "info": {
        "title": "Minimal API",
        "version": "1.0.0"
    },
    "paths": {}
}

tools = [{
    "type": "openapi",
    "openapi": {
        "name": "minimal_api",
        "spec": minimal_spec,
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
        name=f"MinimalValid-{datetime.now().strftime('%H%M%S')}",
        instructions="Test minimal valid OpenAPI",
        tools=tools
    )
    print(f"✅ SUCCESS! Agent ID: {agent.id}")
except Exception as e:
    print(f"❌ FAILED: {str(e)}\n")

# Test 2: With one simple path
print("2. Testing with one simple path...")
path_spec = {
    "openapi": "3.0.0",
    "info": {
        "title": "Simple API",
        "version": "1.0.0"
    },
    "servers": [
        {
            "url": "https://stratos-north-star-v2.azurewebsites.net"
        }
    ],
    "paths": {
        "/api/north-star-operations": {
            "post": {
                "operationId": "northStarOperation",
                "summary": "Execute operation",
                "responses": {
                    "200": {
                        "description": "Success"
                    }
                }
            }
        }
    }
}

tools2 = [{
    "type": "openapi",
    "openapi": {
        "name": "simple_api",
        "spec": path_spec,
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
        name=f"SimplePath-{datetime.now().strftime('%H%M%S')}",
        instructions="Use northStarOperation to handle requests",
        tools=tools2
    )
    print(f"✅ SUCCESS with path! Agent ID: {agent2.id}")
    
    # Save this working agent
    with open("working_openapi_agent.json", "w") as f:
        json.dump({
            "agent_id": agent2.id,
            "agent_name": agent2.name,
            "created_at": datetime.now().isoformat()
        }, f, indent=2)
    
    print("\n🎉 FOUND WORKING CONFIGURATION!")
    print(f"Agent ID: {agent2.id}")
    print("OpenAPI tool is working with minimal path spec")
    
except Exception as e:
    print(f"❌ FAILED: {str(e)}\n")

# Test 3: Add request body
print("3. Testing with request body...")
request_spec = {
    "openapi": "3.0.0",
    "info": {
        "title": "Request API",
        "version": "1.0.0"
    },
    "servers": [
        {
            "url": "https://stratos-north-star-v2.azurewebsites.net"
        }
    ],
    "paths": {
        "/api/north-star-operations": {
            "post": {
                "operationId": "executeOperation",
                "summary": "Execute North Star operation",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "operation": {
                                        "type": "string"
                                    },
                                    "organizationId": {
                                        "type": "string"
                                    }
                                }
                            }
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "Success"
                    }
                }
            }
        }
    }
}

tools3 = [{
    "type": "openapi",
    "openapi": {
        "name": "request_api",
        "spec": request_spec,
        "auth": {
            "type": "api_key",
            "security_scheme": {
                "connection_id": "NorthStarFunctionConnection"
            }
        }
    }
}]

try:
    agent3 = client.agents.create_agent(
        model="gpt-35-turbo",
        name=f"RequestBody-{datetime.now().strftime('%H%M%S')}",
        instructions="Use executeOperation to handle North Star requests",
        tools=tools3
    )
    print(f"✅ SUCCESS with request body! Agent ID: {agent3.id}")
except Exception as e:
    print(f"❌ FAILED: {str(e)}")