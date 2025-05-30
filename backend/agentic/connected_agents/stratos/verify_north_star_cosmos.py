#!/usr/bin/env python3
"""
Verify North Star data in Cosmos DB
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from azure.cosmos import CosmosClient

# Load environment variables
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

# Cosmos DB configuration
COSMOS_ENDPOINT = "https://stratos-ceo-logs-db.documents.azure.com:443/"
COSMOS_KEY = os.getenv("COSMOS_KEY")

# Create Cosmos client
cosmos_client = CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)

def verify_north_star_data():
    """Check North Star container in Cosmos DB"""
    try:
        database = cosmos_client.get_database_client("StratOSData")
        container = database.get_container_client("NorthStar")
        
        # Query for recent organizations
        query = "SELECT * FROM c ORDER BY c._ts DESC OFFSET 0 LIMIT 5"
        items = list(container.query_items(query=query, enable_cross_partition_query=True))
        
        print(f"\nFound {len(items)} recent North Star entries:")
        
        for item in items:
            print(f"\n{'='*60}")
            print(f"Organization ID: {item.get('organizationId', 'N/A')}")
            print(f"Purpose: {item.get('purpose', {}).get('statement', 'Not set')}")
            print(f"Vision: {item.get('vision', {}).get('statement', 'Not set')}")
            
            values = item.get('values', [])
            if values:
                print(f"Values: {len(values)} defined")
                for value in values[:3]:  # Show first 3
                    print(f"  - {value.get('name')}: {value.get('description', '')}")
            
            print(f"Created: {item.get('createdAt', 'Unknown')}")
            print(f"Updated: {item.get('lastUpdated', 'Unknown')}")
        
        # Check specific test organization
        test_org = "test-20250529-205556"
        query = f"SELECT * FROM c WHERE c.organizationId = '{test_org}'"
        items = list(container.query_items(query=query, enable_cross_partition_query=True))
        
        if items:
            print(f"\n✅ Found test organization {test_org} in Cosmos DB!")
            item = items[0]
            print(f"   Purpose: {item.get('purpose', {}).get('statement', 'Not set')}")
        else:
            print(f"\n❌ Test organization {test_org} not found in Cosmos DB")
            
    except Exception as e:
        print(f"Error checking Cosmos DB: {e}")


if __name__ == "__main__":
    print("="*70)
    print("NORTH STAR COSMOS DB VERIFICATION")
    print("="*70)
    
    verify_north_star_data()