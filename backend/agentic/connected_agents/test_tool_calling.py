#!/usr/bin/env python3
"""Test tool calling behavior specifically."""

import logging
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
import os
import json
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [%(funcName)s] %(message)s')
logger = logging.getLogger(__name__)

# Environment variables
connection_string = os.getenv("AZURE_AI_PROJECT_CONNECTION_STRING")

def main():
    """Test tool calling behavior."""
    # Load deployment info
    with open("deployment_info.json", "r") as f:
        deployment_info = json.load(f)
    
    orchestrator_id = deployment_info["orchestrator_agent_id"]
    
    credential = DefaultAzureCredential()
    client = AIProjectClient(endpoint=connection_string, credential=credential)
    
    # Create a thread
    thread = client.agents.threads.create()
    logger.info(f"Created thread: {thread.id}")
    
    # Test with explicit tool request
    test_message = "Please use the enthusiastic_greeter_tool to give me a greeting"
    
    logger.info(f"\nTesting with: '{test_message}'")
    logger.info("=" * 60)
    
    # Add message
    message = client.agents.messages.create(
        thread_id=thread.id,
        role="user",
        content=test_message
    )
    
    # Create run
    run = client.agents.runs.create(
        thread_id=thread.id,
        body={"assistant_id": orchestrator_id}
    )
    
    # Wait for completion
    max_iterations = 30
    iterations = 0
    
    while run.status in ["queued", "in_progress", "requires_action"] and iterations < max_iterations:
        iterations += 1
        logger.info(f"Iteration {iterations}: Run status: {run.status}")
        
        # Handle tool calls if needed
        if run.status == "requires_action":
            logger.info("🔧 Run requires action - tool calls detected!")
            
            if run.required_action and run.required_action.submit_tool_outputs:
                logger.info(f"Number of tool calls: {len(run.required_action.submit_tool_outputs.tool_calls)}")
                
                for tool_call in run.required_action.submit_tool_outputs.tool_calls:
                    logger.info(f"\nTool Call Details:")
                    logger.info(f"  ID: {tool_call.id}")
                    logger.info(f"  Type: {tool_call.type}")
                    
                    if hasattr(tool_call, 'function'):
                        logger.info(f"  Function Name: {tool_call.function.name}")
                        logger.info(f"  Function Args: {tool_call.function.arguments}")
                    
                    # For connected agents, the tool call is handled automatically
                    logger.info("  ✅ Connected agent tool call - will be handled by Azure")
            
            # Azure should handle connected agent calls automatically
            # We just need to wait for the status to change
            time.sleep(2)
        else:
            time.sleep(1)
        
        # Get updated run status
        run = client.agents.runs.get(thread_id=thread.id, run_id=run.id)
    
    logger.info(f"\nFinal run status: {run.status}")
    
    # Get messages
    messages = client.agents.messages.list(thread_id=thread.id)
    
    # Show all messages
    logger.info("\nConversation History:")
    logger.info("=" * 60)
    
    for msg in reversed(list(messages)):
        logger.info(f"\nRole: {msg.role}")
        if msg.content:
            for content_item in msg.content:
                if hasattr(content_item, 'text'):
                    logger.info(f"Content: {content_item.text.value}")
    
    # Analysis
    logger.info("\n" + "=" * 60)
    logger.info("ANALYSIS:")
    
    if iterations >= max_iterations:
        logger.warning("❌ Run timed out - possible issue with tool calling")
    elif run.status == "completed":
        # Check if tool was actually called
        messages_list = list(messages)
        assistant_messages = [m for m in messages_list if m.role == "assistant"]
        
        if assistant_messages:
            latest_response = assistant_messages[0].content[0].text.value if assistant_messages[0].content else ""
            
            # Check for signs of actual tool usage vs mimicking
            if "HELLO THERE!!!" in latest_response and "🎉" in latest_response:
                if "using the enthusiastic_greeter_tool" in latest_response.lower():
                    logger.info("✅ Tool was mentioned in response")
                else:
                    logger.warning("⚠️  Response looks like tool output but tool usage not mentioned")
            else:
                logger.warning("❌ Response doesn't match expected tool output")
    else:
        logger.warning(f"❌ Unexpected final status: {run.status}")

if __name__ == "__main__":
    main()