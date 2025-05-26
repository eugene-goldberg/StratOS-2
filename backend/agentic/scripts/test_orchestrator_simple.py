#!/usr/bin/env python3
"""
Simple test of the Main Orchestrator's routing.
"""

import asyncio
import os
import json
from dotenv import load_dotenv
from azure.identity.aio import DefaultAzureCredential
from semantic_kernel.agents import AzureAIAgent, AzureAIAgentSettings

# Load environment
current_dir = os.path.dirname(os.path.abspath(__file__))
agentic_dir = os.path.dirname(current_dir)
env_path = os.path.join(agentic_dir, '.env')
load_dotenv(env_path)

async def main():
    # Load orchestrator ID
    config_path = os.path.join(agentic_dir, "deployment_configs", "main_orchestrator_deployment.json")
    with open(config_path, 'r') as f:
        config = json.load(f)
        orchestrator_id = config['agent_id']
    
    print(f"Testing Main Orchestrator: {orchestrator_id}")
    
    settings = AzureAIAgentSettings()
    credential = DefaultAzureCredential()
    
    async with AzureAIAgent.create_client(credential=credential, settings=settings) as client:
        # Create thread
        thread = await client.agents.threads.create()
        thread_id = thread.id
        print(f"Thread created: {thread_id}")
        
        # Test messages
        test_messages = [
            "I need to record my thoughts about the market downturn",
            "Can you perform a SWOT analysis for our new product?",
            "What is our company's vision and mission?"
        ]
        
        for test_message in test_messages:
            print(f"\n{'='*60}")
            print(f"Testing: {test_message}")
        
        # Add message
        await client.agents.messages.create(
            thread_id=thread_id,
            role="user", 
            content=test_message
        )
        
        # Create run
        run = await client.agents.runs.create(
            thread_id=thread_id,
            agent_id=orchestrator_id
        )
        
        print(f"Run created: {run.id}")
        
        # Wait for completion (simple polling)
        while run.status in ["queued", "in_progress"]:
            await asyncio.sleep(1)
            run = await client.agents.runs.get(
                thread_id=thread_id,
                run_id=run.id
            )
            print(f"Status: {run.status}")
        
        # Get messages
        messages = client.agents.messages.list(thread_id=thread_id)
        
        print("\nConversation:")
        async for msg in messages:
            role = msg.role.upper()
            if msg.content:
                for content in msg.content:
                    if hasattr(content, 'text'):
                        print(f"\n{role}: {content.text.value}")
        
        # Clean up
        await client.agents.threads.delete(thread_id=thread_id)
    
    await credential.close()

if __name__ == "__main__":
    asyncio.run(main())