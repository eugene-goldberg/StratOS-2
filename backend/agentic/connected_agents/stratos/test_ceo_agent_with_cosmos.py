#!/usr/bin/env python3
"""Test CEO Log Agent with Azure Functions integration"""

import asyncio
import json
import os
from datetime import datetime
from azure.ai.projects.aio import AIProjectClient
from azure.identity.aio import DefaultAzureCredential

# Configuration
PROJECT_CONNECTION_STRING = "eastus2.api.azureml.ms;0a7a2d58-80d4-4d62-9c71-f87740c9b9f1;semantic-kernel-multi-agent;semantic-kernel-multi-agent-rg"

async def test_ceo_log_agent():
    """Test the CEO Log Agent with Azure Functions"""
    
    # Create AI Project client
    async with DefaultAzureCredential() as credential:
        client = AIProjectClient.from_connection_string(
            conn_str=PROJECT_CONNECTION_STRING,
            credential=credential
        )
        
        # Get agent by name
        agents = client.agents.list_agents()
        ceo_agent = None
        
        async for agent in agents:
            if agent.name == "CEOLogAgent":
                ceo_agent = agent
                break
        
        if not ceo_agent:
            print("❌ CEO Log Agent not found")
            return
        
        print(f"✅ Found CEO Log Agent: {ceo_agent.id}")
        
        # Create a thread
        thread = await client.agents.create_thread()
        print(f"✅ Created thread: {thread.id}")
        
        # Test 1: Save a log entry
        print("\n=== Test 1: Save CEO Log Entry ===")
        message1 = await client.agents.create_message(
            thread_id=thread.id,
            role="user",
            content="I'm concerned about our competitor's new AI product launch. We need to accelerate our innovation timeline and focus on our unique differentiators. The team is ready, but we need additional resources."
        )
        
        # Create and poll run
        run1 = await client.agents.create_and_process_run(
            thread_id=thread.id,
            assistant_id=ceo_agent.id
        )
        
        # Get response
        messages1 = await client.agents.list_messages(thread_id=thread.id)
        response1 = None
        async for msg in messages1:
            if msg.role == "assistant" and msg.created_at > message1.created_at:
                response1 = msg.content[0].text.value
                break
        
        print(f"Response: {response1}")
        
        # Test 2: Search for entries
        print("\n=== Test 2: Search CEO Logs ===")
        message2 = await client.agents.create_message(
            thread_id=thread.id,
            role="user",
            content="Find all my entries about competitor and innovation"
        )
        
        run2 = await client.agents.create_and_process_run(
            thread_id=thread.id,
            assistant_id=ceo_agent.id
        )
        
        messages2 = await client.agents.list_messages(thread_id=thread.id)
        response2 = None
        async for msg in messages2:
            if msg.role == "assistant" and msg.created_at > message2.created_at:
                response2 = msg.content[0].text.value
                break
        
        print(f"Response: {response2}")
        
        # Test 3: Get insights
        print("\n=== Test 3: Get Insights ===")
        message3 = await client.agents.create_message(
            thread_id=thread.id,
            role="user",
            content="What insights can you extract from my recent entries?"
        )
        
        run3 = await client.agents.create_and_process_run(
            thread_id=thread.id,
            assistant_id=ceo_agent.id
        )
        
        messages3 = await client.agents.list_messages(thread_id=thread.id)
        response3 = None
        async for msg in messages3:
            if msg.role == "assistant" and msg.created_at > message3.created_at:
                response3 = msg.content[0].text.value
                break
        
        print(f"Response: {response3}")
        
        # Test 4: Analyze entries
        print("\n=== Test 4: Analyze Entries ===")
        message4 = await client.agents.create_message(
            thread_id=thread.id,
            role="user",
            content="Analyze my entries this week about risks and opportunities"
        )
        
        run4 = await client.agents.create_and_process_run(
            thread_id=thread.id,
            assistant_id=ceo_agent.id
        )
        
        messages4 = await client.agents.list_messages(thread_id=thread.id)
        response4 = None
        async for msg in messages4:
            if msg.role == "assistant" and msg.created_at > message4.created_at:
                response4 = msg.content[0].text.value
                break
        
        print(f"Response: {response4}")
        
        # Clean up
        await client.agents.delete_thread(thread.id)
        print("\n✅ All tests completed successfully!")

if __name__ == "__main__":
    asyncio.run(test_ceo_log_agent())