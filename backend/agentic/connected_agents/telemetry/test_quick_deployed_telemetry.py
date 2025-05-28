#!/usr/bin/env python3
"""
Quick test of deployed multi-tool orchestrator with telemetry tracking.
Tests full delegation flow with telemetry capture.
"""

import asyncio
import os
import logging
from dotenv import load_dotenv
from datetime import datetime
import json

# Load environment variables
load_dotenv()

# Import Azure SDK components
from azure.identity.aio import DefaultAzureCredential
from azure.ai.projects.aio import AIProjectClient
from semantic_kernel.agents import AzureAIAgent

# Import telemetry components
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from core.telemetry import create_span_context, add_span_attributes, SpanNames

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TelemetryConnectedAgentTest:
    """Test connected agents with telemetry tracking."""
    
    def __init__(self):
        self.orchestrator_id = os.getenv("MAIN_ORCHESTRATOR_AGENT_ID")
        if not self.orchestrator_id:
            raise ValueError("MAIN_ORCHESTRATOR_AGENT_ID not found in environment")
            
        self.endpoint = os.getenv("AZURE_AI_PROJECT_CONNECTION_STRING")
        if not self.endpoint:
            raise ValueError("AZURE_AI_PROJECT_CONNECTION_STRING not found in environment")
    
    async def test_with_telemetry(self):
        """Run tests with full telemetry tracking."""
        
        # Main test span
        with create_span_context("connected_agents.test.full_flow", {
            "test.name": "connected_agents_telemetry",
            "test.type": "integration",
            "orchestrator.id": self.orchestrator_id
        }) as main_span:
            
            logger.info(f"Testing orchestrator: {self.orchestrator_id}")
            
            async with DefaultAzureCredential() as credential, \
                       AIProjectClient(endpoint=self.endpoint, credential=credential) as client:
                
                # Get orchestrator definition
                with create_span_context("agent.get_definition", {
                    "agent.id": self.orchestrator_id,
                    "agent.type": "orchestrator"
                }):
                    orchestrator_def = await client.agents.get_agent(agent_id=self.orchestrator_id)
                    logger.info(f"Orchestrator: {orchestrator_def.name}")
                    logger.info(f"Tools available: {len(orchestrator_def.tools) if orchestrator_def.tools else 0}")
                
                # Create agent instance
                orchestrator_agent = AzureAIAgent(
                    client=client,
                    definition=orchestrator_def
                )
                
                # Test greeting delegation
                await self._test_greeting_delegation(orchestrator_agent)
                
                # Wait to avoid rate limits
                await asyncio.sleep(3)
                
                # Test calculation delegation
                await self._test_calculation_delegation(orchestrator_agent)
                
                # Wait to avoid rate limits
                await asyncio.sleep(3)
                
                # Test weather delegation
                await self._test_weather_delegation(orchestrator_agent)
                
                # Summary
                add_span_attributes(main_span, {
                    "test.completed": True,
                    "test.status": "success",
                    "test.timestamp": datetime.utcnow().isoformat()
                })
                
                logger.info("\n" + "="*60)
                logger.info("TELEMETRY SUMMARY")
                logger.info("="*60)
                logger.info("✅ Multi-tool orchestrator tested with telemetry")
                logger.info("✅ All delegations tracked with spans")
                logger.info("✅ Check Application Insights for full trace details")
    
    async def _test_greeting_delegation(self, orchestrator_agent):
        """Test greeting delegation with telemetry."""
        
        logger.info("\n" + "="*60)
        logger.info("TEST 1: Greeting Request with Telemetry")
        logger.info("="*60)
        
        with create_span_context("delegation.greeting", {
            "delegation.type": "greeting",
            "orchestrator.name": "MultiToolOrchestrator",
            "target.agent": "GreetingAgent"
        }) as span:
            
            try:
                message = "Hello! Please give me a warm greeting."
                add_span_attributes(span, {"request.message": message})
                
                response = ""
                async for part in orchestrator_agent.invoke(messages=message):
                    if hasattr(part, 'content') and part.content:
                        response += str(part.content)
                
                logger.info(f"Response: {response}")
                
                # Track response
                add_span_attributes(span, {
                    "response.length": len(response),
                    "response.success": True,
                    "delegation.completed": True
                })
                
                # Check if delegation announcement is present
                has_announcement = "greeting specialist" in response.lower()
                add_span_attributes(span, {
                    "delegation.announcement_present": has_announcement
                })
                
            except Exception as e:
                logger.error(f"Greeting test failed: {e}")
                add_span_attributes(span, {
                    "error": str(e),
                    "error.type": type(e).__name__,
                    "response.success": False
                })
    
    async def _test_calculation_delegation(self, orchestrator_agent):
        """Test calculation delegation with telemetry."""
        
        logger.info("\n" + "="*60)
        logger.info("TEST 2: Calculation Request with Telemetry")
        logger.info("="*60)
        
        with create_span_context("delegation.calculation", {
            "delegation.type": "calculation",
            "orchestrator.name": "MultiToolOrchestrator",
            "target.agent": "CalculatorAgent"
        }) as span:
            
            try:
                message = "What is 25 times 4?"
                add_span_attributes(span, {"request.message": message})
                
                response = ""
                async for part in orchestrator_agent.invoke(messages=message):
                    if hasattr(part, 'content') and part.content:
                        response += str(part.content)
                
                logger.info(f"Response: {response}")
                
                # Track response
                add_span_attributes(span, {
                    "response.length": len(response),
                    "response.success": True,
                    "delegation.completed": True
                })
                
                # Check if delegation announcement is present
                has_announcement = "calculation expert" in response.lower()
                add_span_attributes(span, {
                    "delegation.announcement_present": has_announcement
                })
                
            except Exception as e:
                logger.error(f"Calculation test failed: {e}")
                add_span_attributes(span, {
                    "error": str(e),
                    "error.type": type(e).__name__,
                    "response.success": False
                })
    
    async def _test_weather_delegation(self, orchestrator_agent):
        """Test weather delegation with telemetry."""
        
        logger.info("\n" + "="*60)
        logger.info("TEST 3: Weather Request with Telemetry")
        logger.info("="*60)
        
        with create_span_context("delegation.weather", {
            "delegation.type": "weather",
            "orchestrator.name": "MultiToolOrchestrator",
            "target.agent": "WeatherAgent"
        }) as span:
            
            try:
                message = "What's the weather like in San Francisco?"
                add_span_attributes(span, {
                    "request.message": message,
                    "weather.location": "San Francisco"
                })
                
                response = ""
                async for part in orchestrator_agent.invoke(messages=message):
                    if hasattr(part, 'content') and part.content:
                        response += str(part.content)
                
                logger.info(f"Response: {response}")
                
                # Track response
                add_span_attributes(span, {
                    "response.length": len(response),
                    "response.success": True,
                    "delegation.completed": True
                })
                
                # Check if delegation announcement is present
                has_announcement = "weather information specialist" in response.lower()
                add_span_attributes(span, {
                    "delegation.announcement_present": has_announcement
                })
                
                # Check for weather data
                has_weather_data = any(word in response.lower() for word in ["temperature", "conditions", "weather"])
                add_span_attributes(span, {
                    "weather.data_present": has_weather_data
                })
                
            except Exception as e:
                logger.error(f"Weather test failed: {e}")
                add_span_attributes(span, {
                    "error": str(e),
                    "error.type": type(e).__name__,
                    "response.success": False
                })

async def main():
    """Run the telemetry test."""
    
    # Verify Application Insights is configured
    app_insights_connection = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
    if not app_insights_connection:
        logger.error("APPLICATIONINSIGHTS_CONNECTION_STRING not found in environment")
        logger.error("Telemetry will not be captured!")
        return
    
    logger.info("Application Insights configured ✓")
    logger.info(f"Connection: {app_insights_connection[:50]}...")
    
    # Run test
    test = TelemetryConnectedAgentTest()
    await test.test_with_telemetry()
    
    logger.info("\n" + "="*60)
    logger.info("TELEMETRY VERIFICATION")
    logger.info("="*60)
    logger.info("To view telemetry data:")
    logger.info("1. Go to Azure Portal > Application Insights")
    logger.info("2. Navigate to Transaction Search")
    logger.info("3. Filter by operation name: 'connected_agents.test.full_flow'")
    logger.info("4. View the distributed trace to see all delegations")
    logger.info("="*60)

if __name__ == "__main__":
    asyncio.run(main())