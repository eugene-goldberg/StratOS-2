#!/usr/bin/env python3
"""
Simple test using create_thread_and_run
"""

import os
import time
from datetime import datetime
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.cosmos import CosmosClient

# Load environment variables
load_dotenv()

# Configuration
CEO_LOG_AGENT_ID = "asst_85MtpKLDOQA9ttsUckByGTKD"
COSMOS_ENDPOINT = "https://stratos-ceo-logs-db.documents.azure.com:443/"
COSMOS_KEY = "VAThFP4W5W47q1UK3QHrEw0YuPiHkdFkupVtBItd3PgOiuxlM6F4SqurWmwzN3KjZIUWuDBb5RizACDbZPOSzw=="
COSMOS_DATABASE = "StratOSData"
COSMOS_CONTAINER = "CEOLogs"

def test_ceo_log():
    print("\nCEO LOG AGENT TEST - SIMPLE")
    print("="*60)
    
    # Check Cosmos DB
    try:
        client = CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)
        database = client.get_database_client(COSMOS_DATABASE)
        container = database.get_container_client(COSMOS_CONTAINER)
        
        query = "SELECT VALUE COUNT(1) FROM c"
        items = list(container.query_items(query=query, enable_cross_partition_query=True))
        initial_count = items[0] if items else 0
        print(f"Initial Cosmos DB record count: {initial_count}")
    except Exception as e:
        print(f"Cosmos DB error: {e}")
        return
    
    # Connect to Azure AI
    endpoint = os.getenv("AZURE_AI_PROJECT_CONNECTION_STRING")
    credential = DefaultAzureCredential()
    client = AIProjectClient(endpoint=endpoint, credential=credential)
    
    # Test message
    test_id = f"simple_test_{int(time.time())}"
    message = f"""Save this CEO log entry:

Board meeting success! 30% AI budget increase approved.
Test ID: {test_id}
Category: strategic_planning
User ID: ceo_test_001"""
    
    print(f"\nSending: {message}")
    
    try:
        # Create thread and run
        run = client.agents.create_thread_and_run(
            agent_id=CEO_LOG_AGENT_ID,
            thread={
                "messages": [
                    {
                        "role": "user",
                        "content": message
                    }
                ]
            }
        )
        
        print(f"Run ID: {run.id}")
        print(f"Thread ID: {run.thread_id}")
        print(f"Status: {run.status}")
        
        # Wait for completion (simplified - no status updates)
        start = time.time()
        time.sleep(10)  # Just wait 10 seconds
        
        print(f"\nChecking messages after {time.time()-start:.1f}s...")
        
        # Get messages
        messages = client.agents.list_messages(thread_id=run.thread_id)
        
        print("\nAgent Response:")
        print("-"*60)
        for msg in messages.data:
            if msg.role == "assistant":
                for content in msg.content:
                    if hasattr(content, 'text') and content.text:
                        print(content.text.value)
        print("-"*60)
        
        # Check Cosmos DB
        print("\nChecking Cosmos DB...")
        time.sleep(5)
        
        # Check for new records
        query = f"SELECT * FROM c WHERE CONTAINS(c.content, '{test_id}')"
        new_records = list(container.query_items(query=query, enable_cross_partition_query=True))
        
        if new_records:
            print(f"✓ Found record with test ID!")
            record = new_records[0]
            print(f"  ID: {record.get('id')}")
            print(f"  Content: {record.get('content', '')[:100]}...")
        else:
            # Check total count
            query = "SELECT VALUE COUNT(1) FROM c"
            items = list(container.query_items(query=query, enable_cross_partition_query=True))
            final_count = items[0] if items else 0
            
            if final_count > initial_count:
                print(f"✓ New records created! Count: {initial_count} → {final_count}")
            else:
                print(f"✗ No new records. Count: {initial_count}")
                
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_ceo_log()