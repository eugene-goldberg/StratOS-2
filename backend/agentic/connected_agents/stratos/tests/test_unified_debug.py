"""
Debug version of unified test to identify the issue
"""

import asyncio
import logging
from base_agent_test import BaseAgentTest
from typing import List, Dict

# Configure more detailed logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class CEOLogAgentDebugTest(BaseAgentTest):
    """Debug test for CEO Log Agent"""
    
    def __init__(self):
        super().__init__("CEO Log Agent")
    
    def get_test_scenarios(self) -> List[Dict[str, str]]:
        return [
            {
                "name": "tag_generation",
                "query": "Generate tags for this CEO log entry: 'Team meeting went well. Discussed Q2 roadmap and AI strategy.'"
            }
        ]


async def test_with_debugging():
    """Run test with extra debugging"""
    logger.info("Starting debug test...")
    
    try:
        test = CEOLogAgentDebugTest()
        
        # Load deployment info first
        logger.info("Loading deployment info...")
        deployment_info = test.load_deployment_info()
        logger.info(f"Deployment info loaded: {deployment_info}")
        
        # Create client manually to debug
        from azure.ai.projects.aio import AIProjectClient
        from azure.identity.aio import DefaultAzureCredential
        import os
        
        connection_string = os.getenv("AZURE_AI_PROJECT_CONNECTION_STRING")
        logger.info(f"Connection string present: {bool(connection_string)}")
        
        # Try a simple connection first
        logger.info("Creating credential...")
        async with DefaultAzureCredential() as credential:
            logger.info("Credential created successfully")
            
            logger.info("Creating AI Project client...")
            async with AIProjectClient(
                endpoint=connection_string,
                credential=credential
            ) as client:
                logger.info("Client created successfully")
                
                # Try to fetch orchestrator
                logger.info(f"Fetching orchestrator {test.orchestrator_id}...")
                orchestrator_def = await client.agents.get_agent(agent_id=test.orchestrator_id)
                logger.info(f"Orchestrator fetched: {orchestrator_def.name}")
                
                # Create thread with retry logic
                logger.info("Creating thread...")
                max_retries = 3
                retry_delay = 2
                
                for attempt in range(max_retries):
                    try:
                        thread = await client.agents.create_thread()
                        logger.info(f"Thread created successfully: {thread.id}")
                        break
                    except Exception as e:
                        logger.error(f"Thread creation failed (attempt {attempt + 1}/{max_retries}): {str(e)}")
                        if attempt < max_retries - 1:
                            logger.info(f"Waiting {retry_delay} seconds before retry...")
                            await asyncio.sleep(retry_delay)
                        else:
                            raise
                
                logger.info("Debug test completed successfully!")
                
    except Exception as e:
        logger.error(f"Debug test failed: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())


if __name__ == "__main__":
    asyncio.run(test_with_debugging())