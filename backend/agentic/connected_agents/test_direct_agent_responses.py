#!/usr/bin/env python3
"""
Test direct agent invocation to see actual responses.
This bypasses the orchestrator to show what the agents actually return.
"""

import asyncio
import os
import logging
import json
from pathlib import Path
from dotenv import load_dotenv
from azure.identity.aio import DefaultAzureCredential
from azure.ai.projects.aio import AIProjectClient

load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def test_direct_agents():
    """Test agents directly to see their actual responses."""
    
    # Agent IDs from deployment
    agents = {
        "CEO Log": "asst_nbyTtjWspeOEUH5RurvFPNOF",
        "North Star": "asst_kYWqsCwR0JwbovT4zLbRAhNy", 
        "Memory Recall": "asst_SkvhW3DZTtnufdTbmSqkFcpa"
    }
    
    endpoint = os.getenv("AZURE_AI_PROJECT_CONNECTION_STRING")
    
    async with DefaultAzureCredential() as credential, \
               AIProjectClient(endpoint=endpoint, credential=credential) as client:
        
        # Test each agent directly
        test_queries = {
            "CEO Log": "Generate tags for this entry: Team discussed new AI product launch timeline and budget",
            "North Star": "Define a north star metric for customer retention in SaaS",
            "Memory Recall": "What were the key decisions from our last strategic planning session?"
        }
        
        for agent_name, agent_id in agents.items():
            logger.info(f"\n{'='*80}")
            logger.info(f"TESTING {agent_name} DIRECTLY")
            logger.info(f"{'='*80}")
            logger.info(f"Agent ID: {agent_id}")
            logger.info(f"Query: {test_queries[agent_name]}")
            
            try:
                # Create thread
                thread = await client.agents.threads.create()
                
                # Add message
                await client.agents.threads.messages.create(
                    thread_id=thread.id,
                    role="user",
                    content=test_queries[agent_name]
                )
                
                # Create run with the agent directly
                run = await client.agents.threads.runs.create(
                    thread_id=thread.id,
                    assistant_id=agent_id
                )
                
                # Wait for completion
                while run.status in ["queued", "in_progress"]:
                    await asyncio.sleep(1)
                    run = await client.agents.threads.runs.get(
                        thread_id=thread.id,
                        run_id=run.id
                    )
                
                # Get response
                messages = await client.agents.threads.messages.list(thread_id=thread.id)
                
                logger.info(f"\nACTUAL AGENT RESPONSE:")
                logger.info("-" * 60)
                
                for msg in messages.data:
                    if msg.role == "assistant":
                        content = msg.content[0].text.value if msg.content else ""
                        logger.info(content)
                        break
                
                logger.info("-" * 60)
                
            except Exception as e:
                logger.error(f"Error testing {agent_name}: {e}")
            
            await asyncio.sleep(2)  # Rate limiting


if __name__ == "__main__":
    asyncio.run(test_direct_agents())