"""
Remove all deployed StratOS agents
Cleans up CEO Log, North Star, and Orchestrator agents
"""

import asyncio
import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv(Path(__file__).parent.parent.parent / '.env')

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from azure.ai.projects.aio import AIProjectClient
from azure.identity.aio import DefaultAzureCredential

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def remove_all_agents():
    """Remove all deployed StratOS agents"""
    
    # Get connection string
    connection_string = os.getenv("AZURE_AI_PROJECT_CONNECTION_STRING")
    if not connection_string:
        logger.error("AZURE_AI_PROJECT_CONNECTION_STRING not found in environment")
        return
    
    # Load deployment info if exists
    deployment_file = Path(__file__).parent.parent / "archive" / "stratos_deployment_info.json"
    if deployment_file.exists():
        with open(deployment_file, 'r') as f:
            deployment_info = json.load(f)
            logger.info(f"Found deployment info from: {deployment_info.get('deployment_time', 'unknown')}")
    else:
        deployment_info = None
        logger.warning("No deployment info file found")
    
    # Collect agent IDs to remove
    agents_to_remove = []
    
    # From deployment info
    if deployment_info:
        # Add orchestrator
        if deployment_info.get('orchestrator'):
            agents_to_remove.append({
                'name': deployment_info['orchestrator']['name'],
                'id': deployment_info['orchestrator']['id'],
                'type': 'orchestrator'
            })
        
        # Add agents
        for agent_key, agent_info in deployment_info.get('agents', {}).items():
            agents_to_remove.append({
                'name': agent_info['name'],
                'id': agent_info['id'],
                'type': agent_key
            })
    
    # Also check environment variables as backup
    env_agents = [
        ('CEO_LOG_AGENT_ID', 'CEO Log Agent'),
        ('NORTH_STAR_AGENT_ID', 'North Star Agent'),
        ('STRATOS_ORCHESTRATOR_ID', 'StratOS Orchestrator')
    ]
    
    for env_var, agent_name in env_agents:
        agent_id = os.getenv(env_var)
        if agent_id and not any(a['id'] == agent_id for a in agents_to_remove):
            agents_to_remove.append({
                'name': agent_name,
                'id': agent_id,
                'type': env_var.lower().replace('_id', '')
            })
    
    if not agents_to_remove:
        logger.warning("No agents found to remove")
        return
    
    logger.info(f"Found {len(agents_to_remove)} agents to remove")
    
    async with DefaultAzureCredential() as credential:
        async with AIProjectClient(
            endpoint=connection_string,
            credential=credential
        ) as client:
            
            # Remove each agent
            removed_count = 0
            failed_count = 0
            
            for agent in agents_to_remove:
                try:
                    logger.info(f"Removing {agent['type']}: {agent['name']} (ID: {agent['id']})")
                    await client.agents.delete_agent(agent_id=agent['id'])
                    logger.info(f"✅ Successfully removed: {agent['name']}")
                    removed_count += 1
                except Exception as e:
                    logger.error(f"❌ Failed to remove {agent['name']}: {e}")
                    failed_count += 1
            
            # Clean up deployment info file
            if deployment_file.exists() and removed_count > 0:
                # Archive it instead of deleting
                archive_name = f"stratos_deployment_info_removed_{deployment_info.get('deployment_time', 'unknown').replace(':', '-')}.json"
                archive_path = deployment_file.parent / "archive" / archive_name
                archive_path.parent.mkdir(exist_ok=True)
                deployment_file.rename(archive_path)
                logger.info(f"Archived deployment info to: {archive_path}")
            
            # Summary
            logger.info("\n" + "="*60)
            logger.info("REMOVAL SUMMARY")
            logger.info("="*60)
            logger.info(f"✅ Successfully removed: {removed_count} agents")
            if failed_count > 0:
                logger.info(f"❌ Failed to remove: {failed_count} agents")
            logger.info("="*60)
            
            # Clear environment variables reminder
            if removed_count > 0:
                logger.info("\n⚠️  Remember to clear these environment variables:")
                logger.info("   - CEO_LOG_AGENT_ID")
                logger.info("   - NORTH_STAR_AGENT_ID")
                logger.info("   - STRATOS_ORCHESTRATOR_ID")
                logger.info("   from your .env files")

if __name__ == "__main__":
    asyncio.run(remove_all_agents())