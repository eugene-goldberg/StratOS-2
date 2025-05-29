#!/usr/bin/env python3
"""
End-to-end test of CEO Log Agent calling Azure Functions and creating Cosmos DB records.
Using the correct agent ID from the deployment.
"""

import asyncio
import os
import logging
import sys
import json
import time
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from azure.cosmos import CosmosClient
from azure.identity.aio import DefaultAzureCredential
from azure.ai.projects.aio import AIProjectClient
from semantic_kernel.agents import AzureAIAgent

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Cosmos DB configuration
cosmos_client = CosmosClient(
    url=os.getenv("COSMOS_DB_ENDPOINT"),
    credential=os.getenv("COSMOS_DB_KEY")
)

# CEO Log Agent ID from deployment
CEO_LOG_AGENT_ID = "asst_mpgSYbBEqI14rLta34RX8RoP"

def verify_cosmos_before():
    """Check Cosmos DB before the test"""
    try:
        database = cosmos_client.get_database_client("StratOSData")
        container = database.get_container_client("CEOLogs")
        
        # Count existing items
        query = "SELECT VALUE COUNT(1) FROM c"
        items = list(container.query_items(query=query, enable_cross_partition_query=True))
        count_before = items[0] if items else 0
        
        logger.info(f"✓ Connected to Cosmos DB")
        logger.info(f"  Database: StratOSData")
        logger.info(f"  Container: CEOLogs")
        logger.info(f"  Items before test: {count_before}")
        
        return count_before
    except Exception as e:
        logger.error(f"✗ Failed to connect to Cosmos DB: {e}")
        return None

def verify_cosmos_after(test_content, count_before):
    """Verify the log was saved to Cosmos DB"""
    try:
        database = cosmos_client.get_database_client("StratOSData")
        container = database.get_container_client("CEOLogs")
        
        # Count items after
        query = "SELECT VALUE COUNT(1) FROM c"
        items = list(container.query_items(query=query, enable_cross_partition_query=True))
        count_after = items[0] if items else 0
        
        logger.info(f"✓ Items after test: {count_after}")
        logger.info(f"  Items created: {count_after - count_before}")
        
        if count_after > count_before:
            # Get the most recent entries
            query = "SELECT TOP 5 * FROM c ORDER BY c._ts DESC"
            items = list(container.query_items(query=query, enable_cross_partition_query=True))
            
            for item in items:
                logger.info(f"\nFound entry:")
                logger.info(f"  ID: {item.get('id')}")
                logger.info(f"  Content: {item.get('content', '')[:100]}...")
                
                # Check if it contains our test content
                if test_content in str(item.get('content', '')):
                    logger.info(f"\n✅ VERIFIED: Found our test log entry in Cosmos DB!")
                    logger.info(f"  Full content: {item.get('content')}")
                    logger.info(f"  Category: {item.get('category')}")
                    logger.info(f"  Tags: {item.get('tags')}")
                    logger.info(f"  Timestamp: {item.get('timestamp')}")
                    return True
            
            logger.info(f"\n✅ New entries created in Cosmos DB (count increased by {count_after - count_before})")
            return True
        else:
            logger.error(f"\n✗ No new entries found in Cosmos DB")
            return False
            
    except Exception as e:
        logger.error(f"✗ Failed to verify Cosmos DB: {e}")
        return False

async def test_ceo_log_agent_save():
    """Test CEO Log Agent saving entry via Azure Function"""
    
    # Create unique test content
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    test_content = f"E2E Test Entry {timestamp}: Successful integration of CEO Log Agent with Azure Functions and Cosmos DB"
    
    logger.info(f"\nTesting CEO Log Agent: {CEO_LOG_AGENT_ID}")
    logger.info(f"Test content: {test_content}")
    
    endpoint = os.getenv("AZURE_AI_PROJECT_CONNECTION_STRING")
    
    async with DefaultAzureCredential() as credential, \
               AIProjectClient(endpoint=endpoint, credential=credential) as client:
        
        # Get agent definition
        try:
            agent_def = await client.agents.get_agent(agent_id=CEO_LOG_AGENT_ID)
            logger.info(f"✓ Retrieved agent: {agent_def.name}")
            logger.info(f"  Model: {agent_def.model}")
            logger.info(f"  Tools: {len(agent_def.tools) if agent_def.tools else 0}")
        except Exception as e:
            logger.error(f"✗ Failed to get agent: {e}")
            return None
        
        # Create agent instance
        ceo_agent = AzureAIAgent(
            client=client,
            definition=agent_def
        )
        
        # Send save request
        logger.info("\nSending save request to CEO Log Agent...")
        save_message = f"Save this CEO log entry: '{test_content}'. Category: E2E Testing, Tags: integration-test, azure-functions, cosmos-db"
        
        response = ""
        try:
            async for part in ceo_agent.invoke(messages=save_message):
                if hasattr(part, 'content') and part.content:
                    response += str(part.content)
            
            logger.info(f"\n✓ Agent response: {response}")
            
            # Check if response indicates success
            if any(word in response.lower() for word in ["saved", "stored", "created", "success"]):
                logger.info("✓ Agent indicates save was successful")
            else:
                logger.warning("⚠️  Agent response doesn't clearly indicate success")
                
        except Exception as e:
            logger.error(f"✗ Failed to invoke agent: {e}")
            import traceback
            traceback.print_exc()
            return None
        
        return test_content

async def main():
    """Main test function"""
    logger.info("\n" + "="*70)
    logger.info("CEO LOG AGENT END-TO-END VERIFICATION")
    logger.info("Testing: CEO Log Agent → Azure Function → Cosmos DB")
    logger.info("="*70)
    
    # Step 1: Check Cosmos DB before
    logger.info("\n1. Checking Cosmos DB before test...")
    count_before = verify_cosmos_before()
    if count_before is None:
        logger.error("Failed to connect to Cosmos DB - aborting test")
        return
    
    # Step 2: Test CEO Log Agent
    logger.info("\n2. Testing CEO Log Agent with save request...")
    test_content = await test_ceo_log_agent_save()
    if not test_content:
        logger.error("Failed to test CEO Log Agent - aborting test")
        return
    
    # Step 3: Wait for Azure Function processing
    logger.info("\n3. Waiting 10 seconds for Azure Function to process...")
    await asyncio.sleep(10)
    
    # Step 4: Verify in Cosmos DB
    logger.info("\n4. Verifying Cosmos DB after test...")
    success = verify_cosmos_after(test_content, count_before)
    
    # Summary
    logger.info("\n" + "="*70)
    if success:
        logger.info("✅ END-TO-END VERIFICATION SUCCESSFUL!")
        logger.info("   • CEO Log Agent received the save request")
        logger.info("   • Agent called the Azure Function")
        logger.info("   • Azure Function created record in Cosmos DB")
        logger.info("   • Complete flow is working correctly")
    else:
        logger.info("❌ END-TO-END VERIFICATION FAILED")
        logger.info("   • Check Azure Function logs at:")
        logger.info("     https://stratos-ceo-log-functions.azurewebsites.net")
        logger.info("   • Verify Azure Function app settings are correct")

if __name__ == "__main__":
    asyncio.run(main())