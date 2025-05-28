"""
Test script to capture full telemetry traces including tool invocations
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
import sys
from uuid import uuid4

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from azure.ai.projects.aio import AIProjectClient
from azure.identity.aio import DefaultAzureCredential
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv(Path(__file__).parent.parent.parent / '.env')

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Set Azure SDK logging to DEBUG to capture all API calls
logging.getLogger('azure').setLevel(logging.DEBUG)
logging.getLogger('azure.ai.projects').setLevel(logging.DEBUG)

class DetailedTelemetryCapture:
    def __init__(self):
        self.session_id = str(uuid4())
        self.events = []
        
    def capture_event(self, event_type: str, data: dict):
        """Capture a telemetry event with full details"""
        event = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "data": data,
            "session_id": self.session_id
        }
        self.events.append(event)
        logger.info(f"📊 Captured: {event_type} - {json.dumps(data)[:200]}...")
        
    def save_telemetry(self, filename: str):
        """Save telemetry to file"""
        telemetry_data = {
            "session_id": self.session_id,
            "capture_time": datetime.now().isoformat(),
            "events": self.events
        }
        
        with open(filename, 'w') as f:
            json.dump(telemetry_data, f, indent=2)
        logger.info(f"💾 Telemetry saved to: {filename}")

async def test_preference_learning_with_traces():
    """Test Preference Learning Agent with full trace capture"""
    
    telemetry = DetailedTelemetryCapture()
    
    # Get connection details
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
    
    telemetry.capture_event("test_started", {
        "orchestrator_id": orchestrator_id,
        "test_type": "preference_learning_detailed"
    })
    
    try:
        async with DefaultAzureCredential() as credential:
            async with AIProjectClient(
                endpoint=connection_string,
                credential=credential
            ) as client:
                
                # Get orchestrator details
                telemetry.capture_event("fetching_orchestrator", {
                    "orchestrator_id": orchestrator_id
                })
                
                orchestrator = await client.agents.get_agent(orchestrator_id)
                
                telemetry.capture_event("orchestrator_details", {
                    "name": orchestrator.name,
                    "model": orchestrator.model,
                    "tools_count": len(orchestrator.tools) if orchestrator.tools else 0,
                    "tools": [
                        {
                            "type": tool.get("type"),
                            "name": tool.get("connected_agent", {}).get("name") if tool.get("type") == "connected_agent" else tool.get("type"),
                            "id": tool.get("connected_agent", {}).get("id") if tool.get("type") == "connected_agent" else None
                        }
                        for tool in (orchestrator.tools or [])
                    ]
                })
                
                # Create a thread
                telemetry.capture_event("creating_thread", {})
                thread = await client.agents.threads.create()
                telemetry.capture_event("thread_created", {
                    "thread_id": thread.id
                })
                
                # Test query
                query = "Learn from this: User prefers data-driven decisions with visual dashboards"
                
                telemetry.capture_event("sending_message", {
                    "query": query,
                    "thread_id": thread.id
                })
                
                # Create message
                message = await client.agents.threads.messages.create(
                    thread_id=thread.id,
                    role="user",
                    content=query
                )
                
                telemetry.capture_event("message_created", {
                    "message_id": message.id,
                    "role": message.role,
                    "content": message.content
                })
                
                # Create run
                telemetry.capture_event("creating_run", {
                    "thread_id": thread.id,
                    "assistant_id": orchestrator_id
                })
                
                run = await client.agents.threads.runs.create(
                    thread_id=thread.id,
                    assistant_id=orchestrator_id
                )
                
                telemetry.capture_event("run_created", {
                    "run_id": run.id,
                    "status": run.status.value if hasattr(run.status, 'value') else str(run.status)
                })
                
                # Poll for completion
                while run.status in ["queued", "in_progress", "requires_action"]:
                    await asyncio.sleep(0.5)
                    
                    run = await client.agents.threads.runs.get(
                        thread_id=thread.id,
                        run_id=run.id
                    )
                    
                    telemetry.capture_event("run_status_update", {
                        "run_id": run.id,
                        "status": run.status.value if hasattr(run.status, 'value') else str(run.status),
                        "required_action": run.required_action if hasattr(run, 'required_action') and run.required_action else None
                    })
                    
                    # Check for tool calls
                    if run.status == "requires_action" and run.required_action:
                        if hasattr(run.required_action, 'submit_tool_outputs'):
                            tool_calls = run.required_action.submit_tool_outputs.tool_calls
                            
                            for tool_call in tool_calls:
                                telemetry.capture_event("tool_call_required", {
                                    "tool_call_id": tool_call.id,
                                    "function_name": tool_call.function.name,
                                    "function_arguments": tool_call.function.arguments
                                })
                
                # Get run steps to see tool invocations
                telemetry.capture_event("fetching_run_steps", {
                    "thread_id": thread.id,
                    "run_id": run.id
                })
                
                steps = []
                async for step in client.agents.threads.runs.steps.list(
                    thread_id=thread.id,
                    run_id=run.id
                ):
                    step_data = {
                        "step_id": step.id,
                        "type": step.type,
                        "status": step.status.value if hasattr(step.status, 'value') else str(step.status),
                        "created_at": step.created_at
                    }
                    
                    # Capture tool call details
                    if hasattr(step, 'step_details') and step.step_details:
                        if hasattr(step.step_details, 'tool_calls') and step.step_details.tool_calls:
                            step_data["tool_calls"] = []
                            for tc in step.step_details.tool_calls:
                                tool_call_data = {
                                    "id": tc.id if hasattr(tc, 'id') else None,
                                    "type": tc.type if hasattr(tc, 'type') else None
                                }
                                
                                # Get function details if available
                                if hasattr(tc, 'function'):
                                    tool_call_data["function"] = {
                                        "name": tc.function.name if hasattr(tc.function, 'name') else None,
                                        "arguments": tc.function.arguments if hasattr(tc.function, 'arguments') else None,
                                        "output": tc.function.output if hasattr(tc.function, 'output') else None
                                    }
                                    
                                step_data["tool_calls"].append(tool_call_data)
                    
                    steps.append(step_data)
                    telemetry.capture_event("run_step", step_data)
                
                # Get final messages
                telemetry.capture_event("fetching_messages", {
                    "thread_id": thread.id
                })
                
                messages = []
                async for msg in client.agents.threads.messages.list(thread_id=thread.id):
                    msg_data = {
                        "message_id": msg.id,
                        "role": msg.role,
                        "content": msg.content[0].text.value if msg.content and len(msg.content) > 0 and hasattr(msg.content[0], 'text') else str(msg.content),
                        "created_at": msg.created_at
                    }
                    messages.append(msg_data)
                    telemetry.capture_event("message", msg_data)
                
                # Capture final response
                if messages and messages[0]["role"] == "assistant":
                    telemetry.capture_event("final_response", {
                        "response": messages[0]["content"],
                        "delegation_detected": "I'll connect you with" in messages[0]["content"]
                    })
                
                telemetry.capture_event("test_completed", {
                    "total_steps": len(steps),
                    "total_messages": len(messages),
                    "success": run.status == "completed"
                })
                
    except Exception as e:
        telemetry.capture_event("error", {
            "error_type": type(e).__name__,
            "error_message": str(e)
        })
        logger.error(f"Test failed: {e}", exc_info=True)
    
    # Save telemetry
    output_dir = Path(__file__).parent.parent / "telemetry" / "detailed_traces"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = output_dir / f"preference_learning_detailed_trace_{timestamp}.json"
    
    telemetry.save_telemetry(filename)
    
    return filename

if __name__ == "__main__":
    asyncio.run(test_preference_learning_with_traces())