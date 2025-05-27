#!/usr/bin/env python3
"""Quick test of the redeployed multi-agent system."""

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
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Environment variables
connection_string = os.getenv("AZURE_AI_PROJECT_CONNECTION_STRING")

def test_agent(orchestrator_id, query):
    """Test a single query."""
    credential = DefaultAzureCredential()
    client = AIProjectClient(endpoint=connection_string, credential=credential)
    
    # Create a thread
    thread = client.agents.threads.create()
    
    # Add message
    message = client.agents.messages.create(
        thread_id=thread.id,
        role="user",
        content=query
    )
    
    # Create run
    run = client.agents.runs.create(
        thread_id=thread.id,
        body={"assistant_id": orchestrator_id}
    )
    
    # Wait for completion
    while run.status in ["queued", "in_progress", "requires_action"]:
        time.sleep(1)
        run = client.agents.runs.get(thread_id=thread.id, run_id=run.id)
    
    # Get messages
    messages = client.agents.messages.list(thread_id=thread.id)
    
    # Find the assistant's response
    assistant_messages = [m for m in messages if m.role == "assistant"]
    if assistant_messages:
        response = assistant_messages[0].content[0].text.value if assistant_messages[0].content else "No content"
        return response
    return "No response"

def main():
    """Main test function."""
    # Load deployment info
    with open("deployment_info.json", "r") as f:
        deployment_info = json.load(f)
    
    orchestrator_id = deployment_info["orchestrator_agent_id"]
    
    logger.info("=" * 70)
    logger.info("TESTING REDEPLOYED MULTI-AGENT SYSTEM")
    logger.info("=" * 70)
    
    # Test cases
    tests = [
        ("Hello!", "Greeting"),
        ("What's the weather in Seattle?", "Weather"),
        ("What is 2+2?", "Math")
    ]
    
    for query, test_type in tests:
        logger.info(f"\n📝 Test: {test_type}")
        logger.info(f"❓ Query: {query}")
        
        response = test_agent(orchestrator_id, query)
        
        logger.info(f"💬 Response: {response[:100]}..." if len(response) > 100 else f"💬 Response: {response}")
        
        # Check delegation
        if test_type == "Greeting" and "HELLO THERE!!!" in response and "🎉" in response:
            logger.info("✅ Successfully delegated to Enthusiastic Greeter!")
        elif test_type == "Weather" and "📍" in response:
            logger.info("✅ Successfully delegated to Weather Agent!")
        elif test_type == "Math" and "4" in response:
            logger.info("✅ Correctly handled by orchestrator!")
        else:
            logger.info("⚠️  Check delegation behavior")
    
    logger.info("\n" + "=" * 70)
    logger.info("TEST COMPLETE")
    logger.info("=" * 70)

if __name__ == "__main__":
    main()