import asyncio
from openai import AsyncAzureOpenAI
import os
import sys
from dotenv import load_dotenv

# Add the agentic directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

async def test_strategic_planning_flow():
    """Test the orchestrator with a strategic planning request"""
    load_dotenv()
    
    client = AsyncAzureOpenAI(
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_version="2024-02-15-preview"
    )
    
    # Get orchestrator
    orchestrator_id = "asst_IkSbH3d9TaRWfpOcCCE4QxK4"
    
    # Create thread
    thread = await client.agents.threads.create()
    thread_id = thread.id
    
    print("="*80)
    print("TESTING STRATEGIC PLANNING REQUEST")
    print("="*80)
    
    # Test request
    request = "I need to create a strategic plan for expanding into the European market. What initiatives should we prioritize?"
    
    print(f"\n📤 User Request: {request}")
    
    # Send message
    await client.agents.messages.create(
        thread_id=thread_id,
        role="user",
        content=request
    )
    
    # Run orchestrator
    run = await client.agents.runs.create(
        thread_id=thread_id,
        agent_id=orchestrator_id
    )
    
    # Wait for response
    start_time = asyncio.get_event_loop().time()
    while run.status in ["in_progress", "queued", "requires_action"]:
        await asyncio.sleep(1)
        run = await client.agents.runs.retrieve(thread_id=thread_id, run_id=run.id)
        elapsed = int(asyncio.get_event_loop().time() - start_time)
        
        if run.status == "requires_action":
            print(f"\n🔧 Orchestrator delegating to specialist agent...")
            tool_call = run.required_action.tool_calls[0]
            print(f"   Function: {tool_call.function.name}")
            print(f"   Arguments: {tool_call.function.arguments}")
            
            # For demonstration, just show the routing
            await client.agents.runs.submit_tool_outputs(
                thread_id=thread_id,
                run_id=run.id,
                tool_outputs=[{
                    "tool_call_id": tool_call.id,
                    "output": "Strategic plan created: 1) Market research in key European countries, 2) Regulatory compliance assessment, 3) Partner identification, 4) Localization strategy, 5) Phased rollout plan"
                }]
            )
        else:
            print(f"   Status: {run.status} ({elapsed}s)", end="\r")
    
    if run.status == "completed":
        # Get response
        messages = await client.agents.messages.list(thread_id=thread_id)
        response = messages.data[0].content[0].text.value
        
        print(f"\n\n💬 ORCHESTRATOR RESPONSE:")
        print("="*60)
        print(response)
        print("="*60)
        
        # Verify routing occurred
        if "strategic" in response.lower() or "plan" in response.lower():
            print("\n✅ Strategic planning request handled successfully\!")
        else:
            print("\n⚠️  Response doesn't seem to address strategic planning")
    
    # Cleanup
    await client.agents.threads.delete(thread_id=thread_id)

if __name__ == "__main__":
    asyncio.run(test_strategic_planning_flow())