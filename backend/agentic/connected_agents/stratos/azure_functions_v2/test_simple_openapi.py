#!/usr/bin/env python3
"""Test with extremely simple OpenAPI spec"""

import os
import json
from pathlib import Path
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
import time

# Load environment
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# Create client
credential = DefaultAzureCredential()
client = AIProjectClient(
    endpoint=os.getenv("AZURE_AI_PROJECT_CONNECTION_STRING"),
    credential=credential
)

# Ultra-minimal spec - just one operation
spec = {
    "openapi": "3.0.0",
    "info": {
        "title": "North Star API",
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
                "summary": "Execute operation",
                "requestBody": {
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object"
                            }
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "Success",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object"
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}

print("Testing simple OpenAPI deployment...")
print(f"Spec: {json.dumps(spec, indent=2)}")

# Try deployment
tools = [{
    "type": "openapi",
    "openapi": {
        "name": "north_star_api",
        "spec": spec,
        "auth": {
            "type": "none"
        }
    }
}]

try:
    agent = client.agents.create_agent(
        model="gpt-35-turbo",
        name=f"SimpleOpenAPI-{int(time.time())}",
        instructions="Use executeOperation to handle requests.",
        tools=tools
    )
    print(f"\n✅ SUCCESS! Agent created with ID: {agent.id}")
    
    # Test if we can retrieve the agent
    retrieved = client.agents.get_agent(agent.id)
    print(f"✅ Agent retrieved successfully")
    print(f"Tools: {json.dumps(retrieved.tools, indent=2)}")
    
except Exception as e:
    print(f"\n❌ FAILED: {str(e)}")
    
    # Try without auth
    print("\nTrying without auth field...")
    tools_no_auth = [{
        "type": "openapi", 
        "openapi": {
            "name": "north_star_api",
            "spec": spec
        }
    }]
    
    try:
        agent = client.agents.create_agent(
            model="gpt-35-turbo",
            name=f"SimpleOpenAPINoAuth-{int(time.time())}",
            instructions="Use executeOperation to handle requests.",
            tools=tools_no_auth
        )
        print(f"✅ SUCCESS without auth! Agent ID: {agent.id}")
    except Exception as e2:
        print(f"❌ Also failed: {str(e2)}")