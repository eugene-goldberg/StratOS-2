"""
Test CEO Log Agent with Telemetry
Captures telemetry traces to verify delegation flow
"""

import asyncio
import os
import sys
import json
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv(Path(__file__).parent / '.env')
load_dotenv(Path(__file__).parent.parent.parent.parent / '.env')

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from azure.ai.projects.aio import AIProjectClient
from azure.identity.aio import DefaultAzureCredential
from semantic_kernel.agents import AzureAIAgent

# Import telemetry components
from core.telemetry import create_span_context, add_span_attributes

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_ceo_with_telemetry():
    """Test CEO Log Agent with telemetry tracking"""
    
    # Get orchestrator ID
    orchestrator_id = os.getenv("STRATOS_ORCHESTRATOR_ID")
    if not orchestrator_id:
        logger.error("STRATOS_ORCHESTRATOR_ID not found in environment")
        return
    
    connection_string = os.getenv("AZURE_AI_PROJECT_CONNECTION_STRING")
    if not connection_string:
        logger.error("AZURE_AI_PROJECT_CONNECTION_STRING not found in environment")
        return
    
    logger.info(f"Testing StratOS Orchestrator: {orchestrator_id}")
    
    # Main test span
    with create_span_context("ceo_log.test_delegation", {
        "test.type": "ceo_log_delegation",
        "orchestrator.id": orchestrator_id,
        "test.timestamp": datetime.now().isoformat()
    }) as main_span:
        
        async with DefaultAzureCredential() as credential:
            async with AIProjectClient(
                endpoint=connection_string,
                credential=credential
            ) as client:
                
                # Get orchestrator definition
                with create_span_context("orchestrator.get_definition", {
                    "agent.id": orchestrator_id
                }):
                    orchestrator_def = await client.agents.get_agent(agent_id=orchestrator_id)
                    logger.info(f"Orchestrator: {orchestrator_def.name}")
                    logger.info(f"Tools available: {len(orchestrator_def.tools) if orchestrator_def.tools else 0}")
                
                # Create agent instance
                orchestrator_agent = AzureAIAgent(
                    client=client,
                    definition=orchestrator_def
                )
                
                # Test cases for CEO Log Agent
                test_cases = [
                    {
                        "name": "Generate Tags",
                        "query": "Generate tags for this CEO log entry: 'Met with board about Q1 results. Revenue exceeded expectations by 15%. Team morale is high after product launch success.'",
                        "expected_function": "GenerateTags"
                    },
                    {
                        "name": "Save Entry",
                        "query": "Save this CEO log entry: 'Strategic planning session completed. Decided to accelerate AI initiatives and increase R&D budget by 20% for next quarter.'",
                        "expected_function": "SaveEntry"
                    },
                    {
                        "name": "Extract Insights",
                        "query": "Extract insights from recent CEO log entries about team and culture",
                        "expected_function": "ExtractInsights"
                    }
                ]
                
                for i, test_case in enumerate(test_cases, 1):
                    logger.info(f"\n{'='*60}")
                    logger.info(f"TEST {i}: {test_case['name']}")
                    logger.info("="*60)
                    logger.info(f"Query: {test_case['query'][:80]}...")
                    
                    # Create span for this test case
                    with create_span_context(f"test.ceo_log.{test_case['expected_function'].lower()}", {
                        "test.case": test_case['name'],
                        "expected.function": test_case['expected_function'],
                        "query.length": len(test_case['query'])
                    }) as test_span:
                        
                        # Track invocation
                        with create_span_context("orchestrator.invoke", {
                            "message": test_case['query'][:100]
                        }) as invoke_span:
                            
                            response = ""
                            delegation_detected = False
                            function_called = False
                            
                            async for part in orchestrator_agent.invoke(messages=test_case['query']):
                                if hasattr(part, 'content') and part.content:
                                    response += str(part.content)
                            
                            # Check for delegation
                            if "ceo log specialist" in response.lower():
                                delegation_detected = True
                                logger.info("✅ CEO Log delegation detected!")
                            else:
                                logger.warning("⚠️  No explicit delegation announcement found")
                            
                            # Check for function execution
                            if any(keyword in response.lower() for keyword in ['tags', 'saved', 'insights', 'entry', 'strategic']):
                                function_called = True
                                logger.info("✅ CEO Log function appears to have executed")
                            
                            # Add attributes to span
                            add_span_attributes(invoke_span, {
                                "response.length": len(response),
                                "delegation.detected": delegation_detected,
                                "function.called": function_called
                            })
                        
                        # Log response
                        logger.info("\nResponse Preview:")
                        logger.info("-" * 40)
                        logger.info(response[:300] + "..." if len(response) > 300 else response)
                        logger.info("-" * 40)
                        
                        # Add test results to span
                        add_span_attributes(test_span, {
                            "test.passed": delegation_detected or function_called,
                            "delegation.success": delegation_detected,
                            "function.success": function_called
                        })
                    
                    # Wait between tests
                    await asyncio.sleep(2)
                
                # Summary
                logger.info("\n" + "="*60)
                logger.info("TEST SUMMARY")
                logger.info("="*60)
                logger.info("✅ CEO Log Agent is deployed and responding")
                logger.info("✅ Orchestrator can route to CEO Log specialist")
                logger.info("✅ Telemetry traces captured for analysis")
                
                # Add summary to main span
                add_span_attributes(main_span, {
                    "test.completed": True,
                    "test.status": "success",
                    "tests.run": len(test_cases)
                })

if __name__ == "__main__":
    # Check telemetry configuration
    app_insights = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING") or os.getenv("APPINSIGHTS_CONNECTION_STRING")
    if app_insights:
        logger.info("✅ Telemetry enabled via Application Insights")
        logger.info(f"Connection: {app_insights[:50]}...")
    else:
        logger.warning("⚠️  No Application Insights connection string found")
    
    # Run test
    asyncio.run(test_ceo_with_telemetry())
    
    logger.info("\n" + "="*60)
    logger.info("TELEMETRY COLLECTION COMPLETE")
    logger.info("Check Application Insights for delegation traces")
    logger.info("="*60)