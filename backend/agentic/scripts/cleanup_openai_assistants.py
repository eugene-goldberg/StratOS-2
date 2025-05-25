#!/usr/bin/env python3
"""
Clean up the incorrectly deployed Azure OpenAI Assistants.
These should have been deployed to Azure AI Agent Service instead.
"""

import os
import sys
import json
from dotenv import load_dotenv

# Add parent directories to path
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
sys.path.insert(0, backend_dir)

# Load environment variables
env_path = os.path.join(backend_dir, '.env')
load_dotenv(env_path)

print("===== Cleaning up incorrectly deployed Azure OpenAI Assistants =====")

try:
    from openai import AzureOpenAI
    
    # Initialize the Azure OpenAI client
    client = AzureOpenAI(
        azure_endpoint="https://sk-multi-agent-openai.openai.azure.com/",
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_version="2024-05-01-preview"
    )
    
    # Load the deployment info
    deployment_file = os.path.join(backend_dir, "deployment_configs", "stratos_assistants_deployment.json")
    if os.path.exists(deployment_file):
        with open(deployment_file, "r") as f:
            deployment_info = json.load(f)
        
        print(f"\nFound {len(deployment_info['deployed_agents'])} agents to clean up")
        
        # Delete each assistant
        for name, assistant_id in deployment_info['deployed_agents'].items():
            try:
                print(f"Deleting {name} ({assistant_id})...", end=" ")
                client.beta.assistants.delete(assistant_id)
                print("✓")
            except Exception as e:
                print(f"✗ Error: {e}")
        
        # Rename the deployment file to indicate it's been cleaned up
        import shutil
        backup_file = deployment_file.replace(".json", "_DELETED.json")
        shutil.move(deployment_file, backup_file)
        print(f"\n✓ Deployment file moved to: {os.path.basename(backup_file)}")
    else:
        print("No deployment file found. Listing all assistants...")
        
        # List and offer to delete all assistants
        assistants = client.beta.assistants.list()
        if assistants.data:
            print(f"\nFound {len(assistants.data)} assistants:")
            for assistant in assistants.data:
                print(f"  - {assistant.name}: {assistant.id}")
            
            response = input("\nDelete all assistants? (yes/no): ")
            if response.lower() == "yes":
                for assistant in assistants.data:
                    try:
                        print(f"Deleting {assistant.name}...", end=" ")
                        client.beta.assistants.delete(assistant.id)
                        print("✓")
                    except Exception as e:
                        print(f"✗ Error: {e}")
        else:
            print("No assistants found.")
    
    print("\n✓ Cleanup complete")
    print("\nIMPORTANT: These agents should be deployed to Azure AI Agent Service")
    print("within an AI Project, NOT as Azure OpenAI Assistants.")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()