#!/usr/bin/env python3
"""
Test North Star Agent with Direct Function Calls
Agent should call Azure Functions directly without client involvement
"""

import os
import sys
import json
import requests
import time
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# Use the existing deployed agent
AGENT_ID = "asst_7fvXVaebkd4fvb15ySIspxXm"  # Previously deployed North Star Agent
AZURE_AI_ENDPOINT = os.getenv("AZURE_AI_AGENT_ENDPOINT")

# Get auth token
def get_auth_token():
    """Get authentication token using DefaultAzureCredential"""
    from azure.identity import DefaultAzureCredential
    credential = DefaultAzureCredential()
    token = credential.get_token("https://management.azure.com/.default")
    return token.token

def create_thread():
    """Create a new conversation thread"""
    url = f"{AZURE_AI_ENDPOINT}/threads?api-version=2024-12-01-preview"
    headers = {
        "Authorization": f"Bearer {get_auth_token()}",
        "Content-Type": "application/json"
    }
    
    response = requests.post(url, headers=headers, json={})
    response.raise_for_status()
    return response.json()["id"]

def send_message(thread_id, content):
    """Send a message to the thread"""
    url = f"{AZURE_AI_ENDPOINT}/threads/{thread_id}/messages?api-version=2024-12-01-preview"
    headers = {
        "Authorization": f"Bearer {get_auth_token()}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "role": "user",
        "content": content
    }
    
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()

def create_run(thread_id):
    """Create a run to process messages"""
    url = f"{AZURE_AI_ENDPOINT}/threads/{thread_id}/runs?api-version=2024-12-01-preview"
    headers = {
        "Authorization": f"Bearer {get_auth_token()}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "assistant_id": AGENT_ID
    }
    
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()

def get_run_status(thread_id, run_id):
    """Check the status of a run"""
    url = f"{AZURE_AI_ENDPOINT}/threads/{thread_id}/runs/{run_id}?api-version=2024-12-01-preview"
    headers = {
        "Authorization": f"Bearer {get_auth_token()}"
    }
    
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()

def get_messages(thread_id):
    """Get all messages in a thread"""
    url = f"{AZURE_AI_ENDPOINT}/threads/{thread_id}/messages?api-version=2024-12-01-preview"
    headers = {
        "Authorization": f"Bearer {get_auth_token()}"
    }
    
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()["data"]

def test_agent_direct_calls():
    """Test if agent makes direct function calls"""
    print("🚀 Testing North Star Agent Direct Function Calls")
    print("=" * 70)
    print("⚡ IMPORTANT: This test verifies that the agent calls Azure Functions directly")
    print("   The test client will NOT make any function calls!")
    print("=" * 70)
    
    # Test organization ID
    org_id = f"direct-test-{int(datetime.now().timestamp())}"
    
    # Create thread
    print("\n1️⃣ Creating conversation thread...")
    thread_id = create_thread()
    print(f"   ✅ Thread ID: {thread_id}")
    
    # Test: Set organizational purpose
    print("\n2️⃣ Testing: Set organizational purpose")
    message = f"Set the purpose for organization {org_id} to: 'To pioneer breakthrough technologies that solve humanity's greatest challenges'"
    send_message(thread_id, message)
    
    # Create run
    run = create_run(thread_id)
    run_id = run["id"]
    print(f"   ✅ Run ID: {run_id}")
    
    # Monitor the run WITHOUT handling function calls
    print("\n3️⃣ Waiting for agent to complete (agent should call functions directly)...")
    start_time = time.time()
    
    while True:
        run_status = get_run_status(thread_id, run_id)
        status = run_status["status"]
        print(f"   Status: {status}")
        
        if status == "completed":
            print("   ✅ Agent completed successfully!")
            break
            
        elif status == "requires_action":
            # If we see this, it means the agent is NOT calling functions directly
            print("\n   ❌ ERROR: Agent requires action from client!")
            print("   This means the agent is NOT making direct function calls!")
            print("   Required action details:")
            print(json.dumps(run_status.get("required_action", {}), indent=2))
            return False
            
        elif status in ["failed", "cancelled", "expired"]:
            print(f"   ❌ Run failed with status: {status}")
            if "last_error" in run_status:
                print(f"   Error: {run_status['last_error']}")
            return False
        
        # Timeout after 30 seconds
        if time.time() - start_time > 30:
            print("   ❌ Timeout waiting for agent to complete")
            return False
        
        time.sleep(1)
    
    # Get response
    print("\n4️⃣ Getting agent response...")
    messages = get_messages(thread_id)
    for msg in messages:
        if msg["role"] == "assistant":
            print(f"\n🤖 Agent: {msg['content'][0]['text']['value']}")
            break
    
    # Verify in Cosmos DB
    print("\n5️⃣ Verifying data was saved to Cosmos DB...")
    
    from azure.cosmos import CosmosClient
    
    cosmos_connection = os.getenv("COSMOS_DB_CONNECTION_STRING")
    client = CosmosClient.from_connection_string(cosmos_connection)
    database = client.get_database_client("StratOSData")
    container = database.get_container_client("NorthStar")
    
    try:
        item = container.read_item(item=org_id, partition_key=org_id)
        print(f"\n✅ SUCCESS: Data found in Cosmos DB!")
        print(f"   Organization ID: {item['organizationId']}")
        if item.get('purpose'):
            print(f"   Purpose: {item['purpose']['statement']}")
        
        print("\n" + "="*70)
        print("✅ VERIFICATION COMPLETE")
        print("   1. Agent received the request")
        print("   2. Agent made direct HTTP call to Azure Function")
        print("   3. Azure Function saved data to Cosmos DB")
        print("   4. Test client NEVER called any Azure Functions!")
        print("=" * 70)
        
        return True
        
    except Exception as e:
        print(f"❌ No data found in Cosmos DB: {str(e)}")
        print("   This could mean:")
        print("   - The agent didn't make the function call")
        print("   - The function call failed")
        print("   - There was an error saving to Cosmos DB")
        return False

if __name__ == "__main__":
    success = test_agent_direct_calls()
    if success:
        print("\n🎉 Success! The agent is making direct function calls!")
    else:
        print("\n❌ Test failed. The agent is not making direct function calls.")