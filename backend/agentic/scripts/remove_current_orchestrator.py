#!/usr/bin/env python3
"""
Remove the currently deployed Main Orchestrator from Azure AI Agent Service.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from azure.ai.projects.aio import AIProjectClient
from azure.identity.aio import DefaultAzureCredential
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [%(funcName)s] %(message)s')
logger = logging.getLogger(__name__)

async def remove_main_orchestrator():
    """Remove the Main Orchestrator from Azure AI Agent Service."""
    
    # Load environment variables
    env_path = Path(__file__).parent.parent / '.env'
    logger.info(f"Loading .env from: {env_path}")
    load_dotenv(env_path)
    
    # Get orchestrator ID from environment
    orchestrator_id = os.getenv("MAIN_ORCHESTRATOR_AGENT_ID")
    if not orchestrator_id:
        logger.error("MAIN_ORCHESTRATOR_AGENT_ID not found in environment variables")
        return
    
    logger.info(f"Main Orchestrator ID to remove: {orchestrator_id}")
    
    # Get Azure AI Agent Service configuration
    endpoint = os.getenv("AZURE_AI_AGENT_ENDPOINT")
    if not endpoint:
        logger.error("AZURE_AI_AGENT_ENDPOINT not found in environment variables")
        return
    
    # Create credential and client
    credential = DefaultAzureCredential()
    
    try:
        # Create AI Project client
        async with AIProjectClient(
            endpoint=endpoint,
            credential=credential,
            api_version="2024-12-01-preview"
        ) as client:
            # First, verify the agent exists
            logger.info(f"Verifying agent exists: {orchestrator_id}")
            try:
                agent = await client.agents.get_agent(agent_id=orchestrator_id)
                logger.info(f"Found agent: {agent.name} (ID: {agent.id})")
            except Exception as e:
                logger.error(f"Agent not found: {e}")
                return
            
            # Delete the agent
            logger.info(f"Deleting Main Orchestrator: {orchestrator_id}")
            await client.agents.delete_agent(agent_id=orchestrator_id)
            
            print("\n" + "="*80)
            print("✅ MAIN ORCHESTRATOR REMOVED SUCCESSFULLY")
            print("="*80)
            print(f"Deleted Agent: {agent.name}")
            print(f"Agent ID: {orchestrator_id}")
            print("="*80)
            
    except Exception as e:
        logger.error(f"Error removing orchestrator: {e}")
        print("\n" + "="*80)
        print("❌ FAILED TO REMOVE MAIN ORCHESTRATOR")
        print("="*80)
        print(f"Error: {e}")
        print("="*80)

if __name__ == "__main__":
    asyncio.run(remove_main_orchestrator())