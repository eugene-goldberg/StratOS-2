#!/usr/bin/env python3
"""
List all deployed agents in the Azure AI Agent Service.
"""

import asyncio
import os
import logging
from dotenv import load_dotenv
from azure.identity.aio import DefaultAzureCredential
from azure.ai.projects.aio import AIProjectClient

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

async def list_all_agents():
    """List all agents currently deployed."""
    
    endpoint = os.getenv("AZURE_AI_PROJECT_CONNECTION_STRING")
    if not endpoint:
        logger.error("AZURE_AI_PROJECT_CONNECTION_STRING not found")
        return
    
    async with DefaultAzureCredential() as credential, \
               AIProjectClient(endpoint=endpoint, credential=credential) as client:
        
        logger.info("Fetching all deployed agents...")
        agents = client.agents.list_agents()
        
        count = 0
        async for agent in agents:
            count += 1
            logger.info(f"\n{'='*60}")
            logger.info(f"Agent #{count}")
            logger.info(f"Name: {agent.name}")
            logger.info(f"ID: {agent.id}")
            logger.info(f"Model: {agent.model}")
            logger.info(f"Created: {agent.created_at}")
            if agent.tools:
                logger.info(f"Tools: {len(agent.tools)}")
                for i, tool in enumerate(agent.tools):
                    logger.info(f"  Tool {i+1}: {tool}")
        
        if count == 0:
            logger.info("No agents found.")
        else:
            logger.info(f"\nTotal agents found: {count}")

if __name__ == "__main__":
    asyncio.run(list_all_agents())