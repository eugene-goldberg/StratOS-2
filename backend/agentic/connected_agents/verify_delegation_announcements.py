#!/usr/bin/env python3
"""
Verify that orchestrator announces delegation before invoking tools.
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

async def verify_delegation():
    """Verify orchestrator announces delegation."""
    
    orchestrator_id = os.getenv("MAIN_ORCHESTRATOR_AGENT_ID")
    if not orchestrator_id:
        logger.error("MAIN_ORCHESTRATOR_AGENT_ID not found in environment")
        return
        
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
        
        # Test calculation delegation
        logger.info("\n" + "="*70)
        logger.info("TESTING: Calculate 50 + 30")
        logger.info("="*70)
        logger.info("EXPECTED: Orchestrator should announce delegation before calculating")
        logger.info("-"*70)
        
        full_response = ""
        response_parts = []
        async for part in orchestrator_agent.invoke(messages="Calculate 50 + 30 for me please"):
            if hasattr(part, 'content') and part.content:
                content = str(part.content)
                response_parts.append(content)
                full_response += content
                logger.info(f"PART: {content}")
        
        logger.info("-"*70)
        logger.info(f"FULL RESPONSE: {full_response}")
        logger.info("-"*70)
        
        # Check for announcement
        if "calculation expert" in full_response.lower() or "mathematical" in full_response.lower():
            logger.info("✅ SUCCESS: Orchestrator announced delegation to calculator!")
        else:
            logger.warning("❌ WARNING: No clear delegation announcement found")
            
        # Check for calculation result
        if "80" in full_response:
            logger.info("✅ SUCCESS: Calculation result (80) found!")
        else:
            logger.warning("❌ WARNING: Calculation result not found")

if __name__ == "__main__":
    asyncio.run(verify_delegation())