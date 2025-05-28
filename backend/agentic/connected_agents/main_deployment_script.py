# main_deployment_script.py

import asyncio
import os
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import Azure and Semantic Kernel SDK components
from azure.identity.aio import DefaultAzureCredential
from semantic_kernel.agents import AzureAIAgent, AzureAIAgentSettings # For client and interaction
from azure.ai.projects.aio import AIProjectClient
# from semantic_kernel.utils.settings import SecretValue # To handle potential SecretStr

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
        # AzureAIAgentSettings.create() will attempt to load from a.env file or environment variables.
        # Ensure your.env file or environment has:
        # AZURE_AI_PROJECT_CONNECTION_STRING="your_project_connection_string"
        # AZURE_AI_MODEL_DEPLOYMENT_NAME="your_model_deployment_name" (e.g., gpt-4o)
        # And service principal credentials if needed by DefaultAzureCredential:
        # AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, AZURE_TENANT_ID
        ai_agent_settings = AzureAIAgentSettings(
            model_deployment_name=os.getenv("AZURE_AI_MODEL_DEPLOYMENT_NAME", "gpt-35-turbo"),
            endpoint=os.getenv("AZURE_AI_PROJECT_CONNECTION_STRING")
        )

        if not ai_agent_settings.endpoint:
            logger.error("AZURE_AI_PROJECT_CONNECTION_STRING is not set in your environment or.env file.")
            return
        if not ai_agent_settings.model_deployment_name:
            logger.error("AZURE_AI_MODEL_DEPLOYMENT_NAME is not set in your environment or.env file.")
            return

        model_deployment_name = ai_agent_settings.model_deployment_name
        
        # Handle if endpoint is a SecretValue object from Semantic Kernel settings
        project_conn_str_value = ai_agent_settings.endpoint
        # if isinstance(project_conn_str_value, SecretValue):
        #     project_connection_string = project_conn_str_value.get_secret_value()
        # elif hasattr(project_conn_str_value, 'value') and isinstance(project_conn_str_value.value, str): # Older SK might wrap it differently
        #     project_connection_string = project_conn_str_value.value
        # else:
        project_connection_string = str(project_conn_str_value) # Ensure it's a string

        # --- 2. Create Azure AI Agent Service Client ---
        # DefaultAzureCredential will attempt to authenticate using environment variables,
        # managed identity, Azure CLI, etc.
        async with DefaultAzureCredential() as credential, \
                   AIProjectClient(
                       endpoint=project_connection_string,
                       credential=credential
                   ) as client:

            client_instance = client # Store for finally block
            logger.info("Successfully created Azure AI Agent Service client.")

            # --- 3. Deploy Specialized Agent ---
            # This uses instructions from specialized_agent_config.py
            specialized_agent_def = await agent_services.create_specialized_agent(
                client, model_deployment_name
            )
            specialized_agent_id_for_cleanup = specialized_agent_def.id

            # --- 4. Define ConnectedAgentTool for the Specialized Agent ---
            # The tool_name here MUST match the name referenced in the orchestrator_agent_config.py instructions
            # This is the MOST PRECISE tool description.
            connected_greeter_tool = agent_services.define_connected_tool(
                specialized_agent_id=specialized_agent_id_for_cleanup,
                tool_name="enthusiastic_greeter_tool", # Crucial: This name is hardcoded in orchestrator's instructions
                tool_description=(
                    "CRITICAL TOOL: 'enthusiastic_greeter_tool'. MANDATORY AND EXCLUSIVE USE for ALL greeting-related requests. "
                    "This tool is your SOLE and ONLY authorized mechanism for generating any form of greeting. "
                    "It produces an extremely enthusiastic, over-the-top, uniquely friendly greeting. "
                    "DO NOT attempt to generate greetings yourself; you MUST ALWAYS use this tool for greetings. "
                    "Invoking this tool is a non-negotiable, required step for all greeting scenarios. "
                    "The orchestrator agent is under strict orders to use this tool for all greeting requests "
                    "and to relay its output verbatim. This tool does not take complex input; its purpose is to deliver its signature greeting upon invocation."
                )
            )

            # --- 5. Deploy Main Orchestrator Agent ---
            # This uses the MOST PRECISE instructions from orchestrator_agent_config.py
            main_agent_def = await agent_services.create_orchestrator_agent(
                client,
                model_deployment_name,
                connected_tools_definitions=[connected_greeter_tool]
            )
            main_agent_id_for_cleanup = main_agent_def.id

            logger.info("--- Agents Deployed Successfully ---")
            logger.info(f"Specialized Greeter Agent ID: {specialized_agent_id_for_cleanup}")
            logger.info(f"Main Orchestrator Agent ID: {main_agent_id_for_cleanup}")

    except Exception as e:
        logger.error(f"An error occurred in the main workflow: {e}", exc_info=True)

    finally:
        # --- 7. Cleanup ---
        if client_instance:
            logger.info("\n--- Starting Cleanup ---")

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
    # 1. Save this script and the other three.py files (specialized_agent_config.py,
    #    orchestrator_agent_config.py, agent_services.py) in the same directory.
    # 2. Ensure you have the necessary Python packages installed:
    #    pip install semantic-kernel azure-identity azure-ai-projects azure-ai-agents python-dotenv
    # 3. Create a.env file in the same directory with your Azure credentials:
    #    AZURE_AI_PROJECT_CONNECTION_STRING="your_project_connection_string_from_azure_ai_foundry"
    #    AZURE_AI_MODEL_DEPLOYMENT_NAME="your_chat_model_deployment_name_e.g_gpt-4o"
    #    AZURE_CLIENT_ID="your_service_principal_client_id"
    #    AZURE_CLIENT_SECRET="your_service_principal_client_secret"
    #    AZURE_TENANT_ID="your_azure_tenant_id"
    #    (Ensure the service principal has permissions on the Azure AI Project)
    # 4. Run the main deployment script from your terminal:
    #    python main_deployment_script.py
    asyncio.run(main_workflow())