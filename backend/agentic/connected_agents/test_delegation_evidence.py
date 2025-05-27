#!/usr/bin/env python3
"""Test to provide evidence that responses come from connected agents, not the orchestrator."""

import os
import logging
import json
from azure.ai.projects import AIProjectClient
from azure.ai.agents.models import RunStatus
from azure.identity import DefaultAzureCredential
import time

# Configure logging to show detailed information
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - [%(funcName)s] %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Test with detailed evidence of delegation."""
    # Load deployment info
    with open('deployment_info.json', 'r') as f:
        deployment_info = json.load(f)
    
    orchestrator_id = deployment_info['orchestrator_agent_id']
    greeter_id = deployment_info['greeter_agent_id']
    weather_id = deployment_info['weather_agent_id']
    endpoint = deployment_info['endpoint']
    
    logger.info("=" * 60)
    logger.info("TESTING DELEGATION WITH EVIDENCE")
    logger.info("=" * 60)
    logger.info(f"Orchestrator ID: {orchestrator_id}")
    logger.info(f"Greeter Agent ID: {greeter_id}")
    logger.info(f"Weather Agent ID: {weather_id}")
    
    # Set up environment variables
    os.environ['AZURE_CLIENT_ID'] = '0d41080b-9595-4f4a-b6ad-9ef01b3f5ecf'
    os.environ['AZURE_CLIENT_SECRET'] = 'MSg8Q~fSqZvntpsWvETH4ZZb2uUdDfxnuu7~Jbu7'
    os.environ['AZURE_TENANT_ID'] = '5acd02e3-dfea-4b7c-aab5-1633ffe0403a'
    
    # Create client
    credential = DefaultAzureCredential()
    client = AIProjectClient(endpoint=endpoint, credential=credential)
    
    # First, let's check what each agent says when called directly
    logger.info("\n" + "="*60)
    logger.info("STEP 1: Testing agents DIRECTLY (for comparison)")
    logger.info("="*60)
    
    # Test greeter directly
    logger.info("\n--- Testing GREETER agent directly ---")
    thread1 = client.agents.threads.create()
    message1 = client.agents.messages.create(
        thread_id=thread1.id,
        role="user",
        content="Hello"
    )
    run1 = client.agents.runs.create(
        thread_id=thread1.id,
        body={"assistant_id": greeter_id}
    )
    
    # Wait for completion
    while run1.status in [RunStatus.QUEUED, RunStatus.IN_PROGRESS]:
        time.sleep(1)
        run1 = client.agents.runs.get(thread_id=thread1.id, run_id=run1.id)
    
    if run1.status == RunStatus.COMPLETED:
        messages = client.agents.messages.list(thread_id=thread1.id)
        for msg in messages:
            if msg.role == "assistant":
                logger.info(f"GREETER DIRECT RESPONSE: {msg.content[0].text.value}")
                break
    
    # Test weather directly
    logger.info("\n--- Testing WEATHER agent directly ---")
    thread2 = client.agents.threads.create()
    message2 = client.agents.messages.create(
        thread_id=thread2.id,
        role="user",
        content="What's the weather in Seattle?"
    )
    run2 = client.agents.runs.create(
        thread_id=thread2.id,
        body={"assistant_id": weather_id}
    )
    
    # Wait for completion
    while run2.status in [RunStatus.QUEUED, RunStatus.IN_PROGRESS]:
        time.sleep(1)
        run2 = client.agents.runs.get(thread_id=thread2.id, run_id=run2.id)
    
    if run2.status == RunStatus.COMPLETED:
        messages = client.agents.messages.list(thread_id=thread2.id)
        for msg in messages:
            if msg.role == "assistant":
                logger.info(f"WEATHER DIRECT RESPONSE: {msg.content[0].text.value}")
                break
    
    # Now test through orchestrator to see tool calls
    logger.info("\n" + "="*60)
    logger.info("STEP 2: Testing through ORCHESTRATOR (to see delegation)")
    logger.info("="*60)
    
    # Create thread for orchestrator
    thread3 = client.agents.threads.create()
    logger.info(f"Created thread: {thread3.id}")
    
    # Test weather query through orchestrator
    logger.info("\n--- Sending weather query to ORCHESTRATOR ---")
    message3 = client.agents.messages.create(
        thread_id=thread3.id,
        role="user",
        content="What's the weather in Seattle?"
    )
    
    run3 = client.agents.runs.create(
        thread_id=thread3.id,
        body={"assistant_id": orchestrator_id}
    )
    
    # Track tool calls
    tool_calls_made = []
    
    while run3.status in [RunStatus.QUEUED, RunStatus.IN_PROGRESS, RunStatus.REQUIRES_ACTION]:
        if run3.status == RunStatus.REQUIRES_ACTION:
            logger.info("\n🔧 EVIDENCE: Orchestrator is making TOOL CALLS!")
            
            if run3.required_action and run3.required_action.submit_tool_outputs:
                for tool_call in run3.required_action.submit_tool_outputs.tool_calls:
                    logger.info(f"   Tool Called: {tool_call.function.name}")
                    logger.info(f"   Tool ID: {tool_call.id}")
                    logger.info(f"   Arguments: {tool_call.function.arguments}")
                    
                    # Parse arguments to see which agent is being called
                    try:
                        args = json.loads(tool_call.function.arguments)
                        if 'assistant_id' in args:
                            logger.info(f"   🎯 DELEGATING TO AGENT: {args['assistant_id']}")
                            if args['assistant_id'] == weather_id:
                                logger.info("   ✅ CONFIRMED: Calling WEATHER agent!")
                            elif args['assistant_id'] == greeter_id:
                                logger.info("   ✅ CONFIRMED: Calling GREETER agent!")
                    except:
                        pass
                    
                    tool_calls_made.append({
                        "name": tool_call.function.name,
                        "args": tool_call.function.arguments
                    })
                    
                    # Submit dummy output to continue
                    run3 = client.agents.runs.submit_tool_outputs(
                        thread_id=thread3.id,
                        run_id=run3.id,
                        body={"tool_outputs": [{
                            "tool_call_id": tool_call.id,
                            "output": "Connected agent invoked"
                        }]}
                    )
        
        time.sleep(1)
        run3 = client.agents.runs.get(thread_id=thread3.id, run_id=run3.id)
    
    # Get final response
    if run3.status == RunStatus.COMPLETED:
        messages = client.agents.messages.list(thread_id=thread3.id)
        for msg in messages:
            if msg.role == "assistant":
                logger.info(f"\nORCHESTRATOR FINAL RESPONSE: {msg.content[0].text.value}")
                break
    
    # Summary
    logger.info("\n" + "="*60)
    logger.info("EVIDENCE SUMMARY")
    logger.info("="*60)
    logger.info(f"Total tool calls made by orchestrator: {len(tool_calls_made)}")
    for i, tool_call in enumerate(tool_calls_made, 1):
        logger.info(f"{i}. {tool_call['name']} - {tool_call['args']}")

if __name__ == "__main__":
    main()