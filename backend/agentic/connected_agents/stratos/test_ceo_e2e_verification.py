#!/usr/bin/env python3
"""
End-to-end verification of CEO Log Agent -> Azure Function -> Cosmos DB flow
"""
import os
import sys
import json
import time
from datetime import datetime
from openai import AzureOpenAI
from azure.cosmos import CosmosClient
from dotenv import load_dotenv

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

# CEO Log Agent ID from deployment
CEO_LOG_AGENT_ID = "asst_JPnKjEMX4Z2KhiBTxpEQuLGm"

def verify_cosmos_before():
    """Check Cosmos DB before the test"""
    try:
        database = cosmos_client.get_database_client("StratOSData")
        container = database.get_container_client("CEOLogs")
        
        # Count existing items
        query = "SELECT VALUE COUNT(1) FROM c"
        items = list(container.query_items(query=query, enable_cross_partition_query=True))
        count_before = items[0] if items else 0
        
        print(f"✓ Connected to Cosmos DB")
        print(f"  Database: StratOSData")
        print(f"  Container: CEOLogs")
        print(f"  Items before test: {count_before}")
        
        return count_before
    except Exception as e:
        print(f"✗ Failed to connect to Cosmos DB: {e}")
        return None

def test_ceo_log_agent():
    """Test the CEO Log Agent with a save request"""
    print("\n2. Testing CEO Log Agent...")
    
    # Create a unique log entry
    timestamp = datetime.now().isoformat()
    log_content = f"E2E Test Log Entry - {timestamp}"
    
    try:
        # Create a thread
        thread = client.beta.threads.create()
        print(f"✓ Created thread: {thread.id}")
        
        # Add message to thread
        message = client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=f"Please save this CEO log entry: '{log_content}'. Category: Testing, Tags: e2e-test, verification"
        )
        print(f"✓ Added message to thread")
        
        # Run the thread with the CEO Log Agent
        run = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=CEO_LOG_AGENT_ID
        )
        print(f"✓ Started run: {run.id}")
        
        # Wait for completion
        print("  Waiting for agent response...")
        max_attempts = 30
        for i in range(max_attempts):
            run_status = client.beta.threads.runs.retrieve(
                thread_id=thread.id,
                run_id=run.id
            )
            
            if run_status.status == "completed":
                print(f"✓ Run completed successfully")
                break
            elif run_status.status == "failed":
                print(f"✗ Run failed: {run_status.last_error}")
                return None
            elif run_status.status == "requires_action":
                print(f"  Run requires action (function call)")
            
            time.sleep(2)
            print(f"  Status: {run_status.status} (attempt {i+1}/{max_attempts})")
        
        # Get the response
        messages = client.beta.threads.messages.list(thread_id=thread.id)
        for msg in messages.data:
            if msg.role == "assistant":
                print(f"\n✓ Agent response:")
                print(f"  {msg.content[0].text.value}")
                break
        
        return log_content
        
    except Exception as e:
        print(f"✗ Failed to test CEO Log Agent: {e}")
        return None

def verify_cosmos_after(log_content, count_before):
    """Verify the log was saved to Cosmos DB"""
    print("\n3. Verifying Cosmos DB after test...")
    
    try:
        database = cosmos_client.get_database_client("StratOSData")
        container = database.get_container_client("CEOLogs")
        
        # Count items after
        query = "SELECT VALUE COUNT(1) FROM c"
        items = list(container.query_items(query=query, enable_cross_partition_query=True))
        count_after = items[0] if items else 0
        
        print(f"✓ Items after test: {count_after}")
        print(f"  Items created: {count_after - count_before}")
        
        # Search for our specific log
        query = f"SELECT * FROM c WHERE CONTAINS(c.content, '{log_content}')"
        items = list(container.query_items(query=query, enable_cross_partition_query=True))
        
        if items:
            print(f"\n✓ FOUND THE LOG ENTRY IN COSMOS DB!")
            for item in items:
                print(f"  ID: {item.get('id')}")
                print(f"  Content: {item.get('content')}")
                print(f"  Category: {item.get('category')}")
                print(f"  Tags: {item.get('tags')}")
                print(f"  Created: {item.get('timestamp')}")
            return True
        else:
            print(f"\n✗ Log entry not found in Cosmos DB")
            # Show recent entries
            query = "SELECT TOP 5 * FROM c ORDER BY c.timestamp DESC"
            recent = list(container.query_items(query=query, enable_cross_partition_query=True))
            if recent:
                print("\nRecent entries:")
                for item in recent:
                    print(f"  - {item.get('timestamp')}: {item.get('content')[:50]}...")
            return False
            
    except Exception as e:
        print(f"✗ Failed to verify Cosmos DB: {e}")
        return False

def main():
    print("CEO Log Agent End-to-End Verification")
    print("=====================================")
    print("Testing: Agent -> Azure Function -> Cosmos DB")
    
    # Step 1: Check Cosmos DB before
    print("\n1. Checking Cosmos DB before test...")
    count_before = verify_cosmos_before()
    if count_before is None:
        print("Failed to connect to Cosmos DB")
        return
    
    # Step 2: Test the agent
    log_content = test_ceo_log_agent()
    if not log_content:
        print("Failed to test CEO Log Agent")
        return
    
    # Wait a bit for Azure Function to process
    print("\nWaiting 5 seconds for Azure Function to process...")
    time.sleep(5)
    
    # Step 3: Verify in Cosmos DB
    success = verify_cosmos_after(log_content, count_before)
    
    # Summary
    print("\n" + "="*50)
    if success:
        print("✅ END-TO-END VERIFICATION SUCCESSFUL!")
        print("   CEO Log Agent successfully called Azure Function")
        print("   Azure Function successfully created Cosmos DB record")
    else:
        print("❌ END-TO-END VERIFICATION FAILED")
        print("   Check Azure Function logs for errors")
        print("   Function URL: https://stratos-ceo-log-functions.azurewebsites.net")

if __name__ == "__main__":
    main()