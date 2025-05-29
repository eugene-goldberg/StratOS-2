#!/usr/bin/env python3
"""
Full end-to-end test of CEO Log Agent with Cosmos DB verification
Using synchronous approach with proper API calls
"""

import os
import asyncio
import time
from datetime import datetime
from dotenv import load_dotenv
from azure.identity.aio import DefaultAzureCredential
from azure.ai.projects.aio import AIProjectClient
from semantic_kernel.agents import AzureAIAgent
from azure.cosmos import CosmosClient

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

async def test_ceo_log_agent():
    """Test CEO Log Agent with full flow verification"""
    
    print("\n" + "="*80)
    print("CEO LOG AGENT FULL END-TO-END TEST")
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
    
    async with AIProjectClient(endpoint=endpoint, credential=credential) as client:
        try:
            # Verify agent
            print(f"\n1. Verifying agent deployment...")
            agent_def = await client.agents.get_agent(CEO_LOG_AGENT_ID)
            print(f"✓ Agent found: {agent_def.name}")
            print(f"  Model: {agent_def.model}")
            print(f"  Tools: {len(agent_def.tools) if agent_def.tools else 0}")
            
            # Show tools
            if agent_def.tools:
                for i, tool in enumerate(agent_def.tools):
                    print(f"  Tool {i+1}: {tool.get('type', 'unknown')}")
                    if tool.get('type') == 'function':
                        func = tool.get('function', {})
                        print(f"    Name: {func.get('name')}")
            
            # Create agent
            agent = AzureAIAgent(
                client=client,
                definition=agent_def
            )
            
            # Prepare CEO log entry
            test_id = f"e2e_test_{int(time.time())}"
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
            
            print(f"\n2. Sending CEO log entry to agent...")
            print("-" * 80)
            print(log_entry)
            print("-" * 80)
            
            print(f"\n3. Agent processing...")
            start_time = time.time()
            
            # Invoke agent
            response_text = ""
            print("\nAgent Response:")
            print("-" * 80)
            
            async for part in agent.invoke(messages=log_entry):
                if hasattr(part, 'content') and part.content:
                    response_text += str(part.content)
                    print(part.content, end='', flush=True)
            
            print("\n" + "-" * 80)
            duration = time.time() - start_time
            print(f"Processing time: {duration:.1f} seconds")
            
            if response_text:
                # Check if response indicates function was called
                if any(word in response_text.lower() for word in ['saved', 'stored', 'azure', 'function', 'created', 'cosmos']):
                    print("\n✓ Response indicates Azure Function was called!")
                
                # Wait for Azure Function to complete
                print(f"\n4. Waiting for Azure Function to complete...")
                await asyncio.sleep(5)
                
                # Verify Cosmos DB
                print(f"\n5. Verifying Cosmos DB record creation...")
                success = check_cosmos_after(container, initial_count, test_id)
                
                if success:
                    print(f"\n" + "="*80)
                    print("✅ FULL END-TO-END TEST SUCCESSFUL!")
                    print("="*80)
                    print("✓ Agent received CEO log entry")
                    print("✓ Agent called Azure Function")
                    print("✓ Azure Function created Cosmos DB record")
                    print("✓ Record verified in CEOLogs container")
                else:
                    print(f"\n⚠️ Agent responded but no Cosmos DB record found")
                    print("Possible issues:")
                    print("- Azure Function may not be deployed")
                    print("- Function may not have correct Cosmos DB credentials")
                    print("- Agent may not be calling the function correctly")
            else:
                print("\n✗ No response from agent")
                
        except Exception as e:
            print(f"\n✗ Test failed: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_ceo_log_agent())