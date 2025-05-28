#!/usr/bin/env python3
"""
Very simple weather test - just one query.
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

async def test_weather():
    """Test weather with a simple query."""
    
    orchestrator_id = os.getenv("MAIN_ORCHESTRATOR_AGENT_ID")
    if not orchestrator_id:
        logger.error("MAIN_ORCHESTRATOR_AGENT_ID not found in environment")
        return
        
    endpoint = os.getenv("AZURE_AI_PROJECT_CONNECTION_STRING")
    
    async with DefaultAzureCredential() as credential, \
               AIProjectClient(endpoint=endpoint, credential=credential) as client:
        
        # Get orchestrator definition
        orchestrator_def = await client.agents.get_agent(agent_id=orchestrator_id)
        logger.info(f"Testing with orchestrator: {orchestrator_def.name}")
        
        # Create agent instance
        orchestrator_agent = AzureAIAgent(
            client=client,
            definition=orchestrator_def
        )
        
        # Simple test
        query = "What's the current weather in New York City?"
        logger.info(f"\nQUERY: {query}")
        
        response = ""
        async for part in orchestrator_agent.invoke(messages=query):
            if hasattr(part, 'content') and part.content:
                response += str(part.content)
        
        logger.info(f"\nRESPONSE:\n{response}")

if __name__ == "__main__":
    asyncio.run(test_weather())