#!/usr/bin/env python3
"""
Deploy North Star Agent with FunctionTool Pattern
Following the exact Azure AI Agents function calling example
"""

import os
import sys
import json
import logging
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Add parent directories to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.agents.models import FunctionTool

# Import our North Star functions
from north_star_functions import north_star_functions

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# Configuration
AGENT_NAME = "NorthStarAgentFunctionTool"
MODEL_NAME = "gpt-35-turbo"

AGENT_INSTRUCTIONS = """You are the North Star Agent for StratOS, responsible for defining and maintaining the organization's strategic foundation.

You have access to functions for managing North Star elements:
- manage_purpose: Get or set the organizational purpose
- manage_vision: Get or set the organizational vision
- manage_values: Add, remove, or list organizational values
- manage_strategic_goals: Create, update, delete, get, or list strategic goals with hierarchy
- validate_alignment: Check if elements align with the North Star
- get_north_star_summary: Get a complete overview of the North Star

Your responsibilities:
1. Guide organizations in defining clear purpose and vision
2. Help articulate and maintain core organizational values
3. Structure strategic goals in meaningful hierarchies
4. Ensure all activities align with the North Star
5. Provide strategic clarity during decision-making

Always use the appropriate function to interact with North Star data. Provide clear, actionable guidance."""


def deploy_north_star_agent():
    """Deploy North Star Agent with FunctionTool Pattern"""
    
    logger.info("Deploying North Star Agent with FunctionTool Pattern")
    logger.info("=" * 70)
    
    # Create unique agent name
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    agent_name = f"{AGENT_NAME}-{timestamp}"
    
    # Retrieve project endpoint from environment
    project_endpoint = os.getenv("AZURE_AI_PROJECT_CONNECTION_STRING")
    if not project_endpoint:
        raise ValueError("AZURE_AI_PROJECT_CONNECTION_STRING not found in environment")
    
    # Initialize the AIProjectClient
    credential = DefaultAzureCredential()
    project_client = AIProjectClient(
        endpoint=project_endpoint,
        credential=credential,
        api_version="latest"
    )
    
    logger.info(f"Creating agent: {agent_name}")
    logger.info(f"Model: {MODEL_NAME}")
    
    # Initialize the FunctionTool with North Star functions
    functions = FunctionTool(functions=north_star_functions)
    logger.info(f"Configured {len(north_star_functions)} functions")
    
    with project_client:
        # Create an agent with custom functions
        agent = project_client.agents.create_agent(
            model=MODEL_NAME,
            name=agent_name,
            instructions=AGENT_INSTRUCTIONS,
            tools=functions.definitions
        )
        
        logger.info(f"\n✅ North Star Agent deployed successfully!")
        logger.info(f"   Agent ID: {agent.id}")
        logger.info(f"   Name: {agent.name}")
        logger.info(f"   Model: {agent.model}")
    
    # Save deployment info
    deployment_info = {
        "agent_id": agent.id,
        "agent_name": agent.name,
        "deployment_time": datetime.now().isoformat(),
        "model": agent.model,
        "function_tool_pattern": True,
        "functions": [f.__name__ for f in north_star_functions],
        "azure_functions": {
            "app_name": "stratos-north-star-functions",
            "base_url": "https://stratos-north-star-functions.azurewebsites.net/api"
        },
        "cosmos_db": {
            "account": "stratos-ceo-logs-db",
            "database": "StratOSData",
            "container": "NorthStar"
        }
    }
    
    # Save to file
    deployment_file = Path(__file__).parent / f"north_star_function_tool_deployment_{timestamp}.json"
    with open(deployment_file, 'w') as f:
        json.dump(deployment_info, f, indent=2)
    
    logger.info(f"\n💾 Deployment info saved to: {deployment_file}")
    
    # Update main deployment info
    deployment_info_file = Path(__file__).parent.parent.parent / "stratos_deployment_info.json"
    try:
        with open(deployment_info_file, 'r') as f:
            existing_info = json.load(f)
    except:
        existing_info = {}
    
    existing_info["north_star_agent"] = {
        "agent_id": agent.id,
        "agent_name": agent.name,
        "deployed_at": datetime.now().isoformat(),
        "pattern": "FunctionTool",
        "functions": [f.__name__ for f in north_star_functions]
    }
    
    with open(deployment_info_file, 'w') as f:
        json.dump(existing_info, f, indent=2)
    
    logger.info("\n" + "="*70)
    logger.info("📋 DEPLOYMENT SUMMARY")
    logger.info("="*70)
    logger.info(f"Agent Name: {agent.name}")
    logger.info(f"Agent ID: {agent.id}")
    logger.info(f"Pattern: FunctionTool (following Azure example)")
    logger.info(f"\nDeployed Functions:")
    for func_name in [f.__name__ for f in north_star_functions]:
        logger.info(f"  - {func_name}")
    logger.info("\n✅ The agent is now ready to:")
    logger.info("  - Manage organizational purpose and vision")
    logger.info("  - Define and maintain core values")
    logger.info("  - Create hierarchical strategic goals")
    logger.info("  - Validate alignment with North Star")
    logger.info("  - Provide comprehensive North Star summaries")
    
    return agent.id


if __name__ == "__main__":
    agent_id = deploy_north_star_agent()
    print(f"\n🎉 North Star Agent deployed with ID: {agent_id}")
    print("\n📝 Use test_north_star_function_tool.py to test the agent")