"""
Undeploy All StratOS Connected Agents
This script removes all deployed StratOS agents and orchestrator
"""

import os
import sys
import asyncio
import logging
import json
from pathlib import Path
from dotenv import load_dotenv
from azure.ai.projects.aio import AIProjectClient
from azure.identity.aio import DefaultAzureCredential

# Load environment variables
load_dotenv(Path(__file__).parent.parent.parent / '.env')

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def undeploy_all_stratos_agents():
    """Undeploy all StratOS agents and orchestrator"""
    
    # Get connection string
    connection_string = os.getenv("AZURE_AI_PROJECT_CONNECTION_STRING")
    if not connection_string:
        logger.error("AZURE_AI_PROJECT_CONNECTION_STRING not found in environment")
        return
    
    # Check for deployment info file
    archive_dir = Path(__file__).parent.parent / "archive"
    deployment_file = archive_dir / "stratos_deployment_info.json"
    
    if not deployment_file.exists():
        logger.info("No deployment info file found. Checking environment variables...")
        
        # Try to get IDs from environment
        agent_ids = {
            "ceo_log": os.getenv("CEO_LOG_AGENT_ID"),
            "north_star": os.getenv("NORTH_STAR_AGENT_ID"),
            "memory_recall": os.getenv("MEMORY_RECALL_AGENT_ID")
        }
        orchestrator_id = os.getenv("STRATOS_ORCHESTRATOR_ID")
        
        if not any(agent_ids.values()) and not orchestrator_id:
            logger.info("No agent IDs found in environment. Nothing to undeploy.")
            return
    else:
        # Load deployment info
        with open(deployment_file, 'r') as f:
            deployment_info = json.load(f)
        
        agent_ids = {}
        for agent_name, agent_info in deployment_info.get("agents", {}).items():
            agent_ids[agent_name] = agent_info.get("id")
        
        orchestrator_id = deployment_info.get("orchestrator", {}).get("id")
    
    logger.info("Found agents to undeploy:")
    for name, agent_id in agent_ids.items():
        if agent_id:
            logger.info(f"  - {name}: {agent_id}")
    if orchestrator_id:
        logger.info(f"  - orchestrator: {orchestrator_id}")
    
    # Undeploy agents
    try:
        async with DefaultAzureCredential() as credential:
            async with AIProjectClient(
                endpoint=connection_string,
                credential=credential
            ) as client:
                
                # Delete orchestrator first (it depends on other agents)
                if orchestrator_id:
                    logger.info(f"\nDeleting orchestrator: {orchestrator_id}")
                    try:
                        await client.agents.delete_agent(agent_id=orchestrator_id)
                        logger.info("✅ Orchestrator deleted")
                    except Exception as e:
                        logger.error(f"❌ Error deleting orchestrator: {e}")
                
                # Delete each agent
                for agent_name, agent_id in agent_ids.items():
                    if agent_id:
                        logger.info(f"\nDeleting {agent_name}: {agent_id}")
                        try:
                            await client.agents.delete_agent(agent_id=agent_id)
                            logger.info(f"✅ {agent_name} deleted")
                        except Exception as e:
                            logger.error(f"❌ Error deleting {agent_name}: {e}")
                
                logger.info("\n" + "="*60)
                logger.info("UNDEPLOYMENT COMPLETE")
                logger.info("="*60)
                
                # Clean up deployment info file
                if deployment_file.exists():
                    deployment_file.unlink()
                    logger.info("Deleted deployment info file")
                
                # Clean up environment variables
                env_path = Path(__file__).parent.parent.parent / '.env'
                if env_path.exists():
                    logger.info("\nCleaning up .env file...")
                    with open(env_path, 'r') as f:
                        lines = f.readlines()
                    
                    # Remove agent ID lines
                    new_lines = []
                    for line in lines:
                        if not any(line.startswith(f"{key}_AGENT_ID=") for key in ["CEO_LOG", "NORTH_STAR", "MEMORY_RECALL"]):
                            if not line.startswith("STRATOS_ORCHESTRATOR_ID="):
                                new_lines.append(line)
                    
                    with open(env_path, 'w') as f:
                        f.writelines(new_lines)
                    
                    logger.info("Cleaned up .env file")
                
    except Exception as e:
        logger.error(f"Error during undeployment: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(undeploy_all_stratos_agents())