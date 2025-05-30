#!/usr/bin/env python3
"""
Test server-side execution using connection context approach.
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

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


def test_with_connections():
    """Test providing connections in a different way."""
    
    print("=" * 70)
    print("TESTING SERVER-SIDE EXECUTION WITH CONNECTION CONTEXT")
    print("=" * 70)
    
    agent_id = "asst_O4aSd8sNgSTafAdOqLAhWHjP"
    connection_string = os.getenv("AZURE_AI_PROJECT_CONNECTION_STRING")
    
    # Initialize client
    credential = DefaultAzureCredential()
    project_client = AIProjectClient(
        endpoint=connection_string,
        credential=credential
    )
    
    print(f"Agent ID: {agent_id}")
    
    try:
        # First, let's check what the agent looks like
        agent = project_client.agents.get_agent(agent_id)
        print(f"\nAgent Name: {agent.name}")
        print(f"Agent Model: {agent.model}")
        
        if hasattr(agent, 'tools') and agent.tools:
            print(f"\nAgent Tools ({len(agent.tools)}):")
            for i, tool in enumerate(agent.tools):
                print(f"\nTool {i+1}:")
                print(f"  Type: {tool.get('type', 'unknown')}")
                if 'openapi' in str(tool).lower():
                    print("  ✅ OpenAPI tool detected")
                print(f"  Details: {str(tool)[:500]}...")
        
        # Create simple test message
        message = "What is the current organizational purpose for test-org-123?"
        
        print(f"\n\nTesting simple query: {message}")
        print("-" * 70)
        
        # Try the simplest approach - let the agent handle everything
        thread_options = AgentThreadCreationOptions(
            messages=[
                ThreadMessageOptions(
                    role=MessageRole.USER,
                    content=message
                )
            ]
        )
        
        print("\n⚡ Creating thread and run...")
        
        # Let's try the direct approach again with more debugging
        print("\n🚀 Creating thread and run with connections...")
        
        # Check if we can pass connections as environment context
        
        # Try setting connection in environment (some SDKs use this)
        os.environ["AZURE_AI_CONNECTIONS_NORTHSTARFUNCTIONCONNECTION"] = json.dumps({
            "connection_id": "NorthStarFunctionConnection",
            "endpoint": "https://stratos-north-star-v2.azurewebsites.net",
            "key": "fRvKUW-I0NseHY8728jcJtx6E7rxdvKUrK2pBiLNFEGBAzFuVfQ7jw=="
        })
        
        # Create the run directly
        run = project_client.agents.create_thread_and_process_run(
            agent_id=agent_id,
            thread=thread_options
        )
        
        print(f"Run created: {run.id}")
        print(f"Status: {run.status}")
        
        print(f"\n\nFinal status: {run.status}")
        
        if str(run.status) == "RunStatus.FAILED":
            if hasattr(run, 'last_error') and run.last_error:
                print(f"\n❌ Error: {run.last_error}")
            
            # Check if it's still the connection error
            if "NorthStarFunctionConnection" in str(run.last_error):
                print("\n⚠️  Connection issue persists")
                print("\nPossible solutions:")
                print("1. The connection might need to be in a specific format")
                print("2. The agent might need access granted to the connection")
                print("3. The connection might need to be created in the AI Project, not just ML workspace")
        
        elif str(run.status) == "RunStatus.COMPLETED":
            print("\n✅ SUCCESS! Server-side execution completed!")
            
            # Get the response
            messages = agents_client.list_messages(thread_id=thread.id)
            for msg in messages:
                if msg.role == MessageRole.ASSISTANT:
                    print(f"\nAgent Response:")
                    for content in msg.content:
                        if hasattr(content, 'text') and hasattr(content.text, 'value'):
                            print(content.text.value)
                    break
        
        return run
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    if not os.getenv("AZURE_AI_PROJECT_CONNECTION_STRING"):
        print("Error: AZURE_AI_PROJECT_CONNECTION_STRING not set")
        exit(1)
    
    result = test_with_connections()