#!/usr/bin/env python3
"""
Test the Main Orchestrator's actual routing behavior.
This script will send requests and check if the orchestrator properly uses the RouteToAgent tool.
"""

import asyncio
import json
import os
import sys
import logging
from pathlib import Path
from datetime import datetime
from azure.identity import DefaultAzureCredential
from semantic_kernel.agents import AzureAIAgent, AzureAIAgentSettings

# Configure logging  
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [%(funcName)s] %(message)s')
logger = logging.getLogger(__name__)

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables
from dotenv import load_dotenv
env_path = Path(__file__).parent.parent / '.env'
logger.info(f"Loading .env from: {env_path}")
if env_path.exists():
    load_dotenv(dotenv_path=env_path)

async def test_routing_behavior():
    """Test if the Main Orchestrator actually routes requests properly."""
    
    # Get orchestrator ID
    deployment_config_path = Path(__file__).parent.parent / "deployment_configs" / "main_orchestrator_deployment.json"
    with open(deployment_config_path) as f:
        config = json.load(f)
    
    orchestrator_id = config["agent_id"]
    
    print("="*80)
    print("TESTING MAIN ORCHESTRATOR ROUTING BEHAVIOR")
    print("="*80)
    print(f"Agent ID: {orchestrator_id}")
    print(f"Has Tools: {config.get('has_tools', False)}")
    
    # Test cases designed to trigger specific agent routing
    test_cases = [
        {
            "name": "CEO Log Entry",
            "message": "I need to create a CEO log entry about our successful product launch. We exceeded Q4 targets by 25%.",
            "expected_agent": "CEOLogAgent"
        },
        {
            "name": "SWOT Analysis",
            "message": "Please perform a SWOT analysis for our new mobile app strategy",
            "expected_agent": "SWOTTOWSAgent"
        },
        {
            "name": "North Star Query",
            "message": "What is our company's vision and core values?",
            "expected_agent": "NorthStarAgent"
        },
        {
            "name": "Resource Planning",
            "message": "Help me optimize resource allocation for our Q2 engineering projects",
            "expected_agent": "ResourceOptimizationAgent"
        },
        {
            "name": "Risk Assessment",
            "message": "What are the main risks we should consider for our European expansion?",
            "expected_agent": "RiskOpportunityAgent"
        }
    ]
    
    # Create settings and credential
    settings = AzureAIAgentSettings()
    credential = DefaultAzureCredential()
    
    # Track results
    routing_results = []
    
    try:
        async with AzureAIAgent.create_client(credential=credential, settings=settings) as service_client:
            logger.info("Successfully created Azure AI Agent service client")
            
            # Get agent definition
            agent_definition = await service_client.agents.get_agent(agent_id=orchestrator_id)
            
            for test_case in test_cases:
                print(f"\n{'='*60}")
                print(f"TEST: {test_case['name']}")
                print('='*60)
                print(f"Message: {test_case['message']}")
                print(f"Expected Agent: {test_case['expected_agent']}")
                
                try:
                    # Create thread
                    thread = await service_client.agents.create_thread()
                    thread_id = thread.id
                    logger.info(f"Created thread: {thread_id}")
                    
                    # Add message
                    await service_client.agents.create_message(
                        thread_id=thread_id,
                        role="user",
                        content=test_case['message']
                    )
                    
                    # Run the orchestrator
                    run = await service_client.agents.create_run(
                        thread_id=thread_id,
                        assistant_id=orchestrator_id
                    )
                    logger.info(f"Created run: {run.id}")
                    
                    # Wait for completion or action required
                    max_attempts = 20
                    attempt = 0
                    routing_detected = False
                    routed_agent = None
                    routing_reasoning = None
                    
                    while attempt < max_attempts:
                        await asyncio.sleep(1)
                        run = await service_client.agents.get_run(
                            thread_id=thread_id,
                            run_id=run.id
                        )
                        
                        if run.status == "completed":
                            print("\nStatus: COMPLETED")
                            # Get the response
                            messages = await service_client.agents.list_messages(thread_id=thread_id)
                            for msg in messages.data:
                                if msg.role == "assistant":
                                    print(f"Response: {msg.content[0].text.value if msg.content else 'No content'}")
                            break
                            
                        elif run.status == "failed":
                            print(f"\nStatus: FAILED - {getattr(run, 'last_error', 'Unknown error')}")
                            break
                            
                        elif run.status == "requires_action":
                            print("\nStatus: REQUIRES_ACTION (Tool call detected!)")
                            
                            if hasattr(run, 'required_action') and hasattr(run.required_action, 'submit_tool_outputs'):
                                tool_calls = run.required_action.submit_tool_outputs.tool_calls
                                
                                for tool_call in tool_calls:
                                    if tool_call.function.name == "RouteToAgent":
                                        routing_detected = True
                                        try:
                                            args = json.loads(tool_call.function.arguments)
                                            routed_agent = args.get('agent_name')
                                            routing_reasoning = args.get('reasoning')
                                            task_summary = args.get('task_summary')
                                            
                                            print(f"\n✅ ROUTING DETECTED!")
                                            print(f"   Routed to: {routed_agent}")
                                            print(f"   Reasoning: {routing_reasoning}")
                                            print(f"   Task: {task_summary}")
                                            
                                        except Exception as e:
                                            print(f"   Error parsing arguments: {e}")
                                
                                # For this test, we'll cancel the run since we can't actually execute the tool
                                await service_client.agents.cancel_run(
                                    thread_id=thread_id,
                                    run_id=run.id
                                )
                            break
                        
                        attempt += 1
                    
                    # Record result
                    result = {
                        "test": test_case['name'],
                        "expected": test_case['expected_agent'],
                        "actual": routed_agent,
                        "routing_detected": routing_detected,
                        "reasoning": routing_reasoning,
                        "success": routed_agent == test_case['expected_agent'] if routing_detected else False
                    }
                    routing_results.append(result)
                    
                    if routing_detected:
                        if result['success']:
                            print(f"\n✅ CORRECT ROUTING: Expected {test_case['expected_agent']}, got {routed_agent}")
                        else:
                            print(f"\n❌ INCORRECT ROUTING: Expected {test_case['expected_agent']}, got {routed_agent}")
                    else:
                        print(f"\n❌ NO ROUTING DETECTED")
                    
                    # Clean up thread
                    await service_client.agents.delete_thread(thread_id=thread_id)
                    
                except Exception as e:
                    logger.error(f"Error in test case: {e}")
                    routing_results.append({
                        "test": test_case['name'],
                        "expected": test_case['expected_agent'],
                        "actual": None,
                        "routing_detected": False,
                        "reasoning": None,
                        "success": False,
                        "error": str(e)
                    })
            
            # Print summary
            print(f"\n{'='*80}")
            print("ROUTING TEST SUMMARY")
            print('='*80)
            
            total_tests = len(routing_results)
            successful_routes = sum(1 for r in routing_results if r['success'])
            detected_routes = sum(1 for r in routing_results if r['routing_detected'])
            
            print(f"Total Tests: {total_tests}")
            print(f"Routing Detected: {detected_routes}/{total_tests} ({detected_routes/total_tests*100:.0f}%)")
            print(f"Correct Routing: {successful_routes}/{total_tests} ({successful_routes/total_tests*100:.0f}%)")
            
            print("\nDetailed Results:")
            for result in routing_results:
                status = "✅" if result['success'] else "❌"
                print(f"\n{status} {result['test']}:")
                print(f"   Expected: {result['expected']}")
                print(f"   Actual: {result['actual'] or 'No routing'}")
                if result.get('error'):
                    print(f"   Error: {result['error']}")
            
            # Overall assessment
            print(f"\n{'='*80}")
            print("OVERALL ASSESSMENT")
            print('='*80)
            
            if detected_routes == total_tests and successful_routes == total_tests:
                print("✅ EXCELLENT! The Main Orchestrator is routing all requests correctly!")
            elif detected_routes == total_tests:
                print("✅ GOOD! The Main Orchestrator is using routing tools, but some routes are incorrect.")
                print("   Consider refining the orchestrator's instructions for better accuracy.")
            elif detected_routes > 0:
                print("⚠️  PARTIAL SUCCESS: The Main Orchestrator routes some requests but not all.")
                print("   The orchestrator may need clearer instructions about when to route.")
            else:
                print("❌ FAILURE: The Main Orchestrator is not using the routing tools.")
                print("   Check the orchestrator's instructions and tool configuration.")
                
    except Exception as e:
        logger.error(f"Error during routing test: {str(e)}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(test_routing_behavior())