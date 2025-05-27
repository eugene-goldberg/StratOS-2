#!/usr/bin/env python3
"""
Comprehensive test that invokes ALL 15 agents through the Main Orchestrator
and captures complete telemetry for each agent invocation.
"""

import asyncio
import os
import sys
import json
from datetime import datetime
import uuid
from typing import Dict, List, Any

# Add the parent directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from azure.ai.projects.aio import AIProjectClient
from azure.identity.aio import DefaultAzureCredential
from core.telemetry import initialize_telemetry
from opentelemetry import trace

# Initialize telemetry with explicit connection string
connection_string = "InstrumentationKey=189923ab-6ad8-408f-b3f6-7ae4817a3988;IngestionEndpoint=https://eastus-8.in.applicationinsights.azure.com/;LiveEndpoint=https://eastus.livediagnostics.monitor.azure.com/;ApplicationId=dfba6d9b-7df1-4bf5-af6a-2fb21f1881b2"
tracer = initialize_telemetry(
    service_name="All15AgentsTest",
    service_version="1.0.0",
    connection_string=connection_string
)

# Agent test configurations - one test case per agent
AGENT_TEST_CASES = [
    # Strategic Foundation & Insights System (5 agents)
    {
        "name": "CEOLogAgent",
        "message": "I need to record a strategic decision about expanding into the Asian market",
        "expected_function": "invoke_ceologagent"
    },
    {
        "name": "CEOMemoryAgent", 
        "message": "What strategic decisions have we made in the last quarter?",
        "expected_function": "invoke_ceomemoryagent"
    },
    {
        "name": "CEOPreferenceLearningAgent",
        "message": "What are my typical preferences when making expansion decisions?",
        "expected_function": "invoke_ceopreferencelearningagent"
    },
    {
        "name": "NorthStarAgent",
        "message": "What is our current north star metric and how are we tracking?",
        "expected_function": "invoke_northstaragent"
    },
    {
        "name": "InsightSynthesisAgent",
        "message": "Synthesize insights from our recent strategic decisions and market analysis",
        "expected_function": "invoke_insightsynthesisagent"
    },
    
    # Analysis & Intelligence System (4 agents)
    {
        "name": "SWOTTOWSAgent",
        "message": "Perform a SWOT analysis for our planned Asian market expansion",
        "expected_function": "invoke_swottowsagent"
    },
    {
        "name": "RiskOpportunityAgent",
        "message": "Identify risks and opportunities for our new AI product launch",
        "expected_function": "invoke_riskopportunityagent"
    },
    {
        "name": "StrategicContextRouter",
        "message": "Provide strategic context for our Q4 planning session",
        "expected_function": "invoke_strategiccontextrouter"
    },
    {
        "name": "SOLinkageAgent",
        "message": "Link my subjective insights about team morale to our objective performance metrics",
        "expected_function": "invoke_solinkageagent"
    },
    
    # Planning & Execution System (6 agents)
    {
        "name": "PlanningCoordinator",
        "message": "Create a comprehensive plan for our digital transformation initiative",
        "expected_function": "invoke_planningcoordinator"
    },
    {
        "name": "InitiativeGenerator",
        "message": "Generate strategic initiatives based on our SWOT analysis",
        "expected_function": "invoke_initiativegenerator"
    },
    {
        "name": "ResourceOptimizer",
        "message": "Optimize resource allocation for our three concurrent projects",
        "expected_function": "invoke_resourceoptimizer"
    },
    {
        "name": "TimelineStrategist",
        "message": "Create a timeline for our product roadmap deliverables",
        "expected_function": "invoke_timelinestrategist"
    },
    {
        "name": "DependencyMapper",
        "message": "Map dependencies between our strategic initiatives",
        "expected_function": "invoke_dependencymapper"
    },
    {
        "name": "ExecutionTracker",
        "message": "Track execution progress on our Q3 strategic initiatives",
        "expected_function": "invoke_executiontracker"
    }
]

# Main Orchestrator ID
MAIN_ORCHESTRATOR_ID = "asst_IkSbH3d9TaRWfpOcCCE4QxK4"


async def test_single_agent(client: AIProjectClient, test_case: Dict[str, str], test_id: str) -> Dict[str, Any]:
    """Test a single agent through the orchestrator."""
    agent_name = test_case["name"]
    message = test_case["message"]
    expected_function = test_case["expected_function"]
    
    print(f"\n{'='*80}")
    print(f"Testing {agent_name}")
    print(f"Message: {message}")
    print(f"Expected function: {expected_function}")
    print(f"Test ID: {test_id}")
    print("="*80)
    
    result = {
        "agent_name": agent_name,
        "message": message,
        "expected_function": expected_function,
        "test_id": test_id,
        "success": False,
        "error": None,
        "telemetry": {}
    }
    
    with tracer.start_as_current_span(f"test_{agent_name}") as span:
        span.set_attribute("agent.name", agent_name)
        span.set_attribute("test.message", message)
        span.set_attribute("test.id", test_id)
        
        try:
            # Create thread for orchestrator
            print(f"[{agent_name}] Creating orchestrator thread...")
            orchestrator_thread = await client.agents.threads.create()
            orchestrator_thread_id = orchestrator_thread.id
            result["telemetry"]["orchestrator_thread_id"] = orchestrator_thread_id
            span.set_attribute("orchestrator.thread_id", orchestrator_thread_id)
            
            # Send message
            print(f"[{agent_name}] Sending message to orchestrator...")
            await client.agents.messages.create(
                thread_id=orchestrator_thread_id,
                role="user",
                content=message
            )
            span.add_event("message_sent", {"content": message[:100]})
            
            # Create run
            print(f"[{agent_name}] Creating orchestrator run...")
            orchestrator_run = await client.agents.runs.create(
                thread_id=orchestrator_thread_id,
                agent_id=MAIN_ORCHESTRATOR_ID
            )
            orchestrator_run_id = orchestrator_run.id
            result["telemetry"]["orchestrator_run_id"] = orchestrator_run_id
            span.set_attribute("orchestrator.run_id", orchestrator_run_id)
            
            # Wait for orchestrator to process
            print(f"[{agent_name}] Waiting for orchestrator response...")
            max_attempts = 30
            attempt = 0
            tool_call_detected = False
            
            while attempt < max_attempts:
                await asyncio.sleep(2)
                run_status = await client.agents.runs.get(
                    thread_id=orchestrator_thread_id,
                    run_id=orchestrator_run_id
                )
                
                status = run_status.status
                print(f"[{agent_name}] Attempt {attempt + 1}: Status = {status}")
                span.add_event(f"status_check_{attempt + 1}", {"status": status})
                
                if status == "requires_action":
                    if hasattr(run_status, 'required_action') and run_status.required_action:
                        tool_calls = run_status.required_action.submit_tool_outputs.tool_calls
                        if tool_calls:
                            tool_call = tool_calls[0]
                            function_name = tool_call.function.name
                            arguments = tool_call.function.arguments
                            tool_call_id = tool_call.id
                            
                            print(f"[{agent_name}] Tool call detected: {function_name}")
                            print(f"[{agent_name}] Arguments: {arguments[:100]}...")
                            
                            result["telemetry"]["tool_call"] = {
                                "function": function_name,
                                "arguments": arguments,
                                "tool_call_id": tool_call_id
                            }
                            
                            span.add_event("tool_call_detected", {
                                "function": function_name,
                                "tool_call_id": tool_call_id
                            })
                            
                            # Verify it's the expected function
                            if function_name.lower() == expected_function.lower():
                                tool_call_detected = True
                                result["telemetry"]["correct_routing"] = True
                                
                                # Submit a response
                                response = f"This is a response from {agent_name} confirming the request was processed: {message[:50]}..."
                                
                                print(f"[{agent_name}] Submitting tool output...")
                                await client.agents.runs.submit_tool_outputs(
                                    thread_id=orchestrator_thread_id,
                                    run_id=orchestrator_run_id,
                                    tool_outputs=[{
                                        "tool_call_id": tool_call_id,
                                        "output": response
                                    }]
                                )
                                
                                span.add_event("tool_output_submitted", {
                                    "response_length": len(response)
                                })
                            else:
                                result["error"] = f"Wrong function called: {function_name} (expected: {expected_function})"
                                result["telemetry"]["correct_routing"] = False
                                break
                
                elif status == "completed":
                    if tool_call_detected:
                        print(f"[{agent_name}] ✅ Test completed successfully!")
                        result["success"] = True
                        result["telemetry"]["final_status"] = "completed"
                        
                        # Get final response
                        messages = await client.agents.messages.list(
                            thread_id=orchestrator_thread_id,
                            order="desc",
                            limit=1
                        )
                        if messages.value:
                            final_message = messages.value[0]
                            if hasattr(final_message, 'content') and final_message.content:
                                content = final_message.content[0]
                                if hasattr(content, 'text') and hasattr(content.text, 'value'):
                                    result["telemetry"]["final_response"] = str(content.text.value)[:200]
                    else:
                        result["error"] = "Completed without tool call"
                    break
                    
                elif status in ["failed", "cancelled", "expired"]:
                    result["error"] = f"Run failed with status: {status}"
                    if hasattr(run_status, 'last_error') and run_status.last_error:
                        result["error"] += f" - {run_status.last_error.message}"
                    break
                
                attempt += 1
            
            if attempt >= max_attempts:
                result["error"] = "Timeout waiting for orchestrator"
            
            # Cleanup
            try:
                await client.agents.threads.delete(orchestrator_thread_id)
            except:
                pass  # Ignore cleanup errors
            
        except Exception as e:
            result["error"] = f"Exception: {str(e)}"
            span.record_exception(e)
            print(f"[{agent_name}] ❌ Error: {e}")
    
    return result


async def main():
    """Run comprehensive test of all agents."""
    print("="*80)
    print("COMPREHENSIVE TEST: ALL 15 AGENTS WITH TELEMETRY")
    print("="*80)
    print(f"Testing {len(AGENT_TEST_CASES)} agents")
    print(f"Main Orchestrator: {MAIN_ORCHESTRATOR_ID}")
    
    # Generate a unique test ID
    test_id = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
    print(f"Test ID: {test_id}")
    
    # Initialize client with proper endpoint
    credential = DefaultAzureCredential()
    endpoint = "https://ai.azure.com/api/eastus/agents/v1.0/subscriptions/514bd6d3-2c02-45c6-a86f-29cf262a379a/resourceGroups/semantic-kernel-multi-agent-rg/providers/Microsoft.MachineLearningServices/workspaces/sk-multi-agent-project"
    
    client = AIProjectClient(
        endpoint=endpoint,
        subscription_id="514bd6d3-2c02-45c6-a86f-29cf262a379a",
        resource_group_name="semantic-kernel-multi-agent-rg",
        project_name="sk-multi-agent-project",
        credential=credential
    )
    
    # Test all agents
    results = []
    async with client:
        with tracer.start_as_current_span("comprehensive_agent_test") as test_span:
            test_span.set_attribute("test.id", test_id)
            test_span.set_attribute("test.agent_count", len(AGENT_TEST_CASES))
            
            for i, test_case in enumerate(AGENT_TEST_CASES):
                print(f"\n[Progress: {i+1}/{len(AGENT_TEST_CASES)}]")
                result = await test_single_agent(client, test_case, test_id)
                results.append(result)
                
                # Brief pause between tests
                if i < len(AGENT_TEST_CASES) - 1:
                    await asyncio.sleep(3)
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    successful = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]
    
    print(f"\nTotal agents tested: {len(results)}")
    print(f"Successful: {len(successful)} ({len(successful)/len(results)*100:.1f}%)")
    print(f"Failed: {len(failed)} ({len(failed)/len(results)*100:.1f}%)")
    
    if successful:
        print("\n✅ Successful agents:")
        for r in successful:
            print(f"  - {r['agent_name']}")
    
    if failed:
        print("\n❌ Failed agents:")
        for r in failed:
            print(f"  - {r['agent_name']}: {r['error']}")
    
    # Save detailed results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"all_agents_telemetry_{timestamp}.json"
    
    output = {
        "test_id": test_id,
        "timestamp": datetime.now().isoformat(),
        "total_agents": len(results),
        "successful": len(successful),
        "failed": len(failed),
        "success_rate": f"{len(successful)/len(results)*100:.1f}%",
        "results": results
    }
    
    with open(results_file, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\nDetailed results saved to: {results_file}")
    print(f"\nTo query telemetry for this test run:")
    print(f"1. Wait 2-3 minutes for telemetry to appear in Application Insights")
    print(f"2. Query using test.id = '{test_id}'")
    
    # Also print the operation IDs for each successful test
    if successful:
        print("\nOperation IDs for successful tests:")
        for r in successful:
            if "orchestrator_thread_id" in r.get("telemetry", {}):
                print(f"  - {r['agent_name']}: thread={r['telemetry']['orchestrator_thread_id']}")
    
    return len(successful) == len(results)


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)