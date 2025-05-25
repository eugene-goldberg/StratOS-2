#!/usr/bin/env python3
"""
Interacts with a deployed agent in the Azure AI Project Agent Service.
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

# Path setup (consistent with your other scripts)
current_dir = os.path.dirname(os.path.abspath(__file__))
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

async def chat_with_agent(agent_id: str, user_message: str):
    """
    Creates a new thread, sends a message to the specified agent,
    and streams its response.
    """
    logger.info(f"Attempting to chat with agent ID: {agent_id}")

    try:
        # Ensure necessary environment variables for SDK discovery are present
        required_env_vars = [
            "AZURE_AI_AGENT_PROJECT_NAME", "AZURE_AI_AGENT_PROJECT_HUB_NAME",
            "AZURE_AI_AGENT_PROJECT_RESOURCE_GROUP", "AZURE_AI_AGENT_PROJECT_SUBSCRIPTION_ID",
            "AZURE_AI_AGENT_API_VERSION", "AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME" # Model needed for agent context
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
            logger.warning(f"AZURE_AI_AGENT_ENDPOINT is set in .env to '{env_endpoint}'. For SDK discovery of AI Project Agent Service, this should ideally be unset.")
        else:
            logger.info("AZURE_AI_AGENT_ENDPOINT is not set in .env, relying on SDK discovery.")


        settings = AzureAIAgentSettings()

        logger.info(f"--- AzureAIAgentSettings object initialized with ---")
        logger.info(f"  settings.endpoint: '{settings.endpoint}'")
        logger.info(f"  settings.model_deployment_name: '{settings.model_deployment_name}'")
        logger.info(f"  settings.api_version: '{settings.api_version}'")

        if settings.endpoint is None:
            logger.error("CRITICAL FAILURE: AzureAIAgentSettings did not resolve an endpoint.")
            return

        async with DefaultAzureCredential(exclude_interactive_browser_credential=False) as credential:
            async with AzureAIAgent.create_client(credential=credential, settings=settings) as service_client:
                logger.info(f"Successfully created Azure AI Agent service client. Effective endpoint: {settings.endpoint}")

                # 1. Get the agent definition
                logger.info(f"Fetching definition for agent ID: {agent_id}...")
                try:
                    agent_definition = await service_client.agents.get_agent(agent_id=agent_id)
                    logger.info(f"Successfully fetched agent definition for: {agent_definition.name}")
                except Exception as e:
                    logger.error(f"Failed to fetch agent definition for ID '{agent_id}': {e}", exc_info=True)
                    return

                # 2. Create a Semantic Kernel AzureAIAgent instance
                sk_agent = AzureAIAgent(
                    client=service_client, # Use the service client
                    definition=agent_definition
                )

                # 3. Create a new thread for the conversation
                logger.info("Creating a new conversation thread...")
                try:
                    # The SK AzureAIAgent typically expects a thread_id for invoke.
                    # We create the thread using the service_client.agents.threads
                    thread_response = await service_client.agents.threads.create_thread()
                    thread_id = thread_response.id
                    logger.info(f"New thread created with ID: {thread_id}")
                except Exception as e:
                    logger.error(f"Failed to create a new thread: {e}", exc_info=True)
                    return
                
                # 4. Send message and get response
                try:
                    logger.info(f"\nUser: {user_message}")
                    print(f"\nUser: {user_message}")
                    print(f"Agent ({sk_agent.name}): ", end="", flush=True)
                    
                    # Use invoke for streaming (if supported by your SK version and agent setup)
                    # invoke should handle adding the message, creating the run, and streaming results.
                    async for message_chunk in sk_agent.invoke(message=user_message, thread_id=thread_id):
                        if isinstance(message_chunk, ChatMessageContent) and message_chunk.content:
                            print(message_chunk.content, end="", flush=True)
                        elif isinstance(message_chunk, list) and message_chunk and isinstance(message_chunk[0], ChatMessageContent) and message_chunk[0].content: # Older SK versions might stream lists of ChatMessageContent
                            print(message_chunk[0].content, end="", flush=True)
                        # Add more specific handling for other types of streaming chunks if needed

                    print() # Newline after agent response

                except Exception as e:
                    logger.error(f"Error during agent interaction on thread '{thread_id}': {e}", exc_info=True)
                finally:
                    # 5. Delete the thread
                    if thread_id:
                        logger.info(f"Deleting thread: {thread_id}")
                        try:
                            await service_client.agents.threads.delete_thread(thread_id=thread_id)
                            logger.info(f"Thread '{thread_id}' deleted successfully.")
                        except Exception as e:
                            logger.error(f"Failed to delete thread '{thread_id}': {e}", exc_info=True)
                            
    except Exception as e:
        logger.error(f"An error occurred in chat_with_agent: {e}", exc_info=True)

async def main():
    """Gets agent ID and user message, then starts the chat."""
    print("--- Azure AI Project Agent Interaction ---")
    agent_id_input = input("Enter the Agent ID to interact with: ").strip()
    if not agent_id_input:
        logger.error("Agent ID cannot be empty.")
        return

    user_message_input = input("Enter your message: ").strip()
    if not user_message_input:
        logger.error("Message cannot be empty.")
        return
    
    await chat_with_agent(agent_id=agent_id_input, user_message=user_message_input)

    # For continuous chat, you would wrap the message input and chat_with_agent call
    # (or just the sk_agent.invoke part within chat_with_agent) in a loop,
    # reusing the same thread_id. This example does a single turn.

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Interaction stopped by user.")
    except Exception as e:
        logger.error(f"Unhandled error in script: {e}", exc_info=True)