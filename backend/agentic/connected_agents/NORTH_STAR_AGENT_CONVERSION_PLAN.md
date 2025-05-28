# North Star Agent Connected Agent Conversion Plan

## Overview
Convert the existing North Star Agent from the StratOS system to a connected agent following the exact pattern used for CEO Log Agent and Weather Agent.

## Current State Analysis

### 1. Locate Existing North Star Agent Implementation
- **Location**: `/backend/agentic/stratos_agents/strategic_foundation/north_star_agent.py`
- **Plugin**: `/backend/agentic/stratos_agents/strategic_foundation/plugins/north_star_plugin.py`
- **Current Functions**:
  - Define vision and mission
  - Set strategic goals
  - Align objectives with vision
  - Track goal progress
  - Manage strategic priorities

## Conversion Steps

### Phase 1: Create Connected Agent Configuration (30 minutes)

#### 1.1 Create `north_star_agent_config.py`
```python
"""
North Star Agent Configuration
Vision, mission, and strategic goal management specialist
"""

AGENT_NAME_PREFIX = "NorthStarAgent"

AGENT_INSTRUCTIONS = """You are the North Star Agent for StratOS, specializing in vision, mission, and strategic goal management.

You have access to powerful tools for managing organizational North Star:

Available functions:
- DefineVision: Create or update organizational vision statement
- SetMission: Define the organization's mission
- CreateStrategicGoal: Add new strategic goals aligned with vision
- UpdateGoalProgress: Track progress on strategic goals
- GetAlignmentScore: Measure how well initiatives align with North Star
- GenerateOKRs: Create OKRs from strategic goals

[Detailed instructions following CEO Log pattern...]
"""

MODEL_NAME = "gpt-35-turbo"
TOOLS = []  # No tools for connected agents
```

#### 1.2 Create `north_star_plugin.py`
- Copy existing plugin functions from current implementation
- Ensure all functions use `@kernel_function` decorator
- Update function signatures to match connected agent pattern
- Return JSON strings from all functions

### Phase 2: Update Orchestrator Configuration (15 minutes)

#### 2.1 Update `orchestrator_agent_config.py`
Add North Star delegation protocol:
```python
"DIRECTIVE 3: NORTH STAR DELEGATION PROTOCOL "
"For ANY vision, mission, strategic goal, or alignment request: "
"   STEP 3.1: First say EXACTLY: 'I'll connect you with the North Star specialist for strategic alignment!' "
"   STEP 3.2: Then invoke the 'north_star_specialist' tool "
"   STEP 3.3: Present the tool's output as provided "
```

### Phase 3: Create Deployment Script (20 minutes)

#### 3.1 Update `deploy_stratos_connected_agents.py`
Add North Star agent deployment:
```python
# Deploy North Star Agent
north_star_agent_name = f"{north_star_agent_config.AGENT_NAME_PREFIX}-{os.urandom(4).hex()}"
north_star_agent_def = await client.agents.create_agent(
    model=model_deployment_name,
    name=north_star_agent_name,
    instructions=north_star_agent_config.AGENT_INSTRUCTIONS,
    tools=north_star_agent_config.TOOLS
)

# Add North Star tool to orchestrator
north_star_tool_description = (
    "A strategic alignment specialist for vision, mission, and goal management. "
    "Use this tool for defining organizational vision, setting mission statements, "
    "creating strategic goals, tracking progress, measuring alignment, and generating OKRs."
)
```

### Phase 4: Create Test Scripts (45 minutes)

#### 4.1 Create `test_north_star_simple.py`
Quick smoke test (~30 seconds):
- Test vision definition
- Verify delegation announcement
- Check response format

#### 4.2 Create `test_north_star_comprehensive.py`
Full test with telemetry (~2-3 minutes):
- Test all 6 North Star functions
- Capture telemetry for each function
- Verify delegation flow
- Save evidence to `test_outputs/north_star_agent/`

### Phase 5: Execute Deployment and Testing (30 minutes)

#### 5.1 Deployment Steps
```bash
# 1. Run deployment script
python deploy_stratos_connected_agents.py

# 2. Capture deployment info
# Save agent IDs to stratos_deployment_info.json
```

#### 5.2 Testing Protocol
```bash
# 1. Run simple test
python test_north_star_simple.py

# 2. Run comprehensive test with telemetry
python test_north_star_comprehensive.py

# 3. Verify telemetry evidence
ls test_outputs/north_star_agent/
```

### Phase 6: Documentation and Cleanup (20 minutes)

#### 6.1 Create `NORTH_STAR_AGENT_TESTING.md`
Document:
- Test scripts and their purposes
- Agent IDs
- Usage examples
- Expected outputs

#### 6.2 Organize Files
```
connected_agents/
├── north_star_agent_config.py
├── north_star_plugin.py
├── test_north_star_simple.py
├── test_north_star_comprehensive.py
├── test_outputs/
│   └── north_star_agent/
│       ├── telemetry_*.json
│       └── test_logs_*.log
└── NORTH_STAR_AGENT_TESTING.md
```

## Success Criteria

1. **Deployment Success**:
   - North Star Agent created with unique ID
   - Orchestrator updated with north_star_specialist tool
   - Deployment info saved

2. **Delegation Working**:
   - Orchestrator announces "I'll connect you with the North Star specialist"
   - North Star functions execute correctly
   - Responses include strategic guidance

3. **Telemetry Evidence**:
   - All function calls tracked
   - Delegation flow captured
   - Evidence files generated

## Timeline
- **Total Duration**: ~2.5 hours
- **Phase 1**: 30 minutes (Configuration)
- **Phase 2**: 15 minutes (Orchestrator update)
- **Phase 3**: 20 minutes (Deployment script)
- **Phase 4**: 45 minutes (Test scripts)
- **Phase 5**: 30 minutes (Deploy & test)
- **Phase 6**: 20 minutes (Documentation)

## Risk Mitigation

1. **Function Complexity**: North Star functions may be more complex than CEO Log
   - Solution: Start with simpler functions, add complexity incrementally

2. **State Management**: North Star requires persistent vision/mission storage
   - Solution: Use in-memory storage for MVP, plan for Cosmos DB later

3. **Alignment Calculations**: May require complex scoring algorithms
   - Solution: Implement simple scoring first, enhance later

## Next Steps After North Star

Following the same pattern, convert these agents in order:
1. Memory Recall Agent
2. Preference Learning Agent
3. SWOT/TOWS Agent
4. Risk Opportunity Agent
5. SO Linkage Agent
6. Initiative Generation Agent
7. Action Planning Agent
8. Alignment Scoring Agent
9. Resource Optimization Agent
10. Canvas Visualization Agent

Each conversion should take ~2-3 hours following this established pattern.