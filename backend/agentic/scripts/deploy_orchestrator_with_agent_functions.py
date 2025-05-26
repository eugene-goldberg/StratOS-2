#!/usr/bin/env python3
"""
Deploy Main Orchestrator with function tools that reference our deployed agents.
Based on the pattern from semantic_kernel_multi_agent deploy_orchestration.py
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

# Create function tools for each agent
def create_agent_function_tools(deployed_agents):
    """Create function tool definitions for each deployed agent"""
    tools = []
    
    # CEO Log Agent function
    if "CEOLogAgent" in deployed_agents:
        tools.append({
            "type": "function",
            "function": {
                "name": "invoke_ceo_log_agent",
                "description": "Process CEO's subjective inputs, notes, observations, and concerns",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "message": {
                            "type": "string",
                            "description": "The CEO's log entry or message to process"
                        },
                        "agent_id": {
                            "type": "string",
                            "description": f"The CEO Log Agent ID: {deployed_agents['CEOLogAgent']}",
                            "default": deployed_agents['CEOLogAgent']
                        }
                    },
                    "required": ["message"]
                }
            }
        })
    
    # North Star Agent function
    if "NorthStarAgent" in deployed_agents:
        tools.append({
            "type": "function",
            "function": {
                "name": "invoke_north_star_agent",
                "description": "Manage company Purpose, Vision, Values, and Strategic Goals",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Question about vision, values, or strategic goals"
                        },
                        "agent_id": {
                            "type": "string",
                            "description": f"The North Star Agent ID: {deployed_agents['NorthStarAgent']}",
                            "default": deployed_agents['NorthStarAgent']
                        }
                    },
                    "required": ["query"]
                }
            }
        })
    
    # SWOT/TOWS Agent function
    if "SWOTTOWSAgent" in deployed_agents:
        tools.append({
            "type": "function",
            "function": {
                "name": "invoke_swot_agent",
                "description": "Perform SWOT analysis and generate TOWS strategies",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "analysis_request": {
                            "type": "string",
                            "description": "The SWOT analysis request or topic"
                        },
                        "agent_id": {
                            "type": "string",
                            "description": f"The SWOT/TOWS Agent ID: {deployed_agents['SWOTTOWSAgent']}",
                            "default": deployed_agents['SWOTTOWSAgent']
                        }
                    },
                    "required": ["analysis_request"]
                }
            }
        })
    
    # Add more agent functions as needed...
    
    return tools

# Main Orchestrator configuration
def create_orchestrator_config(deployed_agents):
    """Create orchestrator configuration with agent function tools"""
    
    # Get the agent IDs for instructions
    agent_list = "\n".join([f"- {name}: {agent_id}" for name, agent_id in deployed_agents.items()])
    
    return {
        "name": "MainOrchestrator",
        "instructions": (
            "You are the Main Orchestrator for StratOS, a comprehensive strategy operating system. "
            "Your role is to analyze incoming requests and delegate them to the appropriate specialized agent using the provided functions.\n\n"
            
            "IMPORTANT: You have function tools to invoke specific agents. Use these functions to delegate tasks:\n"
            "- For CEO log entries, use invoke_ceo_log_agent\n"
            "- For vision/values queries, use invoke_north_star_agent\n"
            "- For SWOT analysis, use invoke_swot_agent\n\n"
            
            "When you receive a request:\n"
            "1. Analyze what the user needs\n"
            "2. Select the appropriate agent function\n"
            "3. Call the function with the user's message\n"
            "4. Return the agent's response to the user\n\n"
            
            f"Available agents and their IDs:\n{agent_list}\n\n"
            
            "Always explain your routing decision before invoking an agent function."
        ),
        "description": "Primary orchestrator that routes requests to specialized agents using function calls"
    }

async def deploy_orchestrator_with_functions():
    """Deploy the Main Orchestrator with agent function tools."""
    
    try:
        # Load deployed agent IDs
        deployed_agents = load_agent_ids()
        logger.info(f"Loaded {len(deployed_agents)} deployed agents")
        
        # Create function tools
        tools = create_agent_function_tools(deployed_agents)
        logger.info(f"Created {len(tools)} function tools for orchestrator")
        
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
            
            # Create new orchestrator with function tools
            logger.info("Creating Main Orchestrator with agent function tools...")
            
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
            logger.info(f"  Tools: {len(tools)} agent functions")
            
            # Save deployment info
            deployment_info = {
                "agent_name": "MainOrchestrator",
                "agent_id": agent_definition.id,
                "deployment_time": datetime.now(timezone.utc).isoformat(),
                "deployment_type": "main_orchestrator_with_functions",
                "phase": "phase_1_unified_mas",
                "has_tools": True,
                "tool_count": len(tools),
                "tool_names": [tool['function']['name'] for tool in tools]
            }
            
            with open(deployment_config_path, 'w') as f:
                json.dump(deployment_info, f, indent=2)
            
            print("\n" + "="*80)
            print("DEPLOYMENT SUMMARY")
            print("="*80)
            print(f"✅ Main Orchestrator deployed with agent function tools!")
            print(f"✅ Agent ID: {agent_definition.id}")
            print(f"✅ Function tools created for {len(tools)} agents:")
            for tool in tools:
                print(f"   - {tool['function']['name']}")
            print("\nThe orchestrator can now directly invoke other agents!")
            
            return agent_definition.id
            
    except Exception as e:
        logger.error(f"Error deploying orchestrator: {str(e)}", exc_info=True)
        sys.exit(1)
    finally:
        await credential.close()

async def main():
    """Main entry point."""
    print("="*80)
    print("DEPLOYING MAIN ORCHESTRATOR WITH AGENT FUNCTIONS")
    print("Based on semantic_kernel_multi_agent patterns")
    print("="*80)
    print(f"\nDeployment started at: {datetime.now(timezone.utc).isoformat()}")
    
    agent_id = await deploy_orchestrator_with_functions()
    
    print(f"\nDeployment completed at: {datetime.now(timezone.utc).isoformat()}")

if __name__ == "__main__":
    asyncio.run(main())