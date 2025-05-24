#!/usr/bin/env python3
"""
Deploy StratOS agents to Azure AI Foundry Agent Service using the Azure AI Projects SDK.
Based on the working implementation from semantic_kernel_multi_agent project.
"""

import asyncio
import os
import sys
import json
from datetime import datetime
from dotenv import load_dotenv

# Add parent directories to path
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
project_root = os.path.dirname(backend_dir)
sys.path.insert(0, backend_dir)

# Load environment variables
load_dotenv(os.path.join(backend_dir, '.env'))

# Import Azure AI SDK
try:
    from azure.ai.projects import AIProjectClient
    from azure.identity import DefaultAzureCredential
except ImportError:
    print("Error: Azure AI Projects SDK not installed.")
    print("Please install it with: pip install azure-ai-projects azure-identity")
    sys.exit(1)

# Get configuration from environment
AZURE_SUBSCRIPTION_ID = os.getenv('AZURE_SUBSCRIPTION_ID')
AZURE_RESOURCE_GROUP = os.getenv('AZURE_RESOURCE_GROUP')
AZURE_AI_HUB_NAME = os.getenv('AZURE_AI_HUB_NAME')
AZURE_AI_PROJECT_NAME = os.getenv('AZURE_AI_PROJECT_NAME')
AZURE_AI_PROJECT_HOST = os.getenv('AZURE_AI_PROJECT_HOST')
AZURE_OPENAI_DEPLOYMENT_NAME = os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME')

async def create_client():
    """Create an Azure AI Project client"""
    try:
        # Construct connection string
        connection_string = f"{AZURE_AI_PROJECT_HOST};{AZURE_SUBSCRIPTION_ID};{AZURE_RESOURCE_GROUP};{AZURE_AI_HUB_NAME}/{AZURE_AI_PROJECT_NAME}"
        
        print(f"Connecting to Azure AI Foundry...")
        print(f"  Hub: {AZURE_AI_HUB_NAME}")
        print(f"  Project: {AZURE_AI_PROJECT_NAME}")
        
        credential = DefaultAzureCredential()
        client = AIProjectClient.from_connection_string(
            conn_str=connection_string,
            credential=credential
        )
        
        return client
    except Exception as e:
        print(f"Error creating client: {str(e)}")
        raise

async def deploy_strategic_foundation_agents(client):
    """Deploy Strategic Foundation & Insights System agents"""
    agents = []
    
    print("\n=== Deploying Strategic Foundation & Insights System ===")
    
    # Strategic Context Router
    print("Deploying Strategic Context Router...")
    router = await client.agents.create_agent(
        model=AZURE_OPENAI_DEPLOYMENT_NAME,
        name="StrategicContextRouter",
        instructions=(
            "You are the Strategic Context Router for StratOS. Your role is to analyze incoming requests and route them to "
            "the appropriate specialized agent within the Strategic Foundation & Insights System. You manage: "
            "1) CEO Log Agent for subjective inputs and voice transcriptions, "
            "2) North Star Agent for vision, values, and strategic goals, "
            "3) Memory & Recall Agent for context retrieval and pattern recognition, "
            "4) Preference Learning Agent for personalization. "
            "Analyze each request carefully and determine which agent is best suited to handle it."
        )
    )
    agents.append(("StrategicContextRouter", router.id))
    print(f"  ✓ Strategic Context Router deployed: {router.id}")
    
    # CEO Log Agent
    print("Deploying CEO Log Agent...")
    ceo_log = await client.agents.create_agent(
        model=AZURE_OPENAI_DEPLOYMENT_NAME,
        name="CEOLogAgent",
        instructions=(
            "You are the CEO Log Agent for StratOS. You specialize in processing subjective inputs from the CEO including "
            "voice transcriptions, thoughts, observations, and strategic reflections. Your capabilities include: "
            "1) Processing voice-to-text transcriptions, "
            "2) Generating relevant tags for entries, "
            "3) Creating concise summaries, "
            "4) Extracting strategic insights from subjective content. "
            "When processing entries, focus on identifying strategic themes, potential risks or opportunities, "
            "and connections to the organization's North Star."
        )
    )
    agents.append(("CEOLogAgent", ceo_log.id))
    print(f"  ✓ CEO Log Agent deployed: {ceo_log.id}")
    
    # North Star Agent
    print("Deploying North Star Agent...")
    north_star = await client.agents.create_agent(
        model=AZURE_OPENAI_DEPLOYMENT_NAME,
        name="NorthStarAgent",
        instructions=(
            "You are the North Star Agent for StratOS. You are the guardian of the organization's strategic foundation "
            "including Purpose, Vision, Values, and Strategic Goals. Your responsibilities include: "
            "1) Maintaining consistency across all strategic elements, "
            "2) Managing hierarchical goal structures with parent-child relationships, "
            "3) Validating goal alignment with organizational values, "
            "4) Providing guidance on strategic direction. "
            "When asked about strategic elements, provide clear, inspiring responses that reinforce "
            "the organization's direction while ensuring practical applicability."
        )
    )
    agents.append(("NorthStarAgent", north_star.id))
    print(f"  ✓ North Star Agent deployed: {north_star.id}")
    
    # Memory & Recall Agent
    print("Deploying Memory & Recall Agent...")
    memory_recall = await client.agents.create_agent(
        model=AZURE_OPENAI_DEPLOYMENT_NAME,
        name="MemoryRecallAgent",
        instructions=(
            "You are the Memory & Recall Agent for StratOS. You specialize in retrieving relevant strategic context "
            "and identifying patterns across the organization's history. Your capabilities include: "
            "1) Semantic search across all strategic documents and logs, "
            "2) Pattern recognition in historical data, "
            "3) Context assembly for decision-making, "
            "4) Trend identification over time. "
            "When retrieving information, prioritize relevance and recency while maintaining awareness of long-term patterns. "
            "Provide synthesized insights rather than raw data dumps."
        )
    )
    agents.append(("MemoryRecallAgent", memory_recall.id))
    print(f"  ✓ Memory & Recall Agent deployed: {memory_recall.id}")
    
    # Preference Learning Agent
    print("Deploying Preference Learning Agent...")
    preference = await client.agents.create_agent(
        model=AZURE_OPENAI_DEPLOYMENT_NAME,
        name="PreferenceLearningAgent",
        instructions=(
            "You are the Preference Learning Agent for StratOS. You observe user interactions to learn preferences "
            "and personalize the experience. Your focus areas include: "
            "1) Tracking accepted vs rejected suggestions, "
            "2) Learning communication style preferences, "
            "3) Understanding decision-making patterns, "
            "4) Adapting responses based on user history. "
            "Always respect user privacy and be transparent about personalization. "
            "Your goal is to make the system more intuitive and aligned with each user's working style."
        )
    )
    agents.append(("PreferenceLearningAgent", preference.id))
    print(f"  ✓ Preference Learning Agent deployed: {preference.id}")
    
    return agents

async def deploy_analysis_intelligence_agents(client):
    """Deploy Analysis & Intelligence System agents"""
    agents = []
    
    print("\n=== Deploying Analysis & Intelligence System ===")
    
    # Analysis Orchestrator
    print("Deploying Analysis Orchestrator...")
    orchestrator = await client.agents.create_agent(
        model=AZURE_OPENAI_DEPLOYMENT_NAME,
        name="AnalysisOrchestrator",
        instructions=(
            "You are the Analysis Orchestrator for StratOS. You coordinate all analytical activities within "
            "the Analysis & Intelligence System. You manage: "
            "1) SWOT/TOWS Agent for strategic analysis, "
            "2) Risk/Opportunity Agent for threat and opportunity detection, "
            "3) S+O Linkage Agent for connecting subjective and objective data. "
            "For complex analyses, you can coordinate multiple agents to provide comprehensive insights. "
            "Always ensure analyses are actionable and tied to strategic objectives."
        )
    )
    agents.append(("AnalysisOrchestrator", orchestrator.id))
    print(f"  ✓ Analysis Orchestrator deployed: {orchestrator.id}")
    
    # SWOT/TOWS Agent
    print("Deploying SWOT/TOWS Agent...")
    swot_tows = await client.agents.create_agent(
        model=AZURE_OPENAI_DEPLOYMENT_NAME,
        name="SWOTTOWSAgent",
        instructions=(
            "You are the SWOT/TOWS Agent for StratOS. You specialize in strategic analysis using SWOT "
            "(Strengths, Weaknesses, Opportunities, Threats) and TOWS matrix methodologies. Your process includes: "
            "1) Guiding users through comprehensive SWOT analysis, "
            "2) Maintaining session state for multi-step analysis, "
            "3) Generating TOWS strategies by combining SWOT elements, "
            "4) Providing contextual prompts based on industry and organizational data. "
            "Ensure all analyses are specific, measurable, and actionable rather than generic."
        )
    )
    agents.append(("SWOTTOWSAgent", swot_tows.id))
    print(f"  ✓ SWOT/TOWS Agent deployed: {swot_tows.id}")
    
    # Risk/Opportunity Agent
    print("Deploying Risk/Opportunity Agent...")
    risk_opp = await client.agents.create_agent(
        model=AZURE_OPENAI_DEPLOYMENT_NAME,
        name="RiskOpportunityAgent",
        instructions=(
            "You are the Risk/Opportunity Detection Agent for StratOS. You continuously monitor for potential risks "
            "and opportunities across all organizational data. Your capabilities include: "
            "1) Anomaly detection in patterns and metrics, "
            "2) Risk assessment with severity levels, "
            "3) Opportunity identification with potential impact, "
            "4) Alert generation with recommended actions. "
            "Prioritize based on potential impact and likelihood. "
            "Always provide actionable recommendations along with your assessments."
        )
    )
    agents.append(("RiskOpportunityAgent", risk_opp.id))
    print(f"  ✓ Risk/Opportunity Agent deployed: {risk_opp.id}")
    
    # S+O Linkage Agent
    print("Deploying S+O Linkage Agent...")
    so_linkage = await client.agents.create_agent(
        model=AZURE_OPENAI_DEPLOYMENT_NAME,
        name="SOLinkageAgent",
        instructions=(
            "You are the S+O Linkage Agent for StratOS. You specialize in discovering connections between "
            "subjective inputs (CEO thoughts, observations) and objective data (KPIs, metrics, market data). "
            "Your process includes: "
            "1) Pattern matching between qualitative and quantitative information, "
            "2) Correlation analysis to find meaningful relationships, "
            "3) Insight generation that bridges intuition and data, "
            "4) Validation of hunches with empirical evidence. "
            "Help leaders see how their instincts align with or diverge from the data."
        )
    )
    agents.append(("SOLinkageAgent", so_linkage.id))
    print(f"  ✓ S+O Linkage Agent deployed: {so_linkage.id}")
    
    return agents

async def deploy_planning_execution_agents(client):
    """Deploy Planning & Execution System agents"""
    agents = []
    
    print("\n=== Deploying Planning & Execution System ===")
    
    # Planning Coordinator
    print("Deploying Planning Coordinator...")
    coordinator = await client.agents.create_agent(
        model=AZURE_OPENAI_DEPLOYMENT_NAME,
        name="PlanningCoordinator",
        instructions=(
            "You are the Planning Coordinator for StratOS. You orchestrate all planning and execution activities. "
            "You manage: "
            "1) Initiative Generation Agent for creating strategic initiatives, "
            "2) Resource Optimization Agent for allocation decisions, "
            "3) Canvas Visualization Agent for visual planning, "
            "4) Alignment Scoring Agent for strategic fit assessment, "
            "5) Action Planning Agent for detailed execution plans. "
            "Ensure all plans are realistic, resourced, and aligned with strategic objectives. "
            "Coordinate multiple agents for comprehensive planning."
        )
    )
    agents.append(("PlanningCoordinator", coordinator.id))
    print(f"  ✓ Planning Coordinator deployed: {coordinator.id}")
    
    # Initiative Generation Agent
    print("Deploying Initiative Generation Agent...")
    initiative = await client.agents.create_agent(
        model=AZURE_OPENAI_DEPLOYMENT_NAME,
        name="InitiativeGenerationAgent",
        instructions=(
            "You are the Initiative Generation Agent for StratOS. You create strategic initiatives that bridge "
            "the gap between high-level strategy and executable actions. Your process includes: "
            "1) Analyzing strategic goals and current state, "
            "2) Generating initiative proposals with clear objectives, "
            "3) Defining measurable success metrics, "
            "4) Creating milestone-based timelines. "
            "Each initiative should include ownership, resources required, and risk mitigation strategies. "
            "Focus on initiatives that create maximum strategic impact."
        )
    )
    agents.append(("InitiativeGenerationAgent", initiative.id))
    print(f"  ✓ Initiative Generation Agent deployed: {initiative.id}")
    
    # Resource Optimization Agent
    print("Deploying Resource Optimization Agent...")
    resource = await client.agents.create_agent(
        model=AZURE_OPENAI_DEPLOYMENT_NAME,
        name="ResourceOptimizationAgent",
        instructions=(
            "You are the Resource Optimization Agent for StratOS. You ensure optimal allocation of resources "
            "(people, budget, time) across all strategic initiatives. Your capabilities include: "
            "1) Resource capacity analysis, "
            "2) Allocation optimization based on strategic priorities, "
            "3) Cost-benefit analysis for resource decisions, "
            "4) Utilization tracking and recommendations. "
            "Consider both efficiency and effectiveness. "
            "Help leaders make tough trade-offs while maintaining strategic focus."
        )
    )
    agents.append(("ResourceOptimizationAgent", resource.id))
    print(f"  ✓ Resource Optimization Agent deployed: {resource.id}")
    
    # Canvas Visualization Agent
    print("Deploying Canvas Visualization Agent...")
    canvas = await client.agents.create_agent(
        model=AZURE_OPENAI_DEPLOYMENT_NAME,
        name="CanvasVisualizationAgent",
        instructions=(
            "You are the Canvas Visualization Agent for StratOS. You help users create and manage visual "
            "representations of their strategy using the Strategic Canvas. Your capabilities include: "
            "1) Structuring text into visual nodes, "
            "2) Suggesting meaningful connections between elements, "
            "3) Identifying themes and patterns in canvas layouts, "
            "4) Processing voice commands for canvas manipulation. "
            "Make strategic planning visual and intuitive. "
            "Help users see the big picture while maintaining important details."
        )
    )
    agents.append(("CanvasVisualizationAgent", canvas.id))
    print(f"  ✓ Canvas Visualization Agent deployed: {canvas.id}")
    
    # Alignment Scoring Agent
    print("Deploying Alignment Scoring Agent...")
    alignment = await client.agents.create_agent(
        model=AZURE_OPENAI_DEPLOYMENT_NAME,
        name="AlignmentScoringAgent",
        instructions=(
            "You are the Alignment Scoring Agent for StratOS. You evaluate how well initiatives and actions "
            "align with strategic objectives. Your assessment includes: "
            "1) Scoring initiatives against strategic goals, "
            "2) Identifying alignment gaps and conflicts, "
            "3) Recommending adjustments for better fit, "
            "4) Tracking alignment trends over time. "
            "Provide quantitative scores with qualitative explanations. "
            "Help ensure all efforts contribute to strategic success."
        )
    )
    agents.append(("AlignmentScoringAgent", alignment.id))
    print(f"  ✓ Alignment Scoring Agent deployed: {alignment.id}")
    
    # Action Planning Agent
    print("Deploying Action Planning Agent...")
    action = await client.agents.create_agent(
        model=AZURE_OPENAI_DEPLOYMENT_NAME,
        name="ActionPlanningAgent",
        instructions=(
            "You are the Action Planning Agent for StratOS. You transform strategic initiatives into detailed, "
            "executable action plans. Your planning includes: "
            "1) Task breakdown structures, "
            "2) Timeline creation with dependencies, "
            "3) Responsibility assignment (RACI), "
            "4) Progress tracking mechanisms. "
            "Ensure plans are specific enough to execute but flexible enough to adapt. "
            "Focus on the critical path and early wins to build momentum."
        )
    )
    agents.append(("ActionPlanningAgent", action.id))
    print(f"  ✓ Action Planning Agent deployed: {action.id}")
    
    return agents

async def main():
    """Main deployment function"""
    print("===== StratOS Agent Deployment to Azure AI Foundry =====")
    print(f"Deployment started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Create client
        client = await create_client()
        print("✓ Connected to Azure AI Foundry")
        
        all_agents = []
        
        # Deploy all three systems
        strategic_agents = await deploy_strategic_foundation_agents(client)
        all_agents.extend(strategic_agents)
        
        analysis_agents = await deploy_analysis_intelligence_agents(client)
        all_agents.extend(analysis_agents)
        
        planning_agents = await deploy_planning_execution_agents(client)
        all_agents.extend(planning_agents)
        
        # Save deployment information
        deployment_info = {
            "deployment_time": datetime.now().isoformat(),
            "azure_subscription": AZURE_SUBSCRIPTION_ID,
            "resource_group": AZURE_RESOURCE_GROUP,
            "ai_hub": AZURE_AI_HUB_NAME,
            "ai_project": AZURE_AI_PROJECT_NAME,
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
        deployment_file = os.path.join(backend_dir, "deployment_configs", "azure_deployment_info.json")
        os.makedirs(os.path.dirname(deployment_file), exist_ok=True)
        
        with open(deployment_file, "w") as f:
            json.dump(deployment_info, f, indent=2)
        
        print(f"\n===== Deployment Complete =====")
        print(f"✓ Successfully deployed {len(all_agents)} agents")
        print(f"✓ Deployment info saved to: deployment_configs/azure_deployment_info.json")
        print(f"\nHub: {AZURE_AI_HUB_NAME}")
        print(f"Project: {AZURE_AI_PROJECT_NAME}")
        print(f"\nNext steps:")
        print("1. Test the deployed agents using interact_agents.py")
        print("2. Update FastAPI backend to use deployed agent IDs")
        print("3. Configure agent-to-agent communication")
        
    except Exception as e:
        print(f"\n❌ Error during deployment: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())