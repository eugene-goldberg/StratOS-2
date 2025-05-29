#!/usr/bin/env python3

"""Test Cosmos DB connection using connection string from Key Vault"""

import os
import asyncio
from azure.cosmos.aio import CosmosClient
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential
from datetime import datetime
import json

# Color codes
GREEN = '\033[0;32m'
RED = '\033[0;31m'
YELLOW = '\033[1;33m'
NC = '\033[0m'  # No Color

def print_success(msg):
    print(f"{GREEN}✅ {msg}{NC}")

def print_error(msg):
    print(f"{RED}❌ {msg}{NC}")

def print_info(msg):
    print(f"{YELLOW}ℹ️  {msg}{NC}")

async def test_cosmos_connection():
    """Test Cosmos DB operations using connection string"""
    
    # Get connection string from Key Vault
    key_vault_name = "stratos-keyvault"
    credential = DefaultAzureCredential()
    
    print_info("Retrieving connection string from Key Vault...")
    kv_client = SecretClient(
        vault_url=f"https://{key_vault_name}.vault.azure.net/",
        credential=credential
    )
    
    try:
        connection_string = kv_client.get_secret("cosmos-db-connection-string").value
        print_success("Retrieved connection string from Key Vault")
    except Exception as e:
        print_error(f"Failed to get connection string: {e}")
        return
    
    # Connect to Cosmos DB
    print_info("Connecting to Cosmos DB...")
    client = CosmosClient.from_connection_string(connection_string)
    
    try:
        # Get database and container
        database = client.get_database_client("StratOSData")
        container = database.get_container_client("CEOLogs")
        
        # Test 1: Read container properties
        print_info("Testing container access...")
        properties = await container.read()
        print_success(f"Connected to container: {properties['id']}")
        print(f"  Partition key: {properties['partitionKey']['paths'][0]}")
        
        # Test 2: Create a test document
        print_info("Creating test document...")
        test_doc = {
            "id": f"test-{datetime.now().isoformat()}",
            "userId": "test-user",
            "timestamp": datetime.now().isoformat(),
            "logEntry": {
                "content": "Test CEO log entry from Cosmos DB setup script",
                "sentiment": "positive",
                "confidence": 0.95
            },
            "tags": ["test", "cosmos-db", "setup"],
            "metadata": {
                "source": "script",
                "testRun": True
            },
            "createdAt": datetime.now().isoformat(),
            "modifiedAt": datetime.now().isoformat(),
            "version": 1
        }
        
        result = await container.create_item(test_doc)
        print_success(f"Created test document: {result['id']}")
        
        # Test 3: Query documents
        print_info("Querying documents...")
        query = "SELECT * FROM c WHERE c.userId = @userId"
        parameters = [{"name": "@userId", "value": "test-user"}]
        
        items = []
        async for item in container.query_items(
            query=query,
            parameters=parameters
        ):
            items.append(item)
        
        print_success(f"Found {len(items)} documents for test-user")
        
        # Test 4: Delete test document
        print_info("Cleaning up test document...")
        await container.delete_item(item=test_doc["id"], partition_key="test-user")
        print_success("Test document deleted")
        
        print("\n" + "="*50)
        print_success("ALL TESTS PASSED!")
        print("="*50)
        
        # Summary
        print("\nCosmos DB Configuration:")
        print(f"  Database: StratOSData")
        print(f"  Container: CEOLogs")
        print(f"  Partition Key: /userId")
        print(f"  Connection: ✅ Working")
        print(f"  Read Access: ✅ Verified")
        print(f"  Write Access: ✅ Verified")
        print(f"  Query Access: ✅ Verified")
        
    except Exception as e:
        print_error(f"Test failed: {e}")
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(test_cosmos_connection())