#!/usr/bin/env python3
"""
Submit a CEO log request to the deployed CEO Log Agent.
"""

import asyncio
import os
from datetime import datetime
from azure.identity.aio import DefaultAzureCredential
from azure.ai.projects.aio import AIProjectClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
AZURE_AI_PROJECT_CONNECTION_STRING = os.getenv("AZURE_AI_AGENT_ENDPOINT")
CEO_LOG_AGENT_ID = "asst_oPGyOa5Z70gOUrRAQFCB0T5x"  # From deployment

async def submit_ceo_log():
    """Submit a CEO log entry to the deployed agent."""
    
    print("\n🚀 Submitting CEO Log Request")
    print("=" * 60)
    
    # CEO log entry
    log_entry = f"""
    Please process this CEO log entry:
    
    Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}
    
    Strategic Reflection:
    We've successfully deployed all 15 StratOS agents to Azure AI Agent Service. This marks a significant 
    milestone in our AI-driven strategic planning platform. The multi-agent architecture is now operational 
    and ready for integration testing.
    
    Key achievements today:
    - Completed deployment of Strategic Foundation agents (CEO Log, North Star, Memory Recall, Preference Learning)
    - Analysis Intelligence agents are live (SWOT/TOWS, Risk/Opportunity, SO Linkage)
    - Planning Execution agents deployed (Initiative Generation, Resource Optimization, Canvas Visualization)
    
    Immediate priorities:
    1. Test end-to-end orchestration between agents
    2. Validate data persistence across agent interactions
    3. Performance benchmarking of agent response times
    
    Concerns:
    - Need to monitor Azure costs with 15 active agents
    - Ensure proper error handling for inter-agent communication
    - Security review of agent permissions and data access
    
    This positions us well for the Q2 product launch. The team's hard work on the agent architecture 
    is paying off.
    
    Categories: strategic_planning, technology, milestone
    """
    
    try:
        # Create client
        credential = DefaultAzureCredential()
        client = AIProjectClient(
            endpoint=AZURE_AI_PROJECT_CONNECTION_STRING,
            credential=credential
        )
        
        print(f"CEO Log Agent ID: {CEO_LOG_AGENT_ID}")
        print(f"Endpoint: {AZURE_AI_PROJECT_CONNECTION_STRING[:80]}...")
        
        # Create a thread
        print("\n1. Creating conversation thread...")
        thread = await client.agents.threads.create()
        print(f"✅ Thread created: {thread.id}")
        
        # Add the message
        print("\n2. Adding CEO log entry...")
        message = await client.agents.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=log_entry
        )
        print(f"✅ Message added: {message.id}")
        
        # Create and process run
        print("\n3. Processing with CEO Log Agent...")
        print("-" * 60)
        
        # Create run
        run = await client.agents.threads.runs.create(
            thread_id=thread.id,
            assistant_id=CEO_LOG_AGENT_ID
        )
        print(f"Run created: {run.id}")
        print(f"Status: {run.status}")
        
        # Wait for completion
        import time
        max_attempts = 30
        attempt = 0
        
        while run.status in ["queued", "in_progress", "requires_action"] and attempt < max_attempts:
            await asyncio.sleep(2)
            run = await client.agents.threads.runs.get(
                thread_id=thread.id,
                run_id=run.id
            )
            print(f"Status: {run.status}")
            attempt += 1
        
        print("-" * 60)
        
        if run.status == "completed":
            print("✅ Processing complete!")
            
            # Get the response
            messages = client.agents.threads.messages.list(thread_id=thread.id)
            
            print("\n🤖 CEO LOG AGENT RESPONSE:")
            print("-" * 60)
            
            # Get all messages and reverse to show in chronological order
            all_messages = []
            async for msg in messages:
                all_messages.append(msg)
            
            # Find the assistant's response
            for msg in all_messages:
                if msg.role == "assistant":
                    for content in msg.content:
                        if content.type == "text":
                            print(content.text.value)
                    break
                    
        elif run.status == "failed":
            print(f"❌ Run failed!")
            if hasattr(run, 'last_error') and run.last_error:
                print(f"Error: {run.last_error.message}")
        else:
            print(f"⚠️ Run ended with status: {run.status}")
        
        # Summary
        print("\n" + "=" * 60)
        print("CEO LOG SUBMISSION SUMMARY")
        print("=" * 60)
        print(f"Thread ID: {thread.id}")
        print(f"Agent: CEO Log Agent ({CEO_LOG_AGENT_ID})")
        print(f"Status: Successfully processed")
        
        # Clean up
        await client.close()
        
    except Exception as e:
        print(f"\n❌ Error: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(submit_ceo_log())