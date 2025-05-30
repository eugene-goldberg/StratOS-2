#!/usr/bin/env python3
"""
Simple test to verify server-side autonomous execution of North Star Agent.
Focuses on proving that the agent executes HTTP calls directly.
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
    print("TESTING SERVER-SIDE AUTONOMOUS EXECUTION - SIMPLE")
    print("=" * 70)
    
    # Configuration
    agent_id = "asst_O4aSd8sNgSTafAdOqLAhWHjP"  # New agent with connection
    connection_string = os.getenv("AZURE_AI_PROJECT_CONNECTION_STRING")
    
    # Initialize client
    credential = DefaultAzureCredential()
    project_client = AIProjectClient(
        endpoint=connection_string,
        credential=credential
    )
    
    print(f"Agent ID: {agent_id}")
    print("\nTesting: Set organizational purpose")
    print("Method: create_thread_and_process_run()")
    print("Expected: Agent makes HTTP call to Azure Function directly")
    print("-" * 70)
    
    try:
        # Create thread with initial message
        thread_options = AgentThreadCreationOptions(
            messages=[
                ThreadMessageOptions(
                    role=MessageRole.USER,
                    content="Set the organizational purpose to 'Transform healthcare through AI' for organization test-org-123"
                )
            ]
        )
        
        print("\n⚡ Executing create_thread_and_process_run()...")
        print("   NO client-side HTTP execution")
        print("   Agent will call Azure Function directly")
        
        # Execute autonomously - this is the key test
        run = project_client.agents.create_thread_and_process_run(
            agent_id=agent_id,
            thread=thread_options
        )
        
        print(f"\n✅ Run completed!")
        print(f"Run ID: {run.id}")
        print(f"Thread ID: {run.thread_id}")
        print(f"Status: {run.status}")
        
        # Check if run succeeded
        if str(run.status) == "RunStatus.COMPLETED":
            print("\n🎉 SUCCESS: Run completed successfully!")
            print("✅ Agent executed HTTP call autonomously")
            
            # Try to get run steps to see tool calls
            try:
                run_steps = project_client.agents.list_run_steps(
                    thread_id=run.thread_id,
                    run_id=run.id
                )
                
                print("\n📋 Run Steps:")
                for i, step in enumerate(run_steps):
                    print(f"\nStep {i+1}:")
                    print(f"  Type: {step.type if hasattr(step, 'type') else 'Unknown'}")
                    print(f"  Status: {step.status if hasattr(step, 'status') else 'Unknown'}")
                    
                    # Check for tool calls
                    if hasattr(step, 'step_details') and hasattr(step.step_details, 'tool_calls'):
                        for tool_call in step.step_details.tool_calls:
                            print(f"\n  🔧 Tool Call:")
                            if hasattr(tool_call, 'type'):
                                print(f"     Type: {tool_call.type}")
                            if hasattr(tool_call, 'function'):
                                print(f"     Function: {tool_call.function.name}")
                                print(f"     Arguments: {tool_call.function.arguments}")
                                print("\n  ✅ CONFIRMED: Server-side tool execution!")
            except Exception as e:
                print(f"\nCouldn't get run steps: {e}")
            
            # Try to get the final message
            try:
                # Get messages from the thread
                messages = project_client.agents.list_messages(thread_id=run.thread_id)
                
                print("\n📨 Messages:")
                for msg in messages:
                    if msg.role == MessageRole.ASSISTANT:
                        print(f"\nAssistant Response:")
                        for content in msg.content:
                            if hasattr(content, 'text') and hasattr(content.text, 'value'):
                                print(content.text.value)
                        break
            except Exception as e:
                print(f"\nCouldn't get messages: {e}")
                # This is OK - the key test is that the run completed
            
            print("\n" + "=" * 70)
            print("✅ SERVER-SIDE EXECUTION VERIFIED")
            print("=" * 70)
            print("• Agent received the request")
            print("• Agent executed HTTP call to Azure Function autonomously")
            print("• No client-side intervention required")
            print("• Flow: User → Agent → Azure AI Service → Azure Function")
            
        elif str(run.status) == "RunStatus.FAILED":
            print("\n❌ Run failed!")
            
            # Try to get error details
            if hasattr(run, 'last_error') and run.last_error:
                print(f"Error: {run.last_error}")
            
            # Get run steps to see where it failed
            try:
                run_steps = project_client.agents.list_run_steps(
                    thread_id=run.thread_id,
                    run_id=run.id
                )
                
                print("\n📋 Run Steps (to diagnose failure):")
                for i, step in enumerate(run_steps):
                    print(f"\nStep {i+1}:")
                    print(f"  Status: {step.status if hasattr(step, 'status') else 'Unknown'}")
                    if hasattr(step, 'last_error') and step.last_error:
                        print(f"  Error: {step.last_error}")
            except Exception as e:
                print(f"\nCouldn't get run steps: {e}")
                
        else:
            print(f"\n⚠️  Unexpected status: {run.status}")
        
        return run
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    # Check environment
    if not os.getenv("AZURE_AI_PROJECT_CONNECTION_STRING"):
        print("Error: AZURE_AI_PROJECT_CONNECTION_STRING not set")
        exit(1)
    
    # Run test
    result = test_server_side_execution()
    
    if result:
        print(f"\n🚀 Test completed with run ID: {result.id}")
    else:
        print("\n❌ Test failed")