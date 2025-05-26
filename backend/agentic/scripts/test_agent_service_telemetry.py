#!/usr/bin/env python3
"""
Test telemetry integration with Azure AI Agent Service.
This generates traces that can be viewed in Application Insights.
"""

import os
import sys
import json
import asyncio
from datetime import datetime
from dotenv import load_dotenv

# Add the agentic directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.telemetry import initialize_telemetry, create_span_context, SpanNames, trace_method
from azure.ai.projects.aio import AIProjectClient
from azure.identity.aio import DefaultAzureCredential


class AgentServiceTelemetryTester:
    """Tests telemetry integration with Azure AI Agent Service."""
    
    def __init__(self):
        # Load environment variables
        # First load backend .env for Azure credentials
        backend_env = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
        if os.path.exists(backend_env):
            load_dotenv(backend_env)
        
        # Then load root .env which has the Application Insights connection string
        root_env = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')
        if os.path.exists(root_env):
            load_dotenv(root_env, override=True)
        
        # Debug: Print connection string status
        conn_str = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
        if conn_str:
            print(f"✅ Application Insights connection string loaded (length: {len(conn_str)})")
            # Show first few chars to verify it's the right one
            print(f"   Starts with: {conn_str[:50]}...")
        else:
            print("❌ No Application Insights connection string found")
            # Debug: show all env vars starting with APP or AZURE
            print("Available env vars:")
            for key in sorted(os.environ.keys()):
                if key.startswith(('APP', 'AZURE')):
                    print(f"   {key}: {os.environ[key][:50] if len(os.environ[key]) > 50 else os.environ[key]}...")
        
        # Initialize telemetry with explicit connection string
        connection_string = "InstrumentationKey=189923ab-6ad8-408f-b3f6-7ae4817a3988;IngestionEndpoint=https://eastus-8.in.applicationinsights.azure.com/;LiveEndpoint=https://eastus.livediagnostics.monitor.azure.com/;ApplicationId=dfba6d9b-7df1-4bf5-af6a-2fb21f1881b2"
        
        self.tracer = initialize_telemetry(
            service_name="AgentServiceTelemetryTester",
            service_version="1.0.0",
            connection_string=connection_string,
            additional_attributes={
                "test.type": "integration",
                "test.suite": "agent_service_telemetry",
                "deployment.type": "azure_ai_agent_service"
            }
        )
        
        # Set up Azure credentials
        os.environ["AZURE_CLIENT_ID"] = os.getenv("AZURE_CLIENT_ID")
        os.environ["AZURE_CLIENT_SECRET"] = os.getenv("AZURE_CLIENT_SECRET")
        os.environ["AZURE_TENANT_ID"] = os.getenv("AZURE_TENANT_ID")
        
        # Initialize AI Project Client
        self.project_name = os.getenv("AZURE_AI_AGENT_PROJECT_NAME")
        self.resource_group = os.getenv("AZURE_AI_AGENT_PROJECT_RESOURCE_GROUP")
        self.subscription_id = os.getenv("AZURE_AI_AGENT_PROJECT_SUBSCRIPTION_ID")
        
        # Load agent configurations
        self.agents = self._load_agents()
        self.orchestrator_id = self._load_orchestrator_id()
    
    def _load_agents(self) -> dict:
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
    
    @trace_method("test.simulate_agent_call")
    async def simulate_agent_call(self, agent_name: str, message: str):
        """Simulate an agent call with telemetry."""
        
        with create_span_context(f"test.agent.{agent_name.lower()}", {
            "agent.name": agent_name,
            "agent.type": "azure_ai_service",
            "message.content": message[:100],  # First 100 chars
            "message.length": len(message),
            "test.scenario": "telemetry_validation"
        }) as span:
            
            print(f"\n📊 Simulating {agent_name} call with telemetry")
            print(f"   Message: {message}")
            
            # Simulate processing delay
            await asyncio.sleep(1)
            
            # Simulate different outcomes
            import random
            success = random.random() > 0.1  # 90% success rate
            
            if success:
                response = f"[SIMULATED] {agent_name} processed: '{message[:50]}...'"
                span.set_attribute("response.type", "success")
                span.set_attribute("response.length", len(response))
                print(f"   ✅ Success: {response}")
                return response
            else:
                error_msg = f"[SIMULATED] {agent_name} encountered an error"
                span.set_attribute("response.type", "error")
                span.set_attribute("error.message", error_msg)
                print(f"   ❌ Error: {error_msg}")
                raise Exception(error_msg)
    
    @trace_method("test.orchestration_flow")
    async def test_orchestration_flow(self):
        """Test a complete orchestration flow with telemetry."""
        
        print("\n🔄 Testing Orchestration Flow with Telemetry")
        print("=" * 60)
        
        test_scenarios = [
            {
                "message": "I need to analyze market trends for Q4 planning",
                "expected_agent": "SWOTAnalysisAgent",
                "category": "analysis"
            },
            {
                "message": "Record my thoughts about the team's performance this quarter",
                "expected_agent": "CEOLogAgent",
                "category": "strategic"
            },
            {
                "message": "Create a resource optimization plan for the new project",
                "expected_agent": "ResourceOptimizationAgent",
                "category": "planning"
            }
        ]
        
        for scenario in test_scenarios:
            with create_span_context("test.orchestration.scenario", {
                "scenario.message": scenario["message"],
                "scenario.expected_agent": scenario["expected_agent"],
                "scenario.category": scenario["category"]
            }) as span:
                
                print(f"\n📤 Testing: {scenario['message']}")
                
                # Simulate orchestrator routing
                await self.simulate_agent_call("MainOrchestrator", scenario["message"])
                
                # Simulate specialist agent call
                try:
                    await self.simulate_agent_call(
                        scenario["expected_agent"], 
                        scenario["message"]
                    )
                    span.set_attribute("test.result", "success")
                except Exception as e:
                    span.set_attribute("test.result", "failure")
                    span.set_attribute("test.error", str(e))
                    print(f"   ⚠️  Handled error: {e}")
    
    @trace_method("test.performance_metrics")
    async def test_performance_metrics(self):
        """Generate performance metric traces."""
        
        print("\n📈 Generating Performance Metrics")
        print("=" * 60)
        
        agents_to_test = ["CEOLogAgent", "SWOTAnalysisAgent", "StrategicPlanningAgent"]
        
        for agent_name in agents_to_test:
            with create_span_context(f"performance.{agent_name.lower()}", {
                "metric.type": "response_time",
                "agent.name": agent_name
            }) as span:
                
                # Simulate varying response times
                import random
                response_time_ms = random.randint(100, 1500)
                await asyncio.sleep(response_time_ms / 1000)
                
                span.set_attribute("response_time_ms", response_time_ms)
                span.set_attribute("performance.category", 
                    "fast" if response_time_ms < 500 
                    else "normal" if response_time_ms < 1000 
                    else "slow"
                )
                
                print(f"   {agent_name}: {response_time_ms}ms")
    
    @trace_method("test.error_scenarios")
    async def test_error_scenarios(self):
        """Test error tracking with telemetry."""
        
        print("\n🚨 Testing Error Scenarios")
        print("=" * 60)
        
        error_scenarios = [
            {
                "type": "timeout",
                "message": "Agent response timeout after 30s"
            },
            {
                "type": "rate_limit",
                "message": "Rate limit exceeded for API calls"
            },
            {
                "type": "invalid_request",
                "message": "Invalid request format"
            }
        ]
        
        for scenario in error_scenarios:
            with create_span_context(f"error.{scenario['type']}", {
                "error.type": scenario['type'],
                "error.simulated": True
            }) as span:
                
                print(f"   Testing {scenario['type']} error...")
                
                try:
                    # Simulate error
                    raise Exception(scenario['message'])
                except Exception as e:
                    span.record_exception(e)
                    span.set_attribute("error.handled", True)
                    print(f"   ✅ Error tracked: {e}")
    
    async def run_all_tests(self):
        """Run all telemetry tests."""
        
        print("\n🚀 Starting Azure AI Agent Service Telemetry Tests")
        print("=" * 60)
        print(f"📊 Application Insights: stratos-multi-agent-appinsights")
        print(f"🕐 Test Time: {datetime.now().isoformat()}")
        print(f"📍 Project: {self.project_name}")
        print("=" * 60)
        
        # Run test suites
        await self.test_orchestration_flow()
        await self.test_performance_metrics()
        await self.test_error_scenarios()
        
        print("\n" + "=" * 60)
        print("✅ Telemetry tests completed!")
        print("\n📊 View Results:")
        print("1. Go to Azure Portal > Application Insights")
        print("2. Select 'stratos-multi-agent-appinsights'")
        print("3. Navigate to:")
        print("   - Transaction Search: View individual traces")
        print("   - Application Map: See service dependencies")
        print("   - Performance: Analyze response times")
        print("   - Failures: Review error tracking")
        print("\n🔍 Sample Kusto Queries:")
        print("   traces | where customDimensions.service_name == 'AgentServiceTelemetryTester'")
        print("   exceptions | where timestamp > ago(1h)")
        print("   customMetrics | where name contains 'response_time'")


async def main():
    """Main entry point."""
    tester = AgentServiceTelemetryTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())