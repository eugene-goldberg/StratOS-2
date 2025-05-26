#!/usr/bin/env python3
"""
Test the updated Main Orchestrator with routing tools.
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

async def test_updated_orchestrator():
    # Get orchestrator ID
    deployment_config_path = Path(__file__).parent.parent / "deployment_configs" / "main_orchestrator_deployment.json"
    with open(deployment_config_path) as f:
        config = json.load(f)
    
    orchestrator_id = config["agent_id"]
    print(f"Testing Updated Main Orchestrator")
    print(f"{'='*60}")
    print(f"Agent ID: {orchestrator_id}")
    print(f"Has Tools: {config.get('has_tools', False)}")
    print(f"Tool Count: {config.get('tool_count', 0)}")
    print(f"Updated: {config.get('updated_time', 'Unknown')}\n")
    
    # Create settings and credential
    settings = AzureAIAgentSettings()
    credential = DefaultAzureCredential()
    
    async with AzureAIAgent.create_client(credential=credential, settings=settings) as service_client:
        # Get the orchestrator
        agent_definition = await service_client.agents.get_agent(agent_id=orchestrator_id)
        orchestrator = AzureAIAgent(client=service_client, definition=agent_definition)
        
        # Test cases that should trigger routing
        test_cases = [
            {
                "name": "CEO Log Entry Request",
                "message": "I need to create a CEO log entry about our successful product launch"
            },
            {
                "name": "SWOT Analysis Request", 
                "message": "Can you perform a SWOT analysis for our new mobile app?"
            },
            {
                "name": "Resource Planning Request",
                "message": "Help me optimize resource allocation for Q3 projects"
            },
            {
                "name": "North Star Query",
                "message": "What is our company vision and core values?"
            },
            {
                "name": "Risk Assessment",
                "message": "What are the main risks we should be aware of for our expansion plans?"
            }
        ]
        
        for test in test_cases:
            print(f"\n{'='*60}")
            print(f"TEST: {test['name']}")
            print('='*60)
            print(f"User: {test['message']}")
            print(f"\nOrchestrator Response:")
            print("-" * 40)
            
            # Invoke orchestrator - it should now use the RouteToAgent tool
            try:
                response_text = ""
                async for chunk in orchestrator.invoke(message=test['message']):
                    if hasattr(chunk, 'content') and chunk.content:
                        print(chunk.content, end="", flush=True)
                        response_text += str(chunk.content)
                
                print("\n" + "-" * 40)
                
                # Check if the response mentions routing or specific agents
                routing_keywords = [
                    "CEOLogAgent", "NorthStarAgent", "SWOTTOWSAgent", 
                    "ResourceOptimizationAgent", "RiskOpportunityAgent",
                    "route", "routing", "RouteToAgent", "agent"
                ]
                
                found_routing = any(keyword in response_text for keyword in routing_keywords)
                
                if found_routing:
                    print("✅ Routing detected in response!")
                else:
                    print("⚠️ No explicit routing found in response")
                    
            except Exception as e:
                print(f"Error: {str(e)}")
        
        print(f"\n{'='*60}")
        print("TEST SUMMARY")
        print('='*60)
        print("The Main Orchestrator has been updated with routing tools.")
        print("It should now be able to identify which agent to route requests to.")
        print("\nNote: The orchestrator provides routing guidance.")
        print("The FastAPI backend will need to parse these routing decisions")
        print("and invoke the appropriate specialized agents.")

if __name__ == "__main__":
    asyncio.run(test_updated_orchestrator())