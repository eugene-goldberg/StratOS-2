import asyncio
import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from current directory
env_path = Path(__file__).parent / '.env'
if env_path.exists():
    load_dotenv(env_path)

from azure.identity.aio import DefaultAzureCredential
from azure.ai.projects.aio import AIProjectClient
from semantic_kernel.agents import AzureAIAgent

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_orchestrator_agent():
    """
    Tests the deployed orchestrator agent by sending it a query
    and checking if it delegates as expected.
    """
    try:
        # --- 1. Load Settings ---
        # Get environment variables directly
        project_connection_string = os.environ.get("AZURE_AI_PROJECT_CONNECTION_STRING")
        model_deployment_name = os.environ.get("AZURE_AI_MODEL_DEPLOYMENT_NAME")
        
        if not project_connection_string:
            logger.error("AZURE_AI_PROJECT_CONNECTION_STRING is not set in your .env file or environment.")
            return
        if not model_deployment_name:
            logger.error("AZURE_AI_MODEL_DEPLOYMENT_NAME is not set in your .env file or environment.")
            return

        # Get the ID of the orchestrator agent to test
        orchestrator_agent_id = os.getenv("MAIN_ORCHESTRATOR_AGENT_ID")
        if not orchestrator_agent_id:
            logger.error("MAIN_ORCHESTRATOR_AGENT_ID is not set in your .env file or environment.")
            logger.error("Please set this to the ID of your deployed MainGreetingOrchestratorAgent.")
            return

        logger.info(f"Attempting to test orchestrator agent with ID: {orchestrator_agent_id}")
        logger.info(f"Using project connection string from settings.")


        # --- 2. Create Azure AI Agent Service Client ---
        # DefaultAzureCredential will use environment variables for service principal,
        # or other methods like Azure CLI login, Managed Identity, etc.
        credential = DefaultAzureCredential()
        
        async with AIProjectClient(
            endpoint=project_connection_string,
            credential=credential,
            api_version="2024-12-01-preview"
        ) as client:

            logger.info("Successfully created Azure AI Agent Service client.")

            # --- 3. Get the Deployed Orchestrator Agent's Definition ---
            # We are not creating a new agent, but retrieving an existing one.
            try:
                logger.info(f"Retrieving definition for agent ID: {orchestrator_agent_id}...")
                orchestrator_agent_definition = await client.agents.get_agent(agent_id=orchestrator_agent_id)
                logger.info(f"Successfully retrieved definition for agent: {orchestrator_agent_definition.name} (ID: {orchestrator_agent_id})")
                logger.info(f"  Instructions: {orchestrator_agent_definition.instructions[:200]}...") # Log first 200 chars
                if orchestrator_agent_definition.tools:
                    logger.info(f"  Number of tools: {len(orchestrator_agent_definition.tools)}")
                    for idx, tool in enumerate(orchestrator_agent_definition.tools):
                        logger.info(f"  Tool {idx}: {type(tool).__name__}")
                        # Try to access tool properties
                        if hasattr(tool, 'connected_agent'):
                            logger.info(f"    Connected Agent Tool - name: {tool.connected_agent.name if hasattr(tool.connected_agent, 'name') else 'N/A'}")
                            logger.info(f"    Connected Agent Tool - id: {tool.connected_agent.id if hasattr(tool.connected_agent, 'id') else 'N/A'}")
                else:
                    logger.info("  Agent has no tools defined in its retrieved definition. Delegation will not occur.")

            except Exception as e:
                logger.error(f"Failed to retrieve agent definition for ID {orchestrator_agent_id}: {e}", exc_info=True)
                return

            # --- 4. Wrap the Definition and Invoke ---
            # Use the AzureAIAgent class from Semantic Kernel to wrap the agent definition for easy invocation
            main_sk_agent = AzureAIAgent(client=client, definition=orchestrator_agent_definition)

            conversation_thread = None # Let the agent create a new thread for this test

            # This query is designed to trigger the delegation based on the orchestrator's forceful instructions
            user_query = "Hello, I would like a greeting please."
            logger.info(f"\n--- Sending User Query to Orchestrator Agent: '{user_query}' ---")

            full_response = ""
            thread_id_for_cleanup_test = None
            async for response_part in main_sk_agent.invoke(messages=user_query, thread=conversation_thread):
                if not conversation_thread: # Capture thread from the first response part
                    conversation_thread = response_part.thread
                    if conversation_thread:
                         thread_id_for_cleanup_test = conversation_thread.id
                         logger.info(f"Interaction is happening on thread ID: {thread_id_for_cleanup_test}")

                # Handle response content
                if hasattr(response_part, 'content'):
                    logger.info(f"Orchestrator Agent Response Part: {response_part.content}")
                    full_response += str(response_part.content)

            logger.info(f"--- Full Orchestrator Agent Response for '{user_query}': {full_response} ---")

            # Check if the expected announcement and delegated greeting are present
            if "engage my specialized greeting expert" in full_response.lower() and \
               ("woohoo" in full_response.lower() or "magnificent human" in full_response.lower()):
                logger.info("SUCCESS: Orchestrator appears to have delegated the greeting task correctly!")
            else:
                logger.warning("WARNING: Orchestrator response did not clearly indicate delegation or the specialized greeting. Please check logs and agent instructions.")


            # Optional: Clean up the test thread if you want to be tidy
            if thread_id_for_cleanup_test:
                try:
                    logger.info(f"Attempting to delete test thread: {thread_id_for_cleanup_test}")
                    await client.threads.delete_thread(thread_id=thread_id_for_cleanup_test)
                    logger.info(f"Test thread {thread_id_for_cleanup_test} deleted.")
                except Exception as e:
                    logger.error(f"Error deleting test thread {thread_id_for_cleanup_test}: {e}")


    except Exception as e:
        logger.error(f"An error occurred in the test script: {e}", exc_info=True)

if __name__ == "__main__":
    # To run this test script:
    # 1. Ensure the orchestrator and specialized agents are already deployed.
    # 2. Ensure you have the necessary Python packages installed:
    #    pip install semantic-kernel azure-identity python-dotenv
    # 3. Update your.env file in the same directory with:
    #    AZURE_AI_PROJECT_CONNECTION_STRING="your_project_connection_string"
    #    AZURE_AI_MODEL_DEPLOYMENT_NAME="your_model_deployment_name" (e.g., gpt-4o)
    #    MAIN_ORCHESTRATOR_AGENT_ID="<ID_OF_YOUR_DEPLOYED_ORCHESTRATOR_AGENT>"
    #    AZURE_CLIENT_ID="your_service_principal_client_id"
    #    AZURE_CLIENT_SECRET="your_service_principal_client_secret"
    #    AZURE_TENANT_ID="your_azure_tenant_id"
    # 4. Run the script from your terminal:
    #    python simple_test_invoke.py
    asyncio.run(test_orchestrator_agent())