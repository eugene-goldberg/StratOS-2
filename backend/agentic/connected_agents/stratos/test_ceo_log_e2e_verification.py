#!/usr/bin/env python3
"""
Test CEO Log Agent End-to-End verification
Tests: Agent → Azure Function → Cosmos DB
"""

import os
import sys
import json
import asyncio
import uuid
from datetime import datetime
from openai import AzureOpenAI
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import AzureTextCompletion, AzureChatCompletion
from semantic_kernel.connectors.ai.open_ai.services.azure_assistant_agent import AzureAssistantAgent
from azure.cosmos import CosmosClient, PartitionKey
from azure.core.exceptions import HttpResponseError
import requests
import time

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Azure OpenAI configuration
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_AI_AGENT_API_VERSION", "2024-12-01-preview")

# Cosmos DB configuration  
COSMOS_ENDPOINT = os.getenv("COSMOS_ENDPOINT")
COSMOS_KEY = os.getenv("COSMOS_KEY")
COSMOS_DATABASE = os.getenv("COSMOS_DB_DATABASE", "StratOSDatabase")
COSMOS_CONTAINER = os.getenv("COSMOS_DB_CONTAINER_LOGS", "ceoLogEntries")

# Agent configuration
CEO_LOG_AGENT_ID = "asst_9UphrHMFGC2QihVXrtOHDcND"

async def test_ceo_log_agent():
    """Test the CEO Log Agent with full flow verification"""
    
    print("=" * 80)
    print("CEO LOG AGENT END-TO-END VERIFICATION")
    print("=" * 80)
    
    # Initialize the kernel
    kernel = Kernel()
    
    # Create the agent
    try:
        print(f"\n1. Connecting to CEO Log Agent (ID: {CEO_LOG_AGENT_ID})...")
        
        agent = AzureAssistantAgent(
            kernel=kernel,
            name="CEO_Log_Agent",
            service_id="ceo_log_service",
            api_key=AZURE_OPENAI_API_KEY,
            endpoint=AZURE_OPENAI_ENDPOINT,
            api_version=AZURE_OPENAI_API_VERSION,
            assistant_id=CEO_LOG_AGENT_ID
        )
        
        print("✅ Successfully connected to CEO Log Agent")
        
    except Exception as e:
        print(f"❌ Failed to connect to agent: {str(e)}")
        return
    
    # Create a unique test entry
    test_id = str(uuid.uuid4())[:8]
    test_content = f"Test entry {test_id}: Our Q4 revenue projections look strong. We need to accelerate our AI product development to maintain competitive advantage."
    
    print(f"\n2. Sending test log entry...")
    print(f"   Test ID: {test_id}")
    print(f"   Content: {test_content}")
    
    try:
        # Create thread
        thread_id = await agent.create_thread()
        print(f"   Thread ID: {thread_id}")
        
        # Send the message
        message = f"""Please save this CEO log entry:
        
User ID: test_user_{test_id}
Content: {test_content}
Category: strategic_planning
Source: test_verification

Please use the code interpreter to call the SaveCEOLog Azure Function and show me the complete response."""
        
        print("\n3. Invoking agent...")
        start_time = time.time()
        
        messages = []
        async for msg in agent.invoke(thread_id, message):
            messages.append(msg)
            
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"   Duration: {duration:.2f} seconds")
        
        # Display agent response
        print("\n4. Agent Response:")
        print("-" * 40)
        for msg in messages:
            print(f"   {msg.content}")
        print("-" * 40)
        
    except Exception as e:
        print(f"❌ Agent invocation failed: {str(e)}")
        return
    
    # Wait a moment for Cosmos DB to be updated
    print("\n5. Waiting 3 seconds for Cosmos DB update...")
    time.sleep(3)
    
    # Verify in Cosmos DB
    print("\n6. Verifying entry in Cosmos DB...")
    try:
        # Initialize Cosmos client
        cosmos_client = CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)
        database = cosmos_client.get_database_client(COSMOS_DATABASE)
        container = database.get_container_client(COSMOS_CONTAINER)
        
        # Query for our test entry
        query = f"SELECT * FROM c WHERE c.userId = 'test_user_{test_id}' ORDER BY c._ts DESC"
        
        items = list(container.query_items(
            query=query,
            enable_cross_partition_query=True
        ))
        
        if items:
            print(f"✅ Found {len(items)} entries in Cosmos DB!")
            entry = items[0]
            print("\n   Cosmos DB Entry Details:")
            print(f"   - ID: {entry.get('id')}")
            print(f"   - User ID: {entry.get('userId')}")
            print(f"   - Category: {entry.get('category')}")
            print(f"   - Source: {entry.get('source')}")
            print(f"   - Timestamp: {entry.get('timestamp')}")
            print(f"   - Content Preview: {entry.get('content', '')[:100]}...")
            
            if entry.get('aiAnalysis'):
                ai = entry['aiAnalysis']
                print(f"\n   AI Analysis:")
                print(f"   - Summary: {ai.get('summary', '')[:100]}...")
                print(f"   - Tags: {', '.join(ai.get('tags', []))}")
                print(f"   - Sentiment: {ai.get('sentiment')}")
                print(f"   - Action Items: {len(ai.get('actionItems', []))} items")
        else:
            print(f"❌ No entries found for test_user_{test_id}")
            
            # Try a broader query
            print("\n   Checking recent entries...")
            query = "SELECT TOP 5 c.id, c.userId, c.timestamp FROM c ORDER BY c._ts DESC"
            recent_items = list(container.query_items(
                query=query,
                enable_cross_partition_query=True
            ))
            
            if recent_items:
                print(f"   Found {len(recent_items)} recent entries:")
                for item in recent_items:
                    print(f"   - {item['id']} (User: {item['userId']}, Time: {item.get('timestamp', 'N/A')})")
            else:
                print("   No entries found in CeoLogs container")
                
    except Exception as e:
        print(f"❌ Cosmos DB verification failed: {str(e)}")
        
    # Test direct Azure Function call
    print("\n7. Testing direct Azure Function call...")
    try:
        url = "https://stratos-ceo-log-functions.azurewebsites.net/api/SaveCEOLog"
        headers = {
            "x-functions-key": "I3c897PZMtJp1goBaxPwGlXa3Ni6ZsM09t1F7roTLVZeAzFu69TeKA==",
            "Content-Type": "application/json"
        }
        
        direct_test_id = str(uuid.uuid4())[:8]
        payload = {
            "userId": f"direct_test_{direct_test_id}",
            "content": f"Direct test {direct_test_id}: Testing Azure Function directly",
            "category": "general",
            "source": "direct_api_test"
        }
        
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Direct Azure Function call successful!")
            print(f"   Response: {json.dumps(result, indent=2)}")
        else:
            print(f"❌ Direct function call failed: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Direct function test failed: {str(e)}")
    
    print("\n" + "=" * 80)
    print("END-TO-END VERIFICATION COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(test_ceo_log_agent())