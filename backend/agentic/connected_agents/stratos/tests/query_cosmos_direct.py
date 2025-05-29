#!/usr/bin/env python3

"""
Query Cosmos DB directly to show CEO Log entries and delegations
Uses connection string directly for testing purposes
"""

import asyncio
import os
from datetime import datetime, timedelta
from azure.cosmos.aio import CosmosClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


async def query_cosmos_db():
    """Query Cosmos DB to show CEO log entries and delegation records"""
    
    print("="*60)
    print("QUERYING COSMOS DB DIRECTLY")
    print("="*60)
    print()
    
    # For testing, we'll use the connection string directly
    # In production, this should come from Key Vault
    connection_string = os.environ.get("COSMOS_CONNECTION_STRING")
    
    if not connection_string:
        print("❌ COSMOS_CONNECTION_STRING environment variable not set")
        print("Please set it to query Cosmos DB")
        return
    
    client = CosmosClient.from_connection_string(connection_string)
    
    try:
        database = client.get_database_client("StratOSData")
        
        # Query CEO Log Entries
        print("CEO LOG ENTRIES")
        print("-" * 60)
        
        ceo_logs_container = database.get_container_client("CEOLogs")
        
        # Get recent CEO log entries
        query = """
        SELECT * FROM c 
        WHERE c.timestamp >= @startTime
        ORDER BY c.timestamp DESC
        """
        
        start_time = datetime.utcnow() - timedelta(hours=1)
        parameters = [{"name": "@startTime", "value": start_time.isoformat()}]
        
        print(f"Querying CEO logs from the last hour...")
        
        logs = []
        async for item in ceo_logs_container.query_items(
            query=query,
            parameters=parameters
        ):
            logs.append(item)
        
        print(f"\nFound {len(logs)} CEO log entries:\n")
        
        for idx, log in enumerate(logs[:10], 1):
            print(f"Log Entry {idx}:")
            print(f"  ID: {log.get('id')}")
            print(f"  Timestamp: {log.get('timestamp')}")
            print(f"  User ID: {log.get('userId')}")
            
            # Log entry content
            if 'logEntry' in log:
                content = log['logEntry'].get('content', '')
                print(f"  Content: {content[:100]}...")
                print(f"  Sentiment: {log['logEntry'].get('sentiment', 'N/A')}")
            
            # Tags and themes
            tags = log.get('tags', [])
            if tags:
                print(f"  Tags: {', '.join(tags[:5])}")
            
            themes = log.get('strategicThemes', [])
            if themes:
                print(f"  Themes: {', '.join(themes)}")
            
            # Analysis
            if 'analysis' in log:
                analysis = log['analysis']
                action_items = analysis.get('actionItems', [])
                risk_factors = analysis.get('riskFactors', [])
                if action_items:
                    print(f"  Action Items: {len(action_items)}")
                if risk_factors:
                    print(f"  Risk Factors: {len(risk_factors)}")
            
            print()
        
        # Query Agent Delegations
        print("\n" + "="*60)
        print("AGENT DELEGATIONS")
        print("-" * 60)
        
        try:
            delegations_container = database.get_container_client("AgentDelegations")
            
            # Check if container exists by trying to read it
            await delegations_container.read()
            
            # Get recent delegations for CEO Log Agent
            delegation_query = """
            SELECT * FROM c 
            WHERE c.agentId = @agentId
            AND c.timestamp >= @startTime
            ORDER BY c.timestamp DESC
            """
            
            delegation_params = [
                {"name": "@agentId", "value": "ceo_log_agent_001"},
                {"name": "@startTime", "value": start_time.isoformat()}
            ]
            
            print(f"Querying delegations for CEO Log Agent from the last hour...")
            
            delegations = []
            async for item in delegations_container.query_items(
                query=delegation_query,
                parameters=delegation_params
            ):
                delegations.append(item)
            
            print(f"\nFound {len(delegations)} delegation records:\n")
            
            for idx, delegation in enumerate(delegations[:10], 1):
                print(f"Delegation {idx}:")
                print(f"  ID: {delegation.get('id')}")
                print(f"  Timestamp: {delegation.get('timestamp')}")
                print(f"  Function: {delegation.get('functionCalled')}")
                print(f"  Query: {delegation.get('delegationQuery', '')[:80]}...")
                print(f"  Status: {delegation.get('status')}")
                print(f"  Duration: {delegation.get('durationMs')}ms" if delegation.get('durationMs') else "  Duration: N/A")
                print(f"  Success: {delegation.get('success')}")
                print(f"  User ID: {delegation.get('userId')}")
                print()
                
        except Exception as e:
            print(f"AgentDelegations container not found or error: {e}")
            print("This is expected if delegation tracking hasn't been set up yet")
        
    except Exception as e:
        print(f"Error querying Cosmos DB: {e}")
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(query_cosmos_db())