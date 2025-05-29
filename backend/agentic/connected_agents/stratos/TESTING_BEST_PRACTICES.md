# Connected Agents Testing Best Practices

## Overview
This guide documents best practices for testing connected agents based on lessons learned from the CEO Log Agent Cosmos DB integration.

## Critical Testing Principles

### 1. Always Test Through the Agent
**✅ DO**: Work exclusively through the agent API
```python
# Correct approach
response = requests.post(
    f"{base_url}/threads/{thread_id}/messages",
    headers=headers,
    json={"role": "user", "content": user_message}
)
```

**❌ DON'T**: Make direct calls to Azure Functions during testing
```python
# Incorrect - bypasses the agent
response = requests.post(
    "https://function-app.azurewebsites.net/api/function",
    headers={"x-functions-key": key},
    json=payload
)
```

### 2. Handle Function Calls Properly
When an agent returns function call requirements, execute them and return results:

```python
# Check for required actions
if msg.get("status") == "requires_action":
    for tool_call in run.required_action.submit_tool_outputs.tool_calls:
        if tool_call.function.name == "call_function":
            # Execute the function
            result = execute_function(tool_call.function.arguments)
            
            # Submit result back to agent
            tool_outputs.append({
                "tool_call_id": tool_call.id,
                "output": json.dumps(result)
            })
```

### 3. Follow the Weather Agent Pattern
The weather agent in semantic_kernel_multi_agent provides the reference implementation:
- Use function tools (not code interpreter)
- Define clear function schemas
- Handle tool outputs correctly
- Return structured responses

### 4. Verify End-to-End Flow
A complete test should verify:
1. User message → Agent
2. Agent → Function call request
3. Test harness → Execute function
4. Function → External service (Cosmos DB, APIs, etc.)
5. Function result → Agent
6. Agent → Final response to user

### 5. Common Pitfalls to Avoid

#### Pitfall 1: Testing Function Directly
```python
# ❌ Wrong - doesn't verify agent integration
result = save_to_cosmos_db(data)
assert result["success"] == True
```

```python
# ✅ Correct - tests through agent
response = send_message_to_agent("Save this log entry")
assert "successfully saved" in response
```

#### Pitfall 2: Not Handling Tool Outputs
```python
# ❌ Wrong - ignores function call requirements
response = send_message_to_agent(message)
print(response)  # Just prints "requires_action"
```

```python
# ✅ Correct - handles the complete flow
response = send_message_to_agent(message)
if requires_action(response):
    tool_outputs = execute_required_functions(response)
    final_response = submit_tool_outputs(tool_outputs)
```

#### Pitfall 3: Incorrect Field Names
```python
# ❌ Wrong - assumes field names
content = entry.get("content")  # May be None
```

```python
# ✅ Correct - check actual field names
# First check what fields exist
print(f"Available fields: {list(entry.keys())}")
# Then use correct field
log_content = entry.get("logEntry")  # Correct field name
```

## Test Script Template

```python
import requests
import json
import time

def test_agent_complete_flow():
    """Test agent with proper function call handling"""
    
    # 1. Create thread
    thread_response = requests.post(
        f"{base_url}/threads",
        headers=headers
    )
    thread_id = thread_response.json()["id"]
    
    # 2. Send message
    message_response = requests.post(
        f"{base_url}/threads/{thread_id}/messages",
        headers=headers,
        json={"role": "user", "content": "Your test message"}
    )
    
    # 3. Create run
    run_response = requests.post(
        f"{base_url}/threads/{thread_id}/runs",
        headers=headers,
        json={"assistant_id": assistant_id}
    )
    run_id = run_response.json()["id"]
    
    # 4. Poll for completion
    while True:
        run = get_run_status(thread_id, run_id)
        
        if run["status"] == "completed":
            break
            
        elif run["status"] == "requires_action":
            # Handle function calls
            tool_outputs = []
            for tool_call in run["required_action"]["submit_tool_outputs"]["tool_calls"]:
                result = execute_function(tool_call)
                tool_outputs.append({
                    "tool_call_id": tool_call["id"],
                    "output": json.dumps(result)
                })
            
            # Submit outputs
            submit_tool_outputs(thread_id, run_id, tool_outputs)
            
        elif run["status"] in ["failed", "cancelled", "expired"]:
            raise Exception(f"Run failed: {run['status']}")
            
        time.sleep(1)
    
    # 5. Get final response
    messages = get_messages(thread_id)
    return messages[0]["content"][0]["text"]["value"]

def execute_function(tool_call):
    """Execute the actual function call"""
    func_name = tool_call["function"]["name"]
    func_args = json.loads(tool_call["function"]["arguments"])
    
    # Route to appropriate function
    if func_name == "call_azure_function":
        return call_azure_function(func_args)
    else:
        return {"error": f"Unknown function: {func_name}"}

def call_azure_function(args):
    """Call the Azure Function with proper parameters"""
    response = requests.post(
        "https://your-function.azurewebsites.net/api/endpoint",
        headers={
            "x-functions-key": "your-key",
            "Content-Type": "application/json"
        },
        json=args
    )
    return response.json()
```

## Verification Checklist

Before claiming success, verify:

- [ ] Agent responds to messages
- [ ] Function calls are triggered by agent (not direct calls)
- [ ] Functions execute successfully
- [ ] External services (Cosmos DB) receive data
- [ ] Agent provides meaningful responses
- [ ] No errors in any step
- [ ] Data persists correctly in storage
- [ ] Field names match expected schema

## Debugging Tips

1. **Check Thread Messages**: Always retrieve all messages to see the flow
2. **Inspect Run Status**: Look for detailed error messages in failed runs
3. **Verify Function Outputs**: Log all function results before returning
4. **Check Field Names**: Don't assume - always verify actual field names
5. **Test Incrementally**: Test each step separately before full integration

## Example: CEO Log Agent Test

```python
# Successful test output
print("Testing CEO Log Agent...")
response = test_ceo_log_save("Completed Cosmos DB integration", "innovation")

# Verify in Cosmos DB
items = query_cosmos_db("SELECT * FROM c WHERE c.category = 'innovation'")
assert len(items) > 0
assert items[0]["logEntry"] == "Completed Cosmos DB integration"  # Note: logEntry, not content

print(f"✅ Success: Entry saved with ID {items[0]['id']}")
```

## Summary

The key to successful connected agent testing is to:
1. Always work through the agent API
2. Handle function calls properly
3. Verify the complete end-to-end flow
4. Check actual field names and schemas
5. Follow established patterns (like weather agent)

This ensures that your tests accurately reflect how the system will behave in production.