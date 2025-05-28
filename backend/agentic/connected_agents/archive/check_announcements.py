#!/usr/bin/env python3
"""
Check if delegation announcements are still working.
"""

import asyncio
import os
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from azure.identity.aio import DefaultAzureCredential
from azure.ai.projects.aio import AIProjectClient
from semantic_kernel.agents import AzureAIAgent

# Configure logging to show all response parts
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

async def check_announcements():
    """Check if orchestrator announces delegations."""
    
    orchestrator_id = os.getenv("MAIN_ORCHESTRATOR_AGENT_ID")
    endpoint = os.getenv("AZURE_AI_PROJECT_CONNECTION_STRING")
    
    async with DefaultAzureCredential() as credential, \
               AIProjectClient(endpoint=endpoint, credential=credential) as client:
        
        # Get orchestrator
        orchestrator_def = await client.agents.get_agent(agent_id=orchestrator_id)
        orchestrator_agent = AzureAIAgent(client=client, definition=orchestrator_def)
        
        # Test 1: Greeting
        logger.info("\n" + "="*70)
        logger.info("TEST 1: GREETING REQUEST")
        logger.info("="*70)
        
        response_parts = []
        async for part in orchestrator_agent.invoke(messages="Hello there!"):
            if hasattr(part, 'content') and part.content:
                content = str(part.content)
                response_parts.append(content)
                logger.info(f"PART: {content}")
        
        full_response = "".join(response_parts)
        logger.info(f"\nFULL RESPONSE: {full_response}")
        
        if "greeting specialist" in full_response.lower():
            logger.info("✅ Greeting announcement found!")
        else:
            logger.info("❌ No greeting announcement found")
            
        # Test 2: Calculation
        logger.info("\n" + "="*70)
        logger.info("TEST 2: CALCULATION REQUEST")
        logger.info("="*70)
        
        response_parts = []
        async for part in orchestrator_agent.invoke(messages="What is 35 plus 65?"):
            if hasattr(part, 'content') and part.content:
                content = str(part.content)
                response_parts.append(content)
                logger.info(f"PART: {content}")
        
        full_response = "".join(response_parts)
        logger.info(f"\nFULL RESPONSE: {full_response}")
        
        if "calculation expert" in full_response.lower() or "mathematical" in full_response.lower():
            logger.info("✅ Calculator announcement found!")
        else:
            logger.info("❌ No calculator announcement found")

if __name__ == "__main__":
    asyncio.run(check_announcements())