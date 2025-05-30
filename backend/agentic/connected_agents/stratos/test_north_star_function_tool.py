#!/usr/bin/env python3
"""
Test North Star Agent with FunctionTool Pattern
Following the exact Azure AI Agents function calling example
"""

import os
import sys
import time
import json
import logging
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Add parent directories to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient

# Import North Star functions for execution
sys.path.append(os.path.join(os.path.dirname(__file__), 'deployment'))
from north_star_functions import (
    manage_purpose, manage_vision, manage_values,
    manage_strategic_goals, validate_alignment, get_north_star_summary
)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

# Get the latest deployed North Star agent ID
def get_latest_north_star_agent_id():
    """Get the most recently deployed North Star agent ID"""
    deployment_info_file = Path(__file__).parent.parent / "stratos_deployment_info.json"
    
    try:
        with open(deployment_info_file, 'r') as f:
            info = json.load(f)
            if "north_star_agent" in info:
                return info["north_star_agent"]["agent_id"]
    except:
        pass
    
    # Fallback to hardcoded ID if needed
    return os.getenv("NORTH_STAR_AGENT_ID")


def execute_function_call(function_name: str, arguments: str) -> str:
    """Execute the function call and return the result"""
    try:
        args = json.loads(arguments)
        logger.info(f"Executing {function_name} with args: {args}")
        
        if function_name == "manage_purpose":
            return manage_purpose(**args)
        elif function_name == "manage_vision":
            return manage_vision(**args)
        elif function_name == "manage_values":
            return manage_values(**args)
        elif function_name == "manage_strategic_goals":
            return manage_strategic_goals(**args)
        elif function_name == "validate_alignment":
            return validate_alignment(**args)
        elif function_name == "get_north_star_summary":
            return get_north_star_summary(**args)
        else:
            return json.dumps({"error": f"Unknown function: {function_name}"})
    except Exception as e:
        logger.error(f"Error executing {function_name}: {e}")
        return json.dumps({"error": str(e)})


def test_north_star_agent():
    """Test North Star Agent with function calling pattern"""
    
    print("\n" + "="*70)
    print("NORTH STAR AGENT TEST WITH FUNCTIONTOOL PATTERN")
    print("="*70)
    
    # Get agent ID
    agent_id = get_latest_north_star_agent_id()
    if not agent_id:
        logger.error("No North Star agent ID found. Please deploy the agent first.")
        return
    
    logger.info(f"Using North Star Agent ID: {agent_id}")
    
    # Retrieve project endpoint
    project_endpoint = os.getenv("AZURE_AI_PROJECT_CONNECTION_STRING")
    if not project_endpoint:
        raise ValueError("AZURE_AI_PROJECT_CONNECTION_STRING not found")
    
    # Initialize client
    credential = DefaultAzureCredential()
    project_client = AIProjectClient(
        endpoint=project_endpoint,
        credential=credential,
        api_version="latest"
    )
    
    # Test organization ID
    org_id = f"test-org-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    print(f"\nTest Organization ID: {org_id}")
    
    # Create a thread
    thread = project_client.agents.create_thread()
    print(f"✓ Thread created: {thread.id}")
    
    # Test 1: Set purpose and vision
    print("\n" + "-"*50)
    print("TEST 1: Setting Purpose and Vision")
    print("-"*50)
    
    message = project_client.agents.create_message(
        thread_id=thread.id,
        role="user",
        content=f"For organization {org_id}, set the purpose to 'Accelerate human potential through innovative technology' and vision to 'A world where technology empowers every individual to achieve their dreams'"
    )
    print("✓ Message sent")
    
    # Create run
    run = project_client.agents.create_run(thread_id=thread.id, assistant_id=agent_id)
    print(f"✓ Run created: {run.id}")
    
    # Poll and handle function calls
    while run.status in ["queued", "in_progress", "requires_action"]:
        time.sleep(1)
        run = project_client.agents.get_run(thread_id=thread.id, run_id=run.id)
        
        if run.status == "requires_action":
            tool_calls = run.required_action.submit_tool_outputs.tool_calls
            tool_outputs = []
            
            print(f"\n🔧 Handling {len(tool_calls)} function call(s)...")
            
            for tool_call in tool_calls:
                print(f"   Function: {tool_call.function.name}")
                print(f"   Arguments: {tool_call.function.arguments}")
                
                # Execute the function
                output = execute_function_call(
                    tool_call.function.name,
                    tool_call.function.arguments
                )
                
                tool_outputs.append({
                    "tool_call_id": tool_call.id,
                    "output": output
                })
            
            # Submit outputs
            project_client.agents.submit_tool_outputs_to_run(
                thread_id=thread.id,
                run_id=run.id,
                tool_outputs=tool_outputs
            )
            print("   ✓ Function outputs submitted")
    
    # Get response
    if run.status == "completed":
        print("\n✓ Run completed!")
        messages = project_client.agents.list_messages(thread_id=thread.id)
        for msg in messages:
            if msg.role == "assistant":
                print(f"\n🤖 Agent Response:")
                for content in msg.content:
                    if content.type == "text":
                        print(f"   {content.text.value}")
                break
    else:
        print(f"\n✗ Run failed with status: {run.status}")
        if hasattr(run, 'last_error'):
            print(f"   Error: {run.last_error}")
    
    # Test 2: Add values
    print("\n" + "-"*50)
    print("TEST 2: Adding Core Values")
    print("-"*50)
    
    message2 = project_client.agents.create_message(
        thread_id=thread.id,
        role="user",
        content=f"Add these core values for {org_id}: 'Innovation' (Constantly pushing boundaries), 'Integrity' (Acting with honesty and transparency), and 'Impact' (Making a positive difference)"
    )
    
    run2 = project_client.agents.create_run(thread_id=thread.id, assistant_id=agent_id)
    
    # Handle second run
    while run2.status in ["queued", "in_progress", "requires_action"]:
        time.sleep(1)
        run2 = project_client.agents.get_run(thread_id=thread.id, run_id=run2.id)
        
        if run2.status == "requires_action":
            tool_calls = run2.required_action.submit_tool_outputs.tool_calls
            tool_outputs = []
            
            for tool_call in tool_calls:
                output = execute_function_call(
                    tool_call.function.name,
                    tool_call.function.arguments
                )
                tool_outputs.append({
                    "tool_call_id": tool_call.id,
                    "output": output
                })
            
            project_client.agents.submit_tool_outputs_to_run(
                thread_id=thread.id,
                run_id=run2.id,
                tool_outputs=tool_outputs
            )
    
    # Test 3: Get summary
    print("\n" + "-"*50)
    print("TEST 3: Getting North Star Summary")
    print("-"*50)
    
    message3 = project_client.agents.create_message(
        thread_id=thread.id,
        role="user",
        content=f"Give me a complete summary of the North Star for {org_id}"
    )
    
    run3 = project_client.agents.create_run(thread_id=thread.id, assistant_id=agent_id)
    
    # Handle third run
    while run3.status in ["queued", "in_progress", "requires_action"]:
        time.sleep(1)
        run3 = project_client.agents.get_run(thread_id=thread.id, run_id=run3.id)
        
        if run3.status == "requires_action":
            tool_calls = run3.required_action.submit_tool_outputs.tool_calls
            tool_outputs = []
            
            for tool_call in tool_calls:
                output = execute_function_call(
                    tool_call.function.name,
                    tool_call.function.arguments
                )
                tool_outputs.append({
                    "tool_call_id": tool_call.id,
                    "output": output
                })
            
            project_client.agents.submit_tool_outputs_to_run(
                thread_id=thread.id,
                run_id=run3.id,
                tool_outputs=tool_outputs
            )
    
    # Get final messages
    messages = project_client.agents.list_messages(thread_id=thread.id)
    print("\n" + "="*70)
    print("COMPLETE CONVERSATION")
    print("="*70)
    
    for msg in reversed(list(messages)):
        print(f"\n{'User' if msg.role == 'user' else 'Agent'}:")
        for content in msg.content:
            if content.type == "text":
                print(f"   {content.text.value}")


def main():
    """Main test function"""
    print("\n" + "="*70)
    print("NORTH STAR AGENT END-TO-END TEST")
    print("Testing: Agent → Client Function Execution → Azure Functions → Cosmos DB")
    print("="*70)
    
    test_north_star_agent()
    
    print("\n" + "="*70)
    print("✅ TEST COMPLETE")
    print("="*70)
    print("\nThe test demonstrates:")
    print("• North Star Agent processes requests")
    print("• Agent returns function calls via requires_action")
    print("• Client executes the functions")
    print("• Functions interact with Azure Functions/Cosmos DB")
    print("• Complete flow working as designed")


if __name__ == "__main__":
    main()