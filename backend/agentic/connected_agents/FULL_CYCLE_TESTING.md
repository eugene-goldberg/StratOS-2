# Full Cycle Testing Scripts

This directory contains automated scripts for running the complete connected agents testing cycle with telemetry.

## Scripts

### 1. `full_cycle.sh` - Basic Full Cycle Test
Simple script that runs the complete test cycle with default settings.

```bash
./full_cycle.sh
```

**What it does:**
1. Undeploys all existing agents
2. Redeploys connected agents (Greeter, Calculator, Weather, Orchestrator)
3. Runs full test suite
4. Waits 2 minutes for telemetry ingestion
5. Collects telemetry from Application Insights
6. Analyzes telemetry data and displays results

### 2. `full_cycle_detailed.sh` - Advanced Full Cycle Test
Feature-rich script with options, logging, and detailed output.

```bash
# Show help
./full_cycle_detailed.sh --help

# Quick mode (30 second wait)
./full_cycle_detailed.sh --quick

# Skip undeploy (use existing agents)
./full_cycle_detailed.sh -s undeploy

# Custom wait time with verbose output
./full_cycle_detailed.sh -w 180 -v

# Skip multiple steps
./full_cycle_detailed.sh -s undeploy -s deploy
```

**Features:**
- Command line options for customization
- Verbose mode for detailed output
- Skip individual steps
- Comprehensive logging to `logs/` directory
- Progress indicators
- Error handling and prerequisites checking

## Expected Output

A successful run will show:
```
✅ All agents successfully removed
✅ All agents successfully deployed
✅ All tests completed successfully
✅ Telemetry data collected successfully
✅ Telemetry analysis completed
```

## Telemetry Analysis

The scripts will analyze and display:
- Number of connected agent delegations
- Tool call patterns
- Token usage statistics
- Thread and trace information
- Response times

## Logs

The detailed script saves all output to:
- `logs/full_cycle_[timestamp].log` - Complete execution log
- `logs/test_output_[timestamp].txt` - Test execution details
- `logs/telemetry_analysis_[timestamp].txt` - Telemetry analysis
- `logs/deployment_info_[timestamp].json` - Agent deployment info

## Prerequisites

Before running:
1. Ensure `.env` file exists with Azure credentials
2. Python 3 installed with required packages
3. Application Insights connection string configured
4. Azure CLI authenticated (if needed)

## Troubleshooting

If the scripts fail:
1. Check the logs in the `logs/` directory
2. Verify Azure credentials in `.env`
3. Ensure Application Insights is accessible
4. Try running with verbose mode: `./full_cycle_detailed.sh -v`
5. Check individual component scripts work:
   - `python3 deploy_connected_agents.py`
   - `python3 test_quick_deployed.py`
   - `python3 telemetry/get_telemetry_simple.py`

## Quick Test

For a quick verification without waiting for telemetry:
```bash
./full_cycle_detailed.sh --quick -s telemetry
```

This runs deployment and tests only, skipping the telemetry collection.