#!/usr/bin/env python3
"""
Simple demonstration of agent interaction with Azure AI Agent Service.
"""

import asyncio
import os
from dotenv import load_dotenv
from datetime import datetime

from azure.identity.aio import DefaultAzureCredential
from semantic_kernel.agents import AzureAIAgent, AzureAIAgentSettings

# Load environment
current_dir = os.path.dirname(os.path.abspath(__file__))
agentic_dir = os.path.dirname(current_dir) 
load_dotenv(os.path.join(agentic_dir, '.env'))

async def demo_agent_interaction():
    """Demonstrate agent interaction."""
    
    # Agent to test
    agent_name = "CEOLogAgent"
    agent_id = "asst_N5azTOnrhdlm4K9wC6i9OtHA"
    
    print(f"Azure AI Agent Service Demo")
    print(f"{'='*50}")
    print(f"Testing: {agent_name}")
    print(f"Agent ID: {agent_id}\n")
    
    try:
        # Create settings
        settings = AzureAIAgentSettings()
        print(f"Endpoint: {settings.endpoint}")
        print(f"Model: {settings.model_deployment_name}\n")
        
        # Create credential and client
        async with DefaultAzureCredential(exclude_interactive_browser_credential=False) as credential:
            async with AzureAIAgent.create_client(credential=credential, settings=settings) as client:
                print("✓ Connected to Azure AI Agent Service")
                
                # Get agent definition
                agent_def = await client.agents.get_agent(agent_id=agent_id)
                print(f"✓ Retrieved agent: {agent_def.name}")
                print(f"  Description: {agent_def.description}")
                
                # Create SK agent
                agent = AzureAIAgent(client=client, definition=agent_def)
                
                # Test message
                test_message = """
                Had an important board meeting today. Key decisions:
                - Approved $25M Series B funding round
                - Expanding to Asian markets in Q3
                - Hiring 50 new engineers
                Team is excited about the growth opportunities!
                """
                
                print(f"\n{'='*50}")
                print(f"User Message:")
                print(test_message.strip())
                print(f"{'='*50}\n")
                
                print(f"Agent Response:")
                print("-" * 50)
                
                # Invoke agent (it handles thread creation internally)
                response_chunks = []
                async for chunk in agent.invoke(message=test_message):
                    if hasattr(chunk, 'content') and chunk.content:
                        print(chunk.content, end="", flush=True)
                        response_chunks.append(chunk.content)
                
                if not response_chunks:
                    print("[Note: Agent returned no content. This could mean the agent is configured differently than expected.]")
                
                print("\n" + "-" * 50)
                
                print(f"\n✓ Interaction completed at {datetime.now().isoformat()}")
                
    except Exception as e:
        print(f"\n✗ Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("\nStarting agent demo...\n")
    asyncio.run(demo_agent_interaction())