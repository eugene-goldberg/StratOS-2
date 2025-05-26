#!/usr/bin/env python3
"""
Deploy Main Orchestrator with function tools for all specialist agents.
Following the semantic_kernel_multi_agent pattern for tool-based delegation.
"""

import asyncio
import os
import json
import sys
import logging
from datetime import datetime, timezone
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add parent directory to path
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

def create_agent_function_tool(agent_name: str, agent_description: str, agent_capabilities: list) -> dict:
    """Create a function tool definition for a specialist agent."""
    
    # Build parameters based on agent capabilities
    properties = {
        "request": {
            "type": "string",
            "description": f"The user's request to be handled by {agent_name}"
        }
    }
    
    # Add specific parameters based on agent type
    if "log" in agent_name.lower() or "ceo" in agent_name.lower():
        properties["category"] = {
            "type": "string",
            "enum": ["strategic", "operational", "personal", "market", "team"],
            "description": "Category of the log entry"
        }
    elif "swot" in agent_name.lower():
        properties["analysis_type"] = {
            "type": "string",
            "enum": ["swot", "tows"],
            "description": "Type of analysis to perform"
        }
    elif "resource" in agent_name.lower():
        properties["resource_type"] = {
            "type": "string",
            "enum": ["budget", "personnel", "time", "equipment"],
            "description": "Type of resource to optimize"
        }
    
    return {
        "type": "function",
        "function": {
            "name": f"invoke_{agent_name.lower().replace(' ', '_')}",
            "description": agent_description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": ["request"]
            }
        }
    }

def create_all_agent_tools() -> list:
    """Create function tool definitions for all StratOS specialist agents."""
    
    agent_definitions = [
        # Strategic Foundation & Insights System
        {
            "name": "CEOLogAgent",
            "description": "Handle CEO's subjective inputs, notes, observations, and log entries",
            "capabilities": ["log_entry", "categorization", "insight_extraction"]
        },
        {
            "name": "NorthStarAgent",
            "description": "Manage company vision, mission, values, and strategic goals",
            "capabilities": ["vision_management", "goal_setting", "okr_tracking"]
        },
        {
            "name": "MemoryRecallAgent",
            "description": "Retrieve historical context, patterns, and past experiences",
            "capabilities": ["context_retrieval", "pattern_recognition", "historical_search"]
        },
        {
            "name": "PreferenceLearningAgent",
            "description": "Track and learn user preferences for personalized experiences",
            "capabilities": ["preference_tracking", "personalization", "behavior_learning"]
        },
        {
            "name": "StrategicContextRouter",
            "description": "Route requests within the strategic foundation domain",
            "capabilities": ["strategic_routing", "context_analysis"]
        },
        
        # Analysis & Intelligence System
        {
            "name": "SWOTTOWSAgent",
            "description": "Perform SWOT analysis and generate TOWS strategies",
            "capabilities": ["swot_analysis", "tows_generation", "strategic_assessment"]
        },
        {
            "name": "RiskOpportunityAgent",
            "description": "Identify and analyze risks and opportunities",
            "capabilities": ["risk_assessment", "opportunity_identification", "impact_analysis"]
        },
        {
            "name": "SOLinkageAgent",
            "description": "Link subjective insights with objective data",
            "capabilities": ["data_correlation", "insight_validation", "objective_linking"]
        },
        {
            "name": "AnalysisOrchestrator",
            "description": "Orchestrate complex analysis workflows",
            "capabilities": ["analysis_coordination", "multi_agent_analysis"]
        },
        
        # Planning & Execution System
        {
            "name": "InitiativeGenerationAgent",
            "description": "Create strategic initiatives and action plans",
            "capabilities": ["initiative_creation", "action_planning", "strategy_development"]
        },
        {
            "name": "ResourceOptimizationAgent",
            "description": "Optimize resource allocation and capacity planning",
            "capabilities": ["resource_allocation", "capacity_planning", "optimization"]
        },
        {
            "name": "ActionPlanningAgent",
            "description": "Develop detailed action plans for initiatives",
            "capabilities": ["detailed_planning", "task_breakdown", "timeline_creation"]
        },
        {
            "name": "AlignmentScoringAgent",
            "description": "Score alignment between initiatives and strategic goals",
            "capabilities": ["alignment_assessment", "goal_mapping", "scoring"]
        },
        {
            "name": "CanvasVisualizationAgent",
            "description": "Handle visual strategic planning on canvas",
            "capabilities": ["visualization", "canvas_management", "visual_planning"]
        },
        {
            "name": "PlanningCoordinator",
            "description": "Coordinate planning activities across the system",
            "capabilities": ["planning_orchestration", "coordination", "workflow_management"]
        }
    ]
    
    # Create function tools for each agent
    tools = []
    for agent_def in agent_definitions:
        tool = create_agent_function_tool(
            agent_def["name"],
            agent_def["description"],
            agent_def["capabilities"]
        )
        tools.append(tool)
    
    return tools

async def deploy_orchestrator_with_tools():
    """Deploy the Main Orchestrator with function tools for all agents."""
    
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
            
            # Create all agent function tools
            agent_tools = create_all_agent_tools()
            logger.info(f"Created {len(agent_tools)} function tool definitions")
            
            # Define the orchestrator configuration with tool calling instructions
            orchestrator_config = {
                "name": "MainOrchestratorWithTools",
                "instructions": (
                    "You are the Main Orchestrator for StratOS, a comprehensive strategy operating system. "
                    "Your role is to analyze incoming requests and delegate them to the appropriate specialized agent using function calls.\n\n"
                    
                    "AVAILABLE SPECIALIST AGENTS (as function tools):\n"
                    "Strategic Foundation & Insights:\n"
                    "- invoke_ceologagent: For CEO notes, observations, or log entries\n"
                    "- invoke_northstaragent: For vision, mission, values, and strategic goals\n"
                    "- invoke_memoryrecallagent: For retrieving past context or patterns\n"
                    "- invoke_preferencelearningagent: For user preference tracking\n"
                    "- invoke_strategiccontextrouter: For strategic foundation routing\n\n"
                    
                    "Analysis & Intelligence:\n"
                    "- invoke_swottowsagent: For SWOT analysis and TOWS strategies\n"
                    "- invoke_riskopportunityagent: For risk assessment or opportunity identification\n"
                    "- invoke_solinkageagent: For linking subjective insights with data\n"
                    "- invoke_analysisorchestrator: For complex analysis orchestration\n\n"
                    
                    "Planning & Execution:\n"
                    "- invoke_initiativegenerationagent: For creating strategic initiatives\n"
                    "- invoke_resourceoptimizationagent: For resource allocation\n"
                    "- invoke_actionplanningagent: For detailed action planning\n"
                    "- invoke_alignmentscoringagent: For initiative-goal alignment\n"
                    "- invoke_canvasvisualizationagent: For strategic canvas visualization\n"
                    "- invoke_planningcoordinator: For planning coordination\n\n"
                    
                    "IMPORTANT INSTRUCTIONS:\n"
                    "1. Analyze the user's request to understand their intent\n"
                    "2. Determine which specialist agent should handle the request\n"
                    "3. Use the appropriate function tool to delegate the request\n"
                    "4. Pass the user's complete request to the specialist agent\n"
                    "5. Return the specialist agent's response to the user\n\n"
                    
                    "Always use function calling to delegate work. Do not try to answer specialized questions yourself. "
                    "Your role is to orchestrate by calling the appropriate specialist agent function."
                ),
                "description": "Main orchestrator using function calling for agent delegation",
                "tools": agent_tools
            }
            
            # Create the orchestrator with tools
            logger.info("Creating Main Orchestrator with function tools...")
            
            agent_definition = await client.agents.create_agent(
                model=settings.model_deployment_name,
                name=orchestrator_config['name'],
                instructions=orchestrator_config['instructions'],
                description=orchestrator_config['description'],
                tools=orchestrator_config['tools']
            )
            
            logger.info(f"✅ Main Orchestrator created successfully!")
            logger.info(f"  ID: {agent_definition.id}")
            logger.info(f"  Name: {agent_definition.name}")
            logger.info(f"  Model: {agent_definition.model}")
            logger.info(f"  Tools: {len(orchestrator_config['tools'])} function tools")
            
            # Save deployment info
            deployment_config_path = os.path.join(agentic_dir, "deployment_configs", "main_orchestrator_tools_deployment.json")
            os.makedirs(os.path.dirname(deployment_config_path), exist_ok=True)
            
            deployment_info = {
                "agent_name": "MainOrchestratorWithTools",
                "agent_id": agent_definition.id,
                "deployment_time": datetime.now(timezone.utc).isoformat(),
                "deployment_type": "main_orchestrator_with_function_tools",
                "architecture": "tool_calling",
                "routing_method": "function_tools",
                "specialist_agents": 15,
                "tools_count": len(agent_tools),
                "notes": "Deployed with function tools for all specialist agents following semantic_kernel_multi_agent pattern"
            }
            
            with open(deployment_config_path, 'w') as f:
                json.dump(deployment_info, f, indent=2)
            
            print("\n" + "="*80)
            print("DEPLOYMENT SUMMARY")
            print("="*80)
            print(f"✅ Main Orchestrator deployed with function tools!")
            print(f"✅ Agent ID: {agent_definition.id}")
            print(f"✅ Architecture: Tool calling with {len(agent_tools)} function tools")
            print(f"✅ Each specialist agent can be invoked via function calls")
            print("\nNext Steps:")
            print("1. Update FastAPI to handle tool calls from orchestrator")
            print("2. Implement tool call handlers that invoke actual agents")
            print("3. Test with scripts/test_orchestrator_tool_calling.py")
            
        await credential.close()
        
    except Exception as e:
        logger.error(f"Deployment failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(deploy_orchestrator_with_tools())