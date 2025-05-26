#!/usr/bin/env python3
"""
Test orchestration flow with Azure AI Agent Service agents and telemetry.
Uses the proper Azure AI Agent Service API, not OpenAI Assistants.
NO MOCKS - REAL AGENT INVOCATIONS ONLY.
"""

import asyncio
import os
import json
import sys
from datetime import datetime
from dotenv import load_dotenv
from typing import Dict, Optional

from azure.identity.aio import DefaultAzureCredential
from azure.ai.projects.aio import AIProjectClient

# Add the agentic directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.telemetry import initialize_telemetry, create_span_context, SpanNames, trace_method


class AzureAgentTelemetryTester:
    """Test Azure AI Agent Service agents with telemetry."""
    
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
            service_name="AzureAgentTelemetryTester",
            service_version="1.0.0",
            connection_string=connection_string,
            additional_attributes={
                "test.type": "azure_ai_agent_service",
                "test.real_agents": True,
                "deployment.type": "azure_ai_project"
            }
        )
        
        print("✅ Telemetry initialized for AzureAgentTelemetryTester")
        
        # Set up credentials
        os.environ["AZURE_CLIENT_ID"] = os.getenv("AZURE_CLIENT_ID")
        os.environ["AZURE_CLIENT_SECRET"] = os.getenv("AZURE_CLIENT_SECRET")
        os.environ["AZURE_TENANT_ID"] = os.getenv("AZURE_TENANT_ID")
        
        # Load configurations
        self.load_configurations()
        
        # Initialize AI Project Client
        self.initialize_client()
    
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
            print(f"📋 Main Orchestrator ID: {self.orchestrator_id}")
        
        # Load actual deployment data to get real agent names
        deployment_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "deployment_configs",
            "ai_project_agents_deployment.json"
        )
        with open(deployment_path, 'r') as f:
            deployment_data = json.load(f)
            self.specialist_agents = deployment_data['deployed_agents']
            project_context = deployment_data['project_context_config_from_env']
            self.project_name = project_context['name']
            self.resource_group = project_context['resource_group']
            self.subscription_id = project_context['subscription_id']
            print(f"📋 Loaded {len(self.specialist_agents)} specialist agents")
            print(f"📋 Project: {self.project_name}")
    
    async def initialize_client(self):
        """Initialize the AI Project Client."""
        self.credential = DefaultAzureCredential()
        
        # Construct the project connection string
        self.connection_string = (
            f"eastus.api.azureml.ms;"
            f"{self.subscription_id};"
            f"{self.resource_group};"
            f"{self.project_name}"
        )
        
        print(f"🔧 Initializing AI Project Client...")
        self.client = AIProjectClient.from_connection_string(
            credential=self.credential,
            conn_str=self.connection_string
        )
        print(f"✅ AI Project Client initialized")
    
    @trace_method("azure_agent.invoke_specialist")
    async def invoke_specialist_agent(self, agent_name: str, agent_id: str, request: str) -> Optional[str]:
        """Invoke a specialist agent through Azure AI Agent Service."""
        
        with create_span_context(f"specialist.{agent_name.lower()}", {
            "agent.name": agent_name,
            "agent.id": agent_id,
            "request.content": request[:100],
            "request.length": len(request),
            "service.type": "azure_ai_agent"
        }) as span:
            
            print(f"\n🤖 Invoking Azure AI Agent: {agent_name}")
            print(f"   Agent ID: {agent_id}")
            
            try:
                # Create thread
                thread = await self.client.agents.create_thread()
                thread_id = thread.id
                span.set_attribute("thread.id", thread_id)
                print(f"   Thread created: {thread_id}")
                
                # Add message
                await self.client.agents.create_message(
                    thread_id=thread_id,
                    role="user",
                    content=request
                )
                print(f"   Message sent: {request[:80]}...")
                
                # Run agent
                run = await self.client.agents.create_run(
                    thread_id=thread_id,
                    assistant_id=agent_id
                )
                span.set_attribute("run.id", run.id)
                print(f"   Run started: {run.id}")
                
                # Wait for completion
                max_wait = 60
                wait_time = 0
                
                while wait_time < max_wait:
                    await asyncio.sleep(2)
                    wait_time += 2
                    
                    run_status = await self.client.agents.get_run(
                        thread_id=thread_id,
                        run_id=run.id
                    )
                    
                    print(f"   Status: {run_status.status} ({wait_time}s)")
                    
                    if run_status.status == "completed":
                        span.set_attribute("run.status", "completed")
                        span.set_attribute("run.duration_seconds", wait_time)
                        
                        # Get messages
                        messages = await self.client.agents.list_messages(thread_id=thread_id)
                        
                        # Find assistant response
                        async for message in messages:
                            if message.role == "assistant":
                                content = message.content[0].text.value if message.content else ""
                                span.set_attribute("response.length", len(content))
                                span.set_attribute("response.preview", content[:200])
                                print(f"   ✅ Response received ({len(content)} chars)")
                                return content
                        
                        print(f"   ⚠️  No assistant response found")
                        return None
                        
                    elif run_status.status in ["failed", "cancelled", "expired"]:
                        error_msg = f"Run failed with status: {run_status.status}"
                        span.set_attribute("run.status", run_status.status)
                        span.set_attribute("error", error_msg)
                        print(f"   ❌ {error_msg}")
                        return None
                
                timeout_msg = f"Agent timed out after {wait_time} seconds"
                span.set_attribute("run.status", "timeout")
                span.set_attribute("error", timeout_msg)
                print(f"   ⏱️ {timeout_msg}")
                return None
                
            except Exception as e:
                error_msg = f"Error invoking agent: {str(e)}"
                span.set_attribute("error", error_msg)
                span.set_attribute("error.type", type(e).__name__)
                print(f"   ❌ {error_msg}")
                import traceback
                traceback.print_exc()
                return None
    
    @trace_method("azure_agent.test_orchestration")
    async def test_orchestration_flow(self, test_message: str):
        """Test the Main Orchestrator routing with Azure AI Agent Service."""
        
        with create_span_context("test.azure_orchestration", {
            "test.message": test_message,
            "orchestrator.id": self.orchestrator_id,
            "test.timestamp": datetime.now().isoformat()
        }) as span:
            
            print("\n" + "=" * 80)
            print("AZURE AI AGENT SERVICE ORCHESTRATION TEST")
            print("=" * 80)
            print(f"Orchestrator: Main Orchestrator")
            print(f"Message: {test_message}")
            
            # First, invoke the Main Orchestrator
            print(f"\n📍 STEP 1: Invoking Main Orchestrator")
            
            try:
                # Create thread for orchestrator
                thread = await self.client.agents.create_thread()
                thread_id = thread.id
                span.set_attribute("orchestrator.thread_id", thread_id)
                print(f"   Thread created: {thread_id}")
                
                # Add message
                await self.client.agents.create_message(
                    thread_id=thread_id,
                    role="user",
                    content=test_message
                )
                
                # Run orchestrator
                run = await self.client.agents.create_run(
                    thread_id=thread_id,
                    assistant_id=self.orchestrator_id
                )
                span.set_attribute("orchestrator.run_id", run.id)
                print(f"   Run started: {run.id}")
                
                # Wait for orchestrator
                max_wait = 60
                wait_time = 0
                
                while wait_time < max_wait:
                    await asyncio.sleep(2)
                    wait_time += 2
                    
                    run_status = await self.client.agents.get_run(
                        thread_id=thread_id,
                        run_id=run.id
                    )
                    
                    print(f"   Orchestrator status: {run_status.status} ({wait_time}s)")
                    
                    if run_status.status == "requires_action":
                        print(f"\n✅ STEP 1 VERIFIED: Orchestrator requires action (tool calls)")
                        span.set_attribute("orchestrator.requires_action", True)
                        
                        # Get required actions
                        if hasattr(run_status, 'required_action') and run_status.required_action:
                            tool_calls = run_status.required_action.submit_tool_outputs.tool_calls
                            span.set_attribute("tool_calls.count", len(tool_calls))
                            
                            print(f"   Tool calls requested: {len(tool_calls)}")
                            
                            # For now, just log the tool calls
                            for tc in tool_calls:
                                print(f"   🔧 Tool: {tc.function.name}")
                                print(f"      Args: {tc.function.arguments}")
                        
                        # Submit empty tool outputs to continue
                        await self.client.agents.submit_tool_outputs_to_run(
                            thread_id=thread_id,
                            run_id=run.id,
                            tool_outputs=[]
                        )
                        
                    elif run_status.status == "completed":
                        span.set_attribute("orchestrator.completed", True)
                        
                        # Get orchestrator response
                        messages = await self.client.agents.list_messages(thread_id=thread_id)
                        
                        async for message in messages:
                            if message.role == "assistant":
                                content = message.content[0].text.value if message.content else ""
                                print(f"\n📝 Orchestrator Response:")
                                print(f"{content[:500]}...")
                                span.set_attribute("orchestrator.response_length", len(content))
                                
                                # Check if it mentions routing
                                if any(keyword in content.lower() for keyword in ["route", "ceo", "swot", "strategic"]):
                                    print(f"\n✅ Orchestrator provided routing guidance")
                                    span.set_attribute("orchestrator.routed", True)
                                break
                        
                        break
                        
                    elif run_status.status in ["failed", "cancelled", "expired"]:
                        print(f"   ❌ Orchestrator failed: {run_status.status}")
                        span.set_attribute("orchestrator.failed", True)
                        break
                
            except Exception as e:
                print(f"\n❌ Orchestration test failed: {e}")
                span.set_attribute("error", str(e))
                import traceback
                traceback.print_exc()
    
    @trace_method("azure_agent.test_all")
    async def run_all_tests(self):
        """Run comprehensive tests with Azure AI Agent Service."""
        
        print("\n🚀 Starting Azure AI Agent Service Tests with Telemetry")
        print("=" * 80)
        print(f"📊 Application Insights: stratos-multi-agent-appinsights")
        print(f"🕐 Start Time: {datetime.now().isoformat()}")
        print(f"📍 Project: {self.project_name}")
        print(f"🔧 Using Azure AI Agent Service (NOT OpenAI Assistants)")
        print("=" * 80)
        
        # Test scenarios
        test_scenarios = [
            {
                "message": "I need to record my concerns about supply chain disruptions",
                "expected_agent": "CEOLogAgent",
                "agent_type": "strategic"
            },
            {
                "message": "Perform a SWOT analysis for our cloud migration strategy",
                "expected_agent": "SWOTTOWSAgent", 
                "agent_type": "analysis"
            },
            {
                "message": "Create an action plan for improving customer satisfaction",
                "expected_agent": "ActionPlanningAgent",
                "agent_type": "planning"
            }
        ]
        
        # Test 1: Direct agent invocations
        print("\n📌 TEST 1: Direct Agent Invocations")
        print("-" * 60)
        
        for scenario in test_scenarios:
            agent_name = scenario["expected_agent"]
            if agent_name in self.specialist_agents:
                agent_id = self.specialist_agents[agent_name]
                response = await self.invoke_specialist_agent(
                    agent_name,
                    agent_id,
                    scenario["message"]
                )
                
                if response:
                    print(f"✅ {agent_name} responded successfully")
                else:
                    print(f"❌ {agent_name} failed to respond")
                
                await asyncio.sleep(3)  # Space out requests
        
        # Test 2: Orchestration flow
        print("\n📌 TEST 2: Orchestration Flow")
        print("-" * 60)
        
        await self.test_orchestration_flow(
            "I need strategic guidance on entering new markets in Asia"
        )
        
        print("\n" + "=" * 80)
        print("✅ ALL AZURE AI AGENT TESTS COMPLETED!")
        print("=" * 80)
        print("\n📊 Telemetry data sent to Application Insights")
        print("⏱️  Wait 2-5 minutes for data to appear")
        print("\n🔍 Kusto Queries for Azure AI Agent traces:")
        print("   traces | where customDimensions.['service.name'] == 'AzureAgentTelemetryTester'")
        print("   traces | where customDimensions.['service.type'] == 'azure_ai_agent'")
        print("   dependencies | project timestamp, name, target, duration, success")
    
    async def cleanup(self):
        """Clean up resources."""
        if hasattr(self, 'credential'):
            await self.credential.close()


async def main():
    """Main entry point."""
    tester = AzureAgentTelemetryTester()
    try:
        await tester.run_all_tests()
    finally:
        await tester.cleanup()


if __name__ == "__main__":
    asyncio.run(main())