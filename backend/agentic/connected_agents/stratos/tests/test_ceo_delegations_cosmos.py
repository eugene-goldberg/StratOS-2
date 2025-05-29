#!/usr/bin/env python3

"""
Test CEO Log Agent Delegations through Orchestrator
This script tests the CEO Log Agent via orchestrator delegation and then queries Cosmos DB
to show the delegation records that were created
"""

import asyncio
import json
from datetime import datetime, timedelta
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from base_agent_test import BaseAgentTest
from services.delegation_tracking_service import DelegationTrackingService
from services.cosmos_db_service import CosmosDBService
from azure.identity.aio import DefaultAzureCredential
from azure.ai.projects.aio import AIProjectClient
from semantic_kernel.agents import AzureAIAgent


class CEODelegationTest(BaseAgentTest):
    """Test CEO Log Agent delegations"""
    
    def __init__(self):
        super().__init__("CEO Log Agent")
        self.agent_key = "ceo_log"
    
    def get_test_scenarios(self):
        """Define test scenarios that will create CEO log entries"""
        return [
            {
                "name": "save_strategic_entry",
                "query": "Save this CEO log: We've made significant progress on our AI transformation. The team successfully deployed the new connected agents architecture. This positions us well for Q3 expansion.",
                "expected_function": "SaveEntry"
            },
            {
                "name": "save_risk_entry",
                "query": "Save this CEO log: I'm concerned about the increasing competition in the AI space. We need to accelerate our innovation timeline and consider strategic partnerships.",
                "expected_function": "SaveEntry"
            },
            {
                "name": "save_team_entry",
                "query": "Save this CEO log: Extremely proud of the engineering team's performance. They've shown exceptional dedication. Planning to expand the team by 20% next quarter.",
                "expected_function": "SaveEntry"
            },
            {
                "name": "search_ai_entries",
                "query": "Search my CEO logs for entries about AI and transformation",
                "expected_function": "SearchEntries"
            },
            {
                "name": "get_summary",
                "query": "Give me a summary of my CEO log entries from the past week",
                "expected_function": "GetLogSummary"
            }
        ]


async def show_cosmos_delegation_records():
    """Query and display delegation records from Cosmos DB"""
    print("\n" + "="*60)
    print("QUERYING COSMOS DB FOR DELEGATION RECORDS")
    print("="*60 + "\n")
    
    # Initialize services
    delegation_service = DelegationTrackingService()
    cosmos_service = CosmosDBService()
    
    try:
        await delegation_service.initialize()
        await cosmos_service.initialize()
        
        # Get recent delegations for CEO Log Agent
        agent_id = "ceo_log_agent_001"
        print(f"Fetching delegations for agent: {agent_id}")
        print("-" * 60)
        
        # Get delegations from the last hour
        delegations = await delegation_service.get_agent_delegations(
            agent_id=agent_id,
            limit=20,
            hours_back=1
        )
        
        print(f"\nFound {len(delegations)} delegation records in the last hour:\n")
        
        # Display each delegation
        for idx, delegation in enumerate(delegations, 1):
            print(f"Delegation {idx}:")
            print(f"  ID: {delegation.id}")
            print(f"  Timestamp: {delegation.timestamp}")
            print(f"  Function: {delegation.functionCalled}")
            print(f"  Query: {delegation.delegationQuery[:100]}...")
            print(f"  Status: {delegation.status.value}")
            print(f"  Duration: {delegation.durationMs}ms" if delegation.durationMs else "  Duration: In progress")
            print(f"  Success: {delegation.success}")
            print(f"  User ID: {delegation.userId}")
            print(f"  Session ID: {delegation.sessionId}")
            
            # Show parameters if it's a save operation
            if delegation.functionCalled == "save_entry" and delegation.parameters:
                print(f"  Category: {delegation.parameters.get('category', 'N/A')}")
            
            print()
        
        # Get summary statistics
        print("\n" + "-" * 60)
        print("DELEGATION SUMMARY")
        print("-" * 60)
        
        summary = await delegation_service.get_delegation_summary(
            agent_id=agent_id,
            agent_name="CEOLogAgent",
            days=1
        )
        
        print(f"Total delegations (24h): {summary.totalDelegations}")
        print(f"Successful: {summary.successfulDelegations}")
        print(f"Failed: {summary.failedDelegations}")
        print(f"Average duration: {summary.averageDurationMs:.2f}ms")
        
        if summary.delegationsByFunction:
            print("\nBy function:")
            for func, count in summary.delegationsByFunction.items():
                print(f"  - {func}: {count}")
        
        # Now show the actual CEO log entries that were created
        print("\n" + "="*60)
        print("CEO LOG ENTRIES IN COSMOS DB")
        print("="*60 + "\n")
        
        # Query recent CEO log entries
        recent_logs = await cosmos_service.get_user_logs(
            user_id="test-user",  # This is the default test user ID
            limit=10,
            start_date=datetime.utcnow() - timedelta(hours=1)
        )
        
        print(f"Found {len(recent_logs)} CEO log entries in the last hour:\n")
        
        for idx, log in enumerate(recent_logs, 1):
            print(f"Log Entry {idx}:")
            print(f"  ID: {log.id}")
            print(f"  Timestamp: {log.timestamp}")
            print(f"  Content: {log.logEntry.content[:100]}...")
            print(f"  Sentiment: {log.logEntry.sentiment.value if log.logEntry.sentiment else 'N/A'}")
            print(f"  Tags: {', '.join(log.tags[:5])}")
            print(f"  Themes: {', '.join(log.strategicThemes)}")
            
            if log.analysis:
                if log.analysis.actionItems:
                    print(f"  Action Items: {len(log.analysis.actionItems)}")
                if log.analysis.riskFactors:
                    print(f"  Risk Factors: {len(log.analysis.riskFactors)}")
            print()
        
    except Exception as e:
        print(f"Error querying Cosmos DB: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await delegation_service.close()
        await cosmos_service.close()


async def main():
    """Main test function"""
    print("CEO Log Agent Delegation Test with Cosmos DB Tracking")
    print("=" * 60)
    print()
    
    # Step 1: Run the CEO Log Agent tests through orchestrator
    print("STEP 1: Running CEO Log Agent tests through orchestrator...")
    print("-" * 60)
    
    test = CEODelegationTest()
    
    # Run each test scenario
    success = True
    scenarios = test.get_test_scenarios()
    
    # We need to manually run the test since we want multiple scenarios
    test.load_deployment_info()
    
    async with DefaultAzureCredential() as credential:
        async with AIProjectClient(
            endpoint=test.connection_string,
            credential=credential
        ) as client:
            # Get orchestrator
            orchestrator_def = await test.get_orchestrator_definition(client)
            orchestrator_agent = AzureAIAgent(
                client=client,
                definition=orchestrator_def
            )
            
            # Run each scenario
            for scenario in scenarios:
                print(f"\nRunning scenario: {scenario['name']}")
                print(f"Query: {scenario['query'][:100]}...")
                
                try:
                    response = await test.invoke_agent(
                        orchestrator_agent,
                        scenario['query'],
                        scenario['name']
                    )
                    print(f"Response: {response[:150]}...")
                except Exception as e:
                    print(f"Error: {e}")
                    success = False
    
    if success:
        print("\n✅ All CEO Log Agent tests completed")
    else:
        print("\n❌ Some tests failed")
    
    # Wait a moment for data to be written to Cosmos DB
    print("\nWaiting for Cosmos DB consistency...")
    await asyncio.sleep(3)
    
    # Step 2: Query and display the Cosmos DB records
    await show_cosmos_delegation_records()
    
    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())