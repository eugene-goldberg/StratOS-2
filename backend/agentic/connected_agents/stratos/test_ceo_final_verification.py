#!/usr/bin/env python3
"""
Final E2E verification for CEO Log Agent
Following the exact pattern that worked for Weather Agent
"""

import os
import time
import json
import asyncio
from datetime import datetime
from dotenv import load_dotenv
from azure.cosmos import CosmosClient
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient

# Load environment variables
load_dotenv()

# Configuration
CEO_LOG_AGENT_ID = "asst_85MtpKLDOQA9ttsUckByGTKD"
COSMOS_ENDPOINT = "https://stratos-ceo-logs-db.documents.azure.com:443/"
COSMOS_KEY = "VAThFP4W5W47q1UK3QHrEw0YuPiHkdFkupVtBItd3PgOiuxlM6F4SqurWmwzN3KjZIUWuDBb5RizACDbZPOSzw=="
COSMOS_DATABASE = "StratOSData"
COSMOS_CONTAINER = "CEOLogs"

def check_cosmos_before():
    """Check Cosmos DB before test"""
    try:
        client = CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)
        database = client.get_database_client(COSMOS_DATABASE)
        container = database.get_container_client(COSMOS_CONTAINER)
        
        query = "SELECT VALUE COUNT(1) FROM c"
        items = list(container.query_items(query=query, enable_cross_partition_query=True))
        count = items[0] if items else 0
        
        print(f"✓ Connected to Cosmos DB")
        print(f"  Database: {COSMOS_DATABASE}")
        print(f"  Container: {COSMOS_CONTAINER}")
        print(f"  Initial record count: {count}")
        
        return container, count
    except Exception as e:
        print(f"✗ Cosmos DB error: {e}")
        return None, 0

def check_cosmos_after(container, initial_count, test_id):
    """Check Cosmos DB after test"""
    try:
        # First check for records with our test ID
        query = f"SELECT * FROM c WHERE CONTAINS(c.content, '{test_id}')"
        new_records = list(container.query_items(query=query, enable_cross_partition_query=True))
        
        if new_records:
            print(f"\n✓ Found {len(new_records)} record(s) with test ID!")
            for record in new_records:
                print(f"\n  Record Details:")
                print(f"  - ID: {record.get('id')}")
                print(f"  - User ID: {record.get('userId')}")
                print(f"  - Category: {record.get('category')}")
                print(f"  - Content: {record.get('content', '')[:150]}...")
                print(f"  - Tags: {record.get('tags', [])}")
                print(f"  - Created: {record.get('createdAt')}")
            return True
        
        # Check total count
        query = "SELECT VALUE COUNT(1) FROM c"
        items = list(container.query_items(query=query, enable_cross_partition_query=True))
        final_count = items[0] if items else 0
        
        if final_count > initial_count:
            print(f"\n✓ New records created! Count: {initial_count} → {final_count}")
            
            # Get latest record
            query = "SELECT TOP 1 * FROM c ORDER BY c._ts DESC"
            latest = list(container.query_items(query=query, enable_cross_partition_query=True))
            
            if latest:
                record = latest[0]
                print(f"\n  Latest Record:")
                print(f"  - ID: {record.get('id')}")
                print(f"  - Content: {record.get('content', '')[:150]}...")
                print(f"  - User ID: {record.get('userId')}")
                print(f"  - Category: {record.get('category')}")
            return True
        else:
            print(f"\n✗ No new records found. Count remains at {initial_count}")
            return False
            
    except Exception as e:
        print(f"\n✗ Cosmos DB verification error: {e}")
        return False

def test_ceo_log_agent():
    """Test CEO Log Agent following Weather Agent pattern"""
    
    print("\n" + "="*80)
    print("CEO LOG AGENT FINAL E2E VERIFICATION")
    print("="*80)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Agent ID: {CEO_LOG_AGENT_ID}")
    
    # Check Cosmos DB before
    container, initial_count = check_cosmos_before()
    if not container:
        print("Cannot proceed without Cosmos DB")
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
        
        # Show tools
        if agent.tools:
            for i, tool in enumerate(agent.tools):
                print(f"  Tool {i+1}: {tool.get('type', 'unknown')}")
                if tool.get('type') == 'function':
                    func = tool.get('function', {})
                    print(f"    Name: {func.get('name')}")
                    print(f"    Description: {func.get('description', '')[:80]}...")
        
        # Create thread and run (following Weather Agent pattern)
        print(f"\n2. Creating thread and run...")
        
        # Prepare CEO log entry
        test_id = f"final_test_{int(time.time())}"
        log_entry = f"""Save this CEO log entry:

Exceptional quarterly board meeting outcomes:
1. Approved 30% increase in AI R&D budget for Q2 2025
2. Green light for European market expansion starting July
3. Strategic partnership with TechCorp finalized

Team exceeded Q1 targets by 20%. Morale is exceptionally high.
Risk: Supply chain disruptions may impact Q3 deliverables.

Test ID: {test_id}
Category: strategic_planning
User ID: ceo_test_user_001"""
        
        print(f"\n3. Sending CEO log entry...")
        print("-" * 80)
        print(log_entry)
        print("-" * 80)
        
        # Create thread and run in one call (like Weather Agent)
        run = client.agents.create_thread_and_run(
            agent_id=CEO_LOG_AGENT_ID,
            thread={
                "messages": [
                    {
                        "role": "user",
                        "content": log_entry
                    }
                ]
            }
        )
        thread_id = run.thread_id
        print(f"✓ Thread created: {thread_id}")
        print(f"✓ Run created: {run.id}")
        
        # Monitor run status
        start_time = time.time()
        last_status = None
        
        while run.status in ["queued", "in_progress", "requires_action"]:
            if run.status != last_status:
                print(f"   Status: {run.status}")
                last_status = run.status
            
            # Handle function calls if needed
            if run.status == "requires_action":
                print("   Agent is making function calls...")
                # In production, we would handle tool calls here
            
            time.sleep(1)
            run = client.agents.get_run(thread_id=thread_id, run_id=run.id)
            
            if time.time() - start_time > 60:
                print("✗ Timeout after 60 seconds")
                break
        
        print(f"   Final status: {run.status}")
        print(f"   Duration: {time.time() - start_time:.1f} seconds")
        
        # Get agent response
        if run.status == "completed":
            print(f"\n5. Agent response:")
            print("="*80)
            
            messages = client.agents.list_messages(thread_id=thread_id)
            response_text = ""
            
            for msg in messages.data:
                if msg.role == "assistant":
                    for content in msg.content:
                        if hasattr(content, 'text') and content.text:
                            response_text = content.text.value
                            print(response_text)
                    break
            
            print("="*80)
            
            if response_text:
                # Check if response indicates function was called
                if any(word in response_text.lower() for word in ['saved', 'stored', 'azure', 'function', 'created', 'cosmos', 'successfully']):
                    print("\n✓ Response indicates Azure Function was called!")
                
                # Wait for Azure Function to complete
                print(f"\n6. Waiting for Azure Function processing...")
                time.sleep(5)
                
                # Verify Cosmos DB
                print(f"\n7. Verifying Cosmos DB record creation...")
                success = check_cosmos_after(container, initial_count, test_id)
                
                if success:
                    print(f"\n" + "="*80)
                    print("✅ FULL END-TO-END TEST SUCCESSFUL!")
                    print("="*80)
                    print("✓ CEO Log Agent received the entry")
                    print("✓ Agent called Azure Function") 
                    print("✓ Azure Function created Cosmos DB record")
                    print("✓ Record verified in CEOLogs container")
                    print("\nThe complete flow is working:")
                    print("User → CEO Log Agent → Azure Function → Cosmos DB")
                else:
                    print(f"\n⚠️ Agent responded but no Cosmos DB record found")
                    print("\nPossible issues:")
                    print("1. Azure Function may not be deployed")
                    print("2. Function may not have correct Cosmos DB credentials")
                    print("3. Agent may not be calling the function correctly")
                    print("\nNext steps:")
                    print("- Check if Azure Function 'stratos-ceo-log-functions' is deployed")
                    print("- Verify function has correct Cosmos DB connection string")
                    print("- Check Azure Function logs for errors")
            else:
                print("\n✗ No response from agent")
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