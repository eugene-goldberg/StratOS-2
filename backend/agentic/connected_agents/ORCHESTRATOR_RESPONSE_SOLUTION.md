# Solution: Making Orchestrator Show Actual Agent Responses

## The Problem

The current StratOS Main Orchestrator only shows delegation announcements like:
```
"I'll connect you with the CEO Log specialist to log this board meeting update!"
```

But it does NOT show the actual response from the CEO Log agent, which would be something like:
```
"I've successfully logged the Q4 board meeting update. Key points recorded:
- Revenue exceeded targets by 15%
- Approved new R&D budget of $5M
This information has been stored in the organizational knowledge base."
```

## Root Cause

Azure AI Agent Service's connected agents (using `connected_agent` tool type) have a limitation:
- The orchestrator invokes the connected agent via tool call
- The tool executes successfully 
- BUT the tool's response is not automatically included in the orchestrator's output
- Users only see the delegation announcement, not the actual result

## Solutions

### Solution 1: Modified Orchestrator Instructions (Partial Fix)

Update the orchestrator instructions to explicitly mention tool results:

```python
INSTRUCTIONS = """
...
CRITICAL: After invoking a specialist tool:
1. Wait for the tool to complete
2. Include this message: "The specialist is processing your request..."
3. Note: The actual response will be delivered separately
"""
```

This helps set expectations but doesn't solve the core issue.

### Solution 2: Thread-Based Response Aggregation (Recommended)

Instead of using streaming API, use the thread-based approach to capture full conversation:

```python
# Create thread
thread = await project_client.agents.threads.create()

# Send message
await project_client.agents.threads.messages.create(
    thread_id=thread.id,
    role="user", 
    content=query
)

# Run orchestrator
run = await project_client.agents.threads.runs.create(
    thread_id=thread.id,
    assistant_id=orchestrator_id
)

# Wait for completion
while run.status in ["queued", "in_progress"]:
    await asyncio.sleep(0.5)
    run = await project_client.agents.threads.runs.retrieve(
        thread_id=thread.id,
        run_id=run.id
    )

# Get ALL messages (including tool responses)
messages = await project_client.agents.threads.messages.list(thread_id=thread.id)

# Aggregate responses
full_response = ""
for msg in messages.data:
    if msg.role == "assistant":
        for content in msg.content:
            if hasattr(content, 'text'):
                full_response += content.text.value + "\n"
```

### Solution 3: Direct Agent Invocation (Bypass Orchestrator)

For critical use cases, invoke agents directly:

```python
# Determine which agent to use (can still ask orchestrator for routing)
agent_id = AGENT_IDS["CEO Log Agent"]

# Invoke agent directly
agent = await project_client.agents.get_agent(agent_id)
response = ""
async for part in agent.invoke(messages=query):
    if hasattr(part, 'content'):
        response += str(part.content)

# Now you have the actual agent response
```

### Solution 4: Custom Response Handler (Advanced)

Build a custom handler that:
1. Captures orchestrator's routing decision
2. Extracts which agent was invoked
3. Makes a separate call to that agent
4. Combines both responses

```python
class EnhancedOrchestrator:
    async def process_request(self, query):
        # Get routing from orchestrator
        routing = await self.get_orchestrator_routing(query)
        
        # Extract target agent
        target_agent = self.extract_target_agent(routing)
        
        # Get actual response from agent
        agent_response = await self.invoke_agent_directly(target_agent, query)
        
        # Combine responses
        return f"{routing}\n\nSpecialist Response:\n{agent_response}"
```

## Recommended Approach

For the StratOS FastAPI integration:

1. **Short term**: Use Solution 2 (Thread-Based Response Aggregation) in the API endpoints
2. **Medium term**: Implement Solution 4 (Custom Response Handler) for better control
3. **Long term**: Work with Azure to enhance connected agent tool responses

## Implementation Example

Here's how to modify the `/api/v1/orchestrate` endpoint:

```python
@router.post("/orchestrate")
async def orchestrate_request(request: OrchestrateRequest):
    # Create thread for full conversation capture
    thread = await project_client.agents.threads.create()
    
    # Send user message
    await project_client.agents.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=request.query
    )
    
    # Run orchestrator
    run = await project_client.agents.threads.runs.create(
        thread_id=thread.id,
        assistant_id=ORCHESTRATOR_ID
    )
    
    # Wait and aggregate full response
    full_response = await aggregate_thread_responses(thread.id, run.id)
    
    return {
        "response": full_response,
        "thread_id": thread.id
    }
```

This ensures users see both the delegation announcement AND the actual agent response.