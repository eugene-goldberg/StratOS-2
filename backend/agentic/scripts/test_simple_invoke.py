#!/usr/bin/env python3
"""
Test simplest possible agent invocation.
"""

import asyncio
import os
import logging
from dotenv import load_dotenv

from azure.identity.aio import DefaultAzureCredential
from semantic_kernel.agents import AzureAIAgent, AzureAIAgentSettings
from semantic_kernel.contents import ChatMessageContent

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment
current_dir = os.path.dirname(os.path.abspath(__file__))
agentic_dir = os.path.dirname(current_dir) 
load_dotenv(os.path.join(agentic_dir, '.env'))

async def test_agent():
    """Test simplest agent invocation."""
    
    # CEO Log Agent ID
    agent_id = "asst_N5azTOnrhdlm4K9wC6i9OtHA"
    
    try:
        # Create settings
        settings = AzureAIAgentSettings()
        logger.info(f"Settings: endpoint={settings.endpoint}, model={settings.model_deployment_name}")
        
        # Create credential and client
        async with DefaultAzureCredential(exclude_interactive_browser_credential=False) as credential:
            async with AzureAIAgent.create_client(credential=credential, settings=settings) as client:
                logger.info("Client created successfully")
                
                # Get agent
                agent_def = await client.agents.get_agent(agent_id=agent_id)
                logger.info(f"Got agent: {agent_def.name}")
                
                # Create SK agent
                agent = AzureAIAgent(client=client, definition=agent_def)
                logger.info("SK agent created")
                
                # Try to invoke without thread_id (let it create one)
                message = "Today we secured a major partnership with Microsoft. This will transform our cloud infrastructure capabilities."
                
                print(f"\nUser: {message}")
                print(f"\nAgent: ", end="", flush=True)
                
                try:
                    # Try invoke without thread_id to see if it creates one automatically
                    async for chunk in agent.invoke(message=message):
                        if isinstance(chunk, ChatMessageContent) and chunk.content:
                            print(chunk.content, end="", flush=True)
                except Exception as e:
                    logger.error(f"Invoke error: {type(e).__name__}: {e}")
                    
                    # Try with an empty thread_id
                    logger.info("Trying with thread_id=None")
                    async for chunk in agent.invoke(message=message, thread_id=None):
                        if isinstance(chunk, ChatMessageContent) and chunk.content:
                            print(chunk.content, end="", flush=True)
                
                print("\n\nTest completed!")
                
    except Exception as e:
        logger.error(f"Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_agent())