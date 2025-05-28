"""
Simple test script for North Star Agent
Tests basic functionality of the deployed North Star agent
"""

import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from connected_agents and parent directories
load_dotenv(Path(__file__).parent.parent.parent / '.env')

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from azure.ai.projects.aio import AIProjectClient
from azure.identity.aio import DefaultAzureCredential
from semantic_kernel.agents import AzureAIAgent

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_north_star_agent():
    """Test the North Star agent directly"""
    
    # Get agent ID
    north_star_id = os.getenv("NORTH_STAR_AGENT_ID")
    if not north_star_id:
        logger.error("NORTH_STAR_AGENT_ID not found in environment")
        return
    
    # Get connection string
    connection_string = os.getenv("AZURE_AI_PROJECT_CONNECTION_STRING")
    if not connection_string:
        logger.error("AZURE_AI_PROJECT_CONNECTION_STRING not found in environment")
        return
    
    logger.info(f"Testing North Star Agent ID: {north_star_id}")
    
    async with DefaultAzureCredential() as credential:
        async with AIProjectClient(
            endpoint=connection_string,
            credential=credential
        ) as client:
            try:
                # Get agent definition
                north_star_def = await client.agents.get_agent(agent_id=north_star_id)
                logger.info(f"North Star Agent: {north_star_def.name}")
                
                # Create agent instance
                north_star_agent = AzureAIAgent(
                    client=client,
                    definition=north_star_def
                )
                
                # Test 1: Set organizational purpose
                logger.info("\n" + "="*60)
                logger.info("TEST 1: Set Organizational Purpose")
                logger.info("="*60)
                
                query = "Help me set our organizational purpose. We are a technology company focused on making strategic planning accessible to everyone through AI."
                logger.info(f"Query: {query}")
                
                response = ""
                async for part in north_star_agent.invoke(messages=query):
                    if hasattr(part, 'content') and part.content:
                        response += str(part.content)
                
                logger.info(f"North Star Response:\n{response}\n")
                
                # Test 2: Set vision
                logger.info("\n" + "="*60)
                logger.info("TEST 2: Set Vision Statement")
                logger.info("="*60)
                
                query = "Now let's create a vision statement. By 2030, we want to be the global leader in AI-powered strategic planning."
                logger.info(f"Query: {query}")
                
                response = ""
                async for part in north_star_agent.invoke(messages=query):
                    if hasattr(part, 'content') and part.content:
                        response += str(part.content)
                
                logger.info(f"North Star Response:\n{response}\n")
                
                # Test 3: Add values
                logger.info("\n" + "="*60)
                logger.info("TEST 3: Add Organizational Values")
                logger.info("="*60)
                
                query = "Add these values: Innovation (pushing boundaries), Transparency (open communication), and Customer Focus (user success is our success)"
                logger.info(f"Query: {query}")
                
                response = ""
                async for part in north_star_agent.invoke(messages=query):
                    if hasattr(part, 'content') and part.content:
                        response += str(part.content)
                
                logger.info(f"North Star Response:\n{response}\n")
                
                # Test 4: Create strategic goal
                logger.info("\n" + "="*60)
                logger.info("TEST 4: Create Strategic Goal")
                logger.info("="*60)
                
                query = "Create a strategic goal: Achieve 1 million active users by Q4 2026"
                logger.info(f"Query: {query}")
                
                response = ""
                async for part in north_star_agent.invoke(messages=query):
                    if hasattr(part, 'content') and part.content:
                        response += str(part.content)
                
                logger.info(f"North Star Response:\n{response}\n")
                
                # Test 5: Get summary
                logger.info("\n" + "="*60)
                logger.info("TEST 5: Get North Star Summary")
                logger.info("="*60)
                
                query = "Show me our complete strategic foundation"
                logger.info(f"Query: {query}")
                
                response = ""
                async for part in north_star_agent.invoke(messages=query):
                    if hasattr(part, 'content') and part.content:
                        response += str(part.content)
                
                logger.info(f"North Star Response:\n{response}\n")
                
                logger.info("\n" + "="*60)
                logger.info("North Star Agent Test Completed Successfully!")
                logger.info("="*60)
                
            except Exception as e:
                logger.error(f"Error testing North Star agent: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(test_north_star_agent())