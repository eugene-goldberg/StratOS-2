# Connected Agents System - Complete Documentation

## Overview

The Connected Agents system demonstrates a multi-agent orchestration pattern using Azure AI Agent Service (formerly Azure OpenAI Assistants API). It consists of an orchestrator agent that delegates specialized tasks to connected agents based on the type of request.

## System Architecture

### Components

1. **Orchestrator Agent** - Main coordinator that routes requests
2. **Greeter Agent** - Specialized agent for enthusiastic greetings
3. **Calculator Agent** - Specialized agent for mathematical calculations
4. **ConnectedAgentTool** - Special tool type that enables agent-to-agent communication

### How It Works

```
User Request → Orchestrator Agent → Analyzes Request Type
                    ↓
            Decision Making:
            - Greeting? → Delegate to Greeter Agent
            - Math? → Delegate to Calculator Agent
            - Other? → Handle directly
                    ↓
            Tool Invocation (via ConnectedAgentTool)
                    ↓
            Specialized Agent Response
                    ↓
            Return to User
```

## Configuration Files

### 1. `specialized_agent_config.py`
Defines the enthusiastic greeter agent:
```python
AGENT_NAME_PREFIX = "SpecializedEnthusiasticGreeterAgent"
AGENT_INSTRUCTIONS = """You are the MOST enthusiastic greeter agent..."""
```

### 2. `calculator_agent_config.py`
Defines the calculator agent:
```python
AGENT_NAME_PREFIX = "CalculatorAgent"
AGENT_INSTRUCTIONS = """You are a precise mathematical calculator agent..."""
```

### 3. `multi_tool_orchestrator_config.py`
Defines the orchestrator with delegation rules:
```python
AGENT_NAME_PREFIX = "MultiToolOrchestratorAgent"
AGENT_INSTRUCTIONS = (
    "CRITICAL PROTOCOL FOR ALL DELEGATIONS: "
    "1. You MUST announce your delegation BEFORE invoking any tool "
    "2. The announcement text MUST appear in your response "
    "3. DO NOT skip announcements - they are MANDATORY "
    ...
)
```

## Key Implementation Details

### ConnectedAgentTool Format

The Azure AI Agent Service requires a specific format for connected agent tools:

```python
{
    "type": "connected_agent",
    "connected_agent": {
        "id": "asst_xxxxx",  # The agent ID to connect to
        "name": "tool_name",  # Must match name in orchestrator instructions
        "description": "Tool description"
    }
}
```

### Delegation Announcements

The orchestrator MUST announce delegations before invoking tools. This is enforced through explicit instructions:

- **For Greetings**: "I'll connect you with my enthusiastic greeting specialist!"
- **For Calculations**: "I'll engage my mathematical calculation expert for this!"

### Why Announcements Matter

1. **User Experience**: Users see that their request is being routed appropriately
2. **Debugging**: Makes it clear when delegation is happening
3. **Transparency**: Shows the multi-agent system in action

## Deployment Process

### 1. Environment Setup
Required environment variables in `.env`:
```bash
# Azure AI Project connection
AZURE_AI_PROJECT_CONNECTION_STRING="..."
AZURE_AI_MODEL_DEPLOYMENT_NAME="gpt-35-turbo"

# Service Principal credentials
AZURE_CLIENT_ID="..."
AZURE_CLIENT_SECRET="..."
AZURE_TENANT_ID="..."

# Agent IDs (populated after deployment)
SPECIALIZED_GREETER_AGENT_ID="..."
SPECIALIZED_CALCULATOR_AGENT_ID="..."
MAIN_ORCHESTRATOR_AGENT_ID="..."
```

### 2. Deployment Script (`deploy_connected_agents.py`)

The deployment process:

1. **Create Specialized Agents**:
   ```python
   # Create greeter agent
   greeter_agent = await client.agents.create_agent(
       model=model_name,
       name=f"{specialized_agent_config.AGENT_NAME_PREFIX}-{uuid}",
       instructions=specialized_agent_config.AGENT_INSTRUCTIONS
   )
   
   # Create calculator agent  
   calculator_agent = await client.agents.create_agent(
       model=model_name,
       name=f"{calculator_agent_config.AGENT_NAME_PREFIX}-{uuid}",
       instructions=calculator_agent_config.AGENT_INSTRUCTIONS
   )
   ```

2. **Create Tools for Orchestrator**:
   ```python
   tools = []
   tools.append({
       "type": "connected_agent",
       "connected_agent": {
           "id": greeter_agent.id,
           "name": "enthusiastic_greeter_tool",
           "description": "A specialized greeting expert..."
       }
   })
   tools.append({
       "type": "connected_agent",
       "connected_agent": {
           "id": calculator_agent.id,
           "name": "precise_calculator_tool",
           "description": "A mathematical calculation expert..."
       }
   })
   ```

3. **Create Orchestrator with Tools**:
   ```python
   orchestrator = await client.agents.create_agent(
       model=model_name,
       name=f"{multi_tool_orchestrator_config.AGENT_NAME_PREFIX}-{uuid}",
       instructions=multi_tool_orchestrator_config.AGENT_INSTRUCTIONS,
       tools=tools
   )
   ```

### 3. Running Deployment

```bash
cd backend/agentic/connected_agents
source ../../../venv/bin/activate
python deploy_connected_agents.py
```

## Testing

### 1. Quick Test (`test_quick_deployed.py`)
Performs basic verification:
- Tests greeting delegation
- Tests calculation delegation
- Verifies responses

### 2. Comprehensive Test (`test_multi_tool_orchestrator.py`)
Tests multiple scenarios:
- Various greeting formats
- Different calculation types
- Complex mathematical expressions
- Validates delegation patterns

### Running Tests

```bash
# Quick test
python test_quick_deployed.py

# Comprehensive test
python test_multi_tool_orchestrator.py
```

## Troubleshooting

### Common Issues

1. **No Delegation Announcements**
   - **Cause**: Orchestrator instructions not emphatic enough
   - **Fix**: Update instructions to make announcements MANDATORY
   - **Key**: Use words like "MUST", "CRITICAL", "MANDATORY"

2. **Tool Not Found Errors**
   - **Cause**: Tool name mismatch between instructions and tool definition
   - **Fix**: Ensure tool names match exactly (e.g., "enthusiastic_greeter_tool")

3. **Agent Not Responding**
   - **Cause**: Agent ID incorrect or agent deleted
   - **Fix**: Verify agent IDs in .env match deployed agents

### Fixing Announcement Issues

If announcements stop working after redeployment:

1. Update `multi_tool_orchestrator_config.py` with stronger instructions
2. Delete and recreate the orchestrator
3. Update the orchestrator ID in `.env`

Example fix:
```python
# Add at the beginning of instructions
"CRITICAL PROTOCOL FOR ALL DELEGATIONS: "
"1. You MUST announce your delegation BEFORE invoking any tool "
"2. The announcement text MUST appear in your response "
"3. DO NOT skip announcements - they are MANDATORY "
```

## API Integration

### Using Semantic Kernel

```python
from semantic_kernel.agents import AzureAIAgent

# Create agent instance
agent = AzureAIAgent(
    client=ai_project_client,
    definition=agent_definition
)

# Invoke agent
async for response in agent.invoke(messages="Hello!"):
    if hasattr(response, 'content'):
        print(response.content)
```

### Direct API Usage

The system uses Azure AI Agent Service REST API under the hood:
- Agents endpoint: `/assistants`
- Threads endpoint: `/threads`
- Messages endpoint: `/threads/{thread_id}/messages`
- Runs endpoint: `/threads/{thread_id}/runs`

## Best Practices

1. **Clear Tool Names**: Use descriptive, action-oriented tool names
2. **Explicit Instructions**: Be very explicit about when to use each tool
3. **Announcement Protocol**: Always include announcement requirements
4. **Error Handling**: Include fallback behavior in orchestrator instructions
5. **Testing**: Always test delegation patterns after deployment

## File Structure

```
connected_agents/
├── agent_services.py              # Helper functions for agent creation
├── calculator_agent_config.py     # Calculator agent configuration
├── deploy_connected_agents.py     # Main deployment script
├── multi_tool_orchestrator_config.py  # Orchestrator configuration
├── specialized_agent_config.py    # Greeter agent configuration
├── test_multi_tool_orchestrator.py    # Comprehensive tests
├── test_quick_deployed.py         # Quick verification tests
├── .env                          # Environment variables
└── archive/                      # Historical/debug scripts
```

## Advanced Topics

### Adding New Specialized Agents

1. Create a new config file (e.g., `weather_agent_config.py`)
2. Define agent name and instructions
3. Update deployment script to create the agent
4. Add tool definition to orchestrator
5. Update orchestrator instructions with delegation rules

### Scaling Considerations

- Each agent consumes Azure resources
- Tool invocations add latency
- Consider grouping related functionality
- Monitor token usage across agents

### Security

- Use service principals with minimal permissions
- Store credentials securely in .env
- Never commit .env to version control
- Rotate credentials regularly

## Conclusion

The Connected Agents system demonstrates a powerful pattern for building modular, scalable AI systems. By separating concerns into specialized agents and using an orchestrator for coordination, you can build complex workflows while maintaining clarity and maintainability.

Key takeaways:
- ConnectedAgentTool enables agent-to-agent communication
- Clear instructions are critical for proper delegation
- Announcement protocols improve user experience
- Modular design allows easy extension