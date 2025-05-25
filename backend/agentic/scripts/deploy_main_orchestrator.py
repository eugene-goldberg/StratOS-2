#!/usr/bin/env python3
"""
Deploy the Main Orchestrator to Azure AI Agent Service.

This is the primary routing agent for Phase 1 Unified MAS architecture.
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
env_path = os.path.join(agentic_dir, '.env')

logger.info(f"Attempting to load .env file from: {env_path}")
if load_dotenv(env_path):
    logger.info(".env file loaded successfully.")
else:
    logger.warning(f".env file not found at '{env_path}' or it's empty.")

# Import required modules
try:
    from azure.identity.aio import DefaultAzureCredential
    from semantic_kernel.agents import AzureAIAgent, AzureAIAgentSettings 
except ImportError as e:
    logger.error(f"Error importing required modules: {e}")
    logger.error("Please ensure 'semantic-kernel[azure]' and 'azure-identity' are installed.")
    sys.exit(1)

# Main Orchestrator configuration
MAIN_ORCHESTRATOR_CONFIG = {
    "name": "MainOrchestrator",
    "instructions": (
        "You are the Main Orchestrator for StratOS, a comprehensive strategy operating system. "
        "Your role is to analyze incoming requests and route them to the appropriate specialized agent within the Unified Multi-Agent System. "
        "\n\n"
        "AVAILABLE AGENTS:\n"
        "1. CEOLogAgent - Handles CEO's subjective inputs, notes, observations, and concerns\n"
        "2. NorthStarAgent - Manages Purpose, Vision, Values, and Strategic Goals\n"
        "3. MemoryAgent - Retrieves context, patterns, and historical information\n"
        "4. PreferenceAgent - Tracks user preferences and personalizes experiences\n"
        "5. SWOTTOWSAgent - Performs SWOT analysis and generates TOWS strategies\n"
        "6. RiskOpportunityAgent - Detects risks and identifies opportunities\n"
        "7. SOLinkageAgent - Links subjective insights with objective data\n"
        "8. InitiativeGenerationAgent - Creates strategic initiatives and action plans\n"
        "9. ResourceOptimizationAgent - Manages resource allocation and capacity planning\n"
        "10. CanvasInteractionAgent - Handles visual strategic planning on canvas\n"
        "11. AlignmentScoringAgent - Assesses strategic alignment of initiatives\n"
        "12. ActionPlanningAgent - Creates detailed execution plans\n"
        "\n"
        "ROUTING APPROACH:\n"
        "1. First, check for explicit task_type in the request\n"
        "2. If no task_type, analyze keywords and patterns in the user_query\n"
        "3. Consider session context for multi-turn conversations\n"
        "4. For ambiguous requests, ask clarifying questions\n"
        "\n"
        "IMPORTANT: You must route to exactly ONE agent per request. Do not attempt to handle requests yourself. "
        "Always provide clear reasoning for your routing decision."
    ),
    "description": "Primary routing agent for StratOS Unified MAS - routes all incoming requests to specialized agents"
}

async def deploy_main_orchestrator():
    """Deploy the Main Orchestrator to Azure AI Agent Service."""
    
    try:
        # Check required environment variables
        required_vars = [
            "AZURE_AI_AGENT_PROJECT_NAME",
            "AZURE_AI_AGENT_PROJECT_HUB_NAME",
            "AZURE_AI_AGENT_PROJECT_RESOURCE_GROUP",
            "AZURE_AI_AGENT_PROJECT_SUBSCRIPTION_ID",
            "AZURE_AI_AGENT_API_VERSION",
            "AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME"
        ]
        
        logger.info("--- Checking required Azure AI Project context variables ---")
        for var_name in required_vars:
            val = os.getenv(var_name)
            if not val:
                logger.error(f"CRITICAL: Required environment variable '{var_name}' is not set.")
                sys.exit(1)
            os.environ[var_name] = val  # Ensure it's in os.environ
            logger.info(f"  {var_name}: '{val}'")
        
        # Initialize settings
        settings = AzureAIAgentSettings()
        logger.info(f"--- AzureAIAgentSettings initialized ---")
        logger.info(f"  Endpoint: {settings.endpoint}")
        logger.info(f"  API Version: {settings.api_version}")
        logger.info(f"  Model: {settings.model_deployment_name}")
        
        # Create credential
        credential = DefaultAzureCredential()
        
        # Create client
        async with AzureAIAgent.create_client(credential=credential, settings=settings) as client:
            logger.info("Successfully connected to Azure AI Agent Service")
            
            # Check if Main Orchestrator already exists
            logger.info(f"Checking if agent '{MAIN_ORCHESTRATOR_CONFIG['name']}' already exists...")
            existing_agent = None
            
            async for agent in client.agents.list_agents():
                if agent.name == MAIN_ORCHESTRATOR_CONFIG['name']:
                    existing_agent = agent
                    logger.info(f"Agent '{MAIN_ORCHESTRATOR_CONFIG['name']}' already exists with ID: {agent.id}")
                    break
            
            if existing_agent:
                # Update existing agent
                logger.info(f"Updating existing Main Orchestrator...")
                try:
                    # Delete and recreate (Azure AI Agent Service doesn't support update yet)
                    logger.info(f"Deleting existing agent to recreate with updated configuration...")
                    await client.agents.delete_agent(existing_agent.id)
                    logger.info(f"Existing agent deleted.")
                except Exception as e:
                    logger.warning(f"Could not delete existing agent: {e}")
            
            # Create new Main Orchestrator
            logger.info(f"Creating Main Orchestrator with model '{settings.model_deployment_name}'...")
            
            agent_definition = await client.agents.create_agent(
                model=settings.model_deployment_name,
                name=MAIN_ORCHESTRATOR_CONFIG['name'],
                instructions=MAIN_ORCHESTRATOR_CONFIG['instructions'],
                description=MAIN_ORCHESTRATOR_CONFIG['description']
            )
            
            logger.info(f"✅ Main Orchestrator created successfully!")
            logger.info(f"  ID: {agent_definition.id}")
            logger.info(f"  Name: {agent_definition.name}")
            logger.info(f"  Model: {agent_definition.model}")
            logger.info(f"  Created: {agent_definition.created_at}")
            
            # Verify deployment by listing all agents
            print("\n" + "="*80)
            print("VERIFYING DEPLOYMENT - CURRENT AGENTS")
            print("="*80)
            
            stratos_agents = []
            test_agents = []
            
            async for agent in client.agents.list_agents():
                if any(agent.name.startswith(prefix) for prefix in ['test', 'Test', 'demo', 'Chat', 'Calculator', 'Weather', 'Orchestrator']):
                    test_agents.append(agent.name)
                else:
                    stratos_agents.append(agent.name)
            
            print(f"\n✅ StratOS Agents ({len(stratos_agents)}):")
            for name in sorted(stratos_agents):
                if name == MAIN_ORCHESTRATOR_CONFIG['name']:
                    print(f"  • {name} ⭐ NEW - PRIMARY ORCHESTRATOR")
                else:
                    print(f"  • {name}")
            
            if test_agents:
                print(f"\n🧪 Test/Demo Agents ({len(test_agents)}):")
                for name in sorted(test_agents):
                    print(f"  • {name}")
            
            print("\n" + "="*80)
            print("DEPLOYMENT SUMMARY")
            print("="*80)
            print(f"✅ Main Orchestrator deployed successfully!")
            print(f"✅ Total StratOS agents: {len(stratos_agents)}")
            print(f"✅ Phase 1 Unified MAS architecture is now complete!")
            print("\nNext steps:")
            print("1. Create FastAPI integration layer (StratOSAgentClient)")
            print("2. Update services to route through Main Orchestrator")
            print("3. Test end-to-end routing with all agents")
            
            return agent_definition.id
            
    except Exception as e:
        logger.error(f"Error deploying Main Orchestrator: {str(e)}", exc_info=True)
        sys.exit(1)
    finally:
        # Clean up credential
        await credential.close()

async def main():
    """Main entry point."""
    print("="*80)
    print("DEPLOYING MAIN ORCHESTRATOR TO AZURE AI AGENT SERVICE")
    print("Phase 1 Unified MAS Primary Routing Agent")
    print("="*80)
    print(f"\nDeployment started at: {datetime.now(timezone.utc).isoformat()}")
    
    agent_id = await deploy_main_orchestrator()
    
    if agent_id:
        # Save deployment info
        deployment_info = {
            "agent_name": MAIN_ORCHESTRATOR_CONFIG['name'],
            "agent_id": agent_id,
            "deployment_time": datetime.now(timezone.utc).isoformat(),
            "deployment_type": "main_orchestrator",
            "phase": "phase_1_unified_mas"
        }
        
        import json
        deployment_file = os.path.join(agentic_dir, "deployment_configs", "main_orchestrator_deployment.json")
        os.makedirs(os.path.dirname(deployment_file), exist_ok=True)
        
        with open(deployment_file, "w") as f:
            json.dump(deployment_info, f, indent=2)
        
        logger.info(f"Deployment info saved to: {deployment_file}")
    
    print(f"\nDeployment completed at: {datetime.now(timezone.utc).isoformat()}")

if __name__ == "__main__":
    asyncio.run(main())