#!/usr/bin/env python3
"""
Test Main Orchestrator routing with direct routing requests
"""

import asyncio
import json
import os
from pathlib import Path
from datetime import datetime
from azure.identity import DefaultAzureCredential
from semantic_kernel.agents import AzureAIAgent, AzureAIAgentSettings

# Load environment variables
from dotenv import load_dotenv
env_path = Path(__file__).parent.parent / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path)

async def test_routing():
    # Get orchestrator ID
    deployment_config_path = Path(__file__).parent.parent / "deployment_configs" / "main_orchestrator_deployment.json"
    with open(deployment_config_path) as f:
        config = json.load(f)
    
    orchestrator_id = config["agent_id"]
    
    # Create settings and credential
    settings = AzureAIAgentSettings()
    credential = DefaultAzureCredential()
    
    async with AzureAIAgent.create_client(credential=credential, settings=settings) as service_client:
        # Get the orchestrator
        agent_definition = await service_client.agents.get_agent(agent_id=orchestrator_id)
        orchestrator = AzureAIAgent(client=service_client, definition=agent_definition)
        
        print(f"Testing Main Orchestrator Routing")
        print(f"{'='*60}")
        print(f"Agent: {agent_definition.name}")
        print(f"ID: {agent_definition.id}")
        print(f"Started: {datetime.now().isoformat()}\n")
        
        # Test cases with very explicit routing instructions
        test_cases = [
            {
                "name": "Direct CEO Log Routing",
                "message": """Please route this request to the appropriate agent:
                
The user wants to create a CEO log entry. The content is: "Had a productive meeting with the engineering team about Q3 roadmap."

Based on your routing instructions, which agent should handle this? Please respond with:
1. The agent name you're routing to
2. Why you chose that agent"""
            },
            {
                "name": "Direct SWOT Analysis Routing", 
                "message": """Please route this request to the appropriate agent:
                
The user wants to perform a SWOT analysis for their new product launch strategy.

Based on your routing instructions, which agent should handle this? Please respond with:
1. The agent name you're routing to
2. Why you chose that agent"""
            },
            {
                "name": "Direct Resource Planning Routing",
                "message": """Please route this request to the appropriate agent:
                
The user needs help with resource allocation and capacity planning for Q2 initiatives.

Based on your routing instructions, which agent should handle this? Please respond with:
1. The agent name you're routing to
2. Why you chose that agent"""
            }
        ]
        
        for test in test_cases:
            print(f"\n{'='*60}")
            print(f"TEST: {test['name']}")
            print('='*60)
            print("User Message:")
            print(test['message'])
            print("\nOrchestrator Response:")
            print("-" * 40)
            
            # Invoke orchestrator
            response_text = ""
            async for chunk in orchestrator.invoke(message=test['message']):
                if hasattr(chunk, 'content') and chunk.content:
                    print(chunk.content, end="", flush=True)
                    response_text += str(chunk.content)
            
            if not response_text:
                print("[No response content]")
            
            print("\n" + "-" * 40)
        
        print(f"\n{'='*60}")
        print("TEST COMPLETE")
        print(f"Finished: {datetime.now().isoformat()}")

if __name__ == "__main__":
    asyncio.run(test_routing())