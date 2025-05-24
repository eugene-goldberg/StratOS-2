# StratOS Agent Scripts

This directory contains scripts for deploying, testing, and interacting with StratOS multi-agent systems.

## Scripts Overview

### Deployment Scripts
- `deploy_stratos_agents.sh` - Deploy all StratOS agents to Azure AI Agent Service
- `deploy_strategic_foundation.sh` - Deploy Strategic Foundation system agents
- `deploy_analysis_system.sh` - Deploy Analysis & Intelligence system agents
- `deploy_planning_system.sh` - Deploy Planning & Execution system agents

### Testing Scripts
- `test_strategic_system.py` - Interactive testing for Strategic Foundation agents
- `test_analysis_system.py` - Interactive testing for Analysis agents
- `test_planning_system.py` - Interactive testing for Planning agents
- `test_orchestration.py` - Test cross-system orchestration

### Utility Scripts
- `check_agent_status.py` - Check status of deployed agents
- `cleanup_agents.py` - Clean up test agent deployments
- `export_agent_configs.py` - Export agent configurations to JSON/YAML

## Usage

### Deploy All Agents
```bash
bash deploy_stratos_agents.sh
```

### Test a Specific System
```bash
python test_strategic_system.py
```

### Check Agent Status
```bash
python check_agent_status.py
```

## Environment Setup

Ensure you have the following environment variables set:
- `AZURE_SUBSCRIPTION_ID`
- `AZURE_RESOURCE_GROUP`
- `AZURE_AI_PROJECT_NAME`
- `AZURE_OPENAI_DEPLOYMENT_NAME`
- `AZURE_OPENAI_ENDPOINT`
- `AZURE_OPENAI_API_KEY`