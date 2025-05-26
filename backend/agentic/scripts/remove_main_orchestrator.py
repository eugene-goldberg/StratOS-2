#!/usr/bin/env python3
"""
Remove the Main Orchestrator from Azure AI Agent Service.
"""

import asyncio
import os
import sys
import json
import logging
from datetime import datetime, timezone
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [%(funcName)s] %(message)s')
logger = logging.getLogger(__name__)

# Add parent directories to path
current_dir = os.path.dirname(os.path.abspath(__file__))
agentic_dir = os.path.dirname(current_dir)
env_path = os.path.join(agentic_dir, '.env')

logger.info(f"Attempting to load .env file from: {env_path}")
if load_dotenv(env_path):
    logger.info(".env file loaded successfully.")

# Import required modules
try:
    from azure.identity.aio import DefaultAzureCredential
    from semantic_kernel.agents import AzureAIAgent, AzureAIAgentSettings
except ImportError as e:
    logger.error(f"Error importing required modules: {e}")
    sys.exit(1)

async def remove_orchestrator():
    """Remove the Main Orchestrator from Azure."""
    
    try:
        # Load orchestrator ID from deployment config
        deployment_config_path = os.path.join(agentic_dir, "deployment_configs", "main_orchestrator_deployment.json")
        
        if not os.path.exists(deployment_config_path):
            logger.error("No Main Orchestrator deployment config found")
            return False
            
        with open(deployment_config_path, 'r') as f:
            config = json.load(f)
            orchestrator_id = config.get('agent_id')
            
        if not orchestrator_id:
            logger.error("No agent ID found in deployment config")
            return False
            
        logger.info(f"Found Main Orchestrator ID: {orchestrator_id}")
        
        # Create settings and credential
        settings = AzureAIAgentSettings()
        credential = DefaultAzureCredential()
        
        # Create client and delete orchestrator
        async with AzureAIAgent.create_client(credential=credential, settings=settings) as client:
            logger.info(f"Connected to Azure AI Agent Service")
            
            try:
                # Try to get the agent first to confirm it exists
                agent = await client.agents.get_agent(agent_id=orchestrator_id)
                logger.info(f"Found agent: {agent.name}")
                
                # Delete the agent
                await client.agents.delete_agent(agent_id=orchestrator_id)
                logger.info(f"✅ Successfully deleted Main Orchestrator: {orchestrator_id}")
                
                # Remove the deployment config file
                os.remove(deployment_config_path)
                logger.info(f"✅ Removed deployment config file")
                
                return True
                
            except Exception as e:
                logger.error(f"Error deleting orchestrator: {e}")
                return False
                
    except Exception as e:
        logger.error(f"Error removing orchestrator: {str(e)}", exc_info=True)
        return False
    finally:
        await credential.close()

async def main():
    """Main entry point."""
    print("="*80)
    print("REMOVING MAIN ORCHESTRATOR FROM AZURE")
    print("="*80)
    print(f"\nStarted at: {datetime.now(timezone.utc).isoformat()}")
    
    success = await remove_orchestrator()
    
    if success:
        print("\n✅ Main Orchestrator successfully removed from Azure AI Agent Service")
        print("Ready to deploy new plugin-based orchestrator")
    else:
        print("\n❌ Failed to remove Main Orchestrator")
    
    print(f"\nCompleted at: {datetime.now(timezone.utc).isoformat()}")

if __name__ == "__main__":
    asyncio.run(main())