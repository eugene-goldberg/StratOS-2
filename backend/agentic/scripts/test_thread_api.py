#!/usr/bin/env python3
"""Check the correct thread API"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Path setup
current_dir = os.path.dirname(os.path.abspath(__file__))
agentic_dir = os.path.dirname(current_dir)
env_path = os.path.join(agentic_dir, '.env')
load_dotenv(env_path)

from azure.identity.aio import DefaultAzureCredential
from semantic_kernel.agents import AzureAIAgent, AzureAIAgentSettings

async def main():
    settings = AzureAIAgentSettings()
    credential = DefaultAzureCredential()
    
    async with AzureAIAgent.create_client(credential=credential, settings=settings) as client:
        print("Client type:", type(client))
        print("Client attributes:", [attr for attr in dir(client) if not attr.startswith('_')])
        
        if hasattr(client, 'agents'):
            print("\nAgents attributes:", [attr for attr in dir(client.agents) if not attr.startswith('_')])
            
            if hasattr(client.agents, 'threads'):
                print("\nThreads attributes:", [attr for attr in dir(client.agents.threads) if not attr.startswith('_')])
    
    await credential.close()

if __name__ == "__main__":
    asyncio.run(main())