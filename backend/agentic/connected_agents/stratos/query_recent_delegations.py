#!/usr/bin/env python3
import asyncio
from datetime import datetime, timedelta
from services.delegation_tracking_service import DelegationTrackingService
import json

async def query_recent_delegations():
    """Query Cosmos DB for delegations created in the last 5 minutes"""
    tracking = DelegationTrackingService()
    
    try:
        # Query for delegations in the last 5 minutes
        await tracking.initialize()
        
        print(f"\n{'='*60}")
        print(f"QUERYING DELEGATIONS FROM LAST 5 MINUTES")
        print(f"{'='*60}\n")
        
        # Get delegations from the last 5 minutes (0.083 hours)
        delegations = await tracking.get_agent_delegations(
            agent_id="ceo_log_agent_001",
            hours_back=0.083,  # 5 minutes
            limit=50
        )
        
        if delegations:
            print(f"Found {len(delegations)} delegation(s) in the last 5 minutes:\n")
            
            for i, delegation in enumerate(delegations, 1):
                print(f"Delegation {i}:")
                print(f"  ID: {delegation.id}")
                print(f"  Timestamp: {delegation.timestamp}")
                print(f"  Agent ID: {delegation.agentId}")
                print(f"  Function: {delegation.functionCalled}")
                print(f"  Status: {delegation.status}")
                print(f"  Duration: {delegation.durationMs}ms" if delegation.durationMs else "  Duration: N/A")
                print(f"  Success: {delegation.success}")
                print(f"  User ID: {delegation.userId}")
                print(f"  Session ID: {delegation.sessionId}")
                if delegation.metadata and delegation.metadata.get('category'):
                    print(f"  Category: {delegation.metadata['category']}")
                print()
        else:
            print("❌ No delegations found in the last 5 minutes")
            print("\nQuerying ALL delegations to verify connection...")
            
            # Query all delegations
            all_delegations = await tracking.get_agent_delegations("ceo_log_agent_001", hours_back=24)
            print(f"\nTotal delegations in database: {len(all_delegations)}")
            
            if all_delegations:
                latest = sorted(all_delegations, key=lambda x: x.timestamp, reverse=True)[0]
                print(f"Most recent delegation: {latest.timestamp} ({latest.functionCalled})")
                
    finally:
        await tracking.close()

if __name__ == "__main__":
    asyncio.run(query_recent_delegations())