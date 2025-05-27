#!/usr/bin/env python3
"""
Simple test script to interact with the deployed MainOrchestratorAgent
"""

import asyncio
import os
import sys
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Path setup
current_dir = os.path.dirname(os.path.abspath(__file__))
agentic_dir = os.path.dirname(current_dir) 
env_path = os.path.join(agentic_dir, '.env')

logger.info(f"Loading .env from: {env_path}")
load_dotenv(env_path)

# Import required modules
try:
    from azure.identity.aio import DefaultAzureCredential
    from semantic_kernel.agents import AzureAIAgent, AzureAIAgentSettings
    from semantic_kernel.contents import ChatMessageContent
except ImportError as e:
    logger.error(f"Error importing required modules: {e}")
    sys.exit(1)

async def test_orchestrator():
    """Test the deployed MainOrchestratorAgent"""
    
    # Known orchestrator ID from deployment
    orchestrator_agent_id = "asst_LgNjAIwEDV5wQcogIUmGf4qq"
    
    # Test messages
    test_messages = [
        "I need to record my thoughts about the market downturn and its effect on Q3 projections.",
        "What is our company's core vision statement?",
        "Perform a SWOT analysis for the new Alpha project."
    ]
    
    try:
        settings = AzureAIAgentSettings()
        logger.info(f"Settings - Endpoint: {settings.endpoint}")
        logger.info(f"Settings - Model: {settings.model_deployment_name}")
        
        async with DefaultAzureCredential(exclude_interactive_browser_credential=False) as credential:
            async with AzureAIAgent.create_client(credential=credential, settings=settings) as service_client:
                logger.info("Successfully created Azure AI Agent service client")
                
                # Get agent definition
                agent_definition = await service_client.agents.get_agent(agent_id=orchestrator_agent_id)
                logger.info(f"Found agent: {agent_definition.name} (ID: {agent_definition.id})")
                
                # Create SK agent
                sk_orchestrator = AzureAIAgent(
                    client=service_client,
                    definition=agent_definition
                )
                
                # Test each message
                for test_message in test_messages:
                    print(f"\n{'='*60}")
                    print(f"User: {test_message}")
                    print(f"Orchestrator: ", end="", flush=True)
                    
                    # Create thread
                    thread = await service_client.assistants.create_thread()
                    thread_id = thread.id
                    
                    try:
                        # Get response
                        full_response = ""
                        async for chunk in sk_orchestrator.invoke(message=test_message, thread_id=thread_id):
                            if isinstance(chunk, ChatMessageContent) and chunk.content:
                                print(chunk.content, end="", flush=True)
                                full_response += chunk.content
                            elif isinstance(chunk, list) and chunk and isinstance(chunk[0], ChatMessageContent) and chunk[0].content:
                                print(chunk[0].content, end="", flush=True)
                                full_response += chunk[0].content
                        print()
                        logger.info(f"Response received (length: {len(full_response)})")
                        
                    finally:
                        # Clean up thread
                        await service_client.assistants.delete_thread(thread_id=thread_id)
                        logger.info(f"Thread {thread_id} deleted")
                        
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(test_orchestrator())