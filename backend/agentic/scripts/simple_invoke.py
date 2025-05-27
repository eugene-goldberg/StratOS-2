#!/usr/bin/env python3
"""
Test script for a DEPLOYED MainOrchestratorAgent.
This script implements client-side execution for function tools
requested by the deployed orchestrator. Each tool implementation
makes an SDK call to the appropriate DEPLOYED specialist agent.
"""

import asyncio
import os
import sys
import logging
from typing import List, Dict, Optional
from datetime import datetime, timezone
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [%(funcName)s] %(message)s')
logger = logging.getLogger(__name__)
logging.getLogger("azure.identity._internal.get_token_mixin").setLevel(logging.WARNING)
logging.getLogger("azure.core.pipeline.policies.http_logging_policy").setLevel(logging.WARNING)
logging.getLogger("semantic_kernel.kernel").setLevel(logging.INFO)


# Path setup
try:
    current_script_dir = os.path.dirname(os.path.abspath(__file__))
    agentic_dir = os.path.dirname(current_script_dir)
    env_path = os.path.join(agentic_dir, '.env')
    logger.info(f"Attempting to load .env file from: {env_path}")
    if load_dotenv(env_path, override=True):
        logger.info(f".env file loaded successfully from {env_path}")
    else:
        logger.warning(f".env file not found at '{env_path}'. Relying on pre-set env vars.")
except Exception as e:
    logger.error(f"Error determining .env path or loading .env: {e}")
    sys.exit(1)

# Semantic Kernel and Azure SDK imports
try:
    from azure.identity.aio import DefaultAzureCredential as AsyncDefaultAzureCredential
    from semantic_kernel import Kernel
    from semantic_kernel.agents import AzureAIAgent, AzureAIAgentSettings
    from semantic_kernel.contents.chat_message_content import ChatMessageContent
    from semantic_kernel.functions.kernel_arguments import KernelArguments
    from semantic_kernel.functions.kernel_function_decorator import kernel_function
    from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.azure_chat_prompt_execution_settings import AzureChatPromptExecutionSettings
except ImportError as e:
    logger.error(f"Error importing required modules: {e}")
    sys.exit(1)

# --- Globals for Specialist Agent SDK Calls (initialized by setup_specialist_call_infra) ---
AZURE_AI_PROJECT_SETTINGS_FOR_SPECIALISTS: Optional[AzureAIAgentSettings] = None
CREDENTIAL_FOR_SPECIALISTS: Optional[AsyncDefaultAzureCredential] = None
SPECIALIST_AGENT_IDS: Dict[str, Optional[str]] = {}


def load_specialist_ids_from_env_for_client():
    """Loads specialist agent IDs from .env for client-side tool execution."""
    global SPECIALIST_AGENT_IDS
    # These conceptual names MUST map to the function names the orchestrator calls
    specialists_map = {
        "RouteToCEOLogAgent": "CEO_LOG_AGENT_ID",
        "RouteToNorthStarAgent": "NORTH_STAR_AGENT_ID",
        "RouteToSWOTTOWSAgent": "SWOT_TOWS_AGENT_ID",
        "RouteToMemoryRecallAgent": "MEMORY_RECALL_AGENT_ID",
        "RouteToPreferenceLearningAgent": "PREFERENCE_LEARNING_AGENT_ID",
        "RouteToRiskOpportunityAgent": "RISK_OPPORTUNITY_AGENT_ID",
        "RouteToSOLinkageAgent": "SO_LINKAGE_AGENT_ID",
        "RouteToInitiativeGenerationAgent": "INITIATIVE_GENERATION_AGENT_ID",
        "RouteToResourceOptimizationAgent": "RESOURCE_OPTIMIZATION_AGENT_ID",
        "RouteToActionPlanningAgent": "ACTION_PLANNING_AGENT_ID",
        "RouteToCanvasVisualizationAgent": "CANVAS_VISUALIZATION_AGENT_ID",
        "RouteToAlignmentScoringAgent": "ALIGNMENT_SCORING_AGENT_ID",
        # Add a general/chat agent if your orchestrator might route to one by a specific tool name
        # "RouteToGeneralChat": "GENERAL_CHAT_AGENT_ID",
    }
    logger.info("Loading specialist agent IDs for client-side tool implementations...")
    for tool_name, env_var_id in specialists_map.items():
        deployed_id = os.getenv(env_var_id)
        if not deployed_id or "YOUR_ACTUAL" in deployed_id or not deployed_id.startswith("asst_"):
            logger.warning(f"Deployed Agent ID for tool '{tool_name}' (env var: {env_var_id}) is not set, is a placeholder, or invalid. Value: '{deployed_id}'. This tool will not be functional.")
            SPECIALIST_AGENT_IDS[tool_name] = None # Mark as not configured
        else:
            SPECIALIST_AGENT_IDS[tool_name] = deployed_id
            logger.info(f"  Tool '{tool_name}' will call deployed agent ID '{deployed_id}' (from env var '{env_var_id}')")


async def _call_deployed_specialist_agent_sdk(specialist_agent_id: str, user_request: str, tool_name_for_log: str) -> str:
    """Internal helper to make an SDK call to a deployed specialist agent using global settings."""
    if not specialist_agent_id or not specialist_agent_id.startswith("asst_"):
        err_msg = f"Tool '{tool_name_for_log}': Invalid or missing specialist_agent_id: '{specialist_agent_id}'."
        logger.error(err_msg)
        return f"Error: {err_msg}"
    if not AZURE_AI_PROJECT_SETTINGS_FOR_SPECIALISTS or not CREDENTIAL_FOR_SPECIALISTS:
        err_msg = f"Tool '{tool_name_for_log}': Azure AI project settings or credential for specialists not initialized."
        logger.error(err_msg)
        return f"Error: {err_msg}"

    logger.info(f"Client-Side Tool '{tool_name_for_log}': Calling deployed specialist (ID: {specialist_agent_id}) with request: '{user_request[:100]}...'")
    
    async with AzureAIAgent.create_client(
        credential=CREDENTIAL_FOR_SPECIALISTS, 
        settings=AZURE_AI_PROJECT_SETTINGS_FOR_SPECIALISTS
    ) as service_client:
        thread_id = None
        try:
            agent_definition = await service_client.agents.get_agent(agent_id=specialist_agent_id)
            sk_specialist = AzureAIAgent(client=service_client, definition=agent_definition)
            
            thread_response = await service_client.threads.create_thread()
            thread_id = thread_response.id
            
            response_content = ""
            args_for_specialist = KernelArguments()
            async for chunk in sk_specialist.invoke(message=user_request, arguments=args_for_specialist, thread_id=thread_id):
                part = chunk.content if hasattr(chunk, 'content') else (chunk[0].content if isinstance(chunk, list) and chunk and hasattr(chunk[0], 'content') else None)
                if part: response_content += part
            
            logger.info(f"Tool '{tool_name_for_log}': Specialist {specialist_agent_id} responded. Length: {len(response_content)}")
            return response_content if response_content else f"Tool '{tool_name_for_log}' (Agent {specialist_agent_id}): Specialist provided no content."
        except Exception as e:
            logger.error(f"Tool '{tool_name_for_log}': Error invoking specialist {specialist_agent_id}: {e}", exc_info=True)
            return f"Error from Tool '{tool_name_for_log}' (Agent {specialist_agent_id}): {str(e)}"
        finally:
            if thread_id:
                try: await service_client.threads.delete_thread(thread_id=thread_id)
                except Exception as e_del: logger.error(f"Tool '{tool_name_for_log}': Error deleting specialist thread {thread_id}: {e_del}")

class ClientSideOrchestratorTools:
    """
    This plugin provides Python implementations for the function tools
    that the deployed MainOrchestratorAgent is expected to call.
    Each method calls the appropriate deployed specialist agent.
    """
    # The method names here (e.g., RouteToCEOLogAgent) MUST match the tool names
    # the deployed orchestrator is trying to call.

    @kernel_function(description="Delegates tasks related to CEO logs to the CEOLogAgent.")
    async def RouteToCEOLogAgent(self, user_query_for_ceo_log: str) -> str: # Parameter name must match what LLM sends
        agent_id = SPECIALIST_AGENT_IDS.get("RouteToCEOLogAgent") # Key matches function name
        if not agent_id: return "Error: CEOLogAgent ID not configured for client-side tool."
        return await _call_deployed_specialist_agent_sdk(agent_id, user_query_for_ceo_log, "RouteToCEOLogAgent")

    @kernel_function(description="Delegates tasks related to North Star elements to the NorthStarAgent.")
    async def RouteToNorthStarAgent(self, user_query_for_north_star: str) -> str:
        agent_id = SPECIALIST_AGENT_IDS.get("RouteToNorthStarAgent")
        if not agent_id: return "Error: NorthStarAgent ID not configured for client-side tool."
        return await _call_deployed_specialist_agent_sdk(agent_id, user_query_for_north_star, "RouteToNorthStarAgent")

    @kernel_function(description="Delegates SWOT/TOWS analysis to the SWOTTOWSAgent.")
    async def RouteToSWOTTOWSAgent(self, user_query_for_swot: str) -> str:
        agent_id = SPECIALIST_AGENT_IDS.get("RouteToSWOTTOWSAgent")
        if not agent_id: return "Error: SWOTTOWSAgent ID not configured for client-side tool."
        return await _call_deployed_specialist_agent_sdk(agent_id, user_query_for_swot, "RouteToSWOTTOWSAgent")

    # ... ADD KERNEL FUNCTIONS FOR ALL 12 TOOLS ...
    # Ensure the @kernel_function name and the method name match the tool names
    # from your error log (e.g., RouteToActionPlanningAgent, RouteToAlignmentScoringAgent, etc.)

    @kernel_function(description="Delegates tasks to the MemoryRecallAgent.")
    async def RouteToMemoryRecallAgent(self, user_query_for_memory: str) -> str:
        agent_id = SPECIALIST_AGENT_IDS.get("RouteToMemoryRecallAgent")
        if not agent_id: return "Error: MemoryRecallAgent ID not configured."
        return await _call_deployed_specialist_agent_sdk(agent_id, user_query_for_memory, "RouteToMemoryRecallAgent")

    # Add all other 8 functions here, for example:
    @kernel_function(description="Delegates tasks to the ActionPlanningAgent.")
    async def RouteToActionPlanningAgent(self, user_query_for_action_plan: str) -> str:
        agent_id = SPECIALIST_AGENT_IDS.get("RouteToActionPlanningAgent")
        if not agent_id: return "Error: ActionPlanningAgent ID not configured."
        return await _call_deployed_specialist_agent_sdk(agent_id, user_query_for_action_plan, "RouteToActionPlanningAgent")

    # ... and so on for RouteToAlignmentScoringAgent, RouteToCanvasVisualizationAgent,
    # RouteToInitiativeGenerationAgent, RouteToPreferenceLearningAgent,
    # RouteToResourceOptimizationAgent, RouteToRiskOpportunityAgent, RouteToSOLinkageAgent.

async def setup_global_sdk_settings():
    """Initializes global AzureAIAgentSettings and Credential for specialist calls."""
    global AZURE_AI_PROJECT_SETTINGS_FOR_SPECIALISTS, CREDENTIAL_FOR_SPECIALISTS
    
    logger.info("Initializing AzureAIAgentSettings for specialist calls (SDK endpoint discovery)...")
    # These vars MUST be in .env for AzureAIAgentSettings to perform discovery
    # AZURE_AI_AGENT_ENDPOINT should be unset.
    essential_vars = [
        "AZURE_AI_AGENT_PROJECT_NAME", "AZURE_AI_AGENT_PROJECT_HUB_NAME",
        "AZURE_AI_AGENT_PROJECT_RESOURCE_GROUP", "AZURE_AI_AGENT_PROJECT_SUBSCRIPTION_ID",
        "AZURE_AI_AGENT_API_VERSION", "AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME"
    ]
    if not all(os.getenv(var) for var in essential_vars):
        logger.error(f"One or more critical env vars for SDK settings are missing from: {essential_vars}. Check .env.")
        return False
    
    # Ensure AZURE_AI_AGENT_ENDPOINT is NOT in os.environ for this discovery to work as intended
    if "AZURE_AI_AGENT_ENDPOINT" in os.environ and os.environ["AZURE_AI_AGENT_ENDPOINT"]:
        logger.warning(f"AZURE_AI_AGENT_ENDPOINT is currently in os.environ ('{os.environ['AZURE_AI_AGENT_ENDPOINT']}'). Unsetting for SDK discovery.")
        del os.environ["AZURE_AI_AGENT_ENDPOINT"]
    elif os.getenv("AZURE_AI_AGENT_ENDPOINT"): # If it was just in .env but not yet in os.environ after load_dotenv
        logger.warning(f"AZURE_AI_AGENT_ENDPOINT is set in .env ('{os.getenv('AZURE_AI_AGENT_ENDPOINT')}'). Forcing SDK discovery by ignoring it for AzureAIAgentSettings init.")
        # No need to del from os.environ if load_dotenv didn't put it there when it was blank.

    AZURE_AI_PROJECT_SETTINGS_FOR_SPECIALISTS = AzureAIAgentSettings()
    if AZURE_AI_PROJECT_SETTINGS_FOR_SPECIALISTS.endpoint is None:
        logger.error("CRITICAL: AzureAIAgentSettings did not resolve an endpoint for specialist calls.")
        return False
    
    logger.info(f"Global settings for specialist calls - Resolved Endpoint: '{AZURE_AI_PROJECT_SETTINGS_FOR_SPECIALISTS.endpoint}', API Version: '{AZURE_AI_PROJECT_SETTINGS_FOR_SPECIALISTS.api_version}'")
    CREDENTIAL_FOR_SPECIALISTS = AsyncDefaultAzureCredential(exclude_interactive_browser_credential=False)
    load_specialist_ids_from_env_for_client()
    return True

async def test_orchestrator_with_client_implemented_tools(orchestrator_agent_id: str, test_message: str):
    logger.info(f"--- Testing Orchestrator (ID: {orchestrator_agent_id}) with Client-Side Tool Execution ---")
    logger.info(f"User Message: \"{test_message}\"")

    if not AZURE_AI_PROJECT_SETTINGS_FOR_SPECIALISTS or not CREDENTIAL_FOR_SPECIALISTS:
        logger.error("Global SDK settings for specialists not initialized. Call setup_global_sdk_settings() first.")
        return

    # The client for the orchestrator itself uses the same project settings
    orchestrator_settings = AZURE_AI_PROJECT_SETTINGS_FOR_SPECIALISTS
    
    async with CREDENTIAL_FOR_SPECIALISTS as credential: # Can reuse the global credential
      async with AzureAIAgent.create_client(credential=credential, settings=orchestrator_settings) as service_client_for_orchestrator:
        logger.info(f"Successfully created service client for orchestrator. Endpoint: {orchestrator_settings.endpoint}")
        try:
            agent_definition = await service_client_for_orchestrator.agents.get_agent(agent_id=orchestrator_agent_id)
            logger.info(f"Fetched orchestrator definition: {agent_definition.name}")
        except Exception as e:
            logger.error(f"Failed to fetch orchestrator definition (ID: {orchestrator_agent_id}): {e}", exc_info=True)
            return

        # Create a kernel for THIS CLIENT SCRIPT and add the tool implementations to it
        client_kernel = Kernel()
        # No LLM service needed for this client_kernel if it's only executing tools.
        # If orchestrator's final response itself needs an LLM by this client (unlikely), then add service.
        client_kernel.add_plugin(ClientSideOrchestratorTools(), "OrchestratorToolFunctions") # Plugin name can be generic
        
        # Debug: Print all functions in the kernel
        logger.info("Functions registered in client kernel:")
        for plugin_name, plugin in client_kernel.plugins.items():
            logger.info(f"  Plugin: {plugin_name}")
            for function_name, function in plugin.functions.items():
                logger.info(f"    Function: {function_name}")

        # Create an AzureAIAgent instance for the DEPLOYED orchestrator.
        # Provide it with the client_kernel that contains the tool implementations.
        sk_orchestrator = AzureAIAgent(
            client=service_client_for_orchestrator, 
            definition=agent_definition,
            # kernel=client_kernel # Pass the kernel with tool implementations
            # According to SK docs, ChatCompletionAgent (which AzureAIAgent often wraps or uses patterns from)
            # should use the kernel passed to it for tool execution if function_call_filter or ToolCallBehavior is set.
            # Let's ensure the ChatCompletionAgent pattern is followed for tool execution.
            # We might need to wrap this in a ChatCompletionAgent that uses our client_kernel.
        )
        
        # To properly handle tool calls indicated by the deployed 'sk_orchestrator' (which is an AzureAIAgent),
        # we need to use an agent that can process the tool calls using 'client_kernel'.
        # We create a new ChatCompletionAgent locally that will *use* sk_orchestrator's abilities
        # but execute tools using client_kernel. This is a bit indirect.
        # A more direct way with SK's AzureAIAgent is to handle the run loop manually if invoke() doesn't auto-execute client kernel tools.

        # Let's use a ChatCompletionAgent configured for tool calling, whose "service"
        # is effectively the deployed sk_orchestrator. This is advanced.
        # For simplicity and directness with AzureAIAgent, it's usually expected that
        # if an agent's definition has tools, and client has a kernel with those tools,
        # invoke with auto-tool-execution should work.

        # The `ChatCompletionAgent` (which `AzureAIAgent` might inherit/compose) uses its own kernel for functions.
        # We need to ensure the `sk_orchestrator`'s internal kernel *is* our `client_kernel`.
        # This usually means `sk_orchestrator = ChatCompletionAgent(service=..., kernel=client_kernel, instructions=..., id=...)`
        # But `AzureAIAgent` is initialized differently.

        # The `AgentInvokeException` means `sk_orchestrator.invoke()` itself is looking in *some* kernel for the tools.
        # If `sk_orchestrator` was created WITHOUT passing a kernel, it might use a default empty one.
        # Let's try to pass the kernel to the AzureAIAgent if its constructor supports it,
        # or use a ChatCompletionAgent as a wrapper.

        # Modification: Initialize AzureAIAgent with the kernel that has the tools
        try:
            sk_orchestrator_with_tools = AzureAIAgent(
                client=service_client_for_orchestrator,
                definition=agent_definition,
                kernel=client_kernel # Provide the kernel with tool implementations
            )
            logger.info(f"Re-initialized AzureAIAgent for orchestrator with client-side kernel containing tools: {list(client_kernel.plugins.keys())}")
        except TypeError:
            logger.warning("AzureAIAgent constructor does not accept 'kernel'. Tool execution might rely on global kernel or other mechanisms.")
            sk_orchestrator_with_tools = sk_orchestrator # Fallback to original


        print(f"\n➡️ User to Orchestrator (ID: {orchestrator_agent_id}): {test_message}")
        print(f"⬅️ Orchestrator ({sk_orchestrator_with_tools.name}): ", end="", flush=True)
        
        full_response = ""
        try:
            # This execution setting enables auto-invocation of functions found in the kernel
            # associated with the agent.
            exec_settings = AzureChatPromptExecutionSettings(tool_choice="auto")
            
            args = KernelArguments() 
            
            async for chunk in sk_orchestrator_with_tools.invoke(
                message=test_message, 
                arguments=args, 
                prompt_execution_settings=exec_settings # Enable tool calling
            ):
                content_part = None
                if isinstance(chunk, ChatMessageContent) and chunk.content:
                    content_part = chunk.content
                elif isinstance(chunk, list) and chunk and isinstance(chunk[0], ChatMessageContent) and chunk[0].content:
                    content_part = chunk[0].content
                
                if content_part:
                    print(content_part, end="", flush=True)
                    full_response += content_part
            
            print("\n") 
            logger.info(f"Orchestrator's final response received (length: {len(full_response)}). Preview: {full_response[:250]}...")

        except Exception as invoke_e: 
            logger.error(f"Error during sk_orchestrator_with_tools.invoke(): {invoke_e}", exc_info=True)
            full_response = f"Error during invoke: {invoke_e}"
            print(f"\nError during interaction: {invoke_e}")

async def run_tests_client_side_tools():
    if not await setup_global_sdk_settings(): 
        logger.critical("Failed to set up global SDK settings. Exiting tests.")
        return

    orchestrator_agent_id = os.getenv("MAIN_ORCHESTRATOR_AGENT_ID")
    if not orchestrator_agent_id:
        orchestrator_agent_id = "asst_ntM606r1K9Zci3YEz1WIQEXI" 
        logger.warning(f"MAIN_ORCHESTRATOR_AGENT_ID not found in .env. Using hardcoded ID: {orchestrator_agent_id}.")
    else:
        logger.info(f"Using MAIN_ORCHESTRATOR_AGENT_ID from .env: {orchestrator_agent_id}")

    if not orchestrator_agent_id or not orchestrator_agent_id.startswith("asst_"):
        logger.error(f"Invalid MAIN_ORCHESTRATOR_AGENT_ID: '{orchestrator_agent_id}'. Must be 'asst_...'.")
        return

    test_cases = [
        {"message": "I need to record my thoughts about the market downturn and its effect on Q3 projections."},
        {"message": "What is our company's core vision statement for the next five years?"},
        {"message": "Can you perform a SWOT analysis for our new product launch?"},
    ]

    for i, tc in enumerate(test_cases):
        logger.info(f"\n--- Running Test Case #{i+1} (Client-Side Tools) ---")
        await test_orchestrator_with_client_implemented_tools(orchestrator_agent_id, tc["message"])
        if i < len(test_cases) - 1: await asyncio.sleep(1)

    logger.info("\n--- All test cases completed. ---")

if __name__ == "__main__":
    try:
        asyncio.run(run_tests_client_side_tools())
    except KeyboardInterrupt:
        logger.info("Test script stopped by user.")
    except Exception as e:
        logger.error(f"Unhandled error in script execution: {e}", exc_info=True)