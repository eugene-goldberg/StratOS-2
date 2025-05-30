#!/usr/bin/env python3
"""
Test using a function tool that makes HTTP calls instead of OpenAPI tool.
This bypasses the connection management entirely.
"""

import os
import sys
import json
import requests
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Add parent directories to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.agents.models import (
    FunctionTool,
    MessageRole,
    AgentThreadCreationOptions,
    ThreadMessageOptions
)

# Load environment variables
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)


def test_function_tool():
    """Test using function tools that the agent can call."""
    
    print("=" * 70)
    print("TESTING FUNCTION TOOL APPROACH (BYPASS CONNECTION)")
    print("=" * 70)
    
    # Configuration
    agent_name = f"NorthStarFunctionTool-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    model_name = "gpt-35-turbo"
    connection_string = os.getenv("AZURE_AI_PROJECT_CONNECTION_STRING")
    
    # Define function tool that makes HTTP calls
    function_definition = {
        "name": "ExecuteNorthStarOperation",
        "description": "Execute North Star operations by calling Azure Function",
        "parameters": {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": ["managePurpose", "manageVision", "manageValues", "manageStrategicGoals", "validateAlignment", "getNorthStarSummary"],
                    "description": "The operation to perform"
                },
                "organizationId": {
                    "type": "string",
                    "description": "The organization ID"
                },
                "action": {
                    "type": "string",
                    "enum": ["get", "set", "list", "add", "remove", "create", "update", "delete"],
                    "description": "The action to perform (depends on operation)"
                },
                "purpose": {"type": "string", "description": "Organization purpose (for managePurpose)"},
                "vision": {"type": "string", "description": "Organization vision (for manageVision)"},
                "values": {"type": "array", "items": {"type": "string"}, "description": "Values to add/remove"},
                "goalId": {"type": "string", "description": "Goal ID for operations"},
                "goalName": {"type": "string", "description": "Goal name"},
                "description": {"type": "string", "description": "Goal description"},
                "targetDate": {"type": "string", "description": "Target date"},
                "elementType": {"type": "string", "description": "Element type for validation"},
                "elementContent": {"type": "string", "description": "Element content for validation"}
            },
            "required": ["operation", "organizationId"]
        }
    }
    
    # Agent instructions with embedded logic
    agent_instructions = """You are the North Star Agent using function tools.

When you receive a request, use the ExecuteNorthStarOperation function to handle it. The function will make the necessary HTTP calls.

IMPORTANT: This is a function tool, not an OpenAPI tool. You call it like a regular function and it handles the HTTP communication internally.

Available operations:
- managePurpose: Get/set organizational purpose
- manageVision: Get/set organizational vision
- manageValues: Manage core values
- manageStrategicGoals: Manage strategic goals
- validateAlignment: Check alignment with North Star
- getNorthStarSummary: Get complete North Star overview

Always include the organizationId parameter."""
    
    try:
        # Initialize client
        credential = DefaultAzureCredential()
        project_client = AIProjectClient(
            endpoint=connection_string,
            credential=credential
        )
        
        print(f"\nCreating agent: {agent_name}")
        print("Using function tools (no connection management needed)")
        
        # Create function tool using the correct format
        function_tool = FunctionTool(
            function={
                "name": function_definition["name"],
                "description": function_definition["description"],
                "parameters": function_definition["parameters"]
            }
        )
        
        # Create agent with function tool
        agent = project_client.agents.create_agent(
            model=model_name,
            name=agent_name,
            instructions=agent_instructions,
            tools=[function_tool]
        )
        
        print(f"✅ Agent created: {agent.id}")
        
        # Test execution
        print("\n" + "=" * 70)
        print("TESTING EXECUTION")
        print("=" * 70)
        
        thread_options = AgentThreadCreationOptions(
            messages=[
                ThreadMessageOptions(
                    role=MessageRole.USER,
                    content="Set the organizational purpose to 'Transform healthcare through AI innovation' for organization test-func-tool"
                )
            ]
        )
        
        print("⚡ Creating thread and run...")
        print("   (Agent will call function, function makes HTTP request)")
        
        run = project_client.agents.create_thread_and_process_run(
            agent_id=agent.id,
            thread=thread_options
        )
        
        print(f"\nRun ID: {run.id}")
        print(f"Status: {run.status}")
        
        if str(run.status) == "RunStatus.REQUIRES_ACTION":
            print("\n✅ Agent is trying to call the function!")
            print("⚠️  But we need to implement function execution")
            print("\nThis proves:")
            print("1. Function tools work without connection issues")
            print("2. Agent can identify and attempt to call functions")
            print("3. We need to implement the actual HTTP call logic")
            
            # In a real implementation, we would:
            # 1. Get the function call details from the run
            # 2. Execute the HTTP request based on parameters
            # 3. Submit the result back to the run
            
            if hasattr(run, 'required_action'):
                print(f"\nRequired action: {run.required_action}")
        
        elif str(run.status) == "RunStatus.FAILED":
            print(f"\n❌ Run failed")
            if hasattr(run, 'last_error'):
                print(f"Error: {run.last_error}")
        
        elif str(run.status) == "RunStatus.COMPLETED":
            print("\n✅ Run completed")
            print("(This would mean function execution is handled automatically)")
        
        return agent.id
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    if not os.getenv("AZURE_AI_PROJECT_CONNECTION_STRING"):
        print("Error: AZURE_AI_PROJECT_CONNECTION_STRING not set")
        exit(1)
    
    print("\nNOTE: Function tools require client-side execution of HTTP calls")
    print("This is NOT server-side execution, but it bypasses connection issues")
    print("-" * 70)
    
    agent_id = test_function_tool()
    if agent_id:
        print(f"\n🚀 Agent with function tools: {agent_id}")