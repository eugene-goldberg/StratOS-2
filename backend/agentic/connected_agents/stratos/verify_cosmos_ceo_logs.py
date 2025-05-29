#!/usr/bin/env python3
"""
Verify Cosmos DB CEOLogs container
"""

import os
from dotenv import load_dotenv
from azure.cosmos import CosmosClient

# Load environment variables
load_dotenv()

# Configuration
COSMOS_ENDPOINT = "https://stratos-ceo-logs-db.documents.azure.com:443/"
COSMOS_KEY = "VAThFP4W5W47q1UK3QHrEw0YuPiHkdFkupVtBItd3PgOiuxlM6F4SqurWmwzN3KjZIUWuDBb5RizACDbZPOSzw=="
COSMOS_DATABASE = "StratOSData"
COSMOS_CONTAINER = "CEOLogs"

def check_cosmos():
    """Check Cosmos DB and list all records"""
    try:
        client = CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)
        database = client.get_database_client(COSMOS_DATABASE)
        container = database.get_container_client(COSMOS_CONTAINER)
        
        print(f"✓ Connected to Cosmos DB")
        print(f"  Database: {COSMOS_DATABASE}")
        print(f"  Container: {COSMOS_CONTAINER}")
        
        # Count records
        query = "SELECT VALUE COUNT(1) FROM c"
        items = list(container.query_items(query=query, enable_cross_partition_query=True))
        count = items[0] if items else 0
        print(f"  Total records: {count}")
        
        if count > 0:
            # List all records
            print("\nRecords in CEOLogs container:")
            print("-" * 80)
            
            query = "SELECT * FROM c ORDER BY c._ts DESC"
            for record in container.query_items(query=query, enable_cross_partition_query=True):
                print(f"\nID: {record.get('id')}")
                print(f"User ID: {record.get('userId')}")
                print(f"Category: {record.get('category')}")
                print(f"Content: {record.get('content', '')[:200]}...")
                print(f"Tags: {record.get('tags', [])}")
                print(f"Created: {record.get('createdAt')}")
                print(f"Timestamp: {record.get('_ts')}")
                print("-" * 80)
        
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

if __name__ == "__main__":
    print("Cosmos DB CEOLogs Container Verification")
    print("="*80)
    check_cosmos()