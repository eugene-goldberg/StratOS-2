#!/usr/bin/env python3
"""
Extended routing test for the Main Orchestrator.
Tests multiple agents from each system.
"""

import asyncio
import os
import json
from dotenv import load_dotenv
from azure.identity.aio import DefaultAzureCredential
from semantic_kernel.agents import AzureAIAgent, AzureAIAgentSettings

# Load environment
current_dir = os.path.dirname(os.path.abspath(__file__))
agentic_dir = os.path.dirname(current_dir)
env_path = os.path.join(agentic_dir, '.env')
load_dotenv(env_path)

async def test_single_routing(client, orchestrator_id, test_message):
    """Test a single routing scenario."""
    # Create thread
    thread = await client.agents.threads.create()
    thread_id = thread.id
    
    # Add message
    await client.agents.messages.create(
        thread_id=thread_id,
        role="user", 
        content=test_message
    )
    
    # Create run
    run = await client.agents.runs.create(
        thread_id=thread_id,
        agent_id=orchestrator_id
    )
    
    # Wait for completion with timeout
    max_wait = 30  # 30 seconds max
    wait_time = 0
    while run.status in ["queued", "in_progress"] and wait_time < max_wait:
        await asyncio.sleep(1)
        wait_time += 1
        run = await client.agents.runs.get(
            thread_id=thread_id,
            run_id=run.id
        )
    
    if run.status not in ["completed", "failed"]:
        # Clean up and return timeout
        await client.agents.threads.delete(thread_id=thread_id)
        return "TIMEOUT", None
    
    # Get the latest assistant message
    messages = client.agents.messages.list(thread_id=thread_id)
    
    routing_response = None
    async for msg in messages:
        if msg.role == "assistant" and msg.content:
            for content in msg.content:
                if hasattr(content, 'text'):
                    routing_response = content.text.value
                    break
            if routing_response:
                break
    
    # Clean up
    await client.agents.threads.delete(thread_id=thread_id)
    
    # Parse routing response
    if routing_response and "ROUTE TO:" in routing_response:
        parts = routing_response.split("ROUTE TO:")[1].split("-")
        if parts:
            routed_agent = parts[0].strip()
            return routing_response, routed_agent
    
    return routing_response, None

async def main():
    # Load orchestrator ID
    config_path = os.path.join(agentic_dir, "deployment_configs", "main_orchestrator_deployment.json")
    with open(config_path, 'r') as f:
        config = json.load(f)
        orchestrator_id = config['agent_id']
    
    print(f"Testing Main Orchestrator Extended Routes: {orchestrator_id}")
    print("=" * 80)
    
    # Extended test scenarios based on actual deployed agents
    test_scenarios = [
        # Strategic Foundation & Insights System
        {
            "system": "Strategic Foundation & Insights", 
            "tests": [
                ("I need to record my thoughts about the market downturn", ["CEOLogAgent"]),
                ("What are our north star goals and OKRs?", ["NorthStarAgent"]),
                ("Remember I prefer concise executive summaries", ["PreferenceLearningAgent"]),
                ("What strategies worked in our last expansion?", ["MemoryRecallAgent"]),
                ("Show me our strategic context and priorities", ["StrategicContextRouter"])
            ]
        },
        
        # Analysis & Intelligence System
        {
            "system": "Analysis & Intelligence",
            "tests": [
                ("Can you perform a SWOT analysis for our new product?", ["SWOTTOWSAgent"]),
                ("What are the risks and opportunities in the market?", ["RiskOpportunityAgent"]),
                ("Link our subjective insights to objective data", ["SOLinkageAgent"]),
                ("Analyze our competitive position", ["AnalysisOrchestrator", "SWOTTOWSAgent"])
            ]
        },
        
        # Planning & Execution System
        {
            "system": "Planning & Execution",
            "tests": [
                ("Generate strategic initiatives for growth", ["InitiativeGenerationAgent", "StrategicInitiativesAgent"]),
                ("How should we allocate resources for Q4?", ["ResourceOptimizationAgent"]),
                ("Create action plans for our initiatives", ["ActionPlanningAgent"]),
                ("Score alignment of initiatives with goals", ["AlignmentScoringAgent"]),
                ("Visualize our strategic plans on a canvas", ["CanvasVisualizationAgent"]),
                ("Coordinate our planning activities", ["PlanningCoordinator"])
            ]
        }
    ]
    
    settings = AzureAIAgentSettings()
    credential = DefaultAzureCredential()
    
    async with AzureAIAgent.create_client(credential=credential, settings=settings) as client:
        system_results = {}
        total_passed = 0
        total_tests = 0
        
        for system_test in test_scenarios:
            system_name = system_test["system"]
            system_results[system_name] = {"passed": 0, "total": 0}
            
            print(f"\n{'='*60}")
            print(f"Testing: {system_name}")
            print(f"{'='*60}")
            
            for test_message, expected_agents in system_test["tests"]:
                total_tests += 1
                system_results[system_name]["total"] += 1
                
                print(f"\nTest: \"{test_message}\"")
                print(f"Expected: {' or '.join(expected_agents)}")
                
                try:
                    response, routed_agent = await test_single_routing(client, orchestrator_id, test_message)
                    
                    if response == "TIMEOUT":
                        print(f"Result: ❌ TIMEOUT")
                    elif routed_agent:
                        # Check if routing matches any expected agent
                        success = any(expected in routed_agent or routed_agent in expected 
                                    for expected in expected_agents)
                        
                        status = "✅ PASS" if success else "❌ FAIL"
                        print(f"Result: {status}")
                        print(f"Routed to: {routed_agent}")
                        
                        if success:
                            total_passed += 1
                            system_results[system_name]["passed"] += 1
                    else:
                        print(f"Result: ❌ FAIL - Could not parse routing")
                        if response:
                            print(f"Response: {response[:100]}...")
                        
                except Exception as e:
                    print(f"Result: ❌ ERROR - {str(e)}")
                
                # Small delay between tests
                await asyncio.sleep(0.5)
        
        # Summary
        print("\n" + "=" * 80)
        print("EXTENDED ROUTING TEST SUMMARY")
        print("=" * 80)
        
        print(f"\nOverall Results:")
        print(f"  Total Tests: {total_tests}")
        print(f"  Passed: {total_passed}")
        print(f"  Failed: {total_tests - total_passed}")
        print(f"  Success Rate: {(total_passed/total_tests)*100:.1f}%")
        
        print(f"\nPer-System Results:")
        for system_name, results in system_results.items():
            passed = results["passed"]
            total = results["total"]
            rate = (passed/total)*100 if total > 0 else 0
            print(f"  {system_name}: {passed}/{total} ({rate:.1f}%)")
        
        if total_passed == total_tests:
            print("\n✅ All routing tests passed!")
        else:
            print(f"\n⚠️  {total_tests - total_passed} tests failed")
    
    await credential.close()

if __name__ == "__main__":
    asyncio.run(main())