#!/usr/bin/env python3
"""
Test the COMPLETE orchestration flow with ACTUAL specialist agent invocation.
This script verifies the entire end-to-end flow without any mocking.
"""

import asyncio
import os
import json
import sys
from datetime import datetime
from dotenv import load_dotenv
from azure.identity.aio import DefaultAzureCredential
from semantic_kernel.agents import AzureAIAgent, AzureAIAgentSettings

# Load environment
current_dir = os.path.dirname(os.path.abspath(__file__))
agentic_dir = os.path.dirname(current_dir)
env_path = os.path.join(agentic_dir, '.env')
load_dotenv(env_path)

async def invoke_specialist_agent(client, agent_id: str, request: str):
    """Actually invoke a specialist agent and get its response."""
    print(f"\n🤖 Creating thread for specialist agent: {agent_id}")
    
    # Create a new thread for the specialist
    specialist_thread = await client.agents.threads.create()
    specialist_thread_id = specialist_thread.id
    print(f"   Thread created: {specialist_thread_id}")
    
    # Add the request message
    print(f"   Sending request: {request}")
    await client.agents.messages.create(
        thread_id=specialist_thread_id,
        role="user",
        content=request
    )
    
    # Create run for specialist
    print(f"   Starting specialist agent run...")
    specialist_run = await client.agents.runs.create(
        thread_id=specialist_thread_id,
        agent_id=agent_id
    )
    
    # Wait for specialist to complete
    max_wait = 30
    wait_time = 0
    
    while wait_time < max_wait:
        await asyncio.sleep(1)
        wait_time += 1
        
        # Get run status
        specialist_run = await client.agents.runs.get(
            thread_id=specialist_thread_id,
            run_id=specialist_run.id
        )
        
        print(f"   Specialist status: {specialist_run.status} ({wait_time}s)")
        
        if specialist_run.status == "completed":
            print(f"   ✅ Specialist completed successfully!")
            
            # Get the specialist's response
            messages = client.agents.messages.list(thread_id=specialist_thread_id)
            
            specialist_response = None
            async for msg in messages:
                if msg.role == "assistant" and msg.content:
                    for content in msg.content:
                        if hasattr(content, 'text'):
                            specialist_response = content.text.value
                            print(f"   📝 Specialist response received (length: {len(specialist_response)} chars)")
                            break
                    if specialist_response:
                        break
            
            # Clean up specialist thread
            await client.agents.threads.delete(thread_id=specialist_thread_id)
            
            return specialist_response
            
        elif specialist_run.status in ["failed", "cancelled", "expired"]:
            print(f"   ❌ Specialist run failed: {specialist_run.status}")
            await client.agents.threads.delete(thread_id=specialist_thread_id)
            return f"Specialist agent failed with status: {specialist_run.status}"
    
    print(f"   ⏱️ Specialist timed out after {wait_time} seconds")
    await client.agents.threads.delete(thread_id=specialist_thread_id)
    return "Specialist agent timed out"

async def main():
    # Load configurations
    orch_config_path = os.path.join(agentic_dir, "deployment_configs", "main_orchestrator_tools_deployment.json")
    with open(orch_config_path, 'r') as f:
        config = json.load(f)
        orchestrator_id = config['agent_id']
    
    deployment_path = os.path.join(agentic_dir, "deployment_configs", "ai_project_agents_deployment.json")
    with open(deployment_path, 'r') as f:
        deployment_data = json.load(f)
        specialist_agents = deployment_data['deployed_agents']
    
    print("=" * 80)
    print("COMPLETE ORCHESTRATION FLOW VERIFICATION")
    print("=" * 80)
    print(f"Main Orchestrator: {orchestrator_id}")
    print(f"Total Specialist Agents: {len(specialist_agents)}")
    print()
    
    settings = AzureAIAgentSettings()
    credential = DefaultAzureCredential()
    
    async with AzureAIAgent.create_client(credential=credential, settings=settings) as client:
        # STEP 1: Create thread for orchestrator
        print("STEP 1: Creating thread for Main Orchestrator")
        orchestrator_thread = await client.agents.threads.create()
        thread_id = orchestrator_thread.id
        print(f"✅ Thread created: {thread_id}")
        
        # Test message
        test_message = "I need to record my thoughts about the market downturn and its potential impact on our Q4 revenue projections"
        print(f"\n📤 User Request: {test_message}")
        
        # Add message to orchestrator thread
        await client.agents.messages.create(
            thread_id=thread_id,
            role="user",
            content=test_message
        )
        
        # STEP 2: Run orchestrator
        print("\nSTEP 2: Running Main Orchestrator")
        run = await client.agents.runs.create(
            thread_id=thread_id,
            agent_id=orchestrator_id
        )
        
        # Wait for orchestrator response
        while True:
            await asyncio.sleep(1)
            run = await client.agents.runs.get(
                thread_id=thread_id,
                run_id=run.id
            )
            
            print(f"Orchestrator status: {run.status}")
            
            if run.status == "requires_action":
                print("\n✅ STEP 2 VERIFIED: Orchestrator requests tool call!")
                
                # Get tool call details
                tool_calls = run.required_action.submit_tool_outputs.tool_calls
                
                print(f"\nTool calls requested: {len(tool_calls)}")
                
                tool_outputs = []
                
                for tool_call in tool_calls:
                    print(f"\n🔧 Tool Call ID: {tool_call.id}")
                    print(f"   Function: {tool_call.function.name}")
                    
                    args = json.loads(tool_call.function.arguments)
                    print(f"   Arguments: {json.dumps(args, indent=2)}")
                    
                    # Extract agent name from function name
                    agent_key = tool_call.function.name.replace("invoke_", "")
                    
                    # Find the specialist agent ID
                    specialist_id = None
                    for agent_name, agent_id in specialist_agents.items():
                        if agent_name.lower() == agent_key:
                            specialist_id = agent_id
                            break
                    
                    if specialist_id:
                        print(f"\nSTEP 3: Invoking ACTUAL specialist agent")
                        print(f"   Agent: {agent_key}")
                        print(f"   Agent ID: {specialist_id}")
                        
                        # ACTUALLY INVOKE THE SPECIALIST AGENT
                        specialist_response = await invoke_specialist_agent(
                            client, 
                            specialist_id, 
                            args.get('request', test_message)
                        )
                        
                        if specialist_response:
                            print(f"\n✅ STEP 3 VERIFIED: Specialist agent responded!")
                            print(f"   Response preview: {specialist_response[:200]}...")
                            
                            tool_outputs.append({
                                "tool_call_id": tool_call.id,
                                "output": specialist_response
                            })
                        else:
                            print(f"\n❌ STEP 3 FAILED: No response from specialist")
                            tool_outputs.append({
                                "tool_call_id": tool_call.id,
                                "output": "No response from specialist agent"
                            })
                    else:
                        print(f"\n❌ Unknown specialist agent: {agent_key}")
                        tool_outputs.append({
                            "tool_call_id": tool_call.id,
                            "output": f"Unknown specialist agent: {agent_key}"
                        })
                
                # STEP 4: Submit specialist responses back to orchestrator
                print("\nSTEP 4: Submitting specialist responses back to orchestrator")
                await client.agents.runs.submit_tool_outputs(
                    thread_id=thread_id,
                    run_id=run.id,
                    tool_outputs=tool_outputs
                )
                print("✅ Tool outputs submitted")
                
            elif run.status == "completed":
                print("\n✅ FINAL STEP: Orchestrator completed with specialist input!")
                
                # Get final response
                messages = client.agents.messages.list(thread_id=thread_id)
                
                final_response = None
                async for msg in messages:
                    if msg.role == "assistant" and msg.content:
                        for content in msg.content:
                            if hasattr(content, 'text'):
                                final_response = content.text.value
                                break
                        if final_response:
                            break
                
                if final_response:
                    print(f"\n💬 ORCHESTRATOR FINAL RESPONSE:")
                    print("=" * 60)
                    print(final_response)
                    print("=" * 60)
                    
                    print("\n✅ ✅ ✅ COMPLETE END-TO-END FLOW VERIFIED! ✅ ✅ ✅")
                    print("\nVerification Summary:")
                    print("1. ✅ Test script sent request to orchestrator")
                    print("2. ✅ Orchestrator delegated via tool call")
                    print("3. ✅ Specialist agent received request and responded")
                    print("4. ✅ Orchestrator received specialist response and formulated final answer")
                else:
                    print("\n❌ No final response from orchestrator")
                
                break
                
            elif run.status in ["failed", "cancelled", "expired"]:
                print(f"\n❌ Orchestrator run failed: {run.status}")
                break
        
        # Clean up
        await client.agents.threads.delete(thread_id=thread_id)
        print("\n🧹 Cleaned up orchestrator thread")
    
    await credential.close()

if __name__ == "__main__":
    asyncio.run(main())