#!/usr/bin/env python3
"""
Deploy North Star Agent with OpenAPI Tool Definition
Following the exact pattern from the guidance document
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

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# Configuration
AGENT_NAME = "NorthStarAgentOpenAPI"
MODEL_NAME = "gpt-35-turbo"
OPENAPI_SPEC_FILE = Path(__file__).parent.parent / "north_star_openapi.json"

AGENT_INSTRUCTIONS = """You are the North Star Agent for StratOS, responsible for defining and maintaining the organization's strategic foundation.

You have direct access to Azure Functions through OpenAPI tools. When users ask you to manage their North Star elements, use the appropriate operations:

- ManagePurpose: To get or set the organizational purpose
- ManageVision: To get or set the organizational vision
- ManageValues: To add, remove, or list organizational values
- ManageStrategicGoals: To create, update, delete, get, or list strategic goals
- ValidateAlignment: To check if an element aligns with the North Star
- GetNorthStarSummary: To get a complete overview of the North Star

IMPORTANT: The Azure AI Agent Service will handle all HTTP communication directly. You just need to decide when to use each operation.

Your responsibilities:
1. Guide organizations in defining clear purpose and vision
2. Help articulate and maintain core organizational values
3. Structure strategic goals in meaningful hierarchies
4. Ensure all activities align with the North Star
5. Provide strategic clarity during decision-making"""

def deploy_north_star_openapi_agent():
    """Deploy North Star Agent with OpenAPI Tool Definition"""
    
    logger.info("Deploying North Star Agent with OpenAPI Tools")
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
    
    # Load OpenAPI specification
    with open(OPENAPI_SPEC_FILE, "r") as f:
        openapi_spec = json.load(f)  # Load as JSON object
    
    logger.info(f"Creating agent: {agent_name}")
    logger.info(f"Model: {MODEL_NAME}")
    logger.info(f"OpenAPI spec loaded from: {OPENAPI_SPEC_FILE}")
    
    # Create OpenAPI tool definition
    # Using the exact structure from the guidance document
    openapi_tool = {
        "type": "openapi",
        "openapi": {
            "name": "NorthStarFunctions",
            "spec": openapi_spec,  # The spec as a dictionary
            "auth": {
                "type": "none"  # Functions handle their own auth via headers
            }
        }
    }
    
    # Create the agent
    agent = client.agents.create_agent(
        name=agent_name,
        instructions=AGENT_INSTRUCTIONS,
        tools=[openapi_tool],
        model=MODEL_NAME
    )
    
    logger.info(f"\n✅ North Star OpenAPI Agent deployed successfully!")
    logger.info(f"   Agent ID: {agent.id}")
    logger.info(f"   Name: {agent.name}")
    logger.info(f"   Model: {agent.model}")
    
    # Save deployment info
    deployment_info = {
        "agent_id": agent.id,
        "agent_name": agent.name,
        "deployment_time": datetime.now().isoformat(),
        "model": agent.model,
        "tool_type": "openapi",
        "openapi_spec": "north_star_openapi.json",
        "azure_functions": {
            "app_name": "stratos-north-star-functions",
            "base_url": "https://stratos-north-star-functions.azurewebsites.net",
            "endpoints": [
                "/api/ManagePurpose",
                "/api/ManageVision",
                "/api/ManageValues",
                "/api/ManageStrategicGoals",
                "/api/ValidateAlignment",
                "/api/GetNorthStarSummary"
            ],
            "auth_method": "x-functions-key header (defined in OpenAPI spec)"
        },
        "cosmos_db": {
            "account": "stratos-ceo-logs-db",
            "database": "StratOSData",
            "container": "NorthStar"
        }
    }
    
    # Save to file
    deployment_file = Path(__file__).parent / f"north_star_openapi_deployment_{timestamp}.json"
    with open(deployment_file, 'w') as f:
        json.dump(deployment_info, f, indent=2)
    
    logger.info(f"\n💾 Deployment info saved to: {deployment_file}")
    
    logger.info("\n" + "="*70)
    logger.info("📋 DEPLOYMENT SUMMARY")
    logger.info("="*70)
    logger.info(f"Agent Name: {agent.name}")
    logger.info(f"Agent ID: {agent.id}")
    logger.info(f"Type: OpenAPI Tools")
    logger.info(f"\n✅ The agent will:")
    logger.info("  - Make direct HTTP POST calls to Azure Functions")
    logger.info("  - Use the OpenAPI specification to understand endpoints")
    logger.info("  - Include function keys from the OpenAPI security scheme")
    logger.info("  - Handle all HTTP communication internally")
    logger.info("\n⚡ CRITICAL BEHAVIOR:")
    logger.info("   1. User sends message to agent")
    logger.info("   2. Agent decides to use a tool")
    logger.info("   3. Azure AI Agent Service makes HTTP call directly")
    logger.info("   4. Test client NEVER makes function calls!")
    
    return agent.id

if __name__ == "__main__":
    agent_id = deploy_north_star_openapi_agent()
    print(f"\n🎉 North Star OpenAPI Agent deployed with ID: {agent_id}")
    print("\n📝 The agent makes direct HTTP calls to Azure Functions!")