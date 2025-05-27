#!/usr/bin/env python3
"""
Remove all deployed agents from Azure AI Agent Service without confirmation.
USE WITH CAUTION - This will delete ALL agents permanently!
"""

import asyncio
import os
import sys
import logging
from typing import List
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

from azure.identity.aio import DefaultAzureCredential
from semantic_kernel.agents import AzureAIAgent, AzureAIAgentSettings

async def list_all_agents() -> List[dict]:
    """List all deployed agents in Azure AI Agent Service."""
    agents = []
    
    try:
        credential = DefaultAzureCredential()
        settings = AzureAIAgentSettings()
        
        logger.info(f"Connecting to: {settings.endpoint}")
        
        async with AzureAIAgent.create_client(credential=credential, settings=settings) as client:
            # List all agents
            response = client.agents.list_agents()
            
            async for agent in response:
                agent_info = {
                    "id": agent.id,
                    "name": agent.name,
                    "description": agent.description,
                    "instructions": agent.instructions[:100] + "..." if agent.instructions and len(agent.instructions) > 100 else agent.instructions,
                    "model": agent.model,
                    "created_at": agent.created_at
                }
                agents.append(agent_info)
                
    except Exception as e:
        logger.error(f"Error listing agents: {str(e)}", exc_info=True)
    finally:
        await credential.close()
    
    return agents

async def delete_agent(agent_id: str, agent_name: str) -> bool:
    """Delete a single agent from Azure AI Agent Service."""
    try:
        credential = DefaultAzureCredential()
        settings = AzureAIAgentSettings()
        
        async with AzureAIAgent.create_client(credential=credential, settings=settings) as client:
            # Delete the agent
            await client.agents.delete_agent(agent_id=agent_id)
            logger.info(f"✅ Deleted agent: {agent_name} (ID: {agent_id})")
            return True
            
    except Exception as e:
        logger.error(f"❌ Error deleting agent {agent_name} (ID: {agent_id}): {str(e)}")
        return False
    finally:
        await credential.close()

async def remove_all_agents():
    """Main function to remove all deployed agents."""
    logger.info("Fetching list of all deployed agents...")
    
    # Get all agents
    agents = await list_all_agents()
    
    if not agents:
        logger.info("No agents found in Azure AI Agent Service.")
        return
    
    # Display all agents
    logger.info(f"\nFound {len(agents)} agents:")
    logger.info("="*80)
    
    for i, agent in enumerate(agents, 1):
        logger.info(f"{i}. {agent['name']} (ID: {agent['id']})")
        logger.info(f"   Model: {agent['model']}")
        logger.info(f"   Created: {agent['created_at']}")
        if agent['description']:
            logger.info(f"   Description: {agent['description']}")
        logger.info("")
    
    # Proceed with deletion without confirmation
    logger.info("="*80)
    logger.warning(f"⚠️  DELETING all {len(agents)} agents permanently!")
    logger.info("="*80)
    
    # Delete all agents
    logger.info("\nDeleting all agents...")
    successful_deletions = 0
    failed_deletions = 0
    
    for agent in agents:
        success = await delete_agent(agent['id'], agent['name'])
        if success:
            successful_deletions += 1
        else:
            failed_deletions += 1
        
        # Small delay between deletions to avoid rate limiting
        await asyncio.sleep(0.5)
    
    # Summary
    logger.info("\n" + "="*80)
    logger.info("DELETION SUMMARY")
    logger.info("="*80)
    logger.info(f"Total agents: {len(agents)}")
    logger.info(f"Successfully deleted: {successful_deletions}")
    logger.info(f"Failed to delete: {failed_deletions}")
    
    if failed_deletions == 0:
        logger.info("\n✅ All agents have been successfully removed from Azure AI Agent Service!")
    else:
        logger.warning(f"\n⚠️  {failed_deletions} agents could not be deleted. Please check the errors above.")

async def main():
    """Entry point."""
    try:
        await remove_all_agents()
    except KeyboardInterrupt:
        logger.info("\nOperation cancelled by user.")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(main())