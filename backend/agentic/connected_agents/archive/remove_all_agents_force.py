#!/usr/bin/env python3
"""
Force remove ALL deployed agents in the Azure AI Agent Service.
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

async def remove_all_agents_force():
    """Remove all agents currently deployed."""
    
    endpoint = os.getenv("AZURE_AI_PROJECT_CONNECTION_STRING")
    if not endpoint:
        logger.error("AZURE_AI_PROJECT_CONNECTION_STRING not found")
        return
    
    async with DefaultAzureCredential() as credential, \
               AIProjectClient(endpoint=endpoint, credential=credential) as client:
        
        logger.info("Fetching all deployed agents...")
        agents = client.agents.list_agents()
        
        agents_to_remove = []
        async for agent in agents:
            agents_to_remove.append({
                'id': agent.id,
                'name': agent.name
            })
        
        if not agents_to_remove:
            logger.info("No agents found to remove.")
            return
        
        logger.info(f"\nFound {len(agents_to_remove)} agents to remove:")
        for agent in agents_to_remove:
            logger.info(f"  - {agent['name']} (ID: {agent['id']})")
        
        logger.info("\nStarting removal process...")
        success_count = 0
        fail_count = 0
        
        for agent in agents_to_remove:
            try:
                logger.info(f"\nRemoving {agent['name']} (ID: {agent['id']})...")
                await client.agents.delete_agent(agent_id=agent['id'])
                logger.info(f"✅ Successfully removed {agent['name']}")
                success_count += 1
            except Exception as e:
                logger.error(f"❌ Failed to remove {agent['name']}: {e}")
                fail_count += 1
        
        logger.info("\n" + "="*60)
        logger.info("REMOVAL SUMMARY")
        logger.info("="*60)
        logger.info(f"Total agents found: {len(agents_to_remove)}")
        logger.info(f"Successfully removed: {success_count}")
        logger.info(f"Failed to remove: {fail_count}")
        logger.info("="*60)

if __name__ == "__main__":
    asyncio.run(remove_all_agents_force())