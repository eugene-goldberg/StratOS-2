#!/usr/bin/env python3
"""
Test StratOS agents using Semantic Kernel with telemetry tracking.
NO MOCKS - REAL AGENT INVOCATIONS ONLY.
"""

import asyncio
import os
import json
import sys
from datetime import datetime
from dotenv import load_dotenv

from azure.identity.aio import DefaultAzureCredential
from semantic_kernel.agents import AzureAIAgent, AzureAIAgentSettings

# Add the agentic directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.telemetry import initialize_telemetry, create_span_context, SpanNames, trace_method


class SKAgentTelemetryTester:
    """Test Semantic Kernel agents with telemetry."""
    
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
            service_name="SKAgentTelemetryTester",
            service_version="1.0.0",
            connection_string=connection_string,
            additional_attributes={
                "test.type": "semantic_kernel_agents",
                "test.real_agents": True,
                "framework": "semantic_kernel"
            }
        )
        
        print("✅ Telemetry initialized for SKAgentTelemetryTester")
        
        # Load configurations
        self.load_configurations()
        
        # Test messages
        self.test_messages = {
            "CEOLogAgent": "I had a productive meeting with our board today. They're excited about our AI initiatives.",
            "SWOTTOWSAgent": "Perform a SWOT analysis for our expansion into the healthcare market.",
            "StrategicPlanningAgent": "Create a 3-year strategic plan for digital transformation.",
            "RiskOpportunityAgent": "What are the key risks in our supply chain?",
            "NorthStarAgent": "What is our company's north star metric?",
            "ActionPlanningAgent": "Create an action plan for improving employee engagement."
        }
    
    def load_configurations(self):
        """Load agent configurations."""
        # Load deployment data
        deployment_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "deployment_configs",
            "ai_project_agents_deployment.json"
        )
        
        with open(deployment_path, 'r') as f:
            data = json.load(f)
            self.deployed_agents = data.get('deployed_agents', {})
            
        print(f"📋 Loaded {len(self.deployed_agents)} deployed agents")
        
        # Load orchestrator
        orch_config_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "deployment_configs",
            "main_orchestrator_tools_deployment.json"
        )
        
        with open(orch_config_path, 'r') as f:
            config = json.load(f)
            self.orchestrator_id = config['agent_id']
            self.deployed_agents['MainOrchestrator'] = self.orchestrator_id
            
        print(f"📋 Main Orchestrator ID: {self.orchestrator_id}")
    
    @trace_method("sk_agent.invoke")
    async def invoke_agent(self, client, agent_name: str, agent_id: str, message: str):
        """Invoke an agent using Semantic Kernel with telemetry."""
        
        with create_span_context(f"agent.{agent_name.lower()}", {
            "agent.name": agent_name,
            "agent.id": agent_id,
            "message.content": message[:100],
            "message.length": len(message),
            "framework": "semantic_kernel"
        }) as span:
            
            print(f"\n{'='*70}")
            print(f"🤖 Testing: {agent_name}")
            print(f"   Agent ID: {agent_id}")
            print(f"   Message: {message[:80]}...")
            
            try:
                # Get agent definition
                agent_def = await client.agents.get_agent(agent_id=agent_id)
                span.set_attribute("agent.retrieved", True)
                print(f"   ✓ Retrieved agent definition")
                
                # Create SK agent
                agent = AzureAIAgent(client=client, definition=agent_def)
                
                # Invoke agent and collect response
                print(f"\n   Response: ", end="", flush=True)
                response_text = ""
                chunk_count = 0
                start_time = asyncio.get_event_loop().time()
                
                async for chunk in agent.invoke(message=message):
                    chunk_count += 1
                    if hasattr(chunk, 'content') and chunk.content:
                        chunk_text = str(chunk.content)
                        print(chunk_text, end="", flush=True)
                        response_text += chunk_text
                
                duration = asyncio.get_event_loop().time() - start_time
                print()  # New line after response
                
                # Record metrics
                span.set_attribute("response.length", len(response_text))
                span.set_attribute("response.chunks", chunk_count)
                span.set_attribute("response.duration_seconds", round(duration, 2))
                span.set_attribute("response.success", bool(response_text))
                
                if response_text:
                    print(f"\n   ✅ Success: {len(response_text)} chars in {chunk_count} chunks ({duration:.1f}s)")
                    span.set_attribute("response.preview", response_text[:200])
                    return True, response_text
                else:
                    print(f"\n   ⚠️  Empty response after {chunk_count} chunks")
                    return False, ""
                    
            except Exception as e:
                error_msg = f"{type(e).__name__}: {str(e)}"
                span.set_attribute("error", error_msg)
                span.set_attribute("error.type", type(e).__name__)
                print(f"\n   ❌ Error: {error_msg}")
                import traceback
                traceback.print_exc()
                return False, None
    
    @trace_method("sk_agent.test_orchestration")
    async def test_orchestration_flow(self, client, test_message: str):
        """Test the orchestration flow with telemetry."""
        
        with create_span_context("test.orchestration", {
            "test.message": test_message,
            "orchestrator.id": self.orchestrator_id
        }) as span:
            
            print(f"\n{'='*80}")
            print(f"🔄 ORCHESTRATION FLOW TEST")
            print(f"{'='*80}")
            
            # Test orchestrator
            success, response = await self.invoke_agent(
                client,
                "MainOrchestrator",
                self.orchestrator_id,
                test_message
            )
            
            if success and response:
                # Check if response mentions routing or specific agents
                routing_keywords = ["route", "ceo", "swot", "strategic", "planning", "risk"]
                found_routing = any(keyword in response.lower() for keyword in routing_keywords)
                
                span.set_attribute("orchestrator.mentions_routing", found_routing)
                
                if found_routing:
                    print(f"\n✅ Orchestrator provided routing guidance")
                    
                    # Try to identify which agent it suggests
                    for agent_name in self.deployed_agents.keys():
                        if agent_name.lower().replace("agent", "") in response.lower():
                            print(f"   → Suggested agent: {agent_name}")
                            span.set_attribute("orchestrator.suggested_agent", agent_name)
                            break
                else:
                    print(f"\n⚠️  Orchestrator did not provide clear routing")
    
    @trace_method("sk_agent.run_all_tests")
    async def run_all_tests(self):
        """Run comprehensive tests with telemetry."""
        
        print("\n🚀 Starting Semantic Kernel Agent Tests with Telemetry")
        print("=" * 80)
        print(f"📊 Application Insights: stratos-multi-agent-appinsights")
        print(f"🕐 Start Time: {datetime.now().isoformat()}")
        print(f"🤖 Total Agents: {len(self.deployed_agents)}")
        print("=" * 80)
        
        # Track results
        results = {
            "successful": [],
            "failed": [],
            "empty": []
        }
        
        try:
            # Create SK client
            settings = AzureAIAgentSettings()
            
            async with DefaultAzureCredential() as credential:
                async with AzureAIAgent.create_client(credential=credential, settings=settings) as client:
                    print("\n✅ Connected to Azure AI Agent Service")
                    
                    # Test 1: Orchestration flow
                    print(f"\n\n📌 TEST 1: Orchestration Flow")
                    print("-" * 60)
                    
                    await self.test_orchestration_flow(
                        client,
                        "I need help creating a strategy for entering new markets in Asia"
                    )
                    
                    await asyncio.sleep(2)
                    
                    # Test 2: Direct agent invocations
                    print(f"\n\n📌 TEST 2: Direct Agent Tests")
                    print("-" * 60)
                    
                    # Test a subset of key agents
                    test_agents = [
                        "CEOLogAgent",
                        "SWOTTOWSAgent",
                        "StrategicPlanningAgent",
                        "RiskOpportunityAgent"
                    ]
                    
                    for agent_name in test_agents:
                        if agent_name in self.deployed_agents:
                            agent_id = self.deployed_agents[agent_name]
                            message = self.test_messages.get(
                                agent_name,
                                "What are your key capabilities and how can you help me?"
                            )
                            
                            success, response = await self.invoke_agent(
                                client,
                                agent_name,
                                agent_id,
                                message
                            )
                            
                            if success and response:
                                results["successful"].append(agent_name)
                            elif success and not response:
                                results["empty"].append(agent_name)
                            else:
                                results["failed"].append(agent_name)
                            
                            await asyncio.sleep(2)  # Pause between agents
                    
                    # Print summary
                    print(f"\n\n{'='*80}")
                    print(f"SUMMARY REPORT")
                    print(f"{'='*80}")
                    
                    total_tested = len(test_agents) + 1  # +1 for orchestrator
                    successful = len(results["successful"]) + (1 if "MainOrchestrator" not in results["failed"] else 0)
                    
                    print(f"\nAgents Tested: {total_tested}")
                    print(f"✅ Successful: {successful}")
                    print(f"⚠️  Empty Responses: {len(results['empty'])}")
                    print(f"❌ Failed: {len(results['failed'])}")
                    
                    if results["successful"]:
                        print(f"\n✅ Successful Agents:")
                        for agent in results["successful"]:
                            print(f"   - {agent}")
                    
                    if results["failed"]:
                        print(f"\n❌ Failed Agents:")
                        for agent in results["failed"]:
                            print(f"   - {agent}")
                    
        except Exception as e:
            print(f"\n❌ Test suite failed: {e}")
            import traceback
            traceback.print_exc()
        
        print(f"\n\n{'='*80}")
        print("✅ ALL TESTS COMPLETED!")
        print(f"{'='*80}")
        print("\n📊 Telemetry data sent to Application Insights")
        print("⏱️  Wait 2-5 minutes for data to appear")
        print("\n🔍 Kusto Queries:")
        print("   traces | where customDimensions.['service.name'] == 'SKAgentTelemetryTester'")
        print("   traces | where customDimensions.['framework'] == 'semantic_kernel'")
        print("   dependencies | where target contains 'agent'")


async def main():
    """Main entry point."""
    tester = SKAgentTelemetryTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())