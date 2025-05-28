# Connected Agents - Quick Reference

## Environment Setup

```bash
# Required environment variables
AZURE_AI_PROJECT_CONNECTION_STRING="..."
AZURE_AI_MODEL_DEPLOYMENT_NAME="gpt-35-turbo"
AZURE_CLIENT_ID="..."
AZURE_CLIENT_SECRET="..."
AZURE_TENANT_ID="..."

# Agent IDs (after deployment)
MAIN_ORCHESTRATOR_AGENT_ID="asst_xxx"
SPECIALIZED_GREETER_AGENT_ID="asst_xxx"
SPECIALIZED_CALCULATOR_AGENT_ID="asst_xxx"
```

## Common Commands

### Deploy System
```bash
cd backend/agentic/connected_agents
source ../../../venv/bin/activate
python deploy_connected_agents.py
```

### Test System
```bash
# Quick test
python test_quick_deployed.py

# Full test suite
python test_multi_tool_orchestrator.py
```

### Remove All Agents
```bash
python archive/remove_all_deployed_agents.py
```

## Code Snippets

### Create an Agent
```python
agent = await client.agents.create_agent(
    model="gpt-35-turbo",
    name="MyAgent",
    instructions="You are a helpful agent."
)
```

### Create Connected Tool
```python
tool = {
    "type": "connected_agent",
    "connected_agent": {
        "id": "asst_xxxxx",
        "name": "my_tool",
        "description": "Tool description"
    }
}
```

### Invoke Agent
```python
# Get agent definition
agent_def = await client.agents.get_agent(agent_id=agent_id)

# Create agent instance
agent = AzureAIAgent(client=client, definition=agent_def)

# Invoke
async for response in agent.invoke(messages="Hello"):
    if hasattr(response, 'content'):
        print(response.content)
```

### Update Orchestrator Instructions
```python
# Delete old orchestrator
await client.agents.delete_agent(agent_id=old_id)

# Create new with updated instructions
new_orchestrator = await client.agents.create_agent(
    model=model_name,
    name=name,
    instructions=new_instructions,
    tools=tools
)
```

## Troubleshooting Checklist

### No Delegation Happening
- [ ] Check tool names match exactly in instructions and definition
- [ ] Verify agent IDs are correct in .env
- [ ] Ensure orchestrator has tools attached
- [ ] Check orchestrator instructions are explicit

### No Announcements
- [ ] Update instructions to make announcements MANDATORY
- [ ] Use emphatic language: MUST, CRITICAL, ALWAYS
- [ ] Place announcement requirement at beginning of instructions
- [ ] Redeploy orchestrator after instruction changes

### Agent Not Found
- [ ] Verify agent ID in .env
- [ ] Check if agent was deleted
- [ ] Ensure correct Azure subscription/resource group
- [ ] Verify credentials are valid

### Tool Invocation Fails
- [ ] Check specialized agent is responding
- [ ] Verify tool format matches API requirements
- [ ] Ensure no timeout issues
- [ ] Check for API rate limits

## Key Configuration Patterns

### Strong Delegation Instructions
```python
"CRITICAL PROTOCOL FOR ALL DELEGATIONS: "
"1. You MUST announce your delegation BEFORE invoking any tool "
"2. The announcement text MUST appear in your response "
"3. DO NOT skip announcements - they are MANDATORY "
```

### Tool Name Convention
```python
# In tool definition
"name": "enthusiastic_greeter_tool"

# In orchestrator instructions
"invoke the 'enthusiastic_greeter_tool'"
```

### Error Handling in Instructions
```python
"If tool invocation fails:
 1. Acknowledge the issue
 2. Attempt once more
 3. Provide alternative help if possible"
```

## Performance Tips

1. **Reuse Threads**: Don't create new threads for each message
2. **Concurrent Creation**: Create agents in parallel during deployment
3. **Stream Responses**: Process content as it arrives
4. **Rate Limiting**: Add delays between rapid API calls
5. **Batch Operations**: Group related operations

## Security Best Practices

1. **Never commit .env file**
2. **Use minimal permissions for service principal**
3. **Rotate credentials regularly**
4. **Store agent IDs securely**
5. **Validate all user inputs**

## Quick Debug Commands

```python
# List all agents
async for agent in client.agents.list_agents():
    print(f"{agent.name}: {agent.id}")

# Check agent tools
agent = await client.agents.get_agent(agent_id=id)
print(f"Tools: {agent.tools}")

# Test specific agent
response = await test_agent(agent_id, "test message")
print(response)
```

## Common Patterns

### Add New Specialized Agent
1. Create config file with name and instructions
2. Add creation logic to deployment script
3. Create tool definition for orchestrator
4. Update orchestrator instructions with delegation rules
5. Test delegation pattern

### Update Existing Agent
1. Get current agent configuration
2. Delete existing agent
3. Create new agent with updated config
4. Update agent ID in .env
5. Test to verify changes

## File Structure Reference
```
connected_agents/
├── Core Files
│   ├── deploy_connected_agents.py      # Main deployment
│   ├── agent_services.py               # Helper functions
│   └── .env                           # Environment config
├── Agent Configs
│   ├── specialized_agent_config.py     # Greeter config
│   ├── calculator_agent_config.py      # Calculator config
│   └── multi_tool_orchestrator_config.py # Orchestrator config
├── Testing
│   ├── test_quick_deployed.py         # Quick verification
│   └── test_multi_tool_orchestrator.py # Full test suite
├── Documentation
│   ├── CONNECTED_AGENTS_DOCUMENTATION.md
│   ├── TECHNICAL_IMPLEMENTATION_GUIDE.md
│   └── QUICK_REFERENCE.md (this file)
└── archive/                           # Historical scripts
```