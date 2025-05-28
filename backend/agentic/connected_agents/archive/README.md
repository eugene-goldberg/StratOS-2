# Archive - Connected Agents Development Scripts

This folder contains intermediate scripts used during the development and debugging of the connected agents system.

## Scripts Overview

### Initial Deployment and Testing
- `main_deployment_script.py` - Original deployment script for single greeter agent (superseded by deploy_connected_agents.py)
- `main_deployment_script_updated.py` - Updated version with improvements
- `simple_test_invoke.py` - Simple test for orchestrator delegation
- `verify_working_system.py` - System verification script
- `quick_test.py` - Quick testing utilities

### Orchestrator Fixes
- `fix_orchestrator_instructions.py` - First attempt at fixing delegation
- `redeploy_with_better_instructions.py` - Improved orchestrator instructions
- `orchestrator_agent_config.py` - Original orchestrator configuration

### Calculator Agent Development
- `debug_calculation_delegation.py` - Debugging why calculator announcements weren't working
- `fix_calculator_announcement.py` - Script that successfully fixed the announcement issue
- `verify_delegation_announcements.py` - Verification of announcement behavior
- `test_simple_calc.py` - Simple calculator delegation test
- `verify_delegation.py` - General delegation verification

### Utilities
- `get_current_agents.py` - Utility to list deployed agents and get their IDs
- `test_tool_calling.py` - Testing tool calling functionality

## Note
These scripts were kept for historical reference and debugging purposes. The active deployment and testing scripts are in the parent directory.