#!/usr/bin/env python3
"""
Interact with deployed StratOS agents on Azure AI Agent Service.
Uses the proper Azure AI SDK approach with Semantic Kernel integration.
"""

import asyncio
import os
import sys
import json
from dotenv import load_dotenv

# Add parent directories to path
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
project_root = os.path.dirname(backend_dir)
sys.path.insert(0, backend_dir)

# Load environment variables
load_dotenv(os.path.join(backend_dir, '.env'))

# Import required modules
try:
    from azure.identity.aio import DefaultAzureCredential
    from azure.ai.projects.aio import AIProjectClient
    from semantic_kernel.agents.azure_ai import AzureAIAgent
except ImportError as e:
    print(f"Error importing required modules: {e}")
    print("\nPlease install required packages:")
    print("pip install semantic-kernel[azure] azure-ai-projects azure-identity")
    sys.exit(1)

# Get configuration
AZURE_PROJECT_ENDPOINT = os.getenv('AZURE_AI_PROJECT_HOST')
if AZURE_PROJECT_ENDPOINT and not AZURE_PROJECT_ENDPOINT.startswith('https://'):
    AZURE_PROJECT_ENDPOINT = f"https://{AZURE_PROJECT_ENDPOINT}"

AZURE_PROJECT_RESOURCE_GROUP = os.getenv('AZURE_RESOURCE_GROUP')
AZURE_PROJECT_SUBSCRIPTION_ID = os.getenv('AZURE_SUBSCRIPTION_ID')
AZURE_AI_HUB_NAME = os.getenv('AZURE_AI_HUB_NAME')
AZURE_AI_PROJECT_NAME = os.getenv('AZURE_AI_PROJECT_NAME')

async def load_deployment_info():
    """Load deployment information from saved file"""
    deployment_file = os.path.join(backend_dir, "deployment_configs", "agent_service_deployment.json")
    
    if not os.path.exists(deployment_file):
        print(f"❌ Deployment info not found at: {deployment_file}")
        print("Please run deploy_agents_proper.py first to deploy the agents.")
        return None
    
    with open(deployment_file, 'r') as f:
        return json.load(f)

async def create_agent_client(agent_id, agent_service_client):
    """Create a Semantic Kernel agent client for a deployed agent"""
    # Retrieve the agent definition
    agent_definition = await agent_service_client.agents.get_agent(agent_id)
    
    # Create Semantic Kernel agent instance
    sk_agent = AzureAIAgent(
        client=agent_service_client,
        definition=agent_definition
    )
    
    return sk_agent

async def chat_with_agent(sk_agent, agent_service_client):
    """Interactive chat with an agent"""
    print(f"\nChatting with {sk_agent.name}")
    print("Type 'exit' to quit, 'clear' to start a new conversation")
    print("-" * 50)
    
    # Create a thread for the conversation
    thread = await agent_service_client.agents.create_thread()
    
    try:
        while True:
            user_input = input("\nYou: ").strip()
            
            if user_input.lower() == 'exit':
                break
            elif user_input.lower() == 'clear':
                # Delete old thread and create new one
                await agent_service_client.agents.delete_thread(thread.id)
                thread = await agent_service_client.agents.create_thread()
                print("Started new conversation thread")
                continue
            
            # Add user message to thread
            await sk_agent.add_chat_message(
                thread_id=thread.id,
                message=user_input
            )
            
            # Get agent response
            print(f"\n{sk_agent.name}: ", end="", flush=True)
            
            async for response_chunk in sk_agent.invoke(thread_id=thread.id):
                if response_chunk.content:
                    print(response_chunk.content, end="", flush=True)
            
            print()  # New line after response
            
    finally:
        # Clean up thread
        await agent_service_client.agents.delete_thread(thread.id)

async def main():
    """Main interaction function"""
    print("===== StratOS Agent Interaction =====")
    
    # Load deployment info
    deployment_info = await load_deployment_info()
    if not deployment_info:
        return
    
    print(f"\nFound deployment from: {deployment_info['deployment_time']}")
    print(f"Total agents: {deployment_info['total_agents']}")
    
    try:
        # Create credential and client
        async with DefaultAzureCredential() as credential:
            print("\n✓ Authenticated with Azure")
            
            # Create project connection string
            project_connection_string = f"{AZURE_PROJECT_ENDPOINT};{AZURE_PROJECT_SUBSCRIPTION_ID};{AZURE_PROJECT_RESOURCE_GROUP};{AZURE_AI_HUB_NAME}/{AZURE_AI_PROJECT_NAME}"
            
            # Create project client
            agent_service_client = AIProjectClient.from_connection_string(
                conn_str=project_connection_string,
                credential=credential
            )
            print("✓ Connected to Azure AI Agent Service")
            
            # Display available agents
            print("\nAvailable agents:")
            agent_list = []
            
            for system, agents in deployment_info['agents'].items():
                print(f"\n{system.replace('_', ' ').title()}:")
                for i, (name, agent_id) in enumerate(agents.items()):
                    agent_list.append((name, agent_id, system))
                    print(f"  {len(agent_list)}. {name}")
            
            # Agent selection loop
            while True:
                print("\nSelect an agent by number (or 'exit' to quit):")
                choice = input("> ").strip()
                
                if choice.lower() == 'exit':
                    break
                
                try:
                    agent_index = int(choice) - 1
                    if 0 <= agent_index < len(agent_list):
                        agent_name, agent_id, system = agent_list[agent_index]
                        
                        # Create agent client
                        sk_agent = await create_agent_client(agent_id, agent_service_client)
                        
                        # Chat with the selected agent
                        await chat_with_agent(sk_agent, agent_service_client)
                    else:
                        print("Invalid selection. Please try again.")
                except ValueError:
                    print("Please enter a valid number.")
            
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())