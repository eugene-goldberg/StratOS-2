# StratOS Multi-Agent System (Agentic Backend)

This directory contains the new multi-agent system implementation using Azure AI Foundry Agent Service and Semantic Kernel.

**Status**: FastAPI backend ready for deployment, 3 of 15 agents implemented (May 24, 2025)

**Status**: FastAPI backend implemented and deployable to Azure Container Apps. Agent migration 20% complete (3 of 15 agents).

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
│   ├── agent_group_chat.py   # Group chat implementation
│   └── orchestration.py      # Function calling orchestration
├── agents/                   # Agent implementations
│   ├── strategic_foundation/ # System 1 agents
│   │   ├── plugins/          # Plugin implementations
│   │   ├── ceo_log_agent.py  # ✅ Implemented
│   │   ├── north_star_agent.py # ✅ Implemented
│   │   └── router.py         # ✅ Implemented
│   ├── analysis_intelligence/# System 2 agents (pending)
│   └── planning_execution/   # System 3 agents (pending)
├── api/                      # FastAPI routes and middleware
├── config/                   # Configuration management
├── scripts/                  # Deployment and testing scripts
├── services/                 # Service layer
├── Dockerfile                # Production Docker build
├── docker-compose.yml        # Local development
└── DEPLOYMENT_GUIDE.md       # Deployment documentation
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

## Getting Started

### Local Development

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set up environment variables:
   ```bash
   # .env file already configured with Azure credentials
   ```

3. Run the FastAPI backend:
   ```bash
   uvicorn main:app --reload
   ```

### Docker Development

1. Test with Docker locally:
   ```bash
   ./scripts/test_docker_locally.sh
   ```

2. Run with Docker Compose:
   ```bash
   docker-compose up
   ```

### Deploy to Azure

1. Deploy to Azure Container Apps:
   ```bash
   ./scripts/deploy_to_azure_container_apps.sh
   ```

2. Test deployed app:
   ```bash
   python scripts/interact_with_azure_app.py health
   ```

See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for detailed deployment instructions.

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

## Deployment

### Quick Start

```bash
# Test locally with Docker
./scripts/test_docker_locally.sh

# Deploy to Azure Container Apps
./scripts/deploy_to_azure_container_apps.sh

# Test deployed app
python scripts/interact_with_azure_app.py health
```

### Deployment Tools
- `scripts/deploy_to_azure_container_apps.sh` - One-command Azure deployment
- `scripts/interact_with_azure_app.py` - CLI for testing deployed app
- `scripts/test_docker_locally.sh` - Local Docker testing
- See `DEPLOYMENT_GUIDE.md` for complete instructions

## Migration Status

This is the new architecture being implemented to replace the legacy backend.
- **Completed**: Plugin architecture, orchestration, Azure deployment tools
- **In Progress**: Strategic Foundation System (60% - 3 of 5 agents)
- **Pending**: Analysis & Intelligence System, Planning & Execution System
- See `agentic_implementation_status.md` for detailed progress

### Current Implementation Progress:
- **FastAPI Backend**: ✅ Complete and deployable
- **Plugin Architecture**: ✅ Implemented with @kernel_function decorators
- **Orchestration**: ✅ Function calling framework ready
- **Strategic Foundation System**: 60% (3/5 agents implemented)
- **Analysis & Intelligence System**: 0% (0/4 agents)  
- **Planning & Execution System**: 0% (0/6 agents)
- **Overall Progress**: 20% (3/15 agents implemented)

## Key Patterns Adopted

### Plugin Architecture
Adopted from semantic_kernel_multi_agent project:
- Plugins use `@kernel_function` decorators
- Registration via `KernelPlugin.from_object()`
- See `agents/strategic_foundation/plugins/` for examples

### Orchestration
- Function calling pattern for agent delegation
- `AgentOrchestrator` class handles orchestration
- Supports Azure OpenAI function calling format

### Deployment
- Docker multi-stage build for production
- Azure Container Apps with auto-scaling
- Environment-based configuration

## Dependencies

Key dependencies (see requirements.txt):
- semantic-kernel>=1.0.0
- azure-ai-inference>=1.0.0b1
- azure-identity>=1.15.0
- fastapi>=0.109.0
- uvicorn[standard]>=0.27.0

## Next Steps

1. Complete remaining Strategic Foundation agents (Memory & Preference)
2. Implement Analysis & Intelligence System (4 agents)
3. Implement Planning & Execution System (6 agents)
4. Integrate with Azure AI Foundry Agent Service
5. Set up cross-system communication via Azure Service Bus

## Key Resources

- [Implementation Status](agentic_implementation_status.md) - Detailed progress tracking
- [Adoption Plan](adoption_plan.md) - Guide for semantic_kernel_multi_agent patterns
- [Deployment Guide](DEPLOYMENT_GUIDE.md) - Azure Container Apps deployment
- [API Documentation](http://localhost:8000/docs) - Interactive API docs (when running)

## Testing

### Unit Tests
```bash
pytest tests/
```

### Integration Tests
```bash
# Test orchestration locally
python scripts/test_orchestration.py

# Test Docker build
./scripts/test_docker_locally.sh
```

### Deployment Testing
```bash
# Deploy agents to Azure
./scripts/deploy_stratos_agents.sh

# Test deployed FastAPI app
python scripts/interact_with_azure_app.py health
```