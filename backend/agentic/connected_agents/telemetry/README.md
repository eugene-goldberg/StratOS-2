# Telemetry Scripts Directory

This directory contains all telemetry-related scripts and data files for the Connected Agents system.

## Quick Start

1. **Run tests with telemetry**:
   ```bash
   python3 test_connected_agents_telemetry.py
   ```

2. **Query recent telemetry**:
   ```bash
   python3 get_telemetry_simple.py
   ```

3. **Analyze captured data**:
   ```bash
   python3 analyze_telemetry_traces.py
   ```

## Main Scripts

- `test_connected_agents_telemetry.py` - Main test runner with telemetry
- `capture_test_telemetry.py` - Capture telemetry during tests
- `get_telemetry_simple.py` - Query Application Insights
- `analyze_telemetry_traces.py` - Analyze delegation flows
- `show_telemetry_summary.py` - Quick telemetry summary
- `view_telemetry.py` - Interactive trace viewer

## Data Files

All JSON files in this directory contain captured telemetry data with timestamps.

For detailed instructions, see `../TELEMETRY_GUIDE.md`