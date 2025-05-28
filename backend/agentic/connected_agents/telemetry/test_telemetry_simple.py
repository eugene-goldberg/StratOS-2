#!/usr/bin/env python3
"""
Simple telemetry test for connected agents.
Demonstrates proper telemetry initialization and tracking.
"""

import asyncio
import os
import sys
import logging
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# Import Azure SDK components
from azure.identity.aio import DefaultAzureCredential
from azure.ai.projects.aio import AIProjectClient
from semantic_kernel.agents import AzureAIAgent

# Import telemetry components
from core.telemetry import initialize_telemetry, create_span_context, add_span_attributes

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize telemetry at module level
tracer = initialize_telemetry(
    service_name="connected-agents-test",
    service_version="1.0.0"
)

async def test_connected_agents_with_telemetry():
    """Test connected agents with proper telemetry tracking."""
    
    orchestrator_id = os.getenv("MAIN_ORCHESTRATOR_AGENT_ID")
    if not orchestrator_id:
        logger.error("MAIN_ORCHESTRATOR_AGENT_ID not found in environment")
        return
        
    endpoint = os.getenv("AZURE_AI_PROJECT_CONNECTION_STRING")
    if not endpoint:
        logger.error("AZURE_AI_PROJECT_CONNECTION_STRING not found in environment")
        return
    
    logger.info(f"Testing orchestrator: {orchestrator_id}")
    logger.info(f"Telemetry enabled: {tracer is not None}")
    
    # Create main test span
    with create_span_context("connected_agents.full_test", {
        "test.type": "integration",
        "orchestrator.id": orchestrator_id
    }) as main_span:
        
        async with DefaultAzureCredential() as credential, \
                   AIProjectClient(endpoint=endpoint, credential=credential) as client:
            
            # Get orchestrator
            orchestrator_def = await client.agents.get_agent(agent_id=orchestrator_id)
            logger.info(f"Orchestrator: {orchestrator_def.name}")
            
            orchestrator_agent = AzureAIAgent(
                client=client,
                definition=orchestrator_def
            )
            
            # Test 1: Weather request with telemetry
            logger.info("\nTesting weather delegation with telemetry...")
            
            with create_span_context("delegation.weather", {
                "request.type": "weather",
                "request.city": "Seattle"
            }) as weather_span:
                
                start_time = datetime.now()
                response = ""
                
                async for part in orchestrator_agent.invoke(messages="What's the weather like in Seattle?"):
                    if hasattr(part, 'content') and part.content:
                        response += str(part.content)
                
                duration = (datetime.now() - start_time).total_seconds()
                
                # Add response attributes
                if weather_span:
                    add_span_attributes(weather_span, {
                        "response.length": len(response),
                        "response.duration_seconds": duration,
                        "delegation.success": True,
                        "delegation.announcement": "weather information specialist" in response
                    })
                
                logger.info(f"Response received in {duration:.2f}s")
                logger.info(f"Response preview: {response[:100]}...")
            
            # Test 2: Calculator request with telemetry
            logger.info("\nTesting calculator delegation with telemetry...")
            
            with create_span_context("delegation.calculator", {
                "request.type": "calculation",
                "request.operation": "multiplication"
            }) as calc_span:
                
                start_time = datetime.now()
                response = ""
                
                async for part in orchestrator_agent.invoke(messages="What is 123 times 456?"):
                    if hasattr(part, 'content') and part.content:
                        response += str(part.content)
                
                duration = (datetime.now() - start_time).total_seconds()
                
                # Add response attributes
                if calc_span:
                    add_span_attributes(calc_span, {
                        "response.length": len(response),
                        "response.duration_seconds": duration,
                        "delegation.success": True,
                        "delegation.announcement": "mathematical specialist" in response
                    })
                
                logger.info(f"Response received in {duration:.2f}s")
                logger.info(f"Response preview: {response[:100]}...")
            
            # Add summary to main span
            if main_span:
                add_span_attributes(main_span, {
                    "test.completed": True,
                    "test.total_delegations": 2,
                    "test.timestamp": datetime.utcnow().isoformat()
                })
    
    logger.info("\n" + "="*60)
    logger.info("TELEMETRY TEST COMPLETE")
    logger.info("="*60)
    logger.info("✅ Telemetry spans created for:")
    logger.info("   - Main test flow")
    logger.info("   - Weather delegation")
    logger.info("   - Calculator delegation")
    logger.info("\nView in Application Insights:")
    logger.info("1. Search for operation: 'connected_agents.full_test'")
    logger.info("2. View distributed trace timeline")
    logger.info("3. Check custom dimensions for details")

if __name__ == "__main__":
    asyncio.run(test_connected_agents_with_telemetry())