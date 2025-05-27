#!/usr/bin/env python3
"""
Script to retrieve the complete instructions from the deployed Main Orchestrator.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from azure.ai.projects.aio import AIProjectClient
from azure.identity.aio import DefaultAzureCredential
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [%(funcName)s] %(message)s')
logger = logging.getLogger(__name__)

async def get_orchestrator_instructions():
    """Retrieve and display the Main Orchestrator's complete instructions."""
    
    # Load environment variables
    env_path = Path(__file__).parent.parent / '.env'
    logger.info(f"Loading .env from: {env_path}")
    load_dotenv(env_path)
    
    # Get orchestrator ID from environment
    orchestrator_id = os.getenv("MAIN_ORCHESTRATOR_AGENT_ID")
    if not orchestrator_id:
        logger.error("MAIN_ORCHESTRATOR_AGENT_ID not found in environment variables")
        return
    
    logger.info(f"Main Orchestrator ID: {orchestrator_id}")
    
    # Get Azure AI Agent Service configuration
    endpoint = os.getenv("AZURE_AI_AGENT_ENDPOINT")
    if not endpoint:
        logger.error("AZURE_AI_AGENT_ENDPOINT not found in environment variables")
        return
    
    logger.info(f"Connecting to: {endpoint}")
    
    # Create credential and client
    credential = DefaultAzureCredential()
    
    try:
        # Create AI Project client
        async with AIProjectClient(
            endpoint=endpoint,
            credential=credential,
            api_version="2024-12-01-preview"
        ) as client:
            # Get the agent definition
            logger.info(f"Fetching agent definition for ID: {orchestrator_id}")
            agent = await client.agents.get_agent(agent_id=orchestrator_id)
            
            # Display agent information
            print("\n" + "="*80)
            print("MAIN ORCHESTRATOR AGENT INFORMATION")
            print("="*80)
            print(f"Name: {agent.name}")
            print(f"ID: {agent.id}")
            print(f"Model: {agent.model}")
            print(f"Created: {agent.created_at}")
            
            # Display tools
            if hasattr(agent, 'tools') and agent.tools:
                print(f"\nTools ({len(agent.tools)}):")
                for i, tool in enumerate(agent.tools, 1):
                    if hasattr(tool, 'function'):
                        print(f"  {i}. {tool.function.name}")
            
            # Display complete instructions
            print("\n" + "="*80)
            print("COMPLETE INSTRUCTIONS:")
            print("="*80)
            if hasattr(agent, 'instructions') and agent.instructions:
                print(agent.instructions)
            else:
                print("No instructions found.")
            print("="*80)
            
    except Exception as e:
        logger.error(f"Error retrieving orchestrator instructions: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(get_orchestrator_instructions())