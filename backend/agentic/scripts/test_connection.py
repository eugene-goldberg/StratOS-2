#!/usr/bin/env python3
"""
Simple test script to verify connection to deployed agents.
"""

import os
import sys
import asyncio
import json
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential, get_bearer_token_provider

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

async def test_connection():
    """Test basic connection to Azure AI Agent Service."""
    print("Testing connection to Azure AI Agent Service...")
    
    # Load configuration
    endpoint = os.getenv("AZURE_AI_AGENT_ENDPOINT")
    api_version = os.getenv("AZURE_AI_AGENT_API_VERSION", "2024-12-01-preview")
    
    print(f"Endpoint: {endpoint}")
    print(f"API Version: {api_version}")
    
    # Load agent configurations
    config_path = os.path.join(
        os.path.dirname(__file__), 
        '..', 
        'deployment_configs', 
        'ai_project_agents_deployment.json'
    )
    
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            data = json.load(f)
            agents = data.get('deployed_agents', {})
            print(f"\nFound {len(agents)} deployed agents:")
            for name in sorted(agents.keys()):
                print(f"  - {name}: {agents[name]}")
    else:
        print("No deployment configuration found!")
        
    # Test authentication
    try:
        credential = DefaultAzureCredential()
        token_provider = get_bearer_token_provider(
            credential, 
            "https://cognitiveservices.azure.com/.default"
        )
        print("\nAuthentication configured successfully")
        
        # Try to get a token
        token = token_provider()
        print(f"Token provider configured successfully")
        
    except Exception as e:
        print(f"\nAuthentication error: {e}")
        
    print("\nNote: Full agent interaction requires the semantic-kernel library.")
    print("This test verifies configuration and authentication only.")

if __name__ == "__main__":
    asyncio.run(test_connection())