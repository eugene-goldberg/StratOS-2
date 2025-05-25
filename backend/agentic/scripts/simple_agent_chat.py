#!/usr/bin/env python3
"""
Simple chat with a deployed agent using Azure AI Agent Service.
"""

import os
import sys
import asyncio
import json
from datetime import datetime
from dotenv import load_dotenv

from azure.identity.aio import DefaultAzureCredential
from semantic_kernel.agents import AzureAIAgent, AzureAIAgentSettings

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

async def chat_with_agent():
    """Chat with a deployed agent."""
    print("StratOS Agent Chat\n")
    
    # Configuration
    endpoint = os.getenv("AZURE_AI_AGENT_ENDPOINT")
    api_version = os.getenv("AZURE_AI_AGENT_API_VERSION", "2024-12-01-preview")
    model_deployment = os.getenv("AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME", "gpt-35-turbo")
    
    # Load agent IDs
    config_path = os.path.join(
        os.path.dirname(__file__), 
        '..', 
        'deployment_configs', 
        'ai_project_agents_deployment.json'
    )
    
    with open(config_path, 'r') as f:
        data = json.load(f)
        agent_configs = data.get('deployed_agents', {})
    
    print("Available agents:")
    for name in sorted(agent_configs.keys()):
        print(f"  - {name}")
    
    # Select agent
    agent_name = input("\nEnter agent name (or press Enter for CEOLogAgent): ").strip()
    if not agent_name:
        agent_name = "CEOLogAgent"
    
    agent_id = agent_configs.get(agent_name)
    if not agent_id:
        print(f"Agent '{agent_name}' not found.")
        return
    
    print(f"\nConnecting to {agent_name}...")
    
    try:
        # Create settings
        settings = AzureAIAgentSettings(
            endpoint=endpoint,
            api_version=api_version,
            model_deployment_name=model_deployment
        )
        
        # Create credential
        credential = DefaultAzureCredential()
        
        # Create client and interact
        async with AzureAIAgent.create_client(credential=credential, settings=settings) as client:
            print("Connected to Azure AI Agent Service")
            
            # Get the agent definition
            agent_definition = await client.agents.get_agent(agent_id)
            print(f"Agent: {agent_definition.name}")
            print(f"Description: {agent_definition.description}")
            
            # Create agent instance
            agent = AzureAIAgent(
                client=client,
                definition=agent_definition
            )
            
            # Create thread
            thread = await agent.create_thread()
            print(f"\nThread created: {thread.id}")
            
            print("\nChat started. Type 'quit' to exit.\n")
            
            while True:
                # Get user input
                user_message = input("You: ").strip()
                
                if user_message.lower() == 'quit':
                    print("Goodbye!")
                    break
                
                if not user_message:
                    continue
                
                # Add user message
                await thread.add_user_message(user_message)
                
                # Get response
                print("Agent: ", end="", flush=True)
                
                # Stream response
                async for message in thread.invoke_stream(agent):
                    if hasattr(message, 'content') and message.content:
                        print(message.content, end="", flush=True)
                
                print("\n")  # New line after response
                
    except Exception as e:
        print(f"\nError: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(chat_with_agent())