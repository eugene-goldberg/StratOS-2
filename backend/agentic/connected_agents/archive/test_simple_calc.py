#!/usr/bin/env python3
"""
Simple test to see full calculation delegation response.
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

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

async def test_calc():
    """Test calculation delegation."""
    
    orchestrator_id = os.getenv("MAIN_ORCHESTRATOR_AGENT_ID")
    endpoint = os.getenv("AZURE_AI_PROJECT_CONNECTION_STRING")
    
    async with DefaultAzureCredential() as credential, \
               AIProjectClient(endpoint=endpoint, credential=credential) as client:
        
        # Get orchestrator definition
        orchestrator_def = await client.agents.get_agent(agent_id=orchestrator_id)
        
        # Create agent instance
        orchestrator_agent = AzureAIAgent(
            client=client,
            definition=orchestrator_def
        )
        
        # Single calculation test
        logger.info("USER: Please calculate 100 divided by 4")
        logger.info("-" * 50)
        
        full_response = ""
        part_count = 0
        async for part in orchestrator_agent.invoke(messages="Please calculate 100 divided by 4"):
            if hasattr(part, 'content') and part.content:
                content = str(part.content)
                part_count += 1
                logger.info(f"RESPONSE PART {part_count}: {content}")
                full_response += content
        
        logger.info("-" * 50)
        logger.info(f"FULL RESPONSE: {full_response}")
        logger.info("-" * 50)
        
        # Check what we got
        if "mathematical calculation expert" in full_response.lower() or "calculation expert" in full_response.lower():
            logger.info("✅ Found announcement about calculation expert")
        else:
            logger.info("❌ No announcement about calculation expert found")
            
        if "25" in full_response:
            logger.info("✅ Found correct result (25)")
        else:
            logger.info("❌ Result not found or incorrect")

if __name__ == "__main__":
    asyncio.run(test_calc())