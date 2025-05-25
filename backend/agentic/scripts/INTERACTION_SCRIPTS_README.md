# StratOS Agent Interaction Scripts

This directory contains scripts for interacting with the deployed StratOS agents on Azure AI Agent Service.

## Prerequisites

1. Ensure you have deployed the agents using `deploy_agents_ai_project.py`
2. The `.env` file in the parent directory must contain valid Azure credentials:
   ```
   AZURE_AI_AGENT_ENDPOINT="https://ai.azure.com/api/eastus/agents/v1.0/..."
   AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME="gpt-35-turbo"
   AZURE_AI_AGENT_API_VERSION="2024-12-01-preview"
   ```
3. Install required dependencies:
   ```bash
   pip install semantic-kernel azure-identity python-dotenv colorama matplotlib numpy
   ```

## Available Scripts

### 1. Agent Interaction Client (`agent_interaction_client.py`)

Base client library for interacting with deployed agents. This is used by other scripts.

**Features:**
- Load agent configurations from deployment
- Create agent instances
- Send messages and receive responses
- Handle authentication with Azure

**Usage:**
```python
from agent_interaction_client import StratosAgentClient

client = StratosAgentClient()
response = await client.chat_with_agent("CEOLogAgent", "Important meeting today")
```

### 2. Interactive Chat CLI (`interactive_agent_chat.py`)

Interactive command-line interface for chatting with agents.

**Features:**
- List all available agents
- Switch between agents
- Maintain conversation history
- Save conversations to file
- Color-coded interface

**Usage:**
```bash
# Start interactive chat
python interactive_agent_chat.py

# Start with specific agent
python interactive_agent_chat.py --agent CEOLogAgent

# Start with system router
python interactive_agent_chat.py --system strategic
```

**Commands:**
- `/agents` - List all available agents
- `/use <name>` - Switch to a specific agent
- `/system <name>` - Use a system router (strategic/analysis/planning)
- `/info` - Show current agent information
- `/history` - Show conversation history
- `/new` - Start a new conversation thread
- `/save` - Save conversation to file
- `/help` - Show help message
- `/quit` - Exit the application

### 3. System Testing (`test_agent_systems.py`)

Test each agent system (Strategic, Analysis, Planning) with predefined scenarios.

**Features:**
- Test all agents in each system
- Predefined test scenarios for each agent
- Success/failure reporting
- Performance metrics
- Detailed JSON report

**Usage:**
```bash
python test_agent_systems.py
```

**Output:**
- Console output with test results
- JSON file with detailed results: `test_results_YYYYMMDD_HHMMSS.json`

### 4. Batch Testing (`batch_test_agents.py`)

Comprehensive testing of all agents with multiple scenarios.

**Features:**
- Test all 15 deployed agents
- Multiple test scenarios per agent
- Progress tracking
- System-level summaries
- Detailed performance metrics

**Usage:**
```bash
python batch_test_agents.py
```

**Output:**
- Console summary with success rates
- JSON file with detailed results: `batch_test_results_YYYYMMDD_HHMMSS.json`

### 5. Performance Benchmarking (`benchmark_agent_performance.py`)

Measure performance characteristics of deployed agents.

**Features:**
- Response time benchmarks (short/medium/long queries)
- Throughput testing (requests per second)
- Concurrency testing (1, 5, 10 concurrent requests)
- Statistical analysis (mean, median, p95, std dev)
- Performance visualization charts

**Usage:**
```bash
python benchmark_agent_performance.py
```

**Output:**
- Console summary with performance metrics
- Performance chart: `agent_response_times_YYYYMMDD_HHMMSS.png`
- JSON file with detailed metrics: `performance_benchmark_YYYYMMDD_HHMMSS.json`

## Agent Systems Overview

### Strategic Foundation & Insights System (5 agents)
- **StrategicContextRouter**: Routes strategic queries to appropriate agents
- **CEOLogAgent**: Processes CEO log entries with tags and summaries
- **NorthStarAgent**: Manages vision, values, and strategic goals
- **MemoryRecallAgent**: Semantic search and pattern recognition
- **PreferenceLearningAgent**: Learns and applies user preferences

### Analysis & Intelligence System (4 agents)
- **AnalysisOrchestrator**: Routes analysis requests
- **SWOTTOWSAgent**: SWOT analysis and TOWS strategy generation
- **RiskOpportunityAgent**: Risk detection and opportunity identification
- **SOLinkageAgent**: Links subjective insights to objective data

### Planning & Execution System (6 agents)
- **PlanningCoordinator**: Routes planning requests
- **InitiativeGenerationAgent**: Creates strategic initiatives
- **ResourceOptimizationAgent**: Optimizes resource allocation
- **CanvasVisualizationAgent**: Creates visual strategy representations
- **AlignmentScoringAgent**: Scores strategic alignment
- **ActionPlanningAgent**: Breaks down initiatives into tasks

## Troubleshooting

### Authentication Issues
- Ensure you're logged in with Azure CLI: `az login`
- Check that your service principal has proper permissions
- Verify the endpoint URL format in `.env`

### Connection Errors
- Verify the Azure AI Agent Service endpoint is correct
- Check that agents are deployed (run `list_ai_project_agents.py`)
- Ensure your network can reach Azure services

### Performance Issues
- Agent responses may take 2-10 seconds depending on complexity
- First request to an agent may be slower (cold start)
- Consider using GPT-3.5-Turbo for faster responses

## Best Practices

1. **Start with the Interactive Chat** to familiarize yourself with each agent
2. **Run System Tests** to verify all agents are working correctly
3. **Use Batch Testing** for comprehensive validation
4. **Run Performance Benchmarks** to understand response characteristics
5. **Save conversation history** for important interactions
6. **Monitor costs** in Azure portal as agent usage incurs charges

## Example Workflow

```bash
# 1. List deployed agents
python list_ai_project_agents.py

# 2. Test all systems
python test_agent_systems.py

# 3. Interactive exploration
python interactive_agent_chat.py --system strategic

# 4. Comprehensive testing
python batch_test_agents.py

# 5. Performance analysis
python benchmark_agent_performance.py
```