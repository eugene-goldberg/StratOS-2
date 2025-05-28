"""
Simple test for CEO Log Agent
Quick smoke test to verify CEO Log Agent delegation is working
Run time: ~30 seconds
"""

import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from connected_agents directory
load_dotenv(Path(__file__).parent.parent.parent / '.env')

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from azure.ai.projects.aio import AIProjectClient
from azure.identity.aio import DefaultAzureCredential
from semantic_kernel.agents import AzureAIAgent

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_simple_ceo():
    """Simple test for CEO Log Agent"""
    
    # Get orchestrator ID
    orchestrator_id = os.getenv("STRATOS_ORCHESTRATOR_ID")
    if not orchestrator_id:
        logger.error("STRATOS_ORCHESTRATOR_ID not found in environment")
        return
    
    logger.info(f"Testing with Orchestrator ID: {orchestrator_id}")
    
    connection_string = os.getenv("AZURE_AI_PROJECT_CONNECTION_STRING")
    if not connection_string:
        logger.error("AZURE_AI_PROJECT_CONNECTION_STRING not found in environment")
        return
    
    async with DefaultAzureCredential() as credential:
        async with AIProjectClient(
            endpoint=connection_string,
            credential=credential
        ) as client:
            
            # Get orchestrator definition
            orchestrator_def = await client.agents.get_agent(agent_id=orchestrator_id)
            logger.info(f"Orchestrator: {orchestrator_def.name}")
            logger.info(f"Tools available: {len(orchestrator_def.tools) if orchestrator_def.tools else 0}")
            
            # Create agent instance
            orchestrator_agent = AzureAIAgent(
                client=client,
                definition=orchestrator_def
            )
            
            # Simple test query
            query = "Generate tags for this CEO log entry: 'Team meeting went well. Discussed Q2 roadmap and AI strategy.'"
            logger.info(f"\nQuery: {query}")
            
            # Invoke agent
            response = ""
            async for part in orchestrator_agent.invoke(messages=query):
                if hasattr(part, 'content') and part.content:
                    response += str(part.content)
            
            logger.info("\n✅ Response:")
            logger.info(response)
            
            # Check for proper delegation
            if "ceo log specialist" in response.lower():
                logger.info("\n✅ CEO Log delegation detected!")
            else:
                logger.error("❌ No CEO Log delegation found in response")

if __name__ == "__main__":
    asyncio.run(test_simple_ceo())