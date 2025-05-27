#!/usr/bin/env python3
"""
Remove all ChatAgent instances from Azure AI Agent Service.
"""

import asyncio
import os
import sys
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [%(funcName)s] %(message)s')
logger = logging.getLogger(__name__)

# Add parent directories to path
current_dir = os.path.dirname(os.path.abspath(__file__))
agentic_dir = os.path.dirname(current_dir)
sys.path.insert(0, agentic_dir)

# Load environment
env_path = os.path.join(agentic_dir, '.env')
logger.info(f"Loading .env from: {env_path}")
load_dotenv(env_path)

from azure.identity import DefaultAzureCredential
from semantic_kernel.agents import AzureAIAgent, AzureAIAgentSettings

async def remove_chat_agents():
    """Remove all ChatAgent instances."""
    chat_agent_ids = [
        "asst_FXhpfiInjMwhUkTTahltv4Js",
        "asst_yexGszT0x7ljnndlt6U5T2E6", 
        "asst_vKJM7vJCmEALy9WKBrg1NWJH"
    ]
    
    try:
        credential = DefaultAzureCredential()
        settings = AzureAIAgentSettings()
        
        logger.info(f"Connecting to: {settings.endpoint}")
        
        async with AzureAIAgent.create_client(credential=credential, settings=settings) as client:
            for agent_id in chat_agent_ids:
                try:
                    logger.info(f"Deleting ChatAgent with ID: {agent_id}")
                    await client.agents.delete_agent(agent_id=agent_id)
                    logger.info(f"✅ Successfully deleted ChatAgent: {agent_id}")
                except Exception as e:
                    logger.error(f"❌ Error deleting ChatAgent {agent_id}: {str(e)}")
            
    except Exception as e:
        logger.error(f"Error connecting to Azure AI Agent Service: {str(e)}")
    finally:
        if 'credential' in locals() and hasattr(credential, 'close') and asyncio.iscoroutinefunction(credential.close):
            await credential.close()

async def main():
    """Main entry point."""
    logger.info("Removing all ChatAgent instances...")
    await remove_chat_agents()
    logger.info("Done!")

if __name__ == "__main__":
    asyncio.run(main())