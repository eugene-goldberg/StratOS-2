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
from semantic_kernel.agents import ChatCompletionAgent, Agent # For the orchestrator itself
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion # For the orchestrator's LLM
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.prompt_template.prompt_template_config import PromptTemplateConfig
from semantic_kernel.prompt_template.input_variable import InputVariable

# Imports for calling deployed specialist agents
from azure.identity.aio import DefaultAzureCredential
from semantic_kernel.agents import AzureAIAgent, AzureAIAgentSettings # For specialist agents

# Configure logging as early as possible
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [%(module)s:%(funcName)s:%(lineno)d] %(message)s')
logger = logging.getLogger(__name__)
# Set higher level for chatty libraries if needed
logging.getLogger("azure.identity._internal.get_token_mixin").setLevel(logging.WARNING)
logging.getLogger("azure.core.pipeline.policies.http_logging_policy").setLevel(logging.WARNING)


# --- Path and .env loading ---
# Assumes .env file is one directory level up from this script's directory
# e.g., if script is in 'orchestrator_module/', .env is in its parent.
# Adjust path if your .env is located elsewhere relative to this script.
try:
    current_script_dir = os.path.dirname(os.path.abspath(__file__))
    env_path_relative_to_this_file = os.path.join(os.path.dirname(current_script_dir), '.env') 

    logger.info(f"Attempting to load .env file from: {env_path_relative_to_this_file}")
    if load_dotenv(env_path_relative_to_this_file):
        logger.info(f".env file loaded successfully from {env_path_relative_to_this_file}")
    else:
        logger.warning(f".env file not found at '{env_path_relative_to_this_file}' or it's empty. Relying on pre-set environment variables.")
except Exception as e:
    logger.error(f"Error determining .env path or loading .env: {e}")
# --- End .env loading ---


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
        self.description = description_for_llm # Overall plugin description
        self._azure_ai_project_settings = azure_ai_project_settings
        self._credential = credential
        logger.info(f"Initialized DeployedAgentPlugin: '{self._plugin_name}' for deployed agent ID: '{self._deployed_agent_id}'")

    @kernel_function(
        description="Processes a user request by delegating it to this specialized agent. Input should be the user's specific query or task intended for this agent.",
        name="delegate_request" # Explicitly naming the function for SK
    )
    async def delegate_request_to_specialist(
        self, 
        user_request_for_specialist: str # Parameter description can also be added here for more complex inputs
    ) -> str:
        """
        Sends the user_request_for_specialist to the deployed specialist agent
        and returns its complete response.
        """
        logger.info(f"Plugin '{self._plugin_name}' (Agent ID: {self._deployed_agent_id}): Delegating request: '{user_request_for_specialist[:100]}...'")
        
        if not self._azure_ai_project_settings.model_deployment_name:
             logger.error(f"Plugin '{self._plugin_name}': AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME is missing in settings for calling specialist.")
             return f"Error: Configuration missing for {self._plugin_name}."
        if self._deployed_agent_id is None or "YOUR_ACTUAL" in self._deployed_agent_id:
            logger.error(f"Plugin '{self._plugin_name}': Invalid or placeholder deployed_agent_id: '{self._deployed_agent_id}'. Cannot proceed.")
            return f"Error: Specialist agent ID for {self._plugin_name} is not configured correctly."

        # Create a new client for each call for isolation, reusing settings and credential.
        async with AzureAIAgent.create_client(credential=self._credential, settings=self._azure_ai_project_settings) as service_client:
            thread_id = None
            try:
                logger.debug(f"Plugin '{self._plugin_name}': Fetching definition for agent ID '{self._deployed_agent_id}' using SDK endpoint '{self._azure_ai_project_settings.endpoint}'")
                agent_definition = await service_client.agents.get_agent(assistant_id=self._deployed_agent_id)
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
                async for message_chunk in sk_specialist_agent.invoke(message=user_request_for_specialist, thread_id=thread_id):
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
    """
    Wrapper for the Main Orchestrator agent.
    Its `ChatCompletionAgent` uses plugins that call deployed specialist Azure AI Agents.
    """
    
    def __init__(self, 
                 orchestrator_llm_service: AzureChatCompletion,
                 azure_ai_project_settings_for_specialists: AzureAIAgentSettings,
                 credential_for_specialists: DefaultAzureCredential,
                 specialist_agent_configs: List[Dict]):
        
        self.kernel = Kernel()
        self.kernel.add_service(orchestrator_llm_service)

        self.azure_ai_project_settings = azure_ai_project_settings_for_specialists
        self.credential = credential_for_specialists
        
        agent_descriptions_for_prompt = []

        logger.info("Initializing Main Orchestrator and adding specialist agent plugins to its kernel...")
        for config in specialist_agent_configs:
            plugin_instance = DeployedAgentPlugin(
                plugin_name=config["plugin_name"],
                deployed_agent_id=config["deployed_agent_id"],
                description_for_llm=config["description_for_orchestrator"],
                azure_ai_project_settings=self.azure_ai_project_settings,
                credential=self.credential
            )
            self.kernel.add_plugin(plugin_instance, plugin_name=config["plugin_name"])
            agent_descriptions_for_prompt.append(f"- {config['plugin_name']}: {config['description_for_orchestrator']}")
        
        agent_list_prompt_segment = "\n".join(agent_descriptions_for_prompt)
        
        # This is the system prompt for the Orchestrator LLM
        orchestrator_instructions = (
            "You are the Main Orchestrator for StratOS, a comprehensive strategy operating system. "
            "Your role is to analyze incoming user requests and delegate them to the most appropriate specialized agent by calling its 'delegate_request' function.\n\n"
            
            "AVAILABLE SPECIALIST AGENT TOOLS (PLUGINS - call their 'delegate_request' function):\n"
            f"{agent_list_prompt_segment}\n\n"
            
            "ROUTING APPROACH:\n"
            "1. Carefully analyze the user's request to understand their specific intent and the type of task they want to perform.\n"
            "2. Review the descriptions of the AVAILABLE SPECIALIST AGENT TOOLS to identify which single specialist agent is best suited to handle the current request.\n"
            "3. Once you have identified the correct specialist agent tool, you MUST invoke its 'delegate_request' function. Provide the complete and relevant part of the user's original request as the 'user_request_for_specialist' parameter for that function.\n"
            "4. After receiving the response from the specialist agent, present this response clearly to the user. You may add a brief introductory phrase like 'The CEOLogAgent reports:' or 'According to the NorthStarAgent:'.\n\n"
            
            "ROUTING GUIDELINES (map user need to the 'delegate_request' function of the specified plugin/tool name):\n"
            "- For CEO notes, observations, log entries, or subjective inputs → Call CEOLogAgent.delegate_request\n"
            "- For questions about vision, mission, values, purpose, or strategic goals → Call NorthStarAgent.delegate_request\n"
            "- For SWOT analysis or TOWS strategies → Call SWOTTOWSAgent.delegate_request\n"
            "- For retrieving past context, patterns, or historical information → Call MemoryRecallAgent.delegate_request\n"
            "- For personalization, user preferences, or behavioral patterns → Call PreferenceLearningAgent.delegate_request\n"
            "- For identifying and analyzing risks or opportunities → Call RiskOpportunityAgent.delegate_request\n"
            "- For linking subjective insights with objective data → Call SOLinkageAgent.delegate_request\n"
            "- For creating new strategic initiatives → Call InitiativeGenerationAgent.delegate_request\n"
            "- For resource allocation, capacity planning, or optimization → Call ResourceOptimizationAgent.delegate_request\n"
            "- For developing action plans or tracking execution → Call ActionPlanningAgent.delegate_request\n"
            "- For visual strategic planning or canvas work → Call CanvasVisualizationAgent.delegate_request\n"
            "- For assessing strategic alignment or managing conversations → Call AlignmentScoringAgent.delegate_request\n"
            "\n"
            "IMPORTANT:\n"
            "- Do NOT attempt to answer the user's request directly if it falls under the responsibility of a specialist agent.\n"
            "- Your primary function is to accurately route the request by choosing the correct specialist agent tool and calling its 'delegate_request' function.\n"
            "- If the user's request is ambiguous or you are unsure which agent to route to, ask clarifying questions to better understand their need before attempting to route.\n"
            "- Ensure you pass the necessary information from the user's query to the 'user_request_for_specialist' parameter of the 'delegate_request' function."
        )
        
        self.agent = ChatCompletionAgent(
            service_id=None, 
            kernel=self.kernel,
            name="MainOrchestrator",
            instructions=orchestrator_instructions
        )
        logger.info(f"MainOrchestrator ChatCompletionAgent created with {len(self.kernel.plugins)} specialist agent plugins available in its kernel.")

    def get_agent(self) -> ChatCompletionAgent:
        return self.agent

def load_specialist_agent_configs_from_env() -> List[Dict]:
    """
    Loads specialist agent configurations from environment variables.
    Each specialist agent needs an environment variable for its deployed ID.
    Example: CEO_LOG_AGENT_ID="asst_XYZ..."
    """
    logger.info("Loading specialist agent configurations from environment variables...")
    configs = []
    # Define your specialist agents and the environment variables that hold their IDs
    # The 'plugin_name' is how SK will refer to the tool (PluginName.FunctionName)
    # The 'description_for_orchestrator' helps the orchestrator LLM choose the right tool.
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
        {"env_var_id": "ALIGNMENT_SCORING_AGENT_ID", "plugin_name": "AlignmentScoringAgent", "description": "Manages strategic conversations and assesses alignment."}
    ]

    for spec_config in specialists_to_configure:
        deployed_id = os.getenv(spec_config["env_var_id"])
        if not deployed_id or "YOUR_ACTUAL" in deployed_id:
            logger.error(f"CRITICAL: Deployed Agent ID for {spec_config['plugin_name']} (env var: {spec_config['env_var_id']}) is not set or is a placeholder. This agent plugin will not be functional.")
            # Decide if you want to skip this agent or raise an error / sys.exit(1)
            # For now, we'll let it try to initialize but it will fail if called.
            deployed_id = "asst_INVALID_ID_NOT_SET" # Fallback to prevent None error later, but it will fail if used
        
        configs.append({
            "plugin_name": spec_config["plugin_name"],
            "deployed_agent_id": deployed_id,
            "description_for_orchestrator": spec_config["description"]
        })
        logger.info(f"Loaded config for {spec_config['plugin_name']}: ID '{deployed_id}' (from env var '{spec_config['env_var_id']}')")
        
    if not configs:
         logger.warning("No specialist agent configurations were loaded. Orchestrator will have no specialist tools.")
    return configs


async def setup_orchestrator_environment_and_agent() -> Optional[ChatCompletionAgent]:
    """
    Loads .env, configures services, and creates the Main Orchestrator agent instance.
    Returns the orchestrator's ChatCompletionAgent instance or None on failure.
    """
    logger.info("Setting up orchestrator environment...")

    # 1. Configure AzureChatCompletion for the Orchestrator's own LLM
    try:
        # These env vars are for the ORCHESTRATOR's primary LLM.
        # Ensure they are set in your .env file (e.g., AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY or AAD, AZURE_OPENAI_CHAT_DEPLOYMENT_NAME)
        # Semantic Kernel's AzureChatCompletion will pick them up by default.
        # Add explicit checks if certain ones are absolutely required:
        if not (os.getenv("AZURE_OPENAI_ENDPOINT") and os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME")): # API Key optional if using AAD
             logger.error("Orchestrator's Azure OpenAI endpoint or chat deployment name not found in .env (e.g., AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_CHAT_DEPLOYMENT_NAME).")
             return None
        orchestrator_llm_service = AzureChatCompletion() # Reads from default SK Azure OpenAI env vars
        logger.info(f"Orchestrator LLM service configured using deployment: {orchestrator_llm_service.settings.deployment_name} at endpoint: {orchestrator_llm_service.settings.endpoint}")
    except Exception as e:
        logger.error(f"Failed to configure AzureChatCompletion for orchestrator: {e}", exc_info=True)
        return None

    # 2. Configure AzureAIAgentSettings for calling DEPLOYED specialist agents
    try:
        # These use AZURE_AI_AGENT_* variables for project context and ai.azure.com discovery
        required_specialist_sdk_vars = [
            "AZURE_AI_AGENT_PROJECT_NAME", "AZURE_AI_AGENT_PROJECT_HUB_NAME",
            "AZURE_AI_AGENT_PROJECT_RESOURCE_GROUP", "AZURE_AI_AGENT_PROJECT_SUBSCRIPTION_ID",
            "AZURE_AI_AGENT_API_VERSION", "AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME"
        ]
        for var_name in required_specialist_sdk_vars:
            if not os.getenv(var_name):
                logger.error(f"Missing environment variable for specialist agent SDK settings: {var_name}. This is required in .env.")
                return None
        
        azure_ai_project_settings = AzureAIAgentSettings() # Loads from AZURE_AI_AGENT_* env vars
        if azure_ai_project_settings.endpoint is None: # Check if SDK discovery worked
            logger.error("SDK Discovery failed for Azure AI Project Agent Service endpoint. AzureAIAgentSettings.endpoint is None. Ensure AZURE_AI_AGENT_ENDPOINT is NOT set in .env and all AZURE_AI_AGENT_PROJECT_* vars are correct.")
            return None
        logger.info(f"Settings for calling specialist agents configured. Effective AI Project Agent Service Endpoint: {azure_ai_project_settings.endpoint}")
    except Exception as e:
        logger.error(f"Failed to configure AzureAIAgentSettings for specialists: {e}", exc_info=True)
        return None

    # 3. DefaultAzureCredential for specialist agent calls
    credential_for_specialists = DefaultAzureCredential(exclude_interactive_browser_credential=False)

    # 4. Specialist Agent Configurations (IDs, names, descriptions)
    specialist_agent_configs = load_specialist_agent_configs_from_env()
    if not specialist_agent_configs: # Check if any configs were actually loaded
        logger.error("No specialist agent configurations loaded. Orchestrator cannot be created without specialist tools.")
        return None

    # 5. Create the Main Orchestrator Agent
    try:
        orchestrator_wrapper = MainOrchestratorAgentWrapper(
            orchestrator_llm_service=orchestrator_llm_service,
            azure_ai_project_settings_for_specialists=azure_ai_project_settings,
            credential_for_specialists=credential_for_specialists,
            specialist_agent_configs=specialist_agent_configs
        )
        return orchestrator_wrapper.get_agent()
    except Exception as e:
        logger.error(f"Failed to create MainOrchestratorAgent: {e}", exc_info=True)
        return None

async def run_chat_loop(orchestrator_sk_agent: ChatCompletionAgent):
    """Runs the interactive chat loop with the orchestrator."""
    # This history should be specific to the orchestrator's conversation
    chat_history = [] 
    print("\n--- StratOS Main Orchestrator ---")
    print("Enter 'exit' to end the chat.")
    while True:
        try:
            user_input = input("User: ")
            if user_input.lower() == "exit":
                logger.info("Exiting chat loop.")
                break
            if not user_input.strip():
                continue

            print("Orchestrator: ", end="", flush=True)
            full_response = ""
            
            # Use KernelArguments for invoke_stream
            args = KernelArguments(input=user_input, chat_history=chat_history)
            
            async for message_fragment in orchestrator_sk_agent.invoke_stream(arguments=args):
                content_part = ""
                # Handle different structures of message_fragment from invoke_stream
                # It often yields ChatMessageContent objects or lists of them.
                if isinstance(message_fragment, ChatMessageContent):
                    if message_fragment.content:
                        content_part = message_fragment.content
                elif isinstance(message_fragment, list) and message_fragment:
                    if isinstance(message_fragment[0], ChatMessageContent) and message_fragment[0].content:
                        content_part = message_fragment[0].content
                elif isinstance(message_fragment, str): # Simpler streaming might yield strings
                    content_part = message_fragment
                
                if content_part:
                    print(content_part, end="", flush=True)
                    full_response += content_part
            
            print() 

            # Update history for the orchestrator's perspective
            chat_history.append(ChatMessageContent(role="user", content=user_input))
            chat_history.append(ChatMessageContent(role="assistant", content=full_response))

        except Exception as e:
            logger.error(f"Error in chat loop: {e}", exc_info=True)
            print(f"\nSystem Error: {e}")


if __name__ == "__main__":
    # This main block is for local testing of the orchestrator.
    # When deploying the orchestrator itself to Azure AI Agent Service, this block would not be the entry point.
    # Instead, Azure AI Agent Service would host the orchestrator agent and invoke its capabilities.
    # The code that defines the orchestrator (MainOrchestratorAgentWrapper and DeployedAgentPlugin)
    # and its tools IS the core logic for the deployed orchestrator agent.
    logger.info("Starting orchestrator for local testing...")
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