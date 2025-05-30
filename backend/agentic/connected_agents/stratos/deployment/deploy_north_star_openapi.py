#!/usr/bin/env python3
"""
Deploy North Star Agent with OpenAPI Tool Definition
Agent calls Azure Functions directly via OpenAPI specification
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
from azure.ai.agents.models import (
    OpenApiToolDefinition,
    OpenApiConnectionAuthDetails,
    OpenApiConnectionSecurityScheme,
    Agent
)

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

# Note: In production, you would create a connection in Azure AI Studio
# with the function keys. For now, we'll use a single key for simplicity
FUNCTION_KEY = "gPXyuj42jT_BnlDhImnO1gaV_xayICaGrxf2NoTA1_hVAzFuSjMcqQ=="

AGENT_INSTRUCTIONS = """You are the North Star Agent for StratOS, responsible for defining and maintaining the organization's strategic foundation.

You have direct access to Azure Functions through OpenAPI tools. When users ask you to manage their North Star elements, use the appropriate tools:

- ManagePurpose: To get or set the organizational purpose
- ManageVision: To get or set the organizational vision
- ManageValues: To add, remove, or list organizational values
- ManageStrategicGoals: To create, update, delete, get, or list strategic goals
- ValidateAlignment: To check if an element aligns with the North Star
- GetNorthStarSummary: To get a complete overview of the North Star

IMPORTANT: 
- Always use organizationId from the user context or ask for it if not provided
- When setting purpose or vision, use action="set" and provide the content
- When adding values, use action="add" with valueName and valueDescription
- When creating goals, use action="create" with goalName, goalDescription, and optionally targetDate

Your responsibilities:
1. Guide organizations in defining clear purpose and vision
2. Help articulate and maintain core organizational values
3. Structure strategic goals in meaningful hierarchies
4. Ensure all activities align with the North Star
5. Provide strategic clarity during decision-making

Response format:
- Use clear, strategic language appropriate for executives
- Provide actionable insights, not just data
- Connect all elements to create coherent strategy
- Highlight gaps or misalignments constructively
- Suggest next steps for strategic development"""

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
        openapi_spec_content = f.read()
    
    logger.info(f"Creating agent: {agent_name}")
    logger.info(f"Model: {MODEL_NAME}")
    logger.info(f"OpenAPI spec loaded from: {OPENAPI_SPEC_FILE}")
    
    # Create OpenAPI tool definition
    # Note: In production, you would use a proper connection for auth
    # For now, we'll create a tool without auth (functions will validate keys)
    openapi_tool = OpenApiToolDefinition(
        spec=openapi_spec_content,
        auth=None  # Functions handle their own auth via x-functions-key header
    )
    
    # Create the agent
    agent_config = Agent(
        name=agent_name,
        instructions=AGENT_INSTRUCTIONS,
        model_deployment_name=MODEL_NAME,
        tools=[openapi_tool]
    )
    
    agent = client.agents.create_or_update(agent_config)
    
    logger.info(f"\n✅ North Star OpenAPI Agent deployed successfully!")
    logger.info(f"   Agent ID: {agent.id}")
    logger.info(f"   Name: {agent.name}")
    logger.info(f"   Model: {MODEL_NAME}")
    
    # Save deployment info
    deployment_info = {
        "agent_id": agent.id,
        "agent_name": agent.name,
        "deployment_time": datetime.now().isoformat(),
        "model": MODEL_NAME,
        "tool_type": "OpenAPI",
        "openapi_spec": "north_star_openapi.json",
        "azure_functions": {
            "app_name": "stratos-north-star-functions",
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
    deployment_file = Path(__file__).parent / f"north_star_openapi_deployment_{timestamp}.json"
    with open(deployment_file, 'w') as f:
        json.dump(deployment_info, f, indent=2)
    
    logger.info(f"\n💾 Deployment info saved to: {deployment_file}")
    
    logger.info("\n" + "="*70)
    logger.info("📋 DEPLOYMENT SUMMARY")
    logger.info("="*70)
    logger.info(f"Agent Name: {agent.name}")
    logger.info(f"Agent ID: {agent.id}")
    logger.info(f"Type: OpenAPI Tools (Agent calls Azure Functions directly)")
    logger.info(f"\n✅ The agent can now:")
    logger.info("  - Directly call Azure Functions using OpenAPI specification")
    logger.info("  - Manage organizational purpose and vision")
    logger.info("  - Define and maintain core values")
    logger.info("  - Create and organize strategic goals hierarchically")
    logger.info("  - Validate alignment of initiatives with North Star")
    logger.info("  - Provide comprehensive strategic foundation summaries")
    logger.info("\n⚡ CRITICAL: The agent makes HTTP calls directly to Azure Functions!")
    logger.info("   The test client does NOT make any function calls!")
    
    return agent.id

if __name__ == "__main__":
    agent_id = deploy_north_star_openapi_agent()
    print(f"\n🎉 North Star OpenAPI Agent deployed with ID: {agent_id}")
    print("\n📝 Note: Function authentication is handled by the Azure Functions themselves")
    print("   Each function validates its own x-functions-key header")