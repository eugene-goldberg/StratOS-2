#!/usr/bin/env python3
"""
Quick test of deployed multi-tool orchestrator to verify delegation works.
Now includes telemetry tracking for better observability.
"""

import asyncio
import os
import logging
import sys
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
    """Quick test of orchestrator delegation with telemetry."""
    
    orchestrator_id = os.getenv("MAIN_ORCHESTRATOR_AGENT_ID")
    if not orchestrator_id:
        logger.error("MAIN_ORCHESTRATOR_AGENT_ID not found in environment")
        return
        
    logger.info(f"Testing orchestrator: {orchestrator_id}")
    
    endpoint = os.getenv("AZURE_AI_PROJECT_CONNECTION_STRING")
    
    # Main test span for telemetry
    with create_span_context("connected_agents.quick_test", {
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
            
            # Test greeting delegation
            logger.info("\n" + "="*60)
            logger.info("TEST 1: Greeting Request")
            logger.info("="*60)
            
            with create_span_context("test.greeting_delegation", {
                "delegation.type": "greeting",
                "target.agent": "GreetingAgent"
            }) as span:
                response = ""
                async for part in orchestrator_agent.invoke(messages="Hello! Please give me a warm greeting."):
                    if hasattr(part, 'content') and part.content:
                        response += str(part.content)
                
                logger.info(f"Response: {response}")
                add_span_attributes(span, {
                    "response.length": len(response),
                    "delegation.success": "greeting specialist" in response.lower()
                })
        
            # Wait to avoid rate limits
            await asyncio.sleep(3)
            
            # Test calculation delegation
            logger.info("\n" + "="*60)
            logger.info("TEST 2: Calculation Request")
            logger.info("="*60)
            
            with create_span_context("test.calculation_delegation", {
                "delegation.type": "calculation",
                "target.agent": "CalculatorAgent"
            }) as span:
                response = ""
                async for part in orchestrator_agent.invoke(messages="What is 25 times 4?"):
                    if hasattr(part, 'content') and part.content:
                        response += str(part.content)
                
                logger.info(f"Response: {response}")
                add_span_attributes(span, {
                    "response.length": len(response),
                    "delegation.success": "calculation expert" in response.lower()
                })
        
            # Wait to avoid rate limits
            await asyncio.sleep(3)
            
            # Test weather delegation
            logger.info("\n" + "="*60)
            logger.info("TEST 3: Weather Request")
            logger.info("="*60)
            
            with create_span_context("test.weather_delegation", {
                "delegation.type": "weather",
                "target.agent": "WeatherAgent",
                "location": "San Francisco"
            }) as span:
                response = ""
                async for part in orchestrator_agent.invoke(messages="What's the weather like in San Francisco?"):
                    if hasattr(part, 'content') and part.content:
                        response += str(part.content)
                
                logger.info(f"Response: {response}")
                add_span_attributes(span, {
                    "response.length": len(response),
                    "delegation.success": "weather information specialist" in response.lower(),
                    "weather.data_present": any(word in response.lower() for word in ["temperature", "conditions", "weather"])
                })
        
            # Summary
            logger.info("\n" + "="*60)
            logger.info("SUMMARY")
            logger.info("="*60)
            logger.info("✅ Multi-tool orchestrator is deployed and responding")
            logger.info("✅ Three specialized agents available: Greeter, Calculator, Weather")
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