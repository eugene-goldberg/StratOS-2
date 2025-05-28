#!/usr/bin/env python3
"""
Check what's happening in a weather agent thread.
"""

import asyncio
import os
import logging
from dotenv import load_dotenv
from azure.identity.aio import DefaultAzureCredential
from azure.ai.projects.aio import AIProjectClient

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

async def check_weather_thread():
    """Create a thread and check messages."""
    
    weather_agent_id = "asst_OmmrIuA3PfIfczyFtY9ui0xz"
    endpoint = os.getenv("AZURE_AI_PROJECT_CONNECTION_STRING")
    
    async with DefaultAzureCredential() as credential, \
               AIProjectClient(endpoint=endpoint, credential=credential) as client:
        
        # Create a thread
        thread = await client.agents.create_thread()
        logger.info(f"Created thread: {thread.id}")
        
        # Add a message
        message = await client.agents.create_message(
            thread_id=thread.id,
            role="user",
            content="What's the weather in Seattle? Please show any code you run."
        )
        logger.info(f"Added message: {message.id}")
        
        # Create a run
        run = await client.agents.create_run(
            thread_id=thread.id,
            assistant_id=weather_agent_id
        )
        logger.info(f"Created run: {run.id}")
        
        # Wait a bit
        await asyncio.sleep(10)
        
        # Check run status
        run_status = await client.agents.get_run(
            thread_id=thread.id,
            run_id=run.id
        )
        logger.info(f"Run status: {run_status.status}")
        
        # List messages
        messages = client.agents.list_messages(thread_id=thread.id)
        async for msg in messages:
            logger.info(f"\nMessage from {msg.role}:")
            if hasattr(msg.content, '__iter__'):
                for content in msg.content:
                    if hasattr(content, 'text'):
                        logger.info(f"Text: {content.text.value}")
                    else:
                        logger.info(f"Content type: {type(content)}")
            else:
                logger.info(f"Content: {msg.content}")
                
        # Check run steps
        steps = client.agents.list_run_steps(
            thread_id=thread.id,
            run_id=run.id
        )
        async for step in steps:
            logger.info(f"\nStep: {step.type}")
            if hasattr(step, 'step_details'):
                logger.info(f"Details: {step.step_details}")

if __name__ == "__main__":
    asyncio.run(check_weather_thread())