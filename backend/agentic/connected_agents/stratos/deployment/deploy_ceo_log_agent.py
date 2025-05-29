#!/usr/bin/env python3
"""
Deploy CEO Log Agent with Azure Function Integration
This script deploys the CEO Log agent with proper function calling setup
"""

import os
import sys
import asyncio
import logging
import json
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from azure.ai.projects.aio import AIProjectClient
from azure.identity.aio import DefaultAzureCredential

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from agents import ceo_log_agent_config

# Load environment variables
load_dotenv(Path(__file__).parent.parent.parent / '.env')

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def deploy_ceo_log_agent():
    """Deploy CEO Log agent with Azure Function integration"""
    
    logger.info("Deploying CEO Log Agent with Azure Function Integration")
    logger.info("=" * 70)
    
    # Get connection string
    connection_string = os.getenv("AZURE_AI_PROJECT_CONNECTION_STRING")
    if not connection_string:
        logger.error("AZURE_AI_PROJECT_CONNECTION_STRING not found in environment")
        return None
    
    try:
        async with DefaultAzureCredential() as credential:
            async with AIProjectClient(
                endpoint=connection_string,
                credential=credential
            ) as client:
                
                # Generate unique name
                import uuid
                unique_suffix = str(uuid.uuid4())[:8]
                agent_name = f"{ceo_log_agent_config.AGENT_NAME_PREFIX}-{unique_suffix}"
                
                logger.info(f"Creating agent: {agent_name}")
                logger.info(f"Model: {ceo_log_agent_config.MODEL_NAME}")
                logger.info(f"Tools: {len(ceo_log_agent_config.TOOLS)} configured")
                
                # Create the agent
                agent = await client.agents.create_agent(
                    model=ceo_log_agent_config.MODEL_NAME,
                    name=agent_name,
                    instructions=ceo_log_agent_config.AGENT_INSTRUCTIONS,
                    tools=ceo_log_agent_config.TOOLS
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
                    "has_azure_function_integration": True,
                    "azure_functions": {
                        "base_url": ceo_log_agent_config.AZURE_FUNCTION_BASE,
                        "endpoints": list(ceo_log_agent_config.AZURE_FUNCTION_KEYS.keys())
                    }
                }
                
                # Save to deployment directory
                deployment_dir = Path(__file__).parent
                deployment_file = deployment_dir / f"ceo_log_agent_deployment_{unique_suffix}.json"
                
                with open(deployment_file, 'w') as f:
                    json.dump(deployment_info, f, indent=2)
                
                logger.info(f"\n💾 Deployment info saved to: {deployment_file}")
                
                # Update .env with agent ID
                env_path = Path(__file__).parent.parent.parent / '.env'
                if env_path.exists():
                    logger.info("\nUpdating .env file with CEO Log Agent ID...")
                    with open(env_path, 'r') as f:
                        env_content = f.read()
                    
                    # Update or add CEO_LOG_AGENT_ID
                    if 'CEO_LOG_AGENT_ID=' in env_content:
                        lines = env_content.split('\n')
                        for i, line in enumerate(lines):
                            if line.startswith('CEO_LOG_AGENT_ID='):
                                lines[i] = f'CEO_LOG_AGENT_ID={agent.id}'
                        env_content = '\n'.join(lines)
                    else:
                        env_content += f'\nCEO_LOG_AGENT_ID={agent.id}\n'
                    
                    with open(env_path, 'w') as f:
                        f.write(env_content)
                
                logger.info("\n" + "="*70)
                logger.info("📋 DEPLOYMENT SUMMARY")
                logger.info("="*70)
                logger.info(f"Agent Name: {agent.name}")
                logger.info(f"Agent ID: {agent.id}")
                logger.info(f"Model: {agent.model}")
                logger.info("\nAzure Function Endpoints:")
                for func_name in ceo_log_agent_config.AZURE_FUNCTION_KEYS:
                    logger.info(f"  - {func_name}: {ceo_log_agent_config.AZURE_FUNCTION_BASE}/{func_name}")
                
                logger.info("\n💡 Test the agent with:")
                logger.info("  1. 'Save this CEO log: Had a productive meeting with the sales team. Q1 revenue exceeded targets by 20%.'")
                logger.info("  2. 'Search for entries about team challenges'")
                logger.info("  3. 'Analyze my logs from this week focusing on risks'")
                logger.info("  4. 'Get insights from my recent entries'")
                
                logger.info("\n✅ The agent is now ready to:")
                logger.info("  - Save CEO log entries to Cosmos DB")
                logger.info("  - Search through historical entries")
                logger.info("  - Analyze logs for patterns and insights")
                logger.info("  - Extract strategic insights from entries")
                
                return agent
                
    except Exception as e:
        logger.error(f"Error during deployment: {e}", exc_info=True)
        return None

if __name__ == "__main__":
    agent = asyncio.run(deploy_ceo_log_agent())
    if agent:
        print(f"\n🎉 CEO Log Agent deployed successfully with ID: {agent.id}")
    else:
        print("\n❌ CEO Log Agent deployment failed")