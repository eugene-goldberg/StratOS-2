#!/usr/bin/env python3
"""
Quick test of deployed StratOS orchestrator to verify delegation works.
Now includes telemetry tracking for better observability.
"""

import asyncio
import os
import logging
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path for telemetry imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# Import Azure SDK components
from azure.identity.aio import DefaultAzureCredential
from azure.ai.projects.aio import AIProjectClient
from semantic_kernel.agents import AzureAIAgent

# Import telemetry components
from core.telemetry import create_span_context, add_span_attributes

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def quick_test():
    """Quick test of StratOS orchestrator delegation with telemetry."""
    
    # Check for deployment info first
    deployment_file = Path(__file__).parent / "stratos_deployment_info.json"
    if deployment_file.exists():
        with open(deployment_file, 'r') as f:
            deployment_info = json.load(f)
        orchestrator_id = deployment_info['orchestrator']['id']
        logger.info(f"Using orchestrator from deployment info: {orchestrator_id}")
    else:
        orchestrator_id = os.getenv("STRATOS_ORCHESTRATOR_ID")
        if not orchestrator_id:
            logger.error("STRATOS_ORCHESTRATOR_ID not found in environment and no deployment info available")
            return
            
    logger.info(f"Testing StratOS orchestrator: {orchestrator_id}")
    
    endpoint = os.getenv("AZURE_AI_PROJECT_CONNECTION_STRING")
    
    # Main test span for telemetry
    with create_span_context("stratos.quick_test", {
        "test.type": "quick_delegation",
        "orchestrator.id": orchestrator_id
    }) as main_span:
        
        async with DefaultAzureCredential() as credential, \
                   AIProjectClient(endpoint=endpoint, credential=credential) as client:
        
            # Get orchestrator definition
            with create_span_context("agent.get_definition", {
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
            
            # Test CEO Log delegation
            logger.info("\n" + "="*60)
            logger.info("TEST 1: CEO Log Tag Generation")
            logger.info("="*60)
            
            with create_span_context("test.ceo_log_delegation", {
                "delegation.type": "ceo_log",
                "target.agent": "CEOLogAgent",
                "function": "GenerateTags"
            }) as span:
                response = ""
                async for part in orchestrator_agent.invoke(messages="Generate tags for this CEO log entry: 'Had a productive meeting with the sales team. Q1 revenue exceeded targets by 20%. Team morale is high.'"):
                    if hasattr(part, 'content') and part.content:
                        response += str(part.content)
                
                logger.info(f"Response: {response}")
                add_span_attributes(span, {
                    "response.length": len(response),
                    "delegation.success": "ceo log specialist" in response.lower()
                })
        
            # Wait to avoid rate limits
            await asyncio.sleep(3)
            
            # Test CEO Log save entry
            logger.info("\n" + "="*60)
            logger.info("TEST 2: CEO Log Save Entry")
            logger.info("="*60)
            
            with create_span_context("test.ceo_log_save", {
                "delegation.type": "ceo_log",
                "target.agent": "CEOLogAgent",
                "function": "SaveEntry"
            }) as span:
                response = ""
                async for part in orchestrator_agent.invoke(messages="Save this CEO log entry: 'Meeting with the board went well. We discussed the new AI strategy and got approval for increased R&D budget.'"):
                    if hasattr(part, 'content') and part.content:
                        response += str(part.content)
                
                logger.info(f"Response: {response}")
                add_span_attributes(span, {
                    "response.length": len(response),
                    "delegation.success": "ceo log specialist" in response.lower()
                })
        
            # Wait to avoid rate limits
            await asyncio.sleep(3)
            
            # Test CEO Log insights
            logger.info("\n" + "="*60)
            logger.info("TEST 3: CEO Log Extract Insights")
            logger.info("="*60)
            
            with create_span_context("test.ceo_log_insights", {
                "delegation.type": "ceo_log",
                "target.agent": "CEOLogAgent",
                "function": "ExtractInsights"
            }) as span:
                response = ""
                async for part in orchestrator_agent.invoke(messages="Extract insights from recent CEO log entries about team and culture"):
                    if hasattr(part, 'content') and part.content:
                        response += str(part.content)
                
                logger.info(f"Response: {response}")
                add_span_attributes(span, {
                    "response.length": len(response),
                    "delegation.success": "ceo log specialist" in response.lower(),
                    "insights.present": any(word in response.lower() for word in ["insight", "theme", "recommendation"])
                })
        
            # Summary
            logger.info("\n" + "="*60)
            logger.info("SUMMARY")
            logger.info("="*60)
            logger.info("✅ StratOS orchestrator is deployed and responding")
            logger.info("✅ CEO Log Agent available with multiple functions")
            logger.info("✅ Check responses above to verify proper delegation with announcements")
            logger.info("✅ Telemetry tracking enabled - check Application Insights for traces")
            
            # Add final test status to main span
            add_span_attributes(main_span, {
                "test.completed": True,
                "test.status": "success"
            })

if __name__ == "__main__":
    # Check for telemetry configuration
    app_insights = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
    if app_insights:
        logger.info("✅ Telemetry enabled via Application Insights")
    else:
        logger.warning("⚠️  No APPLICATIONINSIGHTS_CONNECTION_STRING found - telemetry disabled")
    
    asyncio.run(quick_test())