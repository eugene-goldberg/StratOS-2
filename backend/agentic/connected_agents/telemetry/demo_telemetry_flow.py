#!/usr/bin/env python3
"""
Simple demonstration of telemetry flow for connected agents.
Shows how telemetry tracks the full request lifecycle.
"""

import asyncio
import os
import sys
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# Import telemetry components
from core.telemetry import create_span_context, add_span_attributes
from services.telemetry_agent_client import TelemetryAgentClient

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def demonstrate_telemetry_flow():
    """Demonstrate the telemetry flow with a simple example."""
    
    logger.info("="*60)
    logger.info("TELEMETRY FLOW DEMONSTRATION")
    logger.info("="*60)
    
    # Check telemetry configuration
    app_insights = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
    if not app_insights:
        logger.error("❌ APPLICATIONINSIGHTS_CONNECTION_STRING not configured!")
        return
    
    logger.info("✅ Application Insights configured")
    
    # Create telemetry client
    client = TelemetryAgentClient()
    
    # Demonstrate the telemetry flow
    with create_span_context("demo.telemetry_flow", {
        "demo.type": "connected_agents",
        "demo.timestamp": datetime.utcnow().isoformat()
    }) as demo_span:
        
        logger.info("\n1️⃣ STEP 1: User Request")
        logger.info("User asks: 'Hello, can you greet me and tell me what 5 times 8 is?'")
        
        message = "Hello, can you greet me and tell me what 5 times 8 is?"
        
        logger.info("\n2️⃣ STEP 2: Orchestrator Invocation (with telemetry)")
        logger.info("The request goes to the Main Orchestrator...")
        
        try:
            # This creates a span: "orchestrator.process_request"
            response = await client.invoke_orchestrator(
                message=message,
                user_id="demo_user_123"
            )
            
            logger.info("\n3️⃣ STEP 3: Orchestrator Response")
            logger.info(f"Response: {response[:300]}...")
            
            # Track what happened
            delegations = []
            if "greeting specialist" in response.lower():
                delegations.append("GreetingAgent")
            if "calculation expert" in response.lower():
                delegations.append("CalculatorAgent")
            
            add_span_attributes(demo_span, {
                "delegations.count": len(delegations),
                "delegations.agents": ",".join(delegations),
                "response.length": len(response)
            })
            
            logger.info("\n4️⃣ STEP 4: Telemetry Captured")
            logger.info("The following telemetry was captured:")
            logger.info("- Main span: demo.telemetry_flow")
            logger.info("  └─ orchestrator.process_request")
            logger.info("     ├─ Attributes: user.id, message.length")
            logger.info("     ├─ Delegations to specialized agents")
            logger.info("     └─ Response details")
            
            logger.info("\n5️⃣ STEP 5: View in Application Insights")
            logger.info("To see this telemetry:")
            logger.info("1. Go to Azure Portal → Application Insights")
            logger.info("2. Click on 'Transaction search'")
            logger.info("3. Search for: demo.telemetry_flow")
            logger.info("4. Click on the trace to see the full hierarchy")
            
        except Exception as e:
            logger.error(f"❌ Error: {e}")
            add_span_attributes(demo_span, {
                "error": str(e),
                "error.type": type(e).__name__
            })


async def main():
    """Run the demonstration."""
    await demonstrate_telemetry_flow()
    
    logger.info("\n" + "="*60)
    logger.info("TELEMETRY BENEFITS")
    logger.info("="*60)
    logger.info("With telemetry enabled, you can track:")
    logger.info("✅ Request flow through the system")
    logger.info("✅ Which agents handle which requests")
    logger.info("✅ Performance metrics and bottlenecks")
    logger.info("✅ Error rates and failure patterns")
    logger.info("✅ User behavior and usage patterns")
    logger.info("="*60)


if __name__ == "__main__":
    asyncio.run(main())