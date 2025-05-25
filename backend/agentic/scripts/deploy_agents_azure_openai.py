#!/usr/bin/env python3
"""
Deploy StratOS agents to Azure AI Agent Service using an Azure OpenAI endpoint.
This ensures agents leverage the Assistants API capabilities provided by the specified Azure OpenAI resource.

CRITICAL: The key is using the correct Azure OpenAI resource endpoint.
"""

import asyncio
import os
import sys
import json
import logging
from datetime import datetime
from dotenv import load_dotenv

# Add parent directories to path
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
# project_root = os.path.dirname(backend_dir) # Not used in this script snippet
sys.path.insert(0, backend_dir)

# Configure logging first
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables from .env file in the backend directory
env_path = os.path.join(backend_dir, '.env')
load_dotenv(env_path)
logger.info(f"Attempting to load .env file from: {env_path}")
if os.path.exists(env_path):
    logger.info(".env file loaded successfully.")
else:
    logger.warning(".env file not found at the specified path. Relying on pre-set environment variables.")

# Import required modules
try:
    from azure.identity.aio import DefaultAzureCredential
    from semantic_kernel.agents import AzureAIAgent, AzureAIAgentSettings
except ImportError as e:
    logger.error(f"Error importing required modules: {e}")
    logger.error("Please ensure 'semantic-kernel[azure]' and 'azure-identity' are installed.")
    logger.error("Consider checking your Semantic Kernel version and import paths if issues persist.")
    sys.exit(1)

async def deploy_agent(
    agent_name: str,
    agent_instructions: str,
    agent_description: str,
    settings: AzureAIAgentSettings,
    credential
) -> tuple[AzureAIAgent | None, str | None]:
    """
    Deploys an agent using the configured Azure AI Agent Service (via Azure OpenAI endpoint).
    """
    agent_service_client = None
    try:
        # The AzureAIAgent.create_client is a context manager
        async with AzureAIAgent.create_client(credential=credential, settings=settings) as client:
            agent_service_client = client
            logger.info(f"Deploying agent: {agent_name} using endpoint: {settings.endpoint}")
            
            # Check if agent already exists
            existing_agent_definition = None
            try:
                all_agents_response = await agent_service_client.agents.list_agents()
                # Handle both direct async iteration and .data attribute patterns
                agents_iterable = all_agents_response.data if hasattr(all_agents_response, 'data') else all_agents_response
                async for agent_def in agents_iterable:
                    if agent_def.name == agent_name:
                        existing_agent_definition = agent_def
                        logger.info(f"Agent '{agent_name}' already exists with ID: {existing_agent_definition.id}")
                        break
            except Exception as e:
                logger.warning(f"Could not list existing agents: {e}. Creating new agent.")

            if existing_agent_definition:
                agent_definition = existing_agent_definition
                logger.info(f"Using existing agent definition for '{agent_name}'.")
            else:
                # Create new agent
                logger.info(f"Creating new agent '{agent_name}' with model '{settings.model_deployment_name}'.")
                agent_definition = await agent_service_client.agents.create_agent(
                    model=settings.model_deployment_name,
                    name=agent_name,
                    instructions=agent_instructions,
                    description=agent_description
                )
                logger.info(f"Agent '{agent_name}' created successfully with ID: {agent_definition.id}")

            # Create Semantic Kernel agent instance
            sk_agent = AzureAIAgent(
                client=agent_service_client,
                definition=agent_definition,
            )
            
            return sk_agent, agent_definition.id

    except Exception as e:
        logger.error(f"Failed to deploy agent '{agent_name}': {e}")
        raise

async def deploy_all_agents(settings, credential):
    """Deploy all StratOS agents."""
    deployed_agents_info = []
    
    # Strategic Foundation & Insights System
    logger.info("\n=== Deploying Strategic Foundation & Insights System ===")
    
    agents_to_deploy = [
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
        # Analysis & Intelligence System
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
        # Planning & Execution System
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
    
    for agent_config in agents_to_deploy:
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
        except Exception as e:
            logger.error(f"Skipping agent '{agent_config['name']}' due to deployment error: {e}")
            continue
    
    return deployed_agents_info, len(agents_to_deploy)

async def main():
    """Main deployment function"""
    logger.info("===== StratOS Agent Deployment to Azure AI Agent Service (via Azure OpenAI) =====")
    logger.info(f"Deployment started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # --- CRITICAL ENVIRONMENT VARIABLES TO SET ---
        # 1. AZURE_AI_AGENT_ENDPOINT:
        #    Set to your Azure OpenAI resource endpoint
        os.environ["AZURE_AI_AGENT_ENDPOINT"] = "https://sk-multi-agent-openai.openai.azure.com/"

        # 2. AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME:
        #    CRITICAL: Set to the actual deployment name in your Azure OpenAI resource
        #    Based on our discovery, you have "gpt-35-turbo" deployed
        os.environ["AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME"] = "gpt-35-turbo"
        
        # 3. AZURE_AI_AGENT_API_KEY: (Optional - try without it first if using DefaultAzureCredential)
        #    Using the API key from .env if available
        if os.getenv("AZURE_OPENAI_API_KEY"):
            os.environ["AZURE_AI_AGENT_API_KEY"] = os.getenv("AZURE_OPENAI_API_KEY")

        # 4. AZURE_AI_AGENT_API_VERSION:
        os.environ["AZURE_AI_AGENT_API_VERSION"] = "2024-05-01-preview"

        # Contextual Azure AI Project information
        os.environ["AZURE_AI_AGENT_PROJECT_RESOURCE_GROUP"] = os.getenv("AZURE_RESOURCE_GROUP", "semantic-kernel-multi-agent-rg")
        os.environ["AZURE_AI_AGENT_PROJECT_SUBSCRIPTION_ID"] = os.getenv("AZURE_SUBSCRIPTION_ID", "514bd6d3-2c02-45c6-a86f-29cf262a379a")
        os.environ["AZURE_AI_AGENT_PROJECT_NAME"] = os.getenv("AZURE_AI_PROJECT_NAME", "sk-multi-agent-project")

        logger.info(f"Using Azure OpenAI endpoint: {os.getenv('AZURE_AI_AGENT_ENDPOINT')}")
        logger.info(f"Using Model deployment: {os.getenv('AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME')}")
        
        if os.getenv("AZURE_AI_AGENT_API_KEY"):
            logger.info("Using Azure OpenAI API Key for authentication.")
        else:
            logger.info("Using DefaultAzureCredential (e.g., 'az login') for authentication.")

        # Create settings instance
        settings = AzureAIAgentSettings()
        
        # Use DefaultAzureCredential
        async with DefaultAzureCredential() as credential:
            logger.info("✓ Authenticated with Azure")
            
            # Deploy all agents
            all_deployed_agents_info, total_agents_count = await deploy_all_agents(settings, credential)
            
            if not all_deployed_agents_info:
                logger.warning("No agents were successfully deployed. Please check logs for errors.")
                sys.exit(1)

            # Save deployment information
            deployment_info = {
                "deployment_time": datetime.now().isoformat(),
                "deployment_type": "azure_openai_assistant_via_sk",
                "azure_openai_endpoint": os.getenv("AZURE_AI_AGENT_ENDPOINT"),
                "model_deployment": os.getenv("AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME"),
                "project_name_context": os.getenv("AZURE_AI_PROJECT_NAME"),
                "resource_group_context": os.getenv("AZURE_RESOURCE_GROUP"),
                "total_agents_attempted": total_agents_count,
                "total_agents_deployed": len(all_deployed_agents_info),
                "deployed_agents": {name: agent_id for name, agent_id in all_deployed_agents_info},
                "note": "Agents deployed as Azure OpenAI Assistants using Semantic Kernel."
            }
            
            deployment_file = os.path.join(backend_dir, "deployment_configs", "azure_openai_assistants_deployment.json")
            os.makedirs(os.path.dirname(deployment_file), exist_ok=True)
            
            with open(deployment_file, "w") as f:
                json.dump(deployment_info, f, indent=2)
            
            logger.info(f"\n===== Deployment Complete =====")
            logger.info(f"✓ Successfully deployed {len(all_deployed_agents_info)} agents to Azure OpenAI Assistants")
            logger.info(f"✓ Deployment info saved to: {os.path.relpath(deployment_file, current_dir)}")
            logger.info(f"\nIMPORTANT: These agents are Azure OpenAI Assistants.")
            logger.info(f"You can manage them via Azure OpenAI Studio or the Assistants API.")
            
    except Exception as e:
        logger.error(f"Deployment failed: {e}")
        import traceback
        traceback.print_exc()
        logger.error("\nTroubleshooting:")
        logger.error("1. Ensure AZURE_AI_AGENT_ENDPOINT is the correct Azure OpenAI resource endpoint.")
        logger.error("2. Verify the model deployment name matches what's in your Azure OpenAI resource.")
        logger.error("3. Check that you have the 'Cognitive Services OpenAI User' role on the resource.")
        logger.error("4. Ensure your Azure OpenAI resource has the Assistants feature enabled.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())