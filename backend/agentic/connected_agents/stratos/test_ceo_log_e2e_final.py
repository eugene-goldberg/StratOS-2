#!/usr/bin/env python3
"""
End-to-end test for CEO Log Agent with Azure Function and Cosmos DB verification
"""

import os
import asyncio
import json
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
COSMOS_ENDPOINT = os.getenv("COSMOS_ENDPOINT", "https://stratos-ceo-logs-db.documents.azure.com:443/")
COSMOS_KEY = os.getenv("COSMOS_KEY", "VAThFP4W5W47q1UK3QHrEw0YuPiHkdFkupVtBItd3PgOiuxlM6F4SqurWmwzN3KjZIUWuDBb5RizACDbZPOSzw==")
COSMOS_DATABASE = "StratOSData"  # Correct database name from Azure
COSMOS_CONTAINER = "CEOLogs"     # Correct container name from Azure

def check_cosmos_db():
    """Check Cosmos DB connection and get initial record count"""
    try:
        cosmos_client = CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)
        database = cosmos_client.get_database_client(COSMOS_DATABASE)
        container = database.get_container_client(COSMOS_CONTAINER)
        
        # Query to count records
        query = "SELECT VALUE COUNT(1) FROM c"
        items = list(container.query_items(query=query, enable_cross_partition_query=True))
        initial_count = items[0] if items else 0
        
        print(f"✓ Connected to Cosmos DB")
        print(f"  Database: {COSMOS_DATABASE}")
        print(f"  Container: {COSMOS_CONTAINER}")
        print(f"  Initial record count: {initial_count}")
        
        return container, initial_count
    except Exception as e:
        print(f"✗ Cosmos DB connection failed: {e}")
        return None, 0

def test_ceo_log_agent():
    """Test CEO Log Agent synchronously"""
    print("\n" + "="*70)
    print("CEO LOG AGENT END-TO-END TEST")
    print("="*70)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Agent ID: {CEO_LOG_AGENT_ID}")
    
    # Check Cosmos DB first
    container, initial_count = check_cosmos_db()
    if not container:
        print("Cannot proceed without Cosmos DB connection")
        return
    
    # Connect to Azure AI Project
    endpoint = os.getenv("AZURE_AI_PROJECT_CONNECTION_STRING")
    if not endpoint:
        print("✗ AZURE_AI_PROJECT_CONNECTION_STRING not set")
        return
    
    credential = DefaultAzureCredential()
    client = AIProjectClient(endpoint=endpoint, credential=credential)
    
    try:
        # Verify agent exists
        print(f"\n1. Verifying agent deployment...")
        agent = client.agents.get_agent(CEO_LOG_AGENT_ID)
        print(f"✓ Agent found: {agent.name}")
        print(f"  Model: {agent.model}")
        print(f"  Tools: {len(agent.tools) if agent.tools else 0}")
        
        # Create thread
        print(f"\n2. Creating conversation thread...")
        thread = client.agents.threads.create()
        print(f"✓ Thread created: {thread.id}")
        
        # Prepare CEO log entry with unique identifier
        test_id = f"test_{int(time.time())}"
        log_entry = f"""Save this CEO log entry:

Today's board meeting was exceptional. Key decisions made:
1. Approved 30% increase in AI R&D budget for Q2
2. Green light for European market expansion
3. New strategic partnership with TechCorp confirmed

Team morale is at an all-time high after exceeding Q1 targets by 20%.

Test ID: {test_id}
Category: strategic_planning  
User ID: ceo_test_user_001"""
        
        print(f"\n3. Sending CEO log entry...")
        print("-" * 70)
        print(log_entry)
        print("-" * 70)
        
        # Add message
        message = client.agents.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=log_entry
        )
        
        # Create run
        print(f"\n4. Executing agent...")
        run = client.agents.threads.runs.create(
            thread_id=thread.id,
            assistant_id=CEO_LOG_AGENT_ID
        )
        
        # Monitor run status
        start_time = time.time()
        last_status = None
        
        while run.status in ["queued", "in_progress", "requires_action"]:
            if run.status != last_status:
                print(f"   Status: {run.status}")
                last_status = run.status
            
            time.sleep(1)
            run = client.agents.threads.runs.get(thread_id=thread.id, run_id=run.id)
            
            if time.time() - start_time > 60:
                print("✗ Timeout after 60 seconds")
                break
        
        print(f"   Final status: {run.status}")
        print(f"   Duration: {time.time() - start_time:.1f} seconds")
        
        # Get agent response
        if run.status == "completed":
            print(f"\n5. Agent response:")
            print("-" * 70)
            
            messages = client.agents.threads.messages.list(thread_id=thread.id)
            for msg in messages.data:
                if msg.role == "assistant":
                    for content in msg.content:
                        if hasattr(content, 'text') and content.text:
                            print(content.text.value)
                    break
            
            print("-" * 70)
            
            # Wait for Azure Function to process
            print(f"\n6. Waiting for Azure Function processing...")
            time.sleep(5)
            
            # Verify Cosmos DB record
            print(f"\n7. Verifying Cosmos DB record creation...")
            
            # Query for new records
            query = f"SELECT * FROM c WHERE CONTAINS(c.content, '{test_id}') OR CONTAINS(c.id, '{test_id}')"
            new_records = list(container.query_items(
                query=query,
                enable_cross_partition_query=True
            ))
            
            if new_records:
                print(f"✓ Found {len(new_records)} new record(s) with test ID!")
                for record in new_records:
                    print(f"\n  Record ID: {record.get('id')}")
                    print(f"  User ID: {record.get('userId')}")
                    print(f"  Category: {record.get('category')}")
                    print(f"  Content preview: {record.get('content', '')[:100]}...")
                    print(f"  Tags: {record.get('tags', [])}")
                    print(f"  Created: {record.get('createdAt')}")
            else:
                # Check total count
                query = "SELECT VALUE COUNT(1) FROM c"
                items = list(container.query_items(query=query, enable_cross_partition_query=True))
                final_count = items[0] if items else 0
                
                if final_count > initial_count:
                    print(f"✓ New records created! Count increased from {initial_count} to {final_count}")
                    
                    # Get latest record
                    query = "SELECT TOP 1 * FROM c ORDER BY c._ts DESC"
                    latest = list(container.query_items(
                        query=query,
                        enable_cross_partition_query=True
                    ))
                    
                    if latest:
                        record = latest[0]
                        print(f"\n  Latest record:")
                        print(f"  ID: {record.get('id')}")
                        print(f"  Content: {record.get('content', '')[:200]}...")
                else:
                    print(f"✗ No new records found. Count remains at {initial_count}")
            
            print(f"\n" + "="*70)
            print("✓ END-TO-END TEST COMPLETE")
            print("="*70)
            
        else:
            print(f"\n✗ Agent run failed with status: {run.status}")
            if hasattr(run, 'last_error'):
                print(f"Error: {run.last_error}")
                
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_ceo_log_agent()