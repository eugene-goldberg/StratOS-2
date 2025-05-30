#!/usr/bin/env python3
"""
Diagnose the connection issue preventing server-side execution.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime

# Add parent directories to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.agents.models import (
    MessageRole,
    AgentThreadCreationOptions,
    ThreadMessageOptions
)

# Load environment variables
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)


def diagnose_connection():
    """Diagnose why the connection cannot be found."""
    
    print("=" * 70)
    print("CONNECTION DIAGNOSIS FOR SERVER-SIDE EXECUTION")
    print("=" * 70)
    
    agent_id = "asst_O4aSd8sNgSTafAdOqLAhWHjP"
    connection_string = os.getenv("AZURE_AI_PROJECT_CONNECTION_STRING")
    
    print(f"\n1. Environment:")
    print(f"   Agent ID: {agent_id}")
    print(f"   Connection String: {connection_string[:50]}...")
    
    # Parse connection string to understand the structure
    if "subscriptions" in connection_string:
        parts = connection_string.split("/")
        subscription_idx = parts.index("subscriptions") + 1
        rg_idx = parts.index("resourceGroups") + 1
        ws_idx = parts.index("workspaces") + 1
        
        print(f"\n2. AI Project Details:")
        print(f"   Subscription: {parts[subscription_idx]}")
        print(f"   Resource Group: {parts[rg_idx]}")
        print(f"   Workspace: {parts[ws_idx]}")
    
    # Initialize client
    credential = DefaultAzureCredential()
    project_client = AIProjectClient(
        endpoint=connection_string,
        credential=credential
    )
    
    print(f"\n3. Checking ML Workspace Connection:")
    print("   Running: az ml connection show --name NorthStarFunctionConnection")
    
    import subprocess
    result = subprocess.run([
        "az", "ml", "connection", "show",
        "--name", "NorthStarFunctionConnection",
        "--resource-group", "semantic-kernel-multi-agent-rg",
        "--workspace-name", "sk-multi-agent-project",
        "--query", "name",
        "-o", "tsv"
    ], capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"   ✅ Connection exists: {result.stdout.strip()}")
    else:
        print(f"   ❌ Connection not found")
    
    print(f"\n4. Testing Agent Execution:")
    
    try:
        # Minimal test
        thread_options = AgentThreadCreationOptions(
            messages=[
                ThreadMessageOptions(
                    role=MessageRole.USER,
                    content="Test connection"
                )
            ]
        )
        
        print("   Creating run...")
        run = project_client.agents.create_thread_and_process_run(
            agent_id=agent_id,
            thread=thread_options
        )
        
        print(f"   Run ID: {run.id}")
        print(f"   Status: {run.status}")
        
        if hasattr(run, 'last_error') and run.last_error:
            error = run.last_error
            print(f"\n5. Error Analysis:")
            print(f"   Code: {error.get('code', 'unknown')}")
            print(f"   Message: {error.get('message', 'unknown')}")
            
            if "NorthStarFunctionConnection" in str(error):
                print(f"\n6. Connection Issue Confirmed:")
                print("   The agent is trying to use the connection")
                print("   But the AI Agent Service cannot find it")
                print("\n   Possible reasons:")
                print("   - ML workspace connections are not visible to AI Agent Service")
                print("   - Connections need to be created through AI Studio UI")
                print("   - Different API endpoint for AI Project connections")
                print("   - Connection permissions/sharing not configured")
        
    except Exception as e:
        print(f"\n   ❌ Error: {e}")
    
    print(f"\n7. Recommendations:")
    print("   1. Check Azure AI Studio UI for connection management")
    print("   2. Look for AI Project-specific connection APIs")
    print("   3. Verify if connections need to be 'shared' or 'published'")
    print("   4. Check if service principal needs specific permissions")
    
    print("\n" + "=" * 70)
    print("DIAGNOSIS COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    diagnose_connection()