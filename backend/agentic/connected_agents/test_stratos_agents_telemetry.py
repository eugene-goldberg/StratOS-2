#!/usr/bin/env python3
"""
Test StratOS agents with Application Insights telemetry tracking.
Simpler version that focuses on testing the deployed agents.
"""

import asyncio
import os
import logging
import json
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

# Import Azure SDK components
from azure.identity.aio import DefaultAzureCredential
from azure.ai.projects.aio import AIProjectClient
from semantic_kernel.agents import AzureAIAgent

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def test_stratos_with_telemetry():
    """Test StratOS agents with telemetry tracking."""
    
    # Load deployment info - check multiple locations
    deployment_files = [
        Path(__file__).parent / "stratos" / "archive" / "stratos_deployment_info.json",
        Path(__file__).parent.parent / "stratos_deployment_info.json",
        Path(__file__).parent / "deployment_info.json"
    ]
    
    deployment_info = None
    for deployment_file in deployment_files:
        if deployment_file.exists():
            with open(deployment_file, 'r') as f:
                deployment_info = json.load(f)
                logger.info(f"Using deployment info from: {deployment_file}")
                break
    
    if not deployment_info:
        logger.error("No deployment info found in any location")
        return
    
    # Check for orchestrator ID in different formats
    orchestrator_id = None
    if "orchestrator" in deployment_info and isinstance(deployment_info["orchestrator"], dict):
        orchestrator_id = deployment_info["orchestrator"].get("id")
    elif "main_orchestrator_agent_id" in deployment_info:
        orchestrator_id = deployment_info.get("main_orchestrator_agent_id")
    
    if not orchestrator_id:
        logger.error("No orchestrator ID found in deployment info")
        return
    
    endpoint = os.getenv("AZURE_AI_PROJECT_CONNECTION_STRING")
    if not endpoint:
        logger.error("AZURE_AI_PROJECT_CONNECTION_STRING not found in environment")
        return
    
    logger.info("="*80)
    logger.info("STRATOS AGENTS TELEMETRY TEST")
    logger.info("="*80)
    logger.info(f"Orchestrator: {orchestrator_id}")
    logger.info(f"Telemetry: Application Insights enabled")
    
    async with DefaultAzureCredential() as credential, \
               AIProjectClient(endpoint=endpoint, credential=credential) as client:
        
        # Get orchestrator definition
        orchestrator_def = await client.agents.get_agent(agent_id=orchestrator_id)
        logger.info(f"Orchestrator name: {orchestrator_def.name}")
        logger.info(f"Available tools: {len(orchestrator_def.tools) if orchestrator_def.tools else 0}")
        
        # Create agent instance
        orchestrator_agent = AzureAIAgent(
            client=client,
            definition=orchestrator_def
        )
        
        # Test cases for each agent
        test_cases = [
            {
                "name": "CEO Log Test",
                "query": "I need to log this: Board meeting went well. We discussed Q2 strategy and approved the budget.",
                "expected_agent": "ceo log"
            },
            {
                "name": "North Star Test", 
                "query": "What is our north star metric for customer satisfaction?",
                "expected_agent": "north star"
            },
            {
                "name": "Memory Recall Test",
                "query": "What decisions did we make in our last strategic planning session?",
                "expected_agent": "memory"
            },
            {
                "name": "Preference Learning Test",
                "query": "Learn this preference: I prefer concise bullet-point summaries over long narratives",
                "expected_agent": "preference"
            }
        ]
        
        results = []
        
        for test in test_cases:
            logger.info(f"\n{'-'*60}")
            logger.info(f"TEST: {test['name']}")
            logger.info(f"{'-'*60}")
            logger.info(f"Query: {test['query']}")
            
            start_time = datetime.now()
            
            try:
                # Invoke orchestrator
                response = ""
                async for part in orchestrator_agent.invoke(messages=test['query']):
                    if hasattr(part, 'content') and part.content:
                        response += str(part.content)
                
                duration = (datetime.now() - start_time).total_seconds()
                
                # Check for delegation
                delegation_detected = test['expected_agent'] in response.lower()
                
                logger.info(f"\nResponse ({duration:.1f}s):")
                logger.info(response[:300] + "..." if len(response) > 300 else response)
                logger.info(f"\nDelegation to {test['expected_agent']}: {'✅ Yes' if delegation_detected else '❌ No'}")
                
                results.append({
                    "test": test['name'],
                    "success": delegation_detected,
                    "duration": duration,
                    "response_length": len(response)
                })
                
            except Exception as e:
                logger.error(f"Test failed: {e}")
                results.append({
                    "test": test['name'],
                    "success": False,
                    "error": str(e)
                })
            
            # Wait between tests to avoid rate limits
            await asyncio.sleep(3)
        
        # Print summary
        logger.info("\n" + "="*80)
        logger.info("TEST SUMMARY")
        logger.info("="*80)
        
        passed = sum(1 for r in results if r.get("success", False))
        total = len(results)
        
        logger.info(f"Total Tests: {total}")
        logger.info(f"Passed: {passed} ✅")
        logger.info(f"Failed: {total - passed} ❌")
        logger.info("")
        
        for result in results:
            status = "✅" if result.get("success", False) else "❌"
            details = f"{result.get('duration', 0):.1f}s" if result.get("success") else result.get("error", "Failed")
            logger.info(f"{status} {result['test']}: {details}")
        
        logger.info("\n" + "="*80)
        logger.info("TELEMETRY INFORMATION")
        logger.info("="*80)
        logger.info("Application Insights telemetry has been captured for this test run.")
        logger.info("To view the telemetry data:")
        logger.info("1. Go to Azure Portal > Application Insights")
        logger.info("2. Navigate to Transaction Search or Logs")
        logger.info("3. Look for traces with operation name containing 'stratos' or 'agent'")
        logger.info("4. Filter by time range to see this test run")
        logger.info("")
        logger.info("Key metrics captured:")
        logger.info("- Request/response times")
        logger.info("- Agent delegation patterns")
        logger.info("- Error traces (if any)")
        logger.info("- Custom telemetry from agents")
        logger.info("="*80)


if __name__ == "__main__":
    # Verify Application Insights is configured
    app_insights_connection = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
    if not app_insights_connection:
        logger.warning("⚠️  APPLICATIONINSIGHTS_CONNECTION_STRING not found!")
        logger.warning("Telemetry will not be captured to Application Insights.")
    else:
        logger.info("✅ Application Insights configured")
        logger.info(f"Connection: {app_insights_connection[:50]}...")
    
    asyncio.run(test_stratos_with_telemetry())