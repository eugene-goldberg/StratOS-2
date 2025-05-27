#!/usr/bin/env python3
"""
Test FULL orchestration delegation flow with telemetry.
This script will verify end-to-end routing between MainOrchestrator and ALL specialist agents.
"""

import os
import sys
import asyncio
import json
from datetime import datetime
from typing import Dict, List, Any, Optional

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from azure.ai.projects.aio import AIProjectClient
from azure.identity import DefaultAzureCredential
from semantic_kernel import Kernel
from semantic_kernel.agents.azure_ai import AzureAIAgent
from semantic_kernel.functions import kernel_function
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.contents import ChatMessageContent, AuthorRole

from config.settings import get_settings
from core.telemetry import initialize_telemetry, trace_async
from scripts.load_deployed_agents import load_deployed_agents

settings = get_settings()

# Initialize telemetry
tracer = initialize_telemetry(
    service_name="FullOrchestrationTest",
    service_version="1.0.0",
    connection_string=settings.APPLICATION_INSIGHTS_CONNECTION_STRING
)

class OrchestrationDelegationTester:
    def __init__(self):
        self.client = None
        self.kernel = None
        self.agents = {}
        self.test_results = {
            "orchestrator_works": False,
            "delegations_attempted": 0,
            "successful_delegations": [],
            "failed_delegations": [],
            "agents_tested": set(),
            "full_flows_completed": 0
        }
        
    async def setup(self):
        """Initialize the test environment."""
        print("🔧 Setting up test environment...")
        
        # Load deployed agents
        self.agents = load_deployed_agents()
        print(f"📋 Loaded {len(self.agents)} deployed agents")
        
        # Initialize AI Project Client
        credential = DefaultAzureCredential()
        self.client = AIProjectClient(
            endpoint=settings.AZURE_AI_PROJECT_ENDPOINT,
            subscription_id=settings.AZURE_SUBSCRIPTION_ID,
            resource_group_name=settings.AZURE_RESOURCE_GROUP,
            project_name=settings.AZURE_AI_PROJECT_NAME,
            credential=credential
        )
        
        # Initialize kernel with ALL specialist functions
        self.kernel = Kernel()
        self._register_all_specialist_functions()
        
        print("✅ Test environment ready")
        
    def _register_all_specialist_functions(self):
        """Register function tools for ALL specialist agents."""
        print("\n📝 Registering specialist agent functions...")
        
        # Create a function for each specialist agent
        for agent_name, agent_id in self.agents.items():
            if agent_name == "MainOrchestrator":
                continue
                
            function_name = f"invoke_{agent_name.lower().replace(' ', '')}"
            
            # Create a dynamic function for this agent
            async def invoke_specialist(request: str, agent_id=agent_id, agent_name=agent_name) -> str:
                """Invoke a specialist agent."""
                return await self._actually_invoke_specialist(agent_id, agent_name, request)
            
            # Register the function with the kernel
            self.kernel.add_function(
                plugin_name="specialists",
                function=kernel_function(
                    name=function_name,
                    description=f"Invoke the {agent_name} specialist agent",
                    parameters=[{
                        "name": "request",
                        "description": f"The request to send to {agent_name}",
                        "type": "string",
                        "required": True
                    }]
                )(invoke_specialist)
            )
            
            print(f"  ✓ Registered {function_name}")
            
    async def _actually_invoke_specialist(self, agent_id: str, agent_name: str, request: str) -> str:
        """Actually invoke a specialist agent and return its response."""
        with tracer.start_as_current_span(f"invoke_specialist_{agent_name}") as span:
            span.set_attribute("agent.name", agent_name)
            span.set_attribute("agent.id", agent_id)
            span.set_attribute("request", request[:100])
            
            try:
                # Get agent definition
                agent_def = await self.client.agents.get_agent(agent_id=agent_id)
                agent = AzureAIAgent(client=self.client, definition=agent_def)
                
                # Create thread for specialist
                thread = await self.client.agents.threads.create()
                thread_id = thread.id
                
                # Invoke the specialist
                response_text = ""
                async for chunk in agent.invoke(thread_id=thread_id, message=request):
                    if hasattr(chunk, 'content') and chunk.content:
                        response_text += str(chunk.content)
                
                span.set_attribute("response.length", len(response_text))
                span.set_attribute("success", True)
                
                # Track successful delegation
                self.test_results["successful_delegations"].append({
                    "agent": agent_name,
                    "request": request[:50] + "...",
                    "response_length": len(response_text)
                })
                self.test_results["agents_tested"].add(agent_name)
                
                return response_text
                
            except Exception as e:
                span.set_attribute("error", str(e))
                span.set_attribute("success", False)
                
                # Track failed delegation
                self.test_results["failed_delegations"].append({
                    "agent": agent_name,
                    "error": str(e)
                })
                
                return f"Error invoking {agent_name}: {str(e)}"
    
    async def test_orchestrator_with_delegation(self, test_message: str) -> Dict[str, Any]:
        """Test the MainOrchestrator with actual delegation."""
        with tracer.start_as_current_span("test_orchestrator_delegation") as span:
            span.set_attribute("test.message", test_message)
            
            orchestrator_id = self.agents.get("MainOrchestrator")
            if not orchestrator_id:
                return {"error": "MainOrchestrator not found"}
            
            try:
                # Get orchestrator definition
                orchestrator_def = await self.client.agents.get_agent(agent_id=orchestrator_id)
                
                # Create kernel-aware orchestrator
                orchestrator = AzureAIAgent(
                    client=self.client,
                    definition=orchestrator_def,
                    kernel=self.kernel  # Pass kernel with registered functions
                )
                
                # Create thread
                thread = await self.client.agents.threads.create()
                thread_id = thread.id
                
                print(f"\n🎯 Testing: {test_message}")
                print(f"   Thread: {thread_id}")
                
                # Track delegations
                delegations = []
                
                # Invoke orchestrator
                response_text = ""
                async for chunk in orchestrator.invoke(thread_id=thread_id, message=test_message):
                    if hasattr(chunk, 'content') and chunk.content:
                        response_text += str(chunk.content)
                    
                    # Check if this is a function call
                    if hasattr(chunk, 'function_call'):
                        delegations.append({
                            "function": chunk.function_call.name,
                            "arguments": chunk.function_call.arguments
                        })
                        self.test_results["delegations_attempted"] += 1
                
                # Check if any delegations occurred
                if delegations:
                    self.test_results["orchestrator_works"] = True
                    self.test_results["full_flows_completed"] += 1
                
                span.set_attribute("response.length", len(response_text))
                span.set_attribute("delegations.count", len(delegations))
                span.set_attribute("success", True)
                
                return {
                    "success": True,
                    "response": response_text,
                    "delegations": delegations,
                    "thread_id": thread_id
                }
                
            except Exception as e:
                span.set_attribute("error", str(e))
                span.set_attribute("success", False)
                
                return {
                    "success": False,
                    "error": str(e)
                }
    
    async def run_comprehensive_tests(self):
        """Run comprehensive delegation tests."""
        print("\n" + "="*80)
        print("🚀 COMPREHENSIVE ORCHESTRATION DELEGATION TESTS")
        print("="*80)
        
        # Test cases designed to trigger different specialists
        test_cases = [
            # Strategic Foundation & Insights (5 agents)
            "I need to log that we closed a major deal with Microsoft today for $5M",
            "What are the key risks and opportunities in the AI market?",
            "Perform a SWOT analysis for our cloud expansion strategy",
            "Show me insights from last quarter's strategic decisions",
            "What were our CEO's key decisions in the past month?",
            
            # Analysis & Intelligence (4 agents) 
            "Analyze our competitive position in the healthcare market",
            "Link our revenue goals to our market expansion strategy",
            "What strategic context should guide our product roadmap?",
            "How does our mission align with our current initiatives?",
            
            # Planning & Execution (6 agents)
            "Create an action plan for entering the Asian market",
            "What resources do we need for our AI initiative?",
            "Generate initiatives to achieve 50% revenue growth",
            "How well are our projects aligned with our North Star?",
            "Update our strategic canvas with new market insights",
            "What's our North Star metric for customer satisfaction?"
        ]
        
        # Run each test case
        for i, test_message in enumerate(test_cases, 1):
            print(f"\n{'='*60}")
            print(f"TEST {i}/{len(test_cases)}")
            print(f"{'='*60}")
            
            result = await self.test_orchestrator_with_delegation(test_message)
            
            if result.get("success"):
                print(f"✅ Success!")
                if result.get("delegations"):
                    print(f"   Delegations: {len(result['delegations'])}")
                    for d in result["delegations"]:
                        print(f"   - {d['function']}")
                print(f"   Response length: {len(result.get('response', ''))}")
            else:
                print(f"❌ Failed: {result.get('error')}")
    
    def generate_report(self):
        """Generate comprehensive test report."""
        print("\n" + "="*80)
        print("📊 ORCHESTRATION DELEGATION TEST REPORT")
        print("="*80)
        
        print(f"\n🎯 Orchestrator Status: {'✅ WORKING' if self.test_results['orchestrator_works'] else '❌ NOT WORKING'}")
        print(f"📈 Full Flows Completed: {self.test_results['full_flows_completed']}")
        print(f"🔄 Total Delegations Attempted: {self.test_results['delegations_attempted']}")
        
        print(f"\n✅ Successful Delegations: {len(self.test_results['successful_delegations'])}")
        for delegation in self.test_results["successful_delegations"][:5]:
            print(f"   - {delegation['agent']}: {delegation['request']}")
        
        print(f"\n❌ Failed Delegations: {len(self.test_results['failed_delegations'])}")
        for delegation in self.test_results["failed_delegations"][:5]:
            print(f"   - {delegation['agent']}: {delegation['error']}")
        
        print(f"\n🤖 Agents Tested: {len(self.test_results['agents_tested'])}/{len(self.agents)-1}")
        tested = sorted(self.test_results["agents_tested"])
        for agent in tested:
            print(f"   ✓ {agent}")
        
        # Untested agents
        all_agents = set(self.agents.keys()) - {"MainOrchestrator"}
        untested = all_agents - self.test_results["agents_tested"]
        if untested:
            print(f"\n⚠️  Untested Agents: {len(untested)}")
            for agent in sorted(untested):
                print(f"   ✗ {agent}")
        
        # Final verdict
        print("\n" + "="*80)
        if (self.test_results["orchestrator_works"] and 
            self.test_results["delegations_attempted"] > 0 and
            len(self.test_results["agents_tested"]) >= 10):
            print("✅ VERDICT: Full orchestration delegation is WORKING!")
            print("   Evidence: Multiple successful delegations with telemetry traces")
        else:
            print("❌ VERDICT: Full orchestration delegation is NOT fully verified")
            print("   Missing: Complete end-to-end delegation evidence for all agents")

async def main():
    """Run the comprehensive orchestration delegation test."""
    tester = OrchestrationDelegationTester()
    
    try:
        await tester.setup()
        await tester.run_comprehensive_tests()
        tester.generate_report()
        
        # Save detailed results
        results_file = f"orchestration_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w') as f:
            json.dump(tester.test_results, f, indent=2, default=str)
        print(f"\n💾 Detailed results saved to: {results_file}")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())