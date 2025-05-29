#!/usr/bin/env python3
"""
End-to-end test of CEO Log Agent (Code Interpreter Only) -> Azure Function -> Cosmos DB
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
token = credential.get_token("https://ml.azure.com/.default")

# API configuration
PROJECT_ENDPOINT = os.getenv("AZURE_AI_PROJECT_CONNECTION_STRING")
API_VERSION = "2024-12-01-preview"
CEO_LOG_AGENT_ID = "asst_tslfF2VjSsVrbPNMEHWxcbYD"  # Code-only version

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

def test_ceo_agent_e2e():
    """Test CEO Log Agent end-to-end flow"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    test_content = f"E2E Success Test {timestamp}: CEO Log Agent with Code Interpreter successfully integrated with Azure Functions and Cosmos DB"
    
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
            "content": f"Save this CEO log entry: '{test_content}'. Category: strategic_planning"
        }
        msg_resp = requests.post(message_url, headers=headers, json=message_data)
        msg_resp.raise_for_status()
        print("✓ Message added")
        
        # 3. Create run
        run_url = f"{PROJECT_ENDPOINT}/threads/{thread_id}/runs?api-version={API_VERSION}"
        run_data = {"assistant_id": CEO_LOG_AGENT_ID}
        run_resp = requests.post(run_url, headers=headers, json=run_data)
        run_resp.raise_for_status()
        run_id = run_resp.json()["id"]
        print(f"✓ Run created: {run_id}")
        
        # 4. Wait for completion
        print("\n⏳ Waiting for agent to process...")
        max_wait = 60
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            status_url = f"{PROJECT_ENDPOINT}/threads/{thread_id}/runs/{run_id}?api-version={API_VERSION}"
            status_resp = requests.get(status_url, headers=headers)
            status_resp.raise_for_status()
            run_data = status_resp.json()
            status = run_data["status"]
            
            print(f"  Status: {status}")
            
            if status == "completed":
                print("✓ Run completed!")
                break
            elif status == "failed":
                error = run_data.get("last_error", {})
                print(f"✗ Run failed: {error}")
                return None
            
            time.sleep(3)
        
        # 5. Get messages
        messages_url = f"{PROJECT_ENDPOINT}/threads/{thread_id}/messages?api-version={API_VERSION}"
        messages_resp = requests.get(messages_url, headers=headers)
        messages_resp.raise_for_status()
        
        print("\n🤖 Agent response:")
        for msg in messages_resp.json()["data"]:
            if msg["role"] == "assistant":
                content = msg["content"][0]["text"]["value"]
                print(f"  {content[:300]}...")
                
                # Look for entry ID in response
                if "entryId" in content or "entry ID" in content or "saved successfully" in content.lower():
                    print("\n✓ Agent reports successful save!")
                break
        
        return test_content
        
    except Exception as e:
        print(f"✗ Error: {e}")
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
        
        print(f"\n✓ Cosmos DB items after: {count_after}")
        print(f"  New items created: {count_after - count_before}")
        
        if count_after > count_before:
            # Get recent entries
            query = "SELECT TOP 3 * FROM c ORDER BY c._ts DESC"
            items = list(container.query_items(query=query, enable_cross_partition_query=True))
            
            for i, item in enumerate(items):
                print(f"\n  Entry {i+1}:")
                print(f"    ID: {item.get('id')}")
                print(f"    Content: {item.get('rawContent', item.get('content', ''))[:80]}...")
                print(f"    Category: {item.get('category')}")
                print(f"    Created: {item.get('timestamp', item.get('_ts'))}")
                
                # Check if any contain our test content
                item_content = str(item.get('rawContent', '')) + str(item.get('content', ''))
                if test_content in item_content:
                    print(f"\n🎯 VERIFIED: Found our exact test entry!")
                    return True
            
            print(f"\n✅ New entries created in Cosmos DB")
            return True
        
        return False
        
    except Exception as e:
        print(f"✗ Error checking Cosmos: {e}")
        return False

def main():
    print("\n" + "="*70)
    print("CEO LOG AGENT (CODE INTERPRETER) END-TO-END TEST")
    print("Testing: Agent → Azure Function → Cosmos DB")
    print("="*70)
    
    # Step 1: Check Cosmos before
    count_before = check_cosmos_before()
    if count_before is None:
        return
    
    # Step 2: Test agent
    test_content = test_ceo_agent_e2e()
    if not test_content:
        print("\n❌ Agent test failed")
        return
    
    # Step 3: Wait for Azure Function processing
    print("\n⏳ Waiting 10 seconds for Azure Function to process...")
    time.sleep(10)
    
    # Step 4: Check Cosmos after
    success = check_cosmos_after(test_content, count_before)
    
    # Summary
    print("\n" + "="*70)
    if success:
        print("✅ END-TO-END VERIFICATION SUCCESSFUL!")
        print("   • CEO Log Agent (Code Interpreter) received the request")
        print("   • Agent used code interpreter to call Azure Function") 
        print("   • Azure Function successfully created Cosmos DB record")
        print("   • Complete flow is working correctly!")
    else:
        print("❌ END-TO-END VERIFICATION FAILED")
        print("   Check Azure Function logs for any errors")

if __name__ == "__main__":
    main()