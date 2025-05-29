#!/usr/bin/env python3
"""
Verify the CEO Log entry in Cosmos DB
"""

import os
from dotenv import load_dotenv
from azure.cosmos import CosmosClient

load_dotenv()

cosmos_client = CosmosClient(
    url=os.getenv("COSMOS_DB_ENDPOINT"),
    credential=os.getenv("COSMOS_DB_KEY")
)

def check_entry(entry_id):
    """Check a specific entry in Cosmos DB"""
    try:
        database = cosmos_client.get_database_client("StratOSData")
        container = database.get_container_client("CEOLogs")
        
        # Get the specific item
        item = container.read_item(item=entry_id, partition_key=entry_id)
        
        print(f"✅ Entry found: {entry_id}")
        print("\nFull entry content:")
        
        # Print all fields
        for key, value in item.items():
            if key not in ['_rid', '_self', '_etag', '_attachments']:
                print(f"  {key}: {value}")
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # Check the entry created in our agent-only test
    check_entry("46905ca1-b531-4b72-89f8-4d4c9020f29d")