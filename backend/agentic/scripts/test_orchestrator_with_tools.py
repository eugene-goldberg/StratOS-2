#!/usr/bin/env python3
"""
Test the Main Orchestrator using the Azure AI Agent Service API directly.
This bypasses the Semantic Kernel to test tool calling functionality.
"""

import asyncio
import json
import os
from pathlib import Path
from datetime import datetime
from azure.identity import DefaultAzureCredential
from ai_agents import AzureAIAgentSettings
from ai_agents.models import RunStatus
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
from dotenv import load_dotenv
env_path = Path(__file__).parent.parent / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path)

async def test_orchestrator_with_api():
    # Get orchestrator ID
    deployment_config_path = Path(__file__).parent.parent / "deployment_configs" / "main_orchestrator_deployment.json"
    with open(deployment_config_path) as f:
        config = json.load(f)
    
    orchestrator_id = config["agent_id"]
    
    print(f"Testing Main Orchestrator with Tools via API")
    print(f"{'='*60}")
    print(f"Agent ID: {orchestrator_id}")
    print(f"Has Tools: {config.get('has_tools', False)}")
    print(f"Tool Count: {config.get('tool_count', 0)}\n")
    
    # Create settings and credential
    settings = AzureAIAgentSettings()
    credential = DefaultAzureCredential()
    
    # Import the AI Project Client
    from ai_agents import AIProjectClient
    
    # Create client using connection string
    endpoint = os.getenv("AZURE_AI_AGENT_ENDPOINT")
    
    # Parse endpoint to get connection string components
    import re
    match = re.search(r'/subscriptions/([^/]+)/resourceGroups/([^/]+)/providers/Microsoft.MachineLearningServices/workspaces/([^/]+)', endpoint)
    
    if match:
        subscription_id = match.group(1)
        resource_group = match.group(2)
        project_name = match.group(3)
        
        # Create client
        client = AIProjectClient(
            credential=credential,
            subscription_id=subscription_id,
            resource_group_name=resource_group,
            project_name=project_name
        )
        
        print("Connected to Azure AI Agent Service\n")
        
        # Test messages
        test_messages = [
            "I need to create a CEO log entry about our successful product launch",
            "Can you perform a SWOT analysis for our new mobile app?",
            "What is our company vision and mission?"
        ]
        
        for i, message in enumerate(test_messages, 1):
            print(f"{'='*60}")
            print(f"TEST {i}: {message}")
            print('='*60)
            
            try:
                # Create a thread
                thread = await client.agents.create_thread()
                logger.info(f"Created thread: {thread.id}")
                
                # Add user message
                await client.agents.create_message(
                    thread_id=thread.id,
                    role="user",
                    content=message
                )
                
                # Run the agent
                run = await client.agents.create_run(
                    thread_id=thread.id,
                    assistant_id=orchestrator_id
                )
                logger.info(f"Created run: {run.id}")
                
                # Wait for completion
                while run.status in [RunStatus.QUEUED, RunStatus.IN_PROGRESS]:
                    await asyncio.sleep(1)
                    run = await client.agents.get_run(
                        thread_id=thread.id,
                        run_id=run.id
                    )
                    logger.info(f"Run status: {run.status}")
                
                if run.status == RunStatus.COMPLETED:
                    # Get messages
                    messages = await client.agents.list_messages(thread_id=thread.id)
                    
                    # Find assistant's response
                    for msg in messages:
                        if msg.role == "assistant":
                            print(f"\nAssistant Response:")
                            print("-" * 40)
                            for content in msg.content:
                                if hasattr(content, 'text'):
                                    print(content.text.value)
                                elif hasattr(content, 'value'):
                                    print(content.value)
                            print("-" * 40)
                            break
                    
                    # Check if any tool calls were made
                    steps = await client.agents.list_run_steps(
                        thread_id=thread.id,
                        run_id=run.id
                    )
                    
                    tool_calls_found = False
                    for step in steps:
                        if hasattr(step, 'step_details') and hasattr(step.step_details, 'tool_calls'):
                            for tool_call in step.step_details.tool_calls:
                                if hasattr(tool_call, 'function'):
                                    print(f"\n✅ Tool Call Detected:")
                                    print(f"   Function: {tool_call.function.name}")
                                    print(f"   Arguments: {tool_call.function.arguments}")
                                    tool_calls_found = True
                    
                    if not tool_calls_found:
                        print("\n⚠️ No tool calls detected")
                        
                else:
                    print(f"\n❌ Run failed with status: {run.status}")
                    if hasattr(run, 'last_error'):
                        print(f"   Error: {run.last_error}")
                
                # Clean up thread
                await client.agents.delete_thread(thread_id=thread.id)
                
            except Exception as e:
                print(f"\n❌ Error: {str(e)}")
                logger.error(f"Test failed: {str(e)}", exc_info=True)
            
            print()  # Blank line between tests
        
        print(f"{'='*60}")
        print("TEST COMPLETE")
        print('='*60)
        
    else:
        print("❌ Could not parse endpoint URL")

if __name__ == "__main__":
    asyncio.run(test_orchestrator_with_api())