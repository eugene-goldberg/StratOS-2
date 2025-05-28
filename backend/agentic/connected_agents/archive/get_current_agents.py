#!/usr/bin/env python3
"""
Get current agent IDs from environment and test them.
"""

import asyncio
import os
import logging
from dotenv import load_dotenv
from pathlib import Path

# Load .env from current directory
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path)

from azure.identity.aio import DefaultAzureCredential
from azure.ai.projects.aio import AIProjectClient

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

async def main():
    """List all agents and find our deployed ones."""
    
    endpoint = os.getenv("AZURE_AI_PROJECT_CONNECTION_STRING")
    
    async with DefaultAzureCredential() as credential, \
               AIProjectClient(endpoint=endpoint, credential=credential) as client:
        
        logger.info("Listing all agents...")
        
        agents = []
        async for agent in client.agents.list_agents():
            agents.append(agent)
            
        logger.info(f"Found {len(agents)} agents total")
        
        # Find our agents
        greeter_agent = None
        calculator_agent = None
        orchestrator_agent = None
        
        for agent in agents:
            logger.info(f"- {agent.name} (ID: {agent.id})")
            
            if "greeter" in agent.name.lower():
                greeter_agent = agent
            elif "calculator" in agent.name.lower():
                calculator_agent = agent
            elif "orchestrator" in agent.name.lower():
                orchestrator_agent = agent
                
        logger.info("\n" + "="*60)
        logger.info("IDENTIFIED AGENTS:")
        logger.info("="*60)
        
        if greeter_agent:
            logger.info(f"Greeter: {greeter_agent.id}")
        if calculator_agent:
            logger.info(f"Calculator: {calculator_agent.id}")
        if orchestrator_agent:
            logger.info(f"Orchestrator: {orchestrator_agent.id}")
            
        # Show what to add to .env
        logger.info("\n" + "="*60)
        logger.info("ADD THESE TO .env:")
        logger.info("="*60)
        
        if greeter_agent:
            logger.info(f'SPECIALIZED_GREETER_AGENT_ID="{greeter_agent.id}"')
        if calculator_agent:
            logger.info(f'SPECIALIZED_CALCULATOR_AGENT_ID="{calculator_agent.id}"')

if __name__ == "__main__":
    asyncio.run(main())