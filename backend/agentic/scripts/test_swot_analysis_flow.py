#\!/usr/bin/env python3
"""Test orchestration with SWOT analysis request."""

import asyncio
import os
import json
from openai import AsyncAzureOpenAI
from dotenv import load_dotenv

# Load environment directly
load_dotenv()

async def test_swot_flow():
    """Test SWOT analysis orchestration flow"""
    
    # Hardcoded IDs from deployment
    orchestrator_id = "asst_IkSbH3d9TaRWfpOcCCE4QxK4"
    
    print("=" * 80)
    print("SWOT ANALYSIS ORCHESTRATION TEST")
    print("=" * 80)
    print(f"Main Orchestrator: {orchestrator_id}")
    print()
    
    client = AsyncAzureOpenAI(
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_version="2024-02-15-preview"
    )
    
    # Create thread
    print("Creating thread for Main Orchestrator...")
    thread = await client.beta.threads.create()
    thread_id = thread.id
    print(f"✅ Thread created: {thread_id}")
    
    # Test message
    test_message = "I need a SWOT analysis for our planned expansion into Asia-Pacific markets"
    print(f"\n📤 User Request: {test_message}")
    
    # Add message
    await client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=test_message
    )
    
    # Run orchestrator
    print("\nRunning Main Orchestrator...")
    run = await client.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=orchestrator_id
    )
    
    # Wait for response
    max_wait = 60
    wait_time = 0
    
    while wait_time < max_wait:
        await asyncio.sleep(1)
        wait_time += 1
        
        run = await client.beta.threads.runs.retrieve(
            thread_id=thread_id,
            run_id=run.id
        )
        
        print(f"Status: {run.status} ({wait_time}s)", end="\r")
        
        if run.status == "requires_action":
            print(f"\n\n✅ Orchestrator requesting tool call\!")
            
            tool_calls = run.required_action.submit_tool_outputs.tool_calls
            print(f"Tool calls: {len(tool_calls)}")
            
            for tc in tool_calls:
                print(f"\n🔧 Function: {tc.function.name}")
                print(f"   Arguments: {tc.function.arguments}")
            
            # For demo, just show routing
            await client.beta.threads.runs.submit_tool_outputs(
                thread_id=thread_id,
                run_id=run.id,
                tool_outputs=[{
                    "tool_call_id": tc.id,
                    "output": "SWOT Analysis: Strengths - Strong brand, proven business model. Weaknesses - Limited local knowledge. Opportunities - Growing middle class, digital adoption. Threats - Regulatory uncertainties, local competition."
                } for tc in tool_calls]
            )
            
        elif run.status == "completed":
            print(f"\n\n✅ Orchestrator completed\!")
            
            # Get response
            messages = await client.beta.threads.messages.list(thread_id=thread_id)
            for msg in messages.data:
                if msg.role == "assistant":
                    print(f"\n💬 ORCHESTRATOR RESPONSE:")
                    print("=" * 60)
                    print(msg.content[0].text.value)
                    print("=" * 60)
                    break
            break
            
        elif run.status in ["failed", "cancelled", "expired"]:
            print(f"\n❌ Run failed: {run.status}")
            break
    
    # Cleanup
    await client.beta.threads.delete(thread_id=thread_id)
    print("\n🧹 Cleaned up thread")

if __name__ == "__main__":
    asyncio.run(test_swot_flow())
