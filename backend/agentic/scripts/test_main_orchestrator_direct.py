#!/usr/bin/env python3
"""
Direct test of MainOrchestratorAgent using REST API
"""

import asyncio
import os
import sys
import logging
import aiohttp
from datetime import datetime
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Path setup
current_dir = os.path.dirname(os.path.abspath(__file__))
agentic_dir = os.path.dirname(current_dir) 
env_path = os.path.join(agentic_dir, '.env')

logger.info(f"Loading .env from: {env_path}")
load_dotenv(env_path)

# Import required modules
try:
    from azure.identity.aio import DefaultAzureCredential
except ImportError as e:
    logger.error(f"Error importing required modules: {e}")
    sys.exit(1)

async def test_orchestrator_direct():
    """Test the deployed MainOrchestratorAgent using direct REST API calls"""
    
    # Known orchestrator ID from deployment
    orchestrator_agent_id = "asst_LgNjAIwEDV5wQcogIUmGf4qq"
    
    # Get configuration from environment
    endpoint = os.getenv("AZURE_AI_AGENT_ENDPOINT")
    api_version = os.getenv("AZURE_AI_AGENT_API_VERSION", "2024-12-01-preview")
    
    if not endpoint:
        logger.error("AZURE_AI_AGENT_ENDPOINT not set in environment")
        return
        
    logger.info(f"Using endpoint: {endpoint}")
    logger.info(f"Using API version: {api_version}")
    
    # Test messages
    test_messages = [
        "I need to record my thoughts about the market downturn and its effect on Q3 projections.",
        "What is our company's core vision statement?",
        "Perform a SWOT analysis for the new Alpha project."
    ]
    
    try:
        # Get Azure credential
        async with DefaultAzureCredential(exclude_interactive_browser_credential=False) as credential:
            # Get access token
            token = await credential.get_token("https://management.azure.com/.default")
            
            headers = {
                "Authorization": f"Bearer {token.token}",
                "Content-Type": "application/json"
            }
            
            async with aiohttp.ClientSession() as session:
                for test_message in test_messages:
                    print(f"\n{'='*60}")
                    print(f"User: {test_message}")
                    
                    # Create thread
                    thread_url = f"{endpoint}/threads?api-version={api_version}"
                    async with session.post(thread_url, headers=headers, json={}) as response:
                        if response.status != 200:
                            error_text = await response.text()
                            logger.error(f"Failed to create thread: {response.status} - {error_text}")
                            continue
                        thread_data = await response.json()
                        thread_id = thread_data["id"]
                        logger.info(f"Created thread: {thread_id}")
                    
                    # Add message to thread
                    message_url = f"{endpoint}/threads/{thread_id}/messages?api-version={api_version}"
                    message_data = {
                        "role": "user",
                        "content": test_message
                    }
                    async with session.post(message_url, headers=headers, json=message_data) as response:
                        if response.status != 200:
                            error_text = await response.text()
                            logger.error(f"Failed to add message: {response.status} - {error_text}")
                            continue
                        logger.info("Added message to thread")
                    
                    # Run the agent
                    run_url = f"{endpoint}/threads/{thread_id}/runs?api-version={api_version}"
                    run_data = {
                        "assistant_id": orchestrator_agent_id
                    }
                    async with session.post(run_url, headers=headers, json=run_data) as response:
                        if response.status != 200:
                            error_text = await response.text()
                            logger.error(f"Failed to create run: {response.status} - {error_text}")
                            continue
                        run_response = await response.json()
                        run_id = run_response["id"]
                        logger.info(f"Created run: {run_id}")
                    
                    # Poll for completion
                    print("Orchestrator: ", end="", flush=True)
                    run_status_url = f"{endpoint}/threads/{thread_id}/runs/{run_id}?api-version={api_version}"
                    
                    while True:
                        async with session.get(run_status_url, headers=headers) as response:
                            if response.status != 200:
                                error_text = await response.text()
                                logger.error(f"Failed to get run status: {response.status} - {error_text}")
                                break
                            run_status = await response.json()
                            status = run_status["status"]
                            
                            if status in ["completed", "failed", "cancelled"]:
                                logger.info(f"Run completed with status: {status}")
                                break
                            
                            await asyncio.sleep(1)
                    
                    # Get messages
                    messages_url = f"{endpoint}/threads/{thread_id}/messages?api-version={api_version}"
                    async with session.get(messages_url, headers=headers) as response:
                        if response.status != 200:
                            error_text = await response.text()
                            logger.error(f"Failed to get messages: {response.status} - {error_text}")
                            continue
                        messages_data = await response.json()
                        
                        # Find assistant response
                        for message in messages_data.get("data", []):
                            if message["role"] == "assistant":
                                content = message.get("content", [])
                                if content and len(content) > 0:
                                    text = content[0].get("text", {}).get("value", "")
                                    print(text)
                                    break
                    
                    # Delete thread
                    delete_url = f"{endpoint}/threads/{thread_id}?api-version={api_version}"
                    async with session.delete(delete_url, headers=headers) as response:
                        if response.status == 204:
                            logger.info(f"Deleted thread: {thread_id}")
                        else:
                            logger.warning(f"Failed to delete thread: {response.status}")
                            
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(test_orchestrator_direct())