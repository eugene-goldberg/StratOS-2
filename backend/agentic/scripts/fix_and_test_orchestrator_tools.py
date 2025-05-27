#!/usr/bin/env python3
"""
Fix and test the MainOrchestrator's function tool registration.
This script properly registers all specialist agent functions in the kernel
and tests the complete orchestration flow.
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
from semantic_kernel.agents import AzureAIAgent
from semantic_kernel.functions import kernel_function
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior

from config.settings import get_settings
from core.telemetry import initialize_telemetry
from scripts.load_deployed_agents import load_deployed_agents

settings = get_settings()

# Initialize telemetry
tracer = initialize_telemetry(
    service_name="OrchestratorToolFix",
    service_version="1.0.0",
    connection_string=settings.APPLICATION_INSIGHTS_CONNECTION_STRING
)

class OrchestratorToolFixer:
    def __init__(self):
        self.client = None
        self.kernel = None
        self.agents = {}
        self.test_results = {
            "failures": [],
            "errors": [],
            "successful_delegations": [],
            "agents_responding": set(),
            "orchestrator_status": "NOT_TESTED"
        }
        
    async def setup(self):
        """Initialize the test environment."""
        print("\n❌ STARTING WITH FAILURES AND ERRORS CHECK")
        print("="*60)
        
        # Load deployed agents
        self.agents = load_deployed_agents()
        print(f"📋 Loaded {len(self.agents)} agent configurations")
        
        # Check which agents we have
        missing_agents = []
        for expected in ["MainOrchestrator", "CEOLogAgent", "SWOTTOWSAgent", "RiskOpportunityAgent"]:
            if expected not in self.agents:
                missing_agents.append(expected)
                self.test_results["errors"].append(f"Missing expected agent: {expected}")
        
        if missing_agents:
            print(f"❌ Missing agents: {missing_agents}")
        
        # Initialize AI Project Client
        try:
            credential = DefaultAzureCredential()
            self.client = AIProjectClient(
                endpoint=settings.AZURE_AI_PROJECT_ENDPOINT,
                subscription_id=settings.AZURE_SUBSCRIPTION_ID,
                resource_group_name=settings.AZURE_RESOURCE_GROUP,
                project_name=settings.AZURE_AI_PROJECT_NAME,
                credential=credential
            )
            print("✅ Connected to Azure AI Project")
        except Exception as e:
            error_msg = f"Failed to connect to Azure AI Project: {str(e)}"
            print(f"❌ {error_msg}")
            self.test_results["errors"].append(error_msg)
            raise
        
        # Initialize kernel
        self.kernel = Kernel()
        print("\n📝 Registering specialist agent functions in kernel...")
        
    async def register_specialist_functions(self):
        """Register ALL specialist agent functions in the kernel."""
        registered_count = 0
        failed_registrations = []
        
        # Define the specialist invocation function template
        def create_specialist_invoker(agent_id: str, agent_name: str):
            async def invoke_specialist(request: str) -> str:
                """Invoke a specialist agent and return its response."""
                try:
                    # Get agent definition
                    agent_def = await self.client.agents.get_agent(agent_id=agent_id)
                    agent = AzureAIAgent(client=self.client, definition=agent_def)
                    
                    # Create thread
                    thread = await self.client.agents.threads.create()
                    thread_id = thread.id
                    
                    # Invoke agent
                    response_text = ""
                    async for chunk in agent.invoke(thread_id=thread_id, message=request):
                        if hasattr(chunk, 'content') and chunk.content:
                            response_text += str(chunk.content)
                    
                    # Track success
                    self.test_results["successful_delegations"].append({
                        "agent": agent_name,
                        "request": request[:50] + "...",
                        "response_length": len(response_text)
                    })
                    self.test_results["agents_responding"].add(agent_name)
                    
                    return response_text or f"No response from {agent_name}"
                    
                except Exception as e:
                    error_msg = f"Error invoking {agent_name}: {str(e)}"
                    self.test_results["failures"].append(error_msg)
                    return error_msg
            
            return invoke_specialist
        
        # Register function for each specialist agent
        for agent_name, agent_id in self.agents.items():
            if agent_name == "MainOrchestrator":
                continue
                
            # Normalize function name to match what orchestrator expects
            function_name = f"invoke_{agent_name.lower().replace(' ', '')}"
            
            try:
                # Create the specialist invoker
                invoker = create_specialist_invoker(agent_id, agent_name)
                
                # Register with kernel
                self.kernel.add_function(
                    plugin_name="specialists",
                    function=kernel_function(
                        name=function_name,
                        description=f"Invoke the {agent_name} specialist agent to handle the request",
                    )(invoker)
                )
                
                registered_count += 1
                print(f"  ✓ Registered: {function_name}")
                
            except Exception as e:
                error_msg = f"Failed to register {function_name}: {str(e)}"
                failed_registrations.append(error_msg)
                self.test_results["errors"].append(error_msg)
                print(f"  ✗ {error_msg}")
        
        print(f"\n📊 Registration Summary:")
        print(f"  ✅ Successfully registered: {registered_count}")
        print(f"  ❌ Failed registrations: {len(failed_registrations)}")
        
        return registered_count, failed_registrations
    
    async def test_orchestrator_with_kernel(self, test_message: str) -> Dict[str, Any]:
        """Test the orchestrator with properly registered kernel functions."""
        print(f"\n🧪 TESTING: {test_message}")
        print("-"*60)
        
        orchestrator_id = self.agents.get("MainOrchestrator")
        if not orchestrator_id:
            error = "MainOrchestrator not found in deployed agents"
            print(f"❌ {error}")
            self.test_results["errors"].append(error)
            return {"error": error}
        
        try:
            # Get orchestrator definition
            print("📡 Retrieving orchestrator from Azure...")
            orchestrator_def = await self.client.agents.get_agent(agent_id=orchestrator_id)
            
            # Create orchestrator WITH kernel
            orchestrator = AzureAIAgent(
                client=self.client,
                definition=orchestrator_def,
                kernel=self.kernel  # THIS IS THE KEY - Pass kernel with functions
            )
            
            # Create thread
            thread = await self.client.agents.threads.create()
            thread_id = thread.id
            print(f"📝 Thread created: {thread_id}")
            
            # Invoke orchestrator
            print("🚀 Invoking orchestrator...")
            response_text = ""
            function_calls_made = []
            
            try:
                async for chunk in orchestrator.invoke(thread_id=thread_id, message=test_message):
                    if hasattr(chunk, 'content') and chunk.content:
                        response_text += str(chunk.content)
                    
                    # Track function calls
                    if hasattr(chunk, 'tool_calls'):
                        for tool_call in chunk.tool_calls:
                            function_calls_made.append({
                                "function": tool_call.function.name,
                                "arguments": tool_call.function.arguments
                            })
                
                # Update orchestrator status
                if response_text:
                    self.test_results["orchestrator_status"] = "WORKING"
                
                print(f"\n📊 Results:")
                print(f"  Response length: {len(response_text)}")
                print(f"  Function calls: {len(function_calls_made)}")
                
                if function_calls_made:
                    print("\n  Function calls made:")
                    for fc in function_calls_made:
                        print(f"    - {fc['function']}")
                
                return {
                    "success": True,
                    "response": response_text,
                    "function_calls": function_calls_made,
                    "thread_id": thread_id
                }
                
            except Exception as e:
                error_msg = f"Orchestrator invocation failed: {str(e)}"
                print(f"❌ {error_msg}")
                self.test_results["failures"].append(error_msg)
                self.test_results["orchestrator_status"] = "FAILED"
                
                # Check if it's the missing function tools error
                if "missing from the kernel" in str(e):
                    print("\n🔍 Missing function tools detected!")
                    print("   This confirms the orchestrator expects these functions")
                
                return {
                    "success": False,
                    "error": error_msg
                }
                
        except Exception as e:
            error_msg = f"Failed to setup orchestrator: {str(e)}"
            print(f"❌ {error_msg}")
            self.test_results["errors"].append(error_msg)
            return {"error": error_msg}
    
    async def run_comprehensive_tests(self):
        """Run tests for all specialist agents through orchestrator."""
        print("\n" + "="*80)
        print("COMPREHENSIVE ORCHESTRATION TESTS")
        print("="*80)
        
        # Register functions
        registered, failed = await self.register_specialist_functions()
        
        if registered == 0:
            print("\n❌ CRITICAL: No functions registered! Cannot proceed with tests.")
            return
        
        # Test messages for different agents
        test_cases = [
            ("I need to log an important meeting with investors today", "CEOLogAgent"),
            ("Perform a SWOT analysis for our cloud expansion", "SWOTTOWSAgent"),
            ("What are the main risks in our supply chain?", "RiskOpportunityAgent"),
            ("Generate initiatives for 50% revenue growth", "InitiativeGenerationAgent"),
            ("Update our north star metric for customer satisfaction", "NorthStarAgent")
        ]
        
        # Run tests
        for i, (message, expected_agent) in enumerate(test_cases, 1):
            print(f"\n{'='*60}")
            print(f"TEST {i}/{len(test_cases)} - Expected: {expected_agent}")
            
            result = await self.test_orchestrator_with_kernel(message)
            
            if result.get("success"):
                print(f"✅ Orchestrator responded")
            else:
                print(f"❌ Test failed")
    
    def generate_report(self):
        """Generate failure-first report."""
        print("\n" + "="*80)
        print("❌ FAILURE-FIRST TEST REPORT")
        print("="*80)
        
        # FAILURES FIRST
        print("\n🔴 ERRORS AND FAILURES:")
        if self.test_results["errors"]:
            for error in self.test_results["errors"]:
                print(f"  ❌ {error}")
        else:
            print("  (No setup errors)")
            
        if self.test_results["failures"]:
            print("\n  Runtime Failures:")
            for failure in self.test_results["failures"]:
                print(f"  ❌ {failure}")
        else:
            print("  (No runtime failures)")
        
        # Missing functionality
        print(f"\n🟡 MISSING FUNCTIONALITY:")
        total_agents = len(self.agents) - 1  # Exclude orchestrator
        tested_agents = len(self.test_results["agents_responding"])
        untested = total_agents - tested_agents
        
        print(f"  - Agents not tested: {untested}/{total_agents}")
        print(f"  - Orchestrator status: {self.test_results['orchestrator_status']}")
        
        # Partial successes
        print(f"\n🟢 PARTIAL SUCCESSES:")
        print(f"  - Successful delegations: {len(self.test_results['successful_delegations'])}")
        print(f"  - Agents responding: {len(self.test_results['agents_responding'])}")
        
        if self.test_results["agents_responding"]:
            print("\n  Agents that responded:")
            for agent in sorted(self.test_results["agents_responding"]):
                print(f"    ✓ {agent}")
        
        # Evidence
        print("\n📊 EVIDENCE:")
        if self.test_results["successful_delegations"]:
            print("  Recent successful delegations:")
            for delegation in self.test_results["successful_delegations"][-3:]:
                print(f"    - {delegation['agent']}: {delegation['response_length']} chars")
        
        # Final verdict
        print("\n" + "="*80)
        if (self.test_results["orchestrator_status"] == "WORKING" and 
            len(self.test_results["agents_responding"]) >= 10 and
            len(self.test_results["failures"]) == 0):
            print("✅ VERDICT: Orchestration is WORKING with evidence")
        else:
            print("❌ VERDICT: Orchestration is NOT fully working")
            print(f"   - Orchestrator: {self.test_results['orchestrator_status']}")
            print(f"   - Agents working: {len(self.test_results['agents_responding'])}/15")
            print(f"   - Failures: {len(self.test_results['failures'])}")

async def main():
    """Run the orchestrator tool fix and test."""
    fixer = OrchestratorToolFixer()
    
    try:
        await fixer.setup()
        await fixer.run_comprehensive_tests()
        fixer.generate_report()
        
        # Save results
        results_file = f"orchestrator_fix_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w') as f:
            json.dump(fixer.test_results, f, indent=2, default=str)
        print(f"\n💾 Results saved to: {results_file}")
        
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())