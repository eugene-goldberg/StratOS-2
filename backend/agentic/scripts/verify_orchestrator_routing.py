#!/usr/bin/env python3
"""
Verify that the Main Orchestrator properly routes to Connected Agents.
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

# Path setup
current_dir = os.path.dirname(os.path.abspath(__file__))
agentic_dir = os.path.dirname(current_dir)
env_path = os.path.join(agentic_dir, '.env')
load_dotenv(env_path)

# Import required modules
try:
    from azure.identity.aio import DefaultAzureCredential
    from semantic_kernel.agents import AzureAIAgent, AzureAIAgentSettings
except ImportError as e:
    logger.error(f"Error importing required modules: {e}")
    sys.exit(1)

async def verify_routing():
    """Verify orchestrator routing behavior."""
    
    try:
        # Load orchestrator ID
        deployment_config_path = os.path.join(agentic_dir, "deployment_configs", "main_orchestrator_deployment.json")
        with open(deployment_config_path, 'r') as f:
            config = json.load(f)
            orchestrator_id = config['agent_id']
            logger.info(f"Loaded Main Orchestrator ID: {orchestrator_id}")
        
        settings = AzureAIAgentSettings()
        credential = DefaultAzureCredential()
        
        async with AzureAIAgent.create_client(credential=credential, settings=settings) as client:
            # Get the agent definition
            agent_def = await client.agents.get_agent(agent_id=orchestrator_id)
            logger.info(f"Connected to orchestrator: {agent_def.name}")
            
            # Create thread
            thread = await client.agents.threads.create()
            thread_id = thread.id
            logger.info(f"Created thread: {thread_id}")
            
            # Test message that should route to CEO Log Agent
            test_message = "I need to record my thoughts about the market downturn and how it might affect our expansion plans"
            
            # Add message to thread
            await client.agents.messages.create(
                thread_id=thread_id,
                role="user",
                content=test_message
            )
            
            # Create run
            run = await client.agents.runs.create(
                thread_id=thread_id,
                assistant_id=orchestrator_id
            )
            
            logger.info(f"Created run: {run.id}")
            
            # Poll for completion
            while run.status in ["queued", "in_progress", "requires_action"]:
                await asyncio.sleep(1)
                run = await client.agents.runs.get(
                    thread_id=thread_id,
                    run_id=run.id
                )
                logger.info(f"Run status: {run.status}")
                
                # Check if orchestrator wants to use tools
                if run.status == "requires_action":
                    logger.info("Run requires action - checking tool calls")
                    
                    if hasattr(run, 'required_action') and run.required_action:
                        tool_calls = run.required_action.submit_tool_outputs.tool_calls
                        logger.info(f"Tool calls requested: {len(tool_calls)}")
                        
                        for tool_call in tool_calls:
                            logger.info(f"Tool: {tool_call.type}")
                            if hasattr(tool_call, 'function'):
                                logger.info(f"Function: {tool_call.function.name}")
                                logger.info(f"Arguments: {tool_call.function.arguments}")
                            
                        # For now, just cancel the run to see what tools were requested
                        await client.agents.runs.cancel(
                            thread_id=thread_id,
                            run_id=run.id
                        )
                        break
            
            # Get messages to see the response
            messages = await client.agents.messages.list(thread_id=thread_id)
            
            print("\n" + "="*80)
            print("ORCHESTRATOR ROUTING VERIFICATION")
            print("="*80)
            print(f"Test Message: {test_message}")
            print(f"\nRun Final Status: {run.status}")
            
            if run.status == "requires_action":
                print("\n✅ Orchestrator attempted to use tools!")
                print("This indicates it's trying to route to connected agents.")
            else:
                print("\n❌ Orchestrator did not attempt to use connected agent tools.")
                print("Response was generated directly without routing.")
            
            print("\nMessages in thread:")
            for msg in messages.data:
                print(f"\n{msg.role.upper()}: {msg.content[0].text.value if msg.content else 'No content'}")
            
            # Clean up
            await client.agents.threads.delete(thread_id=thread_id)
            logger.info(f"Deleted thread: {thread_id}")
            
    except Exception as e:
        logger.error(f"Error verifying routing: {str(e)}", exc_info=True)
    finally:
        await credential.close()

async def main():
    """Main entry point."""
    print("="*80)
    print("VERIFYING MAIN ORCHESTRATOR ROUTING")
    print("="*80)
    print(f"\nTest started at: {datetime.now(timezone.utc).isoformat()}")
    
    await verify_routing()
    
    print(f"\nTest completed at: {datetime.now(timezone.utc).isoformat()}")

if __name__ == "__main__":
    asyncio.run(main())