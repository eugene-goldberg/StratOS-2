"""
CEO Log Agent Test - Using Unified Telemetry
Example of updating existing test to use consolidated telemetry system
"""

import asyncio
from base_agent_test import BaseAgentTest
from typing import List, Dict


class CEOLogAgentUnifiedTest(BaseAgentTest):
    """CEO Log Agent test using unified telemetry"""
    
    def __init__(self):
        super().__init__("CEO Log Agent")
        # Agent ID will be loaded from deployment info
        self.agent_key = "ceo_log"
    
    def get_test_scenarios(self) -> List[Dict[str, str]]:
        """Define CEO Log test scenarios"""
        return [
            {
                "name": "tag_generation",
                "query": "Generate tags for this CEO log entry: 'Team meeting went well. Discussed Q2 roadmap and AI strategy.'",
                "expected_function": "GenerateTags"
            },
            {
                "name": "summarize_entry",
                "query": "Summarize this strategic log: 'Met with board to discuss expansion plans. Key focus on Asian markets, particularly Japan and Singapore. Budget approved for $5M investment.'",
                "expected_function": "SummarizeEntry"
            },
            {
                "name": "extract_insights",
                "query": "What strategic insights can you extract from recent CEO communications about digital transformation?",
                "expected_function": "ExtractInsights"
            },
            {
                "name": "analyze_patterns",
                "query": "Analyze patterns in my leadership communication style over the past month",
                "expected_function": "AnalyzePatterns"
            },
            {
                "name": "save_entry",
                "query": "Save this CEO log: Great progress on AI initiative today. Team is motivated and on track.",
                "expected_function": "SaveEntry"
            }
        ]


async def main():
    """Run CEO Log agent tests"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test CEO Log Agent with Unified Telemetry")
    parser.add_argument(
        "--type",
        choices=["simple", "comprehensive"],
        default="simple",
        help="Test type to run (default: simple)"
    )
    
    args = parser.parse_args()
    
    # Create and run test
    test = CEOLogAgentUnifiedTest()
    
    if args.type == "simple":
        success = await test.run_simple_test()
    else:
        success = await test.run_comprehensive_test()
    
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)