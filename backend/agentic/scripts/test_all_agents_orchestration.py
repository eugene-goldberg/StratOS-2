#!/usr/bin/env python3
"""
Test ALL 15 specialist agents through the Main Orchestrator.
This verifies end-to-end delegation for every agent.
"""

import asyncio
import os
import json
import sys
from datetime import datetime
from dotenv import load_dotenv
from azure.identity.aio import DefaultAzureCredential
from semantic_kernel.agents import AzureAIAgent, AzureAIAgentSettings

# Load environment
current_dir = os.path.dirname(os.path.abspath(__file__))
agentic_dir = os.path.dirname(current_dir)
env_path = os.path.join(agentic_dir, '.env')
load_dotenv(env_path)

# Test results tracking
TEST_RESULTS = {
    "failures": [],
    "successes": [],
    "agents_tested": set(),
    "agents_not_responding": set(),
    "total_tests": 0,
    "successful_delegations": 0
}

async def test_orchestrator_delegation(client, orchestrator_id: str, test_message: str, expected_agent: str):
    """Test a single orchestrator delegation."""
    TEST_RESULTS["total_tests"] += 1
    
    try:
        # Create thread
        thread = await client.agents.threads.create()
        thread_id = thread.id
        
        # Send message
        await client.agents.messages.create(
            thread_id=thread_id,
            role="user",
            content=test_message
        )
        
        # Run orchestrator
        run = await client.agents.runs.create(
            thread_id=thread_id,
            agent_id=orchestrator_id
        )
        
        # Wait for response
        max_wait = 30
        wait_time = 0
        tool_call_made = False
        specialist_invoked = None
        
        while wait_time < max_wait:
            await asyncio.sleep(1)
            wait_time += 1
            
            run = await client.agents.runs.get(
                thread_id=thread_id,
                run_id=run.id
            )
            
            if run.status == "requires_action":
                # Check tool calls
                tool_calls = run.required_action.submit_tool_outputs.tool_calls
                
                for tool_call in tool_calls:
                    function_name = tool_call.function.name
                    args = json.loads(tool_call.function.arguments)
                    
                    # Extract agent name from function
                    agent_key = function_name.replace("invoke_", "")
                    specialist_invoked = agent_key
                    tool_call_made = True
                    
                    # Find specialist agent ID
                    deployment_path = os.path.join(agentic_dir, "deployment_configs", "ai_project_agents_deployment.json")
                    with open(deployment_path, 'r') as f:
                        deployment_data = json.load(f)
                        specialist_agents = deployment_data['deployed_agents']
                    
                    specialist_id = None
                    for agent_name, agent_id in specialist_agents.items():
                        if agent_name.lower() == agent_key:
                            specialist_id = agent_id
                            TEST_RESULTS["agents_tested"].add(agent_name)
                            break
                    
                    if specialist_id:
                        # Actually invoke the specialist
                        specialist_thread = await client.agents.threads.create()
                        
                        await client.agents.messages.create(
                            thread_id=specialist_thread.id,
                            role="user",
                            content=args.get('request', test_message)
                        )
                        
                        specialist_run = await client.agents.runs.create(
                            thread_id=specialist_thread.id,
                            agent_id=specialist_id
                        )
                        
                        # Wait for specialist
                        specialist_wait = 0
                        while specialist_wait < 15:
                            await asyncio.sleep(1)
                            specialist_wait += 1
                            
                            specialist_run = await client.agents.runs.get(
                                thread_id=specialist_thread.id,
                                run_id=specialist_run.id
                            )
                            
                            if specialist_run.status == "completed":
                                # Get specialist response
                                messages = client.agents.messages.list(thread_id=specialist_thread.id)
                                
                                specialist_response = None
                                async for msg in messages:
                                    if msg.role == "assistant" and msg.content:
                                        for content in msg.content:
                                            if hasattr(content, 'text'):
                                                specialist_response = content.text.value
                                                break
                                        if specialist_response:
                                            break
                                
                                # Submit back to orchestrator
                                await client.agents.runs.submit_tool_outputs(
                                    thread_id=thread_id,
                                    run_id=run.id,
                                    tool_outputs=[{
                                        "tool_call_id": tool_call.id,
                                        "output": specialist_response or "No response"
                                    }]
                                )
                                
                                if specialist_response:
                                    TEST_RESULTS["successful_delegations"] += 1
                                    TEST_RESULTS["successes"].append({
                                        "agent": agent_name,
                                        "message": test_message[:50] + "...",
                                        "response_length": len(specialist_response)
                                    })
                                
                                # Clean up specialist thread
                                await client.agents.threads.delete(thread_id=specialist_thread.id)
                                break
                            
                            elif specialist_run.status in ["failed", "cancelled", "expired"]:
                                TEST_RESULTS["agents_not_responding"].add(agent_name)
                                TEST_RESULTS["failures"].append({
                                    "agent": agent_name,
                                    "error": f"Specialist run failed: {specialist_run.status}"
                                })
                                await client.agents.threads.delete(thread_id=specialist_thread.id)
                                break
                
                break
                
            elif run.status == "completed":
                if not tool_call_made:
                    TEST_RESULTS["failures"].append({
                        "agent": expected_agent,
                        "error": "Orchestrator completed without making tool calls"
                    })
                break
                
            elif run.status in ["failed", "cancelled", "expired"]:
                TEST_RESULTS["failures"].append({
                    "agent": expected_agent,
                    "error": f"Orchestrator run failed: {run.status}"
                })
                break
        
        # Clean up
        await client.agents.threads.delete(thread_id=thread_id)
        
        return tool_call_made, specialist_invoked
        
    except Exception as e:
        TEST_RESULTS["failures"].append({
            "agent": expected_agent,
            "error": str(e)
        })
        return False, None

async def main():
    # Load configurations
    orch_config_path = os.path.join(agentic_dir, "deployment_configs", "main_orchestrator_tools_deployment.json")
    with open(orch_config_path, 'r') as f:
        config = json.load(f)
        orchestrator_id = config['agent_id']
    
    deployment_path = os.path.join(agentic_dir, "deployment_configs", "ai_project_agents_deployment.json")
    with open(deployment_path, 'r') as f:
        deployment_data = json.load(f)
        all_agents = list(deployment_data['deployed_agents'].keys())
    
    print("\n" + "="*80)
    print("COMPREHENSIVE ORCHESTRATION TEST - ALL 15 AGENTS")
    print("="*80)
    print(f"Main Orchestrator: {orchestrator_id}")
    print(f"Total Agents to Test: {len(all_agents)}")
    print()
    
    # Test cases for each agent
    test_cases = [
        ("I need to record my thoughts about the Q4 revenue projections", "CEOLogAgent"),
        ("What's our company's north star metric?", "NorthStarAgent"),
        ("Show me patterns from our past strategic decisions", "MemoryRecallAgent"),
        ("Track my preference for concise executive summaries", "PreferenceLearningAgent"),
        ("Route this strategic planning request appropriately", "StrategicContextRouter"),
        ("Perform a SWOT analysis for our cloud expansion", "SWOTTOWSAgent"),
        ("What are the key risks in our supply chain?", "RiskOpportunityAgent"),
        ("Link my observation about team morale to our productivity metrics", "SOLinkageAgent"),
        ("Analyze the competitive landscape in the AI market", "AnalysisOrchestrator"),
        ("Generate initiatives for 50% revenue growth", "InitiativeGenerationAgent"),
        ("Optimize resource allocation for Q1 projects", "ResourceOptimizationAgent"),
        ("Create an action plan for improving customer satisfaction", "ActionPlanningAgent"),
        ("Score the alignment of our new product launch with strategic goals", "AlignmentScoringAgent"),
        ("Update the strategic canvas with new market insights", "CanvasVisualizationAgent"),
        ("Coordinate the planning activities for next quarter", "PlanningCoordinator")
    ]
    
    settings = AzureAIAgentSettings()
    credential = DefaultAzureCredential()
    
    print("❌ STARTING WITH FAILURE CHECK")
    print("="*60)
    
    async with AzureAIAgent.create_client(credential=credential, settings=settings) as client:
        for i, (test_message, expected_agent) in enumerate(test_cases, 1):
            print(f"\nTEST {i}/{len(test_cases)}: {expected_agent}")
            print(f"Message: {test_message[:60]}...")
            
            tool_called, agent_invoked = await test_orchestrator_delegation(
                client, orchestrator_id, test_message, expected_agent
            )
            
            if tool_called:
                print(f"✅ Tool call made to: {agent_invoked}")
            else:
                print(f"❌ No tool call made")
    
    await credential.close()
    
    # Generate report
    print("\n" + "="*80)
    print("❌ FAILURE-FIRST REPORT")
    print("="*80)
    
    print(f"\n🔴 FAILURES ({len(TEST_RESULTS['failures'])}):")
    if TEST_RESULTS["failures"]:
        for failure in TEST_RESULTS["failures"]:
            print(f"  ❌ {failure['agent']}: {failure['error']}")
    else:
        print("  None")
    
    print(f"\n🟡 AGENTS NOT TESTED ({len(all_agents) - len(TEST_RESULTS['agents_tested'])}):")
    untested = set(all_agents) - TEST_RESULTS["agents_tested"]
    if untested:
        for agent in sorted(untested):
            print(f"  ⚠️  {agent}")
    else:
        print("  None - All agents tested!")
    
    print(f"\n🟢 SUCCESSFUL DELEGATIONS ({TEST_RESULTS['successful_delegations']}):")
    if TEST_RESULTS["successes"]:
        for success in TEST_RESULTS["successes"][:5]:  # Show first 5
            print(f"  ✅ {success['agent']}: {success['response_length']} chars")
    
    print(f"\n📊 SUMMARY:")
    print(f"  Total Tests: {TEST_RESULTS['total_tests']}")
    print(f"  Successful Delegations: {TEST_RESULTS['successful_delegations']}")
    print(f"  Agents Tested: {len(TEST_RESULTS['agents_tested'])}/15")
    print(f"  Agents Not Responding: {len(TEST_RESULTS['agents_not_responding'])}")
    
    # Final verdict
    print("\n" + "="*80)
    success_rate = TEST_RESULTS['successful_delegations'] / TEST_RESULTS['total_tests'] * 100 if TEST_RESULTS['total_tests'] > 0 else 0
    
    if success_rate >= 80 and len(TEST_RESULTS['agents_tested']) >= 13:
        print(f"✅ ORCHESTRATION IS WORKING! Success rate: {success_rate:.1f}%")
    else:
        print(f"❌ ORCHESTRATION NEEDS WORK. Success rate: {success_rate:.1f}%")
        print(f"   Only {len(TEST_RESULTS['agents_tested'])}/15 agents tested successfully")
    
    # Save results
    results_file = f"orchestration_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, 'w') as f:
        json.dump(TEST_RESULTS, f, indent=2, default=str)
    print(f"\n💾 Detailed results saved to: {results_file}")

if __name__ == "__main__":
    asyncio.run(main())