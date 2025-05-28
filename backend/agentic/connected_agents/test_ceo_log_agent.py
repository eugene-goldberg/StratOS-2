"""
Test CEO Log Agent through Orchestrator
Following the weather agent test pattern
"""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from azure.ai.projects.aio import AIProjectClient
from azure.identity.aio import DefaultAzureCredential
from backend.agentic.config.settings import get_settings

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_ceo_log_agent():
    """Test CEO Log Agent through orchestrator"""
    settings = get_settings()
    
    # Get orchestrator ID from environment
    orchestrator_id = os.getenv("STRATOS_ORCHESTRATOR_ID")
    if not orchestrator_id:
        logger.error("STRATOS_ORCHESTRATOR_ID not found in environment")
        return
    
    logger.info(f"Testing with Orchestrator ID: {orchestrator_id}")
    
    connection_string = settings.get_project_connection_string()
    
    async with DefaultAzureCredential() as credential:
        async with AIProjectClient(
            endpoint=connection_string,
            credential=credential
        ) as client:
            
            # Create a thread for conversation
            thread = await client.agents.create_thread()
            logger.info(f"Created thread: {thread.id}")
            
            # Test cases for CEO Log Agent
            test_queries = [
                "Save this CEO log entry: Met with the board about Q1 results. Revenue exceeded expectations by 15%. Team morale is high after the product launch success.",
                "Generate tags for this entry: 'Concerned about competitor's new AI features. We need to accelerate our ML roadmap.'",
                "Search for entries about team morale",
                "Extract insights from recent entries about product strategy",
                "Summarize this entry: 'Had a breakthrough conversation with the CTO about our cloud migration strategy. We identified three key phases that could reduce costs by 30% while improving scalability.'"
            ]
            
            for i, query in enumerate(test_queries, 1):
                logger.info(f"\n{'='*60}")
                logger.info(f"Test {i}: {query[:80]}...")
                logger.info("="*60)
                
                # Add user message
                message = await client.agents.create_message(
                    thread_id=thread.id,
                    role="user",
                    content=query
                )
                
                # Create run and wait for completion
                run = await client.agents.create_run(
                    thread_id=thread.id,
                    assistant_id=orchestrator_id
                )
                
                # Wait for run completion
                logger.info(f"Waiting for run {run.id} to complete...")
                while run.status in ["queued", "in_progress", "requires_action"]:
                    await asyncio.sleep(1)
                    run = await client.agents.get_run(
                        thread_id=thread.id,
                        run_id=run.id
                    )
                    logger.info(f"Run status: {run.status}")
                
                if run.status == "completed":
                    # Get messages
                    messages = await client.agents.list_messages(thread_id=thread.id)
                    
                    # Find the assistant's response
                    for msg in messages.data:
                        if msg.role == "assistant" and msg.created_at >= run.created_at:
                            logger.info("\nAssistant Response:")
                            logger.info("-" * 40)
                            for content in msg.content:
                                if hasattr(content, 'text'):
                                    logger.info(content.text.value)
                            logger.info("-" * 40)
                            break
                else:
                    logger.error(f"Run failed with status: {run.status}")
                    if hasattr(run, 'last_error'):
                        logger.error(f"Error: {run.last_error}")
                
                # Small delay between tests
                await asyncio.sleep(2)
            
            # Cleanup
            await client.agents.delete_thread(thread_id=thread.id)
            logger.info(f"\nDeleted thread: {thread.id}")

if __name__ == "__main__":
    asyncio.run(test_ceo_log_agent())