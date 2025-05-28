"""
Test Deployed StratOS Agents
Quick verification that agents are deployed and working
"""

import asyncio
import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv(Path(__file__).parent / '.env')
load_dotenv(Path(__file__).parent.parent.parent.parent / '.env')

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from azure.ai.projects.aio import AIProjectClient
from azure.identity.aio import DefaultAzureCredential

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_deployed_agents():
    """Test deployed StratOS agents"""
    
    # Check deployment info
    deployment_file = Path(__file__).parent / "stratos_deployment_info.json"
    if not deployment_file.exists():
        logger.error("No deployment info found. Run deploy_stratos_connected_agents.py first")
        return
    
    with open(deployment_file, 'r') as f:
        deployment_info = json.load(f)
    
    logger.info("="*60)
    logger.info("STRATOS AGENTS DEPLOYMENT INFO")
    logger.info("="*60)
    logger.info(f"Deployment time: {deployment_info['deployment_time']}")
    logger.info(f"Agents deployed: {list(deployment_info['agents'].keys())}")
    logger.info(f"Orchestrator ID: {deployment_info['orchestrator']['id']}")
    
    # Get orchestrator ID
    orchestrator_id = deployment_info['orchestrator']['id']
    
    connection_string = os.getenv("AZURE_AI_PROJECT_CONNECTION_STRING")
    if not connection_string:
        logger.error("AZURE_AI_PROJECT_CONNECTION_STRING not found in environment")
        return
    
    async with DefaultAzureCredential() as credential:
        async with AIProjectClient(
            endpoint=connection_string,
            credential=credential
        ) as client:
            
            # List all agents to verify deployment
            logger.info("\n" + "="*60)
            logger.info("VERIFYING DEPLOYED AGENTS")
            logger.info("="*60)
            
            agents = await client.agents.list_agents()
            agent_list = []
            async for agent in agents:
                agent_list.append({
                    "name": agent.name,
                    "id": agent.id,
                    "model": agent.model
                })
                logger.info(f"Found agent: {agent.name} (ID: {agent.id})")
            
            # Quick test through orchestrator
            logger.info("\n" + "="*60)
            logger.info("TESTING CEO LOG AGENT")
            logger.info("="*60)
            
            thread = await client.agents.create_thread()
            
            # Test CEO Log functionality
            test_query = "Generate tags for this CEO log entry: 'Had a productive meeting with the sales team. Q1 revenue exceeded targets by 20%. Team morale is high.'"
            
            logger.info(f"Query: {test_query}")
            
            # Create message
            await client.agents.create_message(
                thread_id=thread.id,
                role="user",
                content=test_query
            )
            
            # Create run
            run = await client.agents.create_run(
                thread_id=thread.id,
                assistant_id=orchestrator_id
            )
            
            # Wait for completion
            logger.info("Waiting for response...")
            while run.status in ["queued", "in_progress"]:
                await asyncio.sleep(1)
                run = await client.agents.get_run(
                    thread_id=thread.id,
                    run_id=run.id
                )
            
            # Get response
            if run.status == "completed":
                messages = await client.agents.list_messages(thread_id=thread.id)
                for msg in messages.data:
                    if msg.role == "assistant" and msg.created_at >= run.created_at:
                        logger.info("\n✅ SUCCESS - Agent Response:")
                        logger.info("-" * 40)
                        for content in msg.content:
                            if hasattr(content, 'text'):
                                logger.info(content.text.value)
                        logger.info("-" * 40)
                        break
            else:
                logger.error(f"❌ FAILED - Run status: {run.status}")
                if hasattr(run, 'last_error'):
                    logger.error(f"Error: {run.last_error}")
            
            # Cleanup
            await client.agents.delete_thread(thread_id=thread.id)
            
            logger.info("\n" + "="*60)
            logger.info("TEST COMPLETE")
            logger.info("="*60)

if __name__ == "__main__":
    asyncio.run(test_deployed_agents())