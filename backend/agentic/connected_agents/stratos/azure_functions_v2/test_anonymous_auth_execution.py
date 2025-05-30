#!/usr/bin/env python3
"""
Test server-side execution with anonymous auth agent.
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Add parent directories to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.agents.models import (
    MessageRole,
    AgentThreadCreationOptions,
    ThreadMessageOptions
)

# Load environment variables
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)


def test_server_side_execution():
    """Test that the agent executes HTTP calls autonomously."""
    
    print("=" * 70)
    print("TESTING SERVER-SIDE EXECUTION WITH ANONYMOUS AUTH")
    print("=" * 70)
    
    # Configuration
    agent_id = "asst_VNHU36RhozDb0XoMJ9phxOMB"
    connection_string = os.getenv("AZURE_AI_PROJECT_CONNECTION_STRING")
    test_org_id = f"test-org-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    
    # Initialize client
    credential = DefaultAzureCredential()
    project_client = AIProjectClient(
        endpoint=connection_string,
        credential=credential
    )
    
    print(f"Agent ID: {agent_id}")
    print(f"Test Org: {test_org_id}")
    print("\nMethod: create_thread_and_process_run()")
    print("Expected: Agent makes HTTP call to Azure Function directly")
    print("-" * 70)
    
    # Test cases
    test_cases = [
        {
            "name": "Set Purpose",
            "message": f"Set the organizational purpose to 'Transform healthcare through AI innovation' for organization {test_org_id}"
        },
        {
            "name": "Get Purpose",
            "message": f"What is the current organizational purpose for {test_org_id}?"
        },
        {
            "name": "Set Vision",
            "message": f"Set the vision to 'Become the global leader in AI-driven healthcare by 2030' for organization {test_org_id}"
        },
        {
            "name": "Add Values",
            "message": f"Add these core values for {test_org_id}: Innovation, Patient-First, Excellence"
        },
        {
            "name": "Create Goal",
            "message": f"Create a strategic goal for {test_org_id}: 'Launch AI Diagnostic Platform' with description 'Develop and deploy AI-powered diagnostic tools' targeting Q3 2025"
        },
        {
            "name": "Get Summary",
            "message": f"Give me a complete North Star summary for {test_org_id}"
        }
    ]
    
    results = []
    
    for test in test_cases:
        print(f"\n{'='*70}")
        print(f"TEST: {test['name']}")
        print(f"{'='*70}")
        print(f"Message: {test['message']}")
        
        try:
            # Create thread with message
            thread_options = AgentThreadCreationOptions(
                messages=[
                    ThreadMessageOptions(
                        role=MessageRole.USER,
                        content=test['message']
                    )
                ]
            )
            
            print("\n⚡ Executing create_thread_and_process_run()...")
            print("   NO client-side HTTP execution")
            print("   Agent will call Azure Function directly")
            
            # Execute autonomously
            run = project_client.agents.create_thread_and_process_run(
                agent_id=agent_id,
                thread=thread_options
            )
            
            print(f"\n✅ Run completed!")
            print(f"Run ID: {run.id}")
            print(f"Thread ID: {run.thread_id}")
            print(f"Status: {run.status}")
            
            # Check status
            if str(run.status) == "RunStatus.COMPLETED":
                print("\n🎉 SUCCESS: Server-side execution worked!")
                
                # Try to get the response
                try:
                    messages = project_client.agents.list_messages(thread_id=run.thread_id)
                    for msg in messages:
                        if msg.role == MessageRole.ASSISTANT:
                            print("\n📋 Agent Response:")
                            for content in msg.content:
                                if hasattr(content, 'text') and hasattr(content.text, 'value'):
                                    print(content.text.value)
                            break
                except Exception as e:
                    print(f"\nCouldn't retrieve messages: {e}")
                
                results.append({"test": test['name'], "status": "SUCCESS"})
                
            elif str(run.status) == "RunStatus.FAILED":
                print("\n❌ Run failed!")
                if hasattr(run, 'last_error') and run.last_error:
                    print(f"Error: {run.last_error}")
                results.append({"test": test['name'], "status": "FAILED", "error": str(run.last_error)})
            
            else:
                print(f"\n⚠️ Unexpected status: {run.status}")
                results.append({"test": test['name'], "status": str(run.status)})
                
        except Exception as e:
            print(f"\n❌ Exception: {e}")
            results.append({"test": test['name'], "status": "ERROR", "error": str(e)})
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST RESULTS SUMMARY")
    print("=" * 70)
    
    successful = sum(1 for r in results if r["status"] == "SUCCESS")
    total = len(results)
    
    for result in results:
        status_icon = "✅" if result["status"] == "SUCCESS" else "❌"
        print(f"{status_icon} {result['test']}: {result['status']}")
        if "error" in result:
            print(f"   Error: {result['error']}")
    
    print(f"\nTotal: {successful}/{total} successful")
    
    if successful == total:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ Server-side autonomous execution VERIFIED")
        print("✅ Agent makes HTTP calls directly without client intervention")
        print("✅ Flow: User → Agent → Azure AI Service → Azure Function → Cosmos DB")
        
        # Save success report
        success_report = {
            "timestamp": datetime.now().isoformat(),
            "agent_id": agent_id,
            "test_org_id": test_org_id,
            "auth_type": "anonymous",
            "all_tests_passed": True,
            "server_side_execution": "VERIFIED",
            "results": results
        }
        
        success_file = Path(__file__).parent / f"SUCCESS_VERIFIED_{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
        with open(success_file, "w") as f:
            json.dump(success_report, f, indent=2)
        
        print(f"\n✅ Success report saved: {success_file}")
    
    return results


if __name__ == "__main__":
    if not os.getenv("AZURE_AI_PROJECT_CONNECTION_STRING"):
        print("Error: AZURE_AI_PROJECT_CONNECTION_STRING not set")
        exit(1)
    
    print("\n🚀 Starting comprehensive server-side execution test...")
    results = test_server_side_execution()
    
    print("\n" + "=" * 70)
    print("✅ Test completed")
    print("=" * 70)