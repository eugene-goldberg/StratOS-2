"""
Deploy Preference Learning Agent as a connected agent
"""

import os
import sys
import asyncio
import logging
from pathlib import Path
from dotenv import load_dotenv
from azure.ai.projects.aio import AIProjectClient
from azure.identity.aio import DefaultAzureCredential
import uuid

# Add parent directory to path
current_dir = Path(__file__).parent
stratos_dir = current_dir.parent
connected_agents_dir = stratos_dir.parent
sys.path.append(str(connected_agents_dir))

from stratos.agents import preference_learning_agent_config

# Load environment variables
load_dotenv(Path(__file__).parent.parent.parent / '.env')

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def deploy_preference_learning_agent():
    """Deploy the Preference Learning agent"""
    
    connection_string = os.getenv("AZURE_AI_PROJECT_CONNECTION_STRING")
    if not connection_string:
        logger.error("Error: AZURE_AI_PROJECT_CONNECTION_STRING not found")
        return None
    
    try:
        async with DefaultAzureCredential() as credential:
            async with AIProjectClient(
                endpoint=connection_string,
                credential=credential
            ) as client:
                # Generate unique name
                unique_suffix = str(uuid.uuid4())[:8]
                agent_name = f"{preference_learning_agent_config.AGENT_NAME_PREFIX}-{unique_suffix}"
                
                # Create the agent
                logger.info(f"Deploying {agent_name}...")
                
                agent = await client.agents.create_agent(
                    model=preference_learning_agent_config.MODEL_NAME,
                    name=agent_name,
                    instructions=preference_learning_agent_config.AGENT_INSTRUCTIONS,
                    tools=preference_learning_agent_config.TOOLS
                )
                
                logger.info(f"✅ Agent deployed successfully!")
                logger.info(f"   Name: {agent.name}")
                logger.info(f"   ID: {agent.id}")
                
                # Save deployment info
                import json
                deployment_info = {
                    "agent_name": agent.name,
                    "agent_id": agent.id,
                    "deployment_time": datetime.now().isoformat(),
                    "model": preference_learning_agent_config.MODEL_NAME
                }
                
                deployment_file = stratos_dir / "archive" / f"preference_learning_deployment_{unique_suffix}.json"
                deployment_file.parent.mkdir(exist_ok=True)
                
                with open(deployment_file, 'w') as f:
                    json.dump(deployment_info, f, indent=2)
                
                logger.info(f"\n💾 Deployment info saved to: {deployment_file}")
                
                # Update .env file
                env_path = Path(__file__).parent.parent.parent / '.env'
                if env_path.exists():
                    logger.info("\nUpdating .env file with agent ID...")
                    with open(env_path, 'r') as f:
                        env_content = f.read()
                    
                    env_key = 'PREFERENCE_LEARNING_AGENT_ID'
                    if f'{env_key}=' in env_content:
                        lines = env_content.split('\n')
                        for i, line in enumerate(lines):
                            if line.startswith(f'{env_key}='):
                                lines[i] = f'{env_key}={agent.id}'
                        env_content = '\n'.join(lines)
                    else:
                        env_content += f'\n{env_key}={agent.id}\n'
                    
                    with open(env_path, 'w') as f:
                        f.write(env_content)
                
                return agent.id
                
    except Exception as e:
        logger.error(f"Error during deployment: {e}", exc_info=True)
        return None


if __name__ == "__main__":
    from datetime import datetime
    
    agent_id = asyncio.run(deploy_preference_learning_agent())
    if agent_id:
        print(f"\nAdd this to your orchestrator configuration:")
        print(f'PREFERENCE_LEARNING_AGENT_ID = "{agent_id}"')