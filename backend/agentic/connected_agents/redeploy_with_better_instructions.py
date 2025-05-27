#!/usr/bin/env python3
"""Redeploy orchestrator with instructions that force tool usage."""

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
model = os.getenv("AZURE_AI_MODEL_DEPLOYMENT_NAME", "gpt-35-turbo")

def main():
    """Update orchestrator with better instructions."""
    # Load deployment info
    with open("deployment_info.json", "r") as f:
        deployment_info = json.load(f)
    
    orchestrator_id = deployment_info["orchestrator_agent_id"]
    
    credential = DefaultAzureCredential()
    client = AIProjectClient(endpoint=connection_string, credential=credential)
    
    logger.info("Updating orchestrator with better instructions...")
    
    # New instructions that explicitly require tool usage
    new_instructions = """You are an orchestrator that MUST use tools for ALL requests.

CRITICAL RULES:
1. You MUST ALWAYS use the appropriate tool - NEVER answer directly
2. For ANY greeting request: USE enthusiastic_greeter_tool
3. For ANY weather request: USE weather_information_tool
4. You are NOT ALLOWED to provide greetings or weather information yourself
5. If a request matches a tool's purpose, you MUST use that tool

DO NOT:
- Generate your own greetings
- Provide weather information yourself
- Mimic tool responses

ALWAYS:
- Call the appropriate tool
- Wait for the tool's response
- Return the tool's exact response to the user

Your ONLY job is to route requests to tools."""
    
    # Update the orchestrator
    updated_orchestrator = client.agents.update_agent(
        agent_id=orchestrator_id,
        instructions=new_instructions
    )
    
    logger.info(f"✅ Updated orchestrator: {orchestrator_id}")
    logger.info(f"New instructions applied")
    
    # Save updated info
    deployment_info["instructions_updated"] = True
    with open("deployment_info.json", "w") as f:
        json.dump(deployment_info, f, indent=2)
    
    logger.info("\n✅ Orchestrator updated successfully!")
    logger.info("Run test_deployed_system.py to verify improved delegation")

if __name__ == "__main__":
    main()