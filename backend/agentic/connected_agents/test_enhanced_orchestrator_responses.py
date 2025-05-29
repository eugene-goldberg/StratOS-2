"""Test enhanced orchestrator to verify it shows actual agent responses"""

import os
import asyncio
from azure.ai.projects.aio import AIProjectClient
from azure.ai.projects.models import Agent
from azure.identity.aio import DefaultAzureCredential
from azure.core.tracing.decorator import distributed_trace
from azure.ai.projects.models import AgentEventHandler, MessageDeltaChunk, ThreadMessage, ToolCallDeltaChunk, RunStep
from typing import Any, Union
from datetime import datetime
import json

# Application Insights configuration
from azure.monitor.opentelemetry import configure_azure_monitor
from opentelemetry import trace

configure_azure_monitor(
    connection_string="InstrumentationKey=c37055e8-1c8c-410d-ab37-e49f009a0d36;IngestionEndpoint=https://eastus-8.in.applicationinsights.azure.com/;LiveEndpoint=https://eastus.livediagnostics.monitor.azure.com/;ApplicationId=3f9d10f1-3df5-4c80-ab03-41e0b8a02e31"
)

tracer = trace.get_tracer(__name__)

# Environment configuration
subscription_id = "fce3ed09-9636-4ead-b7f0-53581559f0ee"
resource_group_name = "rg-multi-agent"
ai_project_name = "ai-project-multi-agent"
ai_foundry_endpoint = "https://aistudiousecentral123.api.azureml.ms"

class EnhancedResponseHandler(AgentEventHandler):
    """Handler to capture complete responses including tool results"""
    
    def __init__(self):
        self.response = ""
        self.tool_calls = []
        self.tool_results = {}
        self.delegation_detected = False
        self.specialist_response = ""
        
    async def on_message_delta(self, delta: MessageDeltaChunk) -> None:
        if delta.content:
            self.response += delta.content
            # Check for delegation pattern
            if "I'll connect you with" in delta.content:
                self.delegation_detected = True
                
    async def on_tool_call_delta(self, delta: ToolCallDeltaChunk) -> None:
        """Capture tool calls"""
        self.tool_calls.append({
            "tool_id": delta.id,
            "type": delta.type,
            "function": delta.function if hasattr(delta, 'function') else None
        })
        
    async def on_run_step(self, step: RunStep) -> None:
        """Capture tool results from run steps"""
        if hasattr(step, 'step_details') and hasattr(step.step_details, 'tool_calls'):
            for tool_call in step.step_details.tool_calls:
                if hasattr(tool_call, 'output'):
                    self.tool_results[tool_call.id] = tool_call.output
                    self.specialist_response = tool_call.output
                    
    async def on_thread_message(self, message: ThreadMessage) -> None:
        """Capture complete thread messages"""
        if message.content:
            for content in message.content:
                if hasattr(content, 'text') and hasattr(content.text, 'value'):
                    # Check if this is a specialist response
                    if "specialist's response:" in content.text.value:
                        self.specialist_response = content.text.value

async def test_enhanced_orchestrator():
    """Test the enhanced orchestrator with various queries"""
    
    credential = DefaultAzureCredential()
    
    # Create AI Project client
    project_client = AIProjectClient(
        subscription_id=subscription_id,
        resource_group_name=resource_group_name,
        ai_foundry_project_name=ai_project_name,
        endpoint=ai_foundry_endpoint,
        credential=credential
    )
    
    # Get the enhanced orchestrator
    orchestrator_id = "asst_DvAoA85m6eCsWdOT2bsTxE6i"
    orchestrator_agent = project_client.agents.get_agent(orchestrator_id)
    
    # Test queries
    test_queries = [
        {
            "name": "CEO Log Test",
            "query": "Log our Q4 board meeting: Revenue exceeded targets by 15%, approved new R&D budget"
        },
        {
            "name": "North Star Test", 
            "query": "What are our current strategic goals?"
        },
        {
            "name": "Memory Recall Test",
            "query": "What decisions were made in the last board meeting?"
        },
        {
            "name": "Preference Learning Test",
            "query": "How does our CEO prefer to receive updates?"
        }
    ]
    
    results = []
    
    print("Testing Enhanced Orchestrator Response Handling\n" + "="*50)
    
    for test in test_queries:
        print(f"\n📝 Test: {test['name']}")
        print(f"Query: {test['query']}")
        
        with tracer.start_as_current_span(f"test_{test['name']}") as span:
            span.set_attribute("test.name", test['name'])
            span.set_attribute("query", test['query'])
            
            # Create thread and send message
            thread = await project_client.agents.create_thread()
            await project_client.agents.create_message(
                thread_id=thread.id,
                role="user",
                content=test['query']
            )
            
            # Process with enhanced handler
            handler = EnhancedResponseHandler()
            
            try:
                # Create and process run
                run = await project_client.agents.create_run(
                    thread_id=thread.id,
                    assistant_id=orchestrator_agent.id,
                    event_handler=handler
                )
                
                # Wait for completion
                while run.status in ["queued", "in_progress", "requires_action"]:
                    await asyncio.sleep(0.5)
                    run = await project_client.agents.get_run(
                        thread_id=thread.id,
                        run_id=run.id
                    )
                
                # Get complete thread messages
                messages = await project_client.agents.list_messages(thread_id=thread.id)
                
                # Extract full response
                full_response = ""
                for msg in messages:
                    if msg.role == "assistant":
                        for content in msg.content:
                            if hasattr(content, 'text') and hasattr(content.text, 'value'):
                                full_response = content.text.value
                                break
                        break
                
                # Analyze response
                result = {
                    "test_name": test['name'],
                    "query": test['query'],
                    "delegation_detected": handler.delegation_detected,
                    "tool_calls_made": len(handler.tool_calls) > 0,
                    "has_specialist_response": bool(handler.specialist_response),
                    "response_includes_tool_result": "response:" in full_response.lower(),
                    "full_response": full_response,
                    "response_length": len(full_response)
                }
                
                results.append(result)
                
                print(f"\nResponse Analysis:")
                print(f"  ✓ Delegation detected: {result['delegation_detected']}")
                print(f"  ✓ Tool calls made: {result['tool_calls_made']}")
                print(f"  ✓ Has specialist response: {result['has_specialist_response']}")
                print(f"  ✓ Response includes result: {result['response_includes_tool_result']}")
                print(f"  ✓ Response length: {result['response_length']} chars")
                
                print(f"\nFull Response:")
                print("-" * 40)
                print(full_response[:500] + "..." if len(full_response) > 500 else full_response)
                print("-" * 40)
                
                span.set_attribute("response.has_tool_result", result['response_includes_tool_result'])
                span.set_attribute("response.length", result['response_length'])
                
            except Exception as e:
                print(f"❌ Error: {str(e)}")
                span.record_exception(e)
                result = {
                    "test_name": test['name'],
                    "error": str(e)
                }
                results.append(result)
    
    # Summary report
    print("\n\n📊 SUMMARY REPORT")
    print("="*50)
    
    successful_responses = [r for r in results if 'error' not in r]
    responses_with_results = [r for r in successful_responses if r.get('response_includes_tool_result', False)]
    
    print(f"Total tests: {len(test_queries)}")
    print(f"Successful: {len(successful_responses)}")
    print(f"With tool results: {len(responses_with_results)}")
    print(f"Success rate: {len(responses_with_results)/len(test_queries)*100:.1f}%")
    
    # Save detailed results
    report = {
        "test_time": datetime.now().isoformat(),
        "orchestrator_id": orchestrator_id,
        "enhanced_response_handling": True,
        "summary": {
            "total_tests": len(test_queries),
            "successful": len(successful_responses),
            "with_tool_results": len(responses_with_results),
            "success_rate": f"{len(responses_with_results)/len(test_queries)*100:.1f}%"
        },
        "detailed_results": results
    }
    
    with open(f"enhanced_orchestrator_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"\nDetailed report saved to: enhanced_orchestrator_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    
    await credential.close()
    await project_client.close()

if __name__ == "__main__":
    asyncio.run(test_enhanced_orchestrator())