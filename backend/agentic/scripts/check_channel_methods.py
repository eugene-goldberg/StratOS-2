#!/usr/bin/env python3
"""
Check available methods on AzureAIChannel.
"""

import os
import asyncio
import json
from dotenv import load_dotenv

from azure.identity.aio import DefaultAzureCredential
from semantic_kernel.agents import AzureAIAgent, AzureAIAgentSettings

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

async def check_channel():
    """Check channel methods."""
    # Configuration
    endpoint = os.getenv("AZURE_AI_AGENT_ENDPOINT")
    api_version = os.getenv("AZURE_AI_AGENT_API_VERSION", "2024-12-01-preview")
    model_deployment = os.getenv("AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME", "gpt-35-turbo")
    
    # Load agent configurations
    config_path = os.path.join(
        os.path.dirname(__file__), '..', 
        'deployment_configs', 
        'ai_project_agents_deployment.json'
    )
    
    with open(config_path, 'r') as f:
        data = json.load(f)
        agent_configs = data.get('deployed_agents', {})
    
    agent_id = agent_configs.get("StrategicContextRouter")
    
    try:
        # Create settings and credential
        settings = AzureAIAgentSettings(
            endpoint=endpoint,
            api_version=api_version,
            model_deployment_name=model_deployment
        )
        credential = DefaultAzureCredential()
        
        # Create client
        async with AzureAIAgent.create_client(credential=credential, settings=settings) as client:
            # Get agent
            agent_definition = await client.agents.get_agent(agent_id)
            agent = AzureAIAgent(client=client, definition=agent_definition)
            
            # Create channel
            channel = await agent.create_channel()
            
            print("Channel type:", type(channel).__name__)
            print("\nAvailable methods:")
            for attr in dir(channel):
                if not attr.startswith('_'):
                    print(f"  - {attr}")
                    
            # Check if it has specific attributes
            print("\nChecking specific attributes:")
            for method in ['invoke', 'receive', 'send', 'get_history', 'add_message', 'reset']:
                has_it = hasattr(channel, method)
                print(f"  - {method}: {has_it}")
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(check_channel())