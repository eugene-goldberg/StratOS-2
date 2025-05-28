#!/usr/bin/env python3
"""
Test the weather agent directly to see if it's making API calls.
"""

import asyncio
import os
import logging
from dotenv import load_dotenv
from azure.identity.aio import DefaultAzureCredential
from azure.ai.projects.aio import AIProjectClient
from semantic_kernel.agents import AzureAIAgent

# Configure logging to capture ALL details
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

async def test_weather_direct():
    """Test weather agent directly without orchestrator."""
    
    # Get the weather agent ID from deployment
    weather_agent_id = "asst_OmmrIuA3PfIfczyFtY9ui0xz"  # From deployment output
    
    endpoint = os.getenv("AZURE_AI_PROJECT_CONNECTION_STRING")
    
    async with DefaultAzureCredential() as credential, \
               AIProjectClient(endpoint=endpoint, credential=credential) as client:
        
        logger.info("Getting weather agent directly...")
        
        # Get weather agent definition
        weather_def = await client.agents.get_agent(agent_id=weather_agent_id)
        logger.info(f"Weather Agent: {weather_def.name}")
        logger.info(f"Tools: {weather_def.tools}")
        
        # Create agent instance
        weather_agent = AzureAIAgent(
            client=client,
            definition=weather_def
        )
        
        # Test direct weather query
        query = "Use your code interpreter to fetch the current weather for Seattle from weather.gov API. Show me the code you're running and the actual API response."
        logger.info(f"\nQUERY: {query}")
        
        response = ""
        try:
            async for part in weather_agent.invoke(messages=query):
                if hasattr(part, 'content') and part.content:
                    response += str(part.content)
                    logger.info(f"Partial response: {part.content}")
        except Exception as e:
            logger.error(f"Error: {e}")
            logger.error(f"Error type: {type(e)}")
            if hasattr(e, '__dict__'):
                logger.error(f"Error details: {e.__dict__}")
        
        logger.info(f"\nFINAL RESPONSE:\n{response}")
        
        # Check for evidence of API calls
        if "urllib" in response or "weather.gov" in response:
            logger.info("\n✅ Evidence of weather.gov API usage found!")
        else:
            logger.warning("\n❌ No evidence of weather.gov API usage found")
            
        if "°F" in response or "temperature" in response.lower():
            logger.info("✅ Weather data provided")
        else:
            logger.warning("❌ No weather data found")

if __name__ == "__main__":
    asyncio.run(test_weather_direct())