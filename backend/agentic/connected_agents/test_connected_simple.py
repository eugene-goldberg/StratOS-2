#!/usr/bin/env python3
"""Simple test of connected agents pattern to debug tool usage."""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from azure.ai.projects import AIProjectClient
from azure.ai.agents.models import ConnectedAgentTool, FunctionTool
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv

# Load environment variables from connected_agents folder
load_dotenv(Path(__file__).parent / ".env")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - [%(funcName)s] %(message)s",
)
logger = logging.getLogger(__name__)


async def main():
    """Test connected agents with detailed logging."""
    # Get credentials and configuration
    connection_string = os.getenv("AZURE_AI_PROJECT_CONNECTION_STRING", "").strip()
    if not connection_string:
        raise ValueError("AZURE_AI_PROJECT_CONNECTION_STRING not set in environment")
    
    # Extract endpoint from connection string (it IS the endpoint)
    endpoint = connection_string
    
    credential = DefaultAzureCredential()
    model = os.getenv("AZURE_AI_MODEL_DEPLOYMENT_NAME", "gpt-35-turbo")
    
    logger.info(f"Endpoint: {endpoint[:50]}...")
    logger.info(f"Model: {model}")
    
    try:
        client = AIProjectClient(
            endpoint=endpoint,
            credential=credential
        )
        
        # 1. Create specialized greeter agent
        greeter_agent = client.agents.create_agent(
            model=model,
            name="EnthusiasticGreeter",
            instructions=(
                "You are the 'Exuberant Greeter Bot'! "
                "ALWAYS provide extremely enthusiastic greetings with LOTS of CAPITAL LETTERS and emojis! "
                "Start with 'HELLO THERE!!!' and be super excited!"
            )
        )
        logger.info(f"Created greeter agent: {greeter_agent.id}")
        
        # 2. Create connected agent tool
        connected_tool = ConnectedAgentTool(
            id=greeter_agent.id,
            name="enthusiastic_greeter",
            description="Get an enthusiastic greeting from the specialized greeter bot"
        )
        
        # Log the tool definition structure
        logger.info(f"ConnectedAgentTool type: {type(connected_tool)}")
        logger.info(f"ConnectedAgentTool attributes: {dir(connected_tool)}")
        
        # Check if it has definitions
        if hasattr(connected_tool, 'definitions'):
            logger.info(f"Tool definitions: {connected_tool.definitions}")
            logger.info(f"Tool definitions type: {type(connected_tool.definitions)}")
            logger.info(f"Number of definitions: {len(connected_tool.definitions) if connected_tool.definitions else 0}")
            
            # Log each definition
            if connected_tool.definitions:
                for i, definition in enumerate(connected_tool.definitions):
                    logger.info(f"Definition {i}: {definition}")
                    logger.info(f"Definition {i} type: {type(definition)}")
                    if hasattr(definition, '__dict__'):
                        logger.info(f"Definition {i} attributes: {definition.__dict__}")
        
        # 3. Create orchestrator with more explicit instructions
        orchestrator_instructions = (
            "You are an orchestrator assistant with access to specialized tools. "
            "You have ONE connected agent tool that provides enthusiastic greetings. "
            "IMPORTANT: When the user asks for ANY kind of greeting (hello, hi, greet me, etc.), "
            "you MUST use your connected agent tool to get the greeting. "
            "Do NOT provide your own greetings - always delegate to the tool. "
            "For other questions, you can answer directly."
        )
        
        orchestrator_agent = client.agents.create_agent(
            model=model,
            name="Orchestrator",
            instructions=orchestrator_instructions,
            tools=connected_tool.definitions if connected_tool.definitions else []
        )
        logger.info(f"Created orchestrator agent: {orchestrator_agent.id}")
        
        # Check what tools the orchestrator has
        logger.info(f"Orchestrator tools: {orchestrator_agent.tools if hasattr(orchestrator_agent, 'tools') else 'No tools attribute'}")
        
        # 4. Test the orchestrator
        thread = client.agents.threads.create()
        logger.info(f"Created thread: {thread.id}")
        
        # Test greeting request
        test_message = "Hi there! Can you greet me?"
        logger.info(f"\nTesting with: '{test_message}'")
        
        message = client.agents.messages.create(
            thread_id=thread.id,
            role="user",
            content=test_message
        )
        
        run = client.agents.runs.create(
            thread_id=thread.id,
            body={"assistant_id": orchestrator_agent.id}
        )
        
        # Wait for completion with detailed status logging
        while run.status in ["queued", "in_progress", "requires_action"]:
            await asyncio.sleep(1)
            run = client.agents.runs.get(thread_id=thread.id, run_id=run.id)
            logger.info(f"Run status: {run.status}")
            
            # If requires_action, log the required action
            if run.status == "requires_action":
                logger.info(f"Required action: {run.required_action}")
        
        # Get response
        messages = client.agents.messages.list(thread_id=thread.id)
        
        logger.info("\n=== CONVERSATION ===")
        for msg in messages:
            role = msg.role.upper()
            content = msg.content[0].text.value if msg.content else "No content"
            logger.info(f"{role}: {content}")
        
        # Cleanup
        client.agents.delete_agent(orchestrator_agent.id)
        client.agents.delete_agent(greeter_agent.id)
        logger.info("\nAgents cleaned up successfully")
        
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())