#!/usr/bin/env python3
"""
Delete the MainOrchestratorAgent from Azure AI Agent Service
"""

import os
import sys
import asyncio
import logging
from dotenv import load_dotenv
from azure.identity.aio import DefaultAzureCredential
import aiohttp

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
current_dir = os.path.dirname(os.path.abspath(__file__))
agentic_dir = os.path.dirname(current_dir)
env_path = os.path.join(agentic_dir, '.env')
load_dotenv(env_path)

async def delete_orchestrator():
    """Delete the MainOrchestratorAgent"""
    
    # MainOrchestratorAgent ID
    orchestrator_id = "asst_LgNjAIwEDV5wQcogIUmGf4qq"
    
    # Get configuration
    endpoint = os.getenv("AZURE_AI_AGENT_ENDPOINT")
    api_version = os.getenv("AZURE_AI_AGENT_API_VERSION", "2024-12-01-preview")
    
    if not endpoint:
        logger.error("AZURE_AI_AGENT_ENDPOINT not set")
        return
        
    logger.info(f"Using endpoint: {endpoint}")
    logger.info(f"Deleting MainOrchestratorAgent: {orchestrator_id}")
    
    try:
        # Get credential
        async with DefaultAzureCredential() as credential:
            # Get token
            token = await credential.get_token("https://management.azure.com/.default")
            
            headers = {
                "Authorization": f"Bearer {token.token}",
                "Content-Type": "application/json"
            }
            
            async with aiohttp.ClientSession() as session:
                # Delete the agent
                delete_url = f"{endpoint}/assistants/{orchestrator_id}?api-version={api_version}"
                
                async with session.delete(delete_url, headers=headers) as response:
                    if response.status == 204:
                        logger.info(f"Successfully deleted MainOrchestratorAgent: {orchestrator_id}")
                    elif response.status == 404:
                        logger.warning(f"MainOrchestratorAgent not found: {orchestrator_id}")
                    else:
                        error_text = await response.text()
                        logger.error(f"Failed to delete agent: {response.status} - {error_text}")
                        
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(delete_orchestrator())