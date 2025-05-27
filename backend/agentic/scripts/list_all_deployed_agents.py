#!/usr/bin/env python3
"""
List all deployed agents in Azure AI Agent Service.
Shows agent details including ID, name, model, creation date, and description.
"""

import asyncio
import os
import sys
import logging
from typing import List
from dotenv import load_dotenv
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [%(funcName)s] %(message)s')
logger = logging.getLogger(__name__)

# Add parent directories to path
current_dir = os.path.dirname(os.path.abspath(__file__))
agentic_dir = os.path.dirname(current_dir)
sys.path.insert(0, agentic_dir)

# Load environment
env_path = os.path.join(agentic_dir, '.env')
logger.info(f"Loading .env from: {env_path}")
load_dotenv(env_path)

from azure.identity.aio import DefaultAzureCredential
from semantic_kernel.agents import AzureAIAgent, AzureAIAgentSettings

async def list_all_agents() -> List[dict]:
    """List all deployed agents in Azure AI Agent Service."""
    agents = []
    
    try:
        credential = DefaultAzureCredential()
        settings = AzureAIAgentSettings()
        
        logger.info(f"Connecting to: {settings.endpoint}")
        
        async with AzureAIAgent.create_client(credential=credential, settings=settings) as client:
            # List all agents
            response = client.agents.list_agents()
            
            async for agent in response:
                agent_info = {
                    "id": agent.id,
                    "name": agent.name,
                    "description": agent.description,
                    "instructions": agent.instructions[:200] + "..." if agent.instructions and len(agent.instructions) > 200 else agent.instructions,
                    "model": agent.model,
                    "created_at": agent.created_at,
                    "tools": len(agent.tools) if hasattr(agent, 'tools') and agent.tools else 0
                }
                agents.append(agent_info)
                
    except Exception as e:
        logger.error(f"Error listing agents: {str(e)}", exc_info=True)
    finally:
        await credential.close()
    
    return agents

async def display_agents():
    """Display all deployed agents with formatting."""
    logger.info("Fetching list of all deployed agents...")
    
    # Get all agents
    agents = await list_all_agents()
    
    if not agents:
        logger.info("\n✅ No agents currently deployed in Azure AI Agent Service.")
        return
    
    # Sort by creation date (newest first)
    agents.sort(key=lambda x: x['created_at'], reverse=True)
    
    # Display all agents
    print(f"\n{'='*100}")
    print(f"DEPLOYED AGENTS IN AZURE AI AGENT SERVICE")
    print(f"{'='*100}")
    print(f"Total agents: {len(agents)}")
    print(f"{'='*100}\n")
    
    for i, agent in enumerate(agents, 1):
        print(f"{i}. {agent['name']} (ID: {agent['id']})")
        print(f"   Model: {agent['model']}")
        print(f"   Created: {agent['created_at']}")
        if agent['tools'] > 0:
            print(f"   Tools: {agent['tools']}")
        if agent['description']:
            print(f"   Description: {agent['description']}")
        if agent['instructions']:
            print(f"   Instructions Preview: {agent['instructions']}")
        print()
    
    # Group by date
    print(f"{'='*100}")
    print("SUMMARY BY CREATION DATE")
    print(f"{'='*100}")
    
    date_groups = {}
    for agent in agents:
        date_key = agent['created_at'].date()
        if date_key not in date_groups:
            date_groups[date_key] = []
        date_groups[date_key].append(agent['name'])
    
    for date, names in sorted(date_groups.items(), reverse=True):
        print(f"\n{date}: {len(names)} agents")
        for name in names:
            print(f"  - {name}")

async def main():
    """Entry point."""
    try:
        await display_agents()
    except KeyboardInterrupt:
        logger.info("\nOperation cancelled by user.")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(main())