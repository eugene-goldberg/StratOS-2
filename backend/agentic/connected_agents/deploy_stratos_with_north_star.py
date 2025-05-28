"""
Deploy StratOS Agents with North Star as Connected Agents
Following the weather agent pattern for all StratOS agents
"""

import asyncio
import os
import sys
import json
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from connected_agents directory
load_dotenv(Path(__file__).parent / '.env')

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from azure.ai.projects.aio import AIProjectClient
from azure.identity.aio import DefaultAzureCredential

# Import agent configurations
from backend.agentic.connected_agents import ceo_log_agent_config
from backend.agentic.connected_agents import north_star_agent_config
from backend.agentic.connected_agents import orchestrator_agent_config_with_north_star as orchestrator_config

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def deploy_stratos_agents():
    """Deploy StratOS agents as connected agents following the weather agent pattern"""
    
    # Deployment tracking
    deployment_info = {
        "deployment_time": datetime.now().isoformat(),
        "agents": {},
        "orchestrator": None
    }
    
    ceo_log_agent_id = None
    north_star_agent_id = None
    orchestrator_agent_id = None
    client_instance = None
    
    try:
        # Get model deployment name from environment
        model_deployment_name = os.getenv("MODEL_DEPLOYMENT_NAME", "gpt-35-turbo")
        logger.info(f"Using model deployment: {model_deployment_name}")
        
        # Get connection string from environment
        connection_string = os.getenv("AZURE_AI_PROJECT_CONNECTION_STRING")
        if not connection_string:
            logger.error("AZURE_AI_PROJECT_CONNECTION_STRING not found in environment")
            return
        
        logger.info(f"Using Azure AI Project connection")
        
        async with DefaultAzureCredential() as credential:
            async with AIProjectClient(
                endpoint=connection_string,
                credential=credential
            ) as client:
                client_instance = client
                
                # 1. Deploy CEO Log Agent (following weather agent pattern)
                ceo_log_agent_name = f"{ceo_log_agent_config.AGENT_NAME_PREFIX}-{os.urandom(4).hex()}"
                logger.info(f"Creating CEO Log Agent: {ceo_log_agent_name}...")
                
                ceo_log_agent_def = await client.agents.create_agent(
                    model=model_deployment_name,
                    name=ceo_log_agent_name,
                    instructions=ceo_log_agent_config.AGENT_INSTRUCTIONS,
                    tools=ceo_log_agent_config.TOOLS if hasattr(ceo_log_agent_config, 'TOOLS') else None
                )
                ceo_log_agent_id = ceo_log_agent_def.id
                logger.info(f"CEO Log Agent '{ceo_log_agent_name}' created with ID: {ceo_log_agent_id}")
                
                deployment_info["agents"]["ceo_log"] = {
                    "name": ceo_log_agent_name,
                    "id": ceo_log_agent_id,
                    "type": "connected_agent"
                }
                
                # 2. Deploy North Star Agent (following weather agent pattern)
                north_star_agent_name = f"{north_star_agent_config.AGENT_NAME_PREFIX}-{os.urandom(4).hex()}"
                logger.info(f"Creating North Star Agent: {north_star_agent_name}...")
                
                north_star_agent_def = await client.agents.create_agent(
                    model=model_deployment_name,
                    name=north_star_agent_name,
                    instructions=north_star_agent_config.AGENT_INSTRUCTIONS,
                    tools=north_star_agent_config.TOOLS if hasattr(north_star_agent_config, 'TOOLS') else None
                )
                north_star_agent_id = north_star_agent_def.id
                logger.info(f"North Star Agent '{north_star_agent_name}' created with ID: {north_star_agent_id}")
                
                deployment_info["agents"]["north_star"] = {
                    "name": north_star_agent_name,
                    "id": north_star_agent_id,
                    "type": "connected_agent"
                }
                
                # 3. Define tool descriptions
                ceo_log_tool_description = (
                    "A strategic insights and log entry management expert for CEO communications. "
                    "Use this tool for processing executive thoughts, generating tags, creating summaries, "
                    "extracting strategic insights, and managing CEO log entries. It handles strategic planning, "
                    "team leadership, market analysis, risk assessment, and innovation topics."
                )
                
                north_star_tool_description = (
                    "A strategic foundation expert for organizational purpose, vision, values, and goals. "
                    "Use this tool for defining purpose statements, creating vision, managing organizational values, "
                    "structuring strategic goals in hierarchies, validating alignment with North Star elements, "
                    "and providing comprehensive strategic foundation overviews."
                )
                
                # 4. Create Orchestrator with both tools
                orchestrator_name = f"{orchestrator_config.AGENT_NAME_PREFIX}-{os.urandom(4).hex()}"
                logger.info(f"Creating StratOS Orchestrator: {orchestrator_name}...")
                
                # Convert tools to format expected by API
                tools = []
                
                # Add CEO Log tool
                tools.append({
                    "type": "connected_agent",
                    "connected_agent": {
                        "id": ceo_log_agent_id,
                        "name": "ceo_log_specialist",
                        "description": ceo_log_tool_description
                    }
                })
                
                # Add North Star tool
                tools.append({
                    "type": "connected_agent",
                    "connected_agent": {
                        "id": north_star_agent_id,
                        "name": "north_star_specialist",
                        "description": north_star_tool_description
                    }
                })
                
                # Create orchestrator with tools
                orchestrator_agent_def = await client.agents.create_agent(
                    model=model_deployment_name,
                    name=orchestrator_name,
                    instructions=orchestrator_config.AGENT_INSTRUCTIONS,
                    tools=tools
                )
                orchestrator_agent_id = orchestrator_agent_def.id
                logger.info(f"Orchestrator '{orchestrator_name}' created with ID: {orchestrator_agent_id}")
                
                deployment_info["orchestrator"] = {
                    "name": orchestrator_name,
                    "id": orchestrator_agent_id,
                    "connected_agents": ["ceo_log", "north_star"]
                }
                
                # 5. Save deployment info
                deployment_file = Path(__file__).parent / "stratos_deployment_info.json"
                with open(deployment_file, 'w') as f:
                    json.dump(deployment_info, f, indent=2)
                logger.info(f"Deployment info saved to: {deployment_file}")
                
                # 6. Update .env file with new agent IDs
                env_path = project_root / '.env'
                env_content = ""
                if env_path.exists():
                    with open(env_path, 'r') as f:
                        env_content = f.read()
                
                # Update or add CEO Log Agent ID
                if 'CEO_LOG_AGENT_ID=' in env_content:
                    lines = env_content.split('\n')
                    for i, line in enumerate(lines):
                        if line.startswith('CEO_LOG_AGENT_ID='):
                            lines[i] = f'CEO_LOG_AGENT_ID={ceo_log_agent_id}'
                    env_content = '\n'.join(lines)
                else:
                    env_content += f'\nCEO_LOG_AGENT_ID={ceo_log_agent_id}\n'
                
                # Update or add North Star Agent ID
                if 'NORTH_STAR_AGENT_ID=' in env_content:
                    lines = env_content.split('\n')
                    for i, line in enumerate(lines):
                        if line.startswith('NORTH_STAR_AGENT_ID='):
                            lines[i] = f'NORTH_STAR_AGENT_ID={north_star_agent_id}'
                    env_content = '\n'.join(lines)
                else:
                    env_content += f'\nNORTH_STAR_AGENT_ID={north_star_agent_id}\n'
                
                # Update or add Orchestrator ID
                if 'STRATOS_ORCHESTRATOR_ID=' in env_content:
                    lines = env_content.split('\n')
                    for i, line in enumerate(lines):
                        if line.startswith('STRATOS_ORCHESTRATOR_ID='):
                            lines[i] = f'STRATOS_ORCHESTRATOR_ID={orchestrator_agent_id}'
                    env_content = '\n'.join(lines)
                else:
                    env_content += f'\nSTRATOS_ORCHESTRATOR_ID={orchestrator_agent_id}\n'
                
                with open(env_path, 'w') as f:
                    f.write(env_content)
                
                logger.info("\n" + "="*60)
                logger.info("STRATOS DEPLOYMENT SUCCESSFUL!")
                logger.info("="*60)
                logger.info(f"CEO Log Agent ID: {ceo_log_agent_id}")
                logger.info(f"North Star Agent ID: {north_star_agent_id}")
                logger.info(f"Orchestrator Agent ID: {orchestrator_agent_id}")
                logger.info("="*60)
                
                return deployment_info
                
    except Exception as e:
        logger.error(f"Error during deployment: {e}", exc_info=True)
        
    finally:
        # Cleanup on error
        if client_instance and any([ceo_log_agent_id, north_star_agent_id, orchestrator_agent_id]):
            logger.info("\nCleaning up agents...")
            for agent_id in [orchestrator_agent_id, north_star_agent_id, ceo_log_agent_id]:
                if agent_id:
                    try:
                        await client_instance.agents.delete_agent(agent_id=agent_id)
                        logger.info(f"Deleted agent: {agent_id}")
                    except Exception as e:
                        logger.error(f"Error deleting agent {agent_id}: {e}")

if __name__ == "__main__":
    asyncio.run(deploy_stratos_agents())