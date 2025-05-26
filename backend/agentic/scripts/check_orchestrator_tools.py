#!/usr/bin/env python3
"""
Check the Main Orchestrator's tools configuration.
"""

import asyncio
import os
import sys
import json
from dotenv import load_dotenv

# Path setup
current_dir = os.path.dirname(os.path.abspath(__file__))
agentic_dir = os.path.dirname(current_dir)
env_path = os.path.join(agentic_dir, '.env')
load_dotenv(env_path)

from azure.identity.aio import DefaultAzureCredential
from semantic_kernel.agents import AzureAIAgent, AzureAIAgentSettings

async def main():
    # Load orchestrator ID
    deployment_config_path = os.path.join(agentic_dir, "deployment_configs", "main_orchestrator_deployment.json")
    with open(deployment_config_path, 'r') as f:
        config = json.load(f)
        orchestrator_id = config['agent_id']
        print(f"Orchestrator ID: {orchestrator_id}")
    
    settings = AzureAIAgentSettings()
    credential = DefaultAzureCredential()
    
    async with AzureAIAgent.create_client(credential=credential, settings=settings) as client:
        # Get the agent definition
        agent_def = await client.agents.get_agent(agent_id=orchestrator_id)
        
        print(f"\nAgent Name: {agent_def.name}")
        print(f"Model: {agent_def.model}")
        print(f"\nInstructions preview: {agent_def.instructions[:200]}...")
        print(f"\nTools configured: {len(agent_def.tools) if agent_def.tools else 0}")
        
        if agent_def.tools:
            print("\nTool details:")
            for i, tool in enumerate(agent_def.tools):
                print(f"\n{i+1}. Tool type: {tool.get('type', 'unknown')}")
                if tool.get('type') == 'connected_agent':
                    ca = tool.get('connected_agent', {})
                    print(f"   Connected Agent ID: {ca.get('id', 'N/A')}")
                    print(f"   Connected Agent Name: {ca.get('name', 'N/A')}")
                else:
                    print(f"   Details: {tool}")
    
    await credential.close()

if __name__ == "__main__":
    asyncio.run(main())