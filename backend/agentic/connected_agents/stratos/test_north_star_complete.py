#!/usr/bin/env python3
"""
Complete North Star Agent Test - Testing all functionality
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
    
    function_key = FUNCTION_KEYS.get(operation)
    if not function_key:
        return {"error": f"Unknown operation: {operation}"}
    
    url = f"https://stratos-north-star-functions.azurewebsites.net/api/{operation}"
    headers = {
        "x-functions-key": function_key,
        "Content-Type": "application/json"
    }
    
    # Prepare payload
    payload = params.copy()
    
    print(f"\n📤 Calling Azure Function: {operation}")
    print(f"   Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        result = response.json()
        print(f"📥 Response: {json.dumps(result, indent=2)}")
        return result
    except Exception as e:
        print(f"❌ Function call failed: {str(e)}")
        return {"error": str(e)}

def process_run_to_completion(thread_id, run_id, org_id):
    """Process a run until completion, handling function calls"""
    while True:
        run_status = get_run_status(thread_id, run_id)
        status = run_status["status"]
        
        if status == "completed":
            return True
        elif status == "requires_action":
            tool_outputs = []
            
            for tool_call in run_status["required_action"]["submit_tool_outputs"]["tool_calls"]:
                func_name = tool_call["function"]["name"]
                func_args = json.loads(tool_call["function"]["arguments"])
                
                if func_name == "call_north_star_function":
                    operation = func_args.get("operation")
                    params = {k: v for k, v in func_args.items() if k != "operation"}
                    params["organizationId"] = org_id  # Ensure org ID
                    
                    result = call_azure_function(operation, params)
                else:
                    result = {"error": f"Unknown function: {func_name}"}
                
                tool_outputs.append({
                    "tool_call_id": tool_call["id"],
                    "output": json.dumps(result)
                })
            
            submit_tool_outputs(thread_id, run_id, tool_outputs)
            
        elif status in ["failed", "cancelled", "expired"]:
            print(f"❌ Run failed with status: {status}")
            return False
        
        time.sleep(1)

def get_latest_assistant_message(thread_id):
    """Get the latest assistant message"""
    messages = get_messages(thread_id)
    for msg in messages:
        if msg["role"] == "assistant":
            return msg['content'][0]['text']['value']
    return None

def test_complete_north_star_flow():
    """Test all North Star Agent functionality"""
    print("🚀 Complete North Star Agent Test")
    print("=" * 70)
    
    # Test with a different organization
    org_id = f"test-org-{int(datetime.now().timestamp())}"
    print(f"\n📋 Testing with Organization ID: {org_id}")
    
    # Create thread
    print("\n1️⃣ Creating conversation thread...")
    thread_id = create_thread()
    print(f"   ✅ Thread ID: {thread_id}")
    
    # Test 1: Set Vision
    print("\n2️⃣ Testing: Set organizational vision")
    message = "Set our vision to: 'To become the global leader in AI-powered strategic planning by 2030'"
    send_message(thread_id, message)
    run = create_run(thread_id)
    
    if process_run_to_completion(thread_id, run["id"], org_id):
        response = get_latest_assistant_message(thread_id)
        print(f"\n🤖 Agent: {response}")
    
    # Test 2: Create Strategic Goals
    print("\n3️⃣ Testing: Create strategic goals")
    message = "Create a strategic goal: 'Expand to 10 new markets' with target date December 2025"
    send_message(thread_id, message)
    run = create_run(thread_id)
    
    if process_run_to_completion(thread_id, run["id"], org_id):
        response = get_latest_assistant_message(thread_id)
        print(f"\n🤖 Agent: {response}")
    
    # Test 3: Create child goal
    print("\n4️⃣ Testing: Create hierarchical goals")
    message = "Create a sub-goal under the market expansion goal: 'Launch in European markets' with target date June 2025"
    send_message(thread_id, message)
    run = create_run(thread_id)
    
    if process_run_to_completion(thread_id, run["id"], org_id):
        response = get_latest_assistant_message(thread_id)
        print(f"\n🤖 Agent: {response}")
    
    # Test 4: Validate Alignment
    print("\n5️⃣ Testing: Validate alignment")
    message = "Is launching a premium AI analytics product aligned with our North Star?"
    send_message(thread_id, message)
    run = create_run(thread_id)
    
    if process_run_to_completion(thread_id, run["id"], org_id):
        response = get_latest_assistant_message(thread_id)
        print(f"\n🤖 Agent: {response}")
    
    # Test 5: Get Complete Summary
    print("\n6️⃣ Testing: Get complete North Star summary")
    message = "Show me our complete strategic foundation"
    send_message(thread_id, message)
    run = create_run(thread_id)
    
    if process_run_to_completion(thread_id, run["id"], org_id):
        response = get_latest_assistant_message(thread_id)
        print(f"\n🤖 Agent: {response}")
    
    # Verify in Cosmos DB
    print("\n" + "="*70)
    print("7️⃣ Verifying complete data in Cosmos DB...")
    
    from azure.cosmos import CosmosClient
    
    cosmos_connection = os.getenv("COSMOS_DB_CONNECTION_STRING")
    client = CosmosClient.from_connection_string(cosmos_connection)
    database = client.get_database_client("StratOSData")
    container = database.get_container_client("NorthStar")
    
    try:
        item = container.read_item(item=org_id, partition_key=org_id)
        print(f"\n✅ Complete North Star data verified in Cosmos DB!")
        print(f"   Organization ID: {item['organizationId']}")
        
        if item.get('purpose'):
            print(f"   Purpose: Not set in this test")
        
        if item.get('vision'):
            print(f"   Vision: {item['vision']['statement']}")
            
        if item.get('values'):
            print(f"   Values: {len(item['values'])} values")
            
        if item.get('strategicGoals'):
            print(f"   Strategic Goals: {len(item['strategicGoals'])} goals")
            for goal_id, goal in item['strategicGoals'].items():
                indent = "     " if not goal.get('parent_id') else "       "
                print(f"{indent}- {goal['name']} (Target: {goal.get('target_date', 'Not set')})")
                
        # Calculate completeness
        completeness = sum([
            bool(item.get('purpose')),
            bool(item.get('vision')),
            bool(item.get('values')),
            bool(item.get('strategicGoals'))
        ])
        print(f"\n   Completeness: {completeness}/4 elements defined ({completeness*25}%)")
        
    except Exception as e:
        print(f"❌ Failed to verify in Cosmos DB: {str(e)}")
    
    print("\n" + "="*70)
    print("✅ Complete North Star Agent test finished!")
    print(f"   Thread ID: {thread_id}")
    print(f"   Organization ID: {org_id}")
    print(f"   Test completed at: {datetime.now().isoformat()}")
    
    return org_id

if __name__ == "__main__":
    test_complete_north_star_flow()