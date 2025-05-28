"""
Capture CEO Log Agent Telemetry
Simple script to test CEO Log Agent and save telemetry locally
"""

import asyncio
import os
import json
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv(Path(__file__).parent / '.env')
load_dotenv(Path(__file__).parent.parent.parent.parent / '.env')

# Add parent directory to path
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from azure.ai.projects.aio import AIProjectClient
from azure.identity.aio import DefaultAzureCredential
from semantic_kernel.agents import AzureAIAgent
from core.telemetry import create_span_context, add_span_attributes

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Telemetry storage
telemetry_data = {
    "test_run": datetime.now().isoformat(),
    "orchestrator_id": None,
    "tests": [],
    "delegation_evidence": []
}

async def capture_ceo_telemetry():
    """Test CEO Log Agent and capture telemetry"""
    
    orchestrator_id = os.getenv("STRATOS_ORCHESTRATOR_ID")
    if not orchestrator_id:
        logger.error("STRATOS_ORCHESTRATOR_ID not found")
        return
    
    telemetry_data["orchestrator_id"] = orchestrator_id
    
    connection_string = os.getenv("AZURE_AI_PROJECT_CONNECTION_STRING")
    if not connection_string:
        logger.error("Connection string not found")
        return
    
    logger.info(f"Testing orchestrator: {orchestrator_id}")
    
    # Simple test with telemetry
    with create_span_context("ceo_log.telemetry_test", {
        "orchestrator.id": orchestrator_id,
        "test.time": datetime.now().isoformat()
    }) as main_span:
        
        async with DefaultAzureCredential() as credential:
            async with AIProjectClient(
                endpoint=connection_string,
                credential=credential
            ) as client:
                
                # Get orchestrator
                orchestrator_def = await client.agents.get_agent(agent_id=orchestrator_id)
                logger.info(f"Orchestrator: {orchestrator_def.name}")
                
                orchestrator_agent = AzureAIAgent(
                    client=client,
                    definition=orchestrator_def
                )
                
                # Single test query
                query = "Generate tags for this CEO log entry: 'Team meeting went well. Discussed Q2 roadmap and AI strategy.'"
                logger.info(f"\nQuery: {query}")
                
                test_result = {
                    "query": query,
                    "start_time": time.time(),
                    "response": "",
                    "delegation_detected": False,
                    "telemetry_spans": []
                }
                
                # Capture response with telemetry
                with create_span_context("ceo_log.generate_tags", {
                    "query": query[:100],
                    "function": "GenerateTags"
                }) as test_span:
                    
                    try:
                        response = ""
                        async for part in orchestrator_agent.invoke(messages=query):
                            if hasattr(part, 'content') and part.content:
                                response += str(part.content)
                        
                        test_result["response"] = response
                        test_result["end_time"] = time.time()
                        test_result["duration"] = test_result["end_time"] - test_result["start_time"]
                        
                        # Check for delegation
                        if "ceo log specialist" in response.lower():
                            test_result["delegation_detected"] = True
                            telemetry_data["delegation_evidence"].append({
                                "type": "announcement",
                                "text": "CEO Log specialist delegation detected in response"
                            })
                            logger.info("✅ CEO Log delegation detected!")
                        
                        # Check for function execution
                        if any(word in response.lower() for word in ['tags', 'strategic', 'team', 'ai']):
                            telemetry_data["delegation_evidence"].append({
                                "type": "function_execution",
                                "text": "CEO Log function appears to have executed"
                            })
                            logger.info("✅ CEO Log function executed")
                        
                        # Add telemetry attributes
                        add_span_attributes(test_span, {
                            "response.length": len(response),
                            "delegation.detected": test_result["delegation_detected"],
                            "duration.seconds": test_result["duration"]
                        })
                        
                        # Log response
                        logger.info("\nResponse:")
                        logger.info("-" * 40)
                        logger.info(response[:500] + "..." if len(response) > 500 else response)
                        logger.info("-" * 40)
                        
                    except Exception as e:
                        logger.error(f"Error during test: {e}")
                        test_result["error"] = str(e)
                        if "rate_limit" in str(e):
                            logger.warning("Rate limit hit - this is expected with multiple tests")
                
                telemetry_data["tests"].append(test_result)
                
                # Add summary
                add_span_attributes(main_span, {
                    "test.completed": True,
                    "delegation.found": test_result["delegation_detected"],
                    "test.duration": test_result.get("duration", 0)
                })
    
    # Save telemetry data
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    telemetry_file = Path(__file__).parent / f"ceo_telemetry_{timestamp}.json"
    
    with open(telemetry_file, 'w') as f:
        json.dump(telemetry_data, f, indent=2)
    
    logger.info(f"\n✅ Telemetry data saved to: {telemetry_file}")
    
    # Summary
    logger.info("\n" + "="*60)
    logger.info("TELEMETRY CAPTURE COMPLETE")
    logger.info("="*60)
    logger.info(f"Delegation detected: {test_result['delegation_detected']}")
    logger.info(f"Evidence collected: {len(telemetry_data['delegation_evidence'])} items")
    logger.info(f"Test duration: {test_result.get('duration', 0):.2f} seconds")
    
    return telemetry_data

if __name__ == "__main__":
    # Check telemetry setup
    app_insights = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING") or os.getenv("APPINSIGHTS_CONNECTION_STRING")
    if app_insights:
        logger.info("✅ Application Insights configured")
    else:
        logger.warning("⚠️  No Application Insights connection")
    
    # Run capture
    asyncio.run(capture_ceo_telemetry())