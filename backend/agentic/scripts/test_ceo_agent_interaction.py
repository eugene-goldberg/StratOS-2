#!/usr/bin/env python3
"""
Non-interactive test of CEO Log Agent using the working interaction pattern.
"""

import asyncio
import os
import sys
import logging
from datetime import datetime, timezone
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [%(funcName)s] %(message)s')
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

async def test_ceo_log_agent():
    """Test the CEO Log Agent with a predefined message."""
    
    # CEO Log Agent ID from our deployment
    agent_id = "asst_N5azTOnrhdlm4K9wC6i9OtHA"
    user_message = """
    Today we had a pivotal board meeting. Key outcomes:
    1. Approved $15M funding for AI expansion initiative
    2. Decided to enter the European market by Q3
    3. Customer retention improved by 12% this quarter
    
    The team morale is high, and our strategic partnerships are paying off.
    """
    
    logger.info(f"Testing CEO Log Agent (ID: {agent_id})")
    
    try:
        # Create settings
        settings = AzureAIAgentSettings()
        
        logger.info(f"AzureAIAgentSettings initialized:")
        logger.info(f"  Endpoint: {settings.endpoint}")
        logger.info(f"  Model: {settings.model_deployment_name}")
        logger.info(f"  API Version: {settings.api_version}")
        
        if settings.endpoint is None:
            logger.error("CRITICAL: AzureAIAgentSettings did not resolve an endpoint.")
            return
        
        # Create credential and client
        async with DefaultAzureCredential(exclude_interactive_browser_credential=False) as credential:
            async with AzureAIAgent.create_client(credential=credential, settings=settings) as service_client:
                logger.info("Successfully created Azure AI Agent service client")
                
                # Get agent definition
                logger.info("Fetching CEO Log Agent definition...")
                agent_definition = await service_client.agents.get_agent(agent_id=agent_id)
                logger.info(f"Agent: {agent_definition.name}")
                logger.info(f"Description: {agent_definition.description}")
                
                # Create SK agent instance
                sk_agent = AzureAIAgent(
                    client=service_client,
                    definition=agent_definition
                )
                
                # Create thread
                logger.info("Creating conversation thread...")
                thread_response = await service_client.threads.create_thread()
                thread_id = thread_response.id
                logger.info(f"Thread ID: {thread_id}")
                
                # Send message and get response
                print("\n" + "="*60)
                print("CEO LOG AGENT TEST")
                print("="*60)
                print(f"\nUser: {user_message}")
                print(f"\nCEO Log Agent: ", end="", flush=True)
                
                # Stream response
                response_text = ""
                async for message_chunk in sk_agent.invoke(message=user_message, thread_id=thread_id):
                    if isinstance(message_chunk, ChatMessageContent) and message_chunk.content:
                        print(message_chunk.content, end="", flush=True)
                        response_text += message_chunk.content
                    elif isinstance(message_chunk, list) and message_chunk and isinstance(message_chunk[0], ChatMessageContent) and message_chunk[0].content:
                        print(message_chunk[0].content, end="", flush=True)
                        response_text += message_chunk[0].content
                
                print("\n" + "="*60)
                
                # Test a follow-up question
                follow_up = "What are the key tags and themes from this entry?"
                print(f"\nUser: {follow_up}")
                print(f"\nCEO Log Agent: ", end="", flush=True)
                
                async for message_chunk in sk_agent.invoke(message=follow_up, thread_id=thread_id):
                    if isinstance(message_chunk, ChatMessageContent) and message_chunk.content:
                        print(message_chunk.content, end="", flush=True)
                    elif isinstance(message_chunk, list) and message_chunk and isinstance(message_chunk[0], ChatMessageContent) and message_chunk[0].content:
                        print(message_chunk[0].content, end="", flush=True)
                
                print("\n" + "="*60)
                
                # Clean up thread
                logger.info(f"Deleting thread: {thread_id}")
                await service_client.threads.delete_thread(thread_id=thread_id)
                logger.info("Thread deleted successfully")
                
                print(f"\nTest completed successfully at {datetime.now().isoformat()}")
                
    except Exception as e:
        logger.error(f"Error during test: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(test_ceo_log_agent())