#!/usr/bin/env python3
"""List all assistants/agents in Azure OpenAI."""

import os
from openai import AzureOpenAI
from dotenv import load_dotenv

# Load environment
load_dotenv()
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

# Azure OpenAI configuration
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "https://sk-multi-agent-openai.openai.azure.com/")
AZURE_OPENAI_KEY = os.getenv("AZURE_OPENAI_API_KEY", "b77c5b137db6465dabdbc34adb136e2c")
AZURE_OPENAI_VERSION = "2024-02-15-preview"

def list_agents():
    """List all agents."""
    print("\n🔍 Listing all Azure OpenAI Assistants")
    print("=" * 60)
    
    # Create client
    client = AzureOpenAI(
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
        api_key=AZURE_OPENAI_KEY,
        api_version=AZURE_OPENAI_VERSION
    )
    
    try:
        # List assistants
        assistants = client.beta.assistants.list()
        
        ceo_agents = []
        for assistant in assistants.data:
            print(f"\nID: {assistant.id}")
            print(f"Name: {assistant.name}")
            print(f"Model: {assistant.model}")
            print(f"Created: {assistant.created_at}")
            
            # Check if it's a CEO Log agent
            if "ceo" in assistant.name.lower():
                ceo_agents.append(assistant)
            
            # Show tools
            if assistant.tools:
                print("Tools:")
                for tool in assistant.tools:
                    if tool.type == "function":
                        print(f"  - Function: {tool.function.name}")
                    else:
                        print(f"  - {tool.type}")
        
        print("\n" + "=" * 60)
        print(f"Total assistants: {len(assistants.data)}")
        
        if ceo_agents:
            print(f"\n🎯 Found {len(ceo_agents)} CEO Log Agent(s):")
            for agent in ceo_agents:
                print(f"  - {agent.name} (ID: {agent.id})")
        else:
            print("\n❌ No CEO Log agents found")
        
    except Exception as e:
        print(f"\n❌ ERROR: {type(e).__name__}: {str(e)}")

if __name__ == "__main__":
    list_agents()