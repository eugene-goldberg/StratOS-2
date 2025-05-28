"""
Simple telemetry capture for Memory Recall Agent
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

# Load environment variables
load_dotenv(Path(__file__).parent.parent.parent / '.env')

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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
    
    # Get connection string
    connection_string = os.getenv("AZURE_AI_PROJECT_CONNECTION_STRING")
    if not connection_string:
        logger.error("AZURE_AI_PROJECT_CONNECTION_STRING not found")
        return
    
    async with DefaultAzureCredential() as credential:
        async with AIProjectClient(
            endpoint=connection_string,
            credential=credential
        ) as client:
            # Fetch orchestrator to verify tools
            logger.info("\n🔍 Fetching orchestrator configuration...")
            log_telemetry_event("orchestrator_fetch_start", {"orchestrator_id": orchestrator_id})
            
            orchestrator_def = await client.agents.get_agent(agent_id=orchestrator_id)
            
            tools_info = []
            if hasattr(orchestrator_def, 'tools') and orchestrator_def.tools:
                for tool in orchestrator_def.tools:
                    if hasattr(tool, 'connected_agent'):
                        tool_info = {
                            "name": tool.connected_agent.name,
                            "id": tool.connected_agent.id
                        }
                        tools_info.append(tool_info)
                        logger.info(f"  - Tool: {tool_info['name']} -> Agent: {tool_info['id']}")
            
            log_telemetry_event("orchestrator_fetch_complete", {
                "name": orchestrator_def.name,
                "tools_count": len(tools_info),
                "tools": tools_info
            })
            
            # Create agent instance
            orchestrator_agent = AzureAIAgent(
                client=client,
                definition=orchestrator_def
            )
            
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
                
                # Invoke agent
                response = ""
                async for part in orchestrator_agent.invoke(messages=scenario['query']):
                    if hasattr(part, 'content') and part.content:
                        response += str(part.content)
                
                logger.info(f"\n📥 Response preview: {response[:200]}...")
                
                # Check for delegation
                delegation_detected = "memory recall specialist" in response.lower()
                
                log_telemetry_event("response_received", {
                    "scenario": scenario['name'],
                    "response_length": len(response),
                    "delegation_detected": delegation_detected,
                    "response_preview": response[:200]
                })
                
                if delegation_detected:
                    logger.info("✅ Delegation confirmed!")
                    log_telemetry_event("delegation_confirmed", {
                        "type": "memory_recall",
                        "scenario": scenario['name']
                    })
                
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

if __name__ == "__main__":
    asyncio.run(test_memory_recall_with_telemetry())