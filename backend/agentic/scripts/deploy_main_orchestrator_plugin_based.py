#!/usr/bin/env python3
"""
Deploy Main Orchestrator to Azure AI Agent Service using plugin-based architecture.
Following the exact pattern from semantic_kernel_multi_agent example.
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
backend_dir = os.path.dirname(agentic_dir)
project_root = os.path.dirname(backend_dir)
sys.path.insert(0, project_root)

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

async def deploy_orchestrator():
    """Deploy the Main Orchestrator to Azure AI Agent Service."""
    
    try:
        # Check required environment variables
        settings = AzureAIAgentSettings()
        logger.info(f"Endpoint: {settings.endpoint}")
        logger.info(f"Model deployment: {settings.model_deployment_name}")
        
        # Create credential
        credential = DefaultAzureCredential()
        
        # Create client
        async with AzureAIAgent.create_client(credential=credential, settings=settings) as client:
            logger.info("Successfully connected to Azure AI Agent Service")
            
            # Define the orchestrator configuration
            # Note: In Azure AI Agent Service, we can't deploy with actual plugin references
            # Instead, we'll deploy with instructions that describe the routing behavior
            orchestrator_config = {
                "name": "MainOrchestrator",
                "instructions": (
                    "You are the Main Orchestrator for StratOS, a comprehensive strategy operating system. "
                    "Your role is to analyze incoming requests and determine which specialized agent should handle them.\n\n"
                    
                    "AVAILABLE SPECIALIST AGENTS:\n"
                    "1. CEOLogAgent - Handles CEO's subjective inputs, notes, observations, and concerns\n"
                    "2. NorthStarAgent - Manages Purpose, Vision, Values, and Strategic Goals\n"
                    "3. SWOTTOWSAgent - Performs SWOT analysis and generates TOWS strategies\n"
                    "4. OpportunityScoutAgent - Identifies opportunities from market analysis\n"
                    "5. RiskRadarAgent - Detects and analyzes risks\n"
                    "6. CompetitorInsightsAgent - Provides competitive intelligence\n"
                    "7. StrategicInitiativesAgent - Creates strategic initiatives and action plans\n"
                    "8. ResourceOptimizerAgent - Manages resource allocation and capacity planning\n"
                    "9. ExecutionTrackerAgent - Tracks execution progress and milestones\n"
                    "10. CanvasAgent - Handles visual strategic planning on canvas\n"
                    "11. ConversationAgent - Manages strategic conversations and alignment\n"
                    "12. MemoryRecallAgent - Retrieves context, patterns, and historical information\n"
                    "13. PreferenceLearningAgent - Tracks user preferences and personalizes experiences\n\n"
                    
                    "ROUTING APPROACH:\n"
                    "1. Analyze the user's request to understand their intent\n"
                    "2. Identify which specialized agent is best suited to handle the request\n"
                    "3. Provide a routing decision with the agent name and reasoning\n"
                    "4. Format your response as: 'ROUTE TO: [AgentName] - REASON: [Your reasoning]'\n\n"
                    
                    "ROUTING GUIDELINES:\n"
                    "- For CEO notes, observations, or log entries → CEOLogAgent\n"
                    "- For questions about vision, mission, values → NorthStarAgent\n"
                    "- For SWOT analysis requests → SWOTTOWSAgent\n"
                    "- For risk assessment → RiskRadarAgent\n"
                    "- For opportunity identification → OpportunityScoutAgent\n"
                    "- For competitive analysis → CompetitorInsightsAgent\n"
                    "- For creating initiatives or action plans → StrategicInitiativesAgent\n"
                    "- For resource allocation or optimization → ResourceOptimizerAgent\n"
                    "- For execution tracking → ExecutionTrackerAgent\n"
                    "- For strategic canvas or visualization → CanvasAgent\n"
                    "- For strategic conversations → ConversationAgent\n"
                    "- For retrieving past context or patterns → MemoryRecallAgent\n"
                    "- For user preference tracking → PreferenceLearningAgent\n\n"
                    
                    "Always provide clear routing decisions. Do not try to answer questions yourself."
                ),
                "description": "Primary orchestrator for StratOS using plugin-based architecture for routing"
            }
            
            # Create the orchestrator
            logger.info("Creating Main Orchestrator...")
            
            agent_definition = await client.agents.create_agent(
                model=settings.model_deployment_name,
                name=orchestrator_config['name'],
                instructions=orchestrator_config['instructions'],
                description=orchestrator_config['description']
            )
            
            logger.info(f"✅ Main Orchestrator created successfully!")
            logger.info(f"  ID: {agent_definition.id}")
            logger.info(f"  Name: {agent_definition.name}")
            logger.info(f"  Model: {agent_definition.model}")
            
            # Save deployment info
            deployment_config_path = os.path.join(agentic_dir, "deployment_configs", "main_orchestrator_deployment.json")
            os.makedirs(os.path.dirname(deployment_config_path), exist_ok=True)
            
            deployment_info = {
                "agent_name": "MainOrchestrator",
                "agent_id": agent_definition.id,
                "deployment_time": datetime.now(timezone.utc).isoformat(),
                "deployment_type": "main_orchestrator_plugin_based",
                "phase": "phase_1_unified_mas",
                "architecture": "plugin_based",
                "routing_method": "instruction_based",
                "specialist_agents": 13,
                "notes": "Deployed with plugin-based architecture following semantic_kernel_multi_agent pattern"
            }
            
            with open(deployment_config_path, 'w') as f:
                json.dump(deployment_info, f, indent=2)
            
            print("\n" + "="*80)
            print("DEPLOYMENT SUMMARY")
            print("="*80)
            print(f"✅ Main Orchestrator deployed successfully!")
            print(f"✅ Agent ID: {agent_definition.id}")
            print(f"✅ Architecture: Plugin-based (following semantic_kernel_multi_agent)")
            print(f"✅ Routing: Instruction-based with 13 specialist agents")
            print("\nNext Steps:")
            print("1. Test routing with verify_orchestrator_plugin_routing.py")
            print("2. Integrate with FastAPI backend for actual agent invocation")
            print("3. The orchestrator will provide routing decisions")
            print("4. The backend will invoke the appropriate specialist agent")
            
            return agent_definition.id
            
    except Exception as e:
        logger.error(f"Error deploying orchestrator: {str(e)}", exc_info=True)
        sys.exit(1)
    finally:
        await credential.close()

async def main():
    """Main entry point."""
    print("="*80)
    print("DEPLOYING MAIN ORCHESTRATOR (PLUGIN-BASED ARCHITECTURE)")
    print("Following semantic_kernel_multi_agent pattern")
    print("="*80)
    print(f"\nDeployment started at: {datetime.now(timezone.utc).isoformat()}")
    
    agent_id = await deploy_orchestrator()
    
    print(f"\nDeployment completed at: {datetime.now(timezone.utc).isoformat()}")

if __name__ == "__main__":
    asyncio.run(main())