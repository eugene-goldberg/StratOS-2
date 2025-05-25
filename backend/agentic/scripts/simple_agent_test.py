#!/usr/bin/env python3
"""
Simple test to interact with a deployed agent.
"""

import os
import sys
import asyncio
import json
from datetime import datetime
from dotenv import load_dotenv

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.agents import AzureAIAgent
from azure.identity import DefaultAzureCredential, get_bearer_token_provider

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

async def test_agent_interaction():
    """Test interaction with a deployed agent."""
    print("Testing agent interaction...\n")
    
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
    
    # Test agent
    test_agent_name = "CEOLogAgent"
    agent_id = agent_configs.get(test_agent_name)
    
    if not agent_id:
        print(f"Agent '{test_agent_name}' not found in deployment configuration.")
        return
    
    print(f"Testing with agent: {test_agent_name} (ID: {agent_id})")
    
    try:
        # Create kernel
        kernel = Kernel()
        
        # Authentication
        credential = DefaultAzureCredential()
        token_provider = get_bearer_token_provider(
            credential, 
            "https://cognitiveservices.azure.com/.default"
        )
        
        # Add Azure OpenAI service
        service_id = "azure_openai_chat"
        kernel.add_service(
            AzureChatCompletion(
                service_id=service_id,
                deployment_name=model_deployment,
                endpoint=endpoint,
                api_version=api_version,
                ad_token_provider=token_provider
            )
        )
        
        print("Retrieving agent...")
        
        # Retrieve the agent
        agent = await AzureAIAgent.retrieve(
            id=agent_id,
            endpoint=endpoint,
            api_version=api_version,
            kernel=kernel,
            ad_token_provider=token_provider
        )
        
        print(f"Agent retrieved: {agent.name}")
        print(f"Description: {agent.description}")
        
        # Create a thread
        print("\nCreating conversation thread...")
        thread = await agent.create_thread()
        print(f"Thread created: {thread.id}")
        
        # Send a message
        test_message = "I had a great meeting with our largest client today. They're interested in expanding our partnership significantly."
        print(f"\nSending message: {test_message}")
        
        await thread.add_user_message(test_message)
        
        # Get response
        print("\nWaiting for agent response...")
        messages = await thread.invoke(agent)
        
        # Extract assistant response
        for message in messages:
            if hasattr(message, 'role') and str(message.role) == 'assistant':
                print(f"\nAgent response: {message.content}")
                break
        
        print(f"\nConversation completed at: {datetime.now().isoformat()}")
        
    except Exception as e:
        print(f"\nError: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_agent_interaction())