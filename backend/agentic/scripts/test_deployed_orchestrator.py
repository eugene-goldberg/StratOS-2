#!/usr/bin/env python3
"""
Test script for deployed MainOrchestratorAgent - non-interactive version.
This version uses azure.ai.agents.aio.AgentsClient directly
after endpoint discovery using Semantic Kernel's AzureAIAgentSettings.
"""

import asyncio
import os
import sys
import logging
from datetime import datetime, timezone
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [%(funcName)s] %(message)s')
logger = logging.getLogger(__name__)

# Path setup
try:
    current_script_dir = os.path.dirname(os.path.abspath(__file__))
    agentic_dir = os.path.dirname(current_script_dir)
    env_path = os.path.join(agentic_dir, '.env')

    logger.info(f"Attempting to load .env file from: {env_path}")
    if load_dotenv(env_path):
        logger.info(f".env file loaded successfully from {env_path}")
    else:
        logger.warning(f".env file not found at '{env_path}' or it's empty. Relying on pre-set environment variables.")
except Exception as e:
    logger.error(f"Error determining .env path or loading .env: {e}")
    sys.exit(1)


# Import required modules
try:
    from azure.identity.aio import DefaultAzureCredential as AsyncDefaultAzureCredential
    from azure.ai.agents.aio import AgentsClient  # Corrected Client Import
    from semantic_kernel.agents import AzureAIAgentSettings # To resolve the endpoint via SK's logic
except ImportError as e:
    logger.error(f"Error importing required modules: {e}")
    logger.error("Ensure 'azure-identity', 'azure-ai-agents' (for AgentsClient), 'python-dotenv', and 'semantic-kernel' (for AzureAIAgentSettings) are installed.")
    logger.error("If 'AgentsClient' import fails, your 'azure-ai-agents' installation might be corrupted or the client name/path is different than expected for version 1.0.0.")
    sys.exit(1)

async def test_single_interaction_with_direct_sdk(orchestrator_agent_id: str, test_message: str):
    """
    Sends a message to the orchestrator using AgentsClient directly.
    """
    logger.info(f"--- Testing Orchestrator (ID: {orchestrator_agent_id}) with direct AgentsClient calls ---")
    logger.info(f"User Message: \"{test_message}\"")

    try:
        logger.info("Verifying essential environment variables for AzureAIAgentSettings (used for endpoint discovery):")
        essential_vars = [
            "AZURE_AI_AGENT_PROJECT_NAME", "AZURE_AI_AGENT_PROJECT_HUB_NAME",
            "AZURE_AI_AGENT_PROJECT_RESOURCE_GROUP", "AZURE_AI_AGENT_PROJECT_SUBSCRIPTION_ID",
            "AZURE_AI_AGENT_API_VERSION", "AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME"
        ]
        all_vars_present = True
        for var in essential_vars:
            val = os.getenv(var)
            if not val:
                logger.error(f"  MISSING: {var}")
                all_vars_present = False
            else:
                logger.info(f"  {var}: '{val}'")

        if not all_vars_present:
            logger.error("One or more critical environment variables for endpoint discovery are missing. Aborting test.")
            return

        logger.info(f"  AZURE_AI_AGENT_ENDPOINT (from env for SK settings): '{os.getenv('AZURE_AI_AGENT_ENDPOINT', 'Not set - relying on SDK discovery by SK AzureAIAgentSettings')}'")

        sk_settings_for_endpoint_discovery = AzureAIAgentSettings()

        resolved_endpoint = sk_settings_for_endpoint_discovery.endpoint
        api_version_for_client = sk_settings_for_endpoint_discovery.api_version or os.getenv("AZURE_AI_AGENT_API_VERSION", "2024-12-01-preview")

        logger.info(f"SK AzureAIAgentSettings resolved - Endpoint: '{resolved_endpoint}', Intended API_Version for client: '{api_version_for_client}'")

        if resolved_endpoint is None:
            logger.error("CRITICAL FAILURE: SK AzureAIAgentSettings did not resolve an endpoint. SDK discovery failed. Ensure project context env vars are correct and AZURE_AI_AGENT_ENDPOINT is unset in .env.")
            return

        async with AsyncDefaultAzureCredential(exclude_interactive_browser_credential=False) as credential:
            try:
                # Initialize the AgentsClient directly using the resolved endpoint
                data_plane_client = AgentsClient(endpoint=resolved_endpoint, credential=credential, api_version=api_version_for_client)
                logger.info(f"Successfully created AgentsClient for endpoint: {resolved_endpoint} with API version: {api_version_for_client}")
            except Exception as client_init_e:
                logger.error(f"Failed to initialize AgentsClient: {client_init_e}", exc_info=True)
                logger.error("Ensure 'azure-ai-agents' package is installed and the endpoint/API version are correct.")
                return

            logger.info(f"Verifying orchestrator agent ID: {orchestrator_agent_id} exists (by attempting to fetch)...")
            try:
                # AgentsClient uses .assistants for agent definitions, and get_assistant expects assistant_id
                agent_definition = await data_plane_client.assistants.get_assistant(assistant_id=orchestrator_agent_id)
                logger.info(f"Successfully fetched definition for agent: {agent_definition.name} (ID: {agent_definition.id})")
            except Exception as e:
                logger.error(f"Could not fetch/verify agent definition for orchestrator ID '{orchestrator_agent_id}': {e}", exc_info=True)
                logger.warning("Proceeding with interaction attempt, but agent verification failed.")

            logger.info("Creating new conversation thread with orchestrator...")
            thread_id = None
            try:
                thread_resource = await data_plane_client.threads.create_thread()
                thread_id = thread_resource.id
                logger.info(f"Created thread: {thread_id}")
            except Exception as e:
                logger.error(f"Failed to create thread using data_plane_client: {e}", exc_info=True)
                return

            try:
                logger.info(f"Adding user message to thread {thread_id}...")
                await data_plane_client.threads.create_message(
                    thread_id=thread_id,
                    role="user",
                    content=test_message
                )
                logger.info(f"User message added to thread.")

                logger.info(f"Creating run for agent {orchestrator_agent_id} on thread {thread_id}...")
                run_response = await data_plane_client.threads.create_run(
                    thread_id=thread_id,
                    assistant_id=orchestrator_agent_id
                )
                run_id = run_response.id
                logger.info(f"Run created with ID: {run_id}, Status: {run_response.status}")

                print(f"\n➡️ User to Orchestrator (ID: {orchestrator_agent_id}, Thread: {thread_id}): {test_message}")
                print(f"⬅️ Orchestrator: Processing...", end="", flush=True)

                timeout_seconds = 120
                start_time = asyncio.get_event_loop().time()

                while run_response.status in ["queued", "in_progress", "requires_action"]:
                    if asyncio.get_event_loop().time() - start_time > timeout_seconds:
                        logger.error(f"Run {run_id} timed out after {timeout_seconds} seconds.")
                        raise TimeoutError(f"Run {run_id} timed out.")

                    await asyncio.sleep(3)
                    run_response = await data_plane_client.threads.get_run(thread_id=thread_id, run_id=run_id)
                    print(f"\r⬅️ Orchestrator: Processing... (Status: {run_response.status})", end="", flush=True)

                    if run_response.status == "requires_action":
                        logger.warning(f"Run {run_id} requires action. This script does not currently handle client-side tool call submissions.")
                        logger.warning(f"Required action details: {run_response.required_action}")
                        pass

                print("\r" + " " * 70 + "\r", end="", flush=True)

                if run_response.status == "completed":
                    logger.info(f"Run {run_id} completed.")
                    messages_response = await data_plane_client.threads.list_messages(thread_id=thread_id, order="asc")

                    full_response = ""
                    assistant_responses_content = []
                    for msg in reversed(messages_response.data):
                        if msg.run_id == run_id and msg.role == "assistant":
                            if msg.content:
                                for content_item in msg.content:
                                    if content_item.type == "text":
                                        assistant_responses_content.insert(0, content_item.text.value)
                        elif msg.role == "user":
                             # Heuristic: stop if we encounter the user message that started this interaction
                            if hasattr(msg, 'content') and msg.content and msg.content[0].type == "text" and msg.content[0].text.value == test_message:
                                break
                            # More robustly, one might check message IDs if they are sequential or if the run provides output message IDs.
                    
                    if assistant_responses_content:
                        full_response = "\n".join(assistant_responses_content)
                        print(f"⬅️ Orchestrator: {full_response}")
                    else:
                        print("⬅️ Orchestrator: No new textual response from assistant specifically for this run found in messages.")
                        full_response = "No new textual response directly from this run."
                            
                    logger.info(f"Orchestrator's final response extracted. Preview: {full_response[:250]}...")

                elif run_response.status == "failed":
                    logger.error(f"Run {run_id} failed. Reason: {run_response.last_error}")
                    print(f"⬅️ Orchestrator: Run failed - {run_response.last_error.message if run_response.last_error else 'Unknown error'}")
                else:
                    logger.warning(f"Run {run_id} ended with status: {run_response.status}")
                    print(f"⬅️ Orchestrator: Run ended with status: {run_response.status}")

            finally:
                if thread_id:
                    logger.info(f"Deleting thread: {thread_id}")
                    try:
                        await data_plane_client.threads.delete_thread(thread_id=thread_id)
                        logger.info("Thread deleted successfully.")
                    except Exception as e_del:
                        logger.error(f"Failed to delete thread '{thread_id}': {e_del}")

    except Exception as e:
        logger.error(f"An error occurred during the test: {e}", exc_info=True)

async def run_tests():
    """Defines and runs test cases."""
    orchestrator_agent_id = os.getenv("MAIN_ORCHESTRATOR_AGENT_ID")
    if not orchestrator_agent_id:
        orchestrator_agent_id = "asst_PkBVaNwenBlxV3rfPuiunywU" # Your example orchestrator ID
        logger.warning(f"MAIN_ORCHESTRATOR_AGENT_ID not found in .env. Using hardcoded ID: {orchestrator_agent_id}. Please set it in .env.")
    else:
        logger.info(f"Using MAIN_ORCHESTRATOR_AGENT_ID from .env: {orchestrator_agent_id}")

    test_cases = [
        {
            "description": "Test CEOLogAgent delegation",
            "message": "I need to record my thoughts about the market downturn and its effect on Q3 projections.",
            "expected_delegate": "CEOLogAgent"
        },
        {
            "description": "Test NorthStarAgent delegation",
            "message": "What is our company's core vision statement for the next five years?",
            "expected_delegate": "NorthStarAgent"
        },
         {
            "description": "Test SWOTTOWSAgent delegation",
            "message": "Can you perform a SWOT analysis for our new product launch in the European market?",
            "expected_delegate": "SWOTTOWSAgent"
        },
    ]

    for i, test_case in enumerate(test_cases):
        logger.info(f"\n--- Running Test Case #{i+1}: {test_case['description']} ---")
        await test_single_interaction_with_direct_sdk(orchestrator_agent_id, test_case["message"])
        if i < len(test_cases) - 1:
            logger.info("Pausing briefly between tests...")
            await asyncio.sleep(3)

    logger.info("\n--- All test cases completed. ---")


if __name__ == "__main__":
    asyncio.run(run_tests())