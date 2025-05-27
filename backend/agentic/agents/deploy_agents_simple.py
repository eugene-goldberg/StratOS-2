#!/usr/bin/env python3
"""
Simple agent deployment script using Azure AI Agent Service REST API
"""
import os
import json
import requests
from dotenv import load_dotenv
from azure.identity import ClientSecretCredential

# Load environment variables
load_dotenv()

# Get credentials from environment
TENANT_ID = os.getenv("AZURE_TENANT_ID")
CLIENT_ID = os.getenv("AZURE_CLIENT_ID")
CLIENT_SECRET = os.getenv("AZURE_CLIENT_SECRET")
AGENT_ENDPOINT = os.getenv("AZURE_AI_AGENT_ENDPOINT")
API_VERSION = os.getenv("AZURE_AI_AGENT_API_VERSION", "2024-12-01-preview")
MODEL_NAME = os.getenv("AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME", "gpt-35-turbo")

def get_access_token():
    """Get access token using service principal"""
    credential = ClientSecretCredential(
        tenant_id=TENANT_ID,
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET
    )
    # Try management scope first
    token = credential.get_token("https://management.azure.com/.default")
    return token.token

def create_agent(name, instructions, tools=None):
    """Create an agent using REST API"""
    token = get_access_token()
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "name": name,
        "instructions": instructions,
        "model": MODEL_NAME,
        "tools": tools or []
    }
    
    url = f"{AGENT_ENDPOINT}/assistants?api-version={API_VERSION}"
    
    print(f"Creating {name}...")
    print(f"URL: {url}")
    
    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code == 200 or response.status_code == 201:
        agent_data = response.json()
        print(f"✓ Successfully created {name} with ID: {agent_data.get('id')}")
        return agent_data
    else:
        print(f"✗ Failed to create {name}: {response.status_code}")
        print(f"Response: {response.text}")
        return None

def main():
    """Deploy all agents"""
    print("Starting agent deployment...")
    print(f"Endpoint: {AGENT_ENDPOINT}")
    print(f"Model: {MODEL_NAME}")
    
    agents = {}
    
    # Create Chat Agent
    chat_agent = create_agent(
        "ChatAgent",
        "You are a helpful assistant that provides friendly, concise, and accurate information. "
        "You should be conversational but prioritize accuracy and brevity over verbosity."
    )
    if chat_agent:
        agents["chat_agent_id"] = chat_agent.get("id")
    
    # Create Weather Agent
    weather_agent = create_agent(
        "WeatherAgent",
        "You are a weather specialist agent that provides accurate and helpful weather information. "
        "When asked about weather, provide current conditions and brief forecasts.",
        tools=[{
            "type": "function",
            "function": {
                "name": "GetWeather",
                "description": "Get weather information for a location",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {"type": "string", "description": "The city/location"}
                    },
                    "required": ["location"]
                }
            }
        }]
    )
    if weather_agent:
        agents["weather_agent_id"] = weather_agent.get("id")
    
    # Create Calculator Agent
    calculator_agent = create_agent(
        "CalculatorAgent",
        "You are a calculator specialist agent that performs mathematical operations. "
        "You can handle basic arithmetic and advanced calculations.",
        tools=[{
            "type": "function",
            "function": {
                "name": "Calculate",
                "description": "Perform mathematical calculations",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "expression": {"type": "string", "description": "Mathematical expression"}
                    },
                    "required": ["expression"]
                }
            }
        }]
    )
    if calculator_agent:
        agents["calculator_agent_id"] = calculator_agent.get("id")
    
    # Create Orchestrator Agent
    orchestrator_agent = create_agent(
        "OrchestratorAgent",
        "You are an orchestrator that routes requests to appropriate specialist agents. "
        "Analyze the user's request and determine which agent to use.",
        tools=[
            {
                "type": "function",
                "function": {
                    "name": "RouteToAgent",
                    "description": "Route to chat agent for general queries",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "User query"}
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "GetWeather",
                    "description": "Get weather information",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "location": {"type": "string", "description": "Location"}
                        },
                        "required": ["location"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "Calculate",
                    "description": "Perform calculations",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "expression": {"type": "string", "description": "Math expression"}
                        },
                        "required": ["expression"]
                    }
                }
            }
        ]
    )
    if orchestrator_agent:
        agents["orchestrator_agent_id"] = orchestrator_agent.get("id")
    
    # Save deployment info
    if agents:
        with open("simple_deployment_info.json", "w") as f:
            json.dump(agents, f, indent=2)
        print(f"\n✓ Deployment info saved to simple_deployment_info.json")
        print(f"Deployed agents: {list(agents.keys())}")
    else:
        print("\n✗ No agents were successfully deployed")

if __name__ == "__main__":
    main()