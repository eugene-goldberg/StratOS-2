#!/usr/bin/env python3
"""
Test orchestration with TELEMETRY PROOF for each delegation.
This script captures and displays telemetry evidence for each agent invocation.
"""

import asyncio
import os
import json
import sys
from datetime import datetime
from dotenv import load_dotenv
from azure.identity.aio import DefaultAzureCredential
from semantic_kernel.agents import AzureAIAgent, AzureAIAgentSettings

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.telemetry import initialize_telemetry

# Load environment
current_dir = os.path.dirname(os.path.abspath(__file__))
agentic_dir = os.path.dirname(current_dir)
env_path = os.path.join(agentic_dir, '.env')
load_dotenv(env_path)

# Initialize telemetry
tracer = initialize_telemetry(
    service_name="OrchestrationTelemetryProof",
    service_version="1.0.0",
    connection_string=os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
)

# Track all telemetry evidence
TELEMETRY_EVIDENCE = {
    "test_start": datetime.now().isoformat(),
    "delegations": [],
    "traces_captured": []
}

async def test_single_delegation_with_proof(client, orchestrator_id: str, test_case: dict):
    """Test a single delegation and capture telemetry proof."""
    test_name = test_case["name"]
    test_message = test_case["message"]
    expected_agent = test_case["expected_agent"]
    
    delegation_evidence = {
        "test_name": test_name,
        "expected_agent": expected_agent,
        "message": test_message,
        "start_time": datetime.now().isoformat(),
        "orchestrator_thread": None,
        "tool_call": None,
        "specialist_thread": None,
        "specialist_response": None,
        "orchestrator_final_response": None,
        "end_time": None,
        "success": False
    }
    
    with tracer.start_as_current_span(f"test_delegation_{test_name}") as span:
        span.set_attribute("test.name", test_name)
        span.set_attribute("test.expected_agent", expected_agent)
        span.set_attribute("test.message", test_message)
        
        try:
            # Step 1: Create orchestrator thread
            print(f"\n{'='*60}")
            print(f"TESTING: {test_name}")
            print(f"Expected: {expected_agent}")
            print(f"Message: {test_message[:50]}...")
            
            thread = await client.agents.threads.create()
            thread_id = thread.id
            delegation_evidence["orchestrator_thread"] = thread_id
            
            span.set_attribute("orchestrator.thread_id", thread_id)
            print(f"📝 Orchestrator thread: {thread_id}")
            
            # Step 2: Send message
            await client.agents.messages.create(
                thread_id=thread_id,
                role="user",
                content=test_message
            )
            
            # Step 3: Run orchestrator
            run = await client.agents.runs.create(
                thread_id=thread_id,
                agent_id=orchestrator_id
            )
            
            span.set_attribute("orchestrator.run_id", run.id)
            
            # Step 4: Wait for orchestrator response
            max_wait = 30
            wait_time = 0
            
            while wait_time < max_wait:
                await asyncio.sleep(1)
                wait_time += 1
                
                run = await client.agents.runs.get(
                    thread_id=thread_id,
                    run_id=run.id
                )
                
                if run.status == "requires_action":
                    # Capture tool call evidence
                    tool_calls = run.required_action.submit_tool_outputs.tool_calls
                    
                    for tool_call in tool_calls:
                        function_name = tool_call.function.name
                        args = json.loads(tool_call.function.arguments)
                        
                        delegation_evidence["tool_call"] = {
                            "function": function_name,
                            "arguments": args,
                            "tool_call_id": tool_call.id
                        }
                        
                        span.set_attribute("tool_call.function", function_name)
                        span.set_attribute("tool_call.arguments", json.dumps(args))
                        
                        print(f"🔧 Tool call: {function_name}")
                        print(f"   Arguments: {json.dumps(args, indent=2)}")
                        
                        # Find specialist agent
                        agent_key = function_name.replace("invoke_", "")
                        
                        deployment_path = os.path.join(agentic_dir, "deployment_configs", "ai_project_agents_deployment.json")
                        with open(deployment_path, 'r') as f:
                            deployment_data = json.load(f)
                            specialist_agents = deployment_data['deployed_agents']
                        
                        specialist_id = None
                        for agent_name, agent_id in specialist_agents.items():
                            if agent_name.lower() == agent_key:
                                specialist_id = agent_id
                                break
                        
                        if specialist_id:
                            # Step 5: Invoke specialist with telemetry
                            with tracer.start_as_current_span(f"invoke_specialist_{agent_name}") as specialist_span:
                                specialist_span.set_attribute("specialist.name", agent_name)
                                specialist_span.set_attribute("specialist.id", specialist_id)
                                
                                specialist_thread = await client.agents.threads.create()
                                delegation_evidence["specialist_thread"] = specialist_thread.id
                                
                                specialist_span.set_attribute("specialist.thread_id", specialist_thread.id)
                                print(f"🤖 Specialist thread: {specialist_thread.id}")
                                
                                await client.agents.messages.create(
                                    thread_id=specialist_thread.id,
                                    role="user",
                                    content=args.get('request', test_message)
                                )
                                
                                specialist_run = await client.agents.runs.create(
                                    thread_id=specialist_thread.id,
                                    agent_id=specialist_id
                                )
                                
                                specialist_span.set_attribute("specialist.run_id", specialist_run.id)
                                
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
                                        
                                        async for msg in messages:
                                            if msg.role == "assistant" and msg.content:
                                                for content in msg.content:
                                                    if hasattr(content, 'text'):
                                                        specialist_response = content.text.value
                                                        delegation_evidence["specialist_response"] = {
                                                            "text": specialist_response[:200] + "..." if len(specialist_response) > 200 else specialist_response,
                                                            "length": len(specialist_response)
                                                        }
                                                        
                                                        specialist_span.set_attribute("specialist.response_length", len(specialist_response))
                                                        print(f"✅ Specialist responded: {len(specialist_response)} chars")
                                                        break
                                                if delegation_evidence["specialist_response"]:
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
                                        
                                        # Clean up specialist thread
                                        await client.agents.threads.delete(thread_id=specialist_thread.id)
                                        break
                                    
                                    elif specialist_run.status in ["failed", "cancelled", "expired"]:
                                        specialist_span.set_attribute("specialist.error", specialist_run.status)
                                        print(f"❌ Specialist failed: {specialist_run.status}")
                                        await client.agents.threads.delete(thread_id=specialist_thread.id)
                                        break
                    
                    break
                
                elif run.status == "completed":
                    # Get final orchestrator response
                    messages = client.agents.messages.list(thread_id=thread_id)
                    
                    async for msg in messages:
                        if msg.role == "assistant" and msg.content:
                            for content in msg.content:
                                if hasattr(content, 'text'):
                                    final_response = content.text.value
                                    delegation_evidence["orchestrator_final_response"] = final_response[:200] + "..."
                                    delegation_evidence["success"] = True
                                    span.set_attribute("orchestrator.final_response_length", len(final_response))
                                    print(f"💬 Orchestrator final response: {len(final_response)} chars")
                                    break
                            if delegation_evidence["orchestrator_final_response"]:
                                break
                    break
                
                elif run.status in ["failed", "cancelled", "expired"]:
                    span.set_attribute("orchestrator.error", run.status)
                    print(f"❌ Orchestrator failed: {run.status}")
                    break
            
            # Clean up
            await client.agents.threads.delete(thread_id=thread_id)
            
        except Exception as e:
            span.set_attribute("error", str(e))
            delegation_evidence["error"] = str(e)
            print(f"❌ Error: {str(e)}")
        
        delegation_evidence["end_time"] = datetime.now().isoformat()
        TELEMETRY_EVIDENCE["delegations"].append(delegation_evidence)

async def main():
    # Test only a few key agents for telemetry proof
    test_cases = [
        {
            "name": "CEO_Log_Test",
            "message": "I need to record that we just signed a $10M deal with Amazon",
            "expected_agent": "CEOLogAgent"
        },
        {
            "name": "SWOT_Analysis_Test", 
            "message": "Perform a SWOT analysis for our expansion into Europe",
            "expected_agent": "SWOTTOWSAgent"
        },
        {
            "name": "Risk_Assessment_Test",
            "message": "What are the main cybersecurity risks we face?",
            "expected_agent": "RiskOpportunityAgent"
        }
    ]
    
    # Load orchestrator config
    orch_config_path = os.path.join(agentic_dir, "deployment_configs", "main_orchestrator_tools_deployment.json")
    with open(orch_config_path, 'r') as f:
        config = json.load(f)
        orchestrator_id = config['agent_id']
    
    print("\n" + "="*80)
    print("ORCHESTRATION WITH TELEMETRY PROOF")
    print("="*80)
    print(f"Service: OrchestrationTelemetryProof")
    print(f"Orchestrator: {orchestrator_id}")
    print(f"Tests: {len(test_cases)}")
    
    settings = AzureAIAgentSettings()
    credential = DefaultAzureCredential()
    
    async with AzureAIAgent.create_client(credential=credential, settings=settings) as client:
        for test_case in test_cases:
            await test_single_delegation_with_proof(client, orchestrator_id, test_case)
    
    await credential.close()
    
    # Generate telemetry evidence report
    print("\n" + "="*80)
    print("📊 TELEMETRY EVIDENCE REPORT")
    print("="*80)
    
    successful_delegations = [d for d in TELEMETRY_EVIDENCE["delegations"] if d["success"]]
    
    print(f"\n✅ SUCCESSFUL DELEGATIONS WITH PROOF: {len(successful_delegations)}")
    for delegation in successful_delegations:
        print(f"\n{delegation['test_name']}:")
        print(f"  1. Orchestrator Thread: {delegation['orchestrator_thread']}")
        print(f"  2. Tool Call: {delegation['tool_call']['function'] if delegation['tool_call'] else 'None'}")
        print(f"  3. Specialist Thread: {delegation['specialist_thread']}")
        print(f"  4. Specialist Response: {delegation['specialist_response']['length'] if delegation['specialist_response'] else 0} chars")
        print(f"  5. Orchestrator Final: ✓")
        print(f"  Duration: {delegation['start_time']} to {delegation['end_time']}")
    
    failed_delegations = [d for d in TELEMETRY_EVIDENCE["delegations"] if not d["success"]]
    
    print(f"\n❌ FAILED DELEGATIONS: {len(failed_delegations)}")
    for delegation in failed_delegations:
        print(f"\n{delegation['test_name']}:")
        print(f"  Error: {delegation.get('error', 'Unknown')}")
    
    # Save evidence
    evidence_file = f"telemetry_evidence_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(evidence_file, 'w') as f:
        json.dump(TELEMETRY_EVIDENCE, f, indent=2)
    print(f"\n💾 Telemetry evidence saved to: {evidence_file}")
    
    print("\n🔍 To verify in Application Insights:")
    print("   1. Go to Azure Portal > Application Insights")
    print("   2. Search for service.name = 'OrchestrationTelemetryProof'")
    print("   3. Look for spans showing the complete flow")

if __name__ == "__main__":
    asyncio.run(main())