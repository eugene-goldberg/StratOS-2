#!/usr/bin/env python3
"""Test code interpreter limitations"""

import os
import json
import time
import requests
from datetime import datetime
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential

load_dotenv()

credential = DefaultAzureCredential()
token = credential.get_token("https://ml.azure.com/.default")

PROJECT_ENDPOINT = os.getenv("AZURE_AI_PROJECT_CONNECTION_STRING")
API_VERSION = "2024-12-01-preview"
CEO_LOG_AGENT_ID = "asst_tslfF2VjSsVrbPNMEHWxcbYD"

headers = {
    "Authorization": f"Bearer {token.token}",
    "Content-Type": "application/json",
    "api-version": API_VERSION
}

# Create thread
thread_resp = requests.post(f"{PROJECT_ENDPOINT}/threads?api-version={API_VERSION}", headers=headers, json={})
thread_id = thread_resp.json()["id"]

# Add test message
message_data = {
    "role": "user",
    "content": "Test if you can make an HTTP request. Use code interpreter to call: curl https://httpbin.org/get"
}
requests.post(f"{PROJECT_ENDPOINT}/threads/{thread_id}/messages?api-version={API_VERSION}", headers=headers, json=message_data)

# Run
run_resp = requests.post(f"{PROJECT_ENDPOINT}/threads/{thread_id}/runs?api-version={API_VERSION}", 
                        headers=headers, json={"assistant_id": CEO_LOG_AGENT_ID})
run_id = run_resp.json()["id"]

print(f"Testing code interpreter HTTP capabilities...")
print(f"Thread: {thread_id}")
print(f"Run: {run_id}")

# Wait for completion
for i in range(20):
    status_resp = requests.get(f"{PROJECT_ENDPOINT}/threads/{thread_id}/runs/{run_id}?api-version={API_VERSION}", headers=headers)
    status = status_resp.json()["status"]
    print(f"  Status: {status}")
    
    if status in ["completed", "failed"]:
        break
    time.sleep(2)

# Get response
messages_resp = requests.get(f"{PROJECT_ENDPOINT}/threads/{thread_id}/messages?api-version={API_VERSION}", headers=headers)
for msg in messages_resp.json()["data"]:
    if msg["role"] == "assistant":
        print(f"\nAgent response:")
        print(msg["content"][0]["text"]["value"])
        break