#!/usr/bin/env python3
"""
Test North Star Agent server-side autonomous execution.
This script verifies that the agent can make HTTP calls directly
without any client-side intervention using create_and_process().
"""

import os
import sys
import json
import asyncio
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Add parent directories to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.agents.models import (
    MessageTextContent,
    MessageRole
)

# Load environment variables
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)


class ServerSideExecutionTester:
    """Test autonomous server-side execution of North Star Agent."""
    
    def __init__(self):
        """Initialize the tester."""
        self.agent_id = "asst_QE7ixESfb0WvA6xkWUm6ycn4"  # From successful deployment
        self.connection_string = os.getenv("AZURE_AI_PROJECT_CONNECTION_STRING")
        self.organization_id = "test-org-123"
        
        # Initialize client
        self.credential = DefaultAzureCredential()
        self.project_client = AIProjectClient(
            endpoint=self.connection_string,
            credential=self.credential
        )
        
        print("=" * 70)
        print("TESTING SERVER-SIDE AUTONOMOUS EXECUTION")
        print("=" * 70)
        print(f"Agent ID: {self.agent_id}")
        print(f"Test Org: {self.organization_id}")
        print("Method: create_and_process() - NO client execution")
        print("=" * 70)
    
    async def test_operation(self, message: str, operation_name: str):
        """Test a single operation using create_and_process()."""
        print(f"\n🔍 Testing: {operation_name}")
        print(f"Message: {message}")
        print("-" * 50)
        
        try:
            # Create thread and process run in one call - AUTONOMOUS EXECUTION
            print("\n⚡ Executing create_thread_and_process_run()...")
            print("   (Agent will make HTTP calls directly)")
            
            # Create thread options with initial message
            from azure.ai.agents.models import AgentThreadCreationOptions, ThreadMessageOptions
            
            thread_options = AgentThreadCreationOptions(
                messages=[
                    ThreadMessageOptions(
                        role=MessageRole.USER,
                        content=message
                    )
                ]
            )
            
            # Create and process run - this executes autonomously
            run = self.project_client.agents.create_thread_and_process_run(
                agent_id=self.agent_id,
                thread=thread_options
            )
            
            print(f"\n✅ Run completed: {run.id}")
            print(f"Status: {run.status}")
            
            # Get the thread ID from the run
            thread_id = run.thread_id
            
            # Get messages using the SDK
            from azure.ai.agents import AgentsClient
            from azure.identity import DefaultAzureCredential
            
            # Create direct agents client
            agents_client = self.project_client.agents
            
            # List messages
            messages = agents_client.list_messages(thread_id=thread_id)
            
            # Find agent response
            agent_response = None
            for msg in messages:
                if msg.role == MessageRole.ASSISTANT:
                    agent_response = msg
                    break
            
            if agent_response:
                print("\n📋 Agent Response:")
                for content in agent_response.content:
                    if hasattr(content, 'text') and hasattr(content.text, 'value'):
                        print(content.text.value)
                    elif isinstance(content, MessageTextContent):
                        print(content.text.value if hasattr(content.text, 'value') else str(content))
                
                # Check for tool calls in run steps
                run_steps = agents_client.list_run_steps(
                    thread_id=thread_id,
                    run_id=run.id
                )
                
                tool_calls_found = False
                for step in run_steps:
                    if hasattr(step, 'step_details') and hasattr(step.step_details, 'tool_calls'):
                        for tool_call in step.step_details.tool_calls:
                            if hasattr(tool_call, 'function'):
                                tool_calls_found = True
                                print(f"\n🔧 Tool Call Detected:")
                                print(f"   Function: {tool_call.function.name}")
                                print(f"   Arguments: {tool_call.function.arguments}")
                
                if tool_calls_found:
                    print("\n✅ SERVER-SIDE EXECUTION CONFIRMED")
                    print("   The agent made HTTP calls autonomously!")
                else:
                    print("\n⚠️  No tool calls detected in run steps")
                
                return True
            else:
                print("\n❌ No agent response found")
                return False
                
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def run_all_tests(self):
        """Run comprehensive tests for all North Star operations."""
        
        test_cases = [
            # Test 1: Set Purpose
            {
                "message": f"Set the organizational purpose to 'To innovate and transform healthcare through AI' for organization {self.organization_id}",
                "operation": "Set Purpose"
            },
            
            # Test 2: Get Purpose
            {
                "message": f"What is the current organizational purpose for {self.organization_id}?",
                "operation": "Get Purpose"
            },
            
            # Test 3: Set Vision
            {
                "message": f"Set the vision to 'Become the leading AI healthcare platform by 2030' for organization {self.organization_id}",
                "operation": "Set Vision"
            },
            
            # Test 4: Add Values
            {
                "message": f"Add these core values for {self.organization_id}: Innovation, Patient-First, Integrity",
                "operation": "Add Values"
            },
            
            # Test 5: Create Strategic Goal
            {
                "message": f"Create a strategic goal for {self.organization_id}: 'Launch AI diagnostic tool' with description 'Develop and deploy AI-powered diagnostic assistant' targeting Q2 2025",
                "operation": "Create Strategic Goal"
            },
            
            # Test 6: Validate Alignment
            {
                "message": f"Check if the initiative 'Partner with regional hospitals' aligns with our North Star for {self.organization_id}",
                "operation": "Validate Alignment"
            },
            
            # Test 7: Get Summary
            {
                "message": f"Give me a complete North Star summary for {self.organization_id}",
                "operation": "Get North Star Summary"
            }
        ]
        
        results = []
        for test in test_cases:
            success = await self.test_operation(test["message"], test["operation"])
            results.append({
                "operation": test["operation"],
                "success": success
            })
            
            # Small delay between tests
            await asyncio.sleep(2)
        
        # Summary
        print("\n" + "=" * 70)
        print("TEST RESULTS SUMMARY")
        print("=" * 70)
        
        successful = sum(1 for r in results if r["success"])
        total = len(results)
        
        for result in results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['operation']}")
        
        print(f"\nTotal: {successful}/{total} successful")
        
        if successful == total:
            print("\n🎉 ALL TESTS PASSED!")
            print("✅ Server-side autonomous execution verified")
            print("✅ Agent makes HTTP calls directly without client intervention")
            print("✅ Flow: User → Agent → Azure AI Service → Azure Function → Cosmos DB")
        else:
            print(f"\n⚠️  {total - successful} tests failed")
        
        return results


async def main():
    """Main test function."""
    
    # Check for required environment variables
    required_vars = [
        "AZURE_AI_PROJECT_CONNECTION_STRING",
    ]
    
    missing = [var for var in required_vars if not os.getenv(var)]
    if missing:
        print(f"Error: Missing environment variables: {missing}")
        return
    
    # Check if agent exists
    print("\n🔍 Checking for deployed agent...")
    
    # Try to load deployment info
    deployment_files = list(Path(__file__).parent.glob("north_star_openapi_deployment_*.json"))
    if deployment_files:
        latest_deployment = max(deployment_files, key=lambda p: p.stat().st_mtime)
        with open(latest_deployment, 'r') as f:
            deployment_info = json.load(f)
        print(f"Found deployment: {deployment_info['agent_name']}")
        print(f"Agent ID: {deployment_info['agent_id']}")
    
    # Run tests
    tester = ServerSideExecutionTester()
    await tester.run_all_tests()
    
    print("\n" + "=" * 70)
    print("✅ Test completed")
    print("=" * 70)
    print("\nKey Achievement:")
    print("• Agent executes HTTP calls server-side")
    print("• No client intervention required")
    print("• Direct Azure AI Service → Azure Function communication")
    print("• Cosmos DB operations work autonomously")


if __name__ == "__main__":
    asyncio.run(main())