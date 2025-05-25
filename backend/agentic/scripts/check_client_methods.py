#!/usr/bin/env python3
"""
Check available methods on AIProjectClient.
"""

import asyncio
import os
from dotenv import load_dotenv

from azure.identity.aio import DefaultAzureCredential
from semantic_kernel.agents import AzureAIAgent, AzureAIAgentSettings

# Load environment
current_dir = os.path.dirname(os.path.abspath(__file__))
agentic_dir = os.path.dirname(current_dir) 
load_dotenv(os.path.join(agentic_dir, '.env'))

async def check_client():
    """Check client methods."""
    
    try:
        # Create settings
        settings = AzureAIAgentSettings()
        
        # Create credential and client
        async with DefaultAzureCredential(exclude_interactive_browser_credential=False) as credential:
            async with AzureAIAgent.create_client(credential=credential, settings=settings) as client:
                print(f"Client type: {type(client).__name__}")
                print(f"Client module: {type(client).__module__}")
                
                print("\nAvailable attributes:")
                for attr in sorted(dir(client)):
                    if not attr.startswith('_'):
                        print(f"  - {attr}")
                        
                # Check agents client
                print("\nAgents client methods:")
                agents_client = client.agents
                for attr in sorted(dir(agents_client)):
                    if not attr.startswith('_'):
                        print(f"  - {attr}")
                        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check_client())