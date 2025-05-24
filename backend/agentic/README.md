# StratOS Multi-Agent System (Agentic Backend)

This directory contains the new multi-agent system implementation using Azure AI Foundry Agent Service and Semantic Kernel.

## Architecture Overview

The system is organized into 3 multi-agent systems:

### 1. Strategic Foundation & Insights System (WHY/WHAT)
- **Router**: StrategicContextRouter
- **Agents**:
  - CEOLogAgent: Handles CEO log entries, voice transcription, tagging
  - NorthStarAgent: Manages vision, values, and strategic goals
  - MemoryRecallAgent: Context retrieval and pattern recognition
  - PreferenceLearningAgent: User preference tracking and personalization

### 2. Analysis & Intelligence System (ANALYZE)
- **Router**: AnalysisOrchestrator
- **Agents**:
  - SWOTTOWSAgent: Guided SWOT/TOWS analysis
  - RiskOpportunityAgent: Risk detection and opportunity identification
  - SOLinkageAgent: Subjective-Objective data linkage

### 3. Planning & Execution System (PLAN/HOW)
- **Router**: PlanningCoordinator
- **Agents**:
  - InitiativeGenerationAgent: Creates strategic initiatives
  - ResourceOptimizationAgent: Resource allocation and optimization
  - CanvasVisualizationAgent: Strategic canvas operations
  - AlignmentScoringAgent: Strategic alignment scoring
  - ActionPlanningAgent: Task breakdown and planning

## Directory Structure

```
agentic/
├── common/                    # Shared components
│   ├── base_agent.py         # Base agent classes
│   └── agent_group_chat.py   # Group chat implementation
├── agents/                   # Agent implementations
│   ├── strategic_foundation/ # System 1 agents
│   ├── analysis_intelligence/# System 2 agents
│   └── planning_execution/   # System 3 agents
├── strategies/              # Selection and termination strategies
├── clients/                 # AI Foundry client implementations
├── core/                    # Core services and utilities
└── examples/                # Usage examples
```

## Key Components

### BaseStratosAgent
Base class for all agents following Semantic Kernel patterns:
- Integrates with ChatCompletionAgent
- Supports plugins/skills
- Provides standard invoke patterns

### RouterAgent
Base class for routing agents:
- Routes requests to specialized agents
- Supports LLM-based routing decisions
- Manages agent orchestration

### StratosAgentGroupChat
Wrapper for Semantic Kernel AgentGroupChat:
- Manages multi-agent conversations
- Supports selection and termination strategies
- Handles conversation flow

## Usage Example

```python
# Set up Strategic Foundation system
system = await setup_strategic_foundation_system()

# Process a CEO log entry
request = {
    "type": "ceo_log",
    "action": "create_entry",
    "data": {
        "text": "Strategic planning meeting notes...",
        "category": "strategic_planning"
    }
}

result = await system["router"].process_request(request)
```

## Migration Status

This is the new architecture being implemented to replace the legacy backend.
See `/backend/legacy/` for the current implementation being migrated.

## Dependencies

Key dependencies (see requirements.txt):
- semantic-kernel>=1.0.0
- azure-ai-inference>=1.0.0b1
- azure-identity>=1.15.0
- fastapi>=0.109.0

## Next Steps

1. Complete remaining agent implementations
2. Integrate with Azure AI Foundry Agent Service
3. Set up cross-system communication via Azure Service Bus
4. Migrate existing skills to new agent architecture
5. Update FastAPI endpoints to use new agents