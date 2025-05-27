#!/usr/bin/env python3
"""
Test MainOrchestratorAgent using REST API directly
"""

import os
import asyncio
import aiohttp
import logging
from dotenv import load_dotenv
from azure.identity.aio import DefaultAzureCredential

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
current_dir = os.path.dirname(os.path.abspath(__file__))
agentic_dir = os.path.dirname(current_dir)
env_path = os.path.join(agentic_dir, '.env')
load_dotenv(env_path)

async def test_orchestrator():
    """Test the MainOrchestratorAgent via REST API"""
    
    # Configuration
    orchestrator_id = "asst_LgNjAIwEDV5wQcogIUmGf4qq"
    endpoint = os.getenv("AZURE_AI_AGENT_ENDPOINT")
    api_version = os.getenv("AZURE_AI_AGENT_API_VERSION", "2024-12-01-preview")
    
    if not endpoint:
        logger.error("AZURE_AI_AGENT_ENDPOINT not set")
        return
        
    logger.info(f"Using endpoint: {endpoint}")
    logger.info(f"Testing orchestrator: {orchestrator_id}")
    
    # Test message
    test_message = "I need to record my thoughts about the market downturn and its effect on Q3 projections."
    
    try:
        # Get credential
        async with DefaultAzureCredential() as credential:
            # Get token for the correct scope - Azure AI services use management scope
            token = await credential.get_token("https://management.azure.com/.default")
            
            headers = {
                "Authorization": f"Bearer {token.token}",
                "Content-Type": "application/json"
            }
            
            async with aiohttp.ClientSession() as session:
                # 1. Create thread
                logger.info("Creating thread...")
                thread_url = f"{endpoint}/threads?api-version={api_version}"
                async with session.post(thread_url, headers=headers, json={}) as response:
                    if response.status != 200:
                        error = await response.text()
                        logger.error(f"Failed to create thread: {response.status} - {error}")
                        return
                    thread_data = await response.json()
                    thread_id = thread_data["id"]
                    logger.info(f"Created thread: {thread_id}")
                
                # 2. Add message
                logger.info("Adding message to thread...")
                message_url = f"{endpoint}/threads/{thread_id}/messages?api-version={api_version}"
                message_data = {
                    "role": "user",
                    "content": test_message
                }
                async with session.post(message_url, headers=headers, json=message_data) as response:
                    if response.status != 200:
                        error = await response.text()
                        logger.error(f"Failed to add message: {response.status} - {error}")
                        return
                    logger.info("Message added successfully")
                
                # 3. Create run
                logger.info("Creating run...")
                run_url = f"{endpoint}/threads/{thread_id}/runs?api-version={api_version}"
                run_data = {
                    "assistant_id": orchestrator_id
                }
                async with session.post(run_url, headers=headers, json=run_data) as response:
                    if response.status != 200:
                        error = await response.text()
                        logger.error(f"Failed to create run: {response.status} - {error}")
                        return
                    run_response = await response.json()
                    run_id = run_response["id"]
                    logger.info(f"Created run: {run_id}")
                
                # 4. Poll for completion
                logger.info("Waiting for completion...")
                run_status_url = f"{endpoint}/threads/{thread_id}/runs/{run_id}?api-version={api_version}"
                
                while True:
                    async with session.get(run_status_url, headers=headers) as response:
                        if response.status != 200:
                            error = await response.text()
                            logger.error(f"Failed to get run status: {response.status} - {error}")
                            break
                        
                        run_status = await response.json()
                        status = run_status["status"]
                        logger.info(f"Run status: {status}")
                        
                        if status == "completed":
                            logger.info("Run completed successfully")
                            break
                        elif status in ["failed", "cancelled", "expired"]:
                            logger.error(f"Run failed with status: {status}")
                            if "last_error" in run_status:
                                logger.error(f"Error: {run_status['last_error']}")
                            break
                        
                        await asyncio.sleep(2)
                
                # 5. Get messages
                logger.info("Getting messages...")
                messages_url = f"{endpoint}/threads/{thread_id}/messages?api-version={api_version}"
                async with session.get(messages_url, headers=headers) as response:
                    if response.status != 200:
                        error = await response.text()
                        logger.error(f"Failed to get messages: {response.status} - {error}")
                        return
                    
                    messages_data = await response.json()
                    
                    # Display conversation
                    print(f"\n{'='*60}")
                    print(f"User: {test_message}")
                    
                    # Find assistant response
                    for message in messages_data.get("data", []):
                        if message["role"] == "assistant":
                            content = message.get("content", [])
                            if content and len(content) > 0:
                                text = content[0].get("text", {}).get("value", "")
                                print(f"Orchestrator: {text}")
                                break
                
                # 6. Delete thread
                logger.info("Cleaning up thread...")
                delete_url = f"{endpoint}/threads/{thread_id}?api-version={api_version}"
                async with session.delete(delete_url, headers=headers) as response:
                    if response.status == 204:
                        logger.info("Thread deleted successfully")
                    else:
                        logger.warning(f"Failed to delete thread: {response.status}")
                        
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(test_orchestrator())