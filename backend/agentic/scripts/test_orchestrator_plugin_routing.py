#!/usr/bin/env python3
"""
Test the Main Orchestrator's routing behavior with plugin-based architecture.
"""

import asyncio
import os
import sys
import json
import logging
from datetime import datetime, timezone
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [%(funcName)s] %(message)s')
logger = logging.getLogger(__name__)

# Path setup
current_dir = os.path.dirname(os.path.abspath(__file__))
agentic_dir = os.path.dirname(current_dir)
env_path = os.path.join(agentic_dir, '.env')
load_dotenv(env_path)

# Import required modules
try:
    from azure.identity.aio import DefaultAzureCredential
    from semantic_kernel.agents import AzureAIAgent, AzureAIAgentSettings
    from semantic_kernel.contents import ChatMessageContent
except ImportError as e:
    logger.error(f"Error importing required modules: {e}")
    sys.exit(1)

async def test_routing():
    """Test the orchestrator's routing decisions."""
    
    try:
        # Load orchestrator ID
        deployment_config_path = os.path.join(agentic_dir, "deployment_configs", "main_orchestrator_deployment.json")
        with open(deployment_config_path, 'r') as f:
            config = json.load(f)
            orchestrator_id = config['agent_id']
            logger.info(f"Loaded Main Orchestrator ID: {orchestrator_id}")
        
        settings = AzureAIAgentSettings()
        credential = DefaultAzureCredential()
        
        async with AzureAIAgent.create_client(credential=credential, settings=settings) as client:
            # Get agent definition
            agent_def = await client.agents.get_agent(agent_id=orchestrator_id)
            logger.info(f"Connected to orchestrator: {agent_def.name}")
            
            # Create agent instance
            orchestrator = AzureAIAgent(
                client=client,
                definition=agent_def
            )
            
            # Test cases
            test_cases = [
                {
                    "name": "CEO Log Request",
                    "message": "I need to record my thoughts about the market downturn and how it might affect our expansion plans",
                    "expected_agent": "CEOLogAgent"
                },
                {
                    "name": "SWOT Analysis Request", 
                    "message": "Can you perform a SWOT analysis for our new product launch?",
                    "expected_agent": "SWOTTOWSAgent"
                },
                {
                    "name": "Vision Request",
                    "message": "What is our company's vision and core values?",
                    "expected_agent": "NorthStarAgent"
                },
                {
                    "name": "Risk Assessment",
                    "message": "What are the main risks we face with entering the Asian market?",
                    "expected_agent": "RiskRadarAgent"
                },
                {
                    "name": "Resource Planning",
                    "message": "How should we allocate resources for Q2?",
                    "expected_agent": "ResourceOptimizerAgent"
                }
            ]
            
            print("\n" + "="*80)
            print("TESTING MAIN ORCHESTRATOR ROUTING")
            print("="*80)
            
            for test in test_cases:
                print(f"\n--- Test: {test['name']} ---")
                print(f"User: {test['message']}")
                print(f"Expected routing: {test['expected_agent']}")
                
                # Create thread
                thread = await client.agents.threads.create()
                thread_id = thread.id
                
                # Add message to thread
                await client.agents.messages.create(
                    thread_id=thread_id,
                    role="user",
                    content=test['message']
                )
                
                # Run and get response
                run = await client.agents.runs.create_and_process(
                    thread_id=thread_id,
                    agent_id=orchestrator_id
                )
                
                # Get messages
                messages = await client.agents.messages.list(thread_id=thread_id)
                
                # Find the assistant's response
                response_parts = []
                for msg in messages.data:
                    if msg.role == "assistant":
                        if msg.content:
                            for content in msg.content:
                                if hasattr(content, 'text'):
                                    response_parts.append(content.text.value)
                
                # Join response
                full_response = ''.join(str(part) for part in response_parts)
                print(f"\nOrchestrator response:\n{full_response}")
                
                # Check if routing decision was made
                if "ROUTE TO:" in full_response:
                    print("✅ Routing decision detected")
                    # Extract the agent name
                    route_part = full_response.split("ROUTE TO:")[1].split("-")[0].strip()
                    if test['expected_agent'].lower() in route_part.lower():
                        print(f"✅ Correctly routed to {test['expected_agent']}")
                    else:
                        print(f"❌ Routed to {route_part} instead of {test['expected_agent']}")
                else:
                    print("❌ No clear routing decision found")
                
                # Clean up thread
                await client.agents.threads.delete(thread_id=thread_id)
            
            print("\n" + "="*80)
            print("ANALYSIS")
            print("="*80)
            print("The orchestrator should provide clear routing decisions in the format:")
            print("'ROUTE TO: [AgentName] - REASON: [Reasoning]'")
            print("\nThis allows the FastAPI backend to parse the decision and invoke")
            print("the appropriate specialist agent.")
            
    except Exception as e:
        logger.error(f"Error testing routing: {str(e)}", exc_info=True)
    finally:
        await credential.close()

async def main():
    """Main entry point."""
    print("="*80)
    print("TESTING MAIN ORCHESTRATOR PLUGIN-BASED ROUTING")
    print("="*80)
    print(f"\nTest started at: {datetime.now(timezone.utc).isoformat()}")
    
    await test_routing()
    
    print(f"\nTest completed at: {datetime.now(timezone.utc).isoformat()}")

if __name__ == "__main__":
    asyncio.run(main())