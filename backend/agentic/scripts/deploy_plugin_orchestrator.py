#!/usr/bin/env python3
"""
Deploy the MainOrchestratorAgent with its plugin-based code to Azure AI Agent Service.
This orchestrator uses DeployedAgentPlugin classes to make SDK calls to specialist agents.
"""

import asyncio
import os
import sys
import json
import logging
from typing import Optional
from datetime import datetime, timezone
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

# Import the orchestrator module
from agents.plugin_based_orchestrator.main_orchestrator import (
    MainOrchestratorAgent, 
    load_specialist_agent_configs_from_env,
    setup_orchestrator_environment_and_agent
)

async def deploy_plugin_based_orchestrator():
    """Deploy the MainOrchestratorAgent that uses plugin-based SDK calls."""
    logger.info("Starting deployment of plugin-based MainOrchestratorAgent...")
    
    try:
        # Get the orchestrator agent instance with all its plugins configured
        orchestrator_agent = await setup_orchestrator_environment_and_agent()
        
        if not orchestrator_agent:
            logger.error("Failed to setup orchestrator agent")
            return None
        
        logger.info("Orchestrator agent configured with plugins. Now deploying to Azure AI Agent Service...")
        
        # Initialize credentials and settings for deployment
        credential = DefaultAzureCredential()
        settings = AzureAIAgentSettings()
        
        # Check settings
        if not settings.model_deployment_name:
            logger.error("AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME is not set")
            return None
            
        logger.info(f"Using endpoint: {settings.endpoint}")
        logger.info(f"Using model: {settings.model_deployment_name}")
        
        # Create client for deployment
        async with AzureAIAgent.create_client(credential=credential, settings=settings) as client:
            # Get the orchestrator's configuration
            orchestrator_name = orchestrator_agent.name
            orchestrator_instructions = orchestrator_agent.instructions
            
            # Note: The deployed agent won't have access to the Python plugin code directly.
            # Instead, we need to deploy the orchestrator with instructions that guide it
            # to make decisions about routing, and then we'll handle the actual routing
            # through a separate interaction layer.
            
            # For now, let's deploy with the instructions that help it make routing decisions
            logger.info(f"Deploying {orchestrator_name} with routing instructions...")
            
            # Deploy the orchestrator without tools (since it will use text-based routing)
            assistant_response = await client.agents.create_agent(
                name=orchestrator_name,
                instructions=orchestrator_instructions,
                tools=[],  # No tools - will use text-based routing decisions
                model=settings.model_deployment_name
            )
            
            agent_id = assistant_response.id
            logger.info(f"✅ Successfully deployed {orchestrator_name}")
            logger.info(f"   Agent ID: {agent_id}")
            logger.info(f"   Model: {assistant_response.model}")
            
            # Save deployment info
            deployment_info = {
                "orchestrator_id": agent_id,
                "name": orchestrator_name,
                "deployed_at": datetime.now(timezone.utc).isoformat(),
                "model": assistant_response.model,
                "routing_type": "plugin_based_sdk_calls",
                "specialist_agents": load_specialist_agent_configs_from_env()
            }
            
            # Save to file for reference
            deployment_file = os.path.join(agentic_dir, "deployment_configs", "plugin_orchestrator_deployment.json")
            os.makedirs(os.path.dirname(deployment_file), exist_ok=True)
            
            with open(deployment_file, 'w') as f:
                json.dump(deployment_info, f, indent=2)
            
            logger.info(f"\nDeployment info saved to: {deployment_file}")
            
            return agent_id
            
    except Exception as e:
        logger.error(f"Error deploying orchestrator: {str(e)}", exc_info=True)
        return None
    finally:
        if 'credential' in locals():
            await credential.close()

async def main():
    """Main deployment function."""
    # Deploy orchestrator
    agent_id = await deploy_plugin_based_orchestrator()
    
    if agent_id:
        logger.info(f"\n{'='*80}")
        logger.info("DEPLOYMENT SUCCESSFUL!")
        logger.info(f"{'='*80}")
        logger.info(f"Plugin-based MainOrchestratorAgent ID: {agent_id}")
        logger.info("\nIMPORTANT NOTES:")
        logger.info("1. This orchestrator uses a plugin-based architecture")
        logger.info("2. The deployed agent provides routing decisions")
        logger.info("3. Use the local main_orchestrator.py script to run the full plugin-based orchestration")
        logger.info("\nTo run the complete orchestration system locally:")
        logger.info("python3 backend/agentic/agents/plugin_based_orchestrator/main_orchestrator.py")
        logger.info("\nThis will use the local plugin code to make SDK calls to deployed specialists.")
    else:
        logger.error("Failed to deploy orchestrator")

if __name__ == "__main__":
    asyncio.run(main())