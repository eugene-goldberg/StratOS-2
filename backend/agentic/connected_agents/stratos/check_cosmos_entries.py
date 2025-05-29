#!/usr/bin/env python3
"""
Check Cosmos DB for CEO Log entries
"""

import asyncio
import os
from datetime import datetime, timedelta
from azure.cosmos.aio import CosmosClient
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential
from pathlib import Path
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv(Path(__file__).parent.parent / '.env')

# Color codes for output
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
CYAN = '\033[0;36m'
NC = '\033[0m'  # No Color

async def check_cosmos_entries():
    """Check CEOLogs container in Cosmos DB"""
    
    print(f"{YELLOW}Checking Cosmos DB CEOLogs container...{NC}\n")
    
    # Get connection string from Key Vault
    key_vault_name = "stratos-keyvault"
    credential = DefaultAzureCredential()
    
    print(f"Retrieving connection string from Key Vault: {key_vault_name}")
    kv_client = SecretClient(
        vault_url=f"https://{key_vault_name}.vault.azure.net/",
        credential=credential
    )
    
    try:
        connection_string = kv_client.get_secret("cosmos-db-connection-string").value
        print(f"{GREEN}✅ Retrieved connection string from Key Vault{NC}\n")
    except Exception as e:
        print(f"❌ Failed to get connection string: {e}")
        return
    
    # Connect to Cosmos DB
    client = CosmosClient.from_connection_string(connection_string)
    
    try:
        # Get database and container
        database = client.get_database_client("StratOSData")
        container = database.get_container_client("CEOLogs")
        
        # Query for recent entries (last 24 hours)
        print(f"{CYAN}Querying for CEO log entries from the last 24 hours...{NC}\n")
        
        query = """
        SELECT * FROM c 
        WHERE c.timestamp >= @start_time
        ORDER BY c.timestamp DESC
        """
        
        start_time = (datetime.utcnow() - timedelta(hours=24)).isoformat()
        parameters = [{"name": "@start_time", "value": start_time}]
        
        entries = []
        async for item in container.query_items(
            query=query,
            parameters=parameters
        ):
            entries.append(item)
        
        print(f"{GREEN}Found {len(entries)} CEO log entries in the last 24 hours{NC}\n")
        
        # Display entries
        for idx, entry in enumerate(entries, 1):
            print(f"{YELLOW}=== Entry {idx} ==={NC}")
            print(f"ID: {entry.get('id')}")
            print(f"User ID: {entry.get('userId')}")
            print(f"Timestamp: {entry.get('timestamp')}")
            
            log_entry = entry.get('logEntry', {})
            content = log_entry.get('content', '')
            print(f"\nContent Preview: {content[:200]}..." if len(content) > 200 else f"\nContent: {content}")
            
            print(f"\nSentiment: {log_entry.get('sentiment', 'N/A')}")
            print(f"Confidence: {log_entry.get('confidence', 'N/A')}")
            
            tags = entry.get('tags', [])
            print(f"\nTags: {', '.join(tags[:10])}")
            
            themes = entry.get('strategicThemes', [])
            if themes:
                print(f"Strategic Themes: {', '.join(themes)}")
            
            metadata = entry.get('metadata', {})
            print(f"\nSource: {metadata.get('source', 'N/A')}")
            print(f"Session ID: {metadata.get('sessionId', 'N/A')}")
            
            analysis = entry.get('analysis', {})
            action_items = analysis.get('actionItems', [])
            if action_items:
                print(f"\nAction Items:")
                for item in action_items[:3]:
                    print(f"  • {item}")
            
            print(f"\n{'-'*60}\n")
        
        # Query specifically for our test entry
        print(f"{CYAN}Looking for entries with user ID 'ceo-001'...{NC}\n")
        
        ceo_query = "SELECT * FROM c WHERE c.userId = @userId ORDER BY c.timestamp DESC"
        ceo_params = [{"name": "@userId", "value": "ceo-001"}]
        
        ceo_entries = []
        async for item in container.query_items(
            query=ceo_query,
            parameters=ceo_params
        ):
            ceo_entries.append(item)
        
        print(f"{GREEN}Found {len(ceo_entries)} entries for user 'ceo-001'{NC}")
        
        if ceo_entries:
            latest = ceo_entries[0]
            print(f"\nLatest entry for ceo-001:")
            print(f"  Created: {latest.get('timestamp')}")
            print(f"  Content starts with: {latest.get('logEntry', {}).get('content', '')[:100]}...")
        
        # Check delegation tracking container
        print(f"\n{CYAN}Checking AgentDelegations container...{NC}\n")
        
        delegations_container = database.get_container_client("AgentDelegations")
        
        delegation_query = """
        SELECT * FROM c 
        WHERE c.agentId = 'ceo_log_agent_001' OR c.agentName = 'CEOLogAgent'
        ORDER BY c.timestamp DESC
        """
        
        delegations = []
        async for item in delegations_container.query_items(query=delegation_query):
            delegations.append(item)
        
        print(f"{GREEN}Found {len(delegations)} delegation records for CEO Log Agent{NC}")
        
        if delegations:
            print(f"\nRecent delegations:")
            for d in delegations[:3]:
                print(f"  • {d.get('timestamp')} - {d.get('delegationQuery', '')[:80]}...")
                print(f"    Status: {d.get('status')}, Response time: {d.get('responseTimeMs')}ms")
        
    except Exception as e:
        print(f"❌ Error querying Cosmos DB: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(check_cosmos_entries())