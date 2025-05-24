#!/usr/bin/env python3
"""
Deploy StratOS agents to Azure AI Agent Service using the CORRECT approach.
Based on the working reference implementation provided.
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
project_root = os.path.dirname(backend_dir)
sys.path.insert(0, backend_dir)

# Load environment variables
load_dotenv(os.path.join(backend_dir, '.env'))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import required modules
try:
    from azure.identity.aio import DefaultAzureCredential
    from semantic_kernel.agents import AzureAIAgent, AzureAIAgentSettings
except ImportError as e:
    logger.error(f"Error importing required modules: {e}")
    logger.error("Please install required packages:")
    logger.error("pip install 'semantic-kernel[azure]' azure-identity python-dotenv")
    sys.exit(1)

async def deploy_agent(
    agent_name: str,
    agent_instructions: str,
    agent_description: str,
    settings: AzureAIAgentSettings,
    credential
) -> tuple[AzureAIAgent, str]:
    """
    Deploys or updates an agent in Azure AI Agent Service and returns the agent and its ID.
    """
    async with AzureAIAgent.create_client(credential=credential, settings=settings) as agent_service_client:
        logger.info(f"Attempting to create/update agent: {agent_name}")
        try:
            # Check if agent already exists
            existing_agent_definition = None
            try:
                all_agents = await agent_service_client.agents.list_agents()
                for agent_def in all_agents.data:
                    if agent_def.name == agent_name:
                        existing_agent_definition = agent_def
                        logger.info(f"Agent '{agent_name}' already exists with ID: {existing_agent_definition.id}")
                        break
            except Exception as e:
                logger.warning(f"Could not list existing agents: {e}")

            if existing_agent_definition:
                # Use existing agent
                agent_definition = existing_agent_definition
                logger.info(f"Using existing agent definition for '{agent_name}'.")
            else:
                # Create new agent
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
            logger.info(f"Semantic Kernel AzureAIAgent instance initialized for: {sk_agent.name}")
            
            return sk_agent, agent_definition.id

        except Exception as e:
            logger.error(f"Failed to deploy or initialize agent '{agent_name}': {e}")
            raise

async def deploy_strategic_foundation_agents(settings, credential):
    """Deploy Strategic Foundation & Insights System agents"""
    agents = []
    
    logger.info("\n=== Deploying Strategic Foundation & Insights System ===")
    
    # Strategic Context Router
    agent, agent_id = await deploy_agent(
        agent_name="StrategicContextRouter",
        agent_instructions=(
            "You are the Strategic Context Router for StratOS. Your role is to analyze incoming requests and route them to "
            "the appropriate specialized agent within the Strategic Foundation & Insights System. You manage: "
            "1) CEO Log Agent for subjective inputs and voice transcriptions, "
            "2) North Star Agent for vision, values, and strategic goals, "
            "3) Memory & Recall Agent for context retrieval and pattern recognition, "
            "4) Preference Learning Agent for personalization. "
            "Analyze each request carefully and determine which agent is best suited to handle it."
        ),
        agent_description="Routes requests within the Strategic Foundation system",
        settings=settings,
        credential=credential
    )
    agents.append(("StrategicContextRouter", agent_id))
    
    # CEO Log Agent
    agent, agent_id = await deploy_agent(
        agent_name="CEOLogAgent",
        agent_instructions=(
            "You are the CEO Log Agent for StratOS. You specialize in processing subjective inputs from the CEO including "
            "voice transcriptions, thoughts, observations, and strategic reflections. Your capabilities include: "
            "1) Processing voice-to-text transcriptions, "
            "2) Generating relevant tags for entries, "
            "3) Creating concise summaries, "
            "4) Extracting strategic insights from subjective content. "
            "When processing entries, focus on identifying strategic themes, potential risks or opportunities, "
            "and connections to the organization's North Star."
        ),
        agent_description="Manages CEO's subjective inputs, voice transcriptions, and insights",
        settings=settings,
        credential=credential
    )
    agents.append(("CEOLogAgent", agent_id))
    
    # North Star Agent
    agent, agent_id = await deploy_agent(
        agent_name="NorthStarAgent",
        agent_instructions=(
            "You are the North Star Agent for StratOS. You are the guardian of the organization's strategic foundation "
            "including Purpose, Vision, Values, and Strategic Goals. Your responsibilities include: "
            "1) Maintaining consistency across all strategic elements, "
            "2) Managing hierarchical goal structures with parent-child relationships, "
            "3) Validating goal alignment with organizational values, "
            "4) Providing guidance on strategic direction. "
            "When asked about strategic elements, provide clear, inspiring responses that reinforce "
            "the organization's direction while ensuring practical applicability."
        ),
        agent_description="Manages organizational purpose, vision, values, and strategic goals",
        settings=settings,
        credential=credential
    )
    agents.append(("NorthStarAgent", agent_id))
    
    # Memory & Recall Agent
    agent, agent_id = await deploy_agent(
        agent_name="MemoryRecallAgent",
        agent_instructions=(
            "You are the Memory & Recall Agent for StratOS. You specialize in retrieving relevant strategic context "
            "and identifying patterns across the organization's history. Your capabilities include: "
            "1) Semantic search across all strategic documents and logs, "
            "2) Pattern recognition in historical data, "
            "3) Context assembly for decision-making, "
            "4) Trend identification over time. "
            "When retrieving information, prioritize relevance and recency while maintaining awareness of long-term patterns. "
            "Provide synthesized insights rather than raw data dumps."
        ),
        agent_description="Provides strategic context retrieval and pattern recognition",
        settings=settings,
        credential=credential
    )
    agents.append(("MemoryRecallAgent", agent_id))
    
    # Preference Learning Agent
    agent, agent_id = await deploy_agent(
        agent_name="PreferenceLearningAgent",
        agent_instructions=(
            "You are the Preference Learning Agent for StratOS. You observe user interactions to learn preferences "
            "and personalize the experience. Your focus areas include: "
            "1) Tracking accepted vs rejected suggestions, "
            "2) Learning communication style preferences, "
            "3) Understanding decision-making patterns, "
            "4) Adapting responses based on user history. "
            "Always respect user privacy and be transparent about personalization. "
            "Your goal is to make the system more intuitive and aligned with each user's working style."
        ),
        agent_description="Learns and applies user preferences for personalization",
        settings=settings,
        credential=credential
    )
    agents.append(("PreferenceLearningAgent", agent_id))
    
    return agents

async def deploy_analysis_intelligence_agents(settings, credential):
    """Deploy Analysis & Intelligence System agents"""
    agents = []
    
    logger.info("\n=== Deploying Analysis & Intelligence System ===")
    
    # Analysis Orchestrator
    agent, agent_id = await deploy_agent(
        agent_name="AnalysisOrchestrator",
        agent_instructions=(
            "You are the Analysis Orchestrator for StratOS. You coordinate all analytical activities within "
            "the Analysis & Intelligence System. You manage: "
            "1) SWOT/TOWS Agent for strategic analysis, "
            "2) Risk/Opportunity Agent for threat and opportunity detection, "
            "3) S+O Linkage Agent for connecting subjective and objective data. "
            "For complex analyses, you can coordinate multiple agents to provide comprehensive insights. "
            "Always ensure analyses are actionable and tied to strategic objectives."
        ),
        agent_description="Orchestrates complex analysis workflows",
        settings=settings,
        credential=credential
    )
    agents.append(("AnalysisOrchestrator", agent_id))
    
    # SWOT/TOWS Agent
    agent, agent_id = await deploy_agent(
        agent_name="SWOTTOWSAgent",
        agent_instructions=(
            "You are the SWOT/TOWS Agent for StratOS. You specialize in strategic analysis using SWOT "
            "(Strengths, Weaknesses, Opportunities, Threats) and TOWS matrix methodologies. Your process includes: "
            "1) Guiding users through comprehensive SWOT analysis, "
            "2) Maintaining session state for multi-step analysis, "
            "3) Generating TOWS strategies by combining SWOT elements, "
            "4) Providing contextual prompts based on industry and organizational data. "
            "Ensure all analyses are specific, measurable, and actionable rather than generic."
        ),
        agent_description="Performs SWOT analysis and generates TOWS strategies",
        settings=settings,
        credential=credential
    )
    agents.append(("SWOTTOWSAgent", agent_id))
    
    # Risk/Opportunity Agent
    agent, agent_id = await deploy_agent(
        agent_name="RiskOpportunityAgent",
        agent_instructions=(
            "You are the Risk/Opportunity Detection Agent for StratOS. You continuously monitor for potential risks "
            "and opportunities across all organizational data. Your capabilities include: "
            "1) Anomaly detection in patterns and metrics, "
            "2) Risk assessment with severity levels, "
            "3) Opportunity identification with potential impact, "
            "4) Alert generation with recommended actions. "
            "Prioritize based on potential impact and likelihood. "
            "Always provide actionable recommendations along with your assessments."
        ),
        agent_description="Detects and assesses risks and opportunities",
        settings=settings,
        credential=credential
    )
    agents.append(("RiskOpportunityAgent", agent_id))
    
    # S+O Linkage Agent
    agent, agent_id = await deploy_agent(
        agent_name="SOLinkageAgent",
        agent_instructions=(
            "You are the S+O Linkage Agent for StratOS. You specialize in discovering connections between "
            "subjective inputs (CEO thoughts, observations) and objective data (KPIs, metrics, market data). "
            "Your process includes: "
            "1) Pattern matching between qualitative and quantitative information, "
            "2) Correlation analysis to find meaningful relationships, "
            "3) Insight generation that bridges intuition and data, "
            "4) Validation of hunches with empirical evidence. "
            "Help leaders see how their instincts align with or diverge from the data."
        ),
        agent_description="Links subjective insights with objective data",
        settings=settings,
        credential=credential
    )
    agents.append(("SOLinkageAgent", agent_id))
    
    return agents

async def deploy_planning_execution_agents(settings, credential):
    """Deploy Planning & Execution System agents"""
    agents = []
    
    logger.info("\n=== Deploying Planning & Execution System ===")
    
    # Planning Coordinator
    agent, agent_id = await deploy_agent(
        agent_name="PlanningCoordinator",
        agent_instructions=(
            "You are the Planning Coordinator for StratOS. You orchestrate all planning and execution activities. "
            "You manage: "
            "1) Initiative Generation Agent for creating strategic initiatives, "
            "2) Resource Optimization Agent for allocation decisions, "
            "3) Canvas Visualization Agent for visual planning, "
            "4) Alignment Scoring Agent for strategic fit assessment, "
            "5) Action Planning Agent for detailed execution plans. "
            "Ensure all plans are realistic, resourced, and aligned with strategic objectives. "
            "Coordinate multiple agents for comprehensive planning."
        ),
        agent_description="Coordinates planning and execution activities",
        settings=settings,
        credential=credential
    )
    agents.append(("PlanningCoordinator", agent_id))
    
    # Initiative Generation Agent
    agent, agent_id = await deploy_agent(
        agent_name="InitiativeGenerationAgent",
        agent_instructions=(
            "You are the Initiative Generation Agent for StratOS. You create strategic initiatives that bridge "
            "the gap between high-level strategy and executable actions. Your process includes: "
            "1) Analyzing strategic goals and current state, "
            "2) Generating initiative proposals with clear objectives, "
            "3) Defining measurable success metrics, "
            "4) Creating milestone-based timelines. "
            "Each initiative should include ownership, resources required, and risk mitigation strategies. "
            "Focus on initiatives that create maximum strategic impact."
        ),
        agent_description="Creates strategic initiatives and action plans",
        settings=settings,
        credential=credential
    )
    agents.append(("InitiativeGenerationAgent", agent_id))
    
    # Resource Optimization Agent
    agent, agent_id = await deploy_agent(
        agent_name="ResourceOptimizationAgent",
        agent_instructions=(
            "You are the Resource Optimization Agent for StratOS. You ensure optimal allocation of resources "
            "(people, budget, time) across all strategic initiatives. Your capabilities include: "
            "1) Resource capacity analysis, "
            "2) Allocation optimization based on strategic priorities, "
            "3) Cost-benefit analysis for resource decisions, "
            "4) Utilization tracking and recommendations. "
            "Consider both efficiency and effectiveness. "
            "Help leaders make tough trade-offs while maintaining strategic focus."
        ),
        agent_description="Optimizes resource allocation across initiatives",
        settings=settings,
        credential=credential
    )
    agents.append(("ResourceOptimizationAgent", agent_id))
    
    # Canvas Visualization Agent
    agent, agent_id = await deploy_agent(
        agent_name="CanvasVisualizationAgent",
        agent_instructions=(
            "You are the Canvas Visualization Agent for StratOS. You help users create and manage visual "
            "representations of their strategy using the Strategic Canvas. Your capabilities include: "
            "1) Structuring text into visual nodes, "
            "2) Suggesting meaningful connections between elements, "
            "3) Identifying themes and patterns in canvas layouts, "
            "4) Processing voice commands for canvas manipulation. "
            "Make strategic planning visual and intuitive. "
            "Help users see the big picture while maintaining important details."
        ),
        agent_description="Manages visual strategic planning on canvas",
        settings=settings,
        credential=credential
    )
    agents.append(("CanvasVisualizationAgent", agent_id))
    
    # Alignment Scoring Agent
    agent, agent_id = await deploy_agent(
        agent_name="AlignmentScoringAgent",
        agent_instructions=(
            "You are the Alignment Scoring Agent for StratOS. You evaluate how well initiatives and actions "
            "align with strategic objectives. Your assessment includes: "
            "1) Scoring initiatives against strategic goals, "
            "2) Identifying alignment gaps and conflicts, "
            "3) Recommending adjustments for better fit, "
            "4) Tracking alignment trends over time. "
            "Provide quantitative scores with qualitative explanations. "
            "Help ensure all efforts contribute to strategic success."
        ),
        agent_description="Assesses strategic alignment of initiatives",
        settings=settings,
        credential=credential
    )
    agents.append(("AlignmentScoringAgent", agent_id))
    
    # Action Planning Agent
    agent, agent_id = await deploy_agent(
        agent_name="ActionPlanningAgent",
        agent_instructions=(
            "You are the Action Planning Agent for StratOS. You transform strategic initiatives into detailed, "
            "executable action plans. Your planning includes: "
            "1) Task breakdown structures, "
            "2) Timeline creation with dependencies, "
            "3) Responsibility assignment (RACI), "
            "4) Progress tracking mechanisms. "
            "Ensure plans are specific enough to execute but flexible enough to adapt. "
            "Focus on the critical path and early wins to build momentum."
        ),
        agent_description="Creates detailed execution plans for initiatives",
        settings=settings,
        credential=credential
    )
    agents.append(("ActionPlanningAgent", agent_id))
    
    return agents

async def main():
    """Main function to deploy all StratOS agents"""
    logger.info("===== StratOS Agent Deployment to Azure AI Agent Service =====")
    logger.info(f"Deployment started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Map our environment variables to what AzureAIAgentSettings expects
        # AzureAIAgentSettings uses: AZURE_AI_AGENT_ENDPOINT, AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME, AZURE_AI_AGENT_API_VERSION
        
        # Use the Azure OpenAI endpoint for the agent endpoint
        os.environ["AZURE_AI_AGENT_ENDPOINT"] = os.getenv("AZURE_OPENAI_ENDPOINT", "")
        os.environ["AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME"] = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "")
        os.environ["AZURE_AI_AGENT_API_VERSION"] = os.getenv("AZURE_AI_AGENT_API_VERSION", "2024-05-01-preview")
        
        # Check for required settings
        if not (os.getenv("AZURE_AI_AGENT_ENDPOINT") and 
                os.getenv("AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME")):
            logger.error("Critical Azure AI Agent settings are missing. Please ensure these environment variables are set:")
            logger.error("- AZURE_OPENAI_ENDPOINT (or AZURE_AI_AGENT_ENDPOINT)")
            logger.error("- AZURE_OPENAI_DEPLOYMENT_NAME (or AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME)")
            sys.exit(1)
        
        # Create settings instance
        settings = AzureAIAgentSettings()
        
        logger.info(f"Deploying agents to endpoint: '{settings.endpoint}'")
        logger.info(f"Using model deployment: '{settings.model_deployment_name}'")
        logger.info(f"API Version: '{settings.api_version}'")
        
        # Use DefaultAzureCredential
        async with DefaultAzureCredential() as credential:
            logger.info("✓ Authenticated with Azure")
            
            all_agents = []
            
            # Deploy all three systems
            strategic_agents = await deploy_strategic_foundation_agents(settings, credential)
            all_agents.extend(strategic_agents)
            
            analysis_agents = await deploy_analysis_intelligence_agents(settings, credential)
            all_agents.extend(analysis_agents)
            
            planning_agents = await deploy_planning_execution_agents(settings, credential)
            all_agents.extend(planning_agents)
            
            # Save deployment information
            deployment_info = {
                "deployment_time": datetime.now().isoformat(),
                "deployment_type": "azure_ai_agent_service",
                "endpoint": settings.endpoint,
                "model_deployment": settings.model_deployment_name,
                "api_version": settings.api_version,
                "total_agents": len(all_agents),
                "agents": {
                    "strategic_foundation": {
                        name: agent_id for name, agent_id in strategic_agents
                    },
                    "analysis_intelligence": {
                        name: agent_id for name, agent_id in analysis_agents
                    },
                    "planning_execution": {
                        name: agent_id for name, agent_id in planning_agents
                    }
                }
            }
            
            # Save to file
            deployment_file = os.path.join(backend_dir, "deployment_configs", "agent_service_deployment.json")
            os.makedirs(os.path.dirname(deployment_file), exist_ok=True)
            
            with open(deployment_file, "w") as f:
                json.dump(deployment_info, f, indent=2)
            
            logger.info(f"\n===== Deployment Complete =====")
            logger.info(f"✓ Successfully deployed {len(all_agents)} agents to Azure AI Agent Service")
            logger.info(f"✓ Deployment info saved to: deployment_configs/agent_service_deployment.json")
            logger.info(f"\nNext steps:")
            logger.info("1. Test agents using interaction scripts")
            logger.info("2. Update FastAPI backend to use deployed agent IDs")
            logger.info("3. Configure Connected Agents for multi-agent orchestration")
            
    except Exception as e:
        logger.error(f"An error occurred during deployment: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())