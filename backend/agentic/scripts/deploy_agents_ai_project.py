#!/usr/bin/env python3
"""
Deploy StratOS agents to Azure AI Agent Service within an Azure AI Project.
This version attempts to let the SDK discover the endpoint via project context
when targeting ai.azure.com.
"""

import asyncio
import os
import sys
import json
import logging
from datetime import datetime, timezone
from dotenv import load_dotenv

# Configure logging as early as possible
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [%(funcName)s] %(message)s')
logger = logging.getLogger(__name__)

# Add parent directories to path
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
sys.path.insert(0, backend_dir)

# Load environment variables from .env file in the backend directory
env_path = os.path.join(backend_dir, '.env')
logger.info(f"Attempting to load .env file from: {env_path}")
if load_dotenv(env_path):
    logger.info(".env file loaded successfully.")
else:
    logger.warning(f".env file not found at '{env_path}' or it's empty. Relying on pre-set environment variables.")

# Import required modules
try:
    from azure.identity.aio import DefaultAzureCredential
    from semantic_kernel.agents import AzureAIAgent, AzureAIAgentSettings
except ImportError as e:
    logger.error(f"Error importing required modules: {e}")
    logger.error("Please ensure 'semantic-kernel[azure]' and 'azure-identity' are installed.")
    logger.error("Double-check your Semantic Kernel version for the correct import paths if issues persist.")
    sys.exit(1)

async def deploy_agent(
    agent_name: str,
    agent_instructions: str,
    agent_description: str,
    settings: AzureAIAgentSettings,
    credential
) -> tuple[AzureAIAgent | None, str | None]:
    """
    Deploys an agent to the Azure AI Project's Agent Service.
    """
    try:
        async with AzureAIAgent.create_client(credential=credential, settings=settings) as client:
            logger.info(f"AzureAIAgent.create_client successful. SDK is configured with Endpoint: '{settings.endpoint}', Model: '{settings.model_deployment_name}', API_Version: '{settings.api_version}', Project Context (from env): '{os.getenv('AZURE_AI_AGENT_PROJECT_NAME')}'")
            logger.info(f"Attempting to deploy agent: {agent_name}")
            
            existing_agent_definition = None
            try:
                logger.info(f"Checking if agent '{agent_name}' already exists...")
                all_agents_iterable = client.agents.list_agents()
                async for agent_def in all_agents_iterable:
                    if agent_def.name == agent_name:
                        existing_agent_definition = agent_def
                        logger.info(f"Agent '{agent_name}' already exists with ID: {existing_agent_definition.id}")
                        break
                if not existing_agent_definition:
                     logger.info(f"Agent '{agent_name}' not found in existing agents list.")
            except Exception as e:
                logger.warning(f"Could not list existing agents or agent '{agent_name}' not found. Error: {e}", exc_info=False)
                logger.warning("This might be okay if the agent is new or if listing isn't fully supported/required here.")

            if existing_agent_definition:
                agent_definition = existing_agent_definition
                logger.info(f"Using existing agent definition for '{agent_name}'.")
            else:
                logger.info(f"Creating new agent '{agent_name}' with model '{settings.model_deployment_name}'.")
                agent_definition = await client.agents.create_agent(
                    model=settings.model_deployment_name,
                    name=agent_name,
                    instructions=agent_instructions,
                    description=agent_description
                )
                logger.info(f"Agent '{agent_name}' created successfully with ID: {agent_definition.id}")

            sk_agent = AzureAIAgent(
                client=client,
                definition=agent_definition,
            )
            return sk_agent, agent_definition.id
    except Exception as e:
        logger.error(f"Failed to deploy agent '{agent_name}': {e}")
        raise 
    return None, None


AGENTS_TO_DEPLOY_CONFIG = [
    # Strategic Foundation & Insights System (5 agents)
    {
        "name": "StrategicContextRouter",
        "instructions": (
            "You are the Strategic Context Router for StratOS. Your role is to analyze incoming requests and route them to "
            "the appropriate specialized agent within the Strategic Foundation & Insights System. You manage: "
            "1) CEO Log Agent for subjective inputs and voice transcriptions, "
            "2) North Star Agent for vision, values, and strategic goals, "
            "3) Memory & Recall Agent for context retrieval and pattern recognition, "
            "4) Preference Learning Agent for personalization."
        ),
        "description": "Routes requests within the Strategic Foundation system"
    },
    {
        "name": "CEOLogAgent",
        "instructions": (
            "You are the CEO Log Agent for StratOS. You specialize in processing subjective inputs from the CEO including "
            "voice transcriptions, thoughts, observations, and strategic reflections. Your capabilities include: "
            "1) Processing voice-to-text transcriptions, 2) Generating relevant tags for entries, "
            "3) Creating concise summaries, 4) Extracting strategic insights from subjective content."
        ),
        "description": "Manages CEO's subjective inputs, voice transcriptions, and insights"
    },
    {
        "name": "NorthStarAgent",
        "instructions": (
            "You are the North Star Agent for StratOS. You are the guardian of the organization's strategic foundation "
            "including Purpose, Vision, Values, and Strategic Goals. Your responsibilities include: "
            "1) Maintaining consistency across all strategic elements, 2) Managing hierarchical goal structures, "
            "3) Validating goal alignment with organizational values, 4) Providing guidance on strategic direction."
        ),
        "description": "Manages organizational purpose, vision, values, and strategic goals"
    },
    {
        "name": "MemoryRecallAgent",
        "instructions": (
            "You are the Memory & Recall Agent for StratOS. You specialize in retrieving relevant strategic context "
            "and identifying patterns across the organization's history. Your capabilities include: "
            "1) Semantic search across all strategic documents and logs, 2) Pattern recognition in historical data, "
            "3) Context assembly for decision-making, 4) Trend identification over time."
        ),
        "description": "Provides strategic context retrieval and pattern recognition"
    },
    {
        "name": "PreferenceLearningAgent",
        "instructions": (
            "You are the Preference Learning Agent for StratOS. You observe user interactions to learn preferences "
            "and personalize the experience. Your focus areas include: 1) Tracking accepted vs rejected suggestions, "
            "2) Learning communication style preferences, 3) Understanding decision-making patterns, "
            "4) Adapting responses based on user history."
        ),
        "description": "Learns and applies user preferences for personalization"
    },
    # Analysis & Intelligence System (4 agents)
    {
        "name": "AnalysisOrchestrator",
        "instructions": (
            "You are the Analysis Orchestrator for StratOS. You coordinate all analytical activities within the "
            "Analysis & Intelligence System. You manage: 1) SWOT/TOWS Agent for strategic analysis, "
            "2) Risk/Opportunity Agent for threat and opportunity detection, "
            "3) S+O Linkage Agent for connecting subjective and objective data."
        ),
        "description": "Orchestrates complex analysis workflows"
    },
    {
        "name": "SWOTTOWSAgent",
        "instructions": (
            "You are the SWOT/TOWS Agent for StratOS. You specialize in strategic analysis using SWOT "
            "(Strengths, Weaknesses, Opportunities, Threats) and TOWS matrix methodologies. Your process includes: "
            "1) Guiding users through comprehensive SWOT analysis, 2) Maintaining session state for multi-step analysis, "
            "3) Generating TOWS strategies by combining SWOT elements, 4) Providing contextual prompts."
        ),
        "description": "Performs SWOT analysis and generates TOWS strategies"
    },
    {
        "name": "RiskOpportunityAgent",
        "instructions": (
            "You are the Risk/Opportunity Detection Agent for StratOS. You continuously monitor for potential risks "
            "and opportunities across all organizational data. Your capabilities include: "
            "1) Anomaly detection in patterns and metrics, 2) Risk assessment with severity levels, "
            "3) Opportunity identification with potential impact, 4) Alert generation with recommended actions."
        ),
        "description": "Detects and assesses risks and opportunities"
    },
    {
        "name": "SOLinkageAgent",
        "instructions": (
            "You are the S+O Linkage Agent for StratOS. You specialize in discovering connections between subjective "
            "inputs (CEO thoughts, observations) and objective data (KPIs, metrics, market data). Your process includes: "
            "1) Pattern matching between qualitative and quantitative information, 2) Correlation analysis, "
            "3) Insight generation that bridges intuition and data."
        ),
        "description": "Links subjective insights with objective data"
    },
    # Planning & Execution System (6 agents)
    {
        "name": "PlanningCoordinator",
        "instructions": (
            "You are the Planning Coordinator for StratOS. You orchestrate all planning and execution activities. "
            "You manage: 1) Initiative Generation Agent for creating strategic initiatives, "
            "2) Resource Optimization Agent for allocation decisions, 3) Canvas Visualization Agent for visual planning, "
            "4) Alignment Scoring Agent for strategic fit assessment, 5) Action Planning Agent for detailed execution plans."
        ),
        "description": "Coordinates planning and execution activities"
    },
    {
        "name": "InitiativeGenerationAgent",
        "instructions": (
            "You are the Initiative Generation Agent for StratOS. You create strategic initiatives that bridge the gap "
            "between high-level strategy and executable actions. Your process includes: "
            "1) Analyzing strategic goals and current state, 2) Generating initiative proposals with clear objectives, "
            "3) Defining measurable success metrics, 4) Creating milestone-based timelines."
        ),
        "description": "Creates strategic initiatives and action plans"
    },
    {
        "name": "ResourceOptimizationAgent",
        "instructions": (
            "You are the Resource Optimization Agent for StratOS. You ensure optimal allocation of resources "
            "(people, budget, time) across all strategic initiatives. Your capabilities include: "
            "1) Resource capacity analysis, 2) Allocation optimization based on strategic priorities, "
            "3) Cost-benefit analysis for resource decisions, 4) Utilization tracking and recommendations."
        ),
        "description": "Optimizes resource allocation across initiatives"
    },
    {
        "name": "CanvasVisualizationAgent",
        "instructions": (
            "You are the Canvas Visualization Agent for StratOS. You help users create and manage visual representations "
            "of their strategy using the Strategic Canvas. Your capabilities include: "
            "1) Structuring text into visual nodes, 2) Suggesting meaningful connections between elements, "
            "3) Identifying themes and patterns in canvas layouts, 4) Processing voice commands for canvas manipulation."
        ),
        "description": "Manages visual strategic planning on canvas"
    },
    {
        "name": "AlignmentScoringAgent",
        "instructions": (
            "You are the Alignment Scoring Agent for StratOS. You evaluate how well initiatives and actions align "
            "with strategic objectives. Your assessment includes: 1) Scoring initiatives against strategic goals, "
            "2) Identifying alignment gaps and conflicts, 3) Recommending adjustments for better fit, "
            "4) Tracking alignment trends over time."
        ),
        "description": "Assesses strategic alignment of initiatives"
    },
    {
        "name": "ActionPlanningAgent",
        "instructions": (
            "You are the Action Planning Agent for StratOS. You transform strategic initiatives into detailed, "
            "executable action plans. Your planning includes: 1) Task breakdown structures, "
            "2) Timeline creation with dependencies, 3) Responsibility assignment (RACI), "
            "4) Progress tracking mechanisms."
        ),
        "description": "Creates detailed execution plans for initiatives"
    }
]

async def deploy_all_agents(settings, credential):
    """Deploy all StratOS agents."""
    deployed_agents_info = []
    logger.info("\n=== Deploying All Configured Agents ===")
    for agent_config in AGENTS_TO_DEPLOY_CONFIG:
        try:
            _, agent_id = await deploy_agent(
                agent_name=agent_config["name"],
                agent_instructions=agent_config["instructions"],
                agent_description=agent_config["description"],
                settings=settings,
                credential=credential
            )
            if agent_id:
                deployed_agents_info.append((agent_config["name"], agent_id))
        except Exception: 
            logger.error(f"Skipping agent '{agent_config['name']}' in deploy_all_agents due to error during its deployment attempt.")
    return deployed_agents_info

async def main():
    """Main deployment function"""
    logger.info("===== StratOS Agent Deployment to Azure AI Project Agent Service =====")
    logger.info(f"Deployment started at: {datetime.now(timezone.utc).isoformat()}")
    
    try:
        # --- Environment Variables expected by AzureAIAgentSettings ---
        # Script ensures these are set in os.environ for AzureAIAgentSettings to consume.
        # Values should primarily come from .env file.

        # 1. AZURE_AI_AGENT_ENDPOINT:
        #    For this test, we are expecting this to be ABSENT from .env or blank,
        #    to allow SDK to discover the endpoint using project context.
        #    If it IS set in .env, we will use that value.
        env_endpoint = os.getenv("AZURE_AI_AGENT_ENDPOINT")
        if env_endpoint:
            logger.info(f"AZURE_AI_AGENT_ENDPOINT is set in .env: '{env_endpoint}'. Script will use this.")
            os.environ["AZURE_AI_AGENT_ENDPOINT"] = env_endpoint
        else:
            logger.info("AZURE_AI_AGENT_ENDPOINT is NOT SET in .env. Relying on SDK discovery using project context variables.")
            # Ensure it's not lingering in os.environ from a previous hardcoding if .env doesn't have it
            if "AZURE_AI_AGENT_ENDPOINT" in os.environ:
                del os.environ["AZURE_AI_AGENT_ENDPOINT"]


        # 2. Model Deployment Name
        model_deployment_name = os.getenv("AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME")
        if not model_deployment_name:
            logger.error("CRITICAL: AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME is not set in .env. This is required.")
            sys.exit(1)
        os.environ["AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME"] = model_deployment_name

        # 3. API Version
        api_version = os.getenv("AZURE_AI_AGENT_API_VERSION")
        if not api_version:
            logger.error("CRITICAL: AZURE_AI_AGENT_API_VERSION is not set in .env. Expected e.g. '2024-12-01-preview'.")
            sys.exit(1)
        os.environ["AZURE_AI_AGENT_API_VERSION"] = api_version

        # 4. Project Context Variables
        # These MUST have the AZURE_AI_AGENT_ prefix in the .env file for AzureAIAgentSettings to find them automatically
        project_vars_to_check = [
            "AZURE_AI_AGENT_PROJECT_NAME",
            "AZURE_AI_AGENT_PROJECT_HUB_NAME",
            "AZURE_AI_AGENT_PROJECT_RESOURCE_GROUP",
            "AZURE_AI_AGENT_PROJECT_SUBSCRIPTION_ID"
        ]
        logger.info("--- Checking required Azure AI Project context variables in .env ---")
        for var_name in project_vars_to_check:
            val = os.getenv(var_name)
            if not val:
                logger.error(f"CRITICAL: Required environment variable '{var_name}' is not set in .env.")
                sys.exit(1)
            os.environ[var_name] = val # Ensure it's in os.environ for settings
            logger.info(f"  {var_name} from .env: '{val}'")
        
        # 5. API Key (Optional)
        api_key_env = os.getenv("AZURE_AI_AGENT_API_KEY")
        if api_key_env:
            logger.info("AZURE_AI_AGENT_API_KEY is set in .env.")
            os.environ["AZURE_AI_AGENT_API_KEY"] = api_key_env
        else:
            logger.info("AZURE_AI_AGENT_API_KEY is not set in .env. Relying on DefaultAzureCredential.")

        logger.info(f"--- Effective configuration values intended for AzureAIAgentSettings (from environment) ---")
        logger.info(f"  AZURE_AI_AGENT_ENDPOINT (if set): {os.getenv('AZURE_AI_AGENT_ENDPOINT', 'Not set, relying on SDK discovery')}")
        logger.info(f"  AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME: {os.getenv('AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME')}")
        logger.info(f"  AZURE_AI_AGENT_API_VERSION: {os.getenv('AZURE_AI_AGENT_API_VERSION')}")
        logger.info(f"  AZURE_AI_AGENT_PROJECT_NAME: {os.getenv('AZURE_AI_AGENT_PROJECT_NAME')}")
        logger.info(f"  AZURE_AI_AGENT_PROJECT_HUB_NAME: {os.getenv('AZURE_AI_AGENT_PROJECT_HUB_NAME')}")
        
        settings = AzureAIAgentSettings()
        
        logger.info(f"--- AzureAIAgentSettings object initialized with ---")
        logger.info(f"  settings.endpoint: '{settings.endpoint}' << WATCH THIS VALUE CLOSELY")
        logger.info(f"  settings.model_deployment_name: '{settings.model_deployment_name}'")
        logger.info(f"  settings.api_version: '{settings.api_version}'")
        logger.info(f"  (Intended for SDK based on env) Project Name: '{os.getenv('AZURE_AI_AGENT_PROJECT_NAME')}'")
        logger.info(f"  (Intended for SDK based on env) Hub Name: '{os.getenv('AZURE_AI_AGENT_PROJECT_HUB_NAME')}'")
        
        try:
            key_value = getattr(settings, 'api_key', None) 
            if key_value is not None:
                 logger.info(f"  settings.api_key: [loaded/set]")
            else:
                 logger.info(f"  settings.api_key: [None or not set] (expected if using AAD via DefaultAzureCredential)")
        except AttributeError: 
            logger.info(f"  settings.api_key: [attribute not found on settings object] (expected if not using API key auth)")

        # If endpoint is None after SDK init, it means discovery likely failed or is not supported this way
        if settings.endpoint is None:
            logger.error("CRITICAL FAILURE: AzureAIAgentSettings did not resolve an endpoint. SDK discovery might have failed or is not supported without an explicit endpoint for this target. Ensure all AZURE_AI_AGENT_PROJECT_* variables are correctly set in .env.")
            sys.exit(1)
        elif "ai.azure.com" not in settings.endpoint: # If it resolved to something else unexpected
            logger.warning(f"WARNING: AzureAIAgentSettings resolved endpoint to '{settings.endpoint}', which is not the expected 'ai.azure.com' base. This might lead to incorrect targeting.")


        async with DefaultAzureCredential(exclude_interactive_browser_credential=False) as credential:
            try:
                scope_to_test = "https://management.azure.com/.default" 
                logger.info(f"Attempting to get test token with DefaultAzureCredential for scope: {scope_to_test}...")
                token_info = await credential.get_token(scope_to_test)
                logger.info(f"✓ DefaultAzureCredential acquired a test token successfully (expires on: {datetime.fromtimestamp(token_info.expires_on, timezone.utc).isoformat()}).")
            except Exception as auth_e:
                logger.error(f"Failed to acquire test token with DefaultAzureCredential: {auth_e}", exc_info=True)
                logger.error("Ensure your environment is correctly authenticated (e.g., 'az login' or valid Service Principal env vars: AZURE_CLIENT_ID, AZURE_TENANT_ID, AZURE_CLIENT_SECRET).")
                sys.exit(1)
            
            all_deployed_agents_info = await deploy_all_agents(settings, credential)
            
            deployment_info = {
                "deployment_time": datetime.now(timezone.utc).isoformat(),
                "deployment_target": "azure_ai_project_agent_service",
                "target_endpoint_config_from_env": os.getenv('AZURE_AI_AGENT_ENDPOINT', 'Not set in env for SDK discovery'),
                "target_api_version_config_from_env": os.getenv('AZURE_AI_AGENT_API_VERSION'),
                "llm_model_deployment_config_from_env": os.getenv('AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME'),
                "project_context_config_from_env": {
                    "name": os.getenv('AZURE_AI_AGENT_PROJECT_NAME'),
                    "hub": os.getenv('AZURE_AI_AGENT_PROJECT_HUB_NAME'),
                    "resource_group": os.getenv('AZURE_AI_AGENT_PROJECT_RESOURCE_GROUP'),
                    "subscription_id": os.getenv('AZURE_AI_AGENT_PROJECT_SUBSCRIPTION_ID')
                },
                "sdk_resolved_settings": { 
                    "endpoint": settings.endpoint,
                    "api_version": settings.api_version,
                    "model_deployment_name": settings.model_deployment_name,
                },
                "total_agents_configured": len(AGENTS_TO_DEPLOY_CONFIG),
                "total_agents_deployed_successfully": len(all_deployed_agents_info),
                "deployed_agents": {name: agent_id for name, agent_id in all_deployed_agents_info},
            }
            
            deployment_file = os.path.join(backend_dir, "deployment_configs", "ai_project_agents_deployment.json")
            os.makedirs(os.path.dirname(deployment_file), exist_ok=True)
            
            with open(deployment_file, "w") as f:
                json.dump(deployment_info, f, indent=2)
            
            logger.info(f"\n===== Deployment Process Finished =====")
            if all_deployed_agents_info:
                 logger.info(f"✓ {len(all_deployed_agents_info)} out of {len(AGENTS_TO_DEPLOY_CONFIG)} agents were processed (check logs for individual success/failure).")
            else:
                 logger.warning("No agents appear to have been successfully deployed or updated.")
            logger.info(f"✓ Deployment info saved to: {os.path.relpath(deployment_file, current_dir)}")
            logger.info(f"\nIMPORTANT: Review logs above for specific agent deployment statuses.")
            logger.info(f"Verify agents in Azure AI Studio under Project: '{os.getenv('AZURE_AI_AGENT_PROJECT_NAME')}' in Hub: '{os.getenv('AZURE_AI_AGENT_PROJECT_HUB_NAME')}'.")
            
    except Exception as e:
        logger.error(f"Deployment failed critically in main: {e}", exc_info=True)
        logger.error("\nTroubleshooting:")
        logger.error("1. .ENV: Ensure AZURE_AI_AGENT_ENDPOINT is either NOT SET (for SDK discovery) OR set to the correct base URL for AI Studio agents (e.g. 'https://ai.azure.com' or a more specific path like 'https://ai.azure.com/api/eastus/agents/v1.0' if SDK doesn't build it).")
        logger.error("2. .ENV: Ensure AZURE_AI_AGENT_API_VERSION in .env is '2024-12-01-preview'.")
        logger.error("3. .ENV: Ensure AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME is correct.")
        logger.error("4. .ENV: CRITICAL - Ensure AZURE_AI_AGENT_PROJECT_NAME, _HUB_NAME, _RESOURCE_GROUP, _SUBSCRIPTION_ID are correctly set in .env with these exact AZURE_AI_AGENT_ prefixed names.")
        logger.error("5. AUTH: Ensure Service Principal (AZURE_CLIENT_ID, etc.) is valid and has permissions (e.g., 'AzureML Data Scientist' or agent-specific roles) on the AI Project/Hub.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())