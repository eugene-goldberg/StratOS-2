#!/usr/bin/env python3
"""
Interactive chat with the Main Orchestrator that handles tool calls.
This demonstrates the complete flow of tool-based delegation.
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

class ToolOrchestrationClient:
    """Client for interacting with the tool-based orchestrator."""
    
    def __init__(self):
        self.settings = AzureAIAgentSettings()
        self.credential = DefaultAzureCredential()
        self.orchestrator_id = None
        self.specialist_agents = {}
        self.load_configurations()
        
    def load_configurations(self):
        """Load orchestrator and specialist agent configurations."""
        # Load orchestrator config
        orch_config_path = os.path.join(agentic_dir, "deployment_configs", "main_orchestrator_tools_deployment.json")
        if os.path.exists(orch_config_path):
            with open(orch_config_path, 'r') as f:
                config = json.load(f)
                self.orchestrator_id = config['agent_id']
                print(f"Loaded Main Orchestrator: {self.orchestrator_id}")
        
        # Load specialist agent IDs from the deployment file
        deployment_path = os.path.join(agentic_dir, "deployment_configs", "ai_project_agents_deployment.json")
        if os.path.exists(deployment_path):
            with open(deployment_path, 'r') as f:
                deployment_data = json.load(f)
                deployed_agents = deployment_data.get('deployed_agents', {})
                
                # Map agent names to lowercase for tool call matching
                for agent_name, agent_id in deployed_agents.items():
                    self.specialist_agents[agent_name.lower()] = agent_id
        
        print(f"Loaded {len(self.specialist_agents)} specialist agents")
    
    async def handle_tool_calls(self, client, tool_calls, thread_id):
        """Handle tool calls by invoking the appropriate specialist agents."""
        tool_outputs = []
        
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)
            
            print(f"\n🔧 Tool Call: {function_name}")
            print(f"   Request: {function_args.get('request', 'N/A')}")
            
            # Extract agent name from function name (e.g., "invoke_ceologagent" -> "ceologagent")
            agent_key = function_name.replace("invoke_", "")
            
            # Find the specialist agent ID
            specialist_id = self.specialist_agents.get(agent_key)
            
            if specialist_id:
                try:
                    print(f"   Invoking specialist: {agent_key} ({specialist_id})")
                    
                    # Create a new thread for the specialist agent
                    specialist_thread = await client.agents.threads.create()
                    
                    # Add the request to the specialist thread
                    await client.agents.messages.create(
                        thread_id=specialist_thread.id,
                        role="user",
                        content=function_args['request']
                    )
                    
                    # Run the specialist agent
                    specialist_run = await client.agents.runs.create(
                        thread_id=specialist_thread.id,
                        agent_id=specialist_id
                    )
                    
                    # Wait for specialist to complete
                    max_wait = 30
                    wait_time = 0
                    
                    while wait_time < max_wait:
                        await asyncio.sleep(1)
                        wait_time += 1
                        
                        specialist_run = await client.agents.runs.get(
                            thread_id=specialist_thread.id,
                            run_id=specialist_run.id
                        )
                        
                        if specialist_run.status == "completed":
                            # Get the specialist's response
                            messages = client.agents.messages.list(thread_id=specialist_thread.id)
                            
                            specialist_response = None
                            async for msg in messages:
                                if msg.role == "assistant" and msg.content:
                                    for content in msg.content:
                                        if hasattr(content, 'text'):
                                            specialist_response = content.text.value
                                            break
                                    if specialist_response:
                                        break
                            
                            if specialist_response:
                                print(f"   ✅ Specialist response received")
                                tool_outputs.append({
                                    "tool_call_id": tool_call.id,
                                    "output": specialist_response
                                })
                            else:
                                tool_outputs.append({
                                    "tool_call_id": tool_call.id,
                                    "output": "No response from specialist agent"
                                })
                            break
                            
                        elif specialist_run.status in ["failed", "cancelled", "expired"]:
                            print(f"   ❌ Specialist run failed: {specialist_run.status}")
                            tool_outputs.append({
                                "tool_call_id": tool_call.id,
                                "output": f"Specialist agent failed with status: {specialist_run.status}"
                            })
                            break
                    
                    # Clean up specialist thread
                    await client.agents.threads.delete(thread_id=specialist_thread.id)
                    
                except Exception as e:
                    print(f"   ❌ Error invoking specialist: {str(e)}")
                    tool_outputs.append({
                        "tool_call_id": tool_call.id,
                        "output": f"Error invoking specialist: {str(e)}"
                    })
            else:
                print(f"   ❌ Unknown specialist agent: {agent_key}")
                tool_outputs.append({
                    "tool_call_id": tool_call.id,
                    "output": f"Unknown specialist agent: {agent_key}"
                })
        
        return tool_outputs
    
    async def chat(self, message: str):
        """Send a message to the orchestrator and handle the complete flow."""
        if not self.orchestrator_id:
            print("❌ No orchestrator found. Please deploy first.")
            return
        
        async with AzureAIAgent.create_client(credential=self.credential, settings=self.settings) as client:
            # Create thread
            thread = await client.agents.threads.create()
            thread_id = thread.id
            
            # Add message
            await client.agents.messages.create(
                thread_id=thread_id,
                role="user",
                content=message
            )
            
            # Create run
            run = await client.agents.runs.create(
                thread_id=thread_id,
                agent_id=self.orchestrator_id
            )
            
            # Process the run
            max_wait = 60
            wait_time = 0
            
            while wait_time < max_wait:
                await asyncio.sleep(1)
                wait_time += 1
                
                run = await client.agents.runs.get(
                    thread_id=thread_id,
                    run_id=run.id
                )
                
                if run.status == "requires_action":
                    # Handle tool calls
                    print("\n🤖 Orchestrator requests tool calls...")
                    tool_calls = run.required_action.submit_tool_outputs.tool_calls
                    
                    # Process tool calls
                    tool_outputs = await self.handle_tool_calls(client, tool_calls, thread_id)
                    
                    # Submit tool outputs back to orchestrator
                    print("\n📤 Submitting results back to orchestrator...")
                    await client.agents.runs.submit_tool_outputs(
                        thread_id=thread_id,
                        run_id=run.id,
                        tool_outputs=tool_outputs
                    )
                    
                elif run.status == "completed":
                    # Get final response
                    messages = client.agents.messages.list(thread_id=thread_id)
                    
                    async for msg in messages:
                        if msg.role == "assistant" and msg.content:
                            for content in msg.content:
                                if hasattr(content, 'text'):
                                    print(f"\n💬 Orchestrator: {content.text.value}")
                                    break
                            break
                    break
                    
                elif run.status in ["failed", "cancelled", "expired"]:
                    print(f"\n❌ Run failed with status: {run.status}")
                    break
                
                if wait_time % 5 == 0:
                    print(f"Status: {run.status}, waiting... ({wait_time}s)")
            
            # Clean up
            await client.agents.threads.delete(thread_id=thread_id)
    
    async def interactive_session(self):
        """Run an interactive chat session."""
        print("\n" + "="*80)
        print("StratOS Multi-Agent System - Tool-Based Orchestration")
        print("="*80)
        print("Type 'exit' to quit\n")
        
        while True:
            try:
                user_input = input("\n👤 You: ")
                if user_input.lower() == 'exit':
                    break
                
                await self.chat(user_input)
                
            except KeyboardInterrupt:
                print("\n\nExiting...")
                break
            except Exception as e:
                print(f"\n❌ Error: {str(e)}")
        
        await self.credential.close()

async def main():
    """Main entry point."""
    client = ToolOrchestrationClient()
    await client.interactive_session()

if __name__ == "__main__":
    asyncio.run(main())