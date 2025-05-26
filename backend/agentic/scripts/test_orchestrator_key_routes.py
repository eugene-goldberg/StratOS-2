#!/usr/bin/env python3
"""
Test key routing scenarios for the Main Orchestrator.
Tests one scenario per multi-agent system to verify routing works.
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
        return "TIMEOUT"
    
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
    
    return routing_response

async def main():
    # Load orchestrator ID
    config_path = os.path.join(agentic_dir, "deployment_configs", "main_orchestrator_deployment.json")
    with open(config_path, 'r') as f:
        config = json.load(f)
        orchestrator_id = config['agent_id']
    
    print(f"Testing Main Orchestrator Key Routes: {orchestrator_id}")
    print("=" * 80)
    
    # Key test scenarios - one per multi-agent system
    test_scenarios = [
        # Strategic Foundation & Insights System
        {
            "system": "Strategic Foundation & Insights",
            "test": "I need to record my thoughts about the market downturn",
            "expected": "CEOLogAgent"
        },
        
        # Analysis & Intelligence System  
        {
            "system": "Analysis & Intelligence",
            "test": "Can you perform a SWOT analysis for our new product?",
            "expected": "SWOTTOWSAgent"
        },
        
        # Planning & Execution System
        {
            "system": "Planning & Execution",
            "test": "Generate strategic initiatives for our digital transformation",
            "expected": "InitiativeGenerationAgent"
        }
    ]
    
    settings = AzureAIAgentSettings()
    credential = DefaultAzureCredential()
    
    async with AzureAIAgent.create_client(credential=credential, settings=settings) as client:
        results = []
        
        for scenario in test_scenarios:
            print(f"\n{'='*60}")
            print(f"System: {scenario['system']}")
            print(f"Test: \"{scenario['test']}\"")
            print(f"Expected: {scenario['expected']}")
            
            try:
                response = await test_single_routing(client, orchestrator_id, scenario['test'])
                
                if response == "TIMEOUT":
                    print(f"Result: ❌ TIMEOUT")
                    results.append({
                        "system": scenario['system'],
                        "success": False,
                        "reason": "Timeout"
                    })
                elif response and "ROUTE TO:" in response:
                    # Extract the routed agent name
                    parts = response.split("ROUTE TO:")[1].split("-")
                    if parts:
                        routed_agent = parts[0].strip()
                        reason = response.split("REASON:")[1].strip() if "REASON:" in response else ""
                        
                        # Check if routing is correct
                        success = scenario['expected'] in routed_agent or routed_agent in scenario['expected']
                        status = "✅ PASS" if success else "❌ FAIL"
                        
                        print(f"Result: {status}")
                        print(f"Routed to: {routed_agent}")
                        if reason:
                            print(f"Reason: {reason[:100]}...")
                        
                        results.append({
                            "system": scenario['system'],
                            "success": success,
                            "routed_to": routed_agent
                        })
                else:
                    print(f"Result: ❌ FAIL - Invalid response format")
                    print(f"Response: {response[:200] if response else 'No response'}...")
                    
                    results.append({
                        "system": scenario['system'],
                        "success": False,
                        "reason": "Invalid format"
                    })
                    
            except Exception as e:
                print(f"Result: ❌ ERROR - {str(e)}")
                results.append({
                    "system": scenario['system'],
                    "success": False,
                    "reason": str(e)
                })
        
        # Summary
        print("\n" + "=" * 80)
        print("ROUTING TEST SUMMARY")
        print("=" * 80)
        
        passed = sum(1 for r in results if r["success"])
        total = len(results)
        
        print(f"\nTotal Systems Tested: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        
        if passed == total:
            print("\n✅ All multi-agent systems are routing correctly!")
        else:
            print("\n❌ Some systems failed routing tests")
            for r in results:
                if not r["success"]:
                    print(f"  - {r['system']}: {r.get('reason', 'Failed')}")
    
    await credential.close()

if __name__ == "__main__":
    asyncio.run(main())