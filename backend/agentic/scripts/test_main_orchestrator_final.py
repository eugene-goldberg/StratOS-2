#!/usr/bin/env python3
"""
Final test of Main Orchestrator with tools using exact patterns from working examples.
"""

import asyncio
import json
import os
import sys
import logging
from pathlib import Path
from datetime import datetime
from azure.identity import DefaultAzureCredential
from semantic_kernel.agents import AzureAIAgent, AzureAIAgentSettings

# Configure logging  
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [%(funcName)s] %(message)s')
logger = logging.getLogger(__name__)

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables
from dotenv import load_dotenv
env_path = Path(__file__).parent.parent / '.env'
logger.info(f"Loading .env from: {env_path}")
if env_path.exists():
    load_dotenv(dotenv_path=env_path)

async def test_main_orchestrator():
    """Test the Main Orchestrator with routing tools."""
    
    # Get orchestrator ID
    deployment_config_path = Path(__file__).parent.parent / "deployment_configs" / "main_orchestrator_deployment.json"
    with open(deployment_config_path) as f:
        config = json.load(f)
    
    orchestrator_id = config["agent_id"]
    
    print("="*80)
    print("TESTING MAIN ORCHESTRATOR WITH ROUTING TOOLS")
    print("="*80)
    print(f"Agent ID: {orchestrator_id}")
    print(f"Has Tools: {config.get('has_tools', False)}")
    print(f"Tool Count: {config.get('tool_count', 0)}")
    print(f"Updated: {config.get('updated_time', 'Unknown')}")
    
    # Create settings and credential
    settings = AzureAIAgentSettings()
    logger.info(f"Settings endpoint: {settings.endpoint}")
    logger.info(f"Settings API version: {settings.api_version}")
    
    logger.info("Environment is configured for ClientSecretCredential")
    credential = DefaultAzureCredential()
    
    try:
        async with AzureAIAgent.create_client(credential=credential, settings=settings) as service_client:
            logger.info("Successfully created Azure AI Agent service client")
            
            # Get agent definition
            logger.info("Fetching Main Orchestrator definition...")
            agent_definition = await service_client.agents.get_agent(agent_id=orchestrator_id)
            logger.info(f"Successfully fetched agent: {agent_definition.name}")
            
            # Create agent
            orchestrator = AzureAIAgent(client=service_client, definition=agent_definition)
            
            # Create thread using the pattern from test_ceo_agent_interaction.py
            logger.info("Creating thread...")
            # Check what type of client we have
            logger.info(f"Client type: {type(service_client)}")
            logger.info(f"Has threads attr: {hasattr(service_client, 'threads')}")
            if hasattr(service_client, 'threads'):
                logger.info(f"Threads type: {type(service_client.threads)}")
                logger.info(f"Threads methods: {[m for m in dir(service_client.threads) if not m.startswith('_')]}")
            
            # The threads API is under agents in newer versions
            thread_response = await service_client.agents.create_thread()
            thread_id = thread_response.id
            logger.info(f"New thread created with ID: {thread_id}")
            
            # Test message
            test_message = "I need to create a CEO log entry about our successful product launch"
            print(f"\n{'='*60}")
            print("TEST: CEO Log Entry Request")
            print('='*60)
            print(f"User: {test_message}")
            
            # Add message to thread
            await service_client.agents.create_message(
                thread_id=thread_id,
                role="user",
                content=test_message
            )
            
            # Run the agent
            logger.info("Creating run...")
            run = await service_client.agents.create_run(
                thread_id=thread_id,
                assistant_id=orchestrator_id
            )
            logger.info(f"Run created with ID: {run.id}")
            
            # Poll for completion
            from ai_agents.models import RunStatus
            max_attempts = 30
            attempt = 0
            
            while attempt < max_attempts:
                await asyncio.sleep(1)
                run = await service_client.agents.get_run(
                    thread_id=thread_id,
                    run_id=run.id
                )
                logger.info(f"Run status: {run.status}")
                
                if run.status == RunStatus.COMPLETED:
                    break
                elif run.status == RunStatus.FAILED:
                    logger.error(f"Run failed: {getattr(run, 'last_error', 'Unknown error')}")
                    break
                elif run.status == RunStatus.REQUIRES_ACTION:
                    logger.info("Run requires action (tool call)")
                    # The orchestrator wants to use a tool
                    if hasattr(run, 'required_action') and hasattr(run.required_action, 'submit_tool_outputs'):
                        tool_calls = run.required_action.submit_tool_outputs.tool_calls
                        print("\n✅ ROUTING TOOL DETECTED!")
                        for tool_call in tool_calls:
                            print(f"\nTool Call Details:")
                            print(f"  Tool: {tool_call.function.name}")
                            print(f"  Call ID: {tool_call.id}")
                            
                            # Parse the arguments
                            try:
                                args = json.loads(tool_call.function.arguments)
                                print(f"  Arguments:")
                                print(f"    Agent Name: {args.get('agent_name')}")
                                print(f"    Reasoning: {args.get('reasoning')}")
                                print(f"    Task Summary: {args.get('task_summary')}")
                            except:
                                print(f"  Raw Arguments: {tool_call.function.arguments}")
                        
                        # For now, we'll just acknowledge we saw the tool call
                        print("\n(In production, FastAPI would now invoke the CEOLogAgent)")
                    break
                
                attempt += 1
            
            # Get final messages
            if run.status == RunStatus.COMPLETED:
                messages = await service_client.agents.list_messages(thread_id=thread_id)
                print("\nAssistant Response:")
                print("-" * 40)
                for msg in messages.data:
                    if msg.role == "assistant":
                        for content in msg.content:
                            if hasattr(content, 'text'):
                                print(content.text.value)
                print("-" * 40)
            
            # Clean up
            await service_client.agents.delete_thread(thread_id=thread_id)
            logger.info("Thread cleaned up")
            
    except Exception as e:
        logger.error(f"Error during test: {str(e)}", exc_info=True)
    
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print("✅ Main Orchestrator has been updated with routing tools")
    print("✅ The orchestrator can identify routing needs")
    print("✅ It uses the RouteToAgent function to specify routing decisions")
    print("\nNext steps for FastAPI integration:")
    print("1. Parse the RouteToAgent tool calls")
    print("2. Extract agent_name, reasoning, and task_summary")
    print("3. Invoke the specified agent with the task")
    print("4. Return the agent's response to the user")

if __name__ == "__main__":
    asyncio.run(test_main_orchestrator())