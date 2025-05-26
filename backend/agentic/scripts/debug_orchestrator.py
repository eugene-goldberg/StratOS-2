#!/usr/bin/env python3
"""
Debug script to test Main Orchestrator routing logic
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from datetime import datetime, timezone
from azure.identity import DefaultAzureCredential
from semantic_kernel.agents import AzureAIAgent

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))
from config.settings import get_settings

# Load environment variables
from dotenv import load_dotenv
env_path = Path(__file__).parent.parent / '.env'
print(f"Attempting to load .env file from: {env_path}")
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
    print(f".env file loaded successfully.")
else:
    print(f"Warning: .env file not found at {env_path}")

async def debug_orchestrator():
    settings = get_settings()
    credential = DefaultAzureCredential()
    
    # Get orchestrator ID from deployment config
    deployment_config_path = Path(__file__).parent.parent / "deployment_configs" / "main_orchestrator_deployment.json"
    with open(deployment_config_path) as f:
        config = json.load(f)
    
    orchestrator_id = config["agent_id"]
    print(f"Testing Main Orchestrator: {orchestrator_id}")
    
    async with AzureAIAgent.create_client(credential=credential, settings=settings) as service_client:
        # Get the orchestrator
        agent_definition = await service_client.agents.get_agent(agent_id=orchestrator_id)
        print(f"\nOrchestrator Name: {agent_definition.name}")
        print(f"Model: {agent_definition.model}")
        print(f"Instructions Length: {len(agent_definition.instructions) if agent_definition.instructions else 0}")
        print(f"Temperature: {getattr(agent_definition, 'temperature', 'Not set')}")
        
        # Print first 500 chars of instructions
        if agent_definition.instructions:
            print(f"\nFirst 500 chars of instructions:")
            print(agent_definition.instructions[:500])
            print("...")
        
        orchestrator = AzureAIAgent(
            client=service_client,
            definition=agent_definition
        )
        
        # Test with a very explicit routing request
        print("\n" + "="*80)
        print("TESTING EXPLICIT ROUTING REQUEST")
        print("="*80)
        
        test_message = """I need you to route this request to the appropriate agent. Please analyze this request and determine which agent should handle it:

Task Type: CREATE_CEO_LOG
User ID: test-user-123
Request: Create a new CEO log entry with the text "Had a great meeting with the product team"

Based on your routing logic, which agent should handle this CREATE_CEO_LOG task?"""
        
        messages = [{"role": "user", "content": test_message}]
        response = await orchestrator.run(messages=messages)
        
        print(f"\nOrchestrator Response:")
        print("-" * 40)
        print(response.messages[-1]["content"])
        
        # Test with direct instruction check
        print("\n" + "="*80)
        print("TESTING INSTRUCTION UNDERSTANDING")
        print("="*80)
        
        test_message2 = "What are your routing instructions? Can you list the agents you can route to?"
        
        messages2 = [{"role": "user", "content": test_message2}]
        response2 = await orchestrator.run(messages=messages2)
        
        print(f"\nOrchestrator Response:")
        print("-" * 40)
        print(response2.messages[-1]["content"])

if __name__ == "__main__":
    asyncio.run(debug_orchestrator())