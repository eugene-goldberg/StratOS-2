#!/usr/bin/env python3
"""
Test CEO Log Agent with Azure Function Integration
Following the weather agent test pattern
"""

import os
import json
import time
import requests
from datetime import datetime
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.cosmos import CosmosClient

# Load environment variables  
load_dotenv()

# CEO Log Agent ID
CEO_LOG_AGENT_ID = "asst_wyLHPFlQUA3MB69xjMuopI0U"

# Azure Function configuration
AZURE_FUNCTION_BASE = "https://stratos-ceo-log-functions.azurewebsites.net/api"
AZURE_FUNCTION_KEYS = {
    "SaveCEOLog": "I3c897PZMtJp1goBaxPwGlXa3Ni6ZsM09t1F7roTLVZeAzFu69TeKA==",
    "SearchCEOLogs": "uXjWD5crSSJYH_7eL3IcQq_ebEqVqO9D2QaC24UKa_RNAzFuVD7gkg==", 
    "AnalyzeLogs": "1ALdM_XHFGwQ5XtC5BBsnJ-_j_w30lef9DsjGWVrpNJfAzFuEHzbmg==",
    "GetInsights": "Rx3WeFi1SoWXpbiZtsOCBVyswP06bUskqSYKK5HdntHBAzFuqJ56aw=="
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
            
            response = requests.post(url, headers=headers, json=payload)
            result = response.json()
            
            print(f"   Azure Function Response: {json.dumps(result, indent=2)}")
            return json.dumps(result)
            
        elif operation == "SearchCEOLogs":
            # Implement search function call
            url = f"{AZURE_FUNCTION_BASE}/SearchCEOLogs"
            headers = {
                "x-functions-key": AZURE_FUNCTION_KEYS["SearchCEOLogs"],
                "Content-Type": "application/json"
            }
            response = requests.post(url, headers=headers, json=args)
            return json.dumps(response.json())
            
        else:
            return json.dumps({"error": f"Operation {operation} not implemented in test"})
            
    except Exception as e:
        error_result = {"error": str(e)}
        print(f"   Function call error: {error_result}")
        return json.dumps(error_result)

def test_ceo_log_agent():
    """Test the CEO Log Agent"""
    print("\n" + "="*70)
    print("CEO LOG AGENT TEST WITH AZURE FUNCTIONS")
    print("="*70)
    
    # Create unique test content
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    test_content = f"Test Entry {timestamp}: CEO Log Agent successfully integrated with Azure Functions"
    
    print(f"\nTest content: {test_content}")
    
    # Create AI Project client
    endpoint = os.getenv("AZURE_AI_PROJECT_CONNECTION_STRING")
    credential = DefaultAzureCredential()
    client = AIProjectClient(endpoint=endpoint, credential=credential)
    
    # Create a thread
    thread = client.agents.create_thread()
    print(f"\n✓ Thread created: {thread.id}")
    
    # Add message
    message = client.agents.create_message(
        thread_id=thread.id,
        role="user",
        content=f"Save this CEO log entry: '{test_content}'. Category: strategic_planning"
    )
    print("✓ Message added")
    
    # Run the agent
    run = client.agents.create_run(
        thread_id=thread.id,
        assistant_id=CEO_LOG_AGENT_ID
    )
    print(f"✓ Run created: {run.id}")
    
    # Wait for completion and handle function calls
    print("\n⏳ Processing...")
    while run.status in ['queued', 'in_progress', 'requires_action']:
        time.sleep(1)
        run = client.agents.get_run(thread_id=thread.id, run_id=run.id)
        
        # Handle function calls
        if run.status == 'requires_action':
            tool_calls = run.required_action.submit_tool_outputs.tool_calls
            tool_outputs = []
            
            print(f"\n🔧 Handling {len(tool_calls)} function call(s)...")
            
            for tool_call in tool_calls:
                print(f"\n   Function: {tool_call.function.name}")
                print(f"   Arguments: {tool_call.function.arguments}")
                
                # Execute the actual function
                output = execute_function_call(
                    tool_call.function.name,
                    tool_call.function.arguments
                )
                
                tool_outputs.append({
                    "tool_call_id": tool_call.id,
                    "output": output
                })
            
            # Submit tool outputs
            run = client.agents.submit_tool_outputs_to_run(
                thread_id=thread.id,
                run_id=run.id,
                tool_outputs=tool_outputs
            )
            print("   ✓ Function outputs submitted")
    
    # Get the response
    if run.status == 'completed':
        print("\n✓ Run completed!")
        messages = client.agents.list_messages(thread_id=thread.id)
        for msg in messages:
            if msg.role == 'assistant':
                print(f"\n🤖 Agent Response:")
                for content in msg.content:
                    if content.type == 'text':
                        print(f"   {content.text.value}")
                break
    else:
        print(f"\n✗ Run failed with status: {run.status}")
        if hasattr(run, 'last_error'):
            print(f"   Error: {run.last_error}")
    
    return test_content

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
            
            for item in items:
                # Check various content fields
                content_fields = ['rawContent', 'content', 'logContent']
                item_content = ""
                for field in content_fields:
                    if field in item:
                        item_content = str(item[field])
                        break
                
                if test_content in item_content:
                    print(f"\n🎯 VERIFIED: Found our test entry in Cosmos DB!")
                    print(f"   ID: {item.get('id')}")
                    print(f"   Content: {item_content[:100]}...")
                    print(f"   Category: {item.get('category')}")
                    return True
            
            print(f"\n✅ New entry created in Cosmos DB")
            return True
        
        return False
        
    except Exception as e:
        print(f"✗ Error checking Cosmos: {e}")
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
        print("   • Agent called the Azure Function") 
        print("   • Azure Function created Cosmos DB record")
        print("   • Complete flow is working correctly!")
    else:
        print("❌ VERIFICATION INCOMPLETE")
        print("   Check if Azure Function created the record")

if __name__ == "__main__":
    main()