#!/usr/bin/env python3
"""
Simple test of CEO Log Agent directly.
"""

import asyncio
import os
import logging
from dotenv import load_dotenv
from azure.identity.aio import DefaultAzureCredential
from azure.ai.projects.aio import AIProjectClient

load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# CEO Log Agent ID from deployment
CEO_LOG_AGENT_ID = "asst_PladvNoVgJiBhGMCZLoBTxG7"

async def test_ceo_log():
    """Test CEO Log Agent directly."""
    
    endpoint = os.getenv("AZURE_AI_PROJECT_CONNECTION_STRING")
    if not endpoint:
        logger.error("AZURE_AI_PROJECT_CONNECTION_STRING not set")
        return
    
    logger.info(f"Testing CEO Log Agent: {CEO_LOG_AGENT_ID}")
    
    async with DefaultAzureCredential() as credential, \
               AIProjectClient(endpoint=endpoint, credential=credential) as client:
        
        try:
            # Create thread
            thread = await client.agents.threads.create()
            logger.info(f"Created thread: {thread.id}")
            
            # Test message
            test_message = """Save this CEO log entry: Had a productive meeting with the sales team today. 
            Q1 revenue exceeded targets by 20%. Team morale is high and we're on track for a strong Q2. 
            Key concern is supply chain delays affecting our new product launch."""
            
            # Add message
            await client.agents.threads.messages.create(
                thread_id=thread.id,
                role="user",
                content=test_message
            )
            logger.info("Added message to thread")
            
            # Create run
            run = await client.agents.threads.runs.create(
                thread_id=thread.id,
                assistant_id=CEO_LOG_AGENT_ID
            )
            logger.info(f"Created run: {run.id}, status: {run.status}")
            
            # Wait for completion
            max_wait = 30  # seconds
            wait_count = 0
            while run.status in ["queued", "in_progress"] and wait_count < max_wait:
                await asyncio.sleep(1)
                wait_count += 1
                run = await client.agents.threads.runs.get(
                    thread_id=thread.id,
                    run_id=run.id
                )
                logger.info(f"Run status: {run.status}")
            
            if run.status == "completed":
                # Get response
                messages = await client.agents.threads.messages.list(thread_id=thread.id)
                
                logger.info("\n" + "="*60)
                logger.info("CEO LOG AGENT RESPONSE:")
                logger.info("="*60)
                
                for msg in messages.data:
                    if msg.role == "assistant":
                        content = msg.content[0].text.value if msg.content else ""
                        logger.info(content)
                        logger.info("="*60)
                        break
            else:
                logger.error(f"Run failed with status: {run.status}")
                if hasattr(run, 'last_error') and run.last_error:
                    logger.error(f"Error: {run.last_error}")
                
        except Exception as e:
            logger.error(f"Error testing CEO Log Agent: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_ceo_log())