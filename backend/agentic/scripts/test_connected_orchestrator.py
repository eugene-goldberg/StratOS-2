#!/usr/bin/env python3
"""
Test the Main Orchestrator with Connected Agents.
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
    from semantic_kernel.agents import AzureAIAgent, AzureAIAgentSettings
    from azure.identity.aio import DefaultAzureCredential
except ImportError as e:
    logger.error(f"Error importing required modules: {e}")
    sys.exit(1)

async def test_orchestrator():
    """Test the Main Orchestrator with various requests."""
    
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
        
        # Create agent
        orchestrator = AzureAIAgent.from_agent_id(
            assistant_id=orchestrator_id,
            settings=settings
        )
        
        logger.info("Successfully connected to Main Orchestrator")
        
        # Test cases
        test_cases = [
            {
                "name": "CEO Log Request",
                "message": "I need to record my thoughts about the market downturn and how it might affect our expansion plans"
            },
            {
                "name": "SWOT Analysis Request",
                "message": "Can you perform a SWOT analysis for our new product launch?"
            },
            {
                "name": "North Star Request",
                "message": "What is our company's vision and core values?"
            }
        ]
        
        for test in test_cases:
            print("\n" + "="*80)
            print(f"TEST: {test['name']}")
            print("="*80)
            print(f"Request: {test['message']}")
            print("\nObtaining response...\n")
            
            try:
                # Create thread
                async with await orchestrator.create_thread() as thread:
                    # Add message
                    await thread.add_message(AzureAIThreadMessage(
                        role="user",
                        content=test['message']
                    ))
                    
                    # Get response
                    async with await orchestrator.run(thread=thread) as run:
                        # Wait for completion
                        await run.wait_for_completion()
                        
                        # Get messages
                        messages = await thread.get_messages()
                        
                        # Print assistant response
                        for message in messages.data:
                            if message.role == "assistant":
                                print(f"Response: {message.content[0].text.value}")
                                break
                        
                        # Check if tools were used
                        if hasattr(run, 'required_action') and run.required_action:
                            print("\nTools requested:")
                            for tool_call in run.required_action.submit_tool_outputs.tool_calls:
                                print(f"  - Tool: {tool_call.function.name}")
                                print(f"    Args: {tool_call.function.arguments}")
                        
            except Exception as e:
                logger.error(f"Error in test '{test['name']}': {str(e)}")
                continue
        
        print("\n" + "="*80)
        print("TESTING COMPLETE")
        print("="*80)
            
    except Exception as e:
        logger.error(f"Error testing orchestrator: {str(e)}", exc_info=True)
        sys.exit(1)

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