# Connected Agents Telemetry Guide

## Overview

This guide provides comprehensive instructions for implementing, capturing, and analyzing telemetry for the Connected Agents system. All telemetry-related scripts and data files are located in the `telemetry/` subdirectory.

## Status: ✅ FULLY ENABLED

The connected agents system has comprehensive telemetry tracking through Azure Application Insights, providing complete visibility into agent invocations, delegations, tool calls, and responses.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Running Tests with Telemetry](#running-tests-with-telemetry)
4. [Capturing Telemetry Data](#capturing-telemetry-data)
5. [Analyzing Telemetry](#analyzing-telemetry)
6. [Telemetry Scripts Reference](#telemetry-scripts-reference)
7. [Troubleshooting](#troubleshooting)

## What's Tracked

### 1. **Agent Invocations**
- Each call to the orchestrator agent
- Message content and length
- Agent IDs and names
- Request timestamps

### 2. **Delegations**
- Routing from orchestrator to specialized agents
- Delegation type (greeting, calculator, weather)
- Announcement tracking ("I'll connect you with...")
- Success/failure status

### 3. **Tool Calls**
- Function executions with parameters
- Tool call IDs and types
- Connected agent delegations
- API call results

### 4. **Performance Metrics**
- Response times for each delegation
- Duration of agent invocations
- End-to-end request processing time
- Token usage (input/output)

### 5. **Distributed Tracing**
- Full request flow visualization
- Parent-child span relationships
- Trace IDs for correlation
- Thread and run IDs

## Prerequisites

1. **Azure Application Insights**: Ensure you have access to the Application Insights workspace
   - Resource Name: `stratos-multi-agent-appinsights`
   - Workspace ID: `b318971e-7337-4649-947f-891c69c60ecb`
   - Resource Group: `semantic-kernel-multi-agent-rg`
   - Location: East US

2. **Python Dependencies**:
   ```bash
   pip install azure-monitor-query azure-identity opentelemetry-api opentelemetry-sdk
   ```

3. **Azure CLI**: Authenticated with appropriate permissions
   ```bash
   az login
   ```

## Environment Setup

### Step 1: Set Application Insights Connection String

The connection string must be set in your environment. Check if it's already set:

```bash
# From the backend/agentic directory
grep APPLICATIONINSIGHTS_CONNECTION_STRING .env
```

If not set, add it to your `.env` file:
```
APPLICATIONINSIGHTS_CONNECTION_STRING="InstrumentationKey=189923ab-6ad8-408f-b3f6-7ae4817a3988;IngestionEndpoint=https://eastus-8.in.applicationinsights.azure.com/;LiveEndpoint=https://eastus.livediagnostics.monitor.azure.com/;ApplicationId=dfba6d9b-7df1-4bf5-af6a-2fb21f1881b2"
```

### Step 2: Verify Telemetry Configuration

```bash
# Check telemetry initialization
python3 -c "import os; print('Telemetry enabled:', 'APPLICATIONINSIGHTS_CONNECTION_STRING' in os.environ)"
```

## Running Tests with Telemetry

### Step 1: Deploy Connected Agents

First, ensure your connected agents are deployed:

```bash
cd backend/agentic/connected_agents
python3 deploy_stratos_connected_agents.py
```

### Step 2: Run Tests with Telemetry Capture

Use the telemetry-enabled test script:

```bash
cd backend/agentic/connected_agents
python3 telemetry/test_connected_agents_telemetry.py
```

This script will:
- Initialize telemetry with proper service naming
- Create spans for each test operation
- Capture delegation events
- Save results with timestamps

### Step 3: Monitor Real-time Telemetry

During test execution, you'll see telemetry confirmations:
```
Telemetry transmission successful. Items accepted: 6/6
```

## Capturing Telemetry Data

### Method 1: Capture During Test Execution

The most reliable method captures telemetry as tests run:

```bash
cd backend/agentic/connected_agents
python3 telemetry/capture_test_telemetry.py
```

This creates a timestamped JSON file with:
- Test execution details
- Response times
- Delegation confirmations
- Operation IDs

### Method 2: Query Historical Telemetry

To query telemetry from the last hour:

```bash
cd backend/agentic/connected_agents
python3 telemetry/get_telemetry_simple.py
```

This will:
1. Connect to Application Insights
2. Query AppTraces table for agent-related activity
3. Save results to `agent_telemetry_[timestamp].json`

## Analyzing Telemetry

### Step 1: Run the Analysis Script

```bash
cd backend/agentic/connected_agents
python3 telemetry/analyze_telemetry_traces.py
```

This provides:
- Thread-by-thread breakdown
- Delegation flow visualization
- Token usage statistics
- Timing information

### Step 2: Understanding the Output

The analysis shows:

```
📥 USER MESSAGE         - Incoming request
💬 MESSAGE CREATION     - Agent response
🔧 TOOL CALLS          - Delegation to connected agent
✅ DELEGATION TO CONNECTED AGENT!
```

### Step 3: View Detailed Traces

For raw telemetry data inspection:

```bash
cd backend/agentic/connected_agents
python3 telemetry/view_telemetry.py
```

## Implementation Details

### Architecture Components

1. **Core Telemetry Module**: `/backend/agentic/core/telemetry.py`
   - OpenTelemetry SDK with Azure Monitor exporter
   - Automatic span creation and context propagation
   - Custom attributes and events

2. **Enhanced Agent Client**: `/backend/agentic/services/telemetry_agent_client.py`
   - Wrapper around standard agent client
   - Automatic telemetry tracking
   - Performance metrics collection

3. **Test Scripts**: Located in `telemetry/` subdirectory
   - Full integration with telemetry
   - Capture and analysis tools

### Code Integration Example

```python
from core.telemetry import initialize_telemetry, create_span_context, add_span_attributes

# Initialize at startup
tracer = initialize_telemetry(
    service_name="connected-agents-orchestrator",
    service_version="1.0.0"
)

# Track agent invocation
async def invoke_agent_with_telemetry(agent_id: str, message: str):
    with create_span_context("agent.invoke", {
        "agent.id": agent_id,
        "message.length": len(message)
    }) as span:
        response = await agent.invoke(message)
        add_span_attributes(span, {
            "response.length": len(response),
            "response.status": "success"
        })
        return response
```

## Telemetry Scripts Reference

### Core Scripts

1. **`telemetry/test_connected_agents_telemetry.py`**
   - Main test runner with telemetry integration
   - Tests all agent types (weather, calculator, greeting)
   - Captures full request/response cycles

2. **`telemetry/capture_test_telemetry.py`**
   - Captures telemetry during test execution
   - Saves to timestamped JSON files
   - Shows real-time test progress

3. **`telemetry/get_telemetry_simple.py`**
   - Queries Application Insights for recent traces
   - Filters for agent-related activity
   - Exports to JSON format

4. **`telemetry/analyze_telemetry_traces.py`**
   - Parses captured telemetry JSON
   - Groups by thread and shows flow
   - Identifies delegations and tool calls

### Utility Scripts

5. **`telemetry/show_telemetry_summary.py`**
   - Quick summary of recent telemetry
   - Shows counts and basic statistics

6. **`telemetry/view_telemetry.py`**
   - Interactive telemetry viewer
   - Displays formatted trace details

## Telemetry Data Structure

### Trace Properties

Each trace contains:
- `gen_ai.system`: "az.ai.agents"
- `gen_ai.thread.id`: Thread identifier
- `gen_ai.agent.id`: Agent assistant ID
- `gen_ai.thread.run.id`: Run identifier
- `gen_ai.usage.input_tokens`: Input token count
- `gen_ai.usage.output_tokens`: Output token count

### Tool Call Events

Delegation events include:
```json
{
  "tool_calls": [{
    "id": "call_[unique_id]",
    "type": "connected_agent"
  }]
}
```

## Troubleshooting

### Issue: No Telemetry Data

1. Check environment variable:
   ```bash
   echo $APPLICATIONINSIGHTS_CONNECTION_STRING
   ```

2. Verify workspace access:
   ```bash
   az account show
   ```

3. Check for recent data:
   ```bash
   python3 telemetry/get_telemetry_simple.py
   ```

### Issue: Authentication Errors

1. Refresh Azure credentials:
   ```bash
   az login
   ```

2. Check DefaultAzureCredential:
   ```python
   from azure.identity import DefaultAzureCredential
   cred = DefaultAzureCredential()
   token = cred.get_token("https://api.loganalytics.io/.default")
   ```

### Issue: Empty Query Results

1. Extend time range in query scripts
2. Check Application Insights data ingestion delay (usually 2-5 minutes)
3. Verify correct workspace ID

## Advanced Features

### Real-time Monitoring
Watch telemetry as it streams in:
```bash
python3 telemetry/show_recent_telemetry.py --follow
```

### Custom Dashboards
Create Application Insights dashboards for:
- Agent performance by type
- Delegation success rates
- Tool usage patterns
- Error rate trends

### Alerts Configuration
Set up alerts for:
- Failed delegations
- Slow response times (>10s)
- High error rates
- Unusual traffic patterns

### Export for Analysis
Export telemetry data for:
- Power BI reports
- Machine learning analysis
- Cost optimization studies
- Performance benchmarking

## Example Workflow

1. Deploy agents:
   ```bash
   python3 deploy_stratos_connected_agents.py
   ```

2. Run telemetry test:
   ```bash
   python3 telemetry/test_connected_agents_telemetry.py
   ```

3. Wait 2-3 minutes for ingestion

4. Query and analyze:
   ```bash
   python3 telemetry/get_telemetry_simple.py
   python3 telemetry/analyze_telemetry_traces.py
   ```

5. Review results:
   - Check delegation success rate
   - Verify announcement protocols
   - Monitor response times
   - Track token usage

This complete workflow ensures full visibility into the multi-agent system's behavior and performance.