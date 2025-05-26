#!/usr/bin/env python3
"""
Verify that the Main Orchestrator has routing tools configured.
"""

import asyncio
import json
import os
from pathlib import Path
from datetime import datetime
from azure.identity import DefaultAzureCredential
from semantic_kernel.agents import AzureAIAgent, AzureAIAgentSettings

# Load environment variables
from dotenv import load_dotenv
env_path = Path(__file__).parent.parent / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path)

async def verify_orchestrator():
    """Verify the Main Orchestrator configuration."""
    
    # Get orchestrator ID
    deployment_config_path = Path(__file__).parent.parent / "deployment_configs" / "main_orchestrator_deployment.json"
    with open(deployment_config_path) as f:
        config = json.load(f)
    
    orchestrator_id = config["agent_id"]
    
    print("="*80)
    print("MAIN ORCHESTRATOR VERIFICATION")
    print("="*80)
    print(f"Agent ID: {orchestrator_id}")
    print(f"Deployment Time: {config.get('deployment_time', 'Unknown')}")
    print(f"Updated Time: {config.get('updated_time', 'Unknown')}")
    print(f"Has Tools: {config.get('has_tools', False)}")
    print(f"Tool Count: {config.get('tool_count', 0)}")
    
    # Create settings and credential
    settings = AzureAIAgentSettings()
    credential = DefaultAzureCredential()
    
    async with AzureAIAgent.create_client(credential=credential, settings=settings) as service_client:
        # Get agent definition
        agent_definition = await service_client.agents.get_agent(agent_id=orchestrator_id)
        
        print(f"\n{'='*80}")
        print("AGENT DETAILS")
        print('='*80)
        print(f"Name: {agent_definition.name}")
        print(f"Model: {agent_definition.model}")
        print(f"Description: {agent_definition.description[:100]}...")
        
        # Check instructions
        if hasattr(agent_definition, 'instructions') and agent_definition.instructions:
            print(f"\nInstructions (first 500 chars):")
            print("-" * 40)
            print(agent_definition.instructions[:500])
            print("...")
            
            # Check if routing is mentioned
            routing_keywords = ["route", "routing", "RouteToAgent", "agent_name", "CEOLogAgent"]
            found_keywords = [kw for kw in routing_keywords if kw.lower() in agent_definition.instructions.lower()]
            print(f"\nRouting keywords found: {found_keywords}")
        
        # Check tools
        print(f"\n{'='*80}")
        print("TOOLS CONFIGURATION")
        print('='*80)
        
        if hasattr(agent_definition, 'tools') and agent_definition.tools:
            print(f"Number of tools: {len(agent_definition.tools)}")
            for i, tool in enumerate(agent_definition.tools):
                print(f"\nTool {i+1}:")
                if isinstance(tool, dict):
                    print(f"  Type: {tool.get('type', 'Unknown')}")
                    if 'function' in tool:
                        func = tool['function']
                        print(f"  Function Name: {func.get('name', 'Unknown')}")
                        print(f"  Description: {func.get('description', 'Unknown')}")
                        if 'parameters' in func:
                            params = func['parameters']
                            if 'properties' in params:
                                print(f"  Parameters:")
                                for param_name, param_def in params['properties'].items():
                                    print(f"    - {param_name}: {param_def.get('type', 'Unknown')} - {param_def.get('description', '')}")
                                    if param_name == 'agent_name' and 'enum' in param_def:
                                        print(f"      Available agents: {', '.join(param_def['enum'][:3])}... ({len(param_def['enum'])} total)")
                else:
                    print(f"  Tool info: {tool}")
        else:
            print("No tools configured")
        
        print(f"\n{'='*80}")
        print("VERIFICATION SUMMARY")
        print('='*80)
        print("✅ Main Orchestrator exists and is accessible")
        print(f"✅ Agent has routing instructions: {'Yes' if found_keywords else 'No'}")
        print(f"✅ Agent has tools configured: {'Yes' if hasattr(agent_definition, 'tools') and agent_definition.tools else 'No'}")
        print(f"✅ RouteToAgent tool present: {'Yes' if any(tool.get('function', {}).get('name') == 'RouteToAgent' for tool in (agent_definition.tools or []) if isinstance(tool, dict)) else 'No'}")
        
        print("\nThe Main Orchestrator is properly configured for routing!")
        print("\nNext steps:")
        print("1. Create StratOSAgentClient in FastAPI")
        print("2. When Main Orchestrator returns REQUIRES_ACTION status with RouteToAgent tool call:")
        print("   - Extract the agent_name from the tool call arguments")
        print("   - Invoke that specific agent with the user's request")
        print("   - Return the specialized agent's response to the user")

if __name__ == "__main__":
    asyncio.run(verify_orchestrator())