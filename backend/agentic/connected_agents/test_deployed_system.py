#!/usr/bin/env python3
"""Test the deployed multi-agent system."""

import logging
from azure.ai.projects import AIProjectClient
from azure.ai.agents.models import RunStatus
from azure.identity import DefaultAzureCredential
import os
import json
from datetime import datetime
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [%(funcName)s] %(message)s')
logger = logging.getLogger(__name__)

# Environment variables
endpoint = os.getenv("AI_PROJECT_ENDPOINT")
connection_string = os.getenv("AI_PROJECT_CONNECTION_STRING") or os.getenv("AZURE_AI_PROJECT_CONNECTION_STRING")
deployment_id = os.getenv("AZURE_OPENAI_DEPLOYMENT_ID") or os.getenv("AZURE_AI_MODEL_DEPLOYMENT_NAME") or "gpt-35-turbo"

if not (endpoint or connection_string):
    raise ValueError("Please set AI_PROJECT_ENDPOINT or AI_PROJECT_CONNECTION_STRING or AZURE_AI_PROJECT_CONNECTION_STRING environment variable")

def test_orchestrator(orchestrator_id, test_queries):
    """Test the orchestrator with various queries."""
    credential = DefaultAzureCredential()
    # Use connection string if available, otherwise use endpoint
    if connection_string:
        client = AIProjectClient(endpoint=connection_string, credential=credential)
    else:
        client = AIProjectClient(endpoint=endpoint, credential=credential)
    
    logger.info("=" * 60)
    logger.info("TESTING DEPLOYED ORCHESTRATOR")
    logger.info("=" * 60)
    
    # Create a thread
    thread = client.agents.threads.create()
    logger.info(f"Created thread: {thread.id}")
    
    for i, query in enumerate(test_queries, 1):
        logger.info(f"\nTest {i}: {query['query']}")
        logger.info(f"Expected: {query['expected']}")
        logger.info("-" * 40)
        
        # Add message
        message = client.agents.messages.create(
            thread_id=thread.id,
            role="user",
            content=query["query"]
        )
        
        # Create and process run
        run = client.agents.runs.create(
            thread_id=thread.id,
            body={"assistant_id": orchestrator_id}
        )
        
        # Wait for completion
        while run.status in ["queued", "in_progress", "requires_action"]:
            # Handle tool calls if needed
            if run.status == "requires_action":
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
            
            # Wait a bit
            time.sleep(1)
            run = client.agents.runs.get(thread_id=thread.id, run_id=run.id)
        
        logger.info(f"Run status: {run.status}")
        
        # Get messages
        messages = client.agents.messages.list(thread_id=thread.id)
        
        # Find the assistant's response
        assistant_messages = [m for m in messages if m.role == "assistant"]
        if assistant_messages:
            latest_response = assistant_messages[0]
            content = latest_response.content[0].text.value if latest_response.content else "No content"
            logger.info(f"Response: {content}")
            
            # Check if delegation occurred
            if query["expected_delegation"]:
                delegation_indicators = [
                    query["expected_agent"],
                    "specialized tool",
                    "using the",
                    "specialist"
                ]
                if any(indicator.lower() in content.lower() for indicator in delegation_indicators):
                    logger.info(f"✅ Correctly delegated to {query['expected_agent']}")
                else:
                    logger.warning(f"❌ Expected delegation to {query['expected_agent']}")
            else:
                logger.info("✅ Handled directly by orchestrator")
        else:
            logger.warning("No assistant response found")

def main():
    """Main test function."""
    # Load deployment info
    with open("deployment_info.json", "r") as f:
        deployment_info = json.load(f)
    
    orchestrator_id = deployment_info["orchestrator_agent_id"]
    
    # Test queries
    test_queries = [
        {
            "query": "Hello!",
            "expected": "Enthusiastic greeting",
            "expected_delegation": True,
            "expected_agent": "Enthusiastic Greeter"
        },
        {
            "query": "What's the weather in Seattle?",
            "expected": "Weather information for Seattle",
            "expected_delegation": True,
            "expected_agent": "Weather Information Specialist"
        },
        {
            "query": "Give me a greeting",
            "expected": "Enthusiastic greeting",
            "expected_delegation": True,
            "expected_agent": "Enthusiastic Greeter"
        },
        {
            "query": "What's the temperature in Miami?",
            "expected": "Temperature information for Miami",
            "expected_delegation": True,
            "expected_agent": "Weather Information Specialist"
        },
        {
            "query": "What is 2+2?",
            "expected": "Direct answer: 4",
            "expected_delegation": False,
            "expected_agent": None
        },
        {
            "query": "Tell me about Python",
            "expected": "Information about Python",
            "expected_delegation": False,
            "expected_agent": None
        }
    ]
    
    test_orchestrator(orchestrator_id, test_queries)
    
    logger.info("\n" + "=" * 60)
    logger.info("TEST COMPLETE")
    logger.info("=" * 60)

if __name__ == "__main__":
    main()