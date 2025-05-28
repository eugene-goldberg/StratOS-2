# Connected Agents System

A multi-agent orchestration system using Azure AI Agent Service that demonstrates agent-to-agent communication through the ConnectedAgentTool pattern.

## 🚀 Quick Start

```bash
# 1. Set up environment
cd backend/agentic/connected_agents
cp .env.example .env  # Edit with your Azure credentials

# 2. Deploy agents
python deploy_connected_agents.py

# 3. Test the system
python test_quick_deployed.py
```

## 📋 System Overview

The system consists of:
- **Orchestrator Agent**: Routes requests to specialized agents
- **Greeter Agent**: Provides enthusiastic greetings
- **Calculator Agent**: Performs mathematical calculations

### How It Works

1. User sends a request to the Orchestrator
2. Orchestrator analyzes the request type
3. Orchestrator announces delegation (e.g., "I'll engage my mathematical calculation expert!")
4. Orchestrator invokes the appropriate specialized agent via ConnectedAgentTool
5. Specialized agent processes the request
6. Response is returned to the user

## 📁 Project Structure

```
connected_agents/
├── Core Implementation
│   ├── deploy_connected_agents.py         # Main deployment script
│   ├── agent_services.py                  # Helper functions
│   └── .env                              # Environment configuration
│
├── Agent Configurations
│   ├── specialized_agent_config.py        # Greeter agent config
│   ├── calculator_agent_config.py         # Calculator agent config
│   └── multi_tool_orchestrator_config.py  # Orchestrator config
│
├── Testing
│   ├── test_quick_deployed.py            # Quick verification test
│   └── test_multi_tool_orchestrator.py   # Comprehensive test suite
│
├── Documentation
│   ├── README.md                         # This file
│   ├── CONNECTED_AGENTS_DOCUMENTATION.md # Complete system documentation
│   ├── TECHNICAL_IMPLEMENTATION_GUIDE.md # Technical details
│   └── QUICK_REFERENCE.md               # Quick command reference
│
└── archive/                             # Historical/debug scripts
    └── README.md                        # Archive documentation
```

## 🔑 Key Features

### Delegation with Announcements
The orchestrator announces before delegating:
- **Greetings**: "I'll connect you with my enthusiastic greeting specialist!"
- **Calculations**: "I'll engage my mathematical calculation expert for this!"

### ConnectedAgentTool Pattern
Enables agent-to-agent communication:
```python
{
    "type": "connected_agent",
    "connected_agent": {
        "id": "asst_xxxxx",
        "name": "tool_name",
        "description": "Tool description"
    }
}
```

### Modular Architecture
- Easy to add new specialized agents
- Clear separation of concerns
- Reusable configuration patterns

## 🛠️ Configuration

### Environment Variables (.env)
```bash
# Azure AI Project
AZURE_AI_PROJECT_CONNECTION_STRING="..."
AZURE_AI_MODEL_DEPLOYMENT_NAME="gpt-35-turbo"

# Service Principal
AZURE_CLIENT_ID="..."
AZURE_CLIENT_SECRET="..."
AZURE_TENANT_ID="..."

# Agent IDs (populated after deployment)
MAIN_ORCHESTRATOR_AGENT_ID="..."
SPECIALIZED_GREETER_AGENT_ID="..."
SPECIALIZED_CALCULATOR_AGENT_ID="..."
```

## 🧪 Testing

### Quick Test
```bash
python test_quick_deployed.py
```
- Tests basic greeting delegation
- Tests simple calculation
- Verifies system is working

### Comprehensive Test
```bash
python test_multi_tool_orchestrator.py
```
- Tests multiple greeting formats
- Tests various calculation types
- Validates delegation patterns
- Checks announcement behavior

## 🔧 Common Operations

### Deploy/Redeploy System
```bash
python deploy_connected_agents.py
```

### Remove All Agents
```bash
python archive/remove_all_deployed_agents.py
```

### Add New Specialized Agent
1. Create agent config file
2. Update deployment script
3. Add tool to orchestrator
4. Update orchestrator instructions
5. Test delegation

## 📚 Documentation

- **[Complete Documentation](CONNECTED_AGENTS_DOCUMENTATION.md)**: Full system overview and details
- **[Technical Guide](TECHNICAL_IMPLEMENTATION_GUIDE.md)**: Implementation details and code walkthrough
- **[Quick Reference](QUICK_REFERENCE.md)**: Common commands and snippets

## 🐛 Troubleshooting

### No Delegation Announcements
- Update orchestrator instructions to make announcements MANDATORY
- Use emphatic language: MUST, CRITICAL, ALWAYS
- Redeploy orchestrator after changes

### Agent Not Found
- Verify agent IDs in .env
- Check if agents were deleted
- Ensure correct Azure credentials

### Tool Invocation Fails
- Check tool name matches in instructions and definition
- Verify specialized agents are deployed
- Check for API rate limits

## 🏗️ Architecture Decisions

1. **Why ConnectedAgentTool?**
   - Official Azure pattern for agent communication
   - Clean separation of concerns
   - Scalable to many agents

2. **Why Announcements?**
   - Better user experience
   - Debugging transparency
   - Shows multi-agent coordination

3. **Why Separate Configs?**
   - Modular design
   - Easy to modify individual agents
   - Clear organization

## 🚦 Current Status

✅ **Working Features**:
- Multi-agent orchestration
- Greeting delegation with announcements
- Calculator delegation with announcements
- Comprehensive test coverage
- Full documentation

🔄 **Future Enhancements**:
- Add more specialized agents
- Implement conversation memory
- Add web API interface
- Create UI dashboard

## 📄 License

This is part of the StratOS-2 project. See main project LICENSE.

## 🤝 Contributing

1. Test changes thoroughly
2. Update documentation
3. Follow existing patterns
4. Add tests for new features

---

For detailed information, see the [Complete Documentation](CONNECTED_AGENTS_DOCUMENTATION.md).