"""
Test North Star Agent Delegation through Orchestrator
"""

import asyncio
import os
import sys
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
from semantic_kernel.agents import AzureAIAgent

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_orchestrator_north_star():
    """Test North Star delegation through orchestrator"""
    
    orchestrator_id = os.getenv('STRATOS_ORCHESTRATOR_ID')
    if not orchestrator_id:
        logger.error("STRATOS_ORCHESTRATOR_ID not found in environment")
        return
        
    connection_string = os.getenv('AZURE_AI_PROJECT_CONNECTION_STRING')
    if not connection_string:
        logger.error("AZURE_AI_PROJECT_CONNECTION_STRING not found in environment")
        return
    
    logger.info(f"Testing Orchestrator ID: {orchestrator_id}")
    
    async with DefaultAzureCredential() as credential:
        async with AIProjectClient(
            endpoint=connection_string,
            credential=credential
        ) as client:
            try:
                # Get orchestrator
                orchestrator_def = await client.agents.get_agent(agent_id=orchestrator_id)
                logger.info(f'Orchestrator: {orchestrator_def.name}')
                logger.info(f'Tools available: {len(orchestrator_def.tools) if orchestrator_def.tools else 0}')
                
                # Create agent instance
                orchestrator_agent = AzureAIAgent(
                    client=client,
                    definition=orchestrator_def
                )
                
                # Test 1: Purpose definition
                logger.info("\n" + "="*60)
                logger.info("TEST 1: Purpose Definition Delegation")
                logger.info("="*60)
                
                query = 'Help me define our organizational purpose. We are focused on democratizing AI technology.'
                logger.info(f'Query: {query}')
                
                response = ''
                async for part in orchestrator_agent.invoke(messages=query):
                    if hasattr(part, 'content') and part.content:
                        response += str(part.content)
                
                logger.info('\nOrchestrator Response:')
                logger.info(response)
                
                # Check for proper delegation
                if 'north star specialist' in response.lower():
                    logger.info('\n✅ North Star delegation detected!')
                else:
                    logger.error('❌ No North Star delegation found in response')
                
                # Test 2: Vision creation
                logger.info("\n" + "="*60)
                logger.info("TEST 2: Vision Creation Delegation")
                logger.info("="*60)
                
                query = 'Create a vision statement for becoming the leader in AI strategy by 2030'
                logger.info(f'Query: {query}')
                
                response = ''
                async for part in orchestrator_agent.invoke(messages=query):
                    if hasattr(part, 'content') and part.content:
                        response += str(part.content)
                
                logger.info('\nOrchestrator Response:')
                logger.info(response)
                
                # Test 3: Values management
                logger.info("\n" + "="*60)
                logger.info("TEST 3: Values Management Delegation")
                logger.info("="*60)
                
                query = 'Add our core values: Innovation and Customer Success'
                logger.info(f'Query: {query}')
                
                response = ''
                async for part in orchestrator_agent.invoke(messages=query):
                    if hasattr(part, 'content') and part.content:
                        response += str(part.content)
                
                logger.info('\nOrchestrator Response:')
                logger.info(response)
                
                # Test 4: CEO Log (should still work)
                logger.info("\n" + "="*60)
                logger.info("TEST 4: CEO Log Delegation (Verify Still Works)")
                logger.info("="*60)
                
                query = 'Save this CEO log entry: Team meeting went great, discussed AI roadmap'
                logger.info(f'Query: {query}')
                
                response = ''
                async for part in orchestrator_agent.invoke(messages=query):
                    if hasattr(part, 'content') and part.content:
                        response += str(part.content)
                
                logger.info('\nOrchestrator Response:')
                logger.info(response)
                
                logger.info("\n" + "="*60)
                logger.info("DELEGATION TEST SUMMARY")
                logger.info("="*60)
                logger.info("Expected to see:")
                logger.info("- 'I'll connect you with the North Star specialist for strategic foundation guidance!'")
                logger.info("- 'I'll connect you with the CEO Log specialist for strategic insights!'")
                logger.info("="*60)
                
            except Exception as e:
                logger.error(f"Error testing orchestrator: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(test_orchestrator_north_star())