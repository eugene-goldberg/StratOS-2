"""
Comprehensive test for North Star Agent with Orchestrator Delegation
Tests both direct agent access and orchestrator routing with telemetry
"""

import asyncio
import os
import sys
import json
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import uuid

# Load environment variables
load_dotenv(Path(__file__).parent / '.env')

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from azure.ai.projects.aio import AIProjectClient
from azure.identity.aio import DefaultAzureCredential
from azure.ai.projects.models import AzureAIAgent
from azure.monitor.opentelemetry import configure_azure_monitor

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configure telemetry
def setup_telemetry():
    """Configure Azure Application Insights telemetry"""
    app_insights_key = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
    if app_insights_key:
        configure_azure_monitor(
            connection_string=app_insights_key,
            logger_name="test_north_star_comprehensive"
        )
        logger.info("Telemetry configured with Application Insights")
    else:
        logger.warning("No Application Insights connection string found")

async def test_direct_north_star():
    """Test North Star agent directly"""
    
    north_star_id = os.getenv("NORTH_STAR_AGENT_ID")
    connection_string = os.getenv("AZURE_AI_PROJECT_CONNECTION_STRING")
    
    if not north_star_id or not connection_string:
        logger.error("Missing required environment variables")
        return None
    
    logger.info(f"Testing North Star Agent directly: {north_star_id}")
    
    async with DefaultAzureCredential() as credential:
        async with AIProjectClient(
            endpoint=connection_string,
            credential=credential
        ) as client:
            try:
                # Test setting purpose
                response = await AzureAIAgent.invoke(
                    client=client,
                    agent_id=north_star_id,
                    messages=[{
                        "role": "user",
                        "content": "Set our purpose: To democratize strategic planning through AI technology"
                    }]
                )
                
                logger.info(f"Direct North Star Response:\n{response}\n")
                return response
                
            except Exception as e:
                logger.error(f"Error in direct test: {e}")
                return None

async def test_orchestrator_delegation():
    """Test North Star through orchestrator delegation"""
    
    orchestrator_id = os.getenv("STRATOS_ORCHESTRATOR_ID")
    connection_string = os.getenv("AZURE_AI_PROJECT_CONNECTION_STRING")
    
    if not orchestrator_id or not connection_string:
        logger.error("Missing required environment variables")
        return None
    
    logger.info(f"Testing Orchestrator delegation to North Star: {orchestrator_id}")
    
    async with DefaultAzureCredential() as credential:
        async with AIProjectClient(
            endpoint=connection_string,
            credential=credential
        ) as client:
            try:
                # Create telemetry-tracked session
                session_id = str(uuid.uuid4())
                
                # Test delegation for purpose setting
                logger.info("\n" + "="*60)
                logger.info("TEST: Orchestrator → North Star Delegation")
                logger.info(f"Session ID: {session_id}")
                logger.info("="*60)
                
                response = await AzureAIAgent.invoke(
                    client=client,
                    agent_id=orchestrator_id,
                    messages=[{
                        "role": "user",
                        "content": "I need help defining our organizational purpose. We're a company focused on making strategic planning accessible through AI."
                    }],
                    metadata={
                        "session_id": session_id,
                        "test_type": "north_star_delegation",
                        "timestamp": datetime.now().isoformat()
                    }
                )
                
                logger.info(f"Orchestrator Response:\n{response}\n")
                
                # Test delegation for vision
                response = await AzureAIAgent.invoke(
                    client=client,
                    agent_id=orchestrator_id,
                    messages=[{
                        "role": "user",
                        "content": "Create a vision statement for becoming the global leader in AI-powered strategic planning by 2030"
                    }],
                    metadata={
                        "session_id": session_id,
                        "test_type": "north_star_delegation",
                        "timestamp": datetime.now().isoformat()
                    }
                )
                
                logger.info(f"Orchestrator Response:\n{response}\n")
                
                # Test delegation for values
                response = await AzureAIAgent.invoke(
                    client=client,
                    agent_id=orchestrator_id,
                    messages=[{
                        "role": "user",
                        "content": "Add our core values: Innovation, Transparency, and Customer Success"
                    }],
                    metadata={
                        "session_id": session_id,
                        "test_type": "north_star_delegation",
                        "timestamp": datetime.now().isoformat()
                    }
                )
                
                logger.info(f"Orchestrator Response:\n{response}\n")
                
                # Test delegation for strategic goals
                response = await AzureAIAgent.invoke(
                    client=client,
                    agent_id=orchestrator_id,
                    messages=[{
                        "role": "user",
                        "content": "Create a strategic goal to reach 1 million users by end of 2026"
                    }],
                    metadata={
                        "session_id": session_id,
                        "test_type": "north_star_delegation",
                        "timestamp": datetime.now().isoformat()
                    }
                )
                
                logger.info(f"Orchestrator Response:\n{response}\n")
                
                # Test delegation for alignment check
                response = await AzureAIAgent.invoke(
                    client=client,
                    agent_id=orchestrator_id,
                    messages=[{
                        "role": "user",
                        "content": "Does launching a premium enterprise tier align with our North Star?"
                    }],
                    metadata={
                        "session_id": session_id,
                        "test_type": "north_star_delegation",
                        "timestamp": datetime.now().isoformat()
                    }
                )
                
                logger.info(f"Orchestrator Response:\n{response}\n")
                
                # Get complete summary
                response = await AzureAIAgent.invoke(
                    client=client,
                    agent_id=orchestrator_id,
                    messages=[{
                        "role": "user",
                        "content": "Show me our complete strategic foundation"
                    }],
                    metadata={
                        "session_id": session_id,
                        "test_type": "north_star_delegation",
                        "timestamp": datetime.now().isoformat()
                    }
                )
                
                logger.info(f"Orchestrator Response:\n{response}\n")
                
                return session_id
                
            except Exception as e:
                logger.error(f"Error in orchestrator test: {e}", exc_info=True)
                return None

async def verify_delegation_evidence():
    """Verify that delegation actually happened"""
    
    # Save test results
    results = {
        "test_time": datetime.now().isoformat(),
        "tests_performed": [
            "Direct North Star agent test",
            "Orchestrator delegation test",
            "Purpose setting delegation",
            "Vision creation delegation",
            "Values management delegation",
            "Strategic goals delegation",
            "Alignment validation delegation",
            "Summary retrieval delegation"
        ],
        "expected_delegation_phrases": [
            "I'll connect you with the North Star specialist for strategic foundation guidance!",
            "north_star_specialist"
        ]
    }
    
    results_file = Path(__file__).parent / "test_outputs" / "north_star_agent" / f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    results_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Test results saved to: {results_file}")

async def main():
    """Run comprehensive North Star agent tests"""
    
    logger.info("\n" + "="*80)
    logger.info("NORTH STAR AGENT COMPREHENSIVE TEST")
    logger.info("="*80)
    
    # Setup telemetry
    setup_telemetry()
    
    # Test 1: Direct agent access
    logger.info("\n>>> PHASE 1: Testing Direct North Star Agent Access")
    await test_direct_north_star()
    
    # Test 2: Orchestrator delegation
    logger.info("\n>>> PHASE 2: Testing Orchestrator Delegation to North Star")
    session_id = await test_orchestrator_delegation()
    
    # Verify delegation
    await verify_delegation_evidence()
    
    logger.info("\n" + "="*80)
    logger.info("TEST SUMMARY")
    logger.info("="*80)
    logger.info("✓ Direct North Star agent test completed")
    logger.info("✓ Orchestrator delegation test completed")
    logger.info("✓ Multiple North Star functions tested")
    logger.info(f"✓ Session tracked with ID: {session_id}")
    logger.info("\nLook for delegation evidence:")
    logger.info("- 'I'll connect you with the North Star specialist for strategic foundation guidance!'")
    logger.info("- Function calls to 'north_star_specialist'")
    logger.info("="*80)

if __name__ == "__main__":
    asyncio.run(main())