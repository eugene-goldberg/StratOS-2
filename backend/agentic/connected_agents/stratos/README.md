# StratOS Connected Agents

This directory contains the StratOS-specific connected agents implementation following the Azure AI Agent Service pattern.

## Directory Structure

```
stratos/
├── agents/           # Agent configurations and plugins
│   ├── ceo_log_agent_config.py
│   ├── ceo_log_plugin.py
│   ├── north_star_agent_config.py
│   ├── north_star_plugin.py
│   ├── orchestrator_agent_config.py
│   └── orchestrator_agent_config_with_north_star.py
│
├── deployment/       # Deployment and management scripts
│   ├── deploy_ceo_log_agent.py
│   ├── deploy_stratos_connected_agents.py
│   ├── deploy_stratos_with_north_star.py
│   └── remove_all_stratos_agents.py
│
├── tests/            # Test scripts and test outputs
│   ├── test_ceo_simple.py
│   ├── test_ceo_comprehensive.py
│   ├── test_north_star_simple.py
│   ├── test_north_star_comprehensive.py
│   ├── test_north_star_orchestration.py
│   ├── capture_north_star_telemetry.py
│   ├── CEO_AGENT_TESTING.md
│   ├── NORTH_STAR_AGENT_TESTING.md
│   └── test_outputs/
│
├── telemetry/        # Telemetry data and traces
│   └── north_star_agent/
│
├── archive/          # Archived deployment information
│   └── stratos_deployment_info_removed_*.json
│
└── NORTH_STAR_AGENT_CONVERSION_PLAN.md
```

## Connected Agents Pattern

StratOS agents follow the connected agent pattern:
- Agents have no tools in their configuration (TOOLS = [])
- Agents use Semantic Kernel plugins with @kernel_function decorators
- Agents are deployed with just name, model, and instructions
- The orchestrator uses these agents as connected_agent tools

## Current Agents

1. **CEO Log Agent** - Manages CEO's subjective inputs and strategic insights
2. **North Star Agent** - Manages organizational purpose, vision, values, and strategic goals
3. **StratOS Orchestrator** - Routes requests to appropriate specialized agents

## Deployment

To deploy the agents:
```bash
cd deployment
python deploy_stratos_with_north_star.py
```

To remove all agents:
```bash
cd deployment
python remove_all_stratos_agents.py
```

## Testing

Run tests from the tests directory:
```bash
cd tests
python test_ceo_simple.py           # Quick CEO Log test
python test_north_star_simple.py    # Quick North Star test
```

## Next Agents to Convert

Following the pattern established with CEO Log and North Star agents:
- Memory Recall Agent
- Preference Learning Agent
- SWOT/TOWS Agent
- Risk Opportunity Agent
- SO Linkage Agent
- And others...