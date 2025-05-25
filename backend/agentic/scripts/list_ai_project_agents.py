#!/usr/bin/env python3
"""
Lists agents deployed to the Azure AI Project Agent Service.
Relies on environment variables for configuration, similar to the deployment script.
Ensure your .env file is correctly set up (especially AZURE_AI_AGENT_PROJECT_* vars,
and AZURE_AI_AGENT_API_VERSION. AZURE_AI_AGENT_ENDPOINT should NOT be set to allow SDK discovery).
"""

import asyncio
import os
import sys
import logging
from datetime import datetime, timezone # Ensure timezone is imported
from dotenv import load_dotenv

# Configure logging as early as possible
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [%(funcName)s] %(message)s')
logger = logging.getLogger(__name__)

# Add parent directories to path (consistent with your deploy script)
current_dir = os.path.dirname(os.path.abspath(__file__))
# Assuming .env file is in the parent directory of this script's directory's parent
# If script is in .../scripts/, then current_dir is .../scripts/
# agentic_dir (parent of scripts) is .../agentic/
# env_path should be .../agentic/.env
agentic_dir = os.path.dirname(current_dir) 
env_path = os.path.join(agentic_dir, '.env')

logger.info(f"Attempting to load .env file from: {env_path}")
if load_dotenv(env_path):
    logger.info(".env file loaded successfully.")
else:
    logger.warning(f".env file not found at '{env_path}' or it's empty. Relying on pre-set environment variables.")

# Import required modules
try:
    from azure.identity.aio import DefaultAzureCredential
    from semantic_kernel.agents import AzureAIAgent, AzureAIAgentSettings 
except ImportError as e:
    logger.error(f"Error importing required modules: {e}")
    logger.error("Please ensure 'semantic-kernel[azure]' and 'azure-identity' are installed.")
    sys.exit(1)

async def list_deployed_agents():
    """
    Connects to the Azure AI Project Agent Service and lists deployed agents.
    """
    logger.info("Attempting to list agents from Azure AI Project Agent Service...")

    try:
        # Ensure necessary environment variables for SDK discovery are present
        required_env_vars = [
            "AZURE_AI_AGENT_PROJECT_NAME",
            "AZURE_AI_AGENT_PROJECT_HUB_NAME",
            "AZURE_AI_AGENT_PROJECT_RESOURCE_GROUP",
            "AZURE_AI_AGENT_PROJECT_SUBSCRIPTION_ID",
            "AZURE_AI_AGENT_API_VERSION"
        ]
        logger.info("--- Checking required Azure AI Project context variables from environment ---")
        for var_name in required_env_vars:
            val = os.getenv(var_name)
            if not val:
                logger.error(f"CRITICAL: Required environment variable '{var_name}' is not set. This is needed for SDK discovery.")
                return 
            logger.info(f"  {var_name}: '{val}'")
        
        env_endpoint = os.getenv("AZURE_AI_AGENT_ENDPOINT")
        if env_endpoint: # If user explicitly sets it in .env
            logger.warning(f"AZURE_AI_AGENT_ENDPOINT is set in .env to '{env_endpoint}'. SDK will use this explicit endpoint.")
            # os.environ["AZURE_AI_AGENT_ENDPOINT"] = env_endpoint # Already in env if loaded by dotenv
        else: # Preferred mode for SDK discovery
            logger.info("AZURE_AI_AGENT_ENDPOINT is not set in .env, relying on SDK discovery (this is the preferred mode for this script).")
            if "AZURE_AI_AGENT_ENDPOINT" in os.environ: # Clean up if set by other means
                 del os.environ["AZURE_AI_AGENT_ENDPOINT"]


        settings = AzureAIAgentSettings() # Loads from environment

        logger.info(f"--- AzureAIAgentSettings object initialized with ---")
        logger.info(f"  settings.endpoint: '{settings.endpoint}' << This should be dynamically resolved by the SDK")
        logger.info(f"  settings.api_version: '{settings.api_version}'")
        # model_deployment_name is not strictly needed for listing but part of settings
        logger.info(f"  settings.model_deployment_name (if applicable): '{settings.model_deployment_name}'")


        if settings.endpoint is None:
            logger.error("CRITICAL FAILURE: AzureAIAgentSettings did not resolve an endpoint. SDK discovery might have failed.")
            logger.error("Ensure all AZURE_AI_AGENT_PROJECT_* variables are correctly set in your .env file WITH THE 'AZURE_AI_AGENT_' PREFIX.")
            return

        logger.info(f"Attempting to connect to agent service at resolved endpoint: {settings.endpoint}")

        async with DefaultAzureCredential(exclude_interactive_browser_credential=False) as credential:
            # Test token acquisition
            try:
                scope_to_test = "https://management.azure.com/.default"
                logger.info(f"Acquiring test AAD token for scope: {scope_to_test}...")
                await credential.get_token(scope_to_test) # We don't need to use the token_info here
                logger.info("Test AAD token acquired successfully.")
            except Exception as auth_e:
                logger.error(f"Failed to acquire test AAD token: {auth_e}", exc_info=True)
                return

            async with AzureAIAgent.create_client(credential=credential, settings=settings) as client:
                logger.info(f"Successfully created Azure AI Agent client for project: {os.getenv('AZURE_AI_AGENT_PROJECT_NAME')}")
                logger.info("Fetching list of agents...")
                
                agents_listed_count = 0
                all_agents_iterable = client.agents.list_agents()
                async for agent_def in all_agents_iterable:
                    agents_listed_count += 1
                    
                    # Corrected handling of agent_def.created_at
                    created_at_val = agent_def.created_at
                    if isinstance(created_at_val, datetime):
                        # If it's naive, assume UTC as that's common for API timestamps
                        if created_at_val.tzinfo is None:
                            created_at_val = created_at_val.replace(tzinfo=timezone.utc)
                        created_at_iso = created_at_val.isoformat()
                    elif isinstance(created_at_val, (int, float)): # Fallback if it can be a number
                        created_at_iso = datetime.fromtimestamp(created_at_val, timezone.utc).isoformat()
                    else:
                        created_at_iso = "N/A"
                        
                    logger.info(f"  --------------------------------------------------")
                    logger.info(f"  Agent #{agents_listed_count}")
                    logger.info(f"    Name:         {agent_def.name}")
                    logger.info(f"    ID:           {agent_def.id}")
                    logger.info(f"    Description:  {agent_def.description}")
                    logger.info(f"    Model:        {agent_def.model}")
                    instructions_preview = agent_def.instructions[:100] + '...' if agent_def.instructions and len(agent_def.instructions) > 100 else agent_def.instructions
                    logger.info(f"    Instructions: {instructions_preview}")
                    logger.info(f"    Created At:   {created_at_iso}")
                
                if agents_listed_count == 0:
                    logger.info("No agents found in the project.")
                else:
                    logger.info(f"--------------------------------------------------")
                    logger.info(f"Successfully listed {agents_listed_count} agent(s).")

    except Exception as e:
        logger.error(f"An error occurred while trying to list agents: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(list_deployed_agents())