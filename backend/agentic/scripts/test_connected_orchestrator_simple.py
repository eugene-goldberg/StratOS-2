#!/usr/bin/env python3
"""
Simple test of the Main Orchestrator with Connected Agents.
"""

import asyncio
import os
import sys
import json
import logging
from datetime import datetime, timezone
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [%(funcName)s] %(message)s')
logger = logging.getLogger(__name__)

# Add parent directories to path
current_dir = os.path.dirname(os.path.abspath(__file__))
agentic_dir = os.path.dirname(current_dir) 
env_path = os.path.join(agentic_dir, '.env')

logger.info(f"Attempting to load .env file from: {env_path}")
if load_dotenv(env_path):
    logger.info(".env file loaded successfully.")

# Import required modules
try:
    from azure.identity.aio import DefaultAzureCredential
    from semantic_kernel.agents import AzureAIAgent, AzureAIAgentSettings
    from semantic_kernel.contents import ChatMessageContent
except ImportError as e:
    logger.error(f"Error importing required modules: {e}")
    sys.exit(1)

async def test_orchestrator():
    """Test the Main Orchestrator."""
    
    try:
        # Load orchestrator ID
        deployment_config_path = os.path.join(agentic_dir, "deployment_configs", "main_orchestrator_deployment.json")
        with open(deployment_config_path, 'r') as f:
            config = json.load(f)
            orchestrator_id = config['agent_id']
            logger.info(f"Loaded Main Orchestrator ID: {orchestrator_id}")
        
        # Check required environment variables
        settings = AzureAIAgentSettings()
        logger.info(f"Endpoint: {settings.endpoint}")
        
        # Create credential
        credential = DefaultAzureCredential()
        
        async with AzureAIAgent.create_client(credential=credential, settings=settings) as service_client:
            logger.info(f"Successfully created Azure AI Agent service client")
            
            # Get the agent definition
            logger.info(f"Fetching definition for orchestrator ID: {orchestrator_id}...")
            try:
                agent_definition = await service_client.agents.get_agent(agent_id=orchestrator_id)
                logger.info(f"Successfully fetched agent definition for: {agent_definition.name}")
            except Exception as e:
                logger.error(f"Failed to fetch agent definition: {e}", exc_info=True)
                return
            
            # Create a Semantic Kernel AzureAIAgent instance
            orchestrator = AzureAIAgent(
                client=service_client,
                definition=agent_definition
            )
            
            logger.info("Successfully connected to Main Orchestrator")
            
            # Create thread using service client
            thread_response = await service_client.agents.threads.create()
            thread_id = thread_response.id
            logger.info(f"Created thread: {thread_id}")
            
            # Test CEO Log routing
            print("\n" + "="*80)
            print("TEST: CEO Log Routing")
            print("="*80)
            
            message = "I need to record my thoughts about the market downturn and how it might affect our expansion plans"
            print(f"User: {message}")
            print(f"Orchestrator: ", end="", flush=True)
            
            # Use invoke to send message and get response
            try:
                response_parts = []
                async for message_chunk in orchestrator.invoke(message=message, thread_id=thread_id):
                    # Handle different response formats
                    if hasattr(message_chunk, 'content') and message_chunk.content:
                        print(message_chunk.content, end="", flush=True)
                        response_parts.append(message_chunk.content)
                    elif isinstance(message_chunk, list) and message_chunk and hasattr(message_chunk[0], 'content'):
                        print(message_chunk[0].content, end="", flush=True)
                        response_parts.append(message_chunk[0].content)
                
                print()  # Newline after response
                # Convert ChatMessageContent to strings
                full_response = ''.join(str(part.content) if hasattr(part, 'content') else str(part) for part in response_parts)
                logger.info(f"CEO Log routing response length: {len(full_response)} chars")
            except Exception as e:
                logger.error(f"Error during CEO Log routing test: {e}")
                print(f"\nError: {str(e)}")
            
            # Test SWOT Analysis routing
            print("\n" + "="*80)
            print("TEST: SWOT Analysis Routing")
            print("="*80)
            
            message = "Can you perform a SWOT analysis for our new product launch?"
            print(f"User: {message}")
            print(f"Orchestrator: ", end="", flush=True)
            
            # Use invoke to send message and get response
            try:
                response_parts = []
                async for message_chunk in orchestrator.invoke(message=message, thread_id=thread_id):
                    # Handle different response formats
                    if hasattr(message_chunk, 'content') and message_chunk.content:
                        print(message_chunk.content, end="", flush=True)
                        response_parts.append(message_chunk.content)
                    elif isinstance(message_chunk, list) and message_chunk and hasattr(message_chunk[0], 'content'):
                        print(message_chunk[0].content, end="", flush=True)
                        response_parts.append(message_chunk[0].content)
                
                print()  # Newline after response
                # Convert ChatMessageContent to strings
                full_response = ''.join(str(part.content) if hasattr(part, 'content') else str(part) for part in response_parts)
                logger.info(f"SWOT routing response length: {len(full_response)} chars")
            except Exception as e:
                logger.error(f"Error during SWOT routing test: {e}")
                print(f"\nError: {str(e)}")
            
            print("\n" + "="*80)
            print("TESTING COMPLETE")
            print("="*80)
            
    except Exception as e:
        logger.error(f"Error testing orchestrator: {str(e)}", exc_info=True)
        sys.exit(1)
    finally:
        await credential.close()

async def main():
    """Main entry point."""
    print("="*80)
    print("TESTING MAIN ORCHESTRATOR WITH CONNECTED AGENTS")
    print("="*80)
    print(f"\nTest started at: {datetime.now(timezone.utc).isoformat()}")
    
    await test_orchestrator()
    
    print(f"\nTest completed at: {datetime.now(timezone.utc).isoformat()}")

if __name__ == "__main__":
    asyncio.run(main())