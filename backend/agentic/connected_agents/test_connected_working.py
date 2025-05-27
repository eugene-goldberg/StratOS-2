#!/usr/bin/env python3
"""Working test of connected agents pattern with proper delegation."""

import asyncio
import logging
import os
import sys
import json
from pathlib import Path

# Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from azure.ai.projects import AIProjectClient
from azure.ai.agents.models import ConnectedAgentTool
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
    """Test connected agents with improved delegation instructions."""
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
    
    greeter_agent = None
    orchestrator_agent = None
    
    try:
        client = AIProjectClient(
            endpoint=endpoint,
            credential=credential
        )
        
        # 1. Create specialized greeter agent with very specific behavior
        greeter_agent = client.agents.create_agent(
            model=model,
            name="EnthusiasticGreeterBot",
            instructions=(
                "You are the 'Exuberant Greeter Bot'! Your ONLY job is to provide "
                "EXTREMELY enthusiastic greetings. "
                "ALWAYS start your response with 'HELLO THERE!!! 🎉🎉🎉' "
                "Use LOTS of CAPITAL LETTERS, emojis like 🌟✨🎊, and exclamation marks!!! "
                "Be SUPER DUPER EXCITED about greeting people! "
                "Example: 'HELLO THERE!!! 🎉🎉🎉 OH MY GOODNESS, I'M SO EXCITED TO MEET YOU!!! ✨🌟'"
            )
        )
        logger.info(f"Created greeter agent: {greeter_agent.id}")
        
        # 2. Create connected agent tool
        connected_tool = ConnectedAgentTool(
            id=greeter_agent.id,
            name="enthusiastic_greeter_tool",
            description="Tool that provides extremely enthusiastic greetings with emojis and capital letters"
        )
        
        logger.info(f"Connected tool created with name: enthusiastic_greeter_tool")
        
        # 3. Create orchestrator with VERY explicit instructions about tool usage
        orchestrator_instructions = (
            "You are an orchestrator assistant that has access to specialized tools.\n\n"
            "IMPORTANT TOOL USAGE RULES:\n"
            "1. You have a tool called 'enthusiastic_greeter_tool' that provides enthusiastic greetings.\n"
            "2. When the user asks for ANY kind of greeting, hello, hi, or similar, you MUST:\n"
            "   - Use the 'enthusiastic_greeter_tool' to get the greeting\n"
            "   - Pass the greeting request to the tool\n"
            "   - Return the tool's response to the user\n"
            "3. DO NOT provide your own greetings - ALWAYS use the tool.\n"
            "4. For non-greeting questions, answer them normally.\n\n"
            "Example interaction:\n"
            "User: 'Hi there!'\n"
            "You: [Use enthusiastic_greeter_tool]\n"
            "Tool response: 'HELLO THERE!!! 🎉🎉🎉...'\n"
            "You: Return the tool's enthusiastic response\n\n"
            "Remember: ALWAYS delegate greetings to the enthusiastic_greeter_tool!"
        )
        
        orchestrator_agent = client.agents.create_agent(
            model=model,
            name="OrchestratorWithTools",
            instructions=orchestrator_instructions,
            tools=connected_tool.definitions
        )
        logger.info(f"Created orchestrator agent: {orchestrator_agent.id}")
        logger.info(f"Orchestrator tools: {orchestrator_agent.tools}")
        
        # 4. Test the orchestrator with multiple scenarios
        thread = client.agents.threads.create()
        logger.info(f"Created thread: {thread.id}")
        
        # Test cases
        test_messages = [
            "Hi there! Can you greet me please?",
            "Hello!",
            "Give me an enthusiastic greeting",
            "What is 2 + 2?",  # Non-greeting to test normal response
        ]
        
        for test_msg in test_messages:
            logger.info(f"\n{'='*60}")
            logger.info(f"Testing with: '{test_msg}'")
            logger.info(f"{'='*60}")
            
            # Create message
            message = client.agents.messages.create(
                thread_id=thread.id,
                role="user",
                content=test_msg
            )
            
            # Create run
            run = client.agents.runs.create(
                thread_id=thread.id,
                body={"assistant_id": orchestrator_agent.id}
            )
            
            # Wait for completion
            max_iterations = 30  # Prevent infinite loops
            iterations = 0
            
            while run.status in ["queued", "in_progress", "requires_action"] and iterations < max_iterations:
                await asyncio.sleep(1)
                iterations += 1
                
                run = client.agents.runs.get(thread_id=thread.id, run_id=run.id)
                logger.info(f"Run status: {run.status}")
                
                # Handle tool calls if needed
                if run.status == "requires_action":
                    logger.info("⚡ REQUIRES ACTION - Tool invocation needed!")
                    
                    if hasattr(run, 'required_action') and hasattr(run.required_action, 'submit_tool_outputs'):
                        tool_calls = run.required_action.submit_tool_outputs.tool_calls
                        logger.info(f"Tool calls required: {len(tool_calls)}")
                        
                        for tool_call in tool_calls:
                            logger.info(f"Tool call: {tool_call.function.name}")
                            logger.info(f"Tool arguments: {tool_call.function.arguments}")
                    
                    # Note: In a real implementation, you would handle the tool calls here
                    # For connected agents, Azure should handle this automatically
                    break
            
            # Get the latest message
            messages = client.agents.messages.list(
                thread_id=thread.id,
                order="desc",
                limit=2  # Get last 2 messages (user + assistant)
            )
            
            # Display conversation
            for msg in messages:
                if msg.role == "assistant" and msg.run_id == run.id:
                    content = msg.content[0].text.value if msg.content else "No content"
                    logger.info(f"\n🤖 ASSISTANT RESPONSE:\n{content}\n")
                    
                    # Check if delegation occurred
                    if any(greeting_word in test_msg.lower() for greeting_word in ["hi", "hello", "greet"]):
                        if "HELLO THERE!!!" in content and "🎉" in content:
                            logger.info("✅ SUCCESS: Orchestrator delegated to the enthusiastic greeter!")
                        else:
                            logger.warning("⚠️  WARNING: Expected delegation to greeter bot didn't occur")
                    break
        
        # Cleanup
        logger.info("\n🧹 Cleaning up agents...")
        if orchestrator_agent:
            client.agents.delete_agent(orchestrator_agent.id)
            logger.info(f"Deleted orchestrator: {orchestrator_agent.id}")
        if greeter_agent:
            client.agents.delete_agent(greeter_agent.id)
            logger.info(f"Deleted greeter: {greeter_agent.id}")
        logger.info("✅ Cleanup complete")
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        
        # Cleanup on error
        try:
            if orchestrator_agent:
                client.agents.delete_agent(orchestrator_agent.id)
            if greeter_agent:
                client.agents.delete_agent(greeter_agent.id)
        except:
            pass


if __name__ == "__main__":
    asyncio.run(main())