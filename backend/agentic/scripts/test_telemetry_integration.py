#!/usr/bin/env python3
"""
Test telemetry integration by running sample requests through agents.
This will generate traces that can be viewed in Application Insights.
"""

import os
import sys
import json
import asyncio
from datetime import datetime
from dotenv import load_dotenv
from openai import AsyncAzureOpenAI

# Add the agentic directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.telemetry import initialize_telemetry, create_span_context, SpanNames, trace_method


class TelemetryTester:
    """Tests telemetry integration with deployed agents."""
    
    def __init__(self):
        load_dotenv()
        
        # Initialize telemetry for the test client
        self.tracer = initialize_telemetry(
            service_name="TelemetryTester",
            service_version="1.0.0",
            additional_attributes={
                "test.type": "integration",
                "test.suite": "telemetry"
            }
        )
        
        self.client = AsyncAzureOpenAI(
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version="2024-02-15-preview"
        )
        
        # Load agent configurations
        self.agents = self._load_agents()
        self.orchestrator_id = self._load_orchestrator_id()
    
    def _load_agents(self) -> Dict[str, str]:
        """Load agent configurations."""
        deployment_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "deployment_configs",
            "ai_project_agents_deployment.json"
        )
        
        with open(deployment_path, 'r') as f:
            data = json.load(f)
            return data['deployed_agents']
    
    def _load_orchestrator_id(self) -> str:
        """Load orchestrator configuration."""
        orch_config_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "deployment_configs",
            "main_orchestrator_tools_deployment.json"
        )
        
        with open(orch_config_path, 'r') as f:
            data = json.load(f)
            return data['agent_id']
    
    @trace_method("test.orchestrator_flow")
    async def test_orchestrator_flow(self):
        """Test the complete orchestrator flow with telemetry."""
        print("\n🔍 Testing Orchestrator Flow with Telemetry")
        print("=" * 60)
        
        with create_span_context("test.orchestrator_request", {
            "test.name": "orchestrator_flow",
            "request.type": "ceo_log"
        }) as span:
            
            # Create thread
            thread = await self.client.beta.threads.create()
            thread_id = thread.id
            span.set_attribute("thread.id", thread_id)
            
            # Test message
            test_message = "I need to log my concerns about supply chain disruptions affecting our manufacturing timeline"
            print(f"📤 Sending: {test_message}")
            
            # Add message
            await self.client.beta.threads.messages.create(
                thread_id=thread_id,
                role="user",
                content=test_message
            )
            
            # Run orchestrator
            run = await self.client.beta.threads.runs.create(
                thread_id=thread_id,
                assistant_id=self.orchestrator_id
            )
            
            # Wait for completion
            start_time = asyncio.get_event_loop().time()
            while True:
                await asyncio.sleep(1)
                run = await self.client.beta.threads.runs.retrieve(
                    thread_id=thread_id,
                    run_id=run.id
                )
                
                if run.status == "requires_action":
                    # Handle tool calls
                    tool_call = run.required_action.submit_tool_outputs.tool_calls[0]
                    span.set_attribute("tool.function", tool_call.function.name)
                    
                    print(f"🔧 Tool call: {tool_call.function.name}")
                    
                    # Submit mock response
                    await self.client.beta.threads.runs.submit_tool_outputs(
                        thread_id=thread_id,
                        run_id=run.id,
                        tool_outputs=[{
                            "tool_call_id": tool_call.id,
                            "output": "Entry logged successfully with telemetry tracking"
                        }]
                    )
                
                elif run.status == "completed":
                    elapsed = asyncio.get_event_loop().time() - start_time
                    span.set_attribute("duration.seconds", elapsed)
                    print(f"✅ Completed in {elapsed:.2f} seconds")
                    break
                
                elif run.status in ["failed", "cancelled", "expired"]:
                    span.set_attribute("error", run.status)
                    print(f"❌ Run failed: {run.status}")
                    break
            
            # Clean up
            await self.client.beta.threads.delete(thread_id=thread_id)
    
    @trace_method("test.direct_agent_call")
    async def test_direct_agent_call(self, agent_name: str, agent_id: str):
        """Test direct agent call with telemetry."""
        print(f"\n🔍 Testing {agent_name} with Telemetry")
        
        with create_span_context(f"test.{agent_name.lower()}", {
            "agent.name": agent_name,
            "agent.id": agent_id
        }) as span:
            
            # Create thread
            thread = await self.client.beta.threads.create()
            thread_id = thread.id
            
            # Test message based on agent type
            test_messages = {
                "CEOLogAgent": "Market volatility is concerning but I see opportunities in emerging markets",
                "StrategicPlanningAgent": "We need to develop a 5-year growth strategy",
                "SWOTAnalysisAgent": "Analyze our position in the cloud services market",
                "NorthStarAgent": "Our north star metric should focus on customer retention",
                "MemoryContextAgent": "Recall our discussions about market expansion"
            }
            
            test_message = test_messages.get(
                agent_name, 
                f"Test message for {agent_name}"
            )
            
            print(f"📤 Sending: {test_message}")
            
            # Add message
            await self.client.beta.threads.messages.create(
                thread_id=thread_id,
                role="user",
                content=test_message
            )
            
            # Run agent
            run = await self.client.beta.threads.runs.create(
                thread_id=thread_id,
                assistant_id=agent_id
            )
            
            # Wait for completion
            max_wait = 30
            for i in range(max_wait):
                await asyncio.sleep(1)
                run = await self.client.beta.threads.runs.retrieve(
                    thread_id=thread_id,
                    run_id=run.id
                )
                
                if run.status == "completed":
                    # Get response
                    messages = await self.client.beta.threads.messages.list(
                        thread_id=thread_id
                    )
                    
                    for msg in messages.data:
                        if msg.role == "assistant":
                            response = msg.content[0].text.value
                            span.set_attribute("response.length", len(response))
                            print(f"✅ Response received ({len(response)} chars)")
                            print(f"📝 Preview: {response[:100]}...")
                            break
                    break
                
                elif run.status in ["failed", "cancelled", "expired"]:
                    span.set_attribute("error", run.status)
                    print(f"❌ Run failed: {run.status}")
                    break
            
            # Clean up
            await self.client.beta.threads.delete(thread_id=thread_id)
    
    @trace_method("test.run_all_tests")
    async def run_all_tests(self):
        """Run all telemetry tests."""
        print("\n🚀 Starting Telemetry Integration Tests")
        print("=" * 60)
        print(f"📊 Application Insights: stratos-multi-agent-appinsights")
        print(f"🕐 Test Time: {datetime.now().isoformat()}")
        print("=" * 60)
        
        # Test orchestrator
        await self.test_orchestrator_flow()
        
        # Test a few key agents directly
        key_agents = [
            ("CEOLogAgent", self.agents.get("CEOLogAgent")),
            ("StrategicPlanningAgent", self.agents.get("StrategicPlanningAgent")),
            ("SWOTAnalysisAgent", self.agents.get("SWOTAnalysisAgent"))
        ]
        
        for agent_name, agent_id in key_agents:
            if agent_id:
                await self.test_direct_agent_call(agent_name, agent_id)
                await asyncio.sleep(2)  # Space out requests
        
        print("\n" + "=" * 60)
        print("✅ Telemetry tests completed!")
        print("\n📈 View traces in Azure Portal:")
        print("1. Go to Azure Portal > Application Insights")
        print("2. Select 'stratos-multi-agent-appinsights'")
        print("3. Check Transaction search, Application map, and Performance")
        print("4. Look for service names: TelemetryTester, MainOrchestrator, CEOLogAgent, etc.")


async def main():
    """Main entry point."""
    tester = TelemetryTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())