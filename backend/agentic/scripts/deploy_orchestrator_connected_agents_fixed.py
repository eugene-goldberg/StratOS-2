#!/usr/bin/env python3
"""
Deploy Main Orchestrator using Connected Agents pattern.
The orchestrator will invoke other agents as tools within Azure AI Foundry.
"""

import asyncio
import os
import sys
import json
import logging
from datetime import datetime, timezone
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [%(funcName)s] %(message)s')
logger = logging.getLogger(__name__)

# Add parent directories to path
current_dir = os.path.dirname(os.path.abspath(__file__))
agentic_dir = os.path.dirname(current_dir) 
env_path = os.path.join(agentic_dir, '.env')

logger.info(f"Attempting to load .env file from: {env_path}")
if load_dotenv(env_path):
    logger.info(".env file loaded successfully.")

# Import required modules
try:
    from azure.identity.aio import DefaultAzureCredential
    from semantic_kernel.agents import AzureAIAgent, AzureAIAgentSettings 
except ImportError as e:
    logger.error(f"Error importing required modules: {e}")
    sys.exit(1)

# Load deployed agent IDs
def load_agent_ids():
    """Load all deployed agent IDs from deployment configs"""
    deployment_config_path = os.path.join(agentic_dir, "deployment_configs", "ai_project_agents_deployment.json")
    
    with open(deployment_config_path, 'r') as f:
        data = json.load(f)
        return data.get('deployed_agents', {})

# Create Connected Agent tools
def create_connected_agent_tools(deployed_agents):
    """
    Create tool definitions for Connected Agents.
    Each tool represents a specialty agent that can be invoked.
    """
    tools = []
    
    # Map of agent names to their deployment IDs
    agent_mapping = {
        "CEOLogAgent": "CEOLogAgent",
        "NorthStarAgent": "NorthStarAgent",
        "SWOTTOWSAgent": "SWOTTOWSAgent",
        "OpportunityScoutAgent": "RiskOpportunityAgent",
        "RiskRadarAgent": "RiskOpportunityAgent",
        "CompetitorInsightsAgent": "SOLinkageAgent",
        "StrategicInitiativesAgent": "InitiativeGenerationAgent",
        "ResourceOptimizerAgent": "ResourceOptimizationAgent",
        "ExecutionTrackerAgent": "ActionPlanningAgent",
        "CanvasAgent": "CanvasVisualizationAgent",
        "ConversationAgent": "AlignmentScoringAgent",
        "MemoryRecallAgent": "MemoryRecallAgent",
        "PreferenceLearningAgent": "PreferenceLearningAgent"
    }
    
    # Create tools for each available agent
    for ui_name, deployment_name in agent_mapping.items():
        if deployment_name in deployed_agents:
            tools.append({
                "type": "connected_agent",
                "connected_agent": {
                    "id": deployed_agents[deployment_name],
                    "name": ui_name
                }
            })
            logger.info(f"Added Connected Agent tool: {ui_name} -> {deployment_name}")
    
    return tools

# Main Orchestrator configuration
def create_orchestrator_config(deployed_agents):
    """Create orchestrator configuration for Connected Agents pattern"""
    
    # Build agent descriptions for instructions
    agent_descriptions = {
        "CEOLogAgent": "Handles CEO's subjective inputs, notes, observations, and concerns",
        "NorthStarAgent": "Manages Purpose, Vision, Values, and Strategic Goals",
        "MemoryRecallAgent": "Retrieves context, patterns, and historical information",
        "PreferenceLearningAgent": "Tracks user preferences and personalizes experiences",
        "SWOTTOWSAgent": "Performs SWOT analysis and generates TOWS strategies",
        "RiskOpportunityAgent": "Detects risks and identifies opportunities",
        "SOLinkageAgent": "Links subjective insights with objective data",
        "InitiativeGenerationAgent": "Creates strategic initiatives and action plans",
        "ResourceOptimizationAgent": "Manages resource allocation and capacity planning",
        "CanvasVisualizationAgent": "Handles visual strategic planning on canvas",
        "AlignmentScoringAgent": "Assesses strategic alignment of initiatives",
        "ActionPlanningAgent": "Creates detailed execution plans"
    }
    
    # Build agent list for instructions
    agent_list = "\n".join([
        f"{i+1}. {name} (ID: {agent_id}) - {agent_descriptions.get(name, 'Specialized agent')}"
        for i, (name, agent_id) in enumerate(deployed_agents.items())
    ])
    
    return {
        "name": "MainOrchestrator",
        "instructions": (
            "You are the Main Orchestrator for StratOS, a comprehensive strategy operating system. "
            "Your role is to analyze incoming requests and delegate them to the appropriate specialized agent.\n\n"
            
            "IMPORTANT: You have access to all specialized agents as Connected Agent tools. "
            "Each agent appears as a 'connected_agent' type tool that you can invoke directly.\n\n"
            
            "AVAILABLE AGENTS:\n"
            f"{agent_list}\n\n"
            
            "ROUTING APPROACH:\n"
            "1. Analyze the user's request to understand their intent\n"
            "2. Identify which specialized agent is best suited to handle the request\n"
            "3. Invoke that agent by passing the user's message to it\n"
            "4. Return the specialized agent's response to the user\n\n"
            
            "ROUTING GUIDELINES:\n"
            "- For CEO notes, observations, or log entries → CEOLogAgent\n"
            "- For questions about vision, mission, values → NorthStarAgent\n"
            "- For SWOT analysis requests → SWOTTOWSAgent\n"
            "- For risk assessment or opportunity identification → RiskOpportunityAgent\n"
            "- For linking insights with data → SOLinkageAgent\n"
            "- For creating initiatives or action plans → InitiativeGenerationAgent\n"
            "- For resource allocation or optimization → ResourceOptimizationAgent\n"
            "- For strategic canvas or visualization → CanvasVisualizationAgent\n"
            "- For alignment assessment → AlignmentScoringAgent\n"
            "- For detailed execution planning → ActionPlanningAgent\n"
            "- For retrieving past context or patterns → MemoryRecallAgent\n"
            "- For user preference tracking → PreferenceLearningAgent\n\n"
            
            "Always explain which agent you're routing to and why before invoking it."
        ),
        "description": "Primary orchestrator using Connected Agents to route requests to specialized agents"
    }

async def deploy_orchestrator_with_connected_agents():
    """Deploy the Main Orchestrator with Connected Agents."""
    
    try:
        # Load deployed agent IDs
        deployed_agents = load_agent_ids()
        logger.info(f"Loaded {len(deployed_agents)} deployed agents")
        
        # Create Connected Agent tools
        tools = create_connected_agent_tools(deployed_agents)
        logger.info(f"Created {len(tools)} Connected Agent tools")
        
        # Check required environment variables
        settings = AzureAIAgentSettings()
        logger.info(f"Endpoint: {settings.endpoint}")
        
        # Create credential
        credential = DefaultAzureCredential()
        
        # Create client
        async with AzureAIAgent.create_client(credential=credential, settings=settings) as client:
            logger.info("Successfully connected to Azure AI Agent Service")
            
            # Check if Main Orchestrator already exists
            existing_orchestrator_id = None
            deployment_config_path = os.path.join(agentic_dir, "deployment_configs", "main_orchestrator_deployment.json")
            
            if os.path.exists(deployment_config_path):
                with open(deployment_config_path, 'r') as f:
                    existing_config = json.load(f)
                    existing_orchestrator_id = existing_config.get("agent_id")
                    logger.info(f"Found existing orchestrator: {existing_orchestrator_id}")
                
                # Delete existing orchestrator
                try:
                    await client.agents.delete_agent(existing_orchestrator_id)
                    logger.info("Deleted existing orchestrator")
                except Exception as e:
                    logger.warning(f"Could not delete existing orchestrator: {e}")
            
            # Create orchestrator configuration
            config = create_orchestrator_config(deployed_agents)
            
            # Create new orchestrator with Connected Agent tools
            logger.info("Creating Main Orchestrator with Connected Agents...")
            
            agent_definition = await client.agents.create_agent(
                model=settings.model_deployment_name,
                name=config['name'],
                instructions=config['instructions'],
                description=config['description'],
                tools=tools
            )
            
            logger.info(f"✅ Main Orchestrator created successfully!")
            logger.info(f"  ID: {agent_definition.id}")
            logger.info(f"  Name: {agent_definition.name}")
            logger.info(f"  Connected Agents: {len(tools)}")
            
            # Save deployment info
            deployment_info = {
                "agent_name": "MainOrchestrator",
                "agent_id": agent_definition.id,
                "deployment_time": datetime.now(timezone.utc).isoformat(),
                "deployment_type": "main_orchestrator_connected_agents",
                "phase": "phase_1_unified_mas",
                "has_tools": True,
                "tool_count": len(tools),
                "tool_type": "connected_agents",
                "connected_agent_ids": list(deployed_agents.values())
            }
            
            with open(deployment_config_path, 'w') as f:
                json.dump(deployment_info, f, indent=2)
            
            print("\n" + "="*80)
            print("DEPLOYMENT SUMMARY")
            print("="*80)
            print(f"✅ Main Orchestrator deployed with Connected Agents!")
            print(f"✅ Agent ID: {agent_definition.id}")
            print(f"✅ Connected to {len(tools)} specialized agents:")
            for name, agent_id in deployed_agents.items():
                print(f"   - {name}: {agent_id}")
            print("\nThe orchestrator can now invoke any specialized agent as a tool!")
            print("\nThis follows the Azure AI Foundry 'Connected Agents' pattern.")
            
            return agent_definition.id
            
    except Exception as e:
        logger.error(f"Error deploying orchestrator: {str(e)}", exc_info=True)
        sys.exit(1)
    finally:
        await credential.close()

async def main():
    """Main entry point."""
    print("="*80)
    print("DEPLOYING MAIN ORCHESTRATOR WITH CONNECTED AGENTS")
    print("Using Azure AI Foundry Connected Agents pattern")
    print("="*80)
    print(f"\nDeployment started at: {datetime.now(timezone.utc).isoformat()}")
    
    agent_id = await deploy_orchestrator_with_connected_agents()
    
    print(f"\nDeployment completed at: {datetime.now(timezone.utc).isoformat()}")

if __name__ == "__main__":
    asyncio.run(main())