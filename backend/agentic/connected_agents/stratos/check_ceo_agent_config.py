#!/usr/bin/env python3
"""Check CEO Log Agent configuration."""

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

# CEO Log Agent ID
CEO_LOG_AGENT_ID = "asst_qOFhcSTQ8RmUmUSP7vR1frIG"

def check_agent():
    """Check CEO Log Agent configuration."""
    print("\n🔍 Checking CEO Log Agent Configuration")
    print("=" * 60)
    
    # Create client
    client = AzureOpenAI(
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
        api_key=AZURE_OPENAI_KEY,
        api_version=AZURE_OPENAI_VERSION
    )
    
    try:
        # Get assistant details
        assistant = client.beta.assistants.retrieve(CEO_LOG_AGENT_ID)
        
        print(f"ID: {assistant.id}")
        print(f"Name: {assistant.name}")
        print(f"Model: {assistant.model}")
        print(f"Created: {assistant.created_at}")
        
        print("\nTools:")
        for tool in assistant.tools:
            if tool.type == "function":
                print(f"  - Function: {tool.function.name}")
                print(f"    Description: {tool.function.description}")
                # Show parameters
                if hasattr(tool.function, 'parameters'):
                    print(f"    Parameters: {tool.function.parameters}")
            else:
                print(f"  - {tool.type}")
        
        print("\nInstructions (first 500 chars):")
        print(assistant.instructions[:500] + "...")
        
        # Check available models
        print("\n" + "=" * 60)
        print("Available Models/Deployments:")
        print("=" * 60)
        
        # Try to list models (this might not work with all Azure OpenAI deployments)
        try:
            models = client.models.list()
            for model in models.data:
                print(f"  - {model.id}")
        except:
            print("  Unable to list models - this is normal for Azure OpenAI")
            print("  Common deployment names: gpt-4, gpt-35-turbo, gpt-4-turbo")
        
    except Exception as e:
        print(f"\n❌ ERROR: {type(e).__name__}: {str(e)}")

if __name__ == "__main__":
    check_agent()