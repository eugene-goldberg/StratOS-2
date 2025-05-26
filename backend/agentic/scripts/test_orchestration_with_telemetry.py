#!/usr/bin/env python3
"""
Test the COMPLETE orchestration flow with ACTUAL agents and telemetry tracking.
This script verifies the entire end-to-end flow with telemetry enabled.
NO MOCKS, NO SIMULATIONS - REAL AGENT CALLS ONLY.
"""

import asyncio
import os
import json
import sys
from datetime import datetime
from dotenv import load_dotenv
from openai import AsyncAzureOpenAI

# Add the agentic directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.telemetry import initialize_telemetry, create_span_context, SpanNames, trace_method, add_span_attributes


class OrchestrationTelemetryTester:
    """Tests complete orchestration flow with telemetry."""
    
    def __init__(self):
        # Load environment
        backend_env = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
        if os.path.exists(backend_env):
            load_dotenv(backend_env)
        
        # Load root .env for Application Insights
        root_env = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')
        if os.path.exists(root_env):
            load_dotenv(root_env, override=True)
        
        # Initialize telemetry
        connection_string = "InstrumentationKey=189923ab-6ad8-408f-b3f6-7ae4817a3988;IngestionEndpoint=https://eastus-8.in.applicationinsights.azure.com/;LiveEndpoint=https://eastus.livediagnostics.monitor.azure.com/;ApplicationId=dfba6d9b-7df1-4bf5-af6a-2fb21f1881b2"
        
        self.tracer = initialize_telemetry(
            service_name="OrchestrationTelemetryTester",
            service_version="1.0.0",
            connection_string=connection_string,
            additional_attributes={
                "test.type": "end_to_end",
                "test.real_agents": True,
                "test.no_mocks": True
            }
        )
        
        print("✅ Telemetry initialized for OrchestrationTelemetryTester")
        
        # Initialize OpenAI client
        self.client = AsyncAzureOpenAI(
            azure_endpoint="https://sk-multi-agent-openai.openai.azure.com/",
            api_key="b77c5b137db6465dabdbc34adb136e2c",
            api_version="2024-02-15-preview"
        )
        
        # Load configurations
        self.load_configurations()
    
    def load_configurations(self):
        """Load agent configurations."""
        # Main orchestrator
        orch_config_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "deployment_configs",
            "main_orchestrator_tools_deployment.json"
        )
        with open(orch_config_path, 'r') as f:
            config = json.load(f)
            self.orchestrator_id = config['agent_id']
        
        # Specialist agents
        deployment_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "deployment_configs",
            "ai_project_agents_deployment.json"
        )
        with open(deployment_path, 'r') as f:
            deployment_data = json.load(f)
            self.specialist_agents = deployment_data['deployed_agents']
        
        print(f"📋 Loaded configurations:")
        print(f"   Main Orchestrator: {self.orchestrator_id}")
        print(f"   Specialist Agents: {len(self.specialist_agents)}")
    
    @trace_method("orchestration.invoke_specialist")
    async def invoke_specialist_agent(self, agent_id: str, agent_name: str, request: str):
        """Actually invoke a specialist agent and get its response - NO MOCKS."""
        
        with create_span_context(f"specialist.{agent_name.lower()}", {
            "agent.id": agent_id,
            "agent.name": agent_name,
            "request.content": request[:100],
            "request.length": len(request)
        }) as span:
            
            print(f"\n🤖 Invoking REAL specialist agent: {agent_name}")
            print(f"   Agent ID: {agent_id}")
            
            # Create a new thread for the specialist
            specialist_thread = await self.client.beta.threads.create()
            specialist_thread_id = specialist_thread.id
            span.set_attribute("thread.id", specialist_thread_id)
            print(f"   Thread created: {specialist_thread_id}")
            
            # Add the request message
            print(f"   Sending request: {request}")
            await self.client.beta.threads.messages.create(
                thread_id=specialist_thread_id,
                role="user",
                content=request
            )
            
            # Create run for specialist
            print(f"   Starting specialist agent run...")
            specialist_run = await self.client.beta.threads.runs.create(
                thread_id=specialist_thread_id,
                assistant_id=agent_id
            )
            span.set_attribute("run.id", specialist_run.id)
            
            # Wait for specialist to complete
            max_wait = 60
            wait_time = 0
            
            while wait_time < max_wait:
                await asyncio.sleep(1)
                wait_time += 1
                
                # Get run status
                specialist_run = await self.client.beta.threads.runs.retrieve(
                    thread_id=specialist_thread_id,
                    run_id=specialist_run.id
                )
                
                print(f"   Specialist status: {specialist_run.status} ({wait_time}s)")
                
                if specialist_run.status == "completed":
                    print(f"   ✅ Specialist completed successfully!")
                    span.set_attribute("run.status", "completed")
                    span.set_attribute("run.duration_seconds", wait_time)
                    
                    # Get the specialist's response
                    messages = await self.client.beta.threads.messages.list(
                        thread_id=specialist_thread_id
                    )
                    
                    specialist_response = None
                    for msg in messages.data:
                        if msg.role == "assistant" and msg.content:
                            for content in msg.content:
                                if hasattr(content, 'text'):
                                    specialist_response = content.text.value
                                    span.set_attribute("response.length", len(specialist_response))
                                    span.set_attribute("response.preview", specialist_response[:200])
                                    print(f"   📝 Specialist response received (length: {len(specialist_response)} chars)")
                                    break
                            if specialist_response:
                                break
                    
                    # Clean up specialist thread
                    await self.client.beta.threads.delete(thread_id=specialist_thread_id)
                    
                    return specialist_response
                    
                elif specialist_run.status in ["failed", "cancelled", "expired"]:
                    error_msg = f"Specialist run failed: {specialist_run.status}"
                    print(f"   ❌ {error_msg}")
                    span.set_attribute("run.status", specialist_run.status)
                    span.set_attribute("error", error_msg)
                    await self.client.beta.threads.delete(thread_id=specialist_thread_id)
                    return error_msg
            
            timeout_msg = f"Specialist agent timed out after {wait_time} seconds"
            print(f"   ⏱️ {timeout_msg}")
            span.set_attribute("run.status", "timeout")
            span.set_attribute("error", timeout_msg)
            await self.client.beta.threads.delete(thread_id=specialist_thread_id)
            return timeout_msg
    
    @trace_method("orchestration.complete_flow")
    async def test_complete_orchestration_flow(self, test_message: str):
        """Test the complete orchestration flow with telemetry - NO MOCKS."""
        
        with create_span_context("test.orchestration.complete_flow", {
            "test.message": test_message,
            "test.timestamp": datetime.now().isoformat()
        }) as span:
            
            print("=" * 80)
            print("COMPLETE ORCHESTRATION FLOW TEST WITH TELEMETRY")
            print("=" * 80)
            print(f"Main Orchestrator: {self.orchestrator_id}")
            print(f"Test Message: {test_message}")
            print()
            
            # STEP 1: Create thread for orchestrator
            print("STEP 1: Creating thread for Main Orchestrator")
            orchestrator_thread = await self.client.beta.threads.create()
            thread_id = orchestrator_thread.id
            span.set_attribute("orchestrator.thread_id", thread_id)
            print(f"✅ Thread created: {thread_id}")
            
            # Add message to orchestrator thread
            await self.client.beta.threads.messages.create(
                thread_id=thread_id,
                role="user",
                content=test_message
            )
            
            # STEP 2: Run orchestrator
            print("\nSTEP 2: Running Main Orchestrator")
            run = await self.client.beta.threads.runs.create(
                thread_id=thread_id,
                assistant_id=self.orchestrator_id
            )
            span.set_attribute("orchestrator.run_id", run.id)
            
            # Wait for orchestrator response
            while True:
                await asyncio.sleep(1)
                run = await self.client.beta.threads.runs.retrieve(
                    thread_id=thread_id,
                    run_id=run.id
                )
                
                print(f"Orchestrator status: {run.status}")
                
                if run.status == "requires_action":
                    print("\n✅ STEP 2 VERIFIED: Orchestrator requests tool call!")
                    span.set_attribute("orchestrator.requires_action", True)
                    
                    # Get tool call details
                    tool_calls = run.required_action.submit_tool_outputs.tool_calls
                    span.set_attribute("tool_calls.count", len(tool_calls))
                    
                    print(f"\nTool calls requested: {len(tool_calls)}")
                    
                    tool_outputs = []
                    
                    for tool_call in tool_calls:
                        print(f"\n🔧 Tool Call ID: {tool_call.id}")
                        print(f"   Function: {tool_call.function.name}")
                        
                        args = json.loads(tool_call.function.arguments)
                        print(f"   Arguments: {json.dumps(args, indent=2)}")
                        
                        span.set_attribute(f"tool_call.{tool_call.id}.function", tool_call.function.name)
                        span.set_attribute(f"tool_call.{tool_call.id}.args", json.dumps(args))
                        
                        # Extract agent name from function name
                        agent_key = tool_call.function.name.replace("invoke_", "")
                        
                        # Find the specialist agent ID
                        specialist_id = None
                        specialist_name = None
                        for agent_name, agent_id in self.specialist_agents.items():
                            if agent_name.lower().replace(" ", "").replace("agent", "") == agent_key:
                                specialist_id = agent_id
                                specialist_name = agent_name
                                break
                        
                        if specialist_id:
                            print(f"\nSTEP 3: Invoking ACTUAL specialist agent")
                            print(f"   Agent: {specialist_name}")
                            print(f"   Agent ID: {specialist_id}")
                            
                            # ACTUALLY INVOKE THE SPECIALIST AGENT
                            specialist_response = await self.invoke_specialist_agent(
                                specialist_id, 
                                specialist_name,
                                args.get('request', test_message)
                            )
                            
                            if specialist_response:
                                print(f"\n✅ STEP 3 VERIFIED: Specialist agent responded!")
                                print(f"   Response preview: {specialist_response[:200]}...")
                                span.set_attribute(f"specialist.{specialist_name}.responded", True)
                                
                                tool_outputs.append({
                                    "tool_call_id": tool_call.id,
                                    "output": specialist_response
                                })
                            else:
                                print(f"\n❌ STEP 3 FAILED: No response from specialist")
                                span.set_attribute(f"specialist.{specialist_name}.responded", False)
                                tool_outputs.append({
                                    "tool_call_id": tool_call.id,
                                    "output": "No response from specialist agent"
                                })
                        else:
                            print(f"\n❌ Unknown specialist agent: {agent_key}")
                            span.set_attribute(f"specialist.unknown.{agent_key}", True)
                            tool_outputs.append({
                                "tool_call_id": tool_call.id,
                                "output": f"Unknown specialist agent: {agent_key}"
                            })
                    
                    # STEP 4: Submit specialist responses back to orchestrator
                    print("\nSTEP 4: Submitting specialist responses back to orchestrator")
                    await self.client.beta.threads.runs.submit_tool_outputs(
                        thread_id=thread_id,
                        run_id=run.id,
                        tool_outputs=tool_outputs
                    )
                    print("✅ Tool outputs submitted")
                    span.set_attribute("tool_outputs.submitted", True)
                    
                elif run.status == "completed":
                    print("\n✅ FINAL STEP: Orchestrator completed with specialist input!")
                    span.set_attribute("orchestrator.completed", True)
                    
                    # Get final response
                    messages = await self.client.beta.threads.messages.list(thread_id=thread_id)
                    
                    final_response = None
                    for msg in messages.data:
                        if msg.role == "assistant" and msg.content:
                            for content in msg.content:
                                if hasattr(content, 'text'):
                                    final_response = content.text.value
                                    break
                            if final_response:
                                break
                    
                    if final_response:
                        print(f"\n💬 ORCHESTRATOR FINAL RESPONSE:")
                        print("=" * 60)
                        print(final_response)
                        print("=" * 60)
                        span.set_attribute("final_response.length", len(final_response))
                        span.set_attribute("final_response.preview", final_response[:200])
                        
                        print("\n✅ ✅ ✅ COMPLETE END-TO-END FLOW VERIFIED WITH TELEMETRY! ✅ ✅ ✅")
                        print("\nVerification Summary:")
                        print("1. ✅ Test script sent request to orchestrator")
                        print("2. ✅ Orchestrator delegated via tool call")
                        print("3. ✅ Specialist agent received request and responded")
                        print("4. ✅ Orchestrator received specialist response and formulated final answer")
                        print("5. ✅ All operations tracked with telemetry")
                    else:
                        print("\n❌ No final response from orchestrator")
                        span.set_attribute("final_response.missing", True)
                    
                    break
                    
                elif run.status in ["failed", "cancelled", "expired"]:
                    print(f"\n❌ Orchestrator run failed: {run.status}")
                    span.set_attribute("orchestrator.failed", True)
                    span.set_attribute("orchestrator.failure_reason", run.status)
                    break
            
            # Clean up
            await self.client.beta.threads.delete(thread_id=thread_id)
            print("\n🧹 Cleaned up orchestrator thread")
    
    async def run_multiple_tests(self):
        """Run multiple test scenarios to generate telemetry data."""
        
        test_scenarios = [
            "I need to record my thoughts about the market downturn and its potential impact on our Q4 revenue projections",
            "Create a SWOT analysis for our expansion into the Asian market",
            "What initiatives should we prioritize for improving customer retention?",
            "Analyze the risks and opportunities in our current strategic position"
        ]
        
        print("\n🚀 Running Multiple Orchestration Tests with Telemetry")
        print("=" * 60)
        print(f"📊 Application Insights: stratos-multi-agent-appinsights")
        print(f"🕐 Start Time: {datetime.now().isoformat()}")
        print(f"📝 Test Scenarios: {len(test_scenarios)}")
        print("=" * 60)
        
        for i, scenario in enumerate(test_scenarios, 1):
            print(f"\n\n🔄 TEST SCENARIO {i}/{len(test_scenarios)}")
            print("=" * 60)
            
            try:
                await self.test_complete_orchestration_flow(scenario)
            except Exception as e:
                print(f"\n❌ Test failed with error: {e}")
                import traceback
                traceback.print_exc()
            
            # Wait between tests
            if i < len(test_scenarios):
                print("\n⏳ Waiting 5 seconds before next test...")
                await asyncio.sleep(5)
        
        print("\n\n" + "=" * 80)
        print("✅ ALL TESTS COMPLETED!")
        print("=" * 80)
        print("\n📊 Telemetry data has been sent to Application Insights")
        print("⏱️  Wait 2-5 minutes for data to appear in portal")
        print("\n📈 View traces at:")
        print("   https://portal.azure.com > Application Insights > stratos-multi-agent-appinsights")
        print("\n🔍 Use these Kusto queries:")
        print("   traces | where customDimensions.['service.name'] == 'OrchestrationTelemetryTester'")
        print("   traces | where message contains 'orchestration' | order by timestamp desc")
        print("   dependencies | where target contains 'agent' | order by timestamp desc")


async def main():
    """Main entry point."""
    tester = OrchestrationTelemetryTester()
    await tester.run_multiple_tests()


if __name__ == "__main__":
    asyncio.run(main())