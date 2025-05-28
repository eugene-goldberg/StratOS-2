"""
Example: How to Create a Test for a New Agent
This shows how easy it is to add tests for new agents using the unified system
"""

import asyncio
from base_agent_test import BaseAgentTest
from typing import List, Dict


class PreferenceLearningAgentTest(BaseAgentTest):
    """Example test for Preference Learning Agent (not yet implemented)"""
    
    def __init__(self):
        super().__init__("Preference Learning Agent")
    
    def get_test_scenarios(self) -> List[Dict[str, str]]:
        """Define test scenarios for Preference Learning Agent"""
        return [
            {
                "name": "learn_preference",
                "query": "Learn this preference: I prefer morning meetings over afternoon ones"
            },
            {
                "name": "apply_preferences",
                "query": "Based on my preferences, when should we schedule our strategy session?"
            },
            {
                "name": "preference_patterns",
                "query": "What patterns have you noticed in my decision-making preferences?"
            }
        ]


# Example of how to use it
async def main():
    """Example usage"""
    # Create test instance
    test = PreferenceLearningAgentTest()
    
    # Run simple test (first scenario only)
    print("Running simple test...")
    success = await test.run_simple_test()
    print(f"Simple test {'passed' if success else 'failed'}")
    
    # Run comprehensive test (all scenarios)
    print("\nRunning comprehensive test...")
    success = await test.run_comprehensive_test()
    print(f"Comprehensive test {'passed' if success else 'failed'}")


if __name__ == "__main__":
    # This would fail since Preference Learning Agent isn't deployed yet
    # But it shows how easy it is to add new agent tests
    try:
        asyncio.run(main())
    except FileNotFoundError:
        print("\n⚠️ This is just an example - Preference Learning Agent not deployed yet")
        print("Once deployed, this test will work automatically!")