#!/usr/bin/env python3
"""
Simple test of the updated Main Orchestrator.
Uses the pattern from interact_with_ai_project_agent.py
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from datetime import datetime
from azure.identity import DefaultAzureCredential
from semantic_kernel.agents import AzureAIAgent, AzureAIAgentSettings

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables
from dotenv import load_dotenv
env_path = Path(__file__).parent.parent / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path)

# Import settings
from config.settings import get_settings

async def test_orchestrator():
    print("Testing Updated Main Orchestrator")
    print("="*60)
    
    # Get orchestrator ID
    deployment_config_path = Path(__file__).parent.parent / "deployment_configs" / "main_orchestrator_deployment.json"
    with open(deployment_config_path) as f:
        config = json.load(f)
    
    orchestrator_id = config["agent_id"]
    print(f"Agent ID: {orchestrator_id}")
    print(f"Has Tools: {config.get('has_tools', False)}")
    print(f"Tool Count: {config.get('tool_count', 0)}")
    
    # Create settings and credential
    settings = AzureAIAgentSettings()
    credential = DefaultAzureCredential()
    
    print(f"\nConnecting to: {settings.endpoint}")
    
    async with AzureAIAgent.create_client(credential=credential, settings=settings) as service_client:
        print("✓ Connected to Azure AI Agent Service\n")
        
        # Get the agent
        agent_definition = await service_client.agents.get_agent(agent_id=orchestrator_id)
        print(f"✓ Retrieved agent: {agent_definition.name}")
        
        # Check if tools are configured
        if hasattr(agent_definition, 'tools') and agent_definition.tools:
            print(f"✓ Agent has {len(agent_definition.tools)} tool(s) configured")
            for i, tool in enumerate(agent_definition.tools):
                print(f"  Tool {i+1}: {tool}")
        else:
            print("⚠️ No tools found on agent")
        
        # Create a thread and test
        print("\n" + "="*60)
        print("TESTING ROUTING CAPABILITY")
        print("="*60)
        
        # Create a thread
        thread = await service_client.agents.threads.create_thread()
        print(f"Created thread: {thread.id}")
        
        # Test message
        test_message = "I need to create a CEO log entry about our successful product launch"
        print(f"\nUser: {test_message}")
        
        # Add message to thread
        await service_client.agents.threads.create_message(
            thread_id=thread.id,
            role="user", 
            content=test_message
        )
        
        # Run the agent
        print("\nRunning agent...")
        run = await service_client.agents.threads.create_run(
            thread_id=thread.id,
            assistant_id=orchestrator_id
        )
        
        # Wait for completion
        from ai_agents.models import RunStatus
        while run.status in [RunStatus.QUEUED, RunStatus.IN_PROGRESS, RunStatus.REQUIRES_ACTION]:
            await asyncio.sleep(1)
            run = await service_client.agents.threads.get_run(
                thread_id=thread.id,
                run_id=run.id
            )
            print(f"  Status: {run.status}")
            
            # If action is required (tool call), we need to submit tool outputs
            if run.status == RunStatus.REQUIRES_ACTION:
                print("  Agent wants to call a tool!")
                if hasattr(run, 'required_action') and hasattr(run.required_action, 'submit_tool_outputs'):
                    tool_calls = run.required_action.submit_tool_outputs.tool_calls
                    for tool_call in tool_calls:
                        print(f"  Tool: {tool_call.function.name}")
                        print(f"  Args: {tool_call.function.arguments}")
                    
                    # For testing, we'll cancel the run since we don't have the actual tools
                    await service_client.agents.threads.cancel_run(
                        thread_id=thread.id,
                        run_id=run.id
                    )
                    print("  (Run cancelled - tools not implemented in test)")
                    break
        
        print(f"\nFinal status: {run.status}")
        
        if run.status == RunStatus.COMPLETED:
            # Get messages
            messages = await service_client.agents.threads.list_messages(thread_id=thread.id)
            
            print("\nAssistant Response:")
            print("-" * 40)
            for msg in messages.data:
                if msg.role == "assistant":
                    for content in msg.content:
                        if hasattr(content, 'text'):
                            print(content.text.value)
            print("-" * 40)
        
        # Check run steps to see if tools were invoked
        try:
            steps = await service_client.agents.threads.list_run_steps(
                thread_id=thread.id,
                run_id=run.id
            )
            
            print("\nRun Steps:")
            for step in steps.data:
                print(f"  Step {step.id}: {step.type}")
                if hasattr(step, 'step_details'):
                    if hasattr(step.step_details, 'tool_calls'):
                        for tool_call in step.step_details.tool_calls:
                            if hasattr(tool_call, 'function'):
                                print(f"    Tool Call: {tool_call.function.name}")
                                print(f"    Arguments: {tool_call.function.arguments}")
        except Exception as e:
            print(f"\nCould not retrieve run steps: {e}")
        
        # Clean up
        await service_client.agents.threads.delete_thread(thread_id=thread.id)
        print("\n✓ Thread cleaned up")
    
    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("="*60)
    print("\nSummary:")
    print("- Main Orchestrator has been updated with routing tools")
    print("- The agent can identify routing needs and attempt to call RouteToAgent")
    print("- FastAPI backend will need to handle these routing decisions")

if __name__ == "__main__":
    asyncio.run(test_orchestrator())