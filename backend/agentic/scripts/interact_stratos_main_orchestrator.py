#!/usr/bin/env python3
"""
Interacts with a deployed MainOrchestratorAgent in the Azure AI Project Agent Service.
The orchestrator is expected to delegate tasks to other deployed specialist agents.
Relies on environment variables for configuration.
"""

import asyncio
import os
import sys
import logging
from datetime import datetime, timezone
from dotenv import load_dotenv

# Configure logging as early as possible
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [%(funcName)s] %(message)s')
logger = logging.getLogger(__name__)

# Path setup
current_dir = os.path.dirname(os.path.abspath(__file__))
# Assuming .env is in the parent directory of this script's directory's parent
# If script is in .../scripts/, then agentic_dir is .../agentic/
# And .env is expected at .../agentic/.env
agentic_dir = os.path.dirname(current_dir) 
env_path = os.path.join(agentic_dir, '.env')

logger.info(f"Attempting to load .env file from: {env_path}")
if load_dotenv(env_path):
    logger.info(".env file loaded successfully.")
else:
    logger.warning(f".env file not found at '{env_path}' or it's empty. Relying on pre-set environment variables.")

# Import required modules
try:
    from azure.identity.aio import DefaultAzureCredential
    from semantic_kernel.agents import AzureAIAgent, AzureAIAgentSettings
    from semantic_kernel.contents import ChatMessageContent # For streaming handler
except ImportError as e:
    logger.error(f"Error importing required modules: {e}")
    logger.error("Please ensure 'semantic-kernel[azure]' and 'azure-identity' are installed.")
    sys.exit(1)

async def chat_with_orchestrator(orchestrator_agent_id: str, user_message: str):
    """
    Creates a new thread, sends a message to the deployed orchestrator agent,
    and streams its response. The orchestrator is expected to delegate to specialists.
    """
    logger.info(f"Attempting to chat with DEPLOYED MainOrchestratorAgent ID: {orchestrator_agent_id}")

    try:
        # Ensure necessary environment variables for SDK discovery are present
        required_env_vars = [
            "AZURE_AI_AGENT_PROJECT_NAME", "AZURE_AI_AGENT_PROJECT_HUB_NAME",
            "AZURE_AI_AGENT_PROJECT_RESOURCE_GROUP", "AZURE_AI_AGENT_PROJECT_SUBSCRIPTION_ID",
            "AZURE_AI_AGENT_API_VERSION", "AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME"
        ]
        logger.info("--- Checking required Azure AI Project context variables from environment ---")
        for var_name in required_env_vars:
            val = os.getenv(var_name)
            if not val:
                logger.error(f"CRITICAL: Required environment variable '{var_name}' is not set.")
                return
            logger.info(f"  {var_name}: '{val}'")
        
        env_endpoint = os.getenv("AZURE_AI_AGENT_ENDPOINT")
        if env_endpoint:
            logger.warning(f"AZURE_AI_AGENT_ENDPOINT is set in .env to '{env_endpoint}'. For SDK discovery of AI Project Agent Service, this should ideally be unset. The SDK might prioritize this explicit endpoint.")
        else:
            logger.info("AZURE_AI_AGENT_ENDPOINT is not set in .env, relying on SDK discovery (preferred).")

        settings = AzureAIAgentSettings() # Loads from environment

        logger.info(f"--- AzureAIAgentSettings object initialized with ---")
        logger.info(f"  settings.endpoint: '{settings.endpoint}'")
        logger.info(f"  settings.model_deployment_name: '{settings.model_deployment_name}'")
        logger.info(f"  settings.api_version: '{settings.api_version}'")

        if settings.endpoint is None:
            logger.error("CRITICAL FAILURE: AzureAIAgentSettings did not resolve an endpoint.")
            logger.error("Ensure all AZURE_AI_AGENT_PROJECT_* variables are correctly set in your .env file WITH THE 'AZURE_AI_AGENT_' PREFIX.")
            return

        async with DefaultAzureCredential(exclude_interactive_browser_credential=False) as credential:
            async with AzureAIAgent.create_client(credential=credential, settings=settings) as service_client:
                logger.info(f"Successfully created Azure AI Agent service client. Effective endpoint: {settings.endpoint}")

                # 1. Get the definition of the deployed MainOrchestratorAgent
                logger.info(f"Fetching definition for MainOrchestratorAgent ID: {orchestrator_agent_id}...")
                try:
                    agent_definition = await service_client.agents.get_agent(assistant_id=orchestrator_agent_id)
                    logger.info(f"Successfully fetched agent definition for: {agent_definition.name} (ID: {agent_definition.id})")
                except Exception as e:
                    logger.error(f"Failed to fetch agent definition for ID '{orchestrator_agent_id}': {e}", exc_info=True)
                    return

                # 2. Create a Semantic Kernel AzureAIAgent instance for the orchestrator
                sk_orchestrator_agent = AzureAIAgent(
                    client=service_client,
                    definition=agent_definition
                )

                # 3. Create a new thread for the conversation
                logger.info("Creating a new conversation thread with the orchestrator...")
                thread_id = None # Initialize thread_id
                try:
                    thread_response = await service_client.threads.create_thread()
                    thread_id = thread_response.id
                    logger.info(f"New thread created with ID: {thread_id}")
                except Exception as e:
                    logger.error(f"Failed to create a new thread: {e}", exc_info=True)
                    return
                
                # 4. Send message to orchestrator and get response
                try:
                    logger.info(f"\nUser: {user_message}")
                    print(f"\nUser: {user_message}")
                    print(f"Orchestrator ({sk_orchestrator_agent.name}): ", end="", flush=True)
                    
                    full_response_content = ""
                    async for message_chunk in sk_orchestrator_agent.invoke(message=user_message, thread_id=thread_id):
                        chunk_text = None
                        if isinstance(message_chunk, ChatMessageContent) and message_chunk.content:
                            chunk_text = message_chunk.content
                        elif isinstance(message_chunk, list) and message_chunk and isinstance(message_chunk[0], ChatMessageContent) and message_chunk[0].content:
                            chunk_text = message_chunk[0].content
                        
                        if chunk_text:
                            print(chunk_text, end="", flush=True)
                            full_response_content += chunk_text
                    print() # Newline after agent response
                    logger.info(f"Orchestrator full response received (length: {len(full_response_content)}).")

                except Exception as e:
                    logger.error(f"Error during orchestrator interaction on thread '{thread_id}': {e}", exc_info=True)
                finally:
                    # 5. Delete the thread
                    if thread_id:
                        logger.info(f"Deleting thread: {thread_id}")
                        try:
                            await service_client.threads.delete_thread(thread_id=thread_id)
                            logger.info(f"Thread '{thread_id}' deleted successfully.")
                        except Exception as e_del:
                            logger.error(f"Failed to delete thread '{thread_id}': {e_del}", exc_info=True)
                            
    except Exception as e:
        logger.error(f"An error occurred in chat_with_orchestrator: {e}", exc_info=True)

async def main():
    """Gets orchestrator agent ID and user message, then starts the chat."""
    print("--- StratOS Deployed Main Orchestrator Interaction ---")
    
    # You can get this ID from the output of your deployment script or list_ai_project_agents.py
    orchestrator_agent_id_input = input("Enter the Agent ID of your DEPLOYED MainOrchestratorAgent: ").strip()
    if not orchestrator_agent_id_input or not orchestrator_agent_id_input.startswith("asst_"):
        logger.error("Invalid or empty Agent ID provided. It should start with 'asst_'.")
        return

    print("\nExamples of requests for the orchestrator:")
    print("- 'I need to record my thoughts about the market downturn and its effect on Q3 projections.' (→ CEOLogAgent)")
    print("- 'What is our company's core vision statement?' (→ NorthStarAgent)")
    print("- 'Perform a SWOT analysis for the new Alpha project.' (→ SWOTTOWSAgent)")
    print("- 'Can you retrieve the key decisions made in last month's strategy meeting?' (→ MemoryRecallAgent)")
    
    user_message_input = input("\nEnter your request for the Orchestrator: ").strip()
    if not user_message_input:
        logger.error("Message cannot be empty.")
        return
    
    await chat_with_orchestrator(orchestrator_agent_id=orchestrator_agent_id_input, user_message=user_message_input)

    # To make this a continuous chat loop:
    # while True:
    #     user_message_input = input("\nEnter your request for the Orchestrator (or 'exit'): ").strip()
    #     if user_message_input.lower() == 'exit':
    #         break
    #     if not user_message_input:
    #         continue
    #     await chat_with_orchestrator(orchestrator_agent_id=orchestrator_agent_id_input, user_message=user_message_input)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Interaction stopped by user.")
    except Exception as e:
        logger.error(f"Unhandled error in script: {e}", exc_info=True)