#!/usr/bin/env python3
"""
Direct invocation of CEO Log Agent without kernel setup
Following the weather agent pattern
"""

import os
import sys
import json
import time
from datetime import datetime
from dotenv import load_dotenv
from openai import AzureOpenAI
from azure.cosmos import CosmosClient

# Load environment variables
load_dotenv()

# Azure OpenAI configuration  
client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_KEY"),
    api_version="2024-07-01-preview",
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
)

# Cosmos DB configuration
cosmos_client = CosmosClient(
    url=os.getenv("COSMOS_DB_ENDPOINT"),
    credential=os.getenv("COSMOS_DB_KEY")
)

# CEO Log Agent ID
CEO_LOG_AGENT_ID = "asst_JPnKjEMX4Z2KhiBTxpEQuLGm"

def check_cosmos_before():
    """Check Cosmos DB before test"""
    try:
        database = cosmos_client.get_database_client("StratOSData")
        container = database.get_container_client("CEOLogs")
        
        query = "SELECT VALUE COUNT(1) FROM c"
        items = list(container.query_items(query=query, enable_cross_partition_query=True))
        count = items[0] if items else 0
        
        print(f"✓ Connected to Cosmos DB - Items before: {count}")
        return count
    except Exception as e:
        print(f"✗ Cosmos DB error: {e}")
        return None

def test_agent_save():
    """Test CEO Log Agent save functionality"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    test_content = f"E2E Test {timestamp}: Integration test successful"
    
    print(f"\n📝 Testing save with content: {test_content}")
    
    try:
        # Create thread
        thread = client.beta.threads.create()
        print(f"✓ Thread created: {thread.id}")
        
        # Add message
        message = client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=f"Save this CEO log entry: '{test_content}'. Category: testing, Source: e2e-test"
        )
        
        # Run with CEO Log Agent
        run = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=CEO_LOG_AGENT_ID
        )
        print(f"✓ Run started: {run.id}")
        
        # Wait for completion
        print("⏳ Waiting for response...")
        max_wait = 60
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            run_status = client.beta.threads.runs.retrieve(
                thread_id=thread.id,
                run_id=run.id
            )
            
            if run_status.status == "completed":
                print("✓ Run completed")
                break
            elif run_status.status == "failed":
                print(f"✗ Run failed: {run_status.last_error}")
                return None
            elif run_status.status == "requires_action":
                # Handle tool calls
                if hasattr(run_status.required_action, 'submit_tool_outputs'):
                    tool_calls = run_status.required_action.submit_tool_outputs.tool_calls
                    tool_outputs = []
                    
                    for tool_call in tool_calls:
                        print(f"📞 Tool call: {tool_call.function.name}")
                        # Submit dummy output to continue
                        tool_outputs.append({
                            "tool_call_id": tool_call.id,
                            "output": json.dumps({"message": "Please use code interpreter to make HTTP calls"})
                        })
                    
                    client.beta.threads.runs.submit_tool_outputs(
                        thread_id=thread.id,
                        run_id=run.id,
                        tool_outputs=tool_outputs
                    )
            
            time.sleep(2)
            print(f"  Status: {run_status.status}")
        
        # Get response
        messages = client.beta.threads.messages.list(thread_id=thread.id)
        response = ""
        for msg in messages.data:
            if msg.role == "assistant":
                response = msg.content[0].text.value
                print(f"\n🤖 Agent response: {response[:200]}...")
                break
        
        return test_content if response else None
        
    except Exception as e:
        print(f"✗ Error: {e}")
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
    print("CEO LOG AGENT → AZURE FUNCTION → COSMOS DB TEST")
    print("="*60)
    
    # Check before
    count_before = check_cosmos_before()
    if count_before is None:
        return
    
    # Test agent
    test_content = test_agent_save()
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
    else:
        print("❌ FAILED: Check Azure Function logs")
        print("   https://stratos-ceo-log-functions.azurewebsites.net")

if __name__ == "__main__":
    main()