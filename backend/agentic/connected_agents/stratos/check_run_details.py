#!/usr/bin/env python3
"""Check details of a specific run"""

import os
import requests
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential

load_dotenv()

credential = DefaultAzureCredential()
token = credential.get_token("https://ml.azure.com/.default")

PROJECT_ENDPOINT = os.getenv("AZURE_AI_PROJECT_CONNECTION_STRING")
API_VERSION = "2024-12-01-preview"

thread_id = "thread_GtsWjKFPjg41Ke2KUVLdWwpO"
run_id = "run_UnWCQZvpXgqLulfTGkT8hziz"

headers = {
    "Authorization": f"Bearer {token.token}",
    "Content-Type": "application/json",
    "api-version": API_VERSION
}

# Get run status
status_url = f"{PROJECT_ENDPOINT}/threads/{thread_id}/runs/{run_id}?api-version={API_VERSION}"
status_resp = requests.get(status_url, headers=headers)
run_data = status_resp.json()

print(f"Run Status: {run_data['status']}")
if 'last_error' in run_data:
    print(f"Error: {run_data['last_error']}")

# Get run steps
steps_url = f"{PROJECT_ENDPOINT}/threads/{thread_id}/runs/{run_id}/steps?api-version={API_VERSION}"
steps_resp = requests.get(steps_url, headers=headers)

if steps_resp.status_code == 200:
    steps = steps_resp.json().get("data", [])
    print(f"\nRun Steps: {len(steps)}")
    
    for step in steps:
        print(f"\nStep {step['id']}:")
        print(f"  Type: {step['type']}")
        print(f"  Status: {step['status']}")
        
        if step['type'] == 'tool_calls':
            step_details = step.get('step_details', {})
            tool_calls = step_details.get('tool_calls', [])
            for tc in tool_calls:
                print(f"  Tool: {tc.get('type')}")
                if tc.get('type') == 'code_interpreter':
                    code = tc.get('code_interpreter', {})
                    if 'input' in code:
                        print(f"  Code Input: {code['input'][:100]}...")

# Get messages
messages_url = f"{PROJECT_ENDPOINT}/threads/{thread_id}/messages?api-version={API_VERSION}"
messages_resp = requests.get(messages_url, headers=headers)
messages = messages_resp.json()["data"]

print(f"\nMessages: {len(messages)}")
for msg in messages:
    print(f"\n[{msg['role'].upper()}]")
    for content in msg["content"]:
        if content["type"] == "text":
            print(content["text"]["value"][:200] + "...")