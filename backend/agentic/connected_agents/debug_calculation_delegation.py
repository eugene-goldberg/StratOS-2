#!/usr/bin/env python3
"""
Debug why calculation delegation doesn't include announcement.
"""

import asyncio
import os
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import Azure SDK components
from azure.identity.aio import DefaultAzureCredential
from azure.ai.projects.aio import AIProjectClient
from semantic_kernel.agents import AzureAIAgent

# Configure logging to show all details
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

async def debug_delegation():
    """Debug calculation delegation."""
    
    orchestrator_id = os.getenv("MAIN_ORCHESTRATOR_AGENT_ID")
    endpoint = os.getenv("AZURE_AI_PROJECT_CONNECTION_STRING")
    
    async with DefaultAzureCredential() as credential, \
               AIProjectClient(endpoint=endpoint, credential=credential) as client:
        
        # Get orchestrator definition
        orchestrator_def = await client.agents.get_agent(agent_id=orchestrator_id)
        logger.info(f"Orchestrator: {orchestrator_def.name}")
        
        # Log instructions to verify they're correct
        logger.info("=" * 70)
        logger.info("ORCHESTRATOR INSTRUCTIONS:")
        logger.info("-" * 70)
        logger.info(orchestrator_def.instructions[:500] + "...")  # First 500 chars
        logger.info("=" * 70)
        
        # Create agent instance
        orchestrator_agent = AzureAIAgent(
            client=client,
            definition=orchestrator_def
        )
        
        # Test greeting first (which we know works)
        logger.info("\nTEST 1: Greeting (Expected to work with announcement)")
        logger.info("-" * 70)
        
        response = ""
        async for part in orchestrator_agent.invoke(messages="Hi there!"):
            if hasattr(part, 'content') and part.content:
                content = str(part.content)
                response += content
                logger.info(f"PART: {content}")
        
        logger.info("-" * 70)
        
        # Test calculation
        logger.info("\nTEST 2: Calculation (Should announce but doesn't)")
        logger.info("-" * 70)
        
        response = ""
        async for part in orchestrator_agent.invoke(messages="What is 15 + 25?"):
            if hasattr(part, 'content') and part.content:
                content = str(part.content)
                response += content
                logger.info(f"PART: {content}")
        
        logger.info("-" * 70)

if __name__ == "__main__":
    asyncio.run(debug_delegation())