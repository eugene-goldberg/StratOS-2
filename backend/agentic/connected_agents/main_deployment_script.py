# main_deployment_script.py

import asyncio
import os
import logging

# Import Azure and Semantic Kernel SDK components
from azure.identity.aio import DefaultAzureCredential
from semantic_kernel.agents import AzureAIAgent, AzureAIAgentSettings # For client and interaction

# Import our service functions
import agent_services

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def main_workflow():
    """
    Main workflow to deploy agents, interact, and cleanup.
    """
    client_instance = None
    thread_id_for_cleanup = None
    specialized_agent_id_for_cleanup = None
    main_agent_id_for_cleanup = None

    try:
        # --- 1. Configuration and Setup ---
        ai_agent_settings = AzureAIAgentSettings.create() # Loads from.env or environment variables

        if not ai_agent_settings.project_connection_string:
            logger.error("AZURE_AI_PROJECT_CONNECTION_STRING is not set.")
            return
        if not ai_agent_settings.model_deployment_name:
            logger.error("AZURE_AI_MODEL_DEPLOYMENT_NAME is not set.")
            return
        
        model_deployment_name = ai_agent_settings.model_deployment_name

        # --- 2. Create Azure AI Agent Service Client ---
        async with DefaultAzureCredential() as credential, \
                   AzureAIAgent.create_client(
                       credential=credential,
                       conn_str=ai_agent_settings.project_connection_string
                   ) as client:
            
            client_instance = client # Store for finally block
            logger.info("Successfully created Azure AI Agent Service client.")

            # --- 3. Deploy Specialized Agent ---
            specialized_agent_def = await agent_services.create_specialized_agent(
                client, model_deployment_name
            )
            specialized_agent_id_for_cleanup = specialized_agent_def.id

            # --- 4. Define ConnectedAgentTool for the Specialized Agent ---
            connected_greeter_tool = agent_services.define_connected_tool(
                specialized_agent_id=specialized_agent_id_for_cleanup,
                tool_name="enthusiastic_greeter_tool",
                tool_description="Use this tool ONLY when you need to provide an enthusiastic greeting to the user."
            )

            # --- 5. Deploy Main Orchestrator Agent ---
            main_agent_def = await agent_services.create_orchestrator_agent(
                client,
                model_deployment_name,
                connected_tools_definitions=[connected_greeter_tool.definitions]
            )
            main_agent_id_for_cleanup = main_agent_def.id

            # --- 6. Interact with the Main Orchestrator Agent ---
            main_sk_agent = AzureAIAgent(client=client, definition=main_agent_def)
            
            conversation_thread = None
            
            user_query = "Hello there, can you greet me?"
            logger.info(f"\n--- User Query to Main Agent: '{user_query}' ---")

            async for response_part in main_sk_agent.invoke(messages=user_query, thread=conversation_thread):
                if not conversation_thread: # Capture thread from the first response part
                    conversation_thread = response_part.thread
                    thread_id_for_cleanup = conversation_thread.id if conversation_thread else None
                
                for content_item in response_part.contents:
                    if content_item.text:
                        logger.info(f"Main Agent Response Part: {content_item.text.value}")
            
            logger.info("--- Interaction Complete ---")

            user_query_2 = "What is the capital of France?"
            logger.info(f"\n--- User Query to Main Agent: '{user_query_2}' ---")
            async for response_part in main_sk_agent.invoke(messages=user_query_2, thread=conversation_thread):
                for content_item in response_part.contents:
                    if content_item.text:
                        logger.info(f"Main Agent Response Part: {content_item.text.value}")
            logger.info("--- Second Interaction Complete ---")

    except Exception as e:
        logger.error(f"An error occurred in the main workflow: {e}", exc_info=True)

    finally:
        # --- 7. Cleanup ---
        if client_instance:
            logger.info("\n--- Starting Cleanup ---")
            if thread_id_for_cleanup:
                try:
                    logger.info(f"Deleting thread: {thread_id_for_cleanup}")
                    await client_instance.threads.delete_thread(thread_id=thread_id_for_cleanup)
                    logger.info(f"Thread {thread_id_for_cleanup} deleted.")
                except Exception as e:
                    logger.error(f"Error deleting thread {thread_id_for_cleanup}: {e}")
            
            if main_agent_id_for_cleanup:
                try:
                    logger.info(f"Deleting main agent: {main_agent_id_for_cleanup}")
                    await client_instance.agents.delete_agent(agent_id=main_agent_id_for_cleanup)
                    logger.info(f"Main agent {main_agent_id_for_cleanup} deleted.")
                except Exception as e:
                    logger.error(f"Error deleting main agent {main_agent_id_for_cleanup}: {e}")

            if specialized_agent_id_for_cleanup:
                try:
                    logger.info(f"Deleting specialized agent: {specialized_agent_id_for_cleanup}")
                    await client_instance.agents.delete_agent(agent_id=specialized_agent_id_for_cleanup)
                    logger.info(f"Specialized agent {specialized_agent_id_for_cleanup} deleted.")
                except Exception as e:
                    logger.error(f"Error deleting specialized agent {specialized_agent_id_for_cleanup}: {e}")
            logger.info("--- Cleanup Complete ---")
        else:
            logger.info("Client was not initialized, skipping cleanup.")


if __name__ == "__main__":
    # To run this example:
    # 1. Save each code block above into its respective.py file in the same directory.
    #    (specialized_agent_config.py, orchestrator_agent_config.py, agent_services.py, main_deployment_script.py)
    # 2. Ensure you have the necessary packages:
    #    pip install semantic-kernel azure-identity azure-ai-projects azure-ai-agents
    # 3. Set up your environment variables (or a.env file in the same directory):
    #    AZURE_AI_PROJECT_CONNECTION_STRING="your_project_connection_string_from_azure_ai_foundry"
    #    AZURE_AI_MODEL_DEPLOYMENT_NAME="your_chat_model_deployment_name_e.g_gpt-4o"
    # 4. Run the main deployment script: python main_deployment_script.py
    asyncio.run(main_workflow())