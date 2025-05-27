#!/usr/bin/env python3
"""
Deploy the Unified StratOS Agent to Azure AI Agent Service.
This script uses the configuration from agents.unified.unified_stratos_agent.
"""

import asyncio
import os
import sys
import logging
from datetime import datetime, timezone
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [%(funcName)s] %(message)s')
logger = logging.getLogger(__name__)

# Add parent directories to path
current_dir = os.path.dirname(os.path.abspath(__file__))
agentic_dir = os.path.dirname(current_dir)
sys.path.insert(0, agentic_dir)

# Load environment variables
env_path = os.path.join(agentic_dir, '.env')
logger.info(f"Loading .env from: {env_path}")
load_dotenv(env_path)

# Import required modules
from azure.identity.aio import DefaultAzureCredential
from azure.ai.projects.aio import AIProjectClient
from agents.unified import get_unified_agent_config

async def deploy_unified_agent():
    """Deploy the Unified StratOS Agent to Azure AI Agent Service."""
    
    # Hardcode the endpoint since SDK discovery isn't working
    endpoint = "https://ai.azure.com/api/eastus/agents/v1.0/subscriptions/514bd6d3-2c02-45c6-a86f-29cf262a379a/resourceGroups/semantic-kernel-multi-agent-rg/providers/Microsoft.MachineLearningServices/workspaces/sk-multi-agent-project"
    
    # Get model deployment
    model_deployment = os.getenv("AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME", "gpt-35-turbo")
    
    logger.info(f"Using endpoint: {endpoint}")
    logger.info(f"Using model: {model_deployment}")
    
    # Get the unified agent configuration
    agent_config = get_unified_agent_config(model_deployment)
    
    # Create credential
    credential = DefaultAzureCredential()
    
    try:
        # Create AI Project client
        async with AIProjectClient(
            endpoint=endpoint,
            credential=credential,
            api_version="2024-12-01-preview"
        ) as client:
            logger.info("Successfully connected to Azure AI Agent Service")
            
            # Check if we should delete existing unified agent
            existing_id = os.getenv("STRATOS_UNIFIED_AGENT_ID")
            if existing_id:
                try:
                    logger.info(f"Attempting to delete existing unified agent: {existing_id}")
                    await client.agents.delete_agent(agent_id=existing_id)
                    logger.info("Existing unified agent deleted successfully")
                except Exception as e:
                    logger.warning(f"Could not delete existing unified agent: {e}")
            
            # Create the agent
            logger.info(f"Creating {agent_config['name']}...")
            agent = await client.agents.create_agent(
                name=agent_config["name"],
                instructions=agent_config["instructions"],
                model=agent_config["model"],
                tools=agent_config["tools"]
            )
            
            logger.info(f"✅ {agent_config['name']} deployed successfully!")
            logger.info(f"Agent ID: {agent.id}")
            logger.info(f"Name: {agent.name}")
            logger.info(f"Model: {agent.model}")
            logger.info(f"Tools: {len(agent.tools) if hasattr(agent, 'tools') else 0}")
            
            # List all tools
            if hasattr(agent, 'tools') and agent.tools:
                logger.info("\nDeployed Tools:")
                for i, tool in enumerate(agent.tools, 1):
                    if hasattr(tool, 'function'):
                        logger.info(f"  {i}. {tool.function.name}")
            
            logger.info(f"\n📝 Add this to your .env file:")
            logger.info(f'STRATOS_UNIFIED_AGENT_ID="{agent.id}"')
            
            # Also save to a deployment info file
            deployment_info = {
                "agent_id": agent.id,
                "agent_name": agent.name,
                "model": agent.model,
                "tool_count": len(agent.tools) if hasattr(agent, 'tools') else 0,
                "deployed_at": datetime.now(timezone.utc).isoformat(),
                "endpoint": endpoint
            }
            
            import json
            deployment_file = os.path.join(agentic_dir, "deployment_configs", "unified_agent_deployment.json")
            os.makedirs(os.path.dirname(deployment_file), exist_ok=True)
            with open(deployment_file, 'w') as f:
                json.dump(deployment_info, f, indent=2)
            logger.info(f"Deployment info saved to: {deployment_file}")
            
            return agent.id
            
    except Exception as e:
        logger.error(f"Error deploying unified agent: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    print("\n" + "="*80)
    print("DEPLOYING STRATOS UNIFIED AGENT")
    print("="*80 + "\n")
    
    agent_id = asyncio.run(deploy_unified_agent())
    
    if agent_id:
        print("\n" + "="*80)
        print("✅ DEPLOYMENT SUCCESSFUL")
        print("="*80)
        print(f"Unified Agent ID: {agent_id}")
        print("\nThis single agent combines all StratOS capabilities:")
        print("- Orchestrator logic built-in (no routing needed)")
        print("- All 12 specialist functions as direct tools")
        print("- Single conversation context")
        print("- No inter-agent communication overhead")
        print("="*80)
    else:
        print("\n" + "="*80)
        print("❌ DEPLOYMENT FAILED")
        print("="*80)