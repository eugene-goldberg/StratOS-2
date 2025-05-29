#!/usr/bin/env python3
"""
Capture and display telemetry data in real-time during StratOS agent tests.
This script shows detailed request/response data and timing information.
"""

import asyncio
import os
import logging
import json
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime
import time

# Load environment variables
load_dotenv()

# Import Azure SDK components
from azure.identity.aio import DefaultAzureCredential
from azure.ai.projects.aio import AIProjectClient
from semantic_kernel.agents import AzureAIAgent

# Configure detailed logging to capture HTTP traffic
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f'stratos_telemetry_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)
logger = logging.getLogger(__name__)

# Enable Azure SDK HTTP logging
logging.getLogger('azure').setLevel(logging.WARNING)
logging.getLogger('azure.core.pipeline.policies.http_logging_policy').setLevel(logging.INFO)


class TelemetryCapture:
    """Capture detailed telemetry during test execution."""
    
    def __init__(self):
        self.events = []
        self.start_time = datetime.now()
        
    def log_event(self, event_type, data):
        """Log an event with timestamp and duration."""
        event = {
            "timestamp": datetime.now().isoformat(),
            "duration_ms": (datetime.now() - self.start_time).total_seconds() * 1000,
            "type": event_type,
            "data": data
        }
        self.events.append(event)
        
        # Also log to console
        logger.info(f"📊 {event_type}: {json.dumps(data, indent=2)}")
        
    def save_to_file(self, filename):
        """Save telemetry to file."""
        with open(filename, 'w') as f:
            json.dump({
                "start_time": self.start_time.isoformat(),
                "end_time": datetime.now().isoformat(),
                "duration_seconds": (datetime.now() - self.start_time).total_seconds(),
                "events": self.events
            }, f, indent=2)
        logger.info(f"💾 Telemetry saved to: {filename}")


async def capture_agent_telemetry():
    """Run tests and capture detailed telemetry."""
    
    telemetry = TelemetryCapture()
    
    # Load deployment info
    deployment_file = Path(__file__).parent / "stratos" / "archive" / "stratos_deployment_info.json"
    if not deployment_file.exists():
        logger.error("Deployment info not found")
        return
        
    with open(deployment_file, 'r') as f:
        deployment_info = json.load(f)
    
    orchestrator_id = deployment_info["orchestrator"]["id"]
    telemetry.log_event("deployment_info_loaded", {
        "orchestrator_id": orchestrator_id,
        "agents": list(deployment_info["agents"].keys())
    })
    
    endpoint = os.getenv("AZURE_AI_PROJECT_CONNECTION_STRING")
    if not endpoint:
        logger.error("AZURE_AI_PROJECT_CONNECTION_STRING not found")
        return
    
    logger.info("="*80)
    logger.info("STRATOS TELEMETRY CAPTURE")
    logger.info("="*80)
    
    async with DefaultAzureCredential() as credential, \
               AIProjectClient(endpoint=endpoint, credential=credential) as client:
        
        # Get orchestrator details
        telemetry.log_event("fetching_orchestrator", {"id": orchestrator_id})
        start = time.time()
        
        orchestrator_def = await client.agents.get_agent(agent_id=orchestrator_id)
        
        telemetry.log_event("orchestrator_fetched", {
            "duration_ms": (time.time() - start) * 1000,
            "name": orchestrator_def.name,
            "model": orchestrator_def.model,
            "tools_count": len(orchestrator_def.tools) if orchestrator_def.tools else 0,
            "tools": [
                {
                    "type": tool.get("type"),
                    "name": tool.get("connected_agent", {}).get("name") if tool.get("type") == "connected_agent" else tool.get("type")
                }
                for tool in (orchestrator_def.tools or [])
            ]
        })
        
        # Create agent instance
        orchestrator_agent = AzureAIAgent(
            client=client,
            definition=orchestrator_def
        )
        
        # Test a single query with detailed telemetry
        query = "I need to log this important update: Team successfully deployed new AI features"
        
        logger.info(f"\n📝 Testing query: {query}")
        telemetry.log_event("query_start", {"query": query})
        
        # Create thread
        thread_start = time.time()
        thread = await client.agents.create_thread()
        thread_duration = (time.time() - thread_start) * 1000
        
        telemetry.log_event("thread_created", {
            "thread_id": thread.id,
            "duration_ms": thread_duration
        })
        
        # Add message
        msg_start = time.time()
        message = await client.agents.create_message(
            thread_id=thread.id,
            role="user", 
            content=query
        )
        msg_duration = (time.time() - msg_start) * 1000
        
        telemetry.log_event("message_created", {
            "message_id": message.id,
            "duration_ms": msg_duration
        })
        
        # Create run
        run_start = time.time()
        run = await client.agents.create_run(
            thread_id=thread.id,
            assistant_id=orchestrator_id
        )
        run_duration = (time.time() - run_start) * 1000
        
        telemetry.log_event("run_created", {
            "run_id": run.id,
            "initial_status": run.status,
            "duration_ms": run_duration
        })
        
        # Poll for completion
        poll_count = 0
        status_changes = []
        
        while run.status in ["queued", "in_progress", "requires_action"]:
            poll_start = time.time()
            await asyncio.sleep(0.5)
            
            run = await client.agents.get_run(
                thread_id=thread.id,
                run_id=run.id
            )
            poll_duration = (time.time() - poll_start) * 1000
            poll_count += 1
            
            status_changes.append({
                "poll_number": poll_count,
                "status": run.status,
                "duration_ms": poll_duration,
                "timestamp": datetime.now().isoformat()
            })
            
            if run.status == "requires_action":
                telemetry.log_event("requires_action", {
                    "run_id": run.id,
                    "action_type": "tool_calls" if hasattr(run.required_action, 'submit_tool_outputs') else "unknown"
                })
        
        total_run_duration = (time.time() - run_start) * 1000
        
        telemetry.log_event("run_completed", {
            "run_id": run.id,
            "final_status": run.status,
            "total_duration_ms": total_run_duration,
            "poll_count": poll_count,
            "status_changes": status_changes
        })
        
        # Get run steps
        steps_start = time.time()
        steps_response = await client.agents.list_run_steps(
            thread_id=thread.id,
            run_id=run.id
        )
        steps_duration = (time.time() - steps_start) * 1000
        
        steps_data = []
        for step in steps_response.data:
            step_info = {
                "id": step.id,
                "type": step.type,
                "status": step.status,
                "created_at": step.created_at
            }
            
            # Check for tool calls
            if hasattr(step, 'step_details') and hasattr(step.step_details, 'tool_calls'):
                tool_calls = []
                for tc in step.step_details.tool_calls:
                    tc_info = {"type": getattr(tc, 'type', 'unknown')}
                    
                    if hasattr(tc, 'connected_agent'):
                        tc_info["connected_agent"] = {
                            "assistant_id": getattr(tc.connected_agent, 'assistant_id', None)
                        }
                    
                    tool_calls.append(tc_info)
                step_info["tool_calls"] = tool_calls
            
            steps_data.append(step_info)
        
        telemetry.log_event("run_steps_fetched", {
            "duration_ms": steps_duration,
            "steps_count": len(steps_data),
            "steps": steps_data
        })
        
        # Get messages
        messages_start = time.time()
        messages_response = await client.agents.list_messages(thread_id=thread.id)
        messages_duration = (time.time() - messages_start) * 1000
        
        response_text = ""
        for msg in messages_response.data:
            if msg.role == "assistant" and msg.run_id == run.id:
                for content in msg.content:
                    if hasattr(content, 'text') and hasattr(content.text, 'value'):
                        response_text = content.text.value
                        break
                break
        
        telemetry.log_event("response_received", {
            "duration_ms": messages_duration,
            "response_length": len(response_text),
            "response_preview": response_text[:200] + "..." if len(response_text) > 200 else response_text,
            "delegation_detected": "I'll connect you with" in response_text,
            "ceo_log_mentioned": "ceo log" in response_text.lower()
        })
        
        # Summary
        logger.info("\n" + "="*80)
        logger.info("TELEMETRY SUMMARY")
        logger.info("="*80)
        
        total_duration = (datetime.now() - telemetry.start_time).total_seconds()
        logger.info(f"Total test duration: {total_duration:.2f} seconds")
        logger.info(f"Total events captured: {len(telemetry.events)}")
        
        # Performance breakdown
        logger.info("\nPerformance Breakdown:")
        logger.info(f"  - Thread creation: {thread_duration:.0f}ms")
        logger.info(f"  - Message creation: {msg_duration:.0f}ms")
        logger.info(f"  - Run creation: {run_duration:.0f}ms")
        logger.info(f"  - Run execution: {total_run_duration:.0f}ms")
        logger.info(f"  - Steps fetch: {steps_duration:.0f}ms")
        logger.info(f"  - Messages fetch: {messages_duration:.0f}ms")
        logger.info(f"  - Total API calls: {5 + poll_count}")
        
        # Save telemetry
        output_file = f"stratos_telemetry_capture_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        telemetry.save_to_file(output_file)
        
        # Display key insights
        logger.info("\n" + "="*80)
        logger.info("KEY INSIGHTS")
        logger.info("="*80)
        
        if steps_data:
            logger.info("\nRun Steps:")
            for step in steps_data:
                logger.info(f"  - {step['type']}: {step['status']}")
                if 'tool_calls' in step:
                    for tc in step['tool_calls']:
                        if 'connected_agent' in tc:
                            logger.info(f"    → Delegated to: {tc['connected_agent']['assistant_id']}")
        
        logger.info(f"\nResponse Analysis:")
        logger.info(f"  - Length: {len(response_text)} characters")
        logger.info(f"  - Delegation: {'Yes' if 'I\'ll connect you with' in response_text else 'No'}")
        logger.info(f"  - CEO Log Agent: {'Yes' if 'ceo log' in response_text.lower() else 'No'}")


if __name__ == "__main__":
    asyncio.run(capture_agent_telemetry())