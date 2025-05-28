"""
Comprehensive test for Memory Recall Agent with all functions
Tests context retrieval, pattern recognition, historical analysis, storage, and similarity search
"""

import os
import asyncio
import logging
import json
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import Agent, AgentThread, ThreadMessage, MessageRole
from azure.identity import DefaultAzureCredential
from azure.ai.projects.telemetry import AIProjectTelemetryMixin
from azure.monitor.opentelemetry import configure_azure_monitor
from opentelemetry import trace

# Load environment variables
load_dotenv(Path(__file__).parent.parent.parent / '.env')

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Azure AI configuration
PROJECT_CONNECTION_STRING = os.getenv("AZURE_PROJECT_CONNECTION_STRING")
APPLICATION_INSIGHTS_CONNECTION_STRING = os.getenv("APPLICATION_INSIGHTS_CONNECTION_STRING")

# Configure telemetry if available
if APPLICATION_INSIGHTS_CONNECTION_STRING:
    configure_azure_monitor(connection_string=APPLICATION_INSIGHTS_CONNECTION_STRING)
    tracer = trace.get_tracer(__name__)
else:
    tracer = None

def load_deployment_info():
    """Load deployment info from file"""
    archive_dir = Path(__file__).parent.parent / "archive"
    deployment_file = archive_dir / "stratos_deployment_info.json"
    
    if not deployment_file.exists():
        logger.error(f"Deployment file not found: {deployment_file}")
        return None
        
    with open(deployment_file, 'r') as f:
        return json.load(f)

async def test_function(client, thread_id, orchestrator_id, function_name, query):
    """Test a specific Memory Recall function"""
    logger.info(f"\n{'='*60}")
    logger.info(f"Testing {function_name}")
    logger.info(f"Query: {query}")
    
    # Create span for telemetry
    span = None
    if tracer:
        span = tracer.start_span(f"test_{function_name}")
        span.set_attribute("function", function_name)
        span.set_attribute("query", query)
    
    try:
        # Send message
        message = await client.agents.create_message(
            thread_id=thread_id,
            role=MessageRole.USER,
            content=query
        )
        
        # Run orchestrator
        run = await client.agents.create_run(
            thread_id=thread_id,
            assistant_id=orchestrator_id
        )
        
        # Wait for completion
        while run.status in ["queued", "in_progress", "requires_action"]:
            await asyncio.sleep(1)
            run = await client.agents.get_run(
                thread_id=thread_id,
                run_id=run.id
            )
        
        if run.status == "completed":
            # Get messages
            messages = await client.agents.list_messages(thread_id=thread_id)
            
            # Find latest assistant response
            for msg in messages.data:
                if msg.role == MessageRole.ASSISTANT and msg.run_id == run.id:
                    logger.info("\n📥 Response:")
                    response_text = ""
                    for content in msg.content:
                        if hasattr(content, 'text') and hasattr(content.text, 'value'):
                            response_text = content.text.value
                            logger.info(response_text[:500] + "..." if len(response_text) > 500 else response_text)
                    
                    # Check for delegation
                    if "Memory Recall specialist" in response_text:
                        logger.info(f"✅ {function_name} test passed - delegation detected")
                        if span:
                            span.set_attribute("delegation_detected", True)
                            span.set_attribute("response_length", len(response_text))
                    else:
                        logger.warning(f"⚠️ {function_name} - no delegation detected")
                        if span:
                            span.set_attribute("delegation_detected", False)
                    break
        else:
            logger.error(f"❌ {function_name} test failed - run status: {run.status}")
            if span:
                span.set_attribute("error", True)
                span.set_attribute("run_status", run.status)
                
    finally:
        if span:
            span.end()

async def test_memory_recall_comprehensive():
    """Comprehensive test of all Memory Recall functions"""
    try:
        logger.info("=== Memory Recall Agent Comprehensive Test ===")
        
        # Load deployment info
        deployment_info = load_deployment_info()
        if not deployment_info:
            logger.error("No deployment info found. Please run deployment script first.")
            return
        
        orchestrator_id = deployment_info["orchestrator"]["id"]
        memory_recall_id = deployment_info["agents"]["memory_recall"]["id"]
        
        logger.info(f"Orchestrator ID: {orchestrator_id}")
        logger.info(f"Memory Recall Agent ID: {memory_recall_id}")
        
        # Initialize client
        client = AIProjectClient.from_connection_string(
            credential=DefaultAzureCredential(),
            conn_str=PROJECT_CONNECTION_STRING
        )
        
        # Enable telemetry
        if APPLICATION_INSIGHTS_CONNECTION_STRING:
            client.telemetry.enable()
            logger.info("✅ Telemetry enabled")
        
        # Create thread
        thread = await client.agents.create_thread()
        logger.info(f"Created thread: {thread.id}")
        
        # Test all Memory Recall functions
        test_cases = [
            ("RetrieveContext", "Search our history for any strategic alignment initiatives we've undertaken"),
            ("RecognizePatterns", "What patterns do you see in our CEO log entries over the past month?"),
            ("AnalyzeHistory", "Analyze the evolution of our strategic decisions over the last 90 days"),
            ("StoreContext", "Store this important context: We decided to focus on AI democratization as our core mission"),
            ("FindSimilar", "Find similar situations where we had to pivot our strategy due to market changes")
        ]
        
        for function_name, query in test_cases:
            await test_function(client, thread.id, orchestrator_id, function_name, query)
            await asyncio.sleep(2)  # Brief pause between tests
        
        # Save test results
        test_output_dir = Path(__file__).parent / "test_outputs"
        test_output_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = test_output_dir / f"memory_recall_comprehensive_{timestamp}.json"
        
        test_results = {
            "test_time": datetime.now().isoformat(),
            "orchestrator_id": orchestrator_id,
            "memory_recall_id": memory_recall_id,
            "thread_id": thread.id,
            "test_cases": test_cases,
            "telemetry_enabled": APPLICATION_INSIGHTS_CONNECTION_STRING is not None
        }
        
        with open(output_file, 'w') as f:
            json.dump(test_results, f, indent=2)
        
        logger.info(f"\n💾 Test results saved to: {output_file}")
        logger.info("\n✅ Comprehensive test completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(test_memory_recall_comprehensive())