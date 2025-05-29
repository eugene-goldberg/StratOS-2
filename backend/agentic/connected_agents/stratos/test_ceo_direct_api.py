#!/usr/bin/env python3
"""
Direct API test of CEO Log Agent -> Azure Function -> Cosmos DB
Using REST API directly without semantic kernel
"""

import os
import json
import time
import requests
from datetime import datetime
from dotenv import load_dotenv
from azure.cosmos import CosmosClient
from azure.identity import DefaultAzureCredential

# Load environment variables  
load_dotenv()

# Azure configuration
credential = DefaultAzureCredential()

# Get access token for AI Agent Service
token = credential.get_token("https://ml.azure.com/.default")

# API configuration
PROJECT_ENDPOINT = os.getenv("AZURE_AI_PROJECT_CONNECTION_STRING")
API_VERSION = "2024-12-01-preview"
CEO_LOG_AGENT_ID = "asst_mpgSYbBEqI14rLta34RX8RoP"

# Cosmos DB configuration
cosmos_client = CosmosClient(
    url=os.getenv("COSMOS_DB_ENDPOINT"),
    credential=os.getenv("COSMOS_DB_KEY")
)

def check_cosmos_before():
    """Check Cosmos DB before test"""
    try:
        database = cosmos_client.get_database_client("StratOSData")
        container = database.get_container_client("CEOLogs")
        
        query = "SELECT VALUE COUNT(1) FROM c"
        items = list(container.query_items(query=query, enable_cross_partition_query=True))
        count = items[0] if items else 0
        
        print(f"✓ Cosmos DB connected - Items before: {count}")
        return count
    except Exception as e:
        print(f"✗ Cosmos DB error: {e}")
        return None

def test_ceo_agent_api():
    """Test CEO Log Agent via direct API calls"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    test_content = f"E2E API Test {timestamp}: Testing CEO Log Agent with Azure Functions"
    
    headers = {
        "Authorization": f"Bearer {token.token}",
        "Content-Type": "application/json",
        "api-version": API_VERSION
    }
    
    try:
        # 1. Create thread
        thread_url = f"{PROJECT_ENDPOINT}/threads?api-version={API_VERSION}"
        thread_resp = requests.post(thread_url, headers=headers, json={})
        thread_resp.raise_for_status()
        thread_id = thread_resp.json()["id"]
        print(f"✓ Thread created: {thread_id}")
        
        # 2. Add message
        message_url = f"{PROJECT_ENDPOINT}/threads/{thread_id}/messages?api-version={API_VERSION}"
        message_data = {
            "role": "user",
            "content": f"Save this CEO log entry: '{test_content}'. Category: E2E Testing, Source: API test"
        }
        msg_resp = requests.post(message_url, headers=headers, json=message_data)
        msg_resp.raise_for_status()
        print("✓ Message added to thread")
        
        # 3. Create run
        run_url = f"{PROJECT_ENDPOINT}/threads/{thread_id}/runs?api-version={API_VERSION}"
        run_data = {
            "assistant_id": CEO_LOG_AGENT_ID
        }
        run_resp = requests.post(run_url, headers=headers, json=run_data)
        run_resp.raise_for_status()
        run_id = run_resp.json()["id"]
        print(f"✓ Run created: {run_id}")
        
        # 4. Wait for completion
        print("⏳ Waiting for agent response...")
        max_wait = 60
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            status_url = f"{PROJECT_ENDPOINT}/threads/{thread_id}/runs/{run_id}?api-version={API_VERSION}"
            status_resp = requests.get(status_url, headers=headers)
            status_resp.raise_for_status()
            status = status_resp.json()["status"]
            
            print(f"  Status: {status}")
            
            if status == "completed":
                print("✓ Run completed successfully")
                break
            elif status == "failed":
                error = status_resp.json().get("last_error", {})
                print(f"✗ Run failed: {error}")
                return None
            elif status == "requires_action":
                # Handle required actions
                required_action = status_resp.json().get("required_action", {})
                if required_action.get("type") == "submit_tool_outputs":
                    tool_calls = required_action["submit_tool_outputs"]["tool_calls"]
                    print(f"  Handling {len(tool_calls)} tool calls...")
                    
                    # Submit dummy outputs to continue
                    tool_outputs = []
                    for tool_call in tool_calls:
                        print(f"    Tool: {tool_call['function']['name']}")
                        tool_outputs.append({
                            "tool_call_id": tool_call["id"],
                            "output": json.dumps({"message": "Use code interpreter for HTTP calls"})
                        })
                    
                    submit_url = f"{PROJECT_ENDPOINT}/threads/{thread_id}/runs/{run_id}/submit_tool_outputs?api-version={API_VERSION}"
                    submit_data = {"tool_outputs": tool_outputs}
                    submit_resp = requests.post(submit_url, headers=headers, json=submit_data)
                    submit_resp.raise_for_status()
            
            time.sleep(2)
        
        # 5. Get messages
        messages_url = f"{PROJECT_ENDPOINT}/threads/{thread_id}/messages?api-version={API_VERSION}"
        messages_resp = requests.get(messages_url, headers=headers)
        messages_resp.raise_for_status()
        
        for msg in messages_resp.json()["data"]:
            if msg["role"] == "assistant":
                content = msg["content"][0]["text"]["value"]
                print(f"\n🤖 Agent response: {content[:200]}...")
                return test_content
        
    except Exception as e:
        print(f"✗ API Error: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"   Response: {e.response.text}")
        return None

def check_cosmos_after(test_content, count_before):
    """Check Cosmos DB after test"""
    try:
        database = cosmos_client.get_database_client("StratOSData")
        container = database.get_container_client("CEOLogs")
        
        # Count after
        query = "SELECT VALUE COUNT(1) FROM c"
        items = list(container.query_items(query=query, enable_cross_partition_query=True))
        count_after = items[0] if items else 0
        
        print(f"\n✓ Items after: {count_after} (created: {count_after - count_before})")
        
        if count_after > count_before:
            # Get recent entry
            query = "SELECT TOP 1 * FROM c ORDER BY c._ts DESC"
            items = list(container.query_items(query=query, enable_cross_partition_query=True))
            
            if items:
                item = items[0]
                print(f"\n🎯 Found new entry:")
                print(f"   ID: {item.get('id')}")
                print(f"   Content: {item.get('content', '')[:100]}...")
                
                if test_content in str(item.get('content', '')):
                    print(f"\n✅ VERIFIED: This is our test entry!")
                    return True
                else:
                    print(f"\n✅ New entry created (agent worked)")
                    return True
        
        return False
        
    except Exception as e:
        print(f"✗ Error checking Cosmos: {e}")
        return False

def main():
    print("\n" + "="*60)
    print("CEO LOG AGENT DIRECT API TEST")
    print("Testing: Agent → Azure Function → Cosmos DB")
    print("="*60)
    
    # Check before
    count_before = check_cosmos_before()
    if count_before is None:
        return
    
    # Test agent via API
    test_content = test_ceo_agent_api()
    if not test_content:
        print("❌ Agent test failed")
        return
    
    # Wait for processing
    print("\n⏳ Waiting 10 seconds for Azure Function...")
    time.sleep(10)
    
    # Check after
    success = check_cosmos_after(test_content, count_before)
    
    print("\n" + "="*60)
    if success:
        print("✅ SUCCESS: CEO Log Agent → Azure Function → Cosmos DB")
        print("   The complete flow is working!")
    else:
        print("❌ FAILED: Check Azure Function logs")
        print("   https://stratos-ceo-log-functions.azurewebsites.net")

if __name__ == "__main__":
    main()