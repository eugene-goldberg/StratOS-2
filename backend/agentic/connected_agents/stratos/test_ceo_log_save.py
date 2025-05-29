#!/usr/bin/env python3
"""
Test CEO Log Agent by saving a CEO log entry
"""

import asyncio
import os
import logging
from datetime import datetime
from dotenv import load_dotenv
from azure.identity.aio import DefaultAzureCredential
from azure.ai.projects.aio import AIProjectClient

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# CEO Log Agent ID from deployment
CEO_LOG_AGENT_ID = "asst_85MtpKLDOQA9ttsUckByGTKD"

async def test_save_ceo_log():
    """Test saving a CEO log entry through the agent."""
    
    endpoint = os.getenv("AZURE_AI_PROJECT_CONNECTION_STRING")
    if not endpoint:
        logger.error("AZURE_AI_PROJECT_CONNECTION_STRING not set")
        return
    
    logger.info(f"Testing CEO Log Agent: {CEO_LOG_AGENT_ID}")
    logger.info("="*60)
    
    async with DefaultAzureCredential() as credential, \
               AIProjectClient(endpoint=endpoint, credential=credential) as client:
        
        try:
            # Create thread
            thread = await client.agents.threads.create()
            logger.info(f"Created thread: {thread.id}")
            
            # CEO log entry to save
            log_entry = """Save this CEO log entry: Had a productive quarterly review meeting with the board today. 
            We discussed our AI strategy and the board approved a 30% increase in R&D budget for next quarter. 
            The team's morale is high after hitting Q1 targets. Main concern is potential supply chain disruptions 
            due to geopolitical tensions. Need to accelerate our supplier diversification initiative.
            
            Category: strategic_planning
            User ID: ceo_test_user_001"""
            
            logger.info("\nSubmitting CEO log entry:")
            logger.info("-" * 60)
            logger.info(log_entry)
            logger.info("-" * 60)
            
            # Add message to thread
            await client.agents.threads.messages.create(
                thread_id=thread.id,
                role="user",
                content=log_entry
            )
            logger.info("Added message to thread")
            
            # Create run with the CEO Log agent
            run = await client.agents.threads.runs.create(
                thread_id=thread.id,
                assistant_id=CEO_LOG_AGENT_ID
            )
            logger.info(f"\nCreated run: {run.id}")
            logger.info(f"Initial status: {run.status}")
            
            # Wait for completion with detailed status updates
            max_wait = 60  # seconds
            wait_count = 0
            last_status = run.status
            
            while run.status in ["queued", "in_progress", "requires_action"] and wait_count < max_wait:
                await asyncio.sleep(1)
                wait_count += 1
                
                run = await client.agents.threads.runs.get(
                    thread_id=thread.id,
                    run_id=run.id
                )
                
                # Log status changes
                if run.status != last_status:
                    logger.info(f"Status changed: {last_status} → {run.status}")
                    last_status = run.status
                
                # Check for required actions (function calls)
                if run.status == "requires_action":
                    logger.info("Agent is executing function calls...")
            
            logger.info(f"\nFinal status: {run.status}")
            logger.info(f"Time elapsed: {wait_count} seconds")
            
            if run.status == "completed":
                # Get response messages
                messages = await client.agents.threads.messages.list(thread_id=thread.id)
                
                logger.info("\n" + "="*60)
                logger.info("CEO LOG AGENT RESPONSE:")
                logger.info("="*60)
                
                # Find assistant's response
                for msg in messages.data:
                    if msg.role == "assistant":
                        if msg.content:
                            for content in msg.content:
                                if hasattr(content, 'text') and content.text:
                                    logger.info(content.text.value)
                        break
                
                logger.info("="*60)
                
                logger.info("\n✅ Test completed successfully!")
                
            elif run.status == "failed":
                logger.error(f"Run failed!")
                if hasattr(run, 'last_error') and run.last_error:
                    logger.error(f"Error details: {run.last_error}")
            else:
                logger.warning(f"Run ended with unexpected status: {run.status}")
                
        except Exception as e:
            logger.error(f"Error during test: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    logger.info("Starting CEO Log Save Test")
    logger.info(f"Timestamp: {datetime.now().isoformat()}")
    asyncio.run(test_save_ceo_log())