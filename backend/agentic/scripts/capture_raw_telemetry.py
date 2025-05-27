#!/usr/bin/env python3
"""
Capture and display RAW telemetry output with full details.
This script runs a test and captures ALL telemetry data.
"""

import asyncio
import os
import json
import sys
from datetime import datetime
from dotenv import load_dotenv
from azure.identity.aio import DefaultAzureCredential
from semantic_kernel.agents import AzureAIAgent, AzureAIAgentSettings
import logging

# Configure logging to capture ALL telemetry
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(name)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f'raw_telemetry_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.telemetry import initialize_telemetry

# Load environment
current_dir = os.path.dirname(os.path.abspath(__file__))
agentic_dir = os.path.dirname(current_dir)
env_path = os.path.join(agentic_dir, '.env')
load_dotenv(env_path)

# Initialize telemetry
tracer = initialize_telemetry(
    service_name="RawTelemetryCapture",
    service_version="1.0.0",
    connection_string=os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
)

# Enable Azure SDK logging
logging.getLogger('azure').setLevel(logging.DEBUG)
logging.getLogger('azure.monitor').setLevel(logging.DEBUG)
logging.getLogger('opentelemetry').setLevel(logging.DEBUG)
logging.getLogger('semantic_kernel').setLevel(logging.DEBUG)

async def capture_orchestration_telemetry():
    """Run a single orchestration test and capture all telemetry."""
    
    # Load orchestrator config
    orch_config_path = os.path.join(agentic_dir, "deployment_configs", "main_orchestrator_tools_deployment.json")
    with open(orch_config_path, 'r') as f:
        config = json.load(f)
        orchestrator_id = config['agent_id']
    
    print("\n" + "="*80)
    print("RAW TELEMETRY CAPTURE - FULL ORCHESTRATION FLOW")
    print("="*80)
    print(f"Orchestrator: {orchestrator_id}")
    print(f"Service: RawTelemetryCapture")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("="*80 + "\n")
    
    settings = AzureAIAgentSettings()
    credential = DefaultAzureCredential()
    
    async with AzureAIAgent.create_client(credential=credential, settings=settings) as client:
        # Single test case
        test_message = "I need to record an important strategic decision about our AI product roadmap"
        
        with tracer.start_as_current_span("orchestration_test") as span:
            span.set_attribute("test.message", test_message)
            
            print(f"[TEST] Message: {test_message}")
            print("\n--- BEGIN RAW TELEMETRY ---\n")
            
            try:
                # Create thread
                thread = await client.agents.threads.create()
                thread_id = thread.id
                span.set_attribute("orchestrator.thread_id", thread_id)
                print(f"[TELEMETRY] Orchestrator thread created: {thread_id}")
                
                # Send message
                await client.agents.messages.create(
                    thread_id=thread_id,
                    role="user",
                    content=test_message
                )
                span.add_event("message_sent", {"content": test_message})
                print(f"[TELEMETRY] Message sent to thread")
                
                # Run orchestrator
                run = await client.agents.runs.create(
                    thread_id=thread_id,
                    agent_id=orchestrator_id
                )
                span.set_attribute("orchestrator.run_id", run.id)
                print(f"[TELEMETRY] Orchestrator run created: {run.id}")
                
                # Wait for response
                max_wait = 20
                for i in range(max_wait):
                    await asyncio.sleep(1)
                    
                    run = await client.agents.runs.get(
                        thread_id=thread_id,
                        run_id=run.id
                    )
                    
                    print(f"[TELEMETRY] Run status check {i+1}: {run.status}")
                    span.add_event(f"status_check_{i+1}", {"status": str(run.status)})
                    
                    if run.status == "requires_action":
                        print(f"[TELEMETRY] Orchestrator requires action - tool call detected")
                        
                        # Get tool calls
                        tool_calls = run.required_action.submit_tool_outputs.tool_calls
                        
                        for tool_call in tool_calls:
                            function_name = tool_call.function.name
                            args = json.loads(tool_call.function.arguments)
                            
                            span.add_event("tool_call_requested", {
                                "function": function_name,
                                "arguments": json.dumps(args),
                                "tool_call_id": tool_call.id
                            })
                            
                            print(f"\n[TELEMETRY] Tool call details:")
                            print(f"  Function: {function_name}")
                            print(f"  Tool Call ID: {tool_call.id}")
                            print(f"  Arguments: {json.dumps(args, indent=2)}")
                            
                            # Find specialist agent
                            agent_key = function_name.replace("invoke_", "")
                            
                            deployment_path = os.path.join(agentic_dir, "deployment_configs", "ai_project_agents_deployment.json")
                            with open(deployment_path, 'r') as f:
                                deployment_data = json.load(f)
                                specialist_agents = deployment_data['deployed_agents']
                            
                            specialist_id = None
                            specialist_name = None
                            for agent_name, agent_id in specialist_agents.items():
                                if agent_name.lower() == agent_key:
                                    specialist_id = agent_id
                                    specialist_name = agent_name
                                    break
                            
                            if specialist_id:
                                with tracer.start_as_current_span(f"invoke_{specialist_name}") as spec_span:
                                    spec_span.set_attribute("specialist.name", specialist_name)
                                    spec_span.set_attribute("specialist.id", specialist_id)
                                    
                                    print(f"\n[TELEMETRY] Invoking specialist: {specialist_name}")
                                    print(f"  Specialist ID: {specialist_id}")
                                    
                                    # Create specialist thread
                                    specialist_thread = await client.agents.threads.create()
                                    spec_span.set_attribute("specialist.thread_id", specialist_thread.id)
                                    print(f"[TELEMETRY] Specialist thread: {specialist_thread.id}")
                                    
                                    # Send to specialist
                                    await client.agents.messages.create(
                                        thread_id=specialist_thread.id,
                                        role="user",
                                        content=args.get('request', test_message)
                                    )
                                    
                                    # Run specialist
                                    specialist_run = await client.agents.runs.create(
                                        thread_id=specialist_thread.id,
                                        agent_id=specialist_id
                                    )
                                    spec_span.set_attribute("specialist.run_id", specialist_run.id)
                                    print(f"[TELEMETRY] Specialist run: {specialist_run.id}")
                                    
                                    # Wait for specialist
                                    for j in range(10):
                                        await asyncio.sleep(1)
                                        
                                        specialist_run = await client.agents.runs.get(
                                            thread_id=specialist_thread.id,
                                            run_id=specialist_run.id
                                        )
                                        
                                        print(f"[TELEMETRY] Specialist status {j+1}: {specialist_run.status}")
                                        
                                        if specialist_run.status == "completed":
                                            # Get response
                                            messages = client.agents.messages.list(thread_id=specialist_thread.id)
                                            
                                            async for msg in messages:
                                                if msg.role == "assistant" and msg.content:
                                                    for content in msg.content:
                                                        if hasattr(content, 'text'):
                                                            response = content.text.value
                                                            spec_span.set_attribute("specialist.response_length", len(response))
                                                            spec_span.add_event("specialist_responded", {
                                                                "response_preview": response[:100]
                                                            })
                                                            
                                                            print(f"\n[TELEMETRY] Specialist response:")
                                                            print(f"  Length: {len(response)} chars")
                                                            print(f"  Preview: {response[:150]}...")
                                                            
                                                            # Submit back
                                                            await client.agents.runs.submit_tool_outputs(
                                                                thread_id=thread_id,
                                                                run_id=run.id,
                                                                tool_outputs=[{
                                                                    "tool_call_id": tool_call.id,
                                                                    "output": response
                                                                }]
                                                            )
                                                            print(f"\n[TELEMETRY] Tool output submitted to orchestrator")
                                                            break
                                                    if response:
                                                        break
                                            
                                            # Clean up
                                            await client.agents.threads.delete(thread_id=specialist_thread.id)
                                            break
                        break
                    
                    elif run.status == "completed":
                        print(f"\n[TELEMETRY] Orchestrator completed")
                        
                        # Get final response
                        messages = client.agents.messages.list(thread_id=thread_id)
                        
                        async for msg in messages:
                            if msg.role == "assistant" and msg.content:
                                for content in msg.content:
                                    if hasattr(content, 'text'):
                                        final = content.text.value
                                        span.set_attribute("orchestrator.final_response_length", len(final))
                                        print(f"\n[TELEMETRY] Final orchestrator response:")
                                        print(f"  Length: {len(final)} chars")
                                        print(f"  Content: {final}")
                                        break
                                if final:
                                    break
                        break
                
                # Clean up
                await client.agents.threads.delete(thread_id=thread_id)
                print(f"\n[TELEMETRY] Orchestrator thread cleaned up")
                
            except Exception as e:
                span.record_exception(e)
                print(f"\n[ERROR] {str(e)}")
                import traceback
                traceback.print_exc()
    
    await credential.close()
    
    print("\n--- END RAW TELEMETRY ---\n")
    print("Check the log file for complete telemetry output")

if __name__ == "__main__":
    asyncio.run(capture_orchestration_telemetry())