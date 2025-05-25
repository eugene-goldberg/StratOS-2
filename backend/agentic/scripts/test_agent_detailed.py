#!/usr/bin/env python3
"""
Detailed test of agent interaction showing all steps.
"""

import asyncio
import os
import logging
from dotenv import load_dotenv
from datetime import datetime

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

async def test_multiple_agents():
    """Test multiple agents with detailed output."""
    
    # Agent IDs from deployment
    agents_to_test = {
        "StrategicContextRouter": "asst_W9JAWsfil7Vr1UsAfR9xs6LH",
        "CEOLogAgent": "asst_N5azTOnrhdlm4K9wC6i9OtHA",
        "NorthStarAgent": "asst_9Cd1I1QCYm6TqvjVeKfdQOkf"
    }
    
    # Test messages
    test_messages = {
        "StrategicContextRouter": "What are our strategic priorities for this quarter?",
        "CEOLogAgent": "I had a meeting with our biggest client today. They want to expand our partnership by 50% next year. This is a game-changer for our revenue projections.",
        "NorthStarAgent": "What is our company vision and core values?"
    }
    
    try:
        # Create settings
        settings = AzureAIAgentSettings()
        logger.info(f"Settings configured: {settings.endpoint}")
        
        # Create credential and client
        async with DefaultAzureCredential(exclude_interactive_browser_credential=False) as credential:
            async with AzureAIAgent.create_client(credential=credential, settings=settings) as client:
                logger.info("Client created successfully")
                
                for agent_name, agent_id in agents_to_test.items():
                    print(f"\n{'='*60}")
                    print(f"Testing: {agent_name}")
                    print(f"{'='*60}")
                    
                    try:
                        # Get agent
                        agent_def = await client.agents.get_agent(agent_id=agent_id)
                        print(f"Agent: {agent_def.name}")
                        print(f"Description: {agent_def.description}")
                        print(f"Model: {agent_def.model}")
                        
                        # Create SK agent
                        agent = AzureAIAgent(client=client, definition=agent_def)
                        
                        # Get test message
                        message = test_messages.get(agent_name, "Hello, how can you help me?")
                        print(f"\nUser: {message}")
                        
                        # Invoke agent
                        print(f"\n{agent_name}: ", end="", flush=True)
                        
                        response_count = 0
                        response_text = ""
                        
                        async for chunk in agent.invoke(message=message):
                            response_count += 1
                            if isinstance(chunk, ChatMessageContent):
                                if chunk.content:
                                    print(chunk.content, end="", flush=True)
                                    response_text += chunk.content
                                # Log chunk details for debugging
                                logger.debug(f"Chunk {response_count}: role={chunk.role}, content_length={len(chunk.content or '')}")
                            else:
                                logger.debug(f"Chunk {response_count}: type={type(chunk)}")
                        
                        if not response_text:
                            print("[No response generated]")
                            logger.warning(f"Agent {agent_name} returned no content after {response_count} chunks")
                        
                        print(f"\n\nResponse complete. Chunks received: {response_count}")
                        
                    except Exception as e:
                        logger.error(f"Error testing {agent_name}: {type(e).__name__}: {e}")
                        print(f"Error: {e}")
                
                print(f"\n{'='*60}")
                print(f"All tests completed at {datetime.now().isoformat()}")
                
    except Exception as e:
        logger.error(f"Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Set debug logging for more details
    # logging.getLogger().setLevel(logging.DEBUG)
    asyncio.run(test_multiple_agents())