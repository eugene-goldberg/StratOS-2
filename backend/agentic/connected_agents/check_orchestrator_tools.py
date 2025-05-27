#!/usr/bin/env python3
"""Check the orchestrator's tools configuration."""

import logging
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
import os
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [%(funcName)s] %(message)s')
logger = logging.getLogger(__name__)

# Environment variables
connection_string = os.getenv("AZURE_AI_PROJECT_CONNECTION_STRING")

def main():
    """Check orchestrator tools."""
    # Load deployment info
    with open("deployment_info.json", "r") as f:
        deployment_info = json.load(f)
    
    orchestrator_id = deployment_info["orchestrator_agent_id"]
    
    credential = DefaultAzureCredential()
    client = AIProjectClient(endpoint=connection_string, credential=credential)
    
    # Get the orchestrator agent details
    orchestrator = client.agents.get_agent(agent_id=orchestrator_id)
    
    logger.info(f"Orchestrator ID: {orchestrator_id}")
    logger.info(f"Orchestrator Name: {orchestrator.name}")
    logger.info(f"Orchestrator Model: {orchestrator.model}")
    logger.info(f"Number of Tools: {len(orchestrator.tools) if orchestrator.tools else 0}")
    
    if orchestrator.tools:
        logger.info("\nOrchestrator Tools:")
        for i, tool in enumerate(orchestrator.tools, 1):
            logger.info(f"\nTool {i}:")
            if hasattr(tool, 'type'):
                logger.info(f"  Type: {tool.type}")
            if hasattr(tool, 'id'):
                logger.info(f"  Connected Agent ID: {tool.id}")
            if hasattr(tool, 'name'):
                logger.info(f"  Tool Name: {tool.name}")
            if hasattr(tool, 'description'):
                logger.info(f"  Description: {tool.description}")
            logger.info(f"  Tool Object: {tool}")
    else:
        logger.warning("❌ Orchestrator has NO TOOLS configured!")
    
    logger.info(f"\nOrchestrator Instructions (first 500 chars):")
    logger.info(orchestrator.instructions[:500] + "..." if len(orchestrator.instructions) > 500 else orchestrator.instructions)

if __name__ == "__main__":
    main()