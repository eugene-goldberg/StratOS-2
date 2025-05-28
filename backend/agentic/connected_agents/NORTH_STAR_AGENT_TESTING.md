# North Star Agent Testing Documentation

## Overview
This document outlines the testing approach for the North Star Agent as a connected agent in the StratOS system.

## Agent Configuration
- **Config File**: `north_star_agent_config.py`
- **Plugin File**: `north_star_plugin.py`
- **Model**: GPT-3.5-turbo
- **Pattern**: Connected agent (no tools, used AS a tool by orchestrator)

## Available Functions
The North Star Agent provides these Semantic Kernel functions:
1. **ManagePurpose** - Get/set organizational purpose
2. **ManageVision** - Get/set vision statement
3. **ManageValues** - Add/remove/list organizational values
4. **ManageStrategicGoals** - Create/update goals with hierarchy
5. **ValidateAlignment** - Check alignment with North Star
6. **GetNorthStarSummary** - Complete strategic foundation overview

## Test Scripts

### 1. Simple Test (`test_north_star_simple.py`)
- Direct agent invocation
- Basic function testing
- Quick validation of deployment

### 2. Comprehensive Test (`test_north_star_comprehensive.py`)
- Direct agent testing
- Orchestrator delegation testing
- Telemetry tracking
- Full function coverage
- Delegation evidence verification

## Deployment Process
1. Create agent configuration with TOOLS = []
2. Update orchestrator configuration with North Star delegation rules
3. Deploy using `deploy_stratos_with_north_star.py`
4. Update environment variables with agent IDs

## Testing Approach
1. **Direct Testing**: Invoke North Star agent directly to verify functions
2. **Delegation Testing**: Test through orchestrator to verify routing
3. **Telemetry Verification**: Confirm delegation with telemetry traces
4. **Evidence Collection**: Look for delegation announcements

## Expected Delegation Evidence
When requests go through the orchestrator:
- Announcement: "I'll connect you with the North Star specialist for strategic foundation guidance!"
- Function call to `north_star_specialist`
- Telemetry showing orchestrator → North Star flow

## Key Test Scenarios
1. **Purpose Definition**: Help define organizational purpose
2. **Vision Creation**: Create aspirational vision statements
3. **Values Management**: Add and manage core values
4. **Goal Hierarchies**: Create strategic goals with parent-child relationships
5. **Alignment Validation**: Check if initiatives align with North Star
6. **Complete Summary**: Get full strategic foundation overview

## Success Criteria
- ✅ Agent deployed successfully
- ✅ Direct invocation works
- ✅ Orchestrator routes correctly
- ✅ All functions execute properly
- ✅ Telemetry captures delegation
- ✅ Responses are contextually appropriate

## Troubleshooting
1. **Missing Agent ID**: Check stratos_deployment_info.json
2. **Connection Errors**: Verify AZURE_AI_PROJECT_CONNECTION_STRING
3. **Routing Issues**: Check orchestrator instructions include North Star
4. **Function Errors**: Verify plugin is copied to connected_agents/

## Next Steps
After successful North Star deployment:
1. Convert Memory Recall Agent
2. Convert Preference Learning Agent
3. Update orchestrator with all strategic foundation agents
4. Test complete strategic foundation flow