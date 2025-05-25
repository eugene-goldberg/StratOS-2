#!/usr/bin/env python3
"""
Test CEO Log Agent interaction.
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

async def test_ceo_log_agent():
    """Test interaction with CEO Log Agent."""
    print("Testing CEO Log Agent...\n")
    
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
    
    # Get CEO Log Agent
    agent_name = "CEOLogAgent"
    agent_id = agent_configs.get(agent_name)
    
    if not agent_id:
        print(f"Agent '{agent_name}' not found in deployment configuration.")
        return
    
    print(f"Agent ID: {agent_id}")
    
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
            print(f"Retrieving agent '{agent_name}'...")
            agent_definition = await client.agents.get_agent(agent_id)
            print(f"Agent Name: {agent_definition.name}")
            print(f"Description: {agent_definition.description}")
            print(f"Instructions Preview: {agent_definition.instructions[:200]}...")
            
            # Create agent instance
            agent = AzureAIAgent(
                client=client,
                definition=agent_definition
            )
            
            # Create channel (which creates or uses a thread)
            channel = await agent.create_channel()
            print(f"\nChannel created")
            
            # Test message
            test_message = """
            Today we had a pivotal board meeting. Key outcomes:
            1. Approved $15M funding for AI expansion initiative
            2. Decided to enter the European market by Q3
            3. Customer retention improved by 12% this quarter
            
            The team morale is high, and our strategic partnerships are paying off.
            """
            
            print(f"\nSending message to {agent_name}:")
            print(test_message)
            
            # Send message and get response using the channel
            from semantic_kernel.contents import ChatMessageContent, AuthorRole
            user_message = ChatMessageContent(role=AuthorRole.USER, content=test_message)
            
            print(f"\n{agent_name} Response:")
            print("-" * 50)
            
            # Invoke the agent through the channel
            async for response in channel.invoke(agent):
                if hasattr(response, 'content') and response.content:
                    print(response.content, end="", flush=True)
            
            print("\n" + "-" * 50)
            
            # Test another message
            test_message2 = "What patterns do you see in my recent log entries?"
            print(f"\nSending follow-up: {test_message2}")
            
            user_message2 = ChatMessageContent(role=AuthorRole.USER, content=test_message2)
            
            print(f"\n{agent_name} Response:")
            print("-" * 50)
            
            async for response in channel.invoke(agent):
                if hasattr(response, 'content') and response.content:
                    print(response.content, end="", flush=True)
            
            print("\n" + "-" * 50)
            
            print(f"\nTest completed successfully!")
            print(f"Timestamp: {datetime.now().isoformat()}")
            
    except Exception as e:
        print(f"\nError: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_ceo_log_agent())