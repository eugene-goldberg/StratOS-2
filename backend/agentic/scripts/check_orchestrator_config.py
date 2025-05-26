#!/usr/bin/env python3
"""
Check Main Orchestrator configuration in Azure
"""

import asyncio
import json
import os
from pathlib import Path
from azure.identity import DefaultAzureCredential
from semantic_kernel.agents import AzureAIAgent, AzureAIAgentSettings
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [%(funcName)s] %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
from dotenv import load_dotenv
env_path = Path(__file__).parent.parent / '.env'
logger.info(f"Attempting to load .env file from: {env_path}")
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
    logger.info(f".env file loaded successfully.")

async def check_orchestrator_config():
    # Get orchestrator ID from deployment config
    deployment_config_path = Path(__file__).parent.parent / "deployment_configs" / "main_orchestrator_deployment.json"
    with open(deployment_config_path) as f:
        config = json.load(f)
    
    orchestrator_id = config["agent_id"]
    logger.info(f"Main Orchestrator ID: {orchestrator_id}")
    
    # Create settings
    settings = AzureAIAgentSettings(
        endpoint=os.getenv("AZURE_AI_AGENT_ENDPOINT"),
        model_deployment_name=os.getenv("AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME", "gpt-35-turbo"),
        api_version=os.getenv("AZURE_AI_AGENT_API_VERSION", "2024-12-01-preview")
    )
    
    # Create credential
    credential = DefaultAzureCredential()
    
    # Create client and test
    async with AzureAIAgent.create_client(credential=credential, settings=settings) as service_client:
        logger.info("Successfully created Azure AI Agent service client")
        
        # Get the orchestrator
        logger.info("Fetching Main Orchestrator definition...")
        agent_definition = await service_client.agents.get_agent(agent_id=orchestrator_id)
        
        print(f"\n{'='*80}")
        print("MAIN ORCHESTRATOR CONFIGURATION")
        print('='*80)
        print(f"Name: {agent_definition.name}")
        print(f"ID: {agent_definition.id}")
        print(f"Model: {agent_definition.model}")
        print(f"Description: {agent_definition.description[:100] if agent_definition.description else 'None'}...")
        print(f"Instructions Length: {len(agent_definition.instructions) if agent_definition.instructions else 0} characters")
        
        print(f"\n{'='*80}")
        print("INSTRUCTIONS (First 2000 characters)")
        print('='*80)
        if agent_definition.instructions:
            print(agent_definition.instructions[:2000])
            if len(agent_definition.instructions) > 2000:
                print("\n... [truncated]")
        else:
            print("No instructions found!")
        
        print(f"\n{'='*80}")
        print("TOOLS/FUNCTIONS")
        print('='*80)
        if hasattr(agent_definition, 'tools') and agent_definition.tools:
            for tool in agent_definition.tools:
                print(f"- {tool}")
        else:
            print("No tools/functions configured")
        
        print(f"\n{'='*80}")
        print("OTHER SETTINGS")
        print('='*80)
        print(f"Temperature: {getattr(agent_definition, 'temperature', 'Not set')}")
        print(f"Top P: {getattr(agent_definition, 'top_p', 'Not set')}")
        
        # Check if there are any other agents we can see
        print(f"\n{'='*80}")
        print("LISTING ALL AGENTS")
        print('='*80)
        try:
            agents = service_client.agents.list_agents()
            async for agent in agents:
                print(f"- {agent.name} (ID: {agent.id})")
        except Exception as e:
            print(f"Could not list agents: {e}")

if __name__ == "__main__":
    asyncio.run(check_orchestrator_config())