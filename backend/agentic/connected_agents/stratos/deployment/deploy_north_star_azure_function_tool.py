#!/usr/bin/env python3
"""
Deploy North Star Agent with azure_function Tool Type
Testing if azure_function tool type enables direct calls
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
AGENT_NAME = "NorthStarAgentAzureFunc"
MODEL_NAME = "gpt-35-turbo"

# Get actual function app details
FUNCTION_APP_NAME = "stratos-north-star-functions"
FUNCTION_APP_URL = f"https://{FUNCTION_APP_NAME}.azurewebsites.net"

AGENT_INSTRUCTIONS = """You are the North Star Agent for StratOS, responsible for defining and maintaining the organization's strategic foundation.

You have direct access to Azure Functions. When users ask you to manage their North Star elements, use the appropriate functions:

- ManagePurpose: To get or set the organizational purpose
- ManageVision: To get or set the organizational vision
- ManageValues: To add, remove, or list organizational values
- ManageStrategicGoals: To create, update, delete, get, or list strategic goals
- ValidateAlignment: To check if an element aligns with the North Star
- GetNorthStarSummary: To get a complete overview of the North Star

IMPORTANT: You will directly call these Azure Functions. The agent service handles all HTTP communication.

Your responsibilities:
1. Guide organizations in defining clear purpose and vision
2. Help articulate and maintain core organizational values
3. Structure strategic goals in meaningful hierarchies
4. Ensure all activities align with the North Star
5. Provide strategic clarity during decision-making"""

def deploy_north_star_azure_function_agent():
    """Deploy North Star Agent with azure_function Tool Type"""
    
    logger.info("Deploying North Star Agent with azure_function Tools")
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
    logger.info(f"Function App: {FUNCTION_APP_NAME}")
    
    # Create azure_function tools
    tools = []
    
    # Define each Azure Function as a tool
    functions = [
        {
            "name": "ManagePurpose",
            "endpoint": "/api/ManagePurpose",
            "description": "Manage organizational purpose (get or set)",
            "key": "gPXyuj42jT_BnlDhImnO1gaV_xayICaGrxf2NoTA1_hVAzFuSjMcqQ=="
        },
        {
            "name": "ManageVision",
            "endpoint": "/api/ManageVision",
            "description": "Manage organizational vision (get or set)",
            "key": "hxaRNlD2FmGt9IHzHGXhtVavLrHvlDVkMtDfAe_j3cwyAzFuiAd75Q=="
        },
        {
            "name": "ManageValues",
            "endpoint": "/api/ManageValues",
            "description": "Manage organizational values (add, remove, list)",
            "key": "NliL5fD1aEmXoLSqoa1NSCzDbN2PEeSlCUYZAS6pxcc4AzFujGLDpw=="
        },
        {
            "name": "ManageStrategicGoals",
            "endpoint": "/api/ManageStrategicGoals",
            "description": "Manage strategic goals with hierarchy",
            "key": "kaS2TH5L7__RTKaLc8XfoxHDVW9AP8wE2p_Ei3lBQNvzAzFu4mIw4g=="
        },
        {
            "name": "ValidateAlignment",
            "endpoint": "/api/ValidateAlignment",
            "description": "Validate alignment with North Star elements",
            "key": "968fvYsjeBk7tEbv-0Bvt7RniJcynmitd_JR3Y-I5tHnAzFuZxFbwg=="
        },
        {
            "name": "GetNorthStarSummary",
            "endpoint": "/api/GetNorthStarSummary",
            "description": "Get complete North Star summary",
            "key": "-W8ykJ6kkUyeLQCZXNklZqdoL1fOFhw1dvLQniJtqYvwAzFunTkKNA=="
        }
    ]
    
    for func in functions:
        tool = {
            "type": "azure_function",
            "azure_function": {
                "name": func["name"],
                "description": func["description"],
                "function_app_name": FUNCTION_APP_NAME,
                "function_name": func["name"],
                "http_trigger_url": f"{FUNCTION_APP_URL}{func['endpoint']}",
                "function_key": func["key"]
            }
        }
        tools.append(tool)
    
    logger.info(f"Configured {len(tools)} azure_function tools")
    
    # Create the agent
    agent = client.agents.create_agent(
        name=agent_name,
        instructions=AGENT_INSTRUCTIONS,
        tools=tools,
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
        "tool_type": "azure_function",
        "azure_functions": {
            "app_name": FUNCTION_APP_NAME,
            "base_url": FUNCTION_APP_URL,
            "tools": [f["name"] for f in functions]
        },
        "cosmos_db": {
            "account": "stratos-ceo-logs-db",
            "database": "StratOSData",
            "container": "NorthStar"
        }
    }
    
    # Save to file
    deployment_file = Path(__file__).parent / f"north_star_azure_func_tool_deployment_{timestamp}.json"
    with open(deployment_file, 'w') as f:
        json.dump(deployment_info, f, indent=2)
    
    logger.info(f"\n💾 Deployment info saved to: {deployment_file}")
    
    logger.info("\n" + "="*70)
    logger.info("📋 DEPLOYMENT SUMMARY")
    logger.info("="*70)
    logger.info(f"Agent Name: {agent.name}")
    logger.info(f"Agent ID: {agent.id}")
    logger.info(f"Type: azure_function Tools")
    logger.info(f"\n✅ Expected behavior:")
    logger.info("  - Agent receives user request")
    logger.info("  - Agent decides to use azure_function tool")
    logger.info("  - Azure AI Agent Service makes HTTP call directly")
    logger.info("  - Test client does NOT handle function calls")
    
    return agent.id

if __name__ == "__main__":
    agent_id = deploy_north_star_azure_function_agent()
    print(f"\n🎉 North Star Agent deployed with azure_function tools: {agent_id}")
    print("\n📝 Testing direct function calls next...")