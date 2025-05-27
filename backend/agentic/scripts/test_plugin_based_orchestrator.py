#!/usr/bin/env python3
"""
Test the plugin-based orchestrator with all 15 specialist agents.
"""

import asyncio
import os
import sys
import logging
from typing import List, Dict

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [%(funcName)s] %(message)s')
logger = logging.getLogger(__name__)

# Add parent directories to path
current_dir = os.path.dirname(os.path.abspath(__file__))
agentic_dir = os.path.dirname(current_dir)
backend_dir = os.path.dirname(agentic_dir)
sys.path.insert(0, agentic_dir)
sys.path.insert(0, backend_dir)

# Import the orchestrator
from agents.plugin_based_orchestrator.main_orchestrator import setup_orchestrator_environment_and_agent

# Test cases for each agent
TEST_CASES = [
    # Strategic Foundation & Insights System
    {
        "request": "I need to record a strategic decision about expanding into the Asian market",
        "expected_agent": "CEOLogAgent",
        "description": "CEO strategic decision logging"
    },
    {
        "request": "What is our company's vision and mission statement?",
        "expected_agent": "NorthStarAgent",
        "description": "Vision and mission query"
    },
    {
        "request": "Analyze the patterns in our recent market data and provide insights",
        "expected_agent": "InsightSynthesisAgent",
        "description": "Insight synthesis request"
    },
    {
        "request": "What decisions did I make about product strategy last quarter?",
        "expected_agent": "CEOMemoryAgent",
        "description": "Memory recall request"
    },
    {
        "request": "Learn my communication style preferences for board presentations",
        "expected_agent": "CEOPreferenceLearningAgent",
        "description": "Preference learning request"
    },
    
    # Analysis & Intelligence System
    {
        "request": "Perform a SWOT analysis for our new product line",
        "expected_agent": "SWOTTOWSAgent",
        "description": "SWOT analysis request"
    },
    {
        "request": "What are the key risks in our supply chain strategy?",
        "expected_agent": "RiskOpportunityAgent",
        "description": "Risk analysis request"
    },
    {
        "request": "Route this strategic analysis request to the appropriate team",
        "expected_agent": "StrategicContextRouter",
        "description": "Strategic routing request"
    },
    {
        "request": "Link my observation about customer satisfaction to our NPS scores",
        "expected_agent": "SOLinkageAgent",
        "description": "Subjective-objective linkage"
    },
    
    # Planning & Execution System
    {
        "request": "Coordinate the planning for our Q2 strategic initiatives",
        "expected_agent": "PlanningCoordinator",
        "description": "Planning coordination"
    },
    {
        "request": "Generate initiatives to achieve our 20% growth target",
        "expected_agent": "InitiativeGenerator",
        "description": "Initiative generation"
    },
    {
        "request": "Optimize resource allocation across our three main projects",
        "expected_agent": "ResourceOptimizer",
        "description": "Resource optimization"
    },
    {
        "request": "Create a timeline for the product launch milestones",
        "expected_agent": "TimelineStrategist",
        "description": "Timeline development"
    },
    {
        "request": "Map the dependencies between our technology and marketing initiatives",
        "expected_agent": "DependencyMapper",
        "description": "Dependency analysis"
    },
    {
        "request": "Track the execution progress of our digital transformation initiative",
        "expected_agent": "ExecutionTracker",
        "description": "Execution tracking"
    }
]

async def test_orchestrator_routing(orchestrator_agent, test_case: Dict) -> Dict:
    """Test a single routing case with the orchestrator."""
    logger.info(f"\n{'='*80}")
    logger.info(f"Testing: {test_case['description']}")
    logger.info(f"Request: {test_case['request']}")
    logger.info(f"Expected Agent: {test_case['expected_agent']}")
    
    try:
        # Send request to orchestrator
        full_response = ""
        async for message_fragment in orchestrator_agent.invoke_stream(input=test_case['request'], chat_history=[]):
            content_part = ""
            if isinstance(message_fragment, list) and message_fragment:
                if hasattr(message_fragment[0], 'content') and message_fragment[0].content:
                    content_part = message_fragment[0].content
            elif hasattr(message_fragment, 'content') and message_fragment.content:
                content_part = message_fragment.content
            
            if content_part:
                full_response += content_part
        
        # Check if the expected agent was mentioned in the response
        success = test_case['expected_agent'] in full_response
        
        result = {
            "test_case": test_case['description'],
            "request": test_case['request'],
            "expected_agent": test_case['expected_agent'],
            "response": full_response[:500] + "..." if len(full_response) > 500 else full_response,
            "success": success,
            "error": None
        }
        
        if success:
            logger.info(f"✅ Success: Correctly routed to {test_case['expected_agent']}")
        else:
            logger.warning(f"❌ Failed: Did not route to {test_case['expected_agent']}")
            logger.warning(f"Response: {full_response[:200]}...")
        
        return result
        
    except Exception as e:
        logger.error(f"Error testing {test_case['description']}: {str(e)}")
        return {
            "test_case": test_case['description'],
            "request": test_case['request'],
            "expected_agent": test_case['expected_agent'],
            "response": None,
            "success": False,
            "error": str(e)
        }

async def run_all_tests():
    """Run all test cases against the orchestrator."""
    logger.info("Setting up plugin-based orchestrator...")
    
    # Setup orchestrator
    orchestrator_agent = await setup_orchestrator_environment_and_agent()
    
    if not orchestrator_agent:
        logger.error("Failed to setup orchestrator. Exiting.")
        return
    
    logger.info("Orchestrator setup complete. Running tests...")
    
    # Run all test cases
    results = []
    for test_case in TEST_CASES:
        result = await test_orchestrator_routing(orchestrator_agent, test_case)
        results.append(result)
        await asyncio.sleep(2)  # Small delay between tests
    
    # Print summary
    logger.info(f"\n{'='*80}")
    logger.info("TEST SUMMARY")
    logger.info(f"{'='*80}")
    
    successful_tests = sum(1 for r in results if r['success'])
    total_tests = len(results)
    success_rate = (successful_tests / total_tests) * 100 if total_tests > 0 else 0
    
    logger.info(f"Total Tests: {total_tests}")
    logger.info(f"Successful: {successful_tests}")
    logger.info(f"Failed: {total_tests - successful_tests}")
    logger.info(f"Success Rate: {success_rate:.1f}%")
    
    # Print failed tests
    failed_tests = [r for r in results if not r['success']]
    if failed_tests:
        logger.info(f"\nFAILED TESTS:")
        for test in failed_tests:
            logger.info(f"- {test['test_case']}: Expected {test['expected_agent']}")
            if test['error']:
                logger.info(f"  Error: {test['error']}")
    
    return results

if __name__ == "__main__":
    asyncio.run(run_all_tests())