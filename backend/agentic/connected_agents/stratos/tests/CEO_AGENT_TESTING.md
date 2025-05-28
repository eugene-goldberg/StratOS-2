# CEO Log Agent Testing

## Test Scripts

### 1. `test_ceo_simple.py` 
**Purpose**: Quick smoke test  
**Run time**: ~30 seconds  
**Usage**: 
```bash
python test_ceo_simple.py
```
Tests basic delegation from orchestrator to CEO Log Agent.

### 2. `test_ceo_comprehensive.py`
**Purpose**: Full functionality test with telemetry  
**Run time**: ~2-3 minutes  
**Usage**:
```bash
python test_ceo_comprehensive.py
```
Tests all CEO Log functions (GenerateTags, SaveEntry, ExtractInsights, etc.) and captures telemetry evidence.

## Test Outputs

All test outputs are saved to `test_outputs/ceo_agent/`:
- Telemetry JSON files
- Test execution logs
- Evidence summaries

## Utility Scripts

Located in `../telemetry/`:
- Query and capture scripts for telemetry data

## Running Tests

For quick verification:
```bash
python test_ceo_simple.py
```

For full testing with evidence:
```bash
python test_ceo_comprehensive.py
```

## Agent IDs
- CEO Log Agent: `asst_T3KtZ9Qfg7Z78PRmL9wuJPlX`
- StratOS Orchestrator: `asst_ChNCt7uB1rt88oWfS9YPdAQh`