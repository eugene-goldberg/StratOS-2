#!/usr/bin/env python3
"""
Test CEO Log Agent without Cosmos DB verification
Focus on agent calling Azure Function
"""

import os
import time
from datetime import datetime
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient

# Load environment variables
load_dotenv()

# Configuration
CEO_LOG_AGENT_ID = "asst_85MtpKLDOQA9ttsUckByGTKD"

def test_ceo_log_agent():
    """Test CEO Log Agent functionality"""
    print("\n" + "="*70)
    print("CEO LOG AGENT TEST")
    print("="*70)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Agent ID: {CEO_LOG_AGENT_ID}")
    
    # Connect to Azure AI Project
    endpoint = os.getenv("AZURE_AI_PROJECT_CONNECTION_STRING")
    if not endpoint:
        print("✗ AZURE_AI_PROJECT_CONNECTION_STRING not set")
        return
    
    credential = DefaultAzureCredential()
    client = AIProjectClient(endpoint=endpoint, credential=credential)
    
    try:
        # Verify agent exists
        print(f"\n1. Verifying agent deployment...")
        agent = client.agents.get_agent(CEO_LOG_AGENT_ID)
        print(f"✓ Agent found: {agent.name}")
        print(f"  Model: {agent.model}")
        print(f"  Tools: {len(agent.tools) if agent.tools else 0}")
        
        # Show tool configuration
        if agent.tools:
            print("\n  Tool Configuration:")
            for i, tool in enumerate(agent.tools):
                print(f"  Tool {i+1}: {tool.get('type', 'unknown')}")
                if tool.get('type') == 'function':
                    func = tool.get('function', {})
                    print(f"    Name: {func.get('name')}")
                    print(f"    Description: {func.get('description', '')[:100]}...")
        
        # Create thread
        print(f"\n2. Creating conversation thread...")
        thread = client.agents.create_thread()
        print(f"✓ Thread created: {thread.id}")
        
        # Prepare CEO log entry
        test_id = f"test_{int(time.time())}"
        log_entry = f"""Save this CEO log entry:

Had an exceptional quarterly board meeting today. Key outcomes:
1. Board approved 30% increase in AI R&D budget for Q2 2025
2. Green light for European market expansion starting July
3. Strategic partnership with TechCorp is now confirmed

Team morale is at an all-time high after exceeding Q1 targets by 20%.
Main concern: Supply chain disruptions may impact Q3 deliverables.

Test ID: {test_id}
Category: strategic_planning  
User ID: ceo_test_user_001"""
        
        print(f"\n3. Sending CEO log entry...")
        print("-" * 70)
        print(log_entry)
        print("-" * 70)
        
        # Add message
        message = client.agents.create_message(
            thread_id=thread.id,
            role="user",
            content=log_entry
        )
        
        # Create run
        print(f"\n4. Executing agent...")
        run = client.agents.create_run(
            thread_id=thread.id,
            assistant_id=CEO_LOG_AGENT_ID
        )
        
        # Monitor run status
        start_time = time.time()
        last_status = None
        
        while run.status in ["queued", "in_progress", "requires_action"]:
            if run.status != last_status:
                print(f"   Status: {run.status}")
                last_status = run.status
            
            time.sleep(1)
            run = client.agents.get_run(thread_id=thread.id, run_id=run.id)
            
            if time.time() - start_time > 60:
                print("✗ Timeout after 60 seconds")
                break
        
        print(f"   Final status: {run.status}")
        print(f"   Duration: {time.time() - start_time:.1f} seconds")
        
        # Get agent response
        if run.status == "completed":
            print(f"\n5. Agent response:")
            print("="*70)
            
            messages = client.agents.list_messages(thread_id=thread.id)
            response_found = False
            
            for msg in messages.data:
                if msg.role == "assistant":
                    for content in msg.content:
                        if hasattr(content, 'text') and content.text:
                            print(content.text.value)
                            response_found = True
                            
                            # Check if response indicates Azure Function was called
                            response_text = content.text.value.lower()
                            if any(word in response_text for word in ['saved', 'stored', 'created', 'function', 'azure', 'cosmos', 'database']):
                                print("\n✓ Response indicates Azure Function interaction!")
                    break
            
            print("="*70)
            
            if response_found:
                print("\n✅ TEST COMPLETED")
                print("The agent responded to the CEO log entry request.")
                print("Check the response above to verify if Azure Function was called.")
            else:
                print("\n⚠️ No response found from agent")
            
        else:
            print(f"\n✗ Agent run failed with status: {run.status}")
            if hasattr(run, 'last_error'):
                print(f"Error: {run.last_error}")
                
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_ceo_log_agent()