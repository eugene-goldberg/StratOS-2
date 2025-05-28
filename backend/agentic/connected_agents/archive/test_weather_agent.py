#!/usr/bin/env python3
"""
Simple test for weather agent functionality.
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
    """Test the orchestrator with weather requests only."""
    
    orchestrator_id = os.getenv("MAIN_ORCHESTRATOR_AGENT_ID")
    if not orchestrator_id:
        logger.error("MAIN_ORCHESTRATOR_AGENT_ID not found in environment")
        return
        
    logger.info(f"Testing orchestrator: {orchestrator_id}")
    
    # Weather test queries
    test_queries = [
        "What's the weather like in New York?",
        "Tell me about the weather in London",
        "What's the temperature in Paris?"
    ]
    
    endpoint = os.getenv("AZURE_AI_PROJECT_CONNECTION_STRING")
    
    async with DefaultAzureCredential() as credential, \
               AIProjectClient(endpoint=endpoint, credential=credential) as client:
        
        logger.info("Successfully created client")
        
        # Get orchestrator definition
        orchestrator_def = await client.agents.get_agent(agent_id=orchestrator_id)
        logger.info(f"Retrieved orchestrator: {orchestrator_def.name}")
        logger.info(f"Number of tools: {len(orchestrator_def.tools) if orchestrator_def.tools else 0}")
        
        # Create agent instance using the full definition
        orchestrator_agent = AzureAIAgent(
            client=client,
            definition=orchestrator_def
        )
        
        # Test each query
        for query in test_queries:
            logger.info(f"\n{'='*60}")
            logger.info(f"QUERY: {query}")
            logger.info("="*60)
            
            response = ""
            async for part in orchestrator_agent.invoke(messages=query):
                if hasattr(part, 'content') and part.content:
                    response += str(part.content)
            
            logger.info(f"RESPONSE: {response}")
            
            # Check for proper delegation
            if "weather information specialist" in response.lower() or "°c" in response.lower() or "°f" in response.lower():
                logger.info("✅ Weather delegation successful!")
            else:
                logger.warning("❌ Weather delegation may have failed")
            
            await asyncio.sleep(1)  # Small delay between queries

if __name__ == "__main__":
    asyncio.run(test_weather_agent())