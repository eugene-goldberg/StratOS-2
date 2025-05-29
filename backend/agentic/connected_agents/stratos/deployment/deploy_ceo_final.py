#!/usr/bin/env python3
"""
Deploy CEO Log Agent following Weather Agent Pattern
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
from agents.ceo_log_agent_final import (
    AGENT_NAME_PREFIX,
    MODEL_NAME,
    AGENT_INSTRUCTIONS,
    TOOLS,
    AZURE_FUNCTION_BASE,
    AZURE_FUNCTION_KEYS
)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

def deploy_ceo_log_agent():
    """Deploy CEO Log Agent with Function Tools"""
    
    logger.info("Deploying CEO Log Agent with Azure Function Integration")
    logger.info("=" * 70)
    
    # Create unique agent name
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    agent_name = f"{AGENT_NAME_PREFIX}-{timestamp}"
    
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
    
    logger.info(f"\n✅ CEO Log Agent deployed successfully!")
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
            "endpoints": list(AZURE_FUNCTION_KEYS.keys())
        }
    }
    
    # Save to file
    deployment_file = Path(__file__).parent / f"ceo_final_deployment_{timestamp}.json"
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
        "ceo_log_agent_id": agent.id,
        "ceo_log_agent_name": agent.name,
        "ceo_function_endpoint": AZURE_FUNCTION_BASE,
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
    logger.info(f"Type: Function Tools (following weather agent pattern)")
    logger.info(f"\nAzure Function Endpoints:")
    for endpoint, key in AZURE_FUNCTION_KEYS.items():
        logger.info(f"  - {endpoint}: {AZURE_FUNCTION_BASE}/{endpoint}")
    logger.info("\n✅ The agent is now ready to:")
    logger.info("  - Save CEO log entries to Cosmos DB")
    logger.info("  - Search through historical entries")
    logger.info("  - Analyze logs for patterns and insights")
    logger.info("  - Extract strategic insights from entries")
    
    return agent.id

if __name__ == "__main__":
    print(f"🎉 CEO Log Agent deployed with ID: {deploy_ceo_log_agent()}")