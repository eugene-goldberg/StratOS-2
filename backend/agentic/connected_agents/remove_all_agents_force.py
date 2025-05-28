"""
Remove ALL deployed agents from Azure AI Agent Service
This will list and remove ALL agents, not just StratOS ones
"""

import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv(Path(__file__).parent / '.env')

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from azure.ai.projects.aio import AIProjectClient
from azure.identity.aio import DefaultAzureCredential

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def remove_all_agents_force():
    """Remove ALL deployed agents from the project"""
    
    # Get connection string
    connection_string = os.getenv("AZURE_AI_PROJECT_CONNECTION_STRING")
    if not connection_string:
        logger.error("AZURE_AI_PROJECT_CONNECTION_STRING not found in environment")
        return
    
    logger.info("Connecting to Azure AI Project...")
    
    async with DefaultAzureCredential() as credential:
        async with AIProjectClient(
            endpoint=connection_string,
            credential=credential
        ) as client:
            
            try:
                # List all agents
                logger.info("Fetching list of all deployed agents...")
                agents = []
                async for agent in client.agents.list_agents():
                    agents.append({
                        'id': agent.id,
                        'name': agent.name,
                        'created_at': agent.created_at,
                        'model': agent.model if hasattr(agent, 'model') else 'unknown'
                    })
                
                if not agents:
                    logger.info("No agents found in the project")
                    return
                
                # Display all agents
                logger.info(f"\nFound {len(agents)} agents:")
                logger.info("="*80)
                for i, agent in enumerate(agents, 1):
                    logger.info(f"{i}. {agent['name']}")
                    logger.info(f"   ID: {agent['id']}")
                    logger.info(f"   Created: {agent['created_at']}")
                    logger.info(f"   Model: {agent['model']}")
                    logger.info("-"*40)
                
                # Confirm deletion
                logger.info(f"\n⚠️  WARNING: This will delete ALL {len(agents)} agents!")
                logger.info("Press Ctrl+C within 5 seconds to cancel...")
                
                try:
                    await asyncio.sleep(5)
                except KeyboardInterrupt:
                    logger.info("\n❌ Deletion cancelled by user")
                    return
                
                # Delete all agents
                logger.info("\nStarting deletion process...")
                removed_count = 0
                failed_count = 0
                
                for agent in agents:
                    try:
                        logger.info(f"Removing: {agent['name']} (ID: {agent['id']})")
                        await client.agents.delete_agent(agent_id=agent['id'])
                        logger.info(f"✅ Successfully removed: {agent['name']}")
                        removed_count += 1
                    except Exception as e:
                        logger.error(f"❌ Failed to remove {agent['name']}: {e}")
                        failed_count += 1
                    
                    # Small delay to avoid rate limiting
                    await asyncio.sleep(0.5)
                
                # Summary
                logger.info("\n" + "="*60)
                logger.info("REMOVAL SUMMARY")
                logger.info("="*60)
                logger.info(f"Total agents found: {len(agents)}")
                logger.info(f"✅ Successfully removed: {removed_count}")
                if failed_count > 0:
                    logger.info(f"❌ Failed to remove: {failed_count}")
                logger.info("="*60)
                
                # List remaining agents to verify
                logger.info("\nVerifying cleanup...")
                remaining = 0
                async for agent in client.agents.list_agents():
                    remaining += 1
                
                if remaining == 0:
                    logger.info("✅ All agents have been successfully removed!")
                else:
                    logger.warning(f"⚠️  {remaining} agents still remain in the project")
                    
            except Exception as e:
                logger.error(f"Error during operation: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(remove_all_agents_force())