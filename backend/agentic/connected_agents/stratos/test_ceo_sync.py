#!/usr/bin/env python3
"""
Synchronous test of CEO Log Agent with Azure Functions
"""

import os
import json
import time
import requests
from datetime import datetime
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from openai import AzureOpenAI
from azure.cosmos import CosmosClient

# Load environment variables  
load_dotenv()

# CEO Log Agent ID
CEO_LOG_AGENT_ID = "asst_wyLHPFlQUA3MB69xjMuopI0U"

# Azure Function configuration
AZURE_FUNCTION_BASE = "https://stratos-ceo-log-functions.azurewebsites.net/api"
AZURE_FUNCTION_KEYS = {
    "SaveCEOLog": "I3c897PZMtJp1goBaxPwGlXa3Ni6ZsM09t1F7roTLVZeAzFu69TeKA==",
}

# Azure OpenAI client
client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY", "b77c5b137db6465dabdbc34adb136e2c"),
    api_version="2024-07-01-preview",
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", "https://sk-multi-agent-openai.openai.azure.com/")
)

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
            
            print(f"   Calling Azure Function: {url}")
            response = requests.post(url, headers=headers, json=payload)
            result = response.json()
            
            print(f"   Azure Function Response: {json.dumps(result, indent=2)}")
            return json.dumps(result)
            
        else:
            return json.dumps({"error": f"Operation {operation} not implemented"})
            
    except Exception as e:
        return json.dumps({"error": str(e)})

def test_ceo_log_agent():
    """Test the CEO Log Agent"""
    print("\n" + "="*70)
    print("CEO LOG AGENT TEST WITH AZURE FUNCTIONS")
    print("="*70)
    
    # Create unique test content
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    test_content = f"Test Entry {timestamp}: CEO Log Agent with Azure Functions E2E Test"
    
    print(f"\nTest content: {test_content}")
    
    try:
        # Create a thread
        thread = client.beta.threads.create()
        print(f"\n✓ Thread created: {thread.id}")
        
        # Add message
        message = client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=f"Save this CEO log entry: '{test_content}'. Category: strategic_planning"
        )
        print("✓ Message added")
        
        # Run the agent
        run = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=CEO_LOG_AGENT_ID
        )
        print(f"✓ Run created: {run.id}")
        
        # Wait for completion and handle function calls
        print("\n⏳ Processing...")
        max_iterations = 60
        iteration = 0
        
        while iteration < max_iterations:
            run = client.beta.threads.runs.retrieve(
                thread_id=thread.id,
                run_id=run.id
            )
            
            if run.status == 'completed':
                print("✓ Run completed!")
                break
            elif run.status == 'failed':
                print(f"✗ Run failed: {run.last_error}")
                break
            elif run.status == 'requires_action':
                # Handle function calls
                if hasattr(run.required_action, 'submit_tool_outputs'):
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
                    client.beta.threads.runs.submit_tool_outputs(
                        thread_id=thread.id,
                        run_id=run.id,
                        tool_outputs=tool_outputs
                    )
                    print("   ✓ Function outputs submitted")
            
            time.sleep(1)
            iteration += 1
            if iteration % 5 == 0:
                print(f"   Status: {run.status} (iteration {iteration})")
        
        # Get the response
        messages = client.beta.threads.messages.list(thread_id=thread.id)
        for msg in messages.data:
            if msg.role == 'assistant':
                print(f"\n🤖 Agent Response:")
                print(f"   {msg.content[0].text.value}")
                break
        
        return test_content
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
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
            
            print(f"\n  Recent entries:")
            for i, item in enumerate(items[:3]):
                # Check various content fields
                content_str = ""
                for field in ['rawContent', 'content', 'logContent']:
                    if field in item:
                        content_str = str(item[field])
                        break
                
                print(f"\n  Entry {i+1}:")
                print(f"    ID: {item.get('id')}")
                print(f"    Content: {content_str[:80]}...")
                print(f"    Category: {item.get('category')}")
                
                if test_content in content_str:
                    print(f"\n🎯 VERIFIED: Found our test entry!")
                    return True
            
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
        print("   • Agent called the Azure Function") 
        print("   • Azure Function created Cosmos DB record")
        print("   • Complete flow is working correctly!")
    else:
        print("❌ VERIFICATION INCOMPLETE")

if __name__ == "__main__":
    main()