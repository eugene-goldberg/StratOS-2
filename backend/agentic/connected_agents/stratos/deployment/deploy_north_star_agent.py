#!/usr/bin/env python3
"""
Deploy North Star Agent following CEO Log Agent Pattern
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
from agents.north_star_agent_final import (
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

# Azure Function configuration
AZURE_FUNCTION_BASE = "https://stratos-north-star-functions.azurewebsites.net/api"
AZURE_FUNCTION_KEY = "gPXyuj42jT_BnlDhImnO1gaV_xayICaGrxf2NoTA1_hVAzFuSjMcqQ=="

def deploy_north_star_agent():
    """Deploy North Star Agent with Function Tools"""
    
    logger.info("Deploying North Star Agent with Azure Function Integration")
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
    logger.info(f"Tools: {len(TOOLS)} function tool(s)")
    
    # Create the agent
    agent = client.agents.create_agent(
        name=agent_name,
        instructions=AGENT_INSTRUCTIONS,
        tools=TOOLS,
        model=MODEL_NAME
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
        "has_function_tools": True,
        "azure_functions": {
            "base_url": AZURE_FUNCTION_BASE,
            "endpoints": [
                "ManagePurpose",
                "ManageVision", 
                "ManageValues",
                "ManageStrategicGoals",
                "ValidateAlignment",
                "GetNorthStarSummary"
            ]
        },
        "cosmos_db": {
            "account": "stratos-ceo-logs-db",
            "database": "StratOSData",
            "container": "NorthStar"
        }
    }
    
    # Save to file
    deployment_file = Path(__file__).parent / f"north_star_agent_deployment_{timestamp}.json"
    with open(deployment_file, 'w') as f:
        json.dump(deployment_info, f, indent=2)
    
    logger.info(f"\n💾 Deployment info saved to: {deployment_file}")
    
    # Update deployment_info.json in project root
    deployment_info_file = Path(__file__).parent.parent.parent / "deployment_info.json"
    try:
        with open(deployment_info_file, 'r') as f:
            existing_info = json.load(f)
    except:
        existing_info = {}
    
    existing_info.update({
        "north_star_agent_id": agent.id,
        "north_star_agent_name": agent.name,
        "north_star_function_endpoint": AZURE_FUNCTION_BASE,
        "deployed_at": datetime.now().isoformat(),
        "has_azure_function_integration": True
    })
    
    with open(deployment_info_file, 'w') as f:
        json.dump(existing_info, f, indent=2)
    
    logger.info("\n" + "="*70)
    logger.info("📋 DEPLOYMENT SUMMARY")
    logger.info("="*70)
    logger.info(f"Agent Name: {agent.name}")
    logger.info(f"Agent ID: {agent.id}")
    logger.info(f"Type: Function Tools (following CEO Log agent pattern)")
    logger.info(f"\nAzure Function Endpoints:")
    for endpoint in deployment_info["azure_functions"]["endpoints"]:
        logger.info(f"  - {endpoint}: {AZURE_FUNCTION_BASE}/{endpoint}")
    logger.info("\n✅ The agent is now ready to:")
    logger.info("  - Manage organizational purpose and vision")
    logger.info("  - Define and maintain core values")
    logger.info("  - Create and organize strategic goals hierarchically")
    logger.info("  - Validate alignment of initiatives with North Star")
    logger.info("  - Provide comprehensive strategic foundation summaries")
    
    return agent.id

if __name__ == "__main__":
    print(f"🎉 North Star Agent deployed with ID: {deploy_north_star_agent()}")