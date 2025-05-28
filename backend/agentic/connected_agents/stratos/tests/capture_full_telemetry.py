"""
Capture full telemetry traces for all agents
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
import sys
import os

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from azure.ai.projects.aio import AIProjectClient
from azure.identity.aio import DefaultAzureCredential
from dotenv import load_dotenv

# Load environment variables
load_dotenv(Path(__file__).parent.parent.parent / '.env')

# Configure logging with detailed format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Detailed telemetry storage
TELEMETRY_DATA = {
    "session_start": datetime.now().isoformat(),
    "agents": {}
}

async def test_agent_with_full_telemetry(agent_name: str, orchestrator_id: str, query: str):
    """Test a single agent and capture full telemetry"""
    
    logger.info(f"\n{'='*60}")
    logger.info(f"Testing {agent_name} with full telemetry capture")
    logger.info(f"{'='*60}")
    
    agent_telemetry = {
        "name": agent_name,
        "query": query,
        "start_time": datetime.now().isoformat(),
        "events": []
    }
    
    connection_string = os.getenv("AZURE_AI_PROJECT_CONNECTION_STRING")
    if not connection_string:
        logger.error("AZURE_AI_PROJECT_CONNECTION_STRING not found")
        return
    
    try:
        async with DefaultAzureCredential() as credential:
            async with AIProjectClient(
                endpoint=connection_string,
                credential=credential
            ) as client:
                
                # 1. Get orchestrator details with tools
                logger.info(f"📋 Fetching orchestrator tools...")
                orchestrator = await client.agents.get_agent(orchestrator_id)
                
                tools_info = []
                if orchestrator.tools:
                    for tool in orchestrator.tools:
                        if tool.get("type") == "connected_agent":
                            tool_info = {
                                "type": "connected_agent",
                                "name": tool["connected_agent"]["name"],
                                "id": tool["connected_agent"]["id"]
                            }
                            tools_info.append(tool_info)
                
                agent_telemetry["events"].append({
                    "type": "orchestrator_tools",
                    "time": datetime.now().isoformat(),
                    "data": {
                        "orchestrator_id": orchestrator_id,
                        "orchestrator_name": orchestrator.name,
                        "tools": tools_info
                    }
                })
                
                # 2. Create thread
                logger.info(f"🧵 Creating thread...")
                thread = await client.agents.create_thread()
                thread_id = thread.id
                
                agent_telemetry["events"].append({
                    "type": "thread_created",
                    "time": datetime.now().isoformat(),
                    "data": {"thread_id": thread_id}
                })
                
                # 3. Create message
                logger.info(f"💬 Sending query: {query[:100]}...")
                message = await client.agents.create_message(
                    thread_id=thread_id,
                    role="user",
                    content=query
                )
                
                agent_telemetry["events"].append({
                    "type": "message_sent",
                    "time": datetime.now().isoformat(),
                    "data": {
                        "message_id": message.id,
                        "content": query
                    }
                })
                
                # 4. Create and monitor run
                logger.info(f"🏃 Creating run...")
                run = await client.agents.create_run(
                    thread_id=thread_id,
                    assistant_id=orchestrator_id
                )
                
                agent_telemetry["events"].append({
                    "type": "run_created",
                    "time": datetime.now().isoformat(),
                    "data": {
                        "run_id": run.id,
                        "initial_status": run.status
                    }
                })
                
                # 5. Poll for completion and capture status changes
                logger.info(f"⏳ Waiting for completion...")
                status_history = []
                while run.status in ["queued", "in_progress", "requires_action"]:
                    await asyncio.sleep(0.5)
                    run = await client.agents.get_run(thread_id=thread_id, run_id=run.id)
                    
                    status_event = {
                        "time": datetime.now().isoformat(),
                        "status": run.status,
                        "details": {}
                    }
                    
                    # Capture tool calls if in requires_action state
                    if run.status == "requires_action" and run.required_action:
                        if hasattr(run.required_action, 'submit_tool_outputs'):
                            tool_calls = []
                            for tc in run.required_action.submit_tool_outputs.tool_calls:
                                tool_calls.append({
                                    "id": tc.id,
                                    "function": tc.function.name,
                                    "arguments": tc.function.arguments
                                })
                            status_event["details"]["tool_calls"] = tool_calls
                    
                    status_history.append(status_event)
                
                agent_telemetry["events"].append({
                    "type": "run_status_history",
                    "time": datetime.now().isoformat(),
                    "data": {
                        "final_status": run.status,
                        "history": status_history
                    }
                })
                
                # 6. Get run steps for tool invocations
                logger.info(f"📜 Fetching run steps...")
                steps = await client.agents.list_run_steps(thread_id=thread_id, run_id=run.id)
                
                steps_data = []
                for step in steps.data:
                    step_info = {
                        "id": step.id,
                        "type": step.type,
                        "status": step.status,
                        "created_at": step.created_at
                    }
                    
                    # Capture tool calls in steps
                    if hasattr(step, 'step_details') and step.step_details:
                        if hasattr(step.step_details, 'tool_calls'):
                            tool_calls = []
                            for tc in step.step_details.tool_calls:
                                tc_data = {
                                    "type": getattr(tc, 'type', 'unknown')
                                }
                                
                                # For connected_agent type
                                if hasattr(tc, 'connected_agent'):
                                    tc_data["connected_agent"] = {
                                        "id": tc.connected_agent.id if hasattr(tc.connected_agent, 'id') else None,
                                        "assistant_id": tc.connected_agent.assistant_id if hasattr(tc.connected_agent, 'assistant_id') else None
                                    }
                                
                                tool_calls.append(tc_data)
                            step_info["tool_calls"] = tool_calls
                    
                    steps_data.append(step_info)
                
                agent_telemetry["events"].append({
                    "type": "run_steps",
                    "time": datetime.now().isoformat(),
                    "data": {"steps": steps_data}
                })
                
                # 7. Get final messages
                logger.info(f"📨 Fetching response...")
                messages = await client.agents.list_messages(thread_id=thread_id)
                
                response_text = ""
                for msg in messages.data:
                    if msg.role == "assistant" and msg.run_id == run.id:
                        for content in msg.content:
                            if hasattr(content, 'text') and hasattr(content.text, 'value'):
                                response_text = content.text.value
                                break
                        break
                
                agent_telemetry["events"].append({
                    "type": "response_received",
                    "time": datetime.now().isoformat(),
                    "data": {
                        "response": response_text,
                        "delegation_detected": "I'll connect you with" in response_text,
                        "specialist_mentioned": any(spec in response_text.lower() for spec in ["ceo log", "north star", "memory recall", "preference learning"])
                    }
                })
                
                # Log summary
                logger.info(f"\n✅ Response received:")
                logger.info(f"   Length: {len(response_text)} chars")
                logger.info(f"   Delegation: {'Yes' if 'I\'ll connect you with' in response_text else 'No'}")
                logger.info(f"   Preview: {response_text[:200]}...")
                
                agent_telemetry["end_time"] = datetime.now().isoformat()
                agent_telemetry["success"] = True
                
    except Exception as e:
        logger.error(f"❌ Error testing {agent_name}: {e}")
        agent_telemetry["events"].append({
            "type": "error",
            "time": datetime.now().isoformat(),
            "data": {
                "error_type": type(e).__name__,
                "error_message": str(e)
            }
        })
        agent_telemetry["success"] = False
    
    TELEMETRY_DATA["agents"][agent_name] = agent_telemetry

async def main():
    """Test all agents and capture full telemetry"""
    
    # Load deployment info
    deployment_file = Path(__file__).parent.parent / "archive/stratos_deployment_info.json"
    if not deployment_file.exists():
        logger.error("Deployment info not found. Please deploy agents first.")
        return
    
    with open(deployment_file, 'r') as f:
        deployment_info = json.load(f)
    
    orchestrator_id = deployment_info["orchestrator"]["id"]
    
    # Test scenarios for each agent
    test_cases = [
        ("CEO Log", "Generate insights from this CEO observation: Team morale is high after successful product launch"),
        ("North Star", "What should be our company vision for AI-driven healthcare?"),
        ("Memory Recall", "What patterns have we seen in past strategic pivots?"),
        ("Preference Learning", "Learn this: User prefers visual dashboards over text reports")
    ]
    
    # Run tests
    for agent_name, query in test_cases:
        await test_agent_with_full_telemetry(agent_name, orchestrator_id, query)
        await asyncio.sleep(10)  # Delay between tests
    
    # Save full telemetry
    TELEMETRY_DATA["session_end"] = datetime.now().isoformat()
    
    output_dir = Path(__file__).parent.parent / "telemetry" / "full_traces"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = output_dir / f"all_agents_full_telemetry_{timestamp}.json"
    
    with open(filename, 'w') as f:
        json.dump(TELEMETRY_DATA, f, indent=2)
    
    logger.info(f"\n💾 Full telemetry saved to: {filename}")
    
    # Print summary
    logger.info("\n" + "="*60)
    logger.info("TELEMETRY CAPTURE SUMMARY")
    logger.info("="*60)
    
    for agent_name, data in TELEMETRY_DATA["agents"].items():
        success = data.get("success", False)
        events_count = len(data.get("events", []))
        delegation = False
        
        # Check for delegation in response
        for event in data.get("events", []):
            if event["type"] == "response_received":
                delegation = event["data"].get("delegation_detected", False)
        
        logger.info(f"\n{agent_name}:")
        logger.info(f"  Status: {'✅ Success' if success else '❌ Failed'}")
        logger.info(f"  Events captured: {events_count}")
        logger.info(f"  Delegation: {'✅ Yes' if delegation else '❌ No'}")

if __name__ == "__main__":
    asyncio.run(main())