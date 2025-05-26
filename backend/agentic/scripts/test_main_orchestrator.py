#!/usr/bin/env python3
"""
Test communication with the deployed Main Orchestrator.

This script demonstrates how to send requests to the Main Orchestrator
and receive routing decisions for the Unified MAS.
"""

import asyncio
import os
import sys
import logging
from datetime import datetime, timezone
from dotenv import load_dotenv
import json

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
else:
    logger.warning(f".env file not found at '{env_path}' or it's empty.")

# Import required modules
try:
    from azure.identity.aio import DefaultAzureCredential
    from semantic_kernel.agents import AzureAIAgent, AzureAIAgentSettings
    from semantic_kernel.contents import ChatMessageContent
    from semantic_kernel.contents.chat_history import ChatHistory
except ImportError as e:
    logger.error(f"Error importing required modules: {e}")
    logger.error("Please ensure 'semantic-kernel[azure]' and 'azure-identity' are installed.")
    sys.exit(1)

# Test scenarios for the Main Orchestrator
TEST_SCENARIOS = [
    {
        "name": "CEO Log Entry",
        "request": {
            "task_type": "CREATE_CEO_LOG",
            "user_id": "test-user-123",
            "payload": {
                "text": "Had a great meeting with the product team. We need to focus on improving user retention.",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        }
    },
    {
        "name": "SWOT Analysis Request",
        "request": {
            "user_id": "test-user-123",
            "user_query": "I want to do a SWOT analysis for our new product launch",
            "payload": {}
        }
    },
    {
        "name": "North Star Query",
        "request": {
            "task_type": "GET_NORTH_STAR_DETAILS",
            "user_id": "test-user-123",
            "payload": {
                "include": ["vision", "values", "strategic_goals"]
            }
        }
    },
    {
        "name": "Resource Allocation",
        "request": {
            "user_id": "test-user-123",
            "user_query": "Help me allocate resources for Q2 initiatives",
            "payload": {
                "quarter": "Q2",
                "year": 2025
            }
        }
    },
    {
        "name": "Risk Detection",
        "request": {
            "user_id": "test-user-123",
            "user_query": "What are the potential risks in our current strategy?",
            "session_context": {
                "last_agent_used": "SWOTTOWSAgent",
                "session_id": "test-session-123"
            }
        }
    },
    {
        "name": "Ambiguous Request",
        "request": {
            "user_id": "test-user-123",
            "user_query": "I need help with planning",
            "payload": {}
        }
    }
]

async def test_orchestrator_communication():
    """Test communication with the Main Orchestrator."""
    
    try:
        # Initialize settings
        settings = AzureAIAgentSettings()
        logger.info(f"--- AzureAIAgentSettings initialized ---")
        logger.info(f"  Endpoint: {settings.endpoint}")
        logger.info(f"  API Version: {settings.api_version}")
        logger.info(f"  Model: {settings.model_deployment_name}")
        
        # Create credential
        credential = DefaultAzureCredential()
        
        # Get the Main Orchestrator ID from deployment config
        deployment_config_path = os.path.join(agentic_dir, "deployment_configs", "main_orchestrator_deployment.json")
        if os.path.exists(deployment_config_path):
            with open(deployment_config_path, 'r') as f:
                deployment_info = json.load(f)
                main_orchestrator_id = deployment_info.get("agent_id")
                logger.info(f"Main Orchestrator ID from deployment: {main_orchestrator_id}")
        else:
            logger.error("Main Orchestrator deployment config not found!")
            return
        
        # Create client
        async with AzureAIAgent.create_client(credential=credential, settings=settings) as client:
            logger.info("Successfully connected to Azure AI Agent Service")
            
            # Get the Main Orchestrator agent
            main_orchestrator = await client.agents.get_agent(main_orchestrator_id)
            logger.info(f"Retrieved Main Orchestrator: {main_orchestrator.name}")
            
            # Create an AzureAIAgent instance
            orchestrator_agent = AzureAIAgent(
                client=client,
                definition=main_orchestrator
            )
            
            # Test each scenario
            for i, scenario in enumerate(TEST_SCENARIOS, 1):
                print(f"\n{'='*80}")
                print(f"TEST SCENARIO {i}: {scenario['name']}")
                print(f"{'='*80}")
                
                # Create a new thread for each test
                thread = await client.beta.threads.create()
                logger.info(f"Created thread: {thread.id}")
                
                # Prepare the message
                request_json = json.dumps(scenario['request'], indent=2)
                message = f"Route this request:\n```json\n{request_json}\n```"
                
                print(f"\nSending request:")
                print(request_json)
                
                # Add message to thread
                await client.beta.threads.messages.create(
                    thread_id=thread.id,
                    role="user",
                    content=message
                )
                
                # Run the orchestrator
                run = await client.beta.threads.runs.create(
                    thread_id=thread.id,
                    assistant_id=main_orchestrator_id
                )
                
                # Wait for completion
                print("\nWaiting for response...")
                while run.status in ["queued", "in_progress"]:
                    await asyncio.sleep(1)
                    run = await client.beta.threads.runs.retrieve(
                        thread_id=thread.id,
                        run_id=run.id
                    )
                
                if run.status == "completed":
                    # Get the response
                    messages = await client.beta.threads.messages.list(thread_id=thread.id)
                    
                    # Find the assistant's response
                    assistant_messages = [msg for msg in messages.data if msg.role == "assistant"]
                    
                    if assistant_messages:
                        response = assistant_messages[0]
                        print(f"\n✅ ORCHESTRATOR RESPONSE:")
                        print("-" * 40)
                        for content in response.content:
                            if hasattr(content, 'text'):
                                print(content.text.value)
                            else:
                                print(content)
                    else:
                        print("❌ No response from orchestrator")
                else:
                    print(f"❌ Run failed with status: {run.status}")
                    if hasattr(run, 'last_error'):
                        print(f"Error: {run.last_error}")
                
                # Small delay between tests
                await asyncio.sleep(2)
            
            print(f"\n{'='*80}")
            print("TEST SUMMARY")
            print(f"{'='*80}")
            print(f"Tested {len(TEST_SCENARIOS)} scenarios with Main Orchestrator")
            print("\nNext steps:")
            print("1. Review routing decisions for accuracy")
            print("2. Verify agent names match deployed agents")
            print("3. Check if ambiguous requests trigger clarification")
            
    except Exception as e:
        logger.error(f"Error testing orchestrator: {str(e)}", exc_info=True)
        sys.exit(1)
    finally:
        # Clean up credential
        await credential.close()

async def main():
    """Main entry point."""
    print("="*80)
    print("TESTING MAIN ORCHESTRATOR COMMUNICATION")
    print("Phase 1 Unified MAS Routing Tests")
    print("="*80)
    print(f"\nTest started at: {datetime.now(timezone.utc).isoformat()}")
    
    await test_orchestrator_communication()
    
    print(f"\nTest completed at: {datetime.now(timezone.utc).isoformat()}")

if __name__ == "__main__":
    asyncio.run(main())