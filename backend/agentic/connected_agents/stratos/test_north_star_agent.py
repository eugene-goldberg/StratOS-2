#!/usr/bin/env python3
"""
Test North Star Agent E2E Flow
Following the CEO Log Agent pattern
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
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

# Agent configuration
AGENT_ID = "asst_7fvXVaebkd4fvb15ySIspxXm"
AZURE_AI_ENDPOINT = os.getenv("AZURE_AI_AGENT_ENDPOINT")
AZURE_FUNCTION_KEY = "gPXyuj42jT_BnlDhImnO1gaV_xayICaGrxf2NoTA1_hVAzFuSjMcqQ=="

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
        "assistant_id": AGENT_ID,
        "instructions": "You are the North Star Agent. Process the user's request and use the appropriate functions."
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

def submit_tool_outputs(thread_id, run_id, tool_outputs):
    """Submit function call results back to the agent"""
    url = f"{AZURE_AI_ENDPOINT}/threads/{thread_id}/runs/{run_id}/submit_tool_outputs?api-version=2024-12-01-preview"
    headers = {
        "Authorization": f"Bearer {get_auth_token()}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "tool_outputs": tool_outputs
    }
    
    response = requests.post(url, headers=headers, json=payload)
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

def call_azure_function(operation, params):
    """Call the appropriate Azure Function endpoint"""
    # Map operation to endpoint and key
    endpoint_map = {
        "ManagePurpose": ("ManagePurpose", "gPXyuj42jT_BnlDhImnO1gaV_xayICaGrxf2NoTA1_hVAzFuSjMcqQ=="),
        "ManageVision": ("ManageVision", "hxaRNlD2FmGt9IHzHGXhtVavLrHvlDVkMtDfAe_j3cwyAzFuiAd75Q=="),
        "ManageValues": ("ManageValues", "NliL5fD1aEmXoLSqoa1NSCzDbN2PEeSlCUYZAS6pxcc4AzFujGLDpw=="),
        "ManageStrategicGoals": ("ManageStrategicGoals", "kaS2TH5L7__RTKaLc8XfoxHDVW9AP8wE2p_Ei3lBQNvzAzFu4mIw4g=="),
        "ValidateAlignment": ("ValidateAlignment", "968fvYsjeBk7tEbv-0Bvt7RniJcynmitd_JR3Y-I5tHnAzFuZxFbwg=="),
        "GetNorthStarSummary": ("GetNorthStarSummary", "-W8ykJ6kkUyeLQCZXNklZqdoL1fOFhw1dvLQniJtqYvwAzFunTkKNA==")
    }
    
    endpoint_info = endpoint_map.get(operation)
    if not endpoint_info:
        return {"error": f"Unknown operation: {operation}"}
    
    endpoint, function_key = endpoint_info
    url = f"https://stratos-north-star-functions.azurewebsites.net/api/{endpoint}"
    headers = {
        "x-functions-key": function_key,
        "Content-Type": "application/json"
    }
    
    # Prepare payload based on operation
    payload = params.copy()
    
    print(f"\n📤 Calling Azure Function: {endpoint}")
    print(f"   URL: {url}")
    print(f"   Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        result = response.json()
        print(f"📥 Function Response: {json.dumps(result, indent=2)}")
        return result
    except Exception as e:
        print(f"❌ Function call failed: {str(e)}")
        if hasattr(e, 'response') and hasattr(e.response, 'text'):
            print(f"   Response: {e.response.text}")
        return {"error": str(e)}

def test_north_star_agent():
    """Test the North Star Agent with Azure Function integration"""
    print("🚀 Testing North Star Agent E2E Flow")
    print("=" * 70)
    
    # Test organization ID
    org_id = "stratos-test-org-001"
    
    # Create thread
    print("\n1️⃣ Creating conversation thread...")
    thread_id = create_thread()
    print(f"   ✅ Thread ID: {thread_id}")
    
    # Test 1: Set organizational purpose
    print("\n2️⃣ Testing: Set organizational purpose")
    message = f"Set the organizational purpose to: 'To revolutionize strategic planning through AI-powered insights and automation'"
    send_message(thread_id, message)
    
    # Create run
    run = create_run(thread_id)
    run_id = run["id"]
    print(f"   ✅ Run ID: {run_id}")
    
    # Wait for completion
    print("\n3️⃣ Processing request...")
    while True:
        run_status = get_run_status(thread_id, run_id)
        status = run_status["status"]
        print(f"   Status: {status}")
        
        if status == "completed":
            break
        elif status == "requires_action":
            # Handle function calls
            print("\n4️⃣ Agent requires function call")
            tool_outputs = []
            
            for tool_call in run_status["required_action"]["submit_tool_outputs"]["tool_calls"]:
                func_name = tool_call["function"]["name"]
                func_args = json.loads(tool_call["function"]["arguments"])
                
                print(f"   Function: {func_name}")
                print(f"   Arguments: {json.dumps(func_args, indent=2)}")
                
                # Execute function
                if func_name == "call_north_star_function":
                    # Extract operation and parameters
                    operation = func_args.get("operation")
                    params = {k: v for k, v in func_args.items() if k != "operation"}
                    params["organizationId"] = org_id  # Ensure org ID is included
                    
                    result = call_azure_function(operation, params)
                else:
                    result = {"error": f"Unknown function: {func_name}"}
                
                tool_outputs.append({
                    "tool_call_id": tool_call["id"],
                    "output": json.dumps(result)
                })
            
            # Submit outputs
            submit_tool_outputs(thread_id, run_id, tool_outputs)
            
        elif status in ["failed", "cancelled", "expired"]:
            print(f"   ❌ Run failed with status: {status}")
            if "last_error" in run_status:
                print(f"   Error: {run_status['last_error']}")
            break
        
        time.sleep(1)
    
    # Get response
    print("\n5️⃣ Getting agent response...")
    messages = get_messages(thread_id)
    for msg in messages:
        if msg["role"] == "assistant":
            print(f"\n🤖 Agent: {msg['content'][0]['text']['value']}")
            break
    
    # Test 2: Add organizational values
    print("\n" + "="*70)
    print("6️⃣ Testing: Add organizational values")
    message = "Add these core values: Innovation (Embrace cutting-edge technology), Integrity (Always act ethically), and Customer Focus (Put customers first)"
    send_message(thread_id, message)
    
    run = create_run(thread_id)
    run_id = run["id"]
    
    # Process run (similar to above, simplified for brevity)
    while True:
        run_status = get_run_status(thread_id, run_id)
        status = run_status["status"]
        
        if status == "completed":
            break
        elif status == "requires_action":
            tool_outputs = []
            for tool_call in run_status["required_action"]["submit_tool_outputs"]["tool_calls"]:
                func_args = json.loads(tool_call["function"]["arguments"])
                operation = func_args.get("operation")
                params = {k: v for k, v in func_args.items() if k != "operation"}
                params["organizationId"] = org_id
                
                result = call_azure_function(operation, params)
                tool_outputs.append({
                    "tool_call_id": tool_call["id"],
                    "output": json.dumps(result)
                })
            
            submit_tool_outputs(thread_id, run_id, tool_outputs)
        elif status in ["failed", "cancelled", "expired"]:
            break
        
        time.sleep(1)
    
    # Test 3: Get North Star Summary
    print("\n" + "="*70)
    print("7️⃣ Testing: Get North Star summary")
    message = "Show me our complete North Star foundation"
    send_message(thread_id, message)
    
    run = create_run(thread_id)
    run_id = run["id"]
    
    while True:
        run_status = get_run_status(thread_id, run_id)
        status = run_status["status"]
        
        if status == "completed":
            break
        elif status == "requires_action":
            tool_outputs = []
            for tool_call in run_status["required_action"]["submit_tool_outputs"]["tool_calls"]:
                func_args = json.loads(tool_call["function"]["arguments"])
                operation = func_args.get("operation")
                params = {"organizationId": org_id}
                
                result = call_azure_function(operation, params)
                tool_outputs.append({
                    "tool_call_id": tool_call["id"],
                    "output": json.dumps(result)
                })
            
            submit_tool_outputs(thread_id, run_id, tool_outputs)
        elif status in ["failed", "cancelled", "expired"]:
            break
        
        time.sleep(1)
    
    # Get final response
    messages = get_messages(thread_id)
    for msg in reversed(messages):
        if msg["role"] == "assistant":
            print(f"\n🤖 Agent: {msg['content'][0]['text']['value']}")
            break
    
    # Verify in Cosmos DB
    print("\n" + "="*70)
    print("8️⃣ Verifying data in Cosmos DB...")
    
    from azure.cosmos import CosmosClient
    
    cosmos_connection = os.getenv("COSMOS_DB_CONNECTION_STRING")
    client = CosmosClient.from_connection_string(cosmos_connection)
    database = client.get_database_client("StratOSData")
    container = database.get_container_client("NorthStar")
    
    try:
        item = container.read_item(item=org_id, partition_key=org_id)
        print(f"\n✅ North Star data found in Cosmos DB!")
        print(f"   Organization ID: {item['organizationId']}")
        if item.get('purpose'):
            print(f"   Purpose: {item['purpose']['statement']}")
        if item.get('values'):
            print(f"   Values: {len(item['values'])} values defined")
            for value in item['values']:
                print(f"     - {value['name']}: {value['description']}")
    except Exception as e:
        print(f"❌ Failed to verify in Cosmos DB: {str(e)}")
    
    print("\n" + "="*70)
    print("✅ North Star Agent E2E test completed!")
    print(f"   Thread ID: {thread_id}")
    print(f"   Organization ID: {org_id}")
    print(f"   Test completed at: {datetime.now().isoformat()}")

if __name__ == "__main__":
    test_north_star_agent()