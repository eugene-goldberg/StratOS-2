# StratOS Telemetry Consolidation Documentation

## Overview
The StratOS telemetry system has been consolidated to provide a unified approach for capturing, storing, and analyzing telemetry data across all connected agents. This eliminates code duplication and provides consistent telemetry patterns.

## Architecture

### Core Components

#### 1. `TelemetryCapture` Class (`telemetry/telemetry_capture.py`)
Central telemetry management with:
- Automatic session ID generation
- Standardized event structure
- Application Insights integration
- JSON persistence
- Summary reporting

#### 2. `BaseAgentTest` Class (`tests/base_agent_test.py`)
Base class for all agent tests providing:
- Deployment info management
- Client initialization
- Query/response handling
- Delegation detection
- Test orchestration

#### 3. Unified Test Scripts
- `test_all_agents_unified.py` - Test all agents with one command
- Individual agent test classes inheriting from `BaseAgentTest`

## Key Features

### 1. Standardized Event Types
```python
- telemetry_configured     # System setup
- deployment_loaded        # Deployment info loaded
- orchestrator_fetch_start # Starting to fetch orchestrator
- orchestrator_fetch_complete # Orchestrator loaded with tools
- query_sent              # Query sent to agent
- response_received       # Response from agent
- delegation_confirmed    # Delegation detected
- error                   # Error occurred
- test_complete          # Test finished
```

### 2. Automatic Delegation Detection
The system automatically detects delegation patterns for all StratOS agents:
- CEO Log Specialist
- North Star Specialist  
- Memory Recall Specialist
- (Extensible for future agents)

### 3. Unified Telemetry Storage
All telemetry is stored in a consistent format:
```
stratos/telemetry/
├── ceo_log_agent/
│   └── ceo_log_agent_telemetry_[timestamp]_[session].json
├── north_star_agent/
│   └── north_star_agent_telemetry_[timestamp]_[session].json
└── memory_recall_agent/
    └── memory_recall_agent_telemetry_[timestamp]_[session].json
```

## Usage Examples

### 1. Test All Agents (Simple)
```bash
python test_all_agents_unified.py
```

### 2. Test All Agents (Comprehensive)
```bash
python test_all_agents_unified.py --type comprehensive
```

### 3. Test Single Agent
```bash
# Test only CEO Log agent
python test_all_agents_unified.py --agent ceo --type simple

# Test only Memory Recall agent comprehensively
python test_all_agents_unified.py --agent memory --type comprehensive
```

### 4. Create New Agent Test
```python
from base_agent_test import BaseAgentTest

class MyNewAgentTest(BaseAgentTest):
    def __init__(self):
        super().__init__("My New Agent")
    
    def get_test_scenarios(self):
        return [
            {
                "name": "scenario_1",
                "query": "Test query for scenario 1"
            }
        ]

# Run the test
test = MyNewAgentTest()
await test.run_comprehensive_test()
```

## Migration Guide

### Converting Existing Tests
1. Import the base class:
   ```python
   from base_agent_test import BaseAgentTest
   ```

2. Inherit from `BaseAgentTest`:
   ```python
   class MyAgentTest(BaseAgentTest):
       def __init__(self):
           super().__init__("My Agent Name")
   ```

3. Define test scenarios:
   ```python
   def get_test_scenarios(self):
       return [{"name": "test", "query": "test query"}]
   ```

4. Use built-in test runners:
   ```python
   await test.run_simple_test()
   await test.run_comprehensive_test()
   ```

## Telemetry Data Structure

### Event Format
```json
{
  "timestamp": "2025-05-28T18:00:00.000000",
  "session_id": "uuid-here",
  "event_type": "query_sent",
  "data": {
    "query": "User query text",
    "target": "agent_name",
    "function": "expected_function"
  }
}
```

### Session File Format
```json
{
  "session_id": "uuid-here",
  "agent_name": "Agent Name",
  "capture_time": "2025-05-28T18:00:00.000000",
  "events": [
    {
      "event_type": "...",
      "data": {...},
      "timestamp": "...",
      "session_id": "..."
    }
  ]
}
```

## Benefits of Consolidation

1. **Code Reuse**: Eliminated ~70% code duplication across test scripts
2. **Consistency**: All agents tested with same patterns and telemetry
3. **Maintainability**: Single source of truth for telemetry logic
4. **Extensibility**: Easy to add new agents and test scenarios
5. **Analysis**: Unified format enables cross-agent telemetry analysis

## Future Enhancements

1. **Real-time Dashboard**: Web interface for live telemetry viewing
2. **Automated Analysis**: ML-based pattern detection in telemetry
3. **Performance Metrics**: Response time and throughput tracking
4. **Alert System**: Automatic alerts for delegation failures
5. **Telemetry Aggregation**: Cross-session analysis and reporting

## Troubleshooting

### Common Issues

1. **No deployment info found**
   - Ensure agents are deployed first
   - Check `stratos/archive/stratos_deployment_info.json` exists

2. **No delegation detected**
   - Verify orchestrator has correct instructions
   - Check agent is included in orchestrator tools
   - Review delegation patterns in telemetry

3. **Application Insights not working**
   - Verify `APPLICATION_INSIGHTS_CONNECTION_STRING` in .env
   - Check network connectivity to Azure

### Debug Mode
Set logging to DEBUG for detailed output:
```python
logging.basicConfig(level=logging.DEBUG)
```

## API Reference

### TelemetryCapture
- `capture_event(event_type, data)` - Log an event
- `capture_query(query, target, function)` - Log a query
- `capture_response(response, scenario)` - Log response and detect delegation
- `capture_error(message, context)` - Log an error
- `save(base_dir)` - Save telemetry to JSON
- `get_summary()` - Get telemetry statistics
- `print_summary()` - Print formatted summary

### BaseAgentTest
- `load_deployment_info()` - Load deployment configuration
- `create_agent_client()` - Initialize AI client
- `invoke_agent(agent, query, scenario)` - Send query and capture response
- `run_simple_test()` - Run single test scenario
- `run_comprehensive_test()` - Run all test scenarios
- `get_test_scenarios()` - Abstract method for test definition