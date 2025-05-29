#!/usr/bin/env python3
"""
Direct test of CEO Log Agent using invoke pattern
"""

import os
import asyncio
import time
from datetime import datetime
from dotenv import load_dotenv
from azure.identity.aio import DefaultAzureCredential
from azure.ai.projects.aio import AIProjectClient
from semantic_kernel.agents import AzureAIAgent
from azure.cosmos.aio import CosmosClient

# Load environment variables
load_dotenv()

# Configuration
CEO_LOG_AGENT_ID = "asst_85MtpKLDOQA9ttsUckByGTKD"
COSMOS_ENDPOINT = "https://stratos-ceo-logs-db.documents.azure.com:443/"
COSMOS_KEY = "VAThFP4W5W47q1UK3QHrEw0YuPiHkdFkupVtBItd3PgOiuxlM6F4SqurWmwzN3KjZIUWuDBb5RizACDbZPOSzw=="
COSMOS_DATABASE = "StratOSData"
COSMOS_CONTAINER = "CEOLogs"

async def check_cosmos_async():
    """Check Cosmos DB asynchronously"""
    try:
        async with CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY) as client:
            database = client.get_database_client(COSMOS_DATABASE)
            container = database.get_container_client(COSMOS_CONTAINER)
            
            # Query to count records
            query = "SELECT VALUE COUNT(1) FROM c"
            items = []
            async for item in container.query_items(query=query, enable_cross_partition_query=True):
                items.append(item)
            
            initial_count = items[0] if items else 0
            print(f"✓ Connected to Cosmos DB")
            print(f"  Database: {COSMOS_DATABASE}")
            print(f"  Container: {COSMOS_CONTAINER}")
            print(f"  Initial record count: {initial_count}")
            
            return container, initial_count
    except Exception as e:
        print(f"✗ Cosmos DB connection failed: {e}")
        return None, 0

async def test_ceo_log_agent():
    """Test CEO Log Agent with direct invocation"""
    
    print("\n" + "="*70)
    print("CEO LOG AGENT END-TO-END TEST (ASYNC)")
    print("="*70)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Agent ID: {CEO_LOG_AGENT_ID}")
    
    # Check Cosmos DB first
    container, initial_count = await check_cosmos_async()
    if not container:
        print("Cannot proceed without Cosmos DB connection")
        return
    
    # Connect to Azure AI Project
    endpoint = os.getenv("AZURE_AI_PROJECT_CONNECTION_STRING")
    if not endpoint:
        print("✗ AZURE_AI_PROJECT_CONNECTION_STRING not set")
        return
    
    credential = DefaultAzureCredential()
    
    async with AIProjectClient(endpoint=endpoint, credential=credential) as client:
        try:
            # Verify agent exists
            print(f"\n1. Verifying agent deployment...")
            agent_def = await client.agents.get_agent(CEO_LOG_AGENT_ID)
            print(f"✓ Agent found: {agent_def.name}")
            print(f"  Model: {agent_def.model}")
            print(f"  Tools: {len(agent_def.tools) if agent_def.tools else 0}")
            
            # Create agent instance
            agent = AzureAIAgent(
                client=client,
                definition=agent_def
            )
            
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
            
            print(f"\n2. Sending CEO log entry...")
            print("-" * 70)
            print(log_entry)
            print("-" * 70)
            
            print(f"\n3. Invoking agent...")
            start_time = time.time()
            
            # Invoke agent directly
            response_text = ""
            async for part in agent.invoke(messages=log_entry):
                if hasattr(part, 'content') and part.content:
                    response_text += str(part.content)
                    print(part.content, end='', flush=True)
            
            duration = time.time() - start_time
            print(f"\n\nDuration: {duration:.1f} seconds")
            
            if response_text:
                # Wait for Azure Function processing
                print(f"\n4. Waiting for Azure Function processing...")
                await asyncio.sleep(5)
                
                # Verify Cosmos DB record
                print(f"\n5. Verifying Cosmos DB record creation...")
                
                # Query for new records
                query = f"SELECT * FROM c WHERE CONTAINS(c.content, '{test_id}') OR CONTAINS(c.id, '{test_id}')"
                new_records = []
                async for record in container.query_items(
                    query=query,
                    enable_cross_partition_query=True
                ):
                    new_records.append(record)
                
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
                    items = []
                    async for item in container.query_items(query=query, enable_cross_partition_query=True):
                        items.append(item)
                    final_count = items[0] if items else 0
                    
                    if final_count > initial_count:
                        print(f"✓ New records created! Count increased from {initial_count} to {final_count}")
                        
                        # Get latest record
                        query = "SELECT TOP 1 * FROM c ORDER BY c._ts DESC"
                        latest = []
                        async for record in container.query_items(
                            query=query,
                            enable_cross_partition_query=True
                        ):
                            latest.append(record)
                        
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
                print("\n✗ No response from agent")
                
        except Exception as e:
            print(f"\n✗ Test failed: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_ceo_log_agent())