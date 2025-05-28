#!/usr/bin/env python3
"""
Simple test for weather agent with real API functionality.
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

async def test_weather_agent():
    """Test the weather agent with US cities."""
    
    orchestrator_id = os.getenv("MAIN_ORCHESTRATOR_AGENT_ID")
    if not orchestrator_id:
        logger.error("MAIN_ORCHESTRATOR_AGENT_ID not found in environment")
        return
        
    logger.info(f"Testing orchestrator: {orchestrator_id}")
    
    # Test with US cities where weather.gov API works
    test_query = "What's the weather like in Seattle, Washington?"
    
    endpoint = os.getenv("AZURE_AI_PROJECT_CONNECTION_STRING")
    
    async with DefaultAzureCredential() as credential, \
               AIProjectClient(endpoint=endpoint, credential=credential) as client:
        
        logger.info("Successfully created client")
        
        # Get orchestrator definition
        orchestrator_def = await client.agents.get_agent(agent_id=orchestrator_id)
        logger.info(f"Retrieved orchestrator: {orchestrator_def.name}")
        
        # Create agent instance using the full definition
        orchestrator_agent = AzureAIAgent(
            client=client,
            definition=orchestrator_def
        )
        
        logger.info(f"\n{'='*60}")
        logger.info(f"QUERY: {test_query}")
        logger.info("="*60)
        
        response = ""
        async for part in orchestrator_agent.invoke(messages=test_query):
            if hasattr(part, 'content') and part.content:
                response += str(part.content)
        
        logger.info(f"\nRESPONSE:\n{response}")
        
        # Check for proper delegation
        if "weather information specialist" in response.lower():
            logger.info("\n✅ Weather delegation announcement detected!")
        
        if "°f" in response.lower() or "temperature" in response.lower():
            logger.info("✅ Weather information provided!")
        
        # Test with another city
        await asyncio.sleep(3)  # Wait to avoid rate limits
        
        test_query2 = "How's the weather in Miami, Florida?"
        logger.info(f"\n{'='*60}")
        logger.info(f"QUERY: {test_query2}")
        logger.info("="*60)
        
        response2 = ""
        async for part in orchestrator_agent.invoke(messages=test_query2):
            if hasattr(part, 'content') and part.content:
                response2 += str(part.content)
        
        logger.info(f"\nRESPONSE:\n{response2}")

if __name__ == "__main__":
    asyncio.run(test_weather_agent())