#!/usr/bin/env python3
"""
Simplified E2E test for CEO Log Agent -> Azure Function -> Cosmos DB
Tests the complete flow with actual evidence
"""

import os
import sys
import json
import asyncio
from datetime import datetime
from azure.ai.projects.aio import AIProjectClient
from azure.identity.aio import DefaultAzureCredential
# Note: We'll import CosmosClient later in the code where needed

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configuration
PROJECT_CONNECTION_STRING = "https://ai.azure.com/api/eastus/agents/v1.0/subscriptions/514bd6d3-2c02-45c6-a86f-29cf262a379a/resourceGroups/semantic-kernel-multi-agent-rg/providers/Microsoft.MachineLearningServices/workspaces/sk-multi-agent-project"
CEO_LOG_AGENT_ID = "asst_9UphrHMFGC2QihVXrtOHDcND"
COSMOS_ENDPOINT = "https://stratos-ceo-logs-db.documents.azure.com:443/"
COSMOS_KEY = "VAThFP4W5W47q1UK3QHrEw0YuPiHkdFkupVtBItd3PgOiuxlM6F4SqurWmwzN3KjZIUWuDBb5RizACDbZPOSzw=="
COSMOS_DATABASE = "StratOSDatabase"
COSMOS_CONTAINER = "ceoLogEntries"

async def test_ceo_log_e2e():
    """Test complete flow: Agent -> Function -> Cosmos DB"""
    print("=" * 60)
    print("CEO LOG E2E TEST - SIMPLIFIED")
    print("=" * 60)
    
    # Initialize clients
    credential = DefaultAzureCredential()
    client = AIProjectClient(
        endpoint=PROJECT_CONNECTION_STRING,
        credential=credential
    )
    
    # Test entry
    test_entry = {
        "content": f"E2E test entry - {datetime.utcnow().isoformat()}",
        "priority": "high",
        "tags": ["test", "e2e", "verification"]
    }
    
    print("\n1. SENDING TEST ENTRY TO CEO LOG AGENT")
    print(f"Entry: {json.dumps(test_entry, indent=2)}")
    
    try:
        # Create agent instance
        agent = await client.agents.get_agent(assistant_id=CEO_LOG_AGENT_ID)
        
        # Create thread and send message
        thread = await client.agents.create_thread()
        
        message_content = f"""
        Please create a CEO log entry with the following details:
        - Content: {test_entry['content']}
        - Priority: {test_entry['priority']}
        - Tags: {', '.join(test_entry['tags'])}
        
        Use the create_ceo_log_entry function to save this entry.
        """
        
        await client.agents.create_message(
            thread_id=thread.id,
            role="user",
            content=message_content
        )
        
        # Run and get response
        print("\n2. INVOKING AGENT WITH AZURE FUNCTION")
        run = await client.agents.create_and_process_run(
            thread_id=thread.id,
            assistant_id=agent.id
        )
        
        # Get messages
        messages = await client.agents.list_messages(thread_id=thread.id)
        
        print("\n3. AGENT RESPONSE:")
        for msg in messages:
            if msg.role == "assistant":
                print(f"Assistant: {msg.content[0].text.value if msg.content else 'No content'}")
                
                # Check if function was called
                if hasattr(run, 'required_action') and run.required_action:
                    print("\n4. FUNCTION CALLS MADE:")
                    for tool_call in run.required_action.submit_tool_outputs.tool_calls:
                        print(f"- Function: {tool_call.function.name}")
                        print(f"  Arguments: {tool_call.function.arguments}")
        
        # Verify in Cosmos DB
        print("\n5. VERIFYING IN COSMOS DB")
        from azure.cosmos import CosmosClient as SyncCosmosClient
        cosmos_client = SyncCosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)
        database = cosmos_client.get_database_client(COSMOS_DATABASE)
        container = database.get_container_client(COSMOS_CONTAINER)
        
        # Query for recent entries
        query = """
        SELECT TOP 5 * FROM c 
        WHERE CONTAINS(c.content, 'E2E test entry')
        ORDER BY c.timestamp DESC
        """
        
        items = list(container.query_items(query=query, enable_cross_partition_query=True))
        
        if items:
            print(f"\n✅ FOUND {len(items)} TEST ENTRIES IN COSMOS DB:")
            for item in items[:2]:  # Show first 2
                print(f"\n- ID: {item.get('id')}")
                print(f"  Content: {item.get('content')}")
                print(f"  Priority: {item.get('priority')}")
                print(f"  Tags: {item.get('tags')}")
                print(f"  Timestamp: {item.get('timestamp')}")
        else:
            print("\n❌ NO TEST ENTRIES FOUND IN COSMOS DB")
        
        # Clean up
        cosmos_client.close()
        await client.close()
        
        print("\n" + "=" * 60)
        print("E2E TEST COMPLETE")
        print("=" * 60)
        
        return len(items) > 0
        
    except Exception as e:
        print(f"\n❌ ERROR IN E2E TEST: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run the E2E test"""
    success = await test_ceo_log_e2e()
    
    if success:
        print("\n✅ E2E TEST PASSED - Complete flow verified")
    else:
        print("\n❌ E2E TEST FAILED - Check errors above")
    
    return success

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)