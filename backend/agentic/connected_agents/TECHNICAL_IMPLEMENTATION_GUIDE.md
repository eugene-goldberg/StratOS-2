# Connected Agents - Technical Implementation Guide

## Code Walkthrough

### 1. Agent Service Functions (`agent_services.py`)

```python
async def create_specialized_agent(client, model_deployment_name):
    """Creates a specialized agent in Azure AI Agent Service."""
    agent_name = f"{specialized_agent_config.AGENT_NAME_PREFIX}-{uuid.uuid4()}"
    
    agent_definition = await client.agents.create_agent(
        model=model_deployment_name,
        name=agent_name,
        instructions=specialized_agent_config.AGENT_INSTRUCTIONS,
    )
    return agent_definition
```

**Key Points**:
- Uses UUID for unique agent names
- Returns full agent definition object
- No tools attached to specialized agents

### 2. Tool Definition Function

```python
def define_connected_tool(specialized_agent_id, tool_name, tool_description):
    """Defines a ConnectedAgentTool object."""
    connected_tool = ConnectedAgentTool(
        id=specialized_agent_id,
        name=tool_name,
        description=tool_description
    )
    return connected_tool
```

**Important**: This function is not used in current implementation. We directly create tool dictionaries instead.

### 3. Deployment Script Details

#### Initialization
```python
# Load environment
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
```

#### Azure Client Setup
```python
async with DefaultAzureCredential() as credential, \
           AIProjectClient(
               endpoint=project_connection_string,
               credential=credential,
               api_version="2024-12-01-preview"
           ) as client:
```

#### Tool Format for API
```python
# Critical: This exact format is required by Azure AI Agent Service
tools.append({
    "type": "connected_agent",
    "connected_agent": {
        "id": greeter_agent_id,
        "name": "enthusiastic_greeter_tool",
        "description": "A specialized greeting expert..."
    }
})
```

### 4. Testing Implementation

#### Agent Invocation Pattern
```python
# Get agent definition first
agent_def = await client.agents.get_agent(agent_id=orchestrator_id)

# Create agent instance
agent = AzureAIAgent(client=client, definition=agent_def)

# Invoke and collect response
response = ""
async for part in agent.invoke(messages="Hello!"):
    if hasattr(part, 'content') and part.content:
        response += str(part.content)
```

#### Thread Management
```python
# Threads are created automatically on first invocation
conversation_thread = None

async for response_part in agent.invoke(messages=query, thread=conversation_thread):
    if not conversation_thread:
        conversation_thread = response_part.thread
```

### 5. Critical Implementation Details

#### Why We Don't Use `agent_services.create_orchestrator_agent()`

The original function had issues:
1. Referenced non-existent config after refactoring
2. Complex tool conversion logic
3. We need direct control over tool format

Instead, we create orchestrator directly:
```python
orchestrator = await client.agents.create_agent(
    model=model_name,
    name=f"{multi_tool_orchestrator_config.AGENT_NAME_PREFIX}-{uuid}",
    instructions=multi_tool_orchestrator_config.AGENT_INSTRUCTIONS,
    tools=tools  # Pre-formatted tools list
)
```

#### Tool Name Matching

Tool names MUST match exactly between:
1. Tool definition: `"name": "enthusiastic_greeter_tool"`
2. Orchestrator instructions: `"invoke the 'enthusiastic_greeter_tool'"`

#### Announcement Implementation

The fix that made announcements work consistently:

```python
# Before (didn't work consistently)
"DIRECTIVE 3: CALCULATION DELEGATION PROTOCOL "
"For ANY calculation or math request: "
"   STEP 3.1: Announce with EXACTLY: 'I'll engage my mathematical calculation expert for this!' "

# After (works consistently)  
"CRITICAL PROTOCOL FOR ALL DELEGATIONS: "
"1. You MUST announce your delegation BEFORE invoking any tool "
"2. The announcement text MUST appear in your response "
"3. DO NOT skip announcements - they are MANDATORY "
```

### 6. Error Handling Patterns

#### Agent Creation Failures
```python
try:
    agent = await client.agents.create_agent(...)
except Exception as e:
    logger.error(f"Failed to create agent: {e}")
    # Handle cleanup if needed
```

#### Tool Invocation Failures
The orchestrator should have fallback behavior:
```python
# In orchestrator instructions
"If a tool fails to respond, apologize and either:
 1. Retry once
 2. Provide a direct answer if possible
 3. Explain the issue to the user"
```

### 7. Environment Variable Management

#### Reading IDs
```python
orchestrator_id = os.getenv("MAIN_ORCHESTRATOR_AGENT_ID")
if not orchestrator_id:
    logger.error("MAIN_ORCHESTRATOR_AGENT_ID not found")
    return
```

#### Updating .env After Deployment
```python
from pathlib import Path

env_path = Path(__file__).parent / '.env'
env_content = env_path.read_text()

# Update specific agent ID
new_content = env_content.replace(
    f'MAIN_ORCHESTRATOR_AGENT_ID={old_id}',
    f'MAIN_ORCHESTRATOR_AGENT_ID={new_id}'
)
env_path.write_text(new_content)
```

### 8. API Response Handling

#### Polling Run Status
```python
while True:
    run = await client.runs.get_run(
        thread_id=thread.id,
        run_id=run.id
    )
    
    if run.status == "completed":
        break
    elif run.status == "failed":
        raise Exception(f"Run failed: {run.last_error}")
        
    await asyncio.sleep(0.5)
```

#### Streaming Responses
```python
async for response_part in agent.invoke(messages=query):
    # Each part may contain partial content
    if hasattr(response_part, 'content') and response_part.content:
        # Process incrementally
        print(response_part.content, end='', flush=True)
```

### 9. Common Pitfalls and Solutions

#### Pitfall 1: Forgetting to Pass Full Definition
```python
# Wrong
agent = AzureAIAgent(client=client, definition={"id": agent_id})

# Correct  
agent_def = await client.agents.get_agent(agent_id=agent_id)
agent = AzureAIAgent(client=client, definition=agent_def)
```

#### Pitfall 2: Tool Format Mismatch
```python
# Wrong - using ConnectedAgentTool object directly
tools.append(connected_tool)

# Correct - using dictionary format
tools.append({
    "type": "connected_agent",
    "connected_agent": {
        "id": tool.id,
        "name": tool.name,
        "description": tool.description
    }
})
```

#### Pitfall 3: Weak Orchestrator Instructions
```python
# Weak - model might skip announcements
"You should announce before using tools"

# Strong - model will follow
"You MUST announce your delegation BEFORE invoking any tool"
"DO NOT skip announcements - they are MANDATORY"
```

### 10. Performance Considerations

#### Concurrent Agent Creation
```python
# Create agents concurrently for faster deployment
greeter_task = create_specialized_agent(client, model_name)
calculator_task = create_calculator_agent(client, model_name)

greeter_agent, calculator_agent = await asyncio.gather(
    greeter_task, calculator_task
)
```

#### Response Streaming
- Responses stream incrementally
- Don't wait for full response before processing
- Update UI/logs as content arrives

#### Thread Reuse
```python
# Reuse threads for conversation continuity
thread_id = os.getenv("CONVERSATION_THREAD_ID")
if thread_id:
    thread = await client.threads.get_thread(thread_id)
else:
    thread = await client.threads.create_thread()
```

## Debugging Techniques

### 1. Enable Detailed Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Also enable HTTP logging
import http.client
http.client.HTTPConnection.debuglevel = 1
```

### 2. Inspect Tool Definitions
```python
agent_def = await client.agents.get_agent(agent_id=orchestrator_id)
if agent_def.tools:
    for i, tool in enumerate(agent_def.tools):
        logger.info(f"Tool {i}: {tool}")
```

### 3. Trace Delegation Flow
Add logging in orchestrator instructions:
```
"After identifying request type, state: 'REQUEST TYPE: [type]'"
"Before invoking tool, state: 'INVOKING: [tool_name]'"
```

### 4. Check Agent Availability
```python
try:
    agent = await client.agents.get_agent(agent_id=agent_id)
    logger.info(f"Agent {agent.name} is available")
except Exception as e:
    logger.error(f"Agent {agent_id} not found: {e}")
```

## Integration Examples

### Web API Integration
```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class ChatRequest(BaseModel):
    message: str
    thread_id: Optional[str] = None

@app.post("/chat")
async def chat(request: ChatRequest):
    # Get or create thread
    thread = await get_or_create_thread(request.thread_id)
    
    # Invoke orchestrator
    response = await invoke_orchestrator(
        message=request.message,
        thread=thread
    )
    
    return {
        "response": response,
        "thread_id": thread.id
    }
```

### Batch Processing
```python
async def process_queries(queries: List[str]):
    """Process multiple queries efficiently."""
    
    # Create orchestrator instance once
    orchestrator = await get_orchestrator_agent()
    
    # Process queries with rate limiting
    results = []
    for query in queries:
        result = await orchestrator.invoke(messages=query)
        results.append(result)
        await asyncio.sleep(0.1)  # Rate limit
        
    return results
```

## Conclusion

This technical guide provides the detailed implementation knowledge needed to work with the Connected Agents system. Key takeaways:

1. Tool format must exactly match Azure AI Agent Service requirements
2. Agent definitions must be retrieved before creating AzureAIAgent instances  
3. Strong, explicit instructions are crucial for consistent behavior
4. Proper error handling and logging aid debugging
5. Performance can be optimized through concurrent operations and thread reuse

For practical implementation, always refer to the working example in `deploy_connected_agents.py` as the reference implementation.