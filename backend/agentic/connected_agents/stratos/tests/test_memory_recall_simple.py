"""
Simple test for Memory Recall Agent through orchestrator
Quick smoke test to verify delegation is working
"""

import os
import asyncio
import logging
import json
from pathlib import Path
from dotenv import load_dotenv
from azure.ai.projects.aio import AIProjectClient
from azure.identity.aio import DefaultAzureCredential
from semantic_kernel.agents import AzureAIAgent

# Load environment variables
load_dotenv(Path(__file__).parent.parent.parent / '.env')

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_deployment_info():
    """Load deployment info from file"""
    archive_dir = Path(__file__).parent.parent / "archive"
    deployment_file = archive_dir / "stratos_deployment_info.json"
    
    if not deployment_file.exists():
        logger.error(f"Deployment file not found: {deployment_file}")
        return None
        
    with open(deployment_file, 'r') as f:
        return json.load(f)

async def test_memory_recall_simple():
    """Test Memory Recall agent through orchestrator"""
    logger.info("=== Memory Recall Agent Simple Test ===")
    
    # Load deployment info
    deployment_info = load_deployment_info()
    if not deployment_info:
        logger.error("No deployment info found. Please run deployment script first.")
        return
    
    orchestrator_id = deployment_info["orchestrator"]["id"]
    logger.info(f"Using orchestrator: {orchestrator_id}")
    
    # Get connection string
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
            
            # Test query for Memory Recall
            query = "Search for any previous decisions about customer experience improvements"
            logger.info(f"\n📤 Query: {query}")
            
            # Invoke agent
            response = ""
            async for part in orchestrator_agent.invoke(messages=query):
                if hasattr(part, 'content') and part.content:
                    response += str(part.content)
            
            logger.info("\n📥 Response:")
            logger.info("-" * 60)
            logger.info(response)
            logger.info("-" * 60)
            
            # Check for proper delegation
            if "memory recall specialist" in response.lower():
                logger.info("\n✅ Memory Recall delegation detected!")
                logger.info("✅ Test passed - Memory Recall agent responded successfully")
            else:
                logger.warning("⚠️ No Memory Recall delegation detected in response")
            
            logger.info("\n✅ Simple test completed")

if __name__ == "__main__":
    asyncio.run(test_memory_recall_simple())