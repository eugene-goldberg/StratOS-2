#!/usr/bin/env python3
"""
Test script for deployed MainOrchestratorAgent - non-interactive version
"""

import asyncio
import os
import sys
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [%(funcName)s] %(message)s')
logger = logging.getLogger(__name__)

# Path setup
current_dir = os.path.dirname(os.path.abspath(__file__))
agentic_dir = os.path.dirname(current_dir) 
env_path = os.path.join(agentic_dir, '.env')

logger.info(f"Loading .env from: {env_path}")
load_dotenv(env_path)

# Import required modules
try:
    from azure.identity.aio import DefaultAzureCredential
    from semantic_kernel.agents import AzureAIAgent, AzureAIAgentSettings
    from semantic_kernel.contents import ChatMessageContent
except ImportError as e:
    logger.error(f"Error importing required modules: {e}")
    sys.exit(1)

async def test_orchestrator():
    """Test the deployed MainOrchestratorAgent"""
    
    # Known orchestrator ID from deployment
    orchestrator_agent_id = "asst_PkBVaNwenBlxV3rfPuiunywU"
    
    # Test message
    test_message = "I need to record my thoughts about the market downturn and its effect on Q3 projections."
    
    try:
        # Check environment variables
        required_vars = [
            "AZURE_AI_AGENT_PROJECT_NAME", "AZURE_AI_AGENT_PROJECT_HUB_NAME",
            "AZURE_AI_AGENT_PROJECT_RESOURCE_GROUP", "AZURE_AI_AGENT_PROJECT_SUBSCRIPTION_ID",
            "AZURE_AI_AGENT_API_VERSION", "AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME"
        ]
        
        logger.info("Checking required environment variables:")
        for var in required_vars:
            val = os.getenv(var)
            if not val:
                logger.error(f"Missing required variable: {var}")
                return
            logger.info(f"  {var}: {val}")
        
        settings = AzureAIAgentSettings()
        logger.info(f"Settings endpoint: {settings.endpoint}")
        logger.info(f"Settings model: {settings.model_deployment_name}")
        logger.info(f"Settings API version: {settings.api_version}")
        
        if not settings.endpoint:
            logger.error("No endpoint resolved!")
            return
            
        async with DefaultAzureCredential(exclude_interactive_browser_credential=False) as credential:
            async with AzureAIAgent.create_client(credential=credential, settings=settings) as service_client:
                logger.info("Successfully created Azure AI Agent service client")
                
                # Get agent definition
                logger.info(f"Fetching agent definition for ID: {orchestrator_agent_id}")
                agent_definition = await service_client.agents.get_agent(agent_id=orchestrator_agent_id)
                logger.info(f"Found agent: {agent_definition.name}")
                
                # Create SK agent
                sk_orchestrator = AzureAIAgent(
                    client=service_client,
                    definition=agent_definition
                )
                
                # Create thread
                logger.info("Creating conversation thread...")
                thread = await service_client.agents.create_thread()
                thread_id = thread.id
                logger.info(f"Created thread: {thread_id}")
                
                try:
                    # Send message and get response
                    print(f"\nUser: {test_message}")
                    print(f"Orchestrator: ", end="", flush=True)
                    
                    full_response = ""
                    async for chunk in sk_orchestrator.invoke(message=test_message, thread_id=thread_id):
                        if isinstance(chunk, ChatMessageContent) and chunk.content:
                            print(chunk.content, end="", flush=True)
                            full_response += chunk.content
                        elif isinstance(chunk, list) and chunk and isinstance(chunk[0], ChatMessageContent) and chunk[0].content:
                            print(chunk[0].content, end="", flush=True)
                            full_response += chunk[0].content
                    
                    print("\n")
                    logger.info(f"Response received (length: {len(full_response)})")
                    
                finally:
                    # Clean up thread
                    logger.info(f"Deleting thread: {thread_id}")
                    await service_client.agents.delete_thread(thread_id=thread_id)
                    logger.info("Thread deleted successfully")
                    
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(test_orchestrator())