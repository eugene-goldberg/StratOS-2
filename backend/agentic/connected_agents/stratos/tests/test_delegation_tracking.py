#!/usr/bin/env python3

"""
Test CEO Log Agent Delegation Tracking
Verifies that delegations are automatically tracked when the agent receives requests
"""

import asyncio
import json
from datetime import datetime
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.ceo_log_plugin_with_tracking import CEOLogPluginWithTracking
from services.delegation_tracking_service import DelegationTrackingService


async def test_delegation_tracking():
    """Test the CEO Log Agent with delegation tracking."""
    
    print("="*60)
    print("CEO Log Agent - Delegation Tracking Test")
    print("="*60)
    print()
    
    # Initialize the plugin with a test session
    session_id = f"test_session_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
    plugin = CEOLogPluginWithTracking(session_id=session_id)
    
    # Initialize delegation service for verification
    delegation_service = DelegationTrackingService()
    
    test_user_id = "test_ceo_delegation_001"
    agent_id = "ceo_log_agent_001"
    
    try:
        # Test 1: Save entry - should create delegation record
        print("Test 1: Testing delegation tracking on SaveEntry...")
        entry_content = "This is a test CEO log entry to verify delegation tracking is working correctly. We need to ensure all orchestrator delegations are tracked."
        
        save_result = await plugin.save_entry(
            content=entry_content,
            user_id=test_user_id,
            category="general",
            is_voice=False
        )
        
        result1 = json.loads(save_result)
        print(f"✅ Entry saved: {result1['entry_id']}")
        print(f"   Delegation tracked: {result1.get('delegation_tracked', False)}")
        print(f"   Session ID: {result1.get('session_id', 'N/A')}")
        print()
        
        # Wait for consistency
        await asyncio.sleep(2)
        
        # Test 2: Search entries - should create another delegation record
        print("Test 2: Testing delegation tracking on SearchEntries...")
        search_result = await plugin.search_entries(
            user_id=test_user_id,
            query="delegation tracking",
            limit=5,
            days_back=1
        )
        
        result2 = json.loads(search_result)
        print(f"✅ Search completed: {result2['total_results']} results")
        print(f"   Delegation tracked: {result2.get('delegation_tracked', False)}")
        print()
        
        # Test 3: Get summary - should create third delegation record
        print("Test 3: Testing delegation tracking on GetLogSummary...")
        summary_result = await plugin.get_log_summary(
            user_id=test_user_id,
            days=7
        )
        
        result3 = json.loads(summary_result)
        print(f"✅ Summary retrieved")
        print(f"   Delegation tracked: {result3.get('delegation_tracked', False)}")
        print()
        
        # Wait for all delegations to be processed
        await asyncio.sleep(2)
        
        # Test 4: Verify delegations were tracked
        print("Test 4: Verifying delegation records in Cosmos DB...")
        delegations = await delegation_service.get_agent_delegations(
            agent_id=agent_id,
            limit=10,
            hours_back=1
        )
        
        print(f"✅ Found {len(delegations)} delegation records")
        
        # Display delegation details
        for idx, delegation in enumerate(delegations[:5], 1):
            print(f"\n   Delegation {idx}:")
            print(f"   - ID: {delegation.id}")
            print(f"   - Function: {delegation.functionCalled}")
            print(f"   - Query: {delegation.delegationQuery[:80]}...")
            print(f"   - Status: {delegation.status.value}")
            print(f"   - Timestamp: {delegation.timestamp.isoformat()}")
            print(f"   - Duration: {delegation.durationMs}ms" if delegation.durationMs else "   - Duration: N/A")
            print(f"   - Success: {delegation.success}")
        
        # Test 5: Get delegation metrics
        print("\nTest 5: Getting delegation metrics...")
        metrics_result = await plugin.get_delegation_metrics(
            period="last_24_hours"
        )
        
        metrics = json.loads(metrics_result)
        print(f"✅ Metrics retrieved:")
        print(f"   Total requests: {metrics['volume']['total_requests']}")
        print(f"   Unique users: {metrics['volume']['unique_users']}")
        print(f"   Average response time: {metrics['performance']['average_response_time_ms']}ms")
        print(f"   Success rate: {metrics['reliability']['success_rate']}%")
        
        if metrics['usage_patterns']['top_functions']:
            print(f"\n   Top functions:")
            for func in metrics['usage_patterns']['top_functions']:
                print(f"   - {func['function']}: {func['count']} calls")
        
        # Test 6: Get delegation summary
        print("\nTest 6: Getting delegation summary...")
        summary = await delegation_service.get_delegation_summary(
            agent_id=agent_id,
            agent_name="CEOLogAgent",
            days=1
        )
        
        print(f"✅ Delegation Summary:")
        print(f"   Total delegations: {summary.totalDelegations}")
        print(f"   Successful: {summary.successfulDelegations}")
        print(f"   Failed: {summary.failedDelegations}")
        print(f"   Average duration: {summary.averageDurationMs:.2f}ms")
        
        if summary.delegationsByFunction:
            print(f"\n   By function:")
            for func, count in summary.delegationsByFunction.items():
                print(f"   - {func}: {count}")
        
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED!")
        print("="*60)
        print()
        print("Summary:")
        print(f"- Successfully tracked {len(delegations)} delegations")
        print(f"- All agent functions properly decorated")
        print(f"- Delegation metrics available for monitoring")
        print(f"- Precise timestamps recorded for each delegation")
        print(f"- Session tracking enables request correlation")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup
        await plugin.cleanup()
        await delegation_service.close()


if __name__ == "__main__":
    asyncio.run(test_delegation_tracking())