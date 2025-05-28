#!/usr/bin/env python3
"""
Capture detailed telemetry including delegations and tool calls
"""
import os
import sys
import json
import asyncio
import logging
from datetime import datetime
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode
from azure.ai.projects.aio import AIProjectClient
from azure.identity.aio import DefaultAzureCredential

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.telemetry import initialize_telemetry

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('detailed_telemetry.log'),
        logging.StreamHandler()
    ]
)

# Enable debug logging for OpenTelemetry
logging.getLogger("opentelemetry").setLevel(logging.DEBUG)
logging.getLogger("azure.core.pipeline").setLevel(logging.DEBUG)

async def test_with_detailed_telemetry():
    """Run connected agents test with detailed telemetry capture"""
    
    # Initialize telemetry with debug enabled
    tracer = initialize_telemetry(
        service_name="connected-agents-detailed-test",
        service_version="1.0.0"
    )
    
    # Create main span
    with tracer.start_as_current_span("detailed_test_run") as main_span:
        main_span.set_attribute("test.type", "connected_agents")
        main_span.set_attribute("test.timestamp", datetime.now().isoformat())
        
        try:
            # Initialize client
            project_client = AIProjectClient(
                credential=DefaultAzureCredential(exclude_interactive_browser_credential=False),
                subscription_id="d23c77f9-e54f-4dc4-b8a4-c77577bf3e73",
                resource_group_name="stratos-rg",
                project_name="stratos-ai-project"
            )
            
            orchestrator_id = "asst_39dQPqlyJhVT3CAeTBOLTu59"
            
            # Test cases with detailed spans
            test_cases = [
                ("What's the weather in Seattle?", "weather_test"),
                ("Calculate 123 + 456", "calculator_test"),
                ("Give me a greeting", "greeting_test")
            ]
            
            results = []
            
            for question, test_name in test_cases:
                # Create span for each test
                with tracer.start_as_current_span(test_name) as test_span:
                    test_span.set_attribute("test.question", question)
                    test_span.set_attribute("agent.type", "orchestrator")
                    test_span.set_attribute("agent.id", orchestrator_id)
                    
                    print(f"\n{'='*60}")
                    print(f"Testing: {question}")
                    print(f"Span ID: {test_span.get_span_context().span_id:016x}")
                    print(f"Trace ID: {test_span.get_span_context().trace_id:032x}")
                    
                    try:
                        # Create thread span
                        with tracer.start_as_current_span("create_thread") as thread_span:
                            thread = await project_client.agents.create_thread()
                            thread_span.set_attribute("thread.id", thread.id)
                            print(f"Thread created: {thread.id}")
                        
                        # Create message span
                        with tracer.start_as_current_span("create_message") as msg_span:
                            msg_span.set_attribute("message.content", question)
                            message = await project_client.agents.create_message(
                                thread_id=thread.id,
                                role="user",
                                content=question
                            )
                            msg_span.set_attribute("message.id", message.id)
                        
                        # Create run span
                        with tracer.start_as_current_span("create_and_wait_run") as run_span:
                            run_span.set_attribute("run.assistant_id", orchestrator_id)
                            
                            # Create run
                            run = await project_client.agents.create_and_process_run(
                                thread_id=thread.id,
                                assistant_id=orchestrator_id
                            )
                            
                            run_span.set_attribute("run.id", run.id)
                            run_span.set_attribute("run.status", run.status)
                            
                            if run.status == "failed":
                                run_span.set_status(Status(StatusCode.ERROR, run.last_error.message))
                            else:
                                run_span.set_status(Status(StatusCode.OK))
                        
                        # Get messages span
                        with tracer.start_as_current_span("get_messages") as msg_list_span:
                            messages = await project_client.agents.list_messages(thread_id=thread.id)
                            message_list = []
                            async for msg in messages:
                                if msg.role == "assistant":
                                    content = msg.content[0].text.value if msg.content else ""
                                    message_list.append(content)
                                    
                                    # Check for delegation patterns
                                    if "specialist" in content or "expert" in content:
                                        msg_list_span.add_event(
                                            "delegation_detected",
                                            {"content": content[:100]}
                                        )
                            
                            response = "\n".join(message_list)
                            msg_list_span.set_attribute("response.length", len(response))
                            msg_list_span.set_attribute("response.preview", response[:200])
                        
                        result = {
                            "question": question,
                            "response": response,
                            "thread_id": thread.id,
                            "run_id": run.id,
                            "run_status": run.status,
                            "span_id": f"{test_span.get_span_context().span_id:016x}",
                            "trace_id": f"{test_span.get_span_context().trace_id:032x}"
                        }
                        
                        results.append(result)
                        
                        print(f"Response: {response[:200]}...")
                        print(f"Run Status: {run.status}")
                        
                        test_span.set_status(Status(StatusCode.OK))
                        
                    except Exception as e:
                        test_span.record_exception(e)
                        test_span.set_status(Status(StatusCode.ERROR, str(e)))
                        print(f"Error: {e}")
                        results.append({
                            "question": question,
                            "error": str(e),
                            "span_id": f"{test_span.get_span_context().span_id:016x}",
                            "trace_id": f"{test_span.get_span_context().trace_id:032x}"
                        })
            
            # Save results
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"detailed_telemetry_results_{timestamp}.json"
            
            with open(filename, 'w') as f:
                json.dump({
                    "test_id": f"detailed_{timestamp}",
                    "main_trace_id": f"{main_span.get_span_context().trace_id:032x}",
                    "results": results
                }, f, indent=2)
            
            print(f"\n✅ Results saved to: {filename}")
            print(f"Main Trace ID: {main_span.get_span_context().trace_id:032x}")
            
            main_span.set_status(Status(StatusCode.OK))
            
        except Exception as e:
            main_span.record_exception(e)
            main_span.set_status(Status(StatusCode.ERROR, str(e)))
            raise

if __name__ == "__main__":
    asyncio.run(test_with_detailed_telemetry())