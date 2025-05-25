#!/usr/bin/env python3
"""
Test Azure OpenAI Assistants API directly using the OpenAI Python SDK.
"""

import os
import sys
from dotenv import load_dotenv

# Add parent directories to path
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
sys.path.insert(0, backend_dir)

# Load environment variables
env_path = os.path.join(backend_dir, '.env')
load_dotenv(env_path)

print("Testing Azure OpenAI Assistants API...")
print(f"Endpoint: https://sk-multi-agent-openai.openai.azure.com/")
print(f"API Key: {'Set' if os.getenv('AZURE_OPENAI_API_KEY') else 'Not set'}")

try:
    from openai import AzureOpenAI
    
    # Initialize the Azure OpenAI client
    client = AzureOpenAI(
        azure_endpoint="https://sk-multi-agent-openai.openai.azure.com/",
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_version="2024-05-01-preview"
    )
    
    print("\n✓ Client initialized successfully")
    
    # Try to list existing assistants
    print("\nListing existing assistants...")
    try:
        assistants = client.beta.assistants.list()
        print(f"Found {len(assistants.data)} existing assistants")
        for assistant in assistants.data:
            print(f"  - {assistant.name}: {assistant.id}")
    except Exception as e:
        print(f"Error listing assistants: {e}")
    
    # Try to create a test assistant
    print("\nCreating test assistant...")
    try:
        assistant = client.beta.assistants.create(
            name="TestAssistant",
            instructions="You are a test assistant for verifying the API works.",
            model="gpt-35-turbo"
        )
        print(f"✅ Successfully created assistant: {assistant.id}")
        print(f"   Name: {assistant.name}")
        print(f"   Model: {assistant.model}")
        
        # Try to delete the test assistant
        print("\nDeleting test assistant...")
        client.beta.assistants.delete(assistant.id)
        print("✅ Successfully deleted test assistant")
        
    except Exception as e:
        print(f"❌ Error creating assistant: {e}")
        print(f"   Error type: {type(e).__name__}")
        if hasattr(e, 'response'):
            print(f"   Response status: {e.response.status_code if hasattr(e.response, 'status_code') else 'N/A'}")
            print(f"   Response body: {e.response.text if hasattr(e.response, 'text') else 'N/A'}")
    
except ImportError:
    print("\n❌ OpenAI package not installed. Installing...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "openai"])
    print("Please run this script again after installation.")
except Exception as e:
    print(f"\n❌ Unexpected error: {e}")
    import traceback
    traceback.print_exc()