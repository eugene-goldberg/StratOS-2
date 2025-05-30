#!/usr/bin/env python3
"""
Test North Star Agent with a new organization
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

# Function keys
FUNCTION_KEYS = {
    "ManagePurpose": "gPXyuj42jT_BnlDhImnO1gaV_xayICaGrxf2NoTA1_hVAzFuSjMcqQ==",
    "ManageVision": "hxaRNlD2FmGt9IHzHGXhtVavLrHvlDVkMtDfAe_j3cwyAzFuiAd75Q==",
    "ManageValues": "NliL5fD1aEmXoLSqoa1NSCzDbN2PEeSlCUYZAS6pxcc4AzFujGLDpw==",
    "ManageStrategicGoals": "kaS2TH5L7__RTKaLc8XfoxHDVW9AP8wE2p_Ei3lBQNvzAzFu4mIw4g==",
    "ValidateAlignment": "968fvYsjeBk7tEbv-0Bvt7RniJcynmitd_JR3Y-I5tHnAzFuZxFbwg==",
    "GetNorthStarSummary": "-W8ykJ6kkUyeLQCZXNklZqdoL1fOFhw1dvLQniJtqYvwAzFunTkKNA=="
}

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
    
    function_key = FUNCTION_KEYS.get(operation)
    if not function_key:
        return {"error": f"Unknown operation: {operation}"}
    
    url = f"https://stratos-north-star-functions.azurewebsites.net/api/{operation}"
    headers = {
        "x-functions-key": function_key,
        "Content-Type": "application/json"
    }
    
    print(f"\n📤 Calling Azure Function: {operation}")
    print(f"   Payload: {json.dumps(params, indent=2)}")
    
    try:
        response = requests.post(url, headers=headers, json=params, timeout=30)
        response.raise_for_status()
        result = response.json()
        print(f"📥 Response: Success!")
        return result
    except Exception as e:
        print(f"❌ Function call failed: {str(e)}")
        return {"error": str(e)}

def test_new_organization():
    """Test North Star Agent with a brand new organization"""
    print("🚀 Testing North Star Agent with New Organization")
    print("=" * 70)
    
    # Generate unique organization ID
    timestamp = int(datetime.now().timestamp())
    org_id = f"acme-corp-{timestamp}"
    print(f"\n📋 Creating new organization: {org_id}")
    
    # Create thread
    print("\n1️⃣ Creating conversation thread...")
    thread_id = create_thread()
    print(f"   ✅ Thread ID: {thread_id}")
    
    # Test 1: Set purpose for new organization
    print("\n2️⃣ Setting purpose for ACME Corporation")
    message = f"I'm the CEO of ACME Corporation. Set our purpose to: 'To deliver innovative solutions that transform how businesses operate in the digital age'"
    send_message(thread_id, message)
    
    run = create_run(thread_id)
    run_id = run["id"]
    print(f"   ✅ Run ID: {run_id}")
    
    # Process the run
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
                params["organizationId"] = org_id  # Use our new org ID
                
                result = call_azure_function(operation, params)
                tool_outputs.append({
                    "tool_call_id": tool_call["id"],
                    "output": json.dumps(result)
                })
            
            submit_tool_outputs(thread_id, run_id, tool_outputs)
        elif status in ["failed", "cancelled", "expired"]:
            break
        
        time.sleep(1)
    
    # Test 2: Set vision
    print("\n3️⃣ Setting vision for ACME Corporation")
    message = "Set our vision to: 'To be recognized as the most trusted technology partner for enterprise transformation by 2030'"
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
    
    # Test 3: Add values
    print("\n4️⃣ Adding core values for ACME Corporation")
    message = "Add our core values: Excellence (Strive for the highest quality), Partnership (Build lasting relationships), and Agility (Adapt quickly to change)"
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
    
    # Test 4: Create strategic goal
    print("\n5️⃣ Creating strategic goal for ACME Corporation")
    message = "Create a strategic goal: 'Achieve $100M in annual revenue' with target date December 2026"
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
    
    # Get final summary
    print("\n6️⃣ Getting North Star summary")
    message = "Show me ACME Corporation's complete North Star foundation"
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
            print(f"\n🤖 Agent Response:")
            print(msg['content'][0]['text']['value'])
            break
    
    # Verify in Cosmos DB
    print("\n" + "="*70)
    print("7️⃣ Verifying new organization in Cosmos DB...")
    
    from azure.cosmos import CosmosClient
    
    cosmos_connection = os.getenv("COSMOS_DB_CONNECTION_STRING")
    client = CosmosClient.from_connection_string(cosmos_connection)
    database = client.get_database_client("StratOSData")
    container = database.get_container_client("NorthStar")
    
    # Query all items to show we have multiple organizations
    print("\n📊 All organizations in NorthStar container:")
    query = "SELECT c.id, c.organizationId FROM c"
    items = list(container.query_items(query=query, enable_cross_partition_query=True))
    for item in items:
        print(f"   - {item['organizationId']}")
    
    # Get our new organization
    try:
        item = container.read_item(item=org_id, partition_key=org_id)
        print(f"\n✅ New organization verified in Cosmos DB!")
        print(f"   Organization ID: {item['organizationId']}")
        if item.get('purpose'):
            print(f"   Purpose: {item['purpose']['statement']}")
        if item.get('vision'):
            print(f"   Vision: {item['vision']['statement']}")
        if item.get('values'):
            print(f"   Values: {len(item['values'])} values")
            for value in item['values']:
                print(f"     - {value['name']}: {value['description']}")
        if item.get('strategicGoals'):
            print(f"   Goals: {len(item['strategicGoals'])} goals")
    except Exception as e:
        print(f"❌ Failed to verify in Cosmos DB: {str(e)}")
    
    print("\n" + "="*70)
    print("✅ New organization test completed!")
    print(f"   Organization: ACME Corporation ({org_id})")
    print(f"   Thread ID: {thread_id}")
    print(f"   Total organizations in Cosmos DB: {len(items)}")

if __name__ == "__main__":
    test_new_organization()