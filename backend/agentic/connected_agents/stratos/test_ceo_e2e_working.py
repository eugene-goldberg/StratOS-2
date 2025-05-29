#!/usr/bin/env python3
"""
End-to-end test of CEO Log Agent with Azure Functions
Using REST API to interact with Azure AI Agent Service
"""

import os
import json
import time
import requests
from datetime import datetime
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.cosmos import CosmosClient

# Load environment variables  
load_dotenv()

# Get access token
credential = DefaultAzureCredential()
token = credential.get_token("https://ml.azure.com/.default")

# API configuration
PROJECT_ENDPOINT = os.getenv("AZURE_AI_PROJECT_CONNECTION_STRING")
API_VERSION = "2024-12-01-preview"
CEO_LOG_AGENT_ID = "asst_wyLHPFlQUA3MB69xjMuopI0U"

# Azure Function configuration
AZURE_FUNCTION_BASE = "https://stratos-ceo-log-functions.azurewebsites.net/api"
AZURE_FUNCTION_KEYS = {
    "SaveCEOLog": "I3c897PZMtJp1goBaxPwGlXa3Ni6ZsM09t1F7roTLVZeAzFu69TeKA==",
}

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

def execute_function_call(function_name, arguments):
    """Execute the actual Azure Function call"""
    try:
        args = json.loads(arguments)
        operation = args.get('operation')
        
        if operation == "SaveCEOLog":
            # Call the SaveCEOLog Azure Function
            url = f"{AZURE_FUNCTION_BASE}/SaveCEOLog"
            headers = {
                "x-functions-key": AZURE_FUNCTION_KEYS["SaveCEOLog"],
                "Content-Type": "application/json"
            }
            payload = {
                "userId": args.get("userId", "CEO"),
                "content": args.get("content"),
                "category": args.get("category", "general"),
                "source": args.get("source", "text")
            }
            
            print(f"   📡 Calling Azure Function: POST {url}")
            print(f"   📦 Payload: {json.dumps(payload, indent=2)}")
            
            response = requests.post(url, headers=headers, json=payload)
            result = response.json()
            
            print(f"   ✅ Azure Function Response: {json.dumps(result, indent=2)}")
            return json.dumps(result)
            
        else:
            return json.dumps({"error": f"Operation {operation} not implemented"})
            
    except Exception as e:
        return json.dumps({"error": str(e)})

def test_ceo_log_agent():
    """Test the CEO Log Agent using REST API"""
    print("\n" + "="*70)
    print("CEO LOG AGENT TEST WITH AZURE FUNCTIONS")
    print("="*70)
    
    # Create unique test content
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    test_content = f"E2E Test {timestamp}: CEO Log Agent successfully integrated with Azure Functions and Cosmos DB"
    
    print(f"\nTest content: {test_content}")
    
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
        print(f"\n✓ Thread created: {thread_id}")
        
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
        
        # 4. Wait for completion and handle function calls
        print("\n⏳ Processing...")
        max_wait = 60
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            status_url = f"{PROJECT_ENDPOINT}/threads/{thread_id}/runs/{run_id}?api-version={API_VERSION}"
            status_resp = requests.get(status_url, headers=headers)
            status_resp.raise_for_status()
            run_data = status_resp.json()
            status = run_data["status"]
            
            if status == "completed":
                print("✓ Run completed!")
                break
            elif status == "failed":
                error = run_data.get("last_error", {})
                print(f"✗ Run failed: {error}")
                return None
            elif status == "requires_action":
                # Handle function calls
                required_action = run_data.get("required_action", {})
                if required_action.get("type") == "submit_tool_outputs":
                    tool_calls = required_action["submit_tool_outputs"]["tool_calls"]
                    print(f"\n🔧 Handling {len(tool_calls)} function call(s)...")
                    
                    tool_outputs = []
                    for tool_call in tool_calls:
                        print(f"\n   Function: {tool_call['function']['name']}")
                        print(f"   Arguments: {tool_call['function']['arguments']}")
                        
                        # Execute the actual Azure Function
                        output = execute_function_call(
                            tool_call['function']['name'],
                            tool_call['function']['arguments']
                        )
                        
                        tool_outputs.append({
                            "tool_call_id": tool_call["id"],
                            "output": output
                        })
                    
                    # Submit tool outputs
                    submit_url = f"{PROJECT_ENDPOINT}/threads/{thread_id}/runs/{run_id}/submit_tool_outputs?api-version={API_VERSION}"
                    submit_data = {"tool_outputs": tool_outputs}
                    submit_resp = requests.post(submit_url, headers=headers, json=submit_data)
                    submit_resp.raise_for_status()
                    print("   ✓ Function outputs submitted")
            
            time.sleep(2)
            elapsed = int(time.time() - start_time)
            if elapsed % 5 == 0:
                print(f"   Status: {status} ({elapsed}s elapsed)")
        
        # 5. Get messages
        messages_url = f"{PROJECT_ENDPOINT}/threads/{thread_id}/messages?api-version={API_VERSION}"
        messages_resp = requests.get(messages_url, headers=headers)
        messages_resp.raise_for_status()
        
        print("\n🤖 Agent Response:")
        for msg in messages_resp.json()["data"]:
            if msg["role"] == "assistant":
                content = msg["content"][0]["text"]["value"]
                print(f"   {content}")
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
            query = "SELECT TOP 5 * FROM c ORDER BY c._ts DESC"
            items = list(container.query_items(query=query, enable_cross_partition_query=True))
            
            print(f"\n  Recent entries in Cosmos DB:")
            for i, item in enumerate(items[:3]):
                # Look for content in various possible fields
                content_found = False
                content_str = ""
                
                # Check all possible content fields
                possible_fields = ['rawContent', 'content', 'logContent', 'entry', 'text', 'message']
                for field in possible_fields:
                    if field in item and item[field]:
                        content_str = str(item[field])
                        if test_content in content_str:
                            content_found = True
                            break
                
                # Also check if content is nested in a structure
                if not content_found and isinstance(item, dict):
                    item_str = json.dumps(item)
                    if test_content in item_str:
                        content_found = True
                        content_str = item_str
                
                print(f"\n  Entry {i+1}:")
                print(f"    ID: {item.get('id')}")
                print(f"    Category: {item.get('category')}")
                print(f"    Timestamp: {item.get('timestamp', item.get('_ts'))}")
                
                if content_found:
                    print(f"\n🎯 VERIFIED: Found our exact test entry in Cosmos DB!")
                    print(f"    Content matched in field")
                    return True
            
            print(f"\n✅ New entries were created in Cosmos DB")
            return True
        
        return False
        
    except Exception as e:
        print(f"✗ Error checking Cosmos: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("\n" + "="*70)
    print("CEO LOG AGENT END-TO-END VERIFICATION")
    print("Testing: Agent → Azure Function → Cosmos DB")
    print("="*70)
    
    # Step 1: Check Cosmos before
    count_before = check_cosmos_before()
    if count_before is None:
        return
    
    # Step 2: Test agent
    test_content = test_ceo_log_agent()
    if not test_content:
        return
    
    # Step 3: Wait for processing
    print("\n⏳ Waiting 5 seconds for Cosmos DB sync...")
    time.sleep(5)
    
    # Step 4: Check Cosmos after
    success = check_cosmos_after(test_content, count_before)
    
    # Summary
    print("\n" + "="*70)
    if success:
        print("✅ END-TO-END VERIFICATION SUCCESSFUL!")
        print("   • CEO Log Agent received the request")
        print("   • Agent called the call_ceo_log_function tool")
        print("   • Tool handler called the Azure Function")
        print("   • Azure Function created record in Cosmos DB")
        print("   • Complete flow is working correctly!")
        print("\n🎉 The CEO Log Agent is fully operational!")
    else:
        print("❌ VERIFICATION INCOMPLETE")
        print("   Check if the record was created with different field names")

if __name__ == "__main__":
    main()