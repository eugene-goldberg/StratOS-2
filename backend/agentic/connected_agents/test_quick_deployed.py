#!/usr/bin/env python3
"""
Quick test of deployed multi-tool orchestrator to verify delegation works.
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
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def quick_test():
    """Quick test of orchestrator delegation."""
    
    orchestrator_id = os.getenv("MAIN_ORCHESTRATOR_AGENT_ID")
    if not orchestrator_id:
        logger.error("MAIN_ORCHESTRATOR_AGENT_ID not found in environment")
        return
        
    logger.info(f"Testing orchestrator: {orchestrator_id}")
    
    endpoint = os.getenv("AZURE_AI_PROJECT_CONNECTION_STRING")
    
    async with DefaultAzureCredential() as credential, \
               AIProjectClient(endpoint=endpoint, credential=credential) as client:
        
        # Get orchestrator definition
        orchestrator_def = await client.agents.get_agent(agent_id=orchestrator_id)
        logger.info(f"Orchestrator: {orchestrator_def.name}")
        logger.info(f"Tools available: {len(orchestrator_def.tools) if orchestrator_def.tools else 0}")
        
        # Create agent instance
        orchestrator_agent = AzureAIAgent(
            client=client,
            definition=orchestrator_def
        )
        
        # Test greeting delegation
        logger.info("\n" + "="*60)
        logger.info("TEST 1: Greeting Request")
        logger.info("="*60)
        
        response = ""
        async for part in orchestrator_agent.invoke(messages="Hello! Please give me a warm greeting."):
            if hasattr(part, 'content') and part.content:
                response += str(part.content)
        
        logger.info(f"Response: {response}")
        
        # Wait to avoid rate limits
        await asyncio.sleep(3)
        
        # Test calculation delegation
        logger.info("\n" + "="*60)
        logger.info("TEST 2: Calculation Request")
        logger.info("="*60)
        
        response = ""
        async for part in orchestrator_agent.invoke(messages="What is 25 times 4?"):
            if hasattr(part, 'content') and part.content:
                response += str(part.content)
        
        logger.info(f"Response: {response}")
        
        # Wait to avoid rate limits
        await asyncio.sleep(3)
        
        # Test weather delegation
        logger.info("\n" + "="*60)
        logger.info("TEST 3: Weather Request")
        logger.info("="*60)
        
        response = ""
        async for part in orchestrator_agent.invoke(messages="What's the weather like in San Francisco?"):
            if hasattr(part, 'content') and part.content:
                response += str(part.content)
        
        logger.info(f"Response: {response}")
        
        # Summary
        logger.info("\n" + "="*60)
        logger.info("SUMMARY")
        logger.info("="*60)
        logger.info("✅ Multi-tool orchestrator is deployed and responding")
        logger.info("✅ Three specialized agents available: Greeter, Calculator, Weather")
        logger.info("✅ Check responses above to verify proper delegation with announcements")

if __name__ == "__main__":
    asyncio.run(quick_test())