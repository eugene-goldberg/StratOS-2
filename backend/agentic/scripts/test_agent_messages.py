#!/usr/bin/env python3
"""
Test agent and show thread messages.
"""

import asyncio
import os
import logging
from dotenv import load_dotenv

from azure.identity.aio import DefaultAzureCredential
from semantic_kernel.agents import AzureAIAgent, AzureAIAgentSettings

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment
current_dir = os.path.dirname(os.path.abspath(__file__))
agentic_dir = os.path.dirname(current_dir) 
load_dotenv(os.path.join(agentic_dir, '.env'))

async def test_agent_with_messages():
    """Test agent and examine thread messages."""
    
    # Test with CEO Log Agent
    agent_id = "asst_N5azTOnrhdlm4K9wC6i9OtHA"
    
    try:
        # Create settings
        settings = AzureAIAgentSettings()
        
        # Create credential and client
        async with DefaultAzureCredential(exclude_interactive_browser_credential=False) as credential:
            async with AzureAIAgent.create_client(credential=credential, settings=settings) as client:
                logger.info("Client created")
                
                # Get agent
                agent_def = await client.agents.get_agent(agent_id=agent_id)
                print(f"\nAgent: {agent_def.name}")
                print(f"Description: {agent_def.description}")
                print(f"Instructions: {agent_def.instructions[:200]}...")
                
                # Create thread explicitly
                thread = await client.threads.create_thread()
                thread_id = thread.id
                print(f"\nThread created: {thread_id}")
                
                # Add message to thread
                message = "I met with the board today. We approved a $20M investment in AI infrastructure. This will accelerate our product development significantly."
                print(f"\nAdding message: {message}")
                
                user_msg = await client.threads.create_message(
                    thread_id=thread_id,
                    role="user",
                    content=message
                )
                print(f"Message added: {user_msg.id}")
                
                # Run the agent
                print("\nCreating run...")
                run = await client.threads.create_run(
                    thread_id=thread_id,
                    assistant_id=agent_id
                )
                print(f"Run created: {run.id}, status: {run.status}")
                
                # Wait for completion
                while run.status in ["queued", "in_progress", "cancelling"]:
                    await asyncio.sleep(0.5)
                    run = await client.threads.get_run(
                        thread_id=thread_id,
                        run_id=run.id
                    )
                    print(f"Run status: {run.status}")
                
                print(f"\nFinal run status: {run.status}")
                
                # Get all messages in thread
                print("\nGetting thread messages...")
                messages = client.threads.list_messages(thread_id=thread_id)
                
                print("\nAll thread messages:")
                async for msg in messages:
                    print(f"\n[{msg.role}] (ID: {msg.id}):")
                    if hasattr(msg, 'content') and msg.content:
                        for content in msg.content:
                            if hasattr(content, 'text'):
                                print(f"  {content.text.value}")
                            else:
                                print(f"  Content type: {type(content)}")
                    else:
                        print("  [No content]")
                        
                # Try to get run steps for more details
                print("\nGetting run steps...")
                steps = client.threads.runs.list_steps(
                    thread_id=thread_id,
                    run_id=run.id
                )
                
                async for step in steps:
                    print(f"\nStep: {step.id}")
                    print(f"  Type: {step.type}")
                    print(f"  Status: {step.status}")
                    if hasattr(step, 'step_details'):
                        print(f"  Details: {step.step_details}")
                        
    except Exception as e:
        logger.error(f"Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_agent_with_messages())