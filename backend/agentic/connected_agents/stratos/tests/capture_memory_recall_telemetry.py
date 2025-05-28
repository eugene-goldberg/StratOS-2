"""
Capture telemetry for Memory Recall Agent delegation
Provides evidence of successful orchestration and delegation
"""

import os
import asyncio
import logging
import json
import uuid
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from azure.ai.projects.aio import AIProjectClient
from azure.identity.aio import DefaultAzureCredential
from semantic_kernel.agents import AzureAIAgent
from azure.monitor.opentelemetry import configure_azure_monitor
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

# Load environment variables
load_dotenv(Path(__file__).parent.parent.parent / '.env')

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Azure AI configuration
PROJECT_CONNECTION_STRING = os.getenv("AZURE_PROJECT_CONNECTION_STRING")
APPLICATION_INSIGHTS_CONNECTION_STRING = os.getenv("APPLICATION_INSIGHTS_CONNECTION_STRING")

# Session tracking
SESSION_ID = str(uuid.uuid4())
TELEMETRY_EVENTS = []

def log_telemetry_event(event_type: str, data: dict):
    """Log telemetry event for later analysis"""
    event = {
        "timestamp": datetime.utcnow().isoformat(),
        "session_id": SESSION_ID,
        "event_type": event_type,
        "data": data
    }
    TELEMETRY_EVENTS.append(event)
    logger.info(f"📊 Telemetry: {event_type} - {json.dumps(data)[:100]}...")

def load_deployment_info():
    """Load deployment info from file"""
    archive_dir = Path(__file__).parent.parent / "archive"
    deployment_file = archive_dir / "stratos_deployment_info.json"
    
    if not deployment_file.exists():
        logger.error(f"Deployment file not found: {deployment_file}")
        return None
        
    with open(deployment_file, 'r') as f:
        return json.load(f)

async def test_memory_recall_with_telemetry():
    """Test Memory Recall with comprehensive telemetry capture"""
    # Configure telemetry
    if APPLICATION_INSIGHTS_CONNECTION_STRING:
        configure_azure_monitor(connection_string=APPLICATION_INSIGHTS_CONNECTION_STRING)
        tracer = trace.get_tracer(__name__)
        logger.info("✅ Application Insights configured")
        log_telemetry_event("telemetry_configured", {"app_insights": True})
    else:
        logger.warning("⚠️ No Application Insights connection string found")
        tracer = None
        log_telemetry_event("telemetry_configured", {"app_insights": False})
    
    try:
        logger.info(f"=== Memory Recall Telemetry Capture ===")
        logger.info(f"Session ID: {SESSION_ID}")
        
        # Load deployment info
        deployment_info = load_deployment_info()
        if not deployment_info:
            logger.error("No deployment info found")
            return
        
        orchestrator_id = deployment_info["orchestrator"]["id"]
        memory_recall_id = deployment_info["agents"]["memory_recall"]["id"]
        
        log_telemetry_event("deployment_loaded", {
            "orchestrator_id": orchestrator_id,
            "memory_recall_id": memory_recall_id
        })
        
        # Initialize client
        client = AIProjectClient.from_connection_string(
            credential=DefaultAzureCredential(),
            conn_str=PROJECT_CONNECTION_STRING
        )
        
        # Create main span
        with tracer.start_as_current_span("memory_recall_orchestration_test") if tracer else nullcontext() as span:
            if span:
                span.set_attribute("session_id", SESSION_ID)
                span.set_attribute("orchestrator_id", orchestrator_id)
                span.set_attribute("memory_recall_id", memory_recall_id)
            
            # Fetch orchestrator to verify tools
            logger.info("\n🔍 Fetching orchestrator configuration...")
            log_telemetry_event("orchestrator_fetch_start", {"orchestrator_id": orchestrator_id})
            
            orchestrator = await client.agents.get_agent(assistant_id=orchestrator_id)
            
            tools_info = []
            if hasattr(orchestrator, 'tools') and orchestrator.tools:
                for tool in orchestrator.tools:
                    tool_info = {
                        "name": getattr(tool, 'name', 'unknown'),
                        "id": getattr(tool, 'agent_id', 'unknown')
                    }
                    tools_info.append(tool_info)
                    logger.info(f"  - Tool: {tool_info['name']} -> Agent: {tool_info['id']}")
            
            log_telemetry_event("orchestrator_fetch_complete", {
                "name": orchestrator.name,
                "tools_count": len(tools_info),
                "tools": tools_info
            })
            
            # Create thread
            thread = await client.agents.create_thread()
            logger.info(f"\n🧵 Created thread: {thread.id}")
            
            # Test scenarios designed to trigger Memory Recall
            test_scenarios = [
                {
                    "name": "pattern_recognition",
                    "query": "Identify patterns in our strategic decision-making over the past quarter",
                    "expected_function": "RecognizePatterns"
                },
                {
                    "name": "context_retrieval", 
                    "query": "Search for any previous initiatives related to customer experience improvements",
                    "expected_function": "RetrieveContext"
                },
                {
                    "name": "historical_analysis",
                    "query": "Analyze how our strategic priorities have evolved over the last 90 days",
                    "expected_function": "AnalyzeHistory"
                },
                {
                    "name": "similarity_search",
                    "query": "Find similar situations where we successfully pivoted our product strategy",
                    "expected_function": "FindSimilar"
                }
            ]
            
            for scenario in test_scenarios:
                logger.info(f"\n{'='*60}")
                logger.info(f"📤 Testing: {scenario['name']}")
                logger.info(f"Query: {scenario['query']}")
                
                log_telemetry_event("query_sent", {
                    "query": scenario['query'],
                    "scenario": scenario['name'],
                    "expected_function": scenario['expected_function']
                })
                
                # Send message
                message = await client.agents.create_message(
                    thread_id=thread.id,
                    role=MessageRole.USER,
                    content=scenario['query']
                )
                
                # Run with span
                run_span = tracer.start_span(f"run_{scenario['name']}") if tracer else None
                if run_span:
                    run_span.set_attribute("scenario", scenario['name'])
                    run_span.set_attribute("query", scenario['query'])
                
                try:
                    # Create run
                    run = await client.agents.create_run(
                        thread_id=thread.id,
                        assistant_id=orchestrator_id
                    )
                    
                    # Wait for completion
                    while run.status in ["queued", "in_progress", "requires_action"]:
                        await asyncio.sleep(1)
                        run = await client.agents.get_run(thread_id=thread.id, run_id=run.id)
                    
                    if run.status == "completed":
                        # Get response
                        messages = await client.agents.list_messages(thread_id=thread.id)
                        
                        for msg in messages.data:
                            if msg.role == MessageRole.ASSISTANT and msg.run_id == run.id:
                                response_text = ""
                                for content in msg.content:
                                    if hasattr(content, 'text') and hasattr(content.text, 'value'):
                                        response_text = content.text.value
                                
                                logger.info(f"\n📥 Response preview: {response_text[:200]}...")
                                
                                # Check for delegation
                                delegation_detected = "Memory Recall specialist" in response_text
                                
                                log_telemetry_event("response_received", {
                                    "scenario": scenario['name'],
                                    "response_length": len(response_text),
                                    "delegation_detected": delegation_detected,
                                    "response_preview": response_text[:200]
                                })
                                
                                if delegation_detected:
                                    logger.info("✅ Delegation confirmed!")
                                    log_telemetry_event("delegation_confirmed", {
                                        "type": "memory_recall",
                                        "scenario": scenario['name']
                                    })
                                
                                if run_span:
                                    run_span.set_attribute("delegation_detected", delegation_detected)
                                    run_span.set_attribute("response_length", len(response_text))
                                
                                break
                    else:
                        logger.error(f"❌ Run failed: {run.status}")
                        if run_span:
                            run_span.set_status(Status(StatusCode.ERROR))
                            
                finally:
                    if run_span:
                        run_span.end()
                
                await asyncio.sleep(2)  # Pause between scenarios
            
            # Final summary
            log_telemetry_event("test_complete", {
                "scenarios_tested": len(test_scenarios),
                "session_id": SESSION_ID
            })
        
        # Save telemetry
        telemetry_dir = Path(__file__).parent.parent / "telemetry" / "memory_recall_agent"
        telemetry_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        short_session = SESSION_ID.split('-')[0]
        telemetry_file = telemetry_dir / f"memory_recall_telemetry_{timestamp}_{short_session}.json"
        
        telemetry_data = {
            "session_id": SESSION_ID,
            "capture_time": datetime.utcnow().isoformat(),
            "events": TELEMETRY_EVENTS
        }
        
        with open(telemetry_file, 'w') as f:
            json.dump(telemetry_data, f, indent=2)
        
        logger.info("\n" + "="*60)
        logger.info("TELEMETRY CAPTURE SUMMARY")
        logger.info("="*60)
        logger.info(f"Session ID: {SESSION_ID}")
        logger.info(f"Events captured: {len(TELEMETRY_EVENTS)}")
        logger.info("="*60)
        
        logger.info(f"\n💾 Telemetry saved to: {telemetry_file}")
        logger.info("\n✅ Telemetry capture complete!")
        logger.info(f"📁 Check the telemetry file for evidence: {telemetry_file}")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {str(e)}")
        log_telemetry_event("error", {"message": str(e)})
        raise

# Context manager for optional spans
class nullcontext:
    def __enter__(self):
        return None
    def __exit__(self, *args):
        pass

if __name__ == "__main__":
    asyncio.run(test_memory_recall_with_telemetry())