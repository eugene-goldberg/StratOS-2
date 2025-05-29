#!/usr/bin/env python3
"""
Test CEO Log Agent using REST API directly
This bypasses the Semantic Kernel SDK issues
"""

import os
import time
import json
from datetime import datetime
from dotenv import load_dotenv
import requests
from azure.identity import DefaultAzureCredential
from azure.cosmos import CosmosClient

# Load environment variables
load_dotenv()

# Configuration
CEO_LOG_AGENT_ID = "asst_85MtpKLDOQA9ttsUckByGTKD"
COSMOS_ENDPOINT = "https://stratos-ceo-logs-db.documents.azure.com:443/"
COSMOS_KEY = "VAThFP4W5W47q1UK3QHrEw0YuPiHkdFkupVtBItd3PgOiuxlM6F4SqurWmwzN3KjZIUWuDBb5RizACDbZPOSzw=="
COSMOS_DATABASE = "StratOSData"
COSMOS_CONTAINER = "CEOLogs"

# Azure AI Project settings
AZURE_AI_ENDPOINT = "https://ai.azure.com/api/eastus/agents/v1.0/subscriptions/514bd6d3-2c02-45c6-a86f-29cf262a379a/resourceGroups/semantic-kernel-multi-agent-rg/providers/Microsoft.MachineLearningServices/workspaces/sk-multi-agent-project"
API_VERSION = "2024-12-01-preview"

def get_access_token():
    """Get access token using Azure Identity"""
    credential = DefaultAzureCredential()
    token = credential.get_token("https://management.azure.com/.default")
    return token.token

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
        # Check for records with test ID
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
            return True
        else:
            print(f"\n✗ No new records found. Count remains at {initial_count}")
            return False
            
    except Exception as e:
        print(f"\n✗ Cosmos DB verification error: {e}")
        return False

def test_ceo_log_agent():
    """Test CEO Log Agent using REST API"""
    
    print("\n" + "="*80)
    print("CEO LOG AGENT REST API TEST")
    print("="*80)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Agent ID: {CEO_LOG_AGENT_ID}")
    
    # Check Cosmos DB before
    container, initial_count = check_cosmos_before()
    if not container:
        print("Cannot proceed without Cosmos DB")
        return
    
    # Get access token
    print(f"\n1. Getting Azure access token...")
    token = get_access_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "api-key": os.getenv("AZURE_OPENAI_API_KEY", "")
    }
    print("✓ Access token obtained")
    
    try:
        # Verify agent exists
        print(f"\n2. Verifying agent deployment...")
        agent_url = f"{AZURE_AI_ENDPOINT}/assistants/{CEO_LOG_AGENT_ID}?api-version={API_VERSION}"
        response = requests.get(agent_url, headers=headers)
        
        if response.status_code == 200:
            agent_info = response.json()
            print(f"✓ Agent found: {agent_info.get('name')}")
            print(f"  Model: {agent_info.get('model')}")
            print(f"  Tools: {len(agent_info.get('tools', []))}")
        else:
            print(f"✗ Failed to get agent: {response.status_code}")
            print(response.text)
            return
        
        # Create thread
        print(f"\n3. Creating conversation thread...")
        thread_url = f"{AZURE_AI_ENDPOINT}/threads?api-version={API_VERSION}"
        response = requests.post(thread_url, headers=headers, json={})
        
        if response.status_code in [200, 201]:
            thread = response.json()
            thread_id = thread['id']
            print(f"✓ Thread created: {thread_id}")
        else:
            print(f"✗ Failed to create thread: {response.status_code}")
            print(response.text)
            return
        
        # Prepare CEO log entry
        test_id = f"rest_test_{int(time.time())}"
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
        
        print(f"\n4. Sending CEO log entry...")
        print("-" * 80)
        print(log_entry)
        print("-" * 80)
        
        # Add message to thread
        message_url = f"{AZURE_AI_ENDPOINT}/threads/{thread_id}/messages?api-version={API_VERSION}"
        message_data = {
            "role": "user",
            "content": log_entry
        }
        response = requests.post(message_url, headers=headers, json=message_data)
        
        if response.status_code in [200, 201]:
            print("✓ Message added to thread")
        else:
            print(f"✗ Failed to add message: {response.status_code}")
            print(response.text)
            return
        
        # Create run
        print(f"\n5. Executing agent...")
        run_url = f"{AZURE_AI_ENDPOINT}/threads/{thread_id}/runs?api-version={API_VERSION}"
        run_data = {
            "assistant_id": CEO_LOG_AGENT_ID
        }
        response = requests.post(run_url, headers=headers, json=run_data)
        
        if response.status_code in [200, 201]:
            run = response.json()
            run_id = run['id']
            print(f"✓ Run created: {run_id}")
        else:
            print(f"✗ Failed to create run: {response.status_code}")
            print(response.text)
            return
        
        # Monitor run status
        start_time = time.time()
        last_status = None
        
        while True:
            run_status_url = f"{AZURE_AI_ENDPOINT}/threads/{thread_id}/runs/{run_id}?api-version={API_VERSION}"
            response = requests.get(run_status_url, headers=headers)
            
            if response.status_code == 200:
                run = response.json()
                status = run['status']
                
                if status != last_status:
                    print(f"   Status: {status}")
                    last_status = status
                
                if status in ['completed', 'failed', 'cancelled', 'expired']:
                    break
                    
                if time.time() - start_time > 60:
                    print("✗ Timeout after 60 seconds")
                    break
                    
                time.sleep(1)
            else:
                print(f"✗ Failed to get run status: {response.status_code}")
                break
        
        duration = time.time() - start_time
        print(f"   Duration: {duration:.1f} seconds")
        
        # Get response
        if status == 'completed':
            print(f"\n6. Getting agent response...")
            messages_url = f"{AZURE_AI_ENDPOINT}/threads/{thread_id}/messages?api-version={API_VERSION}"
            response = requests.get(messages_url, headers=headers)
            
            if response.status_code == 200:
                messages = response.json()
                print("\nAgent Response:")
                print("-" * 80)
                
                for msg in messages.get('data', []):
                    if msg['role'] == 'assistant':
                        for content in msg.get('content', []):
                            if content.get('type') == 'text':
                                print(content['text']['value'])
                        break
                
                print("-" * 80)
                
                # Wait for Azure Function
                print(f"\n7. Waiting for Azure Function processing...")
                time.sleep(5)
                
                # Verify Cosmos DB
                print(f"\n8. Verifying Cosmos DB record creation...")
                success = check_cosmos_after(container, initial_count, test_id)
                
                if success:
                    print(f"\n" + "="*80)
                    print("✅ FULL END-TO-END TEST SUCCESSFUL!")
                    print("="*80)
                    print("✓ Agent received CEO log entry")
                    print("✓ Agent processed the request")
                    print("✓ Cosmos DB record created")
                else:
                    print(f"\n⚠️ Agent responded but no Cosmos DB record found")
            else:
                print(f"✗ Failed to get messages: {response.status_code}")
        else:
            print(f"\n✗ Run failed with status: {status}")
            
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_ceo_log_agent()