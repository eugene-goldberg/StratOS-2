"""
Deploy All StratOS Connected Agents (CEO Log, North Star, Memory Recall, Preference Learning)
This script deploys all four agents with proper delays to avoid rate limits
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
from agents import north_star_agent_config
from agents import memory_recall_agent_config
from agents import preference_learning_agent_config

# Load environment variables
load_dotenv(Path(__file__).parent.parent.parent / '.env')

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
DELAY_BETWEEN_AGENTS = 5  # seconds between agent deployments

async def deploy_all_stratos_agents():
    """Deploy all StratOS agents with orchestrator"""
    
    # Get connection string
    connection_string = os.getenv("AZURE_AI_PROJECT_CONNECTION_STRING")
    if not connection_string:
        logger.error("AZURE_AI_PROJECT_CONNECTION_STRING not found in environment")
        return None
    
    # Track deployment info
    deployment_info = {
        "deployment_time": datetime.now().isoformat(),
        "agents": {},
        "orchestrator": None
    }
    
    agent_ids = {}
    orchestrator_agent_id = None
    client_instance = None
    
    try:
        async with DefaultAzureCredential() as credential:
            async with AIProjectClient(
                endpoint=connection_string,
                credential=credential
            ) as client:
                client_instance = client
                
                # Generate unique suffix for this deployment
                import uuid
                unique_suffix = str(uuid.uuid4())[:8]
                
                # 1. Deploy CEO Log Agent
                logger.info("\n" + "="*60)
                logger.info("Deploying CEO Log Agent...")
                logger.info("="*60)
                
                ceo_log_name = f"{ceo_log_agent_config.AGENT_NAME_PREFIX}-{unique_suffix}"
                
                ceo_log_agent = await client.agents.create_agent(
                    model=ceo_log_agent_config.MODEL_NAME,
                    name=ceo_log_name,
                    instructions=ceo_log_agent_config.AGENT_INSTRUCTIONS,
                    tools=ceo_log_agent_config.TOOLS
                )
                
                agent_ids["ceo_log"] = ceo_log_agent.id
                deployment_info["agents"]["ceo_log"] = {
                    "name": ceo_log_agent.name,
                    "id": ceo_log_agent.id,
                    "type": "connected_agent"
                }
                logger.info(f"✅ CEO Log Agent deployed: {ceo_log_agent.name} (ID: {ceo_log_agent.id})")
                
                # Delay to avoid rate limits
                logger.info(f"Waiting {DELAY_BETWEEN_AGENTS} seconds before next deployment...")
                await asyncio.sleep(DELAY_BETWEEN_AGENTS)
                
                # 2. Deploy North Star Agent
                logger.info("\n" + "="*60)
                logger.info("Deploying North Star Agent...")
                logger.info("="*60)
                
                north_star_name = f"{north_star_agent_config.AGENT_NAME_PREFIX}-{unique_suffix}"
                
                north_star_agent = await client.agents.create_agent(
                    model=north_star_agent_config.MODEL_NAME,
                    name=north_star_name,
                    instructions=north_star_agent_config.AGENT_INSTRUCTIONS,
                    tools=north_star_agent_config.TOOLS
                )
                
                agent_ids["north_star"] = north_star_agent.id
                deployment_info["agents"]["north_star"] = {
                    "name": north_star_agent.name,
                    "id": north_star_agent.id,
                    "type": "connected_agent"
                }
                logger.info(f"✅ North Star Agent deployed: {north_star_agent.name} (ID: {north_star_agent.id})")
                
                # Delay to avoid rate limits
                logger.info(f"Waiting {DELAY_BETWEEN_AGENTS} seconds before next deployment...")
                await asyncio.sleep(DELAY_BETWEEN_AGENTS)
                
                # 3. Deploy Memory Recall Agent
                logger.info("\n" + "="*60)
                logger.info("Deploying Memory Recall Agent...")
                logger.info("="*60)
                
                memory_recall_name = f"{memory_recall_agent_config.AGENT_NAME_PREFIX}-{unique_suffix}"
                
                memory_recall_agent = await client.agents.create_agent(
                    model=memory_recall_agent_config.MODEL_NAME,
                    name=memory_recall_name,
                    instructions=memory_recall_agent_config.AGENT_INSTRUCTIONS,
                    tools=memory_recall_agent_config.TOOLS
                )
                
                agent_ids["memory_recall"] = memory_recall_agent.id
                deployment_info["agents"]["memory_recall"] = {
                    "name": memory_recall_agent.name,
                    "id": memory_recall_agent.id,
                    "type": "connected_agent"
                }
                logger.info(f"✅ Memory Recall Agent deployed: {memory_recall_agent.name} (ID: {memory_recall_agent.id})")
                
                # Delay to avoid rate limits
                logger.info(f"Waiting {DELAY_BETWEEN_AGENTS} seconds before next deployment...")
                await asyncio.sleep(DELAY_BETWEEN_AGENTS)
                
                # 4. Deploy Preference Learning Agent
                logger.info("\n" + "="*60)
                logger.info("Deploying Preference Learning Agent...")
                logger.info("="*60)
                
                preference_learning_name = f"{preference_learning_agent_config.AGENT_NAME_PREFIX}-{unique_suffix}"
                
                preference_learning_agent = await client.agents.create_agent(
                    model=preference_learning_agent_config.MODEL_NAME,
                    name=preference_learning_name,
                    instructions=preference_learning_agent_config.AGENT_INSTRUCTIONS,
                    tools=preference_learning_agent_config.TOOLS
                )
                
                agent_ids["preference_learning"] = preference_learning_agent.id
                deployment_info["agents"]["preference_learning"] = {
                    "name": preference_learning_agent.name,
                    "id": preference_learning_agent.id,
                    "type": "connected_agent"
                }
                logger.info(f"✅ Preference Learning Agent deployed: {preference_learning_agent.name} (ID: {preference_learning_agent.id})")
                
                # Delay to avoid rate limits
                logger.info(f"Waiting {DELAY_BETWEEN_AGENTS} seconds before orchestrator deployment...")
                await asyncio.sleep(DELAY_BETWEEN_AGENTS)
                
                # 5. Deploy Orchestrator with all connected agents
                logger.info("\n" + "="*60)
                logger.info("Deploying Orchestrator with all agents...")
                logger.info("="*60)
                
                # Create orchestrator instructions
                orchestrator_name = f"StratOSOrchestratorAgent-{unique_suffix}"
                orchestrator_instructions = """You are the StratOS Orchestrator, responsible for coordinating strategic planning activities by delegating to specialized agents. You MUST follow these delegation rules exactly.

CRITICAL PROTOCOL FOR ALL REQUESTS:
1. ALWAYS start your response with "I'll connect you with the [specialist type] specialist for [purpose]!"
2. Then IMMEDIATELY delegate to the appropriate specialist
3. The specialist will provide the actual response

Your connected specialists:
- CEO Log specialist (ceo_log_specialist): For CEO insights, log entries, tags, summaries
- North Star specialist (north_star_specialist): For vision, mission, values, purpose
- Memory Recall specialist (memory_recall_specialist): For historical context, patterns, past decisions
- Preference Learning specialist (preference_learning_specialist): For user preferences, personalization, recommendations

MANDATORY ROUTING RULES:
- CEO/executive/log/insight queries → ALWAYS use ceo_log_specialist
- Vision/mission/values/purpose queries → ALWAYS use north_star_specialist
- History/memory/recall/past queries → ALWAYS use memory_recall_specialist
- Preference/learning/adaptation/recommendation queries → ALWAYS use preference_learning_specialist

RESPONSE FORMAT:
ALWAYS respond with:
"I'll connect you with the [specialist name] specialist for [specific purpose]!"

Then let the specialist provide the detailed response."""
                
                # Create tools configuration
                tools = [
                    {
                        "type": "connected_agent",
                        "connected_agent": {
                            "name": f"ceo_log_specialist",
                            "id": agent_ids["ceo_log"]
                        }
                    },
                    {
                        "type": "connected_agent",
                        "connected_agent": {
                            "name": f"north_star_specialist",
                            "id": agent_ids["north_star"]
                        }
                    },
                    {
                        "type": "connected_agent",
                        "connected_agent": {
                            "name": f"memory_recall_specialist",
                            "id": agent_ids["memory_recall"]
                        }
                    },
                    {
                        "type": "connected_agent",
                        "connected_agent": {
                            "name": f"preference_learning_specialist",
                            "id": agent_ids["preference_learning"]
                        }
                    }
                ]
                
                orchestrator_agent = await client.agents.create_agent(
                    model="gpt-35-turbo",
                    name=orchestrator_name,
                    instructions=orchestrator_instructions,
                    tools=tools
                )
                
                orchestrator_agent_id = orchestrator_agent.id
                deployment_info["orchestrator"] = {
                    "name": orchestrator_agent.name,
                    "id": orchestrator_agent.id,
                    "connected_agents": list(agent_ids.keys())
                }
                
                logger.info(f"✅ Orchestrator deployed: {orchestrator_agent.name} (ID: {orchestrator_agent.id})")
                logger.info(f"   Connected to: {', '.join(agent_ids.keys())}")
                
                # Save deployment info
                archive_dir = Path(__file__).parent.parent / "archive"
                archive_dir.mkdir(exist_ok=True)
                
                deployment_file = archive_dir / "stratos_deployment_info.json"
                with open(deployment_file, 'w') as f:
                    json.dump(deployment_info, f, indent=2)
                
                logger.info(f"\n💾 Deployment info saved to: {deployment_file}")
                
                # Update .env file with agent IDs
                env_path = Path(__file__).parent.parent.parent / '.env'
                if env_path.exists():
                    logger.info("\nUpdating .env file with agent IDs...")
                    with open(env_path, 'r') as f:
                        env_content = f.read()
                    
                    # Update or add each agent ID
                    for key, agent_id in agent_ids.items():
                        env_key = f"{key.upper()}_AGENT_ID"
                        if f'{env_key}=' in env_content:
                            lines = env_content.split('\n')
                            for i, line in enumerate(lines):
                                if line.startswith(f'{env_key}='):
                                    lines[i] = f'{env_key}={agent_id}'
                            env_content = '\n'.join(lines)
                        else:
                            env_content += f'\n{env_key}={agent_id}\n'
                    
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
                logger.info("ALL STRATOS AGENTS DEPLOYED SUCCESSFULLY!")
                logger.info("="*60)
                logger.info(f"CEO Log Agent ID: {agent_ids['ceo_log']}")
                logger.info(f"North Star Agent ID: {agent_ids['north_star']}")
                logger.info(f"Memory Recall Agent ID: {agent_ids['memory_recall']}")
                logger.info(f"Preference Learning Agent ID: {agent_ids['preference_learning']}")
                logger.info(f"Orchestrator Agent ID: {orchestrator_agent_id}")
                logger.info("="*60)
                
                return deployment_info
                
    except Exception as e:
        logger.error(f"Error during deployment: {e}", exc_info=True)
        
        # Cleanup on error
        if client_instance and (any(agent_ids.values()) or orchestrator_agent_id):
            logger.info("\nCleaning up agents due to error...")
            
            # Delete orchestrator first
            if orchestrator_agent_id:
                try:
                    await client_instance.agents.delete_agent(agent_id=orchestrator_agent_id)
                    logger.info(f"Deleted orchestrator: {orchestrator_agent_id}")
                except Exception as e:
                    logger.error(f"Error deleting orchestrator {orchestrator_agent_id}: {e}")
            
            # Delete agents
            for agent_name, agent_id in agent_ids.items():
                if agent_id:
                    try:
                        await client_instance.agents.delete_agent(agent_id=agent_id)
                        logger.info(f"Deleted {agent_name}: {agent_id}")
                    except Exception as e:
                        logger.error(f"Error deleting {agent_name} {agent_id}: {e}")
        
        return None

if __name__ == "__main__":
    asyncio.run(deploy_all_stratos_agents())