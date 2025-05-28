#!/usr/bin/env python3
"""
Remove all deployed agents by reading agent IDs from .env file.
"""

import asyncio
import os
import logging
from dotenv import load_dotenv
from azure.identity.aio import DefaultAzureCredential
from azure.ai.projects.aio import AIProjectClient
from semantic_kernel.agents import AzureAIAgentSettings

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

async def remove_all_agents():
    """Remove all deployed agents listed in .env file."""
    
    # Get settings
    ai_agent_settings = AzureAIAgentSettings(
        model_deployment_name=os.getenv("AZURE_AI_MODEL_DEPLOYMENT_NAME", "gpt-35-turbo"),
        endpoint=os.getenv("AZURE_AI_PROJECT_CONNECTION_STRING")
    )
    
    if not ai_agent_settings.endpoint:
        logger.error("AZURE_AI_PROJECT_CONNECTION_STRING is not set")
        return
        
    project_connection_string = str(ai_agent_settings.endpoint)
    
    # List of agent IDs to remove
    agent_ids_to_remove = []
    
    # Check for specific agent IDs in environment
    orchestrator_id = os.getenv("MAIN_ORCHESTRATOR_AGENT_ID")
    greeter_id = os.getenv("SPECIALIZED_GREETER_AGENT_ID")
    calculator_id = os.getenv("SPECIALIZED_CALCULATOR_AGENT_ID")
    
    if orchestrator_id:
        agent_ids_to_remove.append(("Main Orchestrator", orchestrator_id))
    if greeter_id:
        agent_ids_to_remove.append(("Specialized Greeter", greeter_id))
    if calculator_id:
        agent_ids_to_remove.append(("Specialized Calculator", calculator_id))
    
    if not agent_ids_to_remove:
        logger.info("No agent IDs found in .env file to remove")
        return
    
    logger.info(f"Found {len(agent_ids_to_remove)} agents to remove:")
    for name, agent_id in agent_ids_to_remove:
        logger.info(f"  - {name}: {agent_id}")
    
    # Create client and remove agents
    async with DefaultAzureCredential() as credential, \
               AIProjectClient(endpoint=project_connection_string, credential=credential) as client:
        
        logger.info("\nStarting agent removal...")
        removed_count = 0
        failed_count = 0
        
        for name, agent_id in agent_ids_to_remove:
            try:
                logger.info(f"\nRemoving {name} (ID: {agent_id})...")
                await client.agents.delete_agent(agent_id=agent_id)
                logger.info(f"✅ Successfully removed {name}")
                removed_count += 1
            except Exception as e:
                logger.error(f"❌ Failed to remove {name}: {e}")
                failed_count += 1
        
        logger.info("\n" + "="*60)
        logger.info("REMOVAL SUMMARY")
        logger.info("="*60)
        logger.info(f"Total agents found: {len(agent_ids_to_remove)}")
        logger.info(f"Successfully removed: {removed_count}")
        logger.info(f"Failed to remove: {failed_count}")
        logger.info("="*60)
        
        # Clean up .env file if all agents were removed successfully
        if removed_count == len(agent_ids_to_remove):
            logger.info("\nCleaning up .env file...")
            env_path = os.path.join(os.path.dirname(__file__), '.env')
            with open(env_path, 'r') as f:
                lines = f.readlines()
            
            # Remove agent ID lines
            new_lines = []
            for line in lines:
                if not (line.startswith('MAIN_ORCHESTRATOR_AGENT_ID=') or 
                       line.startswith('SPECIALIZED_GREETER_AGENT_ID=') or
                       line.startswith('SPECIALIZED_CALCULATOR_AGENT_ID=')):
                    new_lines.append(line)
            
            with open(env_path, 'w') as f:
                f.writelines(new_lines)
            
            logger.info("✅ Cleaned up agent IDs from .env file")

if __name__ == "__main__":
    asyncio.run(remove_all_agents())