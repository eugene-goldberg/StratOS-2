#!/usr/bin/env python3
"""Simple test for the deployed orchestrator without complex endpoint resolution."""

import os
import logging
import json
from azure.ai.projects import AIProjectClient
from azure.ai.agents.models import RunStatus
from azure.identity import DefaultAzureCredential
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [%(funcName)s] %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Test the deployed orchestrator."""
    # Load deployment info
    with open('deployment_info.json', 'r') as f:
        deployment_info = json.load(f)
    
    orchestrator_id = deployment_info['orchestrator_agent_id']
    endpoint = deployment_info['endpoint']
    
    logger.info("=" * 60)
    logger.info("TESTING DEPLOYED ORCHESTRATOR (SIMPLE)")
    logger.info("=" * 60)
    logger.info(f"Orchestrator ID: {orchestrator_id}")
    logger.info(f"Endpoint: {endpoint}")
    
    # Set up environment variables
    os.environ['AZURE_CLIENT_ID'] = '0d41080b-9595-4f4a-b6ad-9ef01b3f5ecf'
    os.environ['AZURE_CLIENT_SECRET'] = 'MSg8Q~fSqZvntpsWvETH4ZZb2uUdDfxnuu7~Jbu7'
    os.environ['AZURE_TENANT_ID'] = '5acd02e3-dfea-4b7c-aab5-1633ffe0403a'
    
    # Create client
    credential = DefaultAzureCredential()
    client = AIProjectClient(endpoint=endpoint, credential=credential)
    
    # Test queries
    test_queries = [
        {"query": "Hello", "expected": "General greeting - should go to greeter agent"},
        {"query": "What's the weather in Seattle?", "expected": "Weather query - should go to weather agent"},
    ]
    
    try:
        # Create thread
        thread = client.agents.threads.create()
        logger.info(f"Created thread: {thread.id}")
        
        for i, test_query in enumerate(test_queries, 1):
            logger.info(f"\n{'='*40}")
            logger.info(f"Test {i}: {test_query['query']}")
            logger.info(f"Expected: {test_query['expected']}")
            logger.info("-" * 40)
            
            # Add message
            message = client.agents.messages.create(
                thread_id=thread.id,
                role="user",
                content=test_query["query"]
            )
            
            # Create run
            run = client.agents.runs.create(
                thread_id=thread.id,
                body={"assistant_id": orchestrator_id}
            )
            
            # Wait for completion
            while run.status in [RunStatus.QUEUED, RunStatus.IN_PROGRESS, RunStatus.REQUIRES_ACTION]:
                # Handle tool calls if needed
                if run.status == RunStatus.REQUIRES_ACTION:
                    logger.info("🔧 Processing tool calls...")
                    tool_outputs = []
                    
                    if run.required_action and run.required_action.submit_tool_outputs:
                        for tool_call in run.required_action.submit_tool_outputs.tool_calls:
                            logger.info(f"   Tool: {tool_call.function.name}")
                            logger.info(f"   Args: {tool_call.function.arguments}")
                            # Let the connected agent handle it
                            tool_outputs.append({
                                "tool_call_id": tool_call.id,
                                "output": "Connected agent invoked"
                            })
                    
                    # Submit outputs
                    run = client.agents.runs.submit_tool_outputs(
                        thread_id=thread.id,
                        run_id=run.id,
                        body={"tool_outputs": tool_outputs}
                    )
                
                time.sleep(1)
                run = client.agents.runs.get(thread_id=thread.id, run_id=run.id)
            
            if run.status == RunStatus.COMPLETED:
                # Get messages
                messages = client.agents.messages.list(thread_id=thread.id)
                
                # Find the assistant's response
                for msg in messages:
                    if msg.role == "assistant":
                        content = msg.content[0].text.value if msg.content else "No content"
                        logger.info(f"Response: {content}")
                        break
            else:
                logger.error(f"Run failed with status: {run.status}")
                
    except Exception as e:
        logger.error(f"Error during test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()