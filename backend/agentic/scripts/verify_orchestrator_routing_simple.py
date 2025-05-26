#!/usr/bin/env python3
"""
Simple verification of orchestrator routing behavior.
"""

import asyncio
import os
import sys
import json
from dotenv import load_dotenv

# Path setup
current_dir = os.path.dirname(os.path.abspath(__file__))
agentic_dir = os.path.dirname(current_dir)
env_path = os.path.join(agentic_dir, '.env')
load_dotenv(env_path)

# Import required modules
from azure.identity.aio import DefaultAzureCredential
from semantic_kernel.agents import AzureAIAgent, AzureAIAgentSettings

async def main():
    # Load orchestrator ID
    deployment_config_path = os.path.join(agentic_dir, "deployment_configs", "main_orchestrator_deployment.json")
    with open(deployment_config_path, 'r') as f:
        config = json.load(f)
        orchestrator_id = config['agent_id']
        print(f"Main Orchestrator ID: {orchestrator_id}")
    
    settings = AzureAIAgentSettings()
    credential = DefaultAzureCredential()
    
    async with AzureAIAgent.create_client(credential=credential, settings=settings) as client:
        # Get the agent
        agent_def = await client.agents.get_agent(agent_id=orchestrator_id)
        
        # Create agent instance
        orchestrator = AzureAIAgent(
            client=client,
            definition=agent_def
        )
        
        # Create thread
        thread = await client.agents.threads.create()
        thread_id = thread.id
        print(f"\nThread created: {thread_id}")
        
        # Test message
        test_message = "I need to record my thoughts about the market downturn and how it might affect our expansion plans"
        print(f"\nUser: {test_message}")
        
        # Add message and run
        await thread.add_user_message(test_message)
        
        # Instead of using invoke, let's create a run manually to see what happens
        run = await client.agents.runs.create_and_process(
            thread_id=thread_id,
            assistant_id=orchestrator_id
        )
        
        print(f"\nRun completed with status: {run.status}")
        
        # Check if any tools were called
        if hasattr(run, 'steps'):
            print(f"\nRun had {len(run.steps)} steps")
            for i, step in enumerate(run.steps):
                print(f"\nStep {i+1}: {step.type}")
                if hasattr(step, 'step_details') and step.step_details:
                    print(f"Details: {step.step_details}")
        
        # Get messages
        messages = await client.agents.messages.list(thread_id=thread_id)
        
        print("\n" + "="*80)
        print("MESSAGES IN THREAD:")
        print("="*80)
        
        for msg in messages.data:
            print(f"\n{msg.role.upper()}:")
            if msg.content:
                for content in msg.content:
                    if hasattr(content, 'text'):
                        print(content.text.value)
        
        # Clean up
        await client.agents.threads.delete(thread_id=thread_id)
        
    await credential.close()
    
    print("\n" + "="*80)
    print("ANALYSIS:")
    print("="*80)
    print("If the orchestrator properly routed to a connected agent, we should see:")
    print("1. Multiple steps in the run")
    print("2. Tool calls to connected agents")
    print("3. A response that appears to come from the CEO Log Agent")
    print("\nIf it didn't route, we'll see:")
    print("1. A single step")
    print("2. Generic response from the orchestrator itself")

if __name__ == "__main__":
    asyncio.run(main())