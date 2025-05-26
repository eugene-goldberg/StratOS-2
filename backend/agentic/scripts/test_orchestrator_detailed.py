#!/usr/bin/env python3
"""
Detailed test of Main Orchestrator to understand routing behavior
"""

import asyncio
import json
import os
from datetime import datetime, timezone
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

async def test_orchestrator_detailed():
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
    
    logger.info(f"Settings endpoint: {settings.endpoint}")
    logger.info(f"Settings API version: {settings.api_version}")
    
    # Create credential
    logger.info("Environment is configured for ClientSecretCredential")
    credential = DefaultAzureCredential()
    
    # Create client and test
    async with AzureAIAgent.create_client(credential=credential, settings=settings) as service_client:
        logger.info("Successfully created Azure AI Agent service client")
        
        # Get the orchestrator
        logger.info("Fetching Main Orchestrator definition...")
        agent_definition = await service_client.agents.get_agent(agent_id=orchestrator_id)
        logger.info(f"Successfully fetched agent: {agent_definition.name}")
        
        orchestrator = AzureAIAgent(
            client=service_client,
            definition=agent_definition
        )
        
        print(f"\n{'='*80}")
        print("ORCHESTRATOR DETAILS")
        print('='*80)
        print(f"Name: {agent_definition.name}")
        print(f"Model: {agent_definition.model}")
        print(f"Instructions Length: {len(agent_definition.instructions) if agent_definition.instructions else 0}")
        
        # Test 1: Check if orchestrator understands its role
        print(f"\n{'='*80}")
        print("TEST 1: ROLE UNDERSTANDING")
        print('='*80)
        print("User Message: What is your role as the Main Orchestrator?")
        
        messages = [{"role": "user", "content": "What is your role as the Main Orchestrator?"}]
        response = await orchestrator.run(messages=messages)
        
        print(f"\nOrchestrator Response:")
        print('-' * 40)
        print(response.messages[-1]["content"])
        
        # Test 2: Check available agents
        print(f"\n{'='*80}")
        print("TEST 2: AVAILABLE AGENTS")
        print('='*80)
        print("User Message: What agents can you route requests to?")
        
        messages = [{"role": "user", "content": "What agents can you route requests to?"}]
        response = await orchestrator.run(messages=messages)
        
        print(f"\nOrchestrator Response:")
        print('-' * 40)
        print(response.messages[-1]["content"])
        
        # Test 3: Test specific routing
        print(f"\n{'='*80}")
        print("TEST 3: SPECIFIC ROUTING TEST")
        print('='*80)
        test_msg = """I need to route the following request:
        
Task Type: CREATE_CEO_LOG
Description: Create a new CEO log entry about a successful product launch

Which agent should handle this request and why?"""
        
        print(f"User Message:\n{test_msg}")
        
        messages = [{"role": "user", "content": test_msg}]
        response = await orchestrator.run(messages=messages)
        
        print(f"\nOrchestrator Response:")
        print('-' * 40)
        print(response.messages[-1]["content"])
        
        # Test 4: Function calling test
        print(f"\n{'='*80}")
        print("TEST 4: FUNCTION CALLING CAPABILITY")
        print('='*80)
        print("User Message: Do you have any tools or functions available to you?")
        
        messages = [{"role": "user", "content": "Do you have any tools or functions available to you?"}]
        response = await orchestrator.run(messages=messages)
        
        print(f"\nOrchestrator Response:")
        print('-' * 40)
        print(response.messages[-1]["content"])
        
        print(f"\n{'='*80}")
        print("TEST COMPLETE")
        print('='*80)

if __name__ == "__main__":
    asyncio.run(test_orchestrator_detailed())