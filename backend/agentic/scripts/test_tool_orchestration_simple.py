#!/usr/bin/env python3
"""
Simple test of the complete tool orchestration flow.
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
    print("TOOL ORCHESTRATION FLOW TEST")
    print("=" * 80)
    print(f"Main Orchestrator: {orchestrator_id}")
    print(f"CEO Log Agent: {specialist_agents['CEOLogAgent']}")
    print()
    
    settings = AzureAIAgentSettings()
    credential = DefaultAzureCredential()
    
    async with AzureAIAgent.create_client(credential=credential, settings=settings) as client:
        # Create thread
        thread = await client.agents.threads.create()
        thread_id = thread.id
        
        # Test message
        test_message = "I need to record my thoughts about the market downturn"
        print(f"User: {test_message}")
        
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
        
        # Wait for tool call
        while True:
            await asyncio.sleep(1)
            run = await client.agents.runs.get(
                thread_id=thread_id,
                run_id=run.id
            )
            
            if run.status == "requires_action":
                print("\n✅ Orchestrator requests tool call!")
                
                # Get tool call details
                tool_calls = run.required_action.submit_tool_outputs.tool_calls
                tool_call = tool_calls[0]
                
                print(f"Function: {tool_call.function.name}")
                args = json.loads(tool_call.function.arguments)
                print(f"Arguments: {args}")
                
                # Simulate CEO Log Agent response
                print("\n📞 Calling CEO Log Agent...")
                print("(In real implementation, this would invoke the actual agent)")
                
                # Mock response
                ceo_response = {
                    "entry_id": "log-12345",
                    "summary": "CEO expressed concerns about market downturn impact on Q4 revenue",
                    "tags": ["market", "strategy", "Q4", "risk"],
                    "insights": [
                        "Market volatility may affect Q4 projections",
                        "Need to reassess budget allocations",
                        "Consider defensive strategies"
                    ]
                }
                
                # Submit tool output
                print("\n📤 Submitting tool output to orchestrator...")
                await client.agents.runs.submit_tool_outputs(
                    thread_id=thread_id,
                    run_id=run.id,
                    tool_outputs=[{
                        "tool_call_id": tool_call.id,
                        "output": json.dumps(ceo_response)
                    }]
                )
                
            elif run.status == "completed":
                print("\n✅ Orchestration complete!")
                
                # Get final response
                messages = client.agents.messages.list(thread_id=thread_id)
                async for msg in messages:
                    if msg.role == "assistant" and msg.content:
                        for content in msg.content:
                            if hasattr(content, 'text'):
                                print(f"\nOrchestrator Final Response:")
                                print("-" * 40)
                                print(content.text.value)
                                break
                        break
                break
                
            elif run.status in ["failed", "cancelled", "expired"]:
                print(f"\n❌ Run failed: {run.status}")
                break
        
        # Clean up
        await client.agents.threads.delete(thread_id=thread_id)
    
    await credential.close()
    
    print("\n" + "=" * 80)
    print("This demonstrates the complete flow:")
    print("1. User sends request to orchestrator")
    print("2. Orchestrator returns tool call (requires_action)")
    print("3. Client invokes specialist agent")
    print("4. Client submits result back to orchestrator")
    print("5. Orchestrator provides final response")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(main())