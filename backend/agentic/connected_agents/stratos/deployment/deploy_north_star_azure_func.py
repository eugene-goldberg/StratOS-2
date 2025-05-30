#!/usr/bin/env python3
"""
Deploy North Star Agent with Azure Function Tools
Agent can directly call Azure Functions
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

# Import agent configuration
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from agents.north_star_agent_azure_function import (
    AGENT_NAME,
    MODEL_NAME,
    AGENT_INSTRUCTIONS,
    TOOLS
)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

def deploy_north_star_azure_func_agent():
    """Deploy North Star Agent with Azure Function Tools"""
    
    logger.info("Deploying North Star Agent with Azure Function Tools")
    logger.info("=" * 70)
    
    # Create unique agent name
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    agent_name = f"{AGENT_NAME}-{timestamp}"
    
    # Azure AI Project configuration
    endpoint = os.getenv("AZURE_AI_PROJECT_CONNECTION_STRING")
    if not endpoint:
        raise ValueError("AZURE_AI_PROJECT_CONNECTION_STRING not found in environment")
    
    # Create AI Project client
    credential = DefaultAzureCredential()
    client = AIProjectClient(
        endpoint=endpoint,
        credential=credential
    )
    
    logger.info(f"Creating agent: {agent_name}")
    logger.info(f"Model: {MODEL_NAME}")
    logger.info(f"Tools: {len(TOOLS)} Azure Function tool(s)")
    logger.info("\nAzure Function Tools configured:")
    for tool in TOOLS:
        logger.info(f"  - {tool['function']['name']}: {tool['function']['url']}")
    
    # Create the agent
    agent = client.agents.create_agent(
        name=agent_name,
        instructions=AGENT_INSTRUCTIONS,
        tools=TOOLS,
        model=MODEL_NAME
    )
    
    logger.info(f"\n✅ North Star Azure Function Agent deployed successfully!")
    logger.info(f"   Agent ID: {agent.id}")
    logger.info(f"   Name: {agent.name}")
    logger.info(f"   Model: {agent.model}")
    
    # Save deployment info
    deployment_info = {
        "agent_id": agent.id,
        "agent_name": agent.name,
        "deployment_time": datetime.now().isoformat(),
        "model": agent.model,
        "has_azure_function_tools": True,
        "azure_function_endpoints": [
            {
                "operation": "ManagePurpose",
                "url": "https://stratos-north-star-functions.azurewebsites.net/api/ManagePurpose"
            },
            {
                "operation": "ManageVision",
                "url": "https://stratos-north-star-functions.azurewebsites.net/api/ManageVision"
            },
            {
                "operation": "ManageValues",
                "url": "https://stratos-north-star-functions.azurewebsites.net/api/ManageValues"
            },
            {
                "operation": "ManageStrategicGoals",
                "url": "https://stratos-north-star-functions.azurewebsites.net/api/ManageStrategicGoals"
            },
            {
                "operation": "ValidateAlignment", 
                "url": "https://stratos-north-star-functions.azurewebsites.net/api/ValidateAlignment"
            },
            {
                "operation": "GetNorthStarSummary",
                "url": "https://stratos-north-star-functions.azurewebsites.net/api/GetNorthStarSummary"
            }
        ],
        "cosmos_db": {
            "account": "stratos-ceo-logs-db",
            "database": "StratOSData",
            "container": "NorthStar"
        }
    }
    
    # Save to file
    deployment_file = Path(__file__).parent / f"north_star_azure_func_deployment_{timestamp}.json"
    with open(deployment_file, 'w') as f:
        json.dump(deployment_info, f, indent=2)
    
    logger.info(f"\n💾 Deployment info saved to: {deployment_file}")
    
    logger.info("\n" + "="*70)
    logger.info("📋 DEPLOYMENT SUMMARY")
    logger.info("="*70)
    logger.info(f"Agent Name: {agent.name}")
    logger.info(f"Agent ID: {agent.id}")
    logger.info(f"Type: Azure Function Tools (Agent calls functions directly)")
    logger.info(f"\n✅ The agent can now:")
    logger.info("  - Directly call Azure Functions without client involvement")
    logger.info("  - Manage organizational purpose and vision")
    logger.info("  - Define and maintain core values")
    logger.info("  - Create and organize strategic goals hierarchically")
    logger.info("  - Validate alignment of initiatives with North Star")
    logger.info("  - Provide comprehensive strategic foundation summaries")
    logger.info("\n⚡ IMPORTANT: The test client will NOT make any Azure Function calls")
    logger.info("   All Azure Function calls are made directly by the agent!")
    
    return agent.id

if __name__ == "__main__":
    print(f"🎉 North Star Azure Function Agent deployed with ID: {deploy_north_star_azure_func_agent()}")