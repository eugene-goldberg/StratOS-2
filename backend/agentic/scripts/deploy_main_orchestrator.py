#!/usr/bin/env python3
"""
Deploy MainOrchestratorAgent to Azure AI Agent Service.
This orchestrator uses tool calling to delegate to specialist agents.
"""

import os
import sys
import json
import asyncio
import logging
from datetime import datetime, timezone
from dotenv import load_dotenv
import aiohttp

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
current_dir = os.path.dirname(os.path.abspath(__file__))
agentic_dir = os.path.dirname(current_dir)
env_path = os.path.join(agentic_dir, '.env')
logger.info(f"Loading .env from: {env_path}")
load_dotenv(env_path)

# Import credential
from azure.identity.aio import DefaultAzureCredential

async def deploy_main_orchestrator():
    """Deploy the MainOrchestratorAgent with tool calling capabilities"""
    
    # Get configuration
    endpoint = os.getenv("AZURE_AI_AGENT_ENDPOINT")
    api_version = os.getenv("AZURE_AI_AGENT_API_VERSION", "2024-12-01-preview")
    model_deployment = os.getenv("AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME", "gpt-35-turbo")
    
    if not endpoint:
        logger.error("AZURE_AI_AGENT_ENDPOINT not set")
        return None
        
    logger.info(f"Using endpoint: {endpoint}")
    logger.info(f"Using model: {model_deployment}")
    
    # Load specialist agent IDs from environment
    specialist_agents = [
        {"name": "CEOLogAgent", "id": os.getenv("CEO_LOG_AGENT_ID"), "description": "Handles CEO's subjective inputs, notes, observations, and concerns"},
        {"name": "NorthStarAgent", "id": os.getenv("NORTH_STAR_AGENT_ID"), "description": "Manages Purpose, Vision, Values, and Strategic Goals"},
        {"name": "SWOTTOWSAgent", "id": os.getenv("SWOT_TOWS_AGENT_ID"), "description": "Performs SWOT analysis and generates TOWS strategies"},
        {"name": "MemoryRecallAgent", "id": os.getenv("MEMORY_RECALL_AGENT_ID"), "description": "Retrieves context, patterns, and historical information"},
        {"name": "PreferenceLearningAgent", "id": os.getenv("PREFERENCE_LEARNING_AGENT_ID"), "description": "Tracks user preferences and personalizes experiences"},
        {"name": "RiskOpportunityAgent", "id": os.getenv("RISK_OPPORTUNITY_AGENT_ID"), "description": "Identifies and analyzes risks and opportunities"},
        {"name": "SOLinkageAgent", "id": os.getenv("SO_LINKAGE_AGENT_ID"), "description": "Links subjective insights with objective data"},
        {"name": "InitiativeGenerationAgent", "id": os.getenv("INITIATIVE_GENERATION_AGENT_ID"), "description": "Creates strategic initiatives"},
        {"name": "ResourceOptimizationAgent", "id": os.getenv("RESOURCE_OPTIMIZATION_AGENT_ID"), "description": "Manages resource allocation and capacity planning"},
        {"name": "ActionPlanningAgent", "id": os.getenv("ACTION_PLANNING_AGENT_ID"), "description": "Develops detailed action plans and tracks execution"},
        {"name": "CanvasVisualizationAgent", "id": os.getenv("CANVAS_VISUALIZATION_AGENT_ID"), "description": "Handles visual strategic planning on canvas"},
        {"name": "AlignmentScoringAgent", "id": os.getenv("ALIGNMENT_SCORING_AGENT_ID"), "description": "Manages strategic conversations and assesses alignment"}
    ]
    
    # Verify all agent IDs are present
    missing_agents = [agent["name"] for agent in specialist_agents if not agent["id"] or "asst_" not in agent["id"]]
    if missing_agents:
        logger.error(f"Missing or invalid agent IDs for: {missing_agents}")
        logger.error("Please ensure all specialist agent IDs are set in .env file")
        return None
    
    logger.info("All specialist agent IDs verified:")
    for agent in specialist_agents:
        logger.info(f"  {agent['name']}: {agent['id']}")
    
    # Build agent descriptions for instructions
    agent_descriptions = "\n".join([f"- {agent['name']}: {agent['description']}" for agent in specialist_agents])
    
    # Build routing guidelines
    routing_guidelines = """
- For CEO notes, observations, log entries, or subjective inputs → Route to CEOLogAgent
- For questions about vision, mission, values, purpose, or strategic goals → Route to NorthStarAgent
- For SWOT analysis or TOWS strategies → Route to SWOTTOWSAgent
- For retrieving past context, patterns, or historical information → Route to MemoryRecallAgent
- For personalization, user preferences, or behavioral patterns → Route to PreferenceLearningAgent
- For identifying and analyzing risks or opportunities → Route to RiskOpportunityAgent
- For linking subjective insights with objective data → Route to SOLinkageAgent
- For creating new strategic initiatives → Route to InitiativeGenerationAgent
- For resource allocation, capacity planning, or optimization → Route to ResourceOptimizationAgent
- For developing action plans or tracking execution → Route to ActionPlanningAgent
- For visual strategic planning or canvas work → Route to CanvasVisualizationAgent
- For assessing strategic alignment or managing conversations → Route to AlignmentScoringAgent"""
    
    # Create the orchestrator configuration
    orchestrator_config = {
        "name": "MainOrchestratorAgent",
        "model": model_deployment,
        "instructions": f"""You are the Main Orchestrator for StratOS, a comprehensive strategy operating system.
Your role is to analyze incoming user requests and delegate them to the most appropriate specialized agent.

AVAILABLE SPECIALIST AGENTS:
{agent_descriptions}

ROUTING APPROACH:
1. Carefully analyze the user's request to understand their specific intent
2. Identify which specialist agent is best suited to handle the request
3. Route the request to that specialist agent
4. Present the specialist's response clearly to the user

ROUTING GUIDELINES:
{routing_guidelines}

IMPORTANT:
- Do NOT attempt to answer requests directly if they fall under a specialist's responsibility
- Your primary function is to accurately route requests to the correct specialist
- If a request is ambiguous, ask clarifying questions before routing
- Always be helpful and professional in your interactions""",
        "tools": [
            {
                "type": "function",
                "function": {
                    "name": "route_to_specialist",
                    "description": "Routes a user request to the appropriate specialist agent",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "specialist_agent_name": {
                                "type": "string",
                                "description": "The name of the specialist agent to route to",
                                "enum": [agent["name"] for agent in specialist_agents]
                            },
                            "user_request": {
                                "type": "string",
                                "description": "The user's request to forward to the specialist"
                            }
                        },
                        "required": ["specialist_agent_name", "user_request"]
                    }
                }
            }
        ],
        "metadata": {
            "deployment_type": "main_orchestrator_with_tools",
            "specialist_agents_count": str(len(specialist_agents)),
            "created_at": datetime.now(timezone.utc).isoformat()
        }
    }
    
    try:
        # Get credential
        async with DefaultAzureCredential() as credential:
            # Get token
            token = await credential.get_token("https://management.azure.com/.default")
            
            headers = {
                "Authorization": f"Bearer {token.token}",
                "Content-Type": "application/json"
            }
            
            async with aiohttp.ClientSession() as session:
                # Deploy the orchestrator
                deploy_url = f"{endpoint}/assistants?api-version={api_version}"
                
                logger.info("Deploying MainOrchestratorAgent...")
                async with session.post(deploy_url, headers=headers, json=orchestrator_config) as response:
                    if response.status in [200, 201]:
                        result = await response.json()
                        orchestrator_id = result["id"]
                        logger.info(f"Successfully deployed MainOrchestratorAgent with ID: {orchestrator_id}")
                        
                        # Save deployment info
                        deployment_info = {
                            "agent_name": "MainOrchestratorAgent",
                            "agent_id": orchestrator_id,
                            "deployment_time": datetime.now(timezone.utc).isoformat(),
                            "deployment_type": "main_orchestrator_with_tool_calling",
                            "architecture": "plugin_based_tool_calling",
                            "routing_method": "semantic_kernel_plugins",
                            "specialist_agents": len(specialist_agents),
                            "specialist_agent_ids": {agent["name"]: agent["id"] for agent in specialist_agents},
                            "notes": "Deployed with Semantic Kernel plugin-based tool calling for multi-agent orchestration"
                        }
                        
                        # Save to file
                        deployment_file = os.path.join(agentic_dir, "deployment_configs", "main_orchestrator_tool_deployment.json")
                        os.makedirs(os.path.dirname(deployment_file), exist_ok=True)
                        with open(deployment_file, 'w') as f:
                            json.dump(deployment_info, f, indent=2)
                        
                        logger.info(f"Deployment info saved to: {deployment_file}")
                        return orchestrator_id
                        
                    else:
                        error_text = await response.text()
                        logger.error(f"Failed to deploy orchestrator: {response.status} - {error_text}")
                        return None
                        
    except Exception as e:
        logger.error(f"Error during deployment: {e}", exc_info=True)
        return None

async def main():
    """Main function"""
    logger.info("Starting MainOrchestratorAgent deployment...")
    orchestrator_id = await deploy_main_orchestrator()
    
    if orchestrator_id:
        print(f"\n✅ MainOrchestratorAgent successfully deployed!")
        print(f"   Agent ID: {orchestrator_id}")
        print(f"\nYou can now test the orchestrator using:")
        print(f"   python3 scripts/test_deployed_orchestrator.py")
    else:
        print("\n❌ Deployment failed. Check the logs above for details.")

if __name__ == "__main__":
    asyncio.run(main())