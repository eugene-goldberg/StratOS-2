"""
Capture telemetry for North Star Agent delegation
"""

import asyncio
import os
import sys
import json
import uuid
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv(Path(__file__).parent / '.env')
load_dotenv(Path(__file__).parent.parent.parent.parent / '.env')

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from azure.ai.projects.aio import AIProjectClient
from azure.identity.aio import DefaultAzureCredential
from semantic_kernel.agents import AzureAIAgent
from azure.monitor.opentelemetry import configure_azure_monitor
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Local telemetry storage
telemetry_events = []

class TelemetryCapture:
    def __init__(self):
        self.session_id = str(uuid.uuid4())
        self.events = []
        
    def capture_event(self, event_type, data):
        event = {
            "timestamp": datetime.now().isoformat(),
            "session_id": self.session_id,
            "event_type": event_type,
            "data": data
        }
        self.events.append(event)
        logger.info(f"📊 Captured: {event_type}")
        
    def save_events(self):
        filename = f"north_star_telemetry_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{self.session_id[:8]}.json"
        filepath = Path(__file__).parent / "telemetry" / "north_star_agent" / filename
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'w') as f:
            json.dump({
                "session_id": self.session_id,
                "capture_time": datetime.now().isoformat(),
                "events": self.events
            }, f, indent=2)
        
        logger.info(f"💾 Telemetry saved to: {filepath}")
        return filepath

async def test_north_star_with_telemetry():
    """Test North Star delegation with telemetry capture"""
    
    telemetry = TelemetryCapture()
    
    orchestrator_id = os.getenv('STRATOS_ORCHESTRATOR_ID')
    if not orchestrator_id:
        logger.error("STRATOS_ORCHESTRATOR_ID not found")
        return
        
    connection_string = os.getenv('AZURE_AI_PROJECT_CONNECTION_STRING')
    if not connection_string:
        logger.error("AZURE_AI_PROJECT_CONNECTION_STRING not found")
        return
    
    # Configure Azure telemetry if available
    app_insights_key = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
    if app_insights_key:
        configure_azure_monitor(
            connection_string=app_insights_key,
            logger_name="north_star_telemetry_test"
        )
        telemetry.capture_event("telemetry_configured", {"app_insights": True})
    else:
        telemetry.capture_event("telemetry_configured", {"app_insights": False})
    
    logger.info(f"🎯 Testing with Session ID: {telemetry.session_id}")
    logger.info(f"🤖 Orchestrator ID: {orchestrator_id}")
    
    async with DefaultAzureCredential() as credential:
        async with AIProjectClient(
            endpoint=connection_string,
            credential=credential
        ) as client:
            try:
                # Get orchestrator
                telemetry.capture_event("orchestrator_fetch_start", {"orchestrator_id": orchestrator_id})
                orchestrator_def = await client.agents.get_agent(agent_id=orchestrator_id)
                telemetry.capture_event("orchestrator_fetch_complete", {
                    "name": orchestrator_def.name,
                    "tools_count": len(orchestrator_def.tools) if orchestrator_def.tools else 0,
                    "tools": [{"name": t.connected_agent.name, "id": t.connected_agent.id} 
                             for t in orchestrator_def.tools if hasattr(t, 'connected_agent')]
                })
                
                logger.info(f"✅ Orchestrator loaded: {orchestrator_def.name}")
                logger.info(f"📋 Available tools: {len(orchestrator_def.tools) if orchestrator_def.tools else 0}")
                
                # Create agent instance
                orchestrator_agent = AzureAIAgent(
                    client=client,
                    definition=orchestrator_def
                )
                
                # Test 1: Purpose Definition
                logger.info("\n" + "="*60)
                logger.info("TEST: North Star Purpose Definition")
                logger.info("="*60)
                
                query = "Help me define our organizational purpose. We want to make AI accessible to everyone."
                telemetry.capture_event("query_sent", {
                    "query": query,
                    "target": "north_star",
                    "function": "purpose_definition"
                })
                
                response = ""
                response_parts = []
                async for part in orchestrator_agent.invoke(messages=query):
                    if hasattr(part, 'content') and part.content:
                        response += str(part.content)
                        response_parts.append({
                            "type": type(part).__name__,
                            "content": str(part.content)[:200]  # First 200 chars
                        })
                
                telemetry.capture_event("response_received", {
                    "response_length": len(response),
                    "parts_count": len(response_parts),
                    "delegation_detected": "north star specialist" in response.lower(),
                    "response_preview": response[:500]
                })
                
                logger.info(f"\n📤 Response preview: {response[:200]}...")
                
                # Check for delegation evidence
                if "north star specialist" in response.lower():
                    logger.info("\n✅ DELEGATION EVIDENCE FOUND!")
                    telemetry.capture_event("delegation_confirmed", {
                        "type": "north_star",
                        "announcement": "I'll connect you with the North Star specialist"
                    })
                else:
                    logger.warning("⚠️ No explicit delegation announcement found")
                    telemetry.capture_event("delegation_not_found", {
                        "response": response[:500]
                    })
                
                # Test 2: Vision Creation
                logger.info("\n" + "="*60)
                logger.info("TEST: North Star Vision Creation")
                logger.info("="*60)
                
                query2 = "Create a vision statement for becoming the global leader in AI by 2030"
                telemetry.capture_event("query_sent", {
                    "query": query2,
                    "target": "north_star",
                    "function": "vision_creation"
                })
                
                response2 = ""
                async for part in orchestrator_agent.invoke(messages=query2):
                    if hasattr(part, 'content') and part.content:
                        response2 += str(part.content)
                
                telemetry.capture_event("response_received", {
                    "response_length": len(response2),
                    "delegation_detected": "north star specialist" in response2.lower(),
                    "response_preview": response2[:500]
                })
                
                logger.info(f"\n📤 Response preview: {response2[:200]}...")
                
                # Test 3: CEO Log (verify it still works)
                logger.info("\n" + "="*60)
                logger.info("TEST: CEO Log Delegation (Verify)")
                logger.info("="*60)
                
                query3 = "Save this CEO log: Great progress on North Star implementation today"
                telemetry.capture_event("query_sent", {
                    "query": query3,
                    "target": "ceo_log",
                    "function": "save_entry"
                })
                
                response3 = ""
                async for part in orchestrator_agent.invoke(messages=query3):
                    if hasattr(part, 'content') and part.content:
                        response3 += str(part.content)
                
                telemetry.capture_event("response_received", {
                    "response_length": len(response3),
                    "delegation_detected": "ceo log specialist" in response3.lower(),
                    "response_preview": response3[:500]
                })
                
                logger.info(f"\n📤 Response preview: {response3[:200]}...")
                
                # Summary
                telemetry.capture_event("test_complete", {
                    "tests_run": 3,
                    "north_star_delegations": 2,
                    "ceo_log_delegations": 1
                })
                
                logger.info("\n" + "="*60)
                logger.info("TELEMETRY CAPTURE SUMMARY")
                logger.info("="*60)
                logger.info(f"Session ID: {telemetry.session_id}")
                logger.info(f"Events captured: {len(telemetry.events)}")
                logger.info("="*60)
                
                # Save telemetry
                filepath = telemetry.save_events()
                
                return telemetry.session_id, filepath
                
            except Exception as e:
                logger.error(f"Error during test: {e}", exc_info=True)
                telemetry.capture_event("error", {
                    "error_type": type(e).__name__,
                    "error_message": str(e)
                })
                telemetry.save_events()
                raise

if __name__ == "__main__":
    session_id, filepath = asyncio.run(test_north_star_with_telemetry())
    if session_id:
        logger.info(f"\n✅ Telemetry capture complete!")
        logger.info(f"📁 Check the telemetry file for evidence: {filepath}")