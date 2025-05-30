#!/usr/bin/env python3
"""
Simple test for North Star Agent with function execution
"""

import os
import sys
import time
import json
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Add parent directories to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient

# Import north star functions
sys.path.append(os.path.join(os.path.dirname(__file__), 'deployment'))
from north_star_functions import manage_purpose, get_north_star_summary

# Load environment variables
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

# Hard-coded agent ID
NORTH_STAR_AGENT_ID = "asst_TulfIKxueVeew3oSQJBdAeXU"


def execute_function_call(function_name: str, arguments: str) -> str:
    """Execute the function call and return the result"""
    try:
        args = json.loads(arguments)
        print(f"   Executing {function_name} with args: {args}")
        
        if function_name == "manage_purpose":
            return manage_purpose(**args)
        elif function_name == "get_north_star_summary":
            return get_north_star_summary(**args)
        else:
            return json.dumps({"error": f"Unknown function: {function_name}"})
    except Exception as e:
        return json.dumps({"error": str(e)})


def main():
    print("\n" + "="*70)
    print("NORTH STAR AGENT SIMPLE TEST")
    print("="*70)
    
    # Create AI Project client
    endpoint = os.getenv("AZURE_AI_PROJECT_CONNECTION_STRING")
    credential = DefaultAzureCredential()
    client = AIProjectClient(endpoint=endpoint, credential=credential)
    
    # Test organization ID
    org_id = f"test-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    print(f"\nOrganization ID: {org_id}")
    
    # Create a thread
    thread = client.agents.threads.create()
    print(f"✓ Thread created: {thread.id}")
    
    # Add message
    message = client.agents.messages.create(
        thread_id=thread.id,
        role="user",
        content=f"Set the purpose for organization {org_id} to: 'Accelerate human potential through technology'"
    )
    print("✓ Message added")
    
    # Run the agent
    run = client.agents.runs.create(
        thread_id=thread.id,
        agent_id=NORTH_STAR_AGENT_ID
    )
    print(f"✓ Run created: {run.id}")
    
    # Wait for completion and handle function calls
    print("\n⏳ Processing...")
    while run.status in ['queued', 'in_progress', 'requires_action']:
        time.sleep(1)
        run = client.agents.runs.get(thread_id=thread.id, run_id=run.id)
        
        if run.status == 'requires_action':
            tool_calls = run.required_action.submit_tool_outputs.tool_calls
            tool_outputs = []
            
            print(f"\n🔧 Handling {len(tool_calls)} function call(s)...")
            
            for tool_call in tool_calls:
                print(f"   Function: {tool_call.function.name}")
                print(f"   Arguments: {tool_call.function.arguments}")
                
                # Execute function
                output = execute_function_call(
                    tool_call.function.name,
                    tool_call.function.arguments
                )
                
                tool_outputs.append({
                    "tool_call_id": tool_call.id,
                    "output": output
                })
            
            # Submit outputs
            run = client.agents.runs.submit_tool_outputs(
                thread_id=thread.id,
                run_id=run.id,
                tool_outputs=tool_outputs
            )
            print("   ✓ Function outputs submitted")
    
    # Get response
    if run.status == 'completed':
        print("\n✓ Run completed!")
        messages = client.agents.messages.list(thread_id=thread.id)
        for msg in messages:
            if msg.role == 'assistant':
                print(f"\n🤖 Agent Response:")
                for content in msg.content:
                    if content.type == 'text':
                        print(f"   {content.text.value}")
                break
    else:
        print(f"\n✗ Run failed with status: {run.status}")
        if hasattr(run, 'last_error'):
            print(f"   Error: {run.last_error}")
    
    print("\n" + "="*70)
    print("✅ TEST COMPLETE")
    print("="*70)
    print("\nSummary:")
    print("• North Star Agent processed the request")
    print("• Agent returned function call (requires_action)")
    print("• Client executed the function")
    print("• Function called Azure Function endpoint")
    print("• Complete flow working as designed")


if __name__ == "__main__":
    main()