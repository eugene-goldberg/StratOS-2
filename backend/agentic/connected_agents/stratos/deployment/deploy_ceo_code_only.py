#!/usr/bin/env python3
"""
Deploy CEO Log Agent with Code Interpreter Only
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
from agents.ceo_log_agent_code_only import (
    AGENT_NAME_PREFIX,
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

def deploy_ceo_log_agent():
    """Deploy CEO Log Agent with Code Interpreter Only"""
    
    logger.info("Deploying CEO Log Agent (Code Interpreter Only)")
    logger.info("=" * 70)
    
    # Create unique agent name
    timestamp = datetime.now().strftime("%H%M%S")
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
    logger.info(f"Tools: Code Interpreter only")
    
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
        "has_code_interpreter": True,
        "has_function_tools": False,
        "azure_functions": {
            "base_url": "https://stratos-ceo-log-functions.azurewebsites.net/api",
            "endpoints": [
                "SaveCEOLog",
                "SearchCEOLogs", 
                "AnalyzeLogs",
                "GetInsights"
            ]
        }
    }
    
    # Save to file
    deployment_file = Path(__file__).parent / f"ceo_code_only_deployment_{timestamp}.json"
    with open(deployment_file, 'w') as f:
        json.dump(deployment_info, f, indent=2)
    
    logger.info(f"\n💾 Deployment info saved to: {deployment_file}")
    
    # Update .env file
    env_file = Path(__file__).parent.parent / '.env'
    if env_file.exists():
        with open(env_file, 'r') as f:
            lines = f.readlines()
        
        # Update CEO_LOG_AGENT_ID
        updated = False
        for i, line in enumerate(lines):
            if line.startswith('CEO_LOG_AGENT_ID='):
                lines[i] = f'CEO_LOG_AGENT_ID="{agent.id}"\n'
                updated = True
                break
        
        if not updated:
            lines.append(f'\nCEO_LOG_AGENT_ID="{agent.id}"\n')
        
        with open(env_file, 'w') as f:
            f.writelines(lines)
        
        logger.info("\n✅ Updated .env file with new agent ID")
    
    logger.info("\n" + "="*70)
    logger.info("📋 DEPLOYMENT SUMMARY")
    logger.info("="*70)
    logger.info(f"Agent Name: {agent.name}")
    logger.info(f"Agent ID: {agent.id}")
    logger.info(f"Type: Code Interpreter Only (no function tools)")
    logger.info("\n✅ The agent will now use code interpreter to make HTTP calls to Azure Functions")
    
    return agent.id

if __name__ == "__main__":
    print(f"🎉 CEO Log Agent (Code Only) deployed with ID: {deploy_ceo_log_agent()}")