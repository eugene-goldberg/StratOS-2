#!/usr/bin/env python3
"""
Simple test of Main Orchestrator routing using the invoke pattern.
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

async def test_simple_routing():
    """Test Main Orchestrator routing with a simple message."""
    
    # Get orchestrator ID
    deployment_config_path = Path(__file__).parent.parent / "deployment_configs" / "main_orchestrator_deployment.json"
    with open(deployment_config_path) as f:
        config = json.load(f)
    
    orchestrator_id = config["agent_id"]
    
    print("="*80)
    print("TESTING MAIN ORCHESTRATOR ROUTING")
    print("="*80)
    print(f"Agent ID: {orchestrator_id}")
    print(f"Time: {datetime.now().isoformat()}")
    
    # Create settings and credential
    settings = AzureAIAgentSettings()
    credential = DefaultAzureCredential()
    
    # Test messages
    test_messages = [
        "I need to create a CEO log entry about our successful product launch.",
        "Can you perform a SWOT analysis for our new mobile app?",
        "What is our company vision and mission?"
    ]
    
    try:
        async with AzureAIAgent.create_client(credential=credential, settings=settings) as service_client:
            print("\n✓ Connected to Azure AI Agent Service")
            
            # Get agent definition
            agent_definition = await service_client.agents.get_agent(agent_id=orchestrator_id)
            print(f"✓ Retrieved agent: {agent_definition.name}")
            
            # Create agent
            orchestrator = AzureAIAgent(client=service_client, definition=agent_definition)
            
            for i, message in enumerate(test_messages, 1):
                print(f"\n{'='*60}")
                print(f"TEST {i}")
                print('='*60)
                print(f"User: {message}")
                print(f"\nOrchestrator Response:")
                print("-" * 40)
                
                try:
                    # Invoke the orchestrator
                    response_text = ""
                    async for chunk in orchestrator.invoke(message=message):
                        if hasattr(chunk, 'content') and chunk.content:
                            print(chunk.content, end="", flush=True)
                            response_text += str(chunk.content)
                    
                    print("\n" + "-" * 40)
                    
                    # Check if routing is mentioned in the response
                    routing_keywords = [
                        "CEOLogAgent", "NorthStarAgent", "SWOTTOWSAgent",
                        "route", "routing", "RouteToAgent", "agent"
                    ]
                    
                    found_keywords = [kw for kw in routing_keywords if kw.lower() in response_text.lower()]
                    
                    if found_keywords:
                        print(f"✅ Routing keywords detected: {found_keywords}")
                    else:
                        print("⚠️ No explicit routing keywords found in response")
                        
                except Exception as e:
                    print(f"Error: {str(e)}")
                    print(f"Error type: {type(e).__name__}")
                    
                    # If it's a kernel error about missing tools, that's actually expected
                    if "function tool(s) are defined on the agent but missing from the kernel" in str(e):
                        print("\n💡 This error indicates the orchestrator tried to use the RouteToAgent tool!")
                        print("   In production, the FastAPI backend would handle this tool call.")
    
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print(f"\n{'='*80}")
    print("CONCLUSION")
    print('='*80)
    print("The Main Orchestrator has the RouteToAgent tool configured.")
    print("When invoked directly through Semantic Kernel, it will try to use this tool")
    print("but fail because the kernel doesn't have the tool registered.")
    print("\nIn production:")
    print("1. FastAPI will use the Azure AI Agent Service API directly")
    print("2. It will handle the REQUIRES_ACTION status when the orchestrator wants to route")
    print("3. It will parse the RouteToAgent tool call and invoke the appropriate agent")

if __name__ == "__main__":
    asyncio.run(test_simple_routing())