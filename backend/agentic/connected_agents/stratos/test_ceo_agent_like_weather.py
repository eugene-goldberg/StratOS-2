#!/usr/bin/env python3
"""
Test CEO Log Agent following the weather agent pattern.
Shows the actual HTTP request the agent makes to Azure Functions.
"""

import asyncio
import os
import logging
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import Azure SDK components
from azure.identity.aio import DefaultAzureCredential
from azure.ai.projects.aio import AIProjectClient
from semantic_kernel.agents import AzureAIAgent

# Configure logging to show HTTP requests
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Enable HTTP logging to see actual requests
import http.client as http_client
http_client.HTTPConnection.debuglevel = 1

async def test_ceo_log_agent():
    """Test the CEO Log Agent with save functionality."""
    
    # Load CEO Log Agent ID from deployment info
    try:
        with open("deployment_info.json", "r") as f:
            deployment_info = json.load(f)
            ceo_agent_id = deployment_info["ceo_log_agent"]["id"]
            logger.info(f"Loaded CEO Log Agent ID: {ceo_agent_id}")
    except Exception as e:
        logger.error(f"Failed to load deployment info: {e}")
        return
        
    logger.info(f"Testing CEO Log Agent: {ceo_agent_id}")
    
    # Test message asking to save a CEO log entry
    test_query = f"Save this CEO log entry: Our Q4 strategy meeting revealed strong alignment between product development and customer needs. The team is excited about the new AI features we're planning to launch. Market conditions remain favorable for expansion. User ID: test_user_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    endpoint = os.getenv("AZURE_AI_PROJECT_CONNECTION_STRING")
    
    async with DefaultAzureCredential() as credential, \
               AIProjectClient(endpoint=endpoint, credential=credential) as client:
        
        logger.info("Successfully created client")
        
        # Get CEO Log Agent definition
        ceo_agent_def = await client.agents.get_agent(agent_id=ceo_agent_id)
        logger.info(f"Retrieved CEO Log Agent: {ceo_agent_def.name}")
        
        # Create agent instance using the full definition
        ceo_agent = AzureAIAgent(
            client=client,
            definition=ceo_agent_def
        )
        
        logger.info(f"\n{'='*60}")
        logger.info(f"QUERY: {test_query}")
        logger.info("="*60)
        logger.info("\n📡 HTTP Request Details will appear below:")
        logger.info("-"*60)
        
        response = ""
        async for part in ceo_agent.invoke(messages=test_query):
            if hasattr(part, 'content') and part.content:
                response += str(part.content)
        
        logger.info("-"*60)
        logger.info(f"\n🤖 AGENT RESPONSE:\n{response}")
        
        # Check for successful save
        if "saved" in response.lower() or "successfully" in response.lower():
            logger.info("\n✅ CEO log entry saved successfully!")
            
        if "entryid" in response.lower() or "id" in response.lower():
            logger.info("✅ Entry ID returned in response!")
            
        if "tags" in response.lower():
            logger.info("✅ Tags extracted from the entry!")
        
        # Test another operation - search
        await asyncio.sleep(3)  # Wait to avoid rate limits
        
        test_query2 = "Search for CEO log entries containing 'AI features' or 'strategy'"
        logger.info(f"\n{'='*60}")
        logger.info(f"QUERY: {test_query2}")
        logger.info("="*60)
        logger.info("\n📡 HTTP Request Details will appear below:")
        logger.info("-"*60)
        
        response2 = ""
        async for part in ceo_agent.invoke(messages=test_query2):
            if hasattr(part, 'content') and part.content:
                response2 += str(part.content)
        
        logger.info("-"*60)
        logger.info(f"\n🤖 AGENT RESPONSE:\n{response2}")
        
        if "result" in response2.lower() or "found" in response2.lower():
            logger.info("\n✅ Search completed successfully!")
            
        # Test analytics
        await asyncio.sleep(3)
        
        test_query3 = "Analyze the recent CEO logs and provide insights on key themes"
        logger.info(f"\n{'='*60}")
        logger.info(f"QUERY: {test_query3}")
        logger.info("="*60)
        logger.info("\n📡 HTTP Request Details will appear below:")
        logger.info("-"*60)
        
        response3 = ""
        async for part in ceo_agent.invoke(messages=test_query3):
            if hasattr(part, 'content') and part.content:
                response3 += str(part.content)
        
        logger.info("-"*60)
        logger.info(f"\n🤖 AGENT RESPONSE:\n{response3}")
        
        if "insight" in response3.lower() or "theme" in response3.lower():
            logger.info("\n✅ Analytics provided successfully!")

if __name__ == "__main__":
    print("\n🚀 Starting CEO Log Agent Test (Weather Pattern)...\n")
    asyncio.run(test_ceo_log_agent())