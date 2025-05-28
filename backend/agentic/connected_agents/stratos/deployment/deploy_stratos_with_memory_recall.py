"""
Deploy StratOS Connected Agents including Memory Recall Agent
This script deploys CEO Log, North Star, Memory Recall agents and the orchestrator
"""

import os
import asyncio
import logging
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any
from dotenv import load_dotenv
from azure.ai.projects.aio import AIProjectClient
from azure.identity.aio import DefaultAzureCredential
import sys

# Load environment variables from connected_agents directory
load_dotenv(Path(__file__).parent.parent.parent / '.env')

# Add stratos agents to path
stratos_root = Path(__file__).parent.parent
sys.path.insert(0, str(stratos_root))

from agents import ceo_log_agent_config
from agents import north_star_agent_config
from agents import memory_recall_agent_config
from agents import orchestrator_agent_config_with_memory_recall

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Azure AI configuration
PROJECT_CONNECTION_STRING = os.getenv("AZURE_AI_PROJECT_CONNECTION_STRING")
MODEL_DEPLOYMENT_NAME = os.getenv("MODEL_DEPLOYMENT_NAME", "gpt-35-turbo")

def save_deployment_info(info: Dict[str, Any]):
    """Save deployment information to archive"""
    archive_dir = Path(__file__).parent.parent / "archive"
    archive_dir.mkdir(exist_ok=True)
    
    filename = archive_dir / "stratos_deployment_info.json"
    with open(filename, 'w') as f:
        json.dump(info, f, indent=2, default=str)
    logger.info(f"💾 Deployment info saved to {filename}")

async def deploy_agents():
    """Deploy all StratOS agents including Memory Recall"""
    deployment_info = {
        "deployment_time": datetime.utcnow().isoformat(),
        "agents": {},
        "orchestrator": {}
    }
    
    try:
        logger.info("=== Starting StratOS Agents Deployment (with Memory Recall) ===")
        
        # Check connection string
        if not PROJECT_CONNECTION_STRING:
            logger.error("AZURE_PROJECT_CONNECTION_STRING not found in environment")
            return
        
        logger.info(f"Using Azure AI Project connection")
        
        async with DefaultAzureCredential() as credential:
            async with AIProjectClient(
                endpoint=PROJECT_CONNECTION_STRING,
                credential=credential
            ) as client:
                
                # 1. Deploy CEO Log Agent
                logger.info("\n📝 Deploying CEO Log Agent...")
                ceo_log_agent_name = f"{ceo_log_agent_config.AGENT_NAME_PREFIX}-{os.urandom(4).hex()}"
                ceo_log_agent_def = await client.agents.create_agent(
                    model=MODEL_DEPLOYMENT_NAME,
                    name=ceo_log_agent_name,
                    instructions=ceo_log_agent_config.AGENT_INSTRUCTIONS,
                    tools=ceo_log_agent_config.TOOLS
                )
                logger.info(f"✅ CEO Log Agent deployed: {ceo_log_agent_def.name} (ID: {ceo_log_agent_def.id})")
                deployment_info["agents"]["ceo_log"] = {
                    "name": ceo_log_agent_def.name,
                    "id": ceo_log_agent_def.id,
                    "type": "connected_agent"
                }
                
                # 2. Deploy North Star Agent
                logger.info("\n⭐ Deploying North Star Agent...")
                north_star_agent_name = f"{north_star_agent_config.AGENT_NAME_PREFIX}-{os.urandom(4).hex()}"
                north_star_agent_def = await client.agents.create_agent(
                    model=MODEL_DEPLOYMENT_NAME,
                    name=north_star_agent_name,
                    instructions=north_star_agent_config.AGENT_INSTRUCTIONS,
                    tools=north_star_agent_config.TOOLS
                )
                logger.info(f"✅ North Star Agent deployed: {north_star_agent_def.name} (ID: {north_star_agent_def.id})")
                deployment_info["agents"]["north_star"] = {
                    "name": north_star_agent_def.name,
                    "id": north_star_agent_def.id,
                    "type": "connected_agent"
                }
                
                # 3. Deploy Memory Recall Agent
                logger.info("\n🧠 Deploying Memory Recall Agent...")
                memory_recall_agent_name = f"{memory_recall_agent_config.AGENT_NAME_PREFIX}-{os.urandom(4).hex()}"
                memory_recall_agent_def = await client.agents.create_agent(
                    model=MODEL_DEPLOYMENT_NAME,
                    name=memory_recall_agent_name,
                    instructions=memory_recall_agent_config.AGENT_INSTRUCTIONS,
                    tools=memory_recall_agent_config.TOOLS
                )
                logger.info(f"✅ Memory Recall Agent deployed: {memory_recall_agent_def.name} (ID: {memory_recall_agent_def.id})")
                deployment_info["agents"]["memory_recall"] = {
                    "name": memory_recall_agent_def.name,
                    "id": memory_recall_agent_def.id,
                    "type": "connected_agent"
                }
                
                # 4. Create connected agent tools for orchestrator
                logger.info("\n🔧 Creating connected agent tools...")
                
                # Convert tools to format expected by API
                tools = []
                
                # Add CEO Log tool
                tools.append({
                    "type": "connected_agent",
                    "connected_agent": {
                        "id": ceo_log_agent_def.id,
                        "name": "ceo_log_specialist",
                        "description": (
                            "A CEO log specialist for strategic insights and executive thoughts. "
                            "Use this tool for saving CEO logs, retrieving executive insights, "
                            "analyzing leadership patterns, and managing strategic reflections."
                        )
                    }
                })
                
                # Add North Star tool
                tools.append({
                    "type": "connected_agent",
                    "connected_agent": {
                        "id": north_star_agent_def.id,
                        "name": "north_star_specialist",
                        "description": (
                            "A strategic alignment specialist for vision, mission, and goal management. "
                            "Use this tool for defining organizational vision, setting mission statements, "
                            "creating strategic goals, tracking progress, measuring alignment, and generating OKRs."
                        )
                    }
                })
                
                # Add Memory Recall tool
                tools.append({
                    "type": "connected_agent",
                    "connected_agent": {
                        "id": memory_recall_agent_def.id,
                        "name": "memory_recall_specialist",
                        "description": (
                            "A memory and pattern recognition specialist for organizational insights. "
                            "Use this tool for searching historical context, identifying patterns, "
                            "analyzing trends, storing important information, and finding similar past situations."
                        )
                    }
                })
                
                # 5. Deploy Orchestrator with all three tools
                logger.info("\n🎯 Deploying Main Orchestrator...")
                orchestrator_name = f"{orchestrator_agent_config_with_memory_recall.AGENT_NAME_PREFIX}-{os.urandom(4).hex()}"
                orchestrator_def = await client.agents.create_agent(
                    model=MODEL_DEPLOYMENT_NAME,
                    name=orchestrator_name,
                    instructions=orchestrator_agent_config_with_memory_recall.AGENT_INSTRUCTIONS,
                    tools=tools
                )
                logger.info(f"✅ Orchestrator deployed: {orchestrator_def.name} (ID: {orchestrator_def.id})")
                
                deployment_info["orchestrator"] = {
                    "name": orchestrator_def.name,
                    "id": orchestrator_def.id,
                    "connected_agents": ["ceo_log", "north_star", "memory_recall"]
                }
                
                # Save deployment info
                save_deployment_info(deployment_info)
                
                logger.info("\n" + "="*60)
                logger.info("✅ ALL STRATOS AGENTS DEPLOYED SUCCESSFULLY")
                logger.info("="*60)
                logger.info(f"📝 CEO Log Agent: {ceo_log_agent_def.id}")
                logger.info(f"⭐ North Star Agent: {north_star_agent_def.id}")
                logger.info(f"🧠 Memory Recall Agent: {memory_recall_agent_def.id}")
                logger.info(f"🎯 Orchestrator: {orchestrator_def.id}")
                logger.info("="*60)
                
                return deployment_info
        
    except Exception as e:
        logger.error(f"❌ Deployment failed: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(deploy_agents())