#!/usr/bin/env python3
"""
Test CEO Log Agent using Semantic Kernel SDK
"""

import os
import sys
import asyncio
import logging
from datetime import datetime
from dotenv import load_dotenv

from azure.identity.aio import DefaultAzureCredential
from azure.ai.projects.aio import AIProjectClient
from semantic_kernel.agents import AzureAIAgent

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# CEO Log Agent ID from deployment
CEO_LOG_AGENT_ID = "asst_85MtpKLDOQA9ttsUckByGTKD"

async def test_ceo_log_agent():
    """Test CEO Log Agent with save entry request."""
    
    logger.info("Testing CEO Log Agent with Semantic Kernel SDK")
    logger.info("="*60)
    
    # Get connection string
    endpoint = os.getenv("AZURE_AI_PROJECT_CONNECTION_STRING")
    if not endpoint:
        logger.error("AZURE_AI_PROJECT_CONNECTION_STRING not set")
        return
    
    logger.info(f"Agent ID: {CEO_LOG_AGENT_ID}")
    
    try:
        # Create credential and client
        credential = DefaultAzureCredential()
        
        async with AIProjectClient(endpoint=endpoint, credential=credential) as client:
            logger.info("Connected to Azure AI Project")
            
            # Get the agent definition
            logger.info(f"Retrieving CEO Log Agent...")
            agent_definition = await client.agents.get_agent(CEO_LOG_AGENT_ID)
            logger.info(f"Agent Name: {agent_definition.name}")
            logger.info(f"Model: {agent_definition.model}")
            
            # Create agent instance
            agent = AzureAIAgent(
                client=client,
                definition=agent_definition
            )
            
            # Create channel (which creates or uses a thread)
            channel = await agent.create_channel()
            logger.info(f"Channel created")
            
            # Test CEO log entry
            log_entry = """Save this CEO log entry: Had a productive quarterly review meeting with the board today. 
We discussed our AI strategy and the board approved a 30% increase in R&D budget for next quarter. 
The team's morale is high after hitting Q1 targets. Main concern is potential supply chain disruptions 
due to geopolitical tensions. Need to accelerate our supplier diversification initiative.

Category: strategic_planning
User ID: ceo_test_user_001"""
            
            logger.info(f"\nSending CEO log entry:")
            logger.info("-" * 60)
            logger.info(log_entry)
            logger.info("-" * 60)
            
            # Send message and get response
            from semantic_kernel.contents import ChatMessageContent, AuthorRole
            user_message = ChatMessageContent(role=AuthorRole.USER, content=log_entry)
            
            logger.info(f"\nCEO Log Agent Response:")
            logger.info("=" * 60)
            
            # Use invoke to send message and get streaming response
            response_text = ""
            async for message in channel.invoke(user_message):
                if hasattr(message, 'content') and message.content:
                    response_text += str(message.content)
                    print(message.content, end='', flush=True)
            
            logger.info("\n" + "=" * 60)
            
            if response_text:
                logger.info("\n✅ Test completed successfully!")
                logger.info(f"Response length: {len(response_text)} characters")
            else:
                logger.warning("⚠️ No response received from agent")
            
    except Exception as e:
        logger.error(f"Error during test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    logger.info("Starting CEO Log Agent Test")
    logger.info(f"Timestamp: {datetime.now().isoformat()}")
    asyncio.run(test_ceo_log_agent())