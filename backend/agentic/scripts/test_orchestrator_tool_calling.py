#!/usr/bin/env python3
"""
Test the Main Orchestrator's tool calling capabilities.
This script verifies that the orchestrator returns tool calls instead of text responses.
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

async def test_tool_calling():
    """Test tool calling with various requests."""
    
    # Load orchestrator ID
    config_path = os.path.join(agentic_dir, "deployment_configs", "main_orchestrator_tools_deployment.json")
    
    if not os.path.exists(config_path):
        print("❌ Main Orchestrator with tools not deployed yet!")
        print("Run: python3 deploy_main_orchestrator_with_tools.py")
        return
    
    with open(config_path, 'r') as f:
        config = json.load(f)
        orchestrator_id = config['agent_id']
    
    print(f"Testing Main Orchestrator Tool Calling: {orchestrator_id}")
    print("=" * 80)
    
    # Test scenarios
    test_scenarios = [
        {
            "name": "CEO Log Entry",
            "message": "I need to record my thoughts about the market downturn and its impact on our Q4 strategy",
            "expected_tool": "invoke_ceologagent"
        },
        {
            "name": "SWOT Analysis",
            "message": "Can you perform a SWOT analysis for our new product launch?",
            "expected_tool": "invoke_swottowsagent"
        },
        {
            "name": "Resource Planning",
            "message": "How should we allocate our budget for the digital transformation initiative?",
            "expected_tool": "invoke_resourceoptimizationagent"
        },
        {
            "name": "Vision Query",
            "message": "What is our company's vision and mission statement?",
            "expected_tool": "invoke_northstaragent"
        }
    ]
    
    settings = AzureAIAgentSettings()
    credential = DefaultAzureCredential()
    
    async with AzureAIAgent.create_client(credential=credential, settings=settings) as client:
        for scenario in test_scenarios:
            print(f"\n{'='*60}")
            print(f"Test: {scenario['name']}")
            print(f"Message: \"{scenario['message']}\"")
            print(f"Expected Tool: {scenario['expected_tool']}")
            print("-" * 60)
            
            # Create thread
            thread = await client.agents.threads.create()
            thread_id = thread.id
            
            # Add message
            await client.agents.messages.create(
                thread_id=thread_id,
                role="user",
                content=scenario['message']
            )
            
            # Create run
            run = await client.agents.runs.create(
                thread_id=thread_id,
                agent_id=orchestrator_id
            )
            
            # Wait for completion or tool call
            max_wait = 30
            wait_time = 0
            
            while wait_time < max_wait:
                await asyncio.sleep(1)
                wait_time += 1
                
                run = await client.agents.runs.get(
                    thread_id=thread_id,
                    run_id=run.id
                )
                
                if run.status == "requires_action":
                    print("✅ Status: REQUIRES_ACTION (Tool call requested)")
                    
                    # Get the required action details
                    if hasattr(run, 'required_action') and hasattr(run.required_action, 'submit_tool_outputs'):
                        tool_calls = run.required_action.submit_tool_outputs.tool_calls
                        
                        print(f"Tool Calls: {len(tool_calls)}")
                        for tool_call in tool_calls:
                            print(f"  - Function: {tool_call.function.name}")
                            print(f"    Arguments: {tool_call.function.arguments}")
                            
                            # Parse arguments
                            try:
                                args = json.loads(tool_call.function.arguments)
                                print(f"    Request: {args.get('request', 'N/A')}")
                            except:
                                pass
                            
                            # Check if it matches expected
                            if tool_call.function.name == scenario['expected_tool']:
                                print(f"    ✅ Matches expected tool!")
                            else:
                                print(f"    ❌ Expected {scenario['expected_tool']}")
                    break
                    
                elif run.status == "completed":
                    print("❌ Status: COMPLETED (No tool call - just text response)")
                    
                    # Get the response
                    messages = client.agents.messages.list(thread_id=thread_id)
                    async for msg in messages:
                        if msg.role == "assistant" and msg.content:
                            for content in msg.content:
                                if hasattr(content, 'text'):
                                    print(f"Response: {content.text.value[:200]}...")
                                    break
                            break
                    break
                    
                elif run.status in ["failed", "cancelled", "expired"]:
                    print(f"❌ Status: {run.status.upper()}")
                    break
                
                print(f"Status: {run.status}, waiting... ({wait_time}s)")
            
            # Clean up
            await client.agents.threads.delete(thread_id=thread_id)
            
            # Small delay between tests
            await asyncio.sleep(0.5)
        
        print("\n" + "="*80)
        print("TOOL CALLING TEST COMPLETE")
        print("="*80)
        print("\nIf the orchestrator is returning 'requires_action' with tool calls,")
        print("then tool-based delegation is working correctly!")
        print("\nNext step: Update FastAPI to handle these tool calls by invoking")
        print("the actual specialist agents.")
    
    await credential.close()

if __name__ == "__main__":
    asyncio.run(test_tool_calling())