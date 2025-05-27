#!/usr/bin/env python3
"""
Deploy Main Orchestrator to Azure AI Agent Service with explicit endpoint.
"""

import asyncio
import os
import sys
import logging
from datetime import datetime, timezone
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [%(funcName)s] %(message)s')
logger = logging.getLogger(__name__)

# Add parent directories to path
current_dir = os.path.dirname(os.path.abspath(__file__))
agentic_dir = os.path.dirname(current_dir)
sys.path.insert(0, agentic_dir)

# Load environment variables
env_path = os.path.join(agentic_dir, '.env')
logger.info(f"Loading .env from: {env_path}")
load_dotenv(env_path)

# Import required modules
from azure.identity.aio import DefaultAzureCredential
from azure.ai.projects.aio import AIProjectClient

async def deploy_orchestrator():
    """Deploy the Main Orchestrator to Azure AI Agent Service."""
    
    # Hardcode the endpoint since SDK discovery isn't working
    endpoint = "https://ai.azure.com/api/eastus/agents/v1.0/subscriptions/514bd6d3-2c02-45c6-a86f-29cf262a379a/resourceGroups/semantic-kernel-multi-agent-rg/providers/Microsoft.MachineLearningServices/workspaces/sk-multi-agent-project"
    
    # Get model deployment
    model_deployment = os.getenv("AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME", "gpt-35-turbo")
    
    logger.info(f"Using endpoint: {endpoint}")
    logger.info(f"Using model: {model_deployment}")
    
    # Create credential
    credential = DefaultAzureCredential()
    
    try:
        # Create AI Project client
        async with AIProjectClient(
            endpoint=endpoint,
            credential=credential,
            api_version="2024-12-01-preview"
        ) as client:
            logger.info("Successfully connected to Azure AI Agent Service")
            
            # Define the orchestrator with routing tools
            orchestrator_config = {
                "name": "MainOrchestratorAgent",
                "instructions": """You are the main orchestrator that routes user requests to the appropriate specialist agent in the StratOS system.

Route requests as follows:
- CEO notes, observations, or subjective inputs → CEOLogAgent
- Vision, mission, values, purpose, or strategic goals → NorthStarAgent
- Past context, patterns, or historical information → MemoryRecallAgent
- User preferences or personalization → PreferenceLearningAgent
- SWOT analysis or TOWS strategies → SWOTTOWSAgent
- Risk assessment or opportunity identification → RiskOpportunityAgent
- Linking subjective insights with objective data → SOLinkageAgent
- Strategic alignment assessment or scoring → AlignmentScoringAgent
- Creating strategic initiatives or high-level planning → InitiativeGenerationAgent
- Resource allocation, optimization, or capacity planning → ResourceOptimizationAgent
- Detailed action planning, task breakdown, progress tracking → ActionPlanningAgent
- Strategic canvas, visualization, or visual planning → CanvasVisualizationAgent

Your job is to determine which specialist can best answer the query and route accordingly. Do not answer questions yourself - route to the appropriate specialist.""",
                "model": model_deployment,
                "tools": [
                    {"type": "function", "function": {"name": "RouteToCEOLogAgent", "description": "Route to CEOLogAgent for CEO notes and observations"}},
                    {"type": "function", "function": {"name": "RouteToNorthStarAgent", "description": "Route to NorthStarAgent for vision, mission, values"}},
                    {"type": "function", "function": {"name": "RouteToMemoryRecallAgent", "description": "Route to MemoryRecallAgent for past context and patterns"}},
                    {"type": "function", "function": {"name": "RouteToPreferenceLearningAgent", "description": "Route to PreferenceLearningAgent for user preferences"}},
                    {"type": "function", "function": {"name": "RouteToSWOTTOWSAgent", "description": "Route to SWOTTOWSAgent for SWOT analysis"}},
                    {"type": "function", "function": {"name": "RouteToRiskOpportunityAgent", "description": "Route to RiskOpportunityAgent for risk and opportunity assessment"}},
                    {"type": "function", "function": {"name": "RouteToSOLinkageAgent", "description": "Route to SOLinkageAgent for linking subjective and objective data"}},
                    {"type": "function", "function": {"name": "RouteToAlignmentScoringAgent", "description": "Route to AlignmentScoringAgent for strategic alignment"}},
                    {"type": "function", "function": {"name": "RouteToInitiativeGenerationAgent", "description": "Route to InitiativeGenerationAgent for strategic initiatives"}},
                    {"type": "function", "function": {"name": "RouteToResourceOptimizationAgent", "description": "Route to ResourceOptimizationAgent for resource planning"}},
                    {"type": "function", "function": {"name": "RouteToActionPlanningAgent", "description": "Route to ActionPlanningAgent for detailed action planning"}},
                    {"type": "function", "function": {"name": "RouteToCanvasVisualizationAgent", "description": "Route to CanvasVisualizationAgent for visual planning"}}
                ]
            }
            
            # Create the agent
            logger.info("Creating Main Orchestrator...")
            agent = await client.agents.create_agent(
                name=orchestrator_config["name"],
                instructions=orchestrator_config["instructions"],
                model=orchestrator_config["model"],
                tools=orchestrator_config["tools"]
            )
            
            logger.info(f"✅ Main Orchestrator deployed successfully!")
            logger.info(f"Agent ID: {agent.id}")
            logger.info(f"Name: {agent.name}")
            logger.info(f"Model: {agent.model}")
            logger.info(f"Tools: {len(agent.tools) if hasattr(agent, 'tools') else 0}")
            
            # Update .env file with new orchestrator ID
            logger.info(f"\n📝 Add this to your .env file:")
            logger.info(f'MAIN_ORCHESTRATOR_AGENT_ID="{agent.id}"')
            
            return agent.id
            
    except Exception as e:
        logger.error(f"Error deploying orchestrator: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    print("\n" + "="*80)
    print("DEPLOYING MAIN ORCHESTRATOR")
    print("="*80 + "\n")
    
    orchestrator_id = asyncio.run(deploy_orchestrator())
    
    if orchestrator_id:
        print("\n" + "="*80)
        print("✅ DEPLOYMENT SUCCESSFUL")
        print("="*80)
        print(f"Orchestrator ID: {orchestrator_id}")
        print("="*80)
    else:
        print("\n" + "="*80)
        print("❌ DEPLOYMENT FAILED")
        print("="*80)