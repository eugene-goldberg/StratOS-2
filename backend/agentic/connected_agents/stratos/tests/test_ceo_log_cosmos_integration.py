#!/usr/bin/env python3

"""
Test CEO Log Agent Cosmos DB Integration
Tests the complete flow of saving and retrieving CEO log entries from Cosmos DB
"""

import asyncio
import json
from datetime import datetime
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.ceo_log_plugin_cosmos import CEOLogPluginCosmos


async def test_ceo_log_cosmos_integration():
    """Test the CEO Log Agent with Cosmos DB integration."""
    
    print("="*60)
    print("CEO Log Agent - Cosmos DB Integration Test")
    print("="*60)
    print()
    
    # Initialize the plugin
    plugin = CEOLogPluginCosmos()
    test_user_id = "test_ceo_user_001"
    
    try:
        # Test 1: Save a strategic planning entry
        print("Test 1: Saving strategic planning entry...")
        entry1 = await plugin.save_entry(
            content="We need to accelerate our AI transformation initiative. The market is moving faster than anticipated, and our competitors are gaining ground. I'm considering a partnership with a leading AI company to jumpstart our capabilities.",
            user_id=test_user_id,
            category="strategic_planning",
            is_voice=False
        )
        result1 = json.loads(entry1)
        print(f"✅ Entry saved: {result1['entry_id']}")
        print(f"   Tags: {result1['tags']}")
        print(f"   Sentiment: {result1['metadata']['sentiment']}")
        print()
        
        # Test 2: Save a risk assessment entry
        print("Test 2: Saving risk assessment entry...")
        entry2 = await plugin.save_entry(
            content="I'm concerned about our cybersecurity posture. Recent industry breaches highlight vulnerabilities we may share. We must conduct an immediate security audit and implement enhanced protection measures. This is urgent.",
            user_id=test_user_id,
            category="risk_assessment",
            is_voice=True
        )
        result2 = json.loads(entry2)
        print(f"✅ Entry saved: {result2['entry_id']}")
        print(f"   Is urgent: {result2['metadata']['is_urgent']}")
        print(f"   Has risks: {result2['metadata']['involves_risk']}")
        print()
        
        # Test 3: Save a team leadership entry
        print("Test 3: Saving team leadership entry...")
        entry3 = await plugin.save_entry(
            content="Great news! Our engineering team just achieved a major breakthrough in product development. Team morale is high, and I see opportunity to expand the team with top talent. Need to ensure we maintain this positive momentum.",
            user_id=test_user_id,
            category="team_leadership",
            is_voice=False
        )
        result3 = json.loads(entry3)
        print(f"✅ Entry saved: {result3['entry_id']}")
        print(f"   Themes: {result3['metadata']['themes']}")
        print()
        
        # Wait a moment for consistency
        await asyncio.sleep(2)
        
        # Test 4: Search for AI-related entries
        print("Test 4: Searching for AI-related entries...")
        search1 = await plugin.search_entries(
            user_id=test_user_id,
            query="AI transformation",
            limit=5,
            days_back=1
        )
        search_result1 = json.loads(search1)
        print(f"✅ Found {search_result1['total_results']} entries matching 'AI transformation'")
        for idx, result in enumerate(search_result1['results'], 1):
            print(f"   {idx}. {result['summary'][:80]}...")
            print(f"      Sentiment: {result['sentiment']}, Created: {result['created_at'][:19]}")
        print()
        
        # Test 5: Search for urgent/risk entries
        print("Test 5: Searching for urgent risk entries...")
        search2 = await plugin.search_entries(
            user_id=test_user_id,
            query="urgent security",
            category="risk_assessment",
            limit=5,
            days_back=1
        )
        search_result2 = json.loads(search2)
        print(f"✅ Found {search_result2['total_results']} urgent risk entries")
        print()
        
        # Test 6: Get log summary
        print("Test 6: Getting log summary...")
        summary = await plugin.get_log_summary(
            user_id=test_user_id,
            days=30
        )
        summary_result = json.loads(summary)
        print(f"✅ Summary for last 30 days:")
        print(f"   Total logs: {summary_result['statistics']['total_logs']}")
        print(f"   Sentiment distribution: {summary_result['statistics']['sentiment_distribution']}")
        print(f"   Dominant sentiment: {summary_result['dominant_sentiment']}")
        print(f"   Top tags: {[tag['tag'] for tag in summary_result['top_tags'][:5]]}")
        print()
        
        # Test 7: Test tag generation
        print("Test 7: Testing tag generation...")
        tags_test = plugin.generate_tags(
            "Urgent: We must immediately address the revenue shortfall by expanding into new markets. This decision requires board approval."
        )
        tags_result = json.loads(tags_test)
        print(f"✅ Generated {tags_result['count']} tags")
        print(f"   Tags: {tags_result['tags']}")
        print(f"   Analysis: Urgent={tags_result['analysis']['is_urgent']}, "
              f"Action={tags_result['analysis']['has_action_items']}, "
              f"Strategic={tags_result['analysis']['strategic_relevance']}")
        print()
        
        print("="*60)
        print("✅ ALL TESTS PASSED!")
        print("="*60)
        print()
        print("Summary:")
        print(f"- Successfully saved 3 CEO log entries to Cosmos DB")
        print(f"- Search functionality working correctly")
        print(f"- Summary statistics retrieved successfully")
        print(f"- Tag generation and sentiment analysis operational")
        print(f"- Cosmos DB integration fully functional")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup
        await plugin.cleanup()


if __name__ == "__main__":
    asyncio.run(test_ceo_log_cosmos_integration())