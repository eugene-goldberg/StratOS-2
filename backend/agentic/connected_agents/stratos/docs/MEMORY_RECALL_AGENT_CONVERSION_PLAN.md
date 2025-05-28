# Memory Recall Agent Connected Agent Conversion Plan

## Overview
Convert the existing Memory Recall Agent from the StratOS system to a connected agent following the exact pattern used for CEO Log Agent and Weather Agent.

## Current State Analysis

### 1. Locate Existing Memory Recall Agent Implementation
- **Location**: `/backend/agentic/stratos_agents/strategic_foundation/memory_recall_agent.py`
- **Plugin**: `/backend/agentic/stratos_agents/strategic_foundation/plugins/memory_plugin.py`
- **Current Functions**:
  - Retrieve context based on semantic queries
  - Recognize patterns in historical data
  - Analyze historical trends and evolution
  - Store important context for future retrieval
  - Find similar situations or decisions

## Conversion Steps

### Phase 1: Create Connected Agent Configuration (30 minutes)

#### 1.1 Create `memory_recall_agent_config.py`
```python
"""
Memory Recall Agent Configuration
Semantic memory, context retrieval, and pattern recognition specialist
"""

AGENT_NAME_PREFIX = "MemoryRecallAgent"

AGENT_INSTRUCTIONS = """You are the Memory Recall Agent for StratOS, specializing in organizational memory management and intelligent context retrieval.

You have access to powerful tools for managing memory and insights:

Available functions:
- RetrieveContext: Search for relevant information based on semantic queries
- RecognizePatterns: Identify patterns, trends, and correlations in historical data
- AnalyzeHistory: Perform historical analysis on strategic data
- StoreContext: Save important information for future retrieval
- FindSimilar: Locate similar situations or decisions from history

Key behaviors:
- Always search for relevant context before making recommendations
- Identify patterns that could inform current decisions
- Highlight lessons learned from similar past situations
- Maintain connections between related pieces of information
- Provide evidence-based insights from historical data

When responding:
- Cite specific examples from memory when relevant
- Highlight patterns or trends you've identified
- Connect current situations to historical precedents
- Suggest lessons learned from past experiences
- Be explicit about confidence levels in pattern recognition

Context types you manage:
- CEO log entries
- North Star vision/mission/goals
- Strategic decisions and outcomes
- Risk assessments and opportunities
- Planning artifacts and initiatives
- Performance metrics and KPIs

Pattern types you can detect:
- Frequency patterns (recurring themes, periodic activities)
- Trends (increasing, decreasing, cyclical)
- Correlations between different data types
- Anomalies and outliers

Remember: Your role is to be the organizational memory, helping leaders make informed decisions based on historical context and patterns."""

MODEL_NAME = "gpt-35-turbo"
TOOLS = []  # No tools for connected agents
```

#### 1.2 Create `memory_recall_plugin.py`
- Copy existing plugin functions from current implementation
- Ensure all functions use `@kernel_function` decorator
- Update function signatures to match connected agent pattern
- Return JSON strings from all functions
- Key functions to convert:
  - `retrieve_context()` - Search semantic memory
  - `recognize_patterns()` - Pattern analysis
  - `analyze_history()` - Historical analysis
  - `store_context()` - Store new memories
  - `find_similar()` - Similarity search

### Phase 2: Update Orchestrator Configuration (15 minutes)

#### 2.1 Update `orchestrator_agent_config.py`
Add Memory Recall delegation protocol:
```python
"DIRECTIVE 4: MEMORY RECALL DELEGATION PROTOCOL "
"For ANY memory search, pattern recognition, historical analysis, or context retrieval request: "
"   STEP 4.1: First say EXACTLY: 'I'll connect you with the Memory Recall specialist for historical insights!' "
"   STEP 4.2: Then invoke the 'memory_recall_specialist' tool "
"   STEP 4.3: Present the tool's output as provided "
```

### Phase 3: Create Deployment Script (20 minutes)

#### 3.1 Update `deploy_stratos_connected_agents.py`
Add Memory Recall agent deployment:
```python
# Deploy Memory Recall Agent
memory_recall_agent_name = f"{memory_recall_agent_config.AGENT_NAME_PREFIX}-{os.urandom(4).hex()}"
memory_recall_agent_def = await client.agents.create_agent(
    model=model_deployment_name,
    name=memory_recall_agent_name,
    instructions=memory_recall_agent_config.AGENT_INSTRUCTIONS,
    tools=memory_recall_agent_config.TOOLS
)

# Add Memory Recall tool to orchestrator
memory_recall_tool_description = (
    "A memory and pattern recognition specialist for organizational insights. "
    "Use this tool for searching historical context, identifying patterns, "
    "analyzing trends, storing important information, and finding similar past situations."
)
```

### Phase 4: Create Test Scripts (45 minutes)

#### 4.1 Create `test_memory_recall_simple.py`
Quick smoke test (~30 seconds):
- Test context retrieval
- Verify delegation announcement
- Check response format

#### 4.2 Create `test_memory_recall_comprehensive.py`
Full test with telemetry (~2-3 minutes):
- Test all 5 Memory Recall functions
- Capture telemetry for each function
- Verify delegation flow
- Save evidence to `test_outputs/memory_recall_agent/`

#### 4.3 Create `capture_memory_recall_telemetry.py`
Telemetry capture script:
- Test pattern recognition scenarios
- Test historical analysis
- Test similarity search
- Capture complete delegation evidence

### Phase 5: Execute Deployment and Testing (30 minutes)

#### 5.1 Deployment Steps
```bash
# 1. Run deployment script
python deployment/deploy_stratos_with_memory_recall.py

# 2. Capture deployment info
# Save agent IDs to archive/stratos_deployment_info.json
```

#### 5.2 Testing Protocol
```bash
# 1. Run simple test
python tests/test_memory_recall_simple.py

# 2. Run comprehensive test with telemetry
python tests/test_memory_recall_comprehensive.py

# 3. Capture telemetry evidence
python tests/capture_memory_recall_telemetry.py

# 4. Verify telemetry evidence
ls telemetry/memory_recall_agent/
```

### Phase 6: Documentation and Cleanup (20 minutes)

#### 6.1 Create `MEMORY_RECALL_AGENT_TESTING.md`
Document:
- Test scripts and their purposes
- Agent IDs
- Usage examples
- Expected outputs
- Pattern recognition examples
- Historical analysis scenarios

#### 6.2 Organize Files
```
stratos/
├── agents/
│   ├── memory_recall_agent_config.py
│   └── memory_recall_plugin.py
├── deployment/
│   └── deploy_stratos_with_memory_recall.py
├── tests/
│   ├── test_memory_recall_simple.py
│   ├── test_memory_recall_comprehensive.py
│   └── capture_memory_recall_telemetry.py
├── telemetry/
│   └── memory_recall_agent/
│       └── memory_recall_telemetry_*.json
└── docs/
    └── MEMORY_RECALL_AGENT_TESTING.md
```

## Success Criteria

1. **Deployment Success**:
   - Memory Recall Agent created with unique ID
   - Orchestrator updated with memory_recall_specialist tool
   - Deployment info saved with all 3 agents (CEO Log, North Star, Memory Recall)

2. **Delegation Working**:
   - Orchestrator announces "I'll connect you with the Memory Recall specialist"
   - Memory Recall functions execute correctly
   - Responses include historical insights and patterns

3. **Telemetry Evidence**:
   - All function calls tracked
   - Delegation flow captured
   - Pattern recognition results logged
   - Evidence files generated with session tracking

## Timeline
- **Total Duration**: ~2.5 hours
- **Phase 1**: 30 minutes (Configuration)
- **Phase 2**: 15 minutes (Orchestrator update)
- **Phase 3**: 20 minutes (Deployment script)
- **Phase 4**: 45 minutes (Test scripts)
- **Phase 5**: 30 minutes (Deploy & test)
- **Phase 6**: 20 minutes (Documentation)

## Risk Mitigation

1. **Memory Store Integration**: Agent currently expects Azure AI Search
   - Solution: Use mock data initially, plan for real memory store later
   - Plugin already handles missing memory store gracefully

2. **Complex Pattern Recognition**: Pattern algorithms may be sophisticated
   - Solution: Start with simple pattern types, enhance incrementally
   - Focus on frequency and trend patterns initially

3. **Data Volume**: Historical analysis may involve large datasets
   - Solution: Implement pagination and time-based filtering
   - Use mock data for initial testing

## Special Considerations

1. **Mock Data Strategy**:
   - Plugin already returns mock data when memory store unavailable
   - Ensure mock data is realistic and varied
   - Include different pattern types and historical scenarios

2. **Integration Points**:
   - Memory Recall works with CEO Log entries
   - Coordinates with North Star for strategic alignment
   - Will feed into analysis and planning agents

3. **Future Enhancements**:
   - Real Azure AI Search integration
   - Advanced ML-based pattern recognition
   - Predictive analytics based on historical patterns

## Next Steps After Memory Recall

Following the same pattern, convert these agents in order:
1. Preference Learning Agent (2-3 hours)
2. SWOT/TOWS Agent (2-3 hours)
3. Risk Opportunity Agent (2-3 hours)
4. SO Linkage Agent (2-3 hours)
5. Initiative Generation Agent (2-3 hours)
6. Action Planning Agent (2-3 hours)
7. Alignment Scoring Agent (2-3 hours)
8. Resource Optimization Agent (2-3 hours)
9. Canvas Visualization Agent (2-3 hours)

Each conversion should follow this established pattern with connected agents having no tools and using instruction-based delegation.