#!/usr/bin/env python3
"""
Direct test of CEO Log Agent using OpenAI client.
This tests if the agent actually makes HTTP calls to Azure Functions.
"""

import os
import json
import time
from openai import AzureOpenAI
from dotenv import load_dotenv

# Load environment
load_dotenv()
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

# Azure OpenAI configuration
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "https://sk-multi-agent-openai.openai.azure.com/")
AZURE_OPENAI_KEY = os.getenv("AZURE_OPENAI_API_KEY", "b77c5b137db6465dabdbc34adb136e2c")
AZURE_OPENAI_VERSION = "2024-02-15-preview"

# CEO Log Agent ID (from OpenAI deployment)
CEO_LOG_AGENT_ID = "asst_qOFhcSTQ8RmUmUSP7vR1frIG"

def test_ceo_log_agent():
    """Test CEO Log Agent directly with OpenAI client."""
    print("\n🚀 Testing CEO Log Agent with OpenAI Client")
    print("=" * 60)
    
    # Create client
    client = AzureOpenAI(
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
        api_key=AZURE_OPENAI_KEY,
        api_version=AZURE_OPENAI_VERSION
    )
    
    print(f"Agent ID: {CEO_LOG_AGENT_ID}")
    print(f"Endpoint: {AZURE_OPENAI_ENDPOINT}")
    
    try:
        # Create a thread
        print("\n1. Creating thread...")
        thread = client.beta.threads.create()
        print(f"✅ Thread created: {thread.id}")
        
        # Add message
        test_message = """
Please save this CEO log entry using the call_ceo_function:

Content: "E2E Test - Successfully integrated CEO Log Agent with Azure Functions and Cosmos DB. 
The agent can now persist strategic insights directly to our database."
Category: strategic_planning
Tags: ["integration", "azure", "cosmos", "e2e-test"]
User ID: test_user_e2e

Use the save_log operation to save this entry.
"""
        
        print("\n2. Adding message...")
        message = client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=test_message
        )
        print(f"✅ Message added: {message.id}")
        
        # Create run
        print("\n3. Creating run...")
        run = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=CEO_LOG_AGENT_ID
        )
        print(f"✅ Run created: {run.id}")
        print(f"Initial status: {run.status}")
        
        # Poll for completion
        print("\n4. Processing...")
        while run.status in ["queued", "in_progress", "requires_action"]:
            time.sleep(2)
            run = client.beta.threads.runs.retrieve(
                thread_id=thread.id,
                run_id=run.id
            )
            print(f"Status: {run.status}")
            
            # Check for required actions (function calls)
            if run.status == "requires_action":
                print("\n🎯 FUNCTION CALL DETECTED!")
                if run.required_action and run.required_action.submit_tool_outputs:
                    tool_calls = run.required_action.submit_tool_outputs.tool_calls
                    for tool_call in tool_calls:
                        print(f"\nFunction: {tool_call.function.name}")
                        print(f"Arguments: {tool_call.function.arguments}")
                        
                        # Parse and display arguments
                        try:
                            args = json.loads(tool_call.function.arguments)
                            print("Parsed arguments:")
                            for key, value in args.items():
                                print(f"  - {key}: {value}")
                        except:
                            pass
                
                # For now, we'll let the run fail to see what happens
                print("\n❗ Not submitting tool outputs - letting agent use code interpreter")
                break
        
        # Get run steps
        print("\n5. Checking run steps...")
        steps = client.beta.threads.runs.steps.list(
            thread_id=thread.id,
            run_id=run.id
        )
        
        for i, step in enumerate(steps.data):
            print(f"\nStep {i+1}:")
            print(f"  Type: {step.type}")
            print(f"  Status: {step.status}")
            
            if step.type == "tool_calls" and step.step_details:
                tool_calls = step.step_details.tool_calls
                for tool_call in tool_calls:
                    if hasattr(tool_call, 'code_interpreter') and tool_call.code_interpreter:
                        print("  Code Interpreter:")
                        if hasattr(tool_call.code_interpreter, 'input'):
                            print(f"    Input: {tool_call.code_interpreter.input[:200]}...")
                        if hasattr(tool_call.code_interpreter, 'outputs'):
                            for output in tool_call.code_interpreter.outputs:
                                if hasattr(output, 'logs'):
                                    print(f"    Output: {output.logs[:500]}...")
        
        # Get messages
        print("\n6. Getting response...")
        messages = client.beta.threads.messages.list(thread_id=thread.id)
        
        for msg in messages.data:
            if msg.role == "assistant":
                print(f"\n🤖 AGENT RESPONSE:")
                for content in msg.content:
                    if content.type == "text":
                        print(content.text.value)
        
        # Final status
        print(f"\n7. Final run status: {run.status}")
        
        # Check if any HTTP requests were made
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        print(f"Thread ID: {thread.id}")
        print(f"Run ID: {run.id}")
        print(f"Final Status: {run.status}")
        
        if run.status == "completed":
            print("\n✅ Run completed successfully!")
            print("Check the steps above to see if HTTP requests were made to Azure Functions")
        elif run.status == "failed":
            print("\n❌ Run failed!")
            if hasattr(run, 'last_error') and run.last_error:
                print(f"Error: {run.last_error.message}")
        
    except Exception as e:
        print(f"\n❌ ERROR: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_ceo_log_agent()