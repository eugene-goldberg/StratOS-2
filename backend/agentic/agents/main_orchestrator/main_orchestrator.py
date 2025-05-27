#!/usr/bin/env python3
"""
Main Orchestrator Agent for StratOS.
This orchestrator uses Semantic Kernel plugins to delegate tasks to specialized agents
deployed in Azure AI Agent Service. Each plugin function makes an SDK call to a
deployed specialist agent.
"""

import asyncio
import os
import sys
import json
import logging
from typing import Optional, List, Dict, AsyncGenerator
from datetime import datetime, timezone
from dotenv import load_dotenv

from semantic_kernel import Kernel
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.functions.kernel_function_decorator import kernel_function
from semantic_kernel.agents import ChatCompletionAgent # For the orchestrator itself
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion # For the orchestrator's LLM
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.azure_chat_prompt_execution_settings import AzureChatPromptExecutionSettings

# Imports for calling deployed specialist agents
from azure.identity.aio import DefaultAzureCredential
from semantic_kernel.agents import AzureAIAgent, AzureAIAgentSettings 

# Configure logging as early as possible
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [%(module)s:%(funcName)s:%(lineno)d] %(message)s')
logger = logging.getLogger(__name__)
# Reduce chattiness of Azure Identity/Core logs if desired
logging.getLogger("azure.identity._internal.get_token_mixin").setLevel(logging.WARNING)
logging.getLogger("azure.core.pipeline.policies.http_logging_policy").setLevel(logging.WARNING)

# --- Path and .env loading ---
# Assumes .env file is in the same directory as this script, or one level up.
# Adjust if your .env is located elsewhere relative to this script.
try:
    env_path = ".env" # Try current directory
    if not os.path.exists(env_path):
        current_script_dir = os.path.dirname(os.path.abspath(__file__))
        # If this script is in 'backend/agentic/orchestrator_module/', and .env is in 'backend/'
        # env_path = os.path.join(os.path.dirname(os.path.dirname(current_script_dir)), '.env') 
        # For your structure (scripts in backend/agentic/scripts, .env in backend/agentic)
        # if this orchestrator.py is in backend/agentic/main_orchestrator_module/
        # then .env would be in os.path.dirname(current_script_dir)
        env_path = os.path.join(os.path.dirname(current_script_dir), '.env')


    logger.info(f"Attempting to load .env file from: {os.path.abspath(env_path)}")
    if load_dotenv(env_path, override=True): # Override to ensure script sees .env values
        logger.info(f".env file loaded successfully from {env_path}")
    else:
        logger.warning(f".env file not found at '{env_path}' or it's empty. Relying on pre-set environment variables.")
except Exception as e:
    logger.error(f"Error determining .env path or loading .env: {e}")
    # Allow to proceed if env vars are set externally

class DeployedAgentPlugin:
    """
    A Semantic Kernel plugin that acts as a proxy to a deployed Azure AI Agent.
    The orchestrator LLM will call the 'delegate_request' function of this plugin.
    """
    def __init__(self, 
                 plugin_name: str, 
                 deployed_agent_id: str,
                 description_for_llm: str, 
                 azure_ai_project_settings: AzureAIAgentSettings,
                 credential: DefaultAzureCredential):
        self._plugin_name = plugin_name
        self._deployed_agent_id = deployed_agent_id
        self.description = description_for_llm 
        self._azure_ai_project_settings = azure_ai_project_settings
        self._credential = credential
        logger.info(f"Initialized DeployedAgentPlugin: '{self._plugin_name}' for deployed agent ID: '{self._deployed_agent_id}'")

    @kernel_function(
        description="Processes a user request by delegating it to this specialized agent. Input should be the user's specific query or task intended for this agent.",
        name="delegate_request" # This is the function name the LLM will use, prefixed by plugin_name
    )
    async def delegate_request_to_specialist(
        self, 
        user_request_for_specialist: str 
    ) -> str:
        logger.info(f"Plugin '{self._plugin_name}' (Agent ID: {self._deployed_agent_id}): Delegating request: '{user_request_for_specialist[:100]}...'")
        
        if not self._azure_ai_project_settings.model_deployment_name:
             logger.error(f"Plugin '{self._plugin_name}': AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME is missing in settings for calling specialist.")
             return f"Error: Configuration missing for {self._plugin_name} (model deployment name)."
        if not self._deployed_agent_id or "YOUR_ACTUAL" in self._deployed_agent_id or not self._deployed_agent_id.startswith("asst_"):
            logger.error(f"Plugin '{self._plugin_name}': Invalid or placeholder deployed_agent_id: '{self._deployed_agent_id}'. Cannot proceed.")
            return f"Error: Specialist agent ID for {self._plugin_name} is not configured correctly."

        # Create a new client for each call for isolation, reusing settings and credential.
        async with AzureAIAgent.create_client(credential=self._credential, settings=self._azure_ai_project_settings) as service_client:
            thread_id = None
            try:
                logger.debug(f"Plugin '{self._plugin_name}': Fetching definition for agent ID '{self._deployed_agent_id}' using SDK endpoint '{self._azure_ai_project_settings.endpoint}'")
                agent_definition = await service_client.agents.get_agent(agent_id=self._deployed_agent_id) 
                logger.debug(f"Plugin '{self._plugin_name}': Fetched definition for '{agent_definition.name}'.")

                sk_specialist_agent = AzureAIAgent(
                    client=service_client, 
                    definition=agent_definition
                )

                thread_response = await service_client.threads.create_thread()
                thread_id = thread_response.id
                logger.info(f"Plugin '{self._plugin_name}': Created new thread '{thread_id}' for specialist agent '{self._deployed_agent_id}'.")

                response_content = ""
                logger.debug(f"Plugin '{self._plugin_name}': Invoking specialist agent on thread '{thread_id}'.")
                
                args_for_specialist = KernelArguments() # No specific arguments beyond the message for this pattern

                async for message_chunk in sk_specialist_agent.invoke(message=user_request_for_specialist, arguments=args_for_specialist, thread_id=thread_id):
                    chunk_text = None
                    if isinstance(message_chunk, ChatMessageContent) and message_chunk.content:
                        chunk_text = message_chunk.content
                    elif isinstance(message_chunk, list) and message_chunk and isinstance(message_chunk[0], ChatMessageContent) and message_chunk[0].content:
                        chunk_text = message_chunk[0].content
                    
                    if chunk_text:
                        response_content += chunk_text
                
                logger.info(f"Plugin '{self._plugin_name}': Specialist agent on thread '{thread_id}' responded (length: {len(response_content)}). Preview: '{response_content[:200]}...'")
                return response_content if response_content else f"{self._plugin_name} provided no substantive content."

            except Exception as e:
                logger.error(f"Plugin '{self._plugin_name}': Error invoking deployed specialist agent '{self._deployed_agent_id}' on thread '{thread_id}': {e}", exc_info=True)
                return f"Error communicating with {self._plugin_name} (ID: {self._deployed_agent_id}). Details: {str(e)}"
            finally:
                if thread_id:
                    try:
                        await service_client.threads.delete_thread(thread_id=thread_id)
                        logger.info(f"Plugin '{self._plugin_name}': Deleted thread '{thread_id}' for specialist agent '{self._deployed_agent_id}'.")
                    except Exception as e_del:
                        logger.error(f"Plugin '{self._plugin_name}': Error deleting thread '{thread_id}': {e_del}")

class MainOrchestratorAgentWrapper:
    def __init__(self, 
                 orchestrator_llm_service: AzureChatCompletion,
                 azure_ai_project_settings_for_specialists: AzureAIAgentSettings,
                 credential_for_specialists: DefaultAzureCredential,
                 specialist_agent_configs: List[Dict]):
        
        self.kernel = Kernel()
        self.kernel.add_service(orchestrator_llm_service, service_id="orchestrator_chat_service") # Give it a service_id

        self.azure_ai_project_settings = azure_ai_project_settings_for_specialists
        self.credential = credential_for_specialists
        
        agent_descriptions_for_prompt = []

        logger.info("Initializing Main Orchestrator and adding specialist agent plugins to its kernel...")
        for config in specialist_agent_configs:
            if not config.get("deployed_agent_id") or "YOUR_ACTUAL" in config.get("deployed_agent_id", "") or not config.get("deployed_agent_id","").startswith("asst_"):
                logger.warning(f"Skipping plugin setup for '{config['plugin_name']}' due to invalid or missing 'deployed_agent_id': '{config.get('deployed_agent_id')}'.")
                continue

            plugin_instance = DeployedAgentPlugin(
                plugin_name=config["plugin_name"],
                deployed_agent_id=config["deployed_agent_id"],
                description_for_llm=config["description_for_orchestrator"],
                azure_ai_project_settings=self.azure_ai_project_settings,
                credential=self.credential
            )
            self.kernel.add_plugin(plugin_instance, plugin_name=config["plugin_name"])
            agent_descriptions_for_prompt.append(f"- Tool Name: {config['plugin_name']}.delegate_request. Description: {config['description_for_orchestrator']}")
        
        agent_list_prompt_segment = "\n".join(agent_descriptions_for_prompt)
        
        orchestrator_instructions = (
            "You are the Main Orchestrator for StratOS, a comprehensive strategy operating system. "
            "Your role is to analyze incoming user requests and delegate them to the most appropriate specialized agent by calling its 'delegate_request' function.\n\n"
            
            "AVAILABLE SPECIALIST AGENT TOOLS (PLUGINS - call their 'delegate_request' function using PluginName.delegate_request syntax):\n"
            f"{agent_list_prompt_segment}\n\n"
            
            "ROUTING APPROACH:\n"
            "1. Carefully analyze the user's request to understand their specific intent and the type of task they want to perform.\n"
            "2. Review the descriptions of the AVAILABLE SPECIALIST AGENT TOOLS to identify which single specialist agent tool (PluginName.delegate_request) is best suited to handle the current request.\n"
            "3. You MUST invoke the chosen 'PluginName.delegate_request' function. Provide the user's full request or the relevant part of it as the 'user_request_for_specialist' parameter for that function call.\n"
            "4. After receiving the response from the specialist agent, present this response clearly to the user. You may add a brief introductory phrase like 'The CEOLogAgent reports:' or 'According to the NorthStarAgent:'.\n\n"
            
            "ROUTING GUIDELINES (map user need to a specific PluginName.delegate_request function call):\n"
            "- For CEO notes, observations, log entries, or subjective inputs → Call CEOLogAgent.delegate_request\n"
            "- For questions about vision, mission, values, purpose, or strategic goals → Call NorthStarAgent.delegate_request\n"
            "- For SWOT analysis or TOWS strategies → Call SWOTTOWSAgent.delegate_request\n"
            "- For retrieving past context, patterns, or historical information → Call MemoryRecallAgent.delegate_request\n"
            # Add ALL your other specialist agents and their routing guidelines here, ensuring they map to PluginName.delegate_request
            # Example: "- For tasks related to PreferenceLearning → Call PreferenceLearningAgent.delegate_request"
            # Example: "- For tasks related to RiskOpportunity → Call RiskOpportunityAgent.delegate_request"
            # Example: "- For tasks related to SOLinkage → Call SOLinkageAgent.delegate_request"
            # Example: "- For tasks related to InitiativeGeneration → Call InitiativeGenerationAgent.delegate_request"
            # Example: "- For tasks related to ResourceOptimization → Call ResourceOptimizationAgent.delegate_request"
            # Example: "- For tasks related to ActionPlanning → Call ActionPlanningAgent.delegate_request"
            # Example: "- For tasks related to CanvasVisualization → Call CanvasVisualizationAgent.delegate_request"
            # Example: "- For tasks related to AlignmentScoring → Call AlignmentScoringAgent.delegate_request"
            "- For any general chat, or if no other specialist is suitable, you can state you don't have a specific tool for that exact request and can offer general assistance or ask for clarification. Alternatively, if a GeneralChatAgent is available, route to GeneralChatAgent.delegate_request.\n\n"
            
            "IMPORTANT:\n"
            "- Do NOT attempt to answer requests directly if a specialist tool is appropriate.\n"
            "- Your primary function is to accurately route the request by choosing the correct specialist agent tool and calling its specific 'PluginName.delegate_request' function.\n"
            "- If the user's request is ambiguous or you are unsure which agent to route to, ask clarifying questions BEFORE attempting to route.\n"
            "- Ensure you pass the necessary information from the user's query to the 'user_request_for_specialist' parameter of the 'delegate_request' function."
        )
        
        self.agent = ChatCompletionAgent(
            service_id="orchestrator_chat_service", 
            kernel=self.kernel,
            name="MainOrchestrator",
            instructions=orchestrator_instructions
        )
        logger.info(f"MainOrchestrator ChatCompletionAgent created with plugins in its kernel: {list(self.kernel.plugins.keys())}")

    def get_agent(self) -> ChatCompletionAgent:
        return self.agent

def load_specialist_agent_configs_from_env() -> List[Dict]:
    logger.info("Loading specialist agent configurations from environment variables...")
    configs = []
    # ** YOU MUST ADD ALL YOUR SPECIALIST AGENT ENV VAR NAMES AND PLUGIN NAMES HERE **
    specialists_to_configure = [
        {"env_var_id": "CEO_LOG_AGENT_ID", "plugin_name": "CEOLogAgent", "description": "Handles CEO's subjective inputs, notes, observations, and concerns."},
        {"env_var_id": "NORTH_STAR_AGENT_ID", "plugin_name": "NorthStarAgent", "description": "Manages Purpose, Vision, Values, and Strategic Goals."},
        {"env_var_id": "SWOT_TOWS_AGENT_ID", "plugin_name": "SWOTTOWSAgent", "description": "Performs SWOT analysis and generates TOWS strategies."},
        {"env_var_id": "MEMORY_RECALL_AGENT_ID", "plugin_name": "MemoryRecallAgent", "description": "Retrieves context, patterns, and historical information from memory."},
        {"env_var_id": "PREFERENCE_LEARNING_AGENT_ID", "plugin_name": "PreferenceLearningAgent", "description": "Tracks user preferences and personalizes experiences."},
        {"env_var_id": "RISK_OPPORTUNITY_AGENT_ID", "plugin_name": "RiskOpportunityAgent", "description": "Identifies and analyzes risks and opportunities."},
        {"env_var_id": "SO_LINKAGE_AGENT_ID", "plugin_name": "SOLinkageAgent", "description": "Links subjective insights with objective data."},
        {"env_var_id": "INITIATIVE_GENERATION_AGENT_ID", "plugin_name": "InitiativeGenerationAgent", "description": "Creates strategic initiatives."},
        {"env_var_id": "RESOURCE_OPTIMIZATION_AGENT_ID", "plugin_name": "ResourceOptimizationAgent", "description": "Manages resource allocation and capacity planning."},
        {"env_var_id": "ACTION_PLANNING_AGENT_ID", "plugin_name": "ActionPlanningAgent", "description": "Develops detailed action plans and tracks execution."},
        {"env_var_id": "CANVAS_VISUALIZATION_AGENT_ID", "plugin_name": "CanvasVisualizationAgent", "description": "Handles visual strategic planning on canvas."},
        {"env_var_id": "ALIGNMENT_SCORING_AGENT_ID", "plugin_name": "AlignmentScoringAgent", "description": "Manages strategic conversations and assesses alignment."},
        {"env_var_id": "GENERAL_CHAT_AGENT_ID", "plugin_name": "GeneralChatAgent", "description": "Handles general conversation and queries not covered by other specialists."}
        # Add entries for all 12-15 of your specialist agents
    ]

    for spec_config in specialists_to_configure:
        deployed_id = os.getenv(spec_config["env_var_id"])
        if not deployed_id or "YOUR_ACTUAL" in deployed_id or not deployed_id.startswith("asst_"):
            logger.warning(f"Deployed Agent ID for {spec_config['plugin_name']} (env var: {spec_config['env_var_id']}) is not set, is a placeholder, or invalid. Value: '{deployed_id}'. This agent plugin might not be functional.")
            # Optionally skip adding this config if ID is invalid:
            # continue 
        
        configs.append({
            "plugin_name": spec_config["plugin_name"],
            "deployed_agent_id": deployed_id if deployed_id else f"asst_INVALID_ID_FOR_{spec_config['plugin_name']}",
            "description_for_orchestrator": spec_config["description"]
        })
        logger.info(f"Loaded config for {spec_config['plugin_name']}: ID '{deployed_id}' (from env var '{spec_config['env_var_id']}')")
        
    if not configs:
         logger.warning("No specialist agent configurations were loaded. Orchestrator will have no specialist tools.")
    return configs


async def setup_orchestrator_environment_and_agent() -> Optional[ChatCompletionAgent]:
    logger.info("Setting up orchestrator environment...")
    try:
        # 1. Configure AzureChatCompletion for the Orchestrator's own LLM
        # Relies on standard SK Azure OpenAI env vars like AZURE_OPENAI_ENDPOINT, 
        # AZURE_OPENAI_API_KEY (or AAD), AZURE_OPENAI_CHAT_DEPLOYMENT_NAME (or AZURE_OPENAI_DEPLOYMENT_NAME)
        # Check for the most common names SK uses for AzureChatCompletion default constructor
        chat_deployment_name = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME", os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"))
        if not (os.getenv("AZURE_OPENAI_ENDPOINT") and chat_deployment_name):
             logger.error("Orchestrator's Azure OpenAI endpoint or chat/text deployment name not found in .env (e.g., AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_CHAT_DEPLOYMENT_NAME/AZURE_OPENAI_DEPLOYMENT_NAME).")
             return None
        # Explicitly pass to ensure correct service is used if multiple are defined in env
        orchestrator_llm_service = AzureChatCompletion(
            deployment_name=chat_deployment_name,
            endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY"), # Will be None if not set, then AAD is used
            # Add other relevant parameters if needed, e.g., api_version for this service
        )
        logger.info(f"Orchestrator LLM service configured using deployment: {orchestrator_llm_service.settings.deployment_name} at endpoint: {orchestrator_llm_service.settings.endpoint}")

        # 2. Configure AzureAIAgentSettings for calling DEPLOYED specialist agents
        required_specialist_sdk_vars = [
            "AZURE_AI_AGENT_PROJECT_NAME", "AZURE_AI_AGENT_PROJECT_HUB_NAME",
            "AZURE_AI_AGENT_PROJECT_RESOURCE_GROUP", "AZURE_AI_AGENT_PROJECT_SUBSCRIPTION_ID",
            "AZURE_AI_AGENT_API_VERSION", "AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME"
        ]
        for var_name in required_specialist_sdk_vars:
            if not os.getenv(var_name): # These MUST come from .env for this part
                logger.error(f"Missing environment variable for specialist agent SDK settings: {var_name}. This is required in .env with the AZURE_AI_AGENT_ prefix.")
                return None
        
        # Ensure AZURE_AI_AGENT_ENDPOINT is NOT set in os.environ for SDK discovery
        if "AZURE_AI_AGENT_ENDPOINT" in os.environ:
            logger.info(f"Temporarily unsetting AZURE_AI_AGENT_ENDPOINT ('{os.environ['AZURE_AI_AGENT_ENDPOINT']}') from os.environ to force SDK discovery for specialists.")
            del os.environ["AZURE_AI_AGENT_ENDPOINT"]
        elif os.getenv("AZURE_AI_AGENT_ENDPOINT"):
             logger.warning(f"AZURE_AI_AGENT_ENDPOINT ('{os.getenv('AZURE_AI_AGENT_ENDPOINT')}') is set in .env. Unsetting it from os.environ to force SDK discovery for specialists.")
             # This is tricky as load_dotenv might not allow easy unsetting if it just happened.
             # Best to ensure it's commented out in .env for this specific configuration.
             # Forcing it for this call:
             original_env_endpoint = os.environ.pop("AZURE_AI_AGENT_ENDPOINT", None)


        azure_ai_project_settings = AzureAIAgentSettings() 
        
        # Restore env endpoint if it was popped, for other parts of app
        if 'original_env_endpoint' in locals() and original_env_endpoint is not None:
            os.environ["AZURE_AI_AGENT_ENDPOINT"] = original_env_endpoint

        if azure_ai_project_settings.endpoint is None:
            logger.error("SDK Discovery failed for Azure AI Project Agent Service endpoint. AzureAIAgentSettings.endpoint is None. Ensure AZURE_AI_AGENT_ENDPOINT is NOT set in .env and all AZURE_AI_AGENT_PROJECT_* vars are correct.")
            return None
        logger.info(f"Settings for calling specialist agents configured. Effective AI Project Agent Service Endpoint: {azure_ai_project_settings.endpoint}")

        credential_for_specialists = DefaultAzureCredential(exclude_interactive_browser_credential=False)
        specialist_agent_configs = load_specialist_agent_configs_from_env()
        if not specialist_agent_configs:
            logger.error("No specialist agent configurations loaded. Orchestrator cannot be created.")
            return None

        orchestrator_wrapper = MainOrchestratorAgentWrapper(
            orchestrator_llm_service=orchestrator_llm_service,
            azure_ai_project_settings_for_specialists=azure_ai_project_settings,
            credential_for_specialists=credential_for_specialists,
            specialist_agent_configs=specialist_agent_configs
        )
        return orchestrator_wrapper.get_agent()
    except Exception as e:
        logger.error(f"Failed during orchestrator setup: {e}", exc_info=True)
        return None

async def run_chat_loop(orchestrator_sk_agent: ChatCompletionAgent):
    chat_history = [] 
    print("\n--- StratOS Main Orchestrator (Local Run, Calls Deployed Specialists) ---")
    print("Enter 'exit' to end the chat.")
    while True:
        try:
            user_input = input("User: ")
            if user_input.lower() == "exit": logger.info("Exiting chat loop."); break
            if not user_input.strip(): continue

            print("Orchestrator: ", end="", flush=True)
            full_response = ""
            
            prompt_exec_settings = AzureChatPromptExecutionSettings(
                tool_choice="auto", 
            )
            
            # For ChatCompletionAgent, history is usually managed via KernelArguments or agent state
            # Let's pass history if the agent supports it.
            # For simplicity, we'll just send the input. If your orchestrator needs history,
            # you'd build up a chat_history list of ChatMessageContent objects.
            args = KernelArguments(input=user_input)
            # If you want to manage history explicitly for the orchestrator:
            # current_history_for_invoke = [msg for msg in chat_history] # Pass a copy
            # args = KernelArguments(input=user_input, chat_history=current_history_for_invoke)


            # Using invoke which should handle tool calls internally and return final ChatMessageContent
            final_result = await orchestrator_sk_agent.invoke(
                input=user_input, # or arguments=args
                prompt_execution_settings=prompt_exec_settings,
                # If managing history explicitly for invoke:
                # chat_history=chat_history # This depends on how ChatCompletionAgent version handles history with invoke vs invoke_stream
            )
            
            content_part = None
            if isinstance(final_result, ChatMessageContent):
                content_part = final_result.content
            elif isinstance(final_result, list) and final_result and isinstance(final_result[0], ChatMessageContent):
                content_part = final_result[0].content # Should not happen with invoke, more for invoke_stream
            elif isinstance(final_result, str): # Should not happen with invoke, more for invoke_stream
                 content_part = final_result

            if content_part:
                print(content_part, end="", flush=True)
                full_response = content_part
            else:
                logger.warning(f"Orchestrator invoke returned no primary content. Result: {final_result}")
                # Try to inspect tool calls if available on final_result (depends on SK version and what invoke returns)
                if hasattr(final_result, 'tool_calls') and final_result.tool_calls:
                    logger.info(f"Orchestrator invoke resulted in tool calls: {final_result.tool_calls}")
                elif isinstance(final_result, ChatMessageContent) and final_result.tool_calls:
                    logger.info(f"Orchestrator invoke ChatMessageContent has tool calls: {final_result.tool_calls}")


            print() 

            # Update chat_history for next turn with orchestrator
            # chat_history.append(ChatMessageContent(role="user", content=user_input))
            # chat_history.append(ChatMessageContent(role="assistant", content=full_response if full_response else "No textual response to add to history."))


        except Exception as e:
            logger.error(f"Error in chat loop: {e}", exc_info=True)
            print(f"\nSystem Error: {e}")


if __name__ == "__main__":
    logger.info("Starting orchestrator for local testing with deployed specialist agents...")
    try:
        orchestrator_agent_instance = asyncio.run(setup_orchestrator_environment_and_agent())
        if orchestrator_agent_instance:
            logger.info("Orchestrator agent setup complete. Starting interactive chat loop...")
            asyncio.run(run_chat_loop(orchestrator_agent_instance))
        else:
            logger.error("Failed to initialize and retrieve the orchestrator agent. Exiting.")
    except KeyboardInterrupt:
        logger.info("Orchestrator script stopped by user.")
    except Exception as e:
        logger.critical(f"Unhandled critical error in orchestrator script: {e}", exc_info=True)