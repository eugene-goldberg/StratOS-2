#!/usr/bin/env python3
"""Direct test of CEO Agent with Cosmos DB integration"""

import os
import sys
import json
import time
from azure.ai.agents import AgentsClient
from azure.identity import DefaultAzureCredential
from azure.core.credentials import AzureKeyCredential

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Azure AI configuration
AZURE_AI_ENDPOINT = "https://sk-multi-agent-ai.openai.azure.com"
AZURE_AI_KEY = "7c86bb2a5ad446e89e9c07ddb14b9eac"

# CEO Agent ID from deployment
CEO_AGENT_ID = "asst_0QgsT6Zvd1rgf0REzXFieiQo"

# Test configuration
TEST_USER_ID = "ceo-001"

def test_ceo_agent_cosmos_integration():
    """Test CEO Agent with Cosmos DB integration"""
    
    print("=" * 60)
    print("CEO Agent - Cosmos DB Integration Test")
    print("=" * 60)
    
    # Create agents client
    client = AgentsClient(
        endpoint=AZURE_AI_ENDPOINT,
        credential=AzureKeyCredential(AZURE_AI_KEY)
    )
    
    # Create a thread
    thread = client.threads.create()
    print(f"\nCreated thread: {thread.id}")
    
    # Test 1: Save a CEO log entry
    print("\n=== Test 1: Save CEO Log Entry ===")
    print("Sending: 'I need to record a critical observation: Our digital transformation initiative...'")
    
    message1 = client.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content="I need to record a critical observation: Our digital transformation initiative is ahead of schedule. The AI agent deployment has exceeded expectations with a 40% improvement in strategic planning efficiency. This validates our technology-first approach."
    )
    
    # Run the assistant
    run1 = client.threads.runs.create(
        thread_id=thread.id,
        assistant_id=CEO_AGENT_ID
    )
    
    # Wait for completion
    while run1.status in ["queued", "in_progress", "requires_action"]:
        time.sleep(1)
        run1 = client.threads.runs.retrieve(
            thread_id=thread.id,
            run_id=run1.id
        )
        
        # Handle function calls if needed
        if run1.status == "requires_action":
            tool_outputs = []
            for tool_call in run1.required_action.submit_tool_outputs.tool_calls:
                print(f"Function call: {tool_call.function.name}")
                print(f"Arguments: {tool_call.function.arguments}")
                
                # Parse arguments
                args = json.loads(tool_call.function.arguments)
                
                # Call the appropriate Azure Function
                if tool_call.function.name == "SaveCEOLog":
                    import requests
                    url = "https://stratos-ceo-log-functions.azurewebsites.net/api/saveceolog?code=I3c897PZMtJp1goBaxPwGlXa3Ni6ZsM09t1F7roTLVZeAzFu69TeKA=="
                    
                    # Ensure userId is set
                    if "userId" not in args:
                        args["userId"] = TEST_USER_ID
                    
                    # Ensure metadata is set
                    if "metadata" not in args:
                        args["metadata"] = {"source": "agent", "device": "test"}
                    
                    response = requests.post(url, json=args)
                    result = response.json() if response.status_code == 201 else {"error": response.text}
                    
                    tool_outputs.append({
                        "tool_call_id": tool_call.id,
                        "output": json.dumps(result)
                    })
            
            # Submit tool outputs
            run1 = client.threads.runs.submit_tool_outputs(
                thread_id=thread.id,
                run_id=run1.id,
                tool_outputs=tool_outputs
            )
    
    # Get response
    if run1.status == "completed":
        messages = client.threads.messages.list(thread_id=thread.id)
        for msg in messages.data:
            if msg.role == "assistant" and msg.created_at > message1.created_at:
                print(f"\nAgent Response: {msg.content[0].text.value}")
                break
    else:
        print(f"\nRun failed with status: {run1.status}")
    
    # Test 2: Search logs
    print("\n=== Test 2: Search CEO Logs ===")
    print("Sending: 'Search for my entries about digital transformation and AI'")
    
    message2 = client.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content="Search for my entries about digital transformation and AI"
    )
    
    run2 = client.threads.runs.create(
        thread_id=thread.id,
        assistant_id=CEO_AGENT_ID
    )
    
    # Wait and handle function calls
    while run2.status in ["queued", "in_progress", "requires_action"]:
        time.sleep(1)
        run2 = client.threads.runs.retrieve(
            thread_id=thread.id,
            run_id=run2.id
        )
        
        if run2.status == "requires_action":
            tool_outputs = []
            for tool_call in run2.required_action.submit_tool_outputs.tool_calls:
                print(f"Function call: {tool_call.function.name}")
                
                args = json.loads(tool_call.function.arguments)
                
                if tool_call.function.name == "SearchCEOLogs":
                    import requests
                    url = "https://stratos-ceo-log-functions.azurewebsites.net/api/searchceologs?code=uXjWD5crSSJYH_7eL3IcQq_ebEqVqO9D2QaC24UKa_RNAzFuVD7gkg=="
                    
                    if "userId" not in args:
                        args["userId"] = TEST_USER_ID
                    
                    response = requests.post(url, json=args)
                    result = response.json()
                    
                    tool_outputs.append({
                        "tool_call_id": tool_call.id,
                        "output": json.dumps(result)
                    })
            
            run2 = client.threads.runs.submit_tool_outputs(
                thread_id=thread.id,
                run_id=run2.id,
                tool_outputs=tool_outputs
            )
    
    if run2.status == "completed":
        messages = client.threads.messages.list(thread_id=thread.id)
        for msg in messages.data:
            if msg.role == "assistant" and msg.created_at > message2.created_at:
                print(f"\nAgent Response: {msg.content[0].text.value[:500]}...")
                break
    
    # Test 3: Get insights
    print("\n=== Test 3: Get Insights ===")
    print("Sending: 'What insights can you provide from my recent log entries?'")
    
    message3 = client.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content="What insights can you provide from my recent log entries?"
    )
    
    run3 = client.threads.runs.create(
        thread_id=thread.id,
        assistant_id=CEO_AGENT_ID
    )
    
    while run3.status in ["queued", "in_progress", "requires_action"]:
        time.sleep(1)
        run3 = client.threads.runs.retrieve(
            thread_id=thread.id,
            run_id=run3.id
        )
        
        if run3.status == "requires_action":
            tool_outputs = []
            for tool_call in run3.required_action.submit_tool_outputs.tool_calls:
                print(f"Function call: {tool_call.function.name}")
                
                args = json.loads(tool_call.function.arguments)
                
                if tool_call.function.name == "GetInsights":
                    import requests
                    url = f"https://stratos-ceo-log-functions.azurewebsites.net/api/getinsights?code=Rx3WeFi1SoWXpbiZtsOCBVyswP06bUskqSYKK5HdntHBAzFuqJ56aw==&userId={TEST_USER_ID}"
                    
                    response = requests.get(url)
                    result = response.json()
                    
                    tool_outputs.append({
                        "tool_call_id": tool_call.id,
                        "output": json.dumps(result)
                    })
                elif tool_call.function.name == "AnalyzeLogs":
                    import requests
                    url = "https://stratos-ceo-log-functions.azurewebsites.net/api/analyzelogs?code=1ALdM_XHFGwQ5XtC5BBsnJ-_j_w30lef9DsjGWVrpNJfAzFuEHzbmg==&userId=ceo-001"
                    
                    if "userId" not in args:
                        args["userId"] = TEST_USER_ID
                    
                    # Fix focus area if needed
                    if args.get("focusArea") == "all":
                        args["focusArea"] = "general"
                    
                    response = requests.post(url, json=args)
                    result = response.json()
                    
                    tool_outputs.append({
                        "tool_call_id": tool_call.id,
                        "output": json.dumps(result)
                    })
            
            run3 = client.threads.runs.submit_tool_outputs(
                thread_id=thread.id,
                run_id=run3.id,
                tool_outputs=tool_outputs
            )
    
    if run3.status == "completed":
        messages = client.threads.messages.list(thread_id=thread.id)
        for msg in messages.data:
            if msg.role == "assistant" and msg.created_at > message3.created_at:
                print(f"\nAgent Response: {msg.content[0].text.value}")
                break
    
    # Clean up
    client.threads.delete(thread.id)
    
    print("\n" + "=" * 60)
    print("Integration Test Complete")
    print("=" * 60)

if __name__ == "__main__":
    test_ceo_agent_cosmos_integration()