#!/usr/bin/env python3
"""
Simple test of Azure AI Agent interaction using channels.
"""

import os
import asyncio
import json
from dotenv import load_dotenv
from datetime import datetime

from azure.identity.aio import DefaultAzureCredential
from semantic_kernel.agents import AzureAIAgent, AzureAIAgentSettings
from semantic_kernel.contents import ChatMessageContent, AuthorRole

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

async def test_agent():
    """Test basic agent interaction."""
    print("Azure AI Agent Test\n")
    
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
    
    # Test with Strategic Context Router
    agent_name = "StrategicContextRouter"
    agent_id = agent_configs.get(agent_name)
    
    if not agent_id:
        print(f"Agent '{agent_name}' not found")
        return
        
    print(f"Testing with: {agent_name}")
    print(f"Agent ID: {agent_id}\n")
    
    try:
        # Create settings
        settings = AzureAIAgentSettings(
            endpoint=endpoint,
            api_version=api_version,
            model_deployment_name=model_deployment
        )
        
        # Create credential
        credential = DefaultAzureCredential()
        
        # Create client
        async with AzureAIAgent.create_client(credential=credential, settings=settings) as client:
            print("Connected to Azure AI Agent Service")
            
            # Get agent definition
            agent_definition = await client.agents.get_agent(agent_id)
            print(f"Retrieved: {agent_definition.name}")
            
            # Create agent instance
            agent = AzureAIAgent(
                client=client,
                definition=agent_definition
            )
            
            # Create a channel for communication
            channel = await agent.create_channel()
            print("Channel created\n")
            
            # Test message
            test_message = "What are our strategic priorities for this quarter?"
            print(f"User: {test_message}")
            
            # Create user message
            user_msg = ChatMessageContent(
                role=AuthorRole.USER,
                content=test_message
            )
            
            # Add message to channel
            await channel.add_message(user_msg)
            
            # Get response
            print(f"\n{agent_name}:")
            async for msg in channel.get_messages():
                if msg.role == AuthorRole.ASSISTANT:
                    print(msg.content)
                    break
                    
            print(f"\nTest completed at {datetime.now().isoformat()}")
            
    except Exception as e:
        print(f"Error: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_agent())