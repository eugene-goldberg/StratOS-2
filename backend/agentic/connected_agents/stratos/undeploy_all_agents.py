#!/usr/bin/env python3
"""
Undeploy all agents from both Azure AI Agent Service and Azure OpenAI.
"""

import os
import json
from datetime import datetime
from openai import AzureOpenAI
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from dotenv import load_dotenv

# Load environment
load_dotenv()
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

# Azure OpenAI configuration
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "https://sk-multi-agent-openai.openai.azure.com/")
AZURE_OPENAI_KEY = os.getenv("AZURE_OPENAI_API_KEY", "b77c5b137db6465dabdbc34adb136e2c")
AZURE_OPENAI_VERSION = "2024-02-15-preview"

# Azure AI Project configuration
AZURE_AI_PROJECT_CONNECTION_STRING = os.getenv("AZURE_AI_PROJECT_CONNECTION_STRING")

def undeploy_openai_agents():
    """Undeploy agents from Azure OpenAI."""
    print("\n🔍 Undeploying agents from Azure OpenAI")
    print("=" * 60)
    
    # Create client
    client = AzureOpenAI(
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
        api_key=AZURE_OPENAI_KEY,
        api_version=AZURE_OPENAI_VERSION
    )
    
    deleted_count = 0
    ceo_agents_deleted = []
    
    try:
        # List all assistants
        assistants = client.beta.assistants.list()
        
        print(f"Found {len(assistants.data)} assistants")
        
        for assistant in assistants.data:
            print(f"\nDeleting: {assistant.name} (ID: {assistant.id})")
            try:
                client.beta.assistants.delete(assistant.id)
                deleted_count += 1
                
                # Track CEO agents
                if "ceo" in assistant.name.lower():
                    ceo_agents_deleted.append({
                        "id": assistant.id,
                        "name": assistant.name
                    })
                
                print(f"  ✅ Deleted successfully")
            except Exception as e:
                print(f"  ❌ Failed to delete: {str(e)}")
        
        print(f"\n✅ Deleted {deleted_count} agents from Azure OpenAI")
        
        if ceo_agents_deleted:
            print(f"\nCEO Agents deleted:")
            for agent in ceo_agents_deleted:
                print(f"  - {agent['name']} (ID: {agent['id']})")
        
    except Exception as e:
        print(f"\n❌ ERROR: {type(e).__name__}: {str(e)}")
    
    return deleted_count

def undeploy_azure_ai_agents():
    """Undeploy agents from Azure AI Agent Service."""
    print("\n\n🔍 Undeploying agents from Azure AI Agent Service")
    print("=" * 60)
    
    if not AZURE_AI_PROJECT_CONNECTION_STRING:
        print("❌ AZURE_AI_PROJECT_CONNECTION_STRING not configured")
        return 0
    
    deleted_count = 0
    
    try:
        # Create client
        credential = DefaultAzureCredential()
        client = AIProjectClient(
            endpoint=AZURE_AI_PROJECT_CONNECTION_STRING,
            credential=credential
        )
        
        # List all agents
        print("Listing agents...")
        try:
            # Try to list agents - this might not be available in all deployments
            agents_list = client.agents.list_agents()
            agents = list(agents_list)
            
            print(f"Found {len(agents)} agents")
            
            for agent in agents:
                print(f"\nDeleting: {agent.name} (ID: {agent.id})")
                try:
                    client.agents.delete_agent(agent.id)
                    deleted_count += 1
                    print(f"  ✅ Deleted successfully")
                except Exception as e:
                    print(f"  ❌ Failed to delete: {str(e)}")
        except AttributeError:
            print("  ⚠️  Azure AI Agent Service API not available or different version")
            print("  Note: Agents deployed to Azure AI Agent Service may need to be deleted via Azure Portal")
        
        print(f"\n✅ Deleted {deleted_count} agents from Azure AI Agent Service")
        
    except Exception as e:
        print(f"\n❌ ERROR: {type(e).__name__}: {str(e)}")
    
    return deleted_count

def cleanup_deployment_files():
    """Clean up deployment info files."""
    print("\n\n🧹 Cleaning up deployment files")
    print("=" * 60)
    
    files_to_clean = [
        "deployment_info.json",
        "ceo_deployment_info.json",
        "stratos_deployment_info.json"
    ]
    
    for filename in files_to_clean:
        filepath = os.path.join(os.path.dirname(__file__), filename)
        if os.path.exists(filepath):
            try:
                # Backup the file first
                backup_name = f"{filename}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                with open(filepath, 'r') as f:
                    content = json.load(f)
                with open(os.path.join(os.path.dirname(__file__), backup_name), 'w') as f:
                    json.dump(content, f, indent=2)
                
                # Clear the file
                with open(filepath, 'w') as f:
                    json.dump({}, f, indent=2)
                
                print(f"  ✅ Cleared {filename} (backup: {backup_name})")
            except Exception as e:
                print(f"  ❌ Failed to clean {filename}: {str(e)}")
        else:
            print(f"  ⚠️  {filename} not found")

def main():
    """Main undeployment process."""
    print("\n🚨 UNDEPLOYING ALL AGENTS")
    print("=" * 60)
    print("This will delete all agents from:")
    print("  1. Azure OpenAI Service")
    print("  2. Azure AI Agent Service")
    print("  3. Clear deployment info files")
    print("=" * 60)
    
    response = input("\nAre you sure you want to continue? (yes/no): ")
    if response.lower() != "yes":
        print("❌ Undeployment cancelled")
        return
    
    # Undeploy from Azure OpenAI
    openai_count = undeploy_openai_agents()
    
    # Undeploy from Azure AI Agent Service
    azure_ai_count = undeploy_azure_ai_agents()
    
    # Clean up deployment files
    cleanup_deployment_files()
    
    # Summary
    print("\n\n" + "=" * 60)
    print("UNDEPLOYMENT COMPLETE")
    print("=" * 60)
    print(f"Azure OpenAI agents deleted: {openai_count}")
    print(f"Azure AI agents deleted: {azure_ai_count}")
    print(f"Total agents deleted: {openai_count + azure_ai_count}")
    print("\n✅ All agents have been undeployed")

if __name__ == "__main__":
    main()