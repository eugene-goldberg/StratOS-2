"""
Unified Test Script for All StratOS Connected Agents
Uses the consolidated telemetry system to test all agents
"""

import asyncio
import logging
from typing import List, Dict
from base_agent_test import BaseAgentTest

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class CEOLogAgentTest(BaseAgentTest):
    """Test implementation for CEO Log Agent"""
    
    def __init__(self):
        super().__init__("CEO Log Agent")
    
    def get_test_scenarios(self) -> List[Dict[str, str]]:
        return [
            {
                "name": "tag_generation",
                "query": "Generate tags for this CEO log entry: 'Team meeting went well. Discussed Q2 roadmap and AI strategy.'"
            },
            {
                "name": "summarize_entry",
                "query": "Summarize this strategic log: 'Met with board to discuss expansion plans. Key focus on Asian markets.'"
            },
            {
                "name": "extract_insights",
                "query": "What strategic insights can you extract from recent CEO communications about digital transformation?"
            }
        ]


class NorthStarAgentTest(BaseAgentTest):
    """Test implementation for North Star Agent"""
    
    def __init__(self):
        super().__init__("North Star Agent")
    
    def get_test_scenarios(self) -> List[Dict[str, str]]:
        return [
            {
                "name": "purpose_definition",
                "query": "Help me define our organizational purpose. We want to make AI accessible to everyone."
            },
            {
                "name": "vision_creation",
                "query": "Create a vision statement for becoming the global leader in AI by 2030"
            },
            {
                "name": "values_management",
                "query": "What core values should guide our AI development efforts?"
            },
            {
                "name": "goal_setting",
                "query": "Set strategic goals for our digital transformation initiative"
            }
        ]


class MemoryRecallAgentTest(BaseAgentTest):
    """Test implementation for Memory Recall Agent"""
    
    def __init__(self):
        super().__init__("Memory Recall Agent")
    
    def get_test_scenarios(self) -> List[Dict[str, str]]:
        return [
            {
                "name": "pattern_recognition",
                "query": "Identify patterns in our strategic decision-making over the past quarter"
            },
            {
                "name": "context_retrieval",
                "query": "Search for any previous initiatives related to customer experience improvements"
            },
            {
                "name": "historical_analysis",
                "query": "Analyze how our strategic priorities have evolved over the last 90 days"
            },
            {
                "name": "similarity_search",
                "query": "Find similar situations where we successfully pivoted our product strategy"
            }
        ]


async def test_single_agent(agent_test_class, test_type: str = "simple") -> bool:
    """
    Test a single agent
    
    Args:
        agent_test_class: Test class for the agent
        test_type: "simple" or "comprehensive"
        
    Returns:
        True if test passed
    """
    test = agent_test_class()
    
    if test_type == "simple":
        return await test.run_simple_test()
    else:
        return await test.run_comprehensive_test()


async def test_all_agents(test_type: str = "simple") -> Dict[str, bool]:
    """
    Test all configured agents
    
    Args:
        test_type: "simple" or "comprehensive"
        
    Returns:
        Dictionary of agent names to test results
    """
    logger.info(f"\n{'='*60}")
    logger.info(f"Running {test_type.upper()} tests for all StratOS agents")
    logger.info(f"{'='*60}\n")
    
    # Define all agent tests
    agent_tests = [
        CEOLogAgentTest,
        NorthStarAgentTest,
        MemoryRecallAgentTest
    ]
    
    results = {}
    
    for agent_test_class in agent_tests:
        try:
            agent_name = agent_test_class().agent_name
            logger.info(f"\n🔍 Testing {agent_name}...")
            
            success = await test_single_agent(agent_test_class, test_type)
            results[agent_name] = success
            
            # Longer pause between agents to avoid rate limits
            logger.info("⏳ Waiting 15 seconds before next agent to avoid rate limits...")
            await asyncio.sleep(15)
            
        except Exception as e:
            logger.error(f"Failed to test {agent_test_class.__name__}: {str(e)}")
            results[agent_test_class.__name__] = False
    
    # Print summary
    logger.info(f"\n{'='*60}")
    logger.info("TEST SUMMARY")
    logger.info(f"{'='*60}")
    
    passed = sum(1 for success in results.values() if success)
    total = len(results)
    
    for agent_name, success in results.items():
        status = "✅ PASSED" if success else "❌ FAILED"
        logger.info(f"{agent_name}: {status}")
    
    logger.info(f"\nTotal: {passed}/{total} agents passed")
    logger.info(f"{'='*60}")
    
    return results


async def main():
    """Main test runner"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test StratOS Connected Agents")
    parser.add_argument(
        "--agent",
        choices=["ceo", "northstar", "memory", "all"],
        default="all",
        help="Which agent to test (default: all)"
    )
    parser.add_argument(
        "--type",
        choices=["simple", "comprehensive"],
        default="simple",
        help="Test type to run (default: simple)"
    )
    
    args = parser.parse_args()
    
    # Map agent names to test classes
    agent_map = {
        "ceo": CEOLogAgentTest,
        "northstar": NorthStarAgentTest,
        "memory": MemoryRecallAgentTest
    }
    
    if args.agent == "all":
        results = await test_all_agents(args.type)
        success = all(results.values())
    else:
        agent_test_class = agent_map[args.agent]
        success = await test_single_agent(agent_test_class, args.type)
    
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)