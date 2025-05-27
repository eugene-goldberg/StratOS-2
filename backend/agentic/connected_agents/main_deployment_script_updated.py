#!/usr/bin/env python3
"""
Updated deployment script for connected agents using the current Azure AI SDK.
This demonstrates the connected agent pattern where one agent can invoke another.
"""

import asyncio
import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [%(funcName)s] %(message)s')
logger = logging.getLogger(__name__)

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

# Load environment variables
env_path = Path(__file__).parent.parent / '.env'
logger.info(f"Loading .env from: {env_path}")
load_dotenv(env_path)

from azure.identity.aio import DefaultAzureCredential
from azure.ai.projects.aio import AIProjectClient
from azure.ai.agents.models import ConnectedAgentTool

# Import configurations
import specialized_agent_config
import orchestrator_agent_config

async def main_workflow():
    """Main workflow to deploy connected agents, interact, and cleanup."""
    
    # Hardcode the endpoint since SDK discovery isn't working
    endpoint = "https://ai.azure.com/api/eastus/agents/v1.0/subscriptions/514bd6d3-2c02-45c6-a86f-29cf262a379a/resourceGroups/semantic-kernel-multi-agent-rg/providers/Microsoft.MachineLearningServices/workspaces/sk-multi-agent-project"
    
    # Get model deployment
    model_deployment = os.getenv("AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME", "gpt-35-turbo")
    
    logger.info(f"Using endpoint: {endpoint}")
    logger.info(f"Using model: {model_deployment}")
    
    # Create credential
    credential = DefaultAzureCredential()
    
    specialized_agent_id = None
    orchestrator_agent_id = None
    thread_id = None
    
    try:
        # Create AI Project client
        async with AIProjectClient(
            endpoint=endpoint,
            credential=credential,
            api_version="2024-12-01-preview"
        ) as client:
            logger.info("Successfully connected to Azure AI Agent Service")
            
            # --- 1. Create Specialized Greeter Agent ---
            logger.info(f"Creating Specialized Agent: {specialized_agent_config.AGENT_NAME_PREFIX}...")
            
            specialized_agent = await client.agents.create_agent(
                model=model_deployment,
                name=specialized_agent_config.AGENT_NAME_PREFIX,
                instructions=specialized_agent_config.AGENT_INSTRUCTIONS,
            )
            specialized_agent_id = specialized_agent.id
            logger.info(f"Specialized Agent created with ID: {specialized_agent_id}")
            
            # --- 2. Create ConnectedAgentTool ---
            # This allows the orchestrator to invoke the specialized agent
            connected_tool = ConnectedAgentTool(
                id=specialized_agent_id,
                name="enthusiastic_greeter_tool",
                description="Use this tool ONLY when you need to provide an enthusiastic greeting to the user."
            )
            logger.info(f"ConnectedAgentTool defined for agent ID: {specialized_agent_id}")
            
            # --- 3. Create Main Orchestrator Agent with Connected Tool ---
            logger.info(f"Creating Orchestrator Agent: {orchestrator_agent_config.AGENT_NAME_PREFIX}...")
            
            orchestrator_agent = await client.agents.create_agent(
                model=model_deployment,
                name=orchestrator_agent_config.AGENT_NAME_PREFIX,
                instructions=orchestrator_agent_config.AGENT_INSTRUCTIONS,
                tools=connected_tool.definitions  # Pass the tool definitions list directly
            )
            orchestrator_agent_id = orchestrator_agent.id
            logger.info(f"Orchestrator Agent created with ID: {orchestrator_agent_id}")
            logger.info(f"Orchestrator has access to connected agent tool")
            
            # --- 4. Test the Connected Agents ---
            # Create a thread
            thread = await client.agents.threads.create()
            thread_id = thread.id
            logger.info(f"Created thread: {thread_id}")
            
            # Test 1: Ask for a greeting (should use the connected agent)
            test_message1 = "Hello there, can you greet me?"
            logger.info(f"\n--- TEST 1: '{test_message1}' ---")
            
            # Add message to thread
            await client.agents.messages.create(
                thread_id=thread_id,
                role="user",
                content=test_message1
            )
            
            # Create a run
            run1 = await client.agents.runs.create(
                thread_id=thread_id,
                body={"assistant_id": orchestrator_agent_id}
            )
            
            # Poll for completion
            while run1.status in ["queued", "in_progress", "requires_action"]:
                await asyncio.sleep(1)
                run1 = await client.agents.runs.get(
                    thread_id=thread_id,
                    run_id=run1.id
                )
                
                if run1.status == "requires_action":
                    # The orchestrator is trying to use the connected agent tool
                    logger.info("Orchestrator is invoking connected agent tool...")
                    
                    # For now, we'll just log and let it timeout
                    # In a real implementation, the Azure service handles the connected agent invocation
                    await asyncio.sleep(2)
            
            # Get the response
            if run1.status == "completed":
                messages = client.agents.messages.list(
                    thread_id=thread_id,
                    order="desc",
                    limit=1
                )
                
                async for message in messages:
                    if message.role == "assistant":
                        logger.info(f"Orchestrator Response: {message.content[0].text.value if message.content else 'No content'}")
                        break
            else:
                logger.warning(f"Run 1 ended with status: {run1.status}")
            
            # Test 2: Ask a general question (should answer directly)
            test_message2 = "What is the capital of France?"
            logger.info(f"\n--- TEST 2: '{test_message2}' ---")
            
            # Add message to thread
            await client.agents.messages.create(
                thread_id=thread_id,
                role="user",
                content=test_message2
            )
            
            # Create another run
            run2 = await client.agents.runs.create(
                thread_id=thread_id,
                body={"assistant_id": orchestrator_agent_id}
            )
            
            # Poll for completion
            while run2.status in ["queued", "in_progress"]:
                await asyncio.sleep(1)
                run2 = await client.agents.runs.get(
                    thread_id=thread_id,
                    run_id=run2.id
                )
            
            # Get the response
            if run2.status == "completed":
                messages = client.agents.messages.list(
                    thread_id=thread_id,
                    order="desc",
                    limit=1
                )
                
                async for message in messages:
                    if message.role == "assistant":
                        logger.info(f"Orchestrator Response: {message.content[0].text.value if message.content else 'No content'}")
                        break
            else:
                logger.warning(f"Run 2 ended with status: {run2.status}")
            
            logger.info("\n--- Testing Complete ---")
            
    except Exception as e:
        logger.error(f"Error in workflow: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # --- Cleanup ---
        if 'client' in locals():
            logger.info("\n--- Cleanup Starting ---")
            
            # Delete thread
            if thread_id:
                try:
                    await client.agents.threads.delete(thread_id=thread_id)
                    logger.info(f"Deleted thread: {thread_id}")
                except Exception as e:
                    logger.error(f"Error deleting thread: {e}")
            
            # Delete orchestrator agent
            if orchestrator_agent_id:
                try:
                    await client.agents.delete_agent(agent_id=orchestrator_agent_id)
                    logger.info(f"Deleted orchestrator agent: {orchestrator_agent_id}")
                except Exception as e:
                    logger.error(f"Error deleting orchestrator: {e}")
            
            # Delete specialized agent
            if specialized_agent_id:
                try:
                    await client.agents.delete_agent(agent_id=specialized_agent_id)
                    logger.info(f"Deleted specialized agent: {specialized_agent_id}")
                except Exception as e:
                    logger.error(f"Error deleting specialized agent: {e}")
            
            logger.info("--- Cleanup Complete ---")

if __name__ == "__main__":
    logger.info("\n================================================================================")
    logger.info("CONNECTED AGENTS DEPLOYMENT TEST")
    logger.info("================================================================================")
    logger.info("This demonstrates how one agent can invoke another using ConnectedAgentTool.")
    logger.info("================================================================================\n")
    
    asyncio.run(main_workflow())