#!/usr/bin/env python3
"""
Detailed test to see exactly what the CEO Log Agent is doing
"""

import os
import json
import time
import requests
from datetime import datetime
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential

# Load environment variables  
load_dotenv()

# Azure configuration
credential = DefaultAzureCredential()
token = credential.get_token("https://ml.azure.com/.default")

# API configuration
PROJECT_ENDPOINT = os.getenv("AZURE_AI_PROJECT_CONNECTION_STRING")
API_VERSION = "2024-12-01-preview"
CEO_LOG_AGENT_ID = "asst_mpgSYbBEqI14rLta34RX8RoP"

headers = {
    "Authorization": f"Bearer {token.token}",
    "Content-Type": "application/json",
    "api-version": API_VERSION
}

def test_detailed():
    """Test CEO Log Agent and print detailed responses"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    try:
        # Create thread
        thread_url = f"{PROJECT_ENDPOINT}/threads?api-version={API_VERSION}"
        thread_resp = requests.post(thread_url, headers=headers, json={})
        thread_id = thread_resp.json()["id"]
        print(f"Thread: {thread_id}")
        
        # Add message
        message_url = f"{PROJECT_ENDPOINT}/threads/{thread_id}/messages?api-version={API_VERSION}"
        message_data = {
            "role": "user",
            "content": f"Save this CEO log entry: 'Test entry {timestamp} - Testing Azure Function integration'. Category: general, Source: detailed test"
        }
        requests.post(message_url, headers=headers, json=message_data)
        
        # Create run
        run_url = f"{PROJECT_ENDPOINT}/threads/{thread_id}/runs?api-version={API_VERSION}"
        run_data = {"assistant_id": CEO_LOG_AGENT_ID}
        run_resp = requests.post(run_url, headers=headers, json=run_data)
        run_id = run_resp.json()["id"]
        print(f"Run: {run_id}")
        
        # Monitor run
        print("\nMonitoring run...")
        for i in range(30):
            status_url = f"{PROJECT_ENDPOINT}/threads/{thread_id}/runs/{run_id}?api-version={API_VERSION}"
            status_resp = requests.get(status_url, headers=headers)
            run_data = status_resp.json()
            status = run_data["status"]
            
            print(f"\nIteration {i+1}:")
            print(f"  Status: {status}")
            
            if status == "requires_action":
                required_action = run_data.get("required_action", {})
                if required_action.get("type") == "submit_tool_outputs":
                    tool_calls = required_action["submit_tool_outputs"]["tool_calls"]
                    print(f"  Tool calls required: {len(tool_calls)}")
                    
                    for tc in tool_calls:
                        print(f"\n  Tool Call:")
                        print(f"    ID: {tc['id']}")
                        print(f"    Function: {tc['function']['name']}")
                        print(f"    Arguments: {tc['function']['arguments']}")
                    
                    # Submit acknowledgment
                    tool_outputs = []
                    for tc in tool_calls:
                        tool_outputs.append({
                            "tool_call_id": tc["id"],
                            "output": json.dumps({"status": "acknowledged", "message": "Please use code interpreter to make HTTP calls"})
                        })
                    
                    submit_url = f"{PROJECT_ENDPOINT}/threads/{thread_id}/runs/{run_id}/submit_tool_outputs?api-version={API_VERSION}"
                    submit_resp = requests.post(submit_url, headers=headers, json={"tool_outputs": tool_outputs})
                    print(f"  Submitted tool outputs: {submit_resp.status_code}")
            
            elif status == "completed":
                print("  Run completed!")
                break
            elif status == "failed":
                print(f"  Run failed: {run_data.get('last_error')}")
                break
            
            time.sleep(2)
        
        # Get all messages
        print("\n" + "="*60)
        print("FINAL MESSAGES:")
        print("="*60)
        
        messages_url = f"{PROJECT_ENDPOINT}/threads/{thread_id}/messages?api-version={API_VERSION}"
        messages_resp = requests.get(messages_url, headers=headers)
        messages = messages_resp.json()["data"]
        
        for msg in reversed(messages):  # Show in chronological order
            print(f"\n[{msg['role'].upper()}]")
            for content in msg["content"]:
                if content["type"] == "text":
                    print(content["text"]["value"])
        
        # Check for code interpreter outputs
        print("\n" + "="*60)
        print("CHECKING FOR CODE INTERPRETER OUTPUTS:")
        print("="*60)
        
        # Get run steps to see what actually happened
        steps_url = f"{PROJECT_ENDPOINT}/threads/{thread_id}/runs/{run_id}/steps?api-version={API_VERSION}"
        steps_resp = requests.get(steps_url, headers=headers)
        
        if steps_resp.status_code == 200:
            steps = steps_resp.json().get("data", [])
            print(f"\nFound {len(steps)} run steps:")
            
            for step in steps:
                print(f"\nStep {step['id']}:")
                print(f"  Type: {step['type']}")
                print(f"  Status: {step['status']}")
                
                if step['type'] == 'tool_calls':
                    step_details = step.get('step_details', {})
                    tool_calls = step_details.get('tool_calls', [])
                    for tc in tool_calls:
                        print(f"  Tool call type: {tc.get('type')}")
                        if tc.get('type') == 'code_interpreter':
                            print("    CODE INTERPRETER USED!")
                            code_interpreter = tc.get('code_interpreter', {})
                            if 'input' in code_interpreter:
                                print(f"    Input: {code_interpreter['input'][:200]}...")
                            if 'outputs' in code_interpreter:
                                for output in code_interpreter['outputs']:
                                    if output['type'] == 'logs':
                                        print(f"    Output: {output.get('logs', '')[:200]}...")
        
    except Exception as e:
        print(f"Error: {e}")
        if hasattr(e, 'response'):
            print(f"Response: {e.response.text}")

if __name__ == "__main__":
    test_detailed()