#!/usr/bin/env python3
"""
Update the orchestrator with fixed instructions.
"""

import asyncio
import os
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from azure.identity.aio import DefaultAzureCredential
from azure.ai.projects.aio import AIProjectClient
import multi_tool_orchestrator_config

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def update_orchestrator():
    """Delete and recreate orchestrator with fixed instructions."""
    
    orchestrator_id = os.getenv("MAIN_ORCHESTRATOR_AGENT_ID")
    greeter_id = os.getenv("SPECIALIZED_GREETER_AGENT_ID")
    calculator_id = os.getenv("SPECIALIZED_CALCULATOR_AGENT_ID")
    
    endpoint = os.getenv("AZURE_AI_PROJECT_CONNECTION_STRING")
    model_name = os.getenv("AZURE_AI_MODEL_DEPLOYMENT_NAME", "gpt-35-turbo")
    
    async with DefaultAzureCredential() as credential, \
               AIProjectClient(endpoint=endpoint, credential=credential) as client:
        
        # Delete current orchestrator
        logger.info(f"Deleting current orchestrator {orchestrator_id}...")
        try:
            await client.agents.delete_agent(agent_id=orchestrator_id)
            logger.info("✅ Deleted current orchestrator")
        except Exception as e:
            logger.warning(f"Could not delete: {e}")
            
        # Create tools list
        tools = []
        tools.append({
            "type": "connected_agent",
            "connected_agent": {
                "id": greeter_id,
                "name": "enthusiastic_greeter_tool",
                "description": "A specialized greeting expert"
            }
        })
        tools.append({
            "type": "connected_agent",
            "connected_agent": {
                "id": calculator_id,
                "name": "precise_calculator_tool",
                "description": "A mathematical calculation expert"
            }
        })
        
        # Create new orchestrator
        logger.info("Creating new orchestrator with fixed instructions...")
        new_orchestrator = await client.agents.create_agent(
            model=model_name,
            name=f"{multi_tool_orchestrator_config.AGENT_NAME_PREFIX}-fixed",
            instructions=multi_tool_orchestrator_config.AGENT_INSTRUCTIONS,
            tools=tools
        )
        
        logger.info(f"✅ Created new orchestrator: {new_orchestrator.id}")
        
        # Update .env file
        from pathlib import Path
        env_path = Path(__file__).parent / '.env'
        env_content = env_path.read_text()
        new_env_content = env_content.replace(
            f'MAIN_ORCHESTRATOR_AGENT_ID={orchestrator_id}',
            f'MAIN_ORCHESTRATOR_AGENT_ID={new_orchestrator.id}'
        )
        env_path.write_text(new_env_content)
        
        logger.info("✅ Updated .env file")
        logger.info("\nNow run check_announcements.py to verify the fix!")

if __name__ == "__main__":
    asyncio.run(update_orchestrator())