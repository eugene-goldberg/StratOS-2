"""
Display raw API traces from a test run showing tool invocations
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
import sys
import os
from typing import Dict, Any

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from azure.ai.projects.aio import AIProjectClient
from azure.identity.aio import DefaultAzureCredential
from dotenv import load_dotenv

# Load environment variables
load_dotenv(Path(__file__).parent.parent.parent / '.env')

# Configure logging to capture everything
logging.basicConfig(
    level=logging.DEBUG,
    format='%(message)s'
)
logger = logging.getLogger(__name__)

# Capture all Azure HTTP requests/responses
logging.getLogger('azure.core.pipeline.policies.http_logging_policy').setLevel(logging.DEBUG)

class APITraceCapture:
    def __init__(self):
        self.traces = []
        
    def add_trace(self, trace_type: str, data: Dict[str, Any]):
        self.traces.append({
            "timestamp": datetime.now().isoformat(),
            "type": trace_type,
            "data": data
        })

async def run_single_query_with_traces():
    """Run a single query and capture all API traces"""
    
    logger.info("\n" + "="*80)
    logger.info("CAPTURING RAW API TRACES FOR PREFERENCE LEARNING AGENT")
    logger.info("="*80 + "\n")
    
    tracer = APITraceCapture()
    
    connection_string = os.getenv("AZURE_AI_PROJECT_CONNECTION_STRING")
    if not connection_string:
        logger.error("AZURE_AI_PROJECT_CONNECTION_STRING not found")
        return
        
    # Load deployment info
    deployment_file = Path(__file__).parent.parent / "archive/stratos_deployment_info.json"
    if not deployment_file.exists():
        logger.error("Deployment info not found")
        return
        
    with open(deployment_file, 'r') as f:
        deployment_info = json.load(f)
    
    orchestrator_id = deployment_info["orchestrator"]["id"]
    
    try:
        async with DefaultAzureCredential() as credential:
            async with AIProjectClient(
                endpoint=connection_string,
                credential=credential
            ) as client:
                
                logger.info("1️⃣ FETCHING ORCHESTRATOR WITH CONNECTED AGENTS")
                logger.info("-" * 60)
                
                orchestrator = await client.agents.get_agent(orchestrator_id)
                
                logger.info(f"Orchestrator: {orchestrator.name}")
                logger.info(f"Model: {orchestrator.model}")
                logger.info(f"Tools: {len(orchestrator.tools) if orchestrator.tools else 0}")
                
                if orchestrator.tools:
                    logger.info("\nConnected Agents (Tools):")
                    for tool in orchestrator.tools:
                        if tool.get("type") == "connected_agent":
                            logger.info(f"  - {tool['connected_agent']['name']}: {tool['connected_agent']['id']}")
                
                tracer.add_trace("orchestrator_fetched", {
                    "id": orchestrator_id,
                    "name": orchestrator.name,
                    "tools": orchestrator.tools
                })
                
                logger.info("\n2️⃣ CREATING THREAD")
                logger.info("-" * 60)
                
                thread = await client.agents.create_thread()
                logger.info(f"Thread created: {thread.id}")
                
                tracer.add_trace("thread_created", {"thread_id": thread.id})
                
                logger.info("\n3️⃣ SENDING MESSAGE")
                logger.info("-" * 60)
                
                query = "Learn from this: User prefers data-driven decisions with visual dashboards"
                logger.info(f"Query: {query}")
                
                message = await client.agents.create_message(
                    thread_id=thread.id,
                    role="user",
                    content=query
                )
                
                logger.info(f"Message created: {message.id}")
                
                tracer.add_trace("message_sent", {
                    "message_id": message.id,
                    "content": query
                })
                
                logger.info("\n4️⃣ CREATING RUN")
                logger.info("-" * 60)
                
                run = await client.agents.create_run(
                    thread_id=thread.id,
                    assistant_id=orchestrator_id
                )
                
                logger.info(f"Run created: {run.id}")
                logger.info(f"Initial status: {run.status}")
                
                tracer.add_trace("run_created", {
                    "run_id": run.id,
                    "status": run.status
                })
                
                logger.info("\n5️⃣ MONITORING RUN STATUS")
                logger.info("-" * 60)
                
                while run.status in ["queued", "in_progress", "requires_action"]:
                    await asyncio.sleep(0.5)
                    run = await client.agents.get_run(thread_id=thread.id, run_id=run.id)
                    logger.info(f"Status: {run.status}")
                    
                    if run.status == "requires_action" and run.required_action:
                        logger.info("\n⚡ TOOL INVOCATION REQUIRED!")
                        if hasattr(run.required_action, 'submit_tool_outputs'):
                            for tc in run.required_action.submit_tool_outputs.tool_calls:
                                logger.info(f"  Tool Call ID: {tc.id}")
                                logger.info(f"  Function: {tc.function.name}")
                                logger.info(f"  Arguments: {tc.function.arguments}")
                                
                                tracer.add_trace("tool_call", {
                                    "id": tc.id,
                                    "function": tc.function.name,
                                    "arguments": tc.function.arguments
                                })
                
                logger.info(f"\nFinal status: {run.status}")
                
                logger.info("\n6️⃣ FETCHING RUN STEPS (TOOL INVOCATIONS)")
                logger.info("-" * 60)
                
                steps = await client.agents.list_run_steps(thread_id=thread.id, run_id=run.id)
                
                for idx, step in enumerate(steps.data):
                    logger.info(f"\nStep {idx + 1}:")
                    logger.info(f"  ID: {step.id}")
                    logger.info(f"  Type: {step.type}")
                    logger.info(f"  Status: {step.status}")
                    
                    if hasattr(step, 'step_details') and step.step_details:
                        if hasattr(step.step_details, 'tool_calls') and step.step_details.tool_calls:
                            logger.info("  Tool Calls:")
                            for tc in step.step_details.tool_calls:
                                logger.info(f"    - Type: {getattr(tc, 'type', 'unknown')}")
                                
                                if hasattr(tc, 'connected_agent'):
                                    logger.info(f"      Connected Agent ID: {tc.connected_agent.id if hasattr(tc.connected_agent, 'id') else 'N/A'}")
                                    logger.info(f"      Assistant ID: {tc.connected_agent.assistant_id if hasattr(tc.connected_agent, 'assistant_id') else 'N/A'}")
                                    
                                    tracer.add_trace("connected_agent_invoked", {
                                        "step_id": step.id,
                                        "agent_id": tc.connected_agent.id if hasattr(tc.connected_agent, 'id') else None,
                                        "assistant_id": tc.connected_agent.assistant_id if hasattr(tc.connected_agent, 'assistant_id') else None
                                    })
                
                logger.info("\n7️⃣ FETCHING RESPONSE")
                logger.info("-" * 60)
                
                messages = await client.agents.list_messages(thread_id=thread.id)
                
                for msg in messages.data:
                    if msg.role == "assistant" and msg.run_id == run.id:
                        logger.info(f"\nAssistant Response:")
                        for content in msg.content:
                            if hasattr(content, 'text') and hasattr(content.text, 'value'):
                                response = content.text.value
                                logger.info(f"{response}")
                                
                                tracer.add_trace("response", {
                                    "message_id": msg.id,
                                    "content": response,
                                    "delegation_detected": "I'll connect you with" in response
                                })
                                break
                        break
                
                # Save traces
                output_dir = Path(__file__).parent.parent / "telemetry" / "raw_api_traces"
                output_dir.mkdir(parents=True, exist_ok=True)
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = output_dir / f"api_traces_{timestamp}.json"
                
                with open(filename, 'w') as f:
                    json.dump({
                        "query": query,
                        "orchestrator_id": orchestrator_id,
                        "traces": tracer.traces
                    }, f, indent=2)
                
                logger.info(f"\n\n💾 Raw API traces saved to: {filename}")
                
    except Exception as e:
        logger.error(f"\n❌ Error: {e}", exc_info=True)

if __name__ == "__main__":
    # Disable other loggers to reduce noise
    for name in ['azure.identity', 'azure.core.pipeline', 'msal']:
        if name != 'azure.core.pipeline.policies.http_logging_policy':
            logging.getLogger(name).setLevel(logging.WARNING)
    
    asyncio.run(run_single_query_with_traces())