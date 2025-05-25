Always use python3 instead of python
Always use python3 virtual environment for running tests

## IMPORTANT: Phase 1 Implementation Guidance
**PRIMARY DOCUMENTS FOR PHASE 1:**
- Always read **docs/phase_1_architecture.md** FIRST - this is the authoritative guide for Phase 1 Unified MAS architecture
- Always read **docs/phase_1_todo.md** to understand current implementation tasks and priorities
- Always read **docs/phase_1_status.md** to track implementation progress and completion status

## IMPORTANT: Documentation Update Protocol for Phase 1
After completing ANY task or making significant progress:
1. Update **docs/phase_1_todo.md** - mark completed items with ✅ and date
2. Update **docs/phase_1_status.md** - update progress percentages and component status
3. Update completion date (e.g., "✅ COMPLETED (May 25)") for tracking
4. Ensure both Phase 1 documents are consistent with each other

## Reference Documents (For Context Only)
These documents provide background but Phase 1 documents take precedence:
- docs/implementation_status.md - Historical implementation status
- docs/azure_ai_foundry_integration_plan.md - Original 3-system architecture (Phase 2+)
- docs/multi_agent_best_practices.md - General implementation guidelines
- backend/agentic/AGENT_DEPLOYMENT_SUCCESS.md - Agent deployment details
- backend/agentic/scripts/INTERACTION_SCRIPTS_README.md - Agent interaction scripts

This ensures accurate progress tracking and session continuity for Phase 1 implementation.

# StratOS Project-Specific Instructions

## IMPORTANT: Azure Deployment Strategy
**DO NOT use Azure OpenAI Assistants API for any deployments.** StratOS agents must be deployed to Azure AI Agent Service (part of Azure AI Studio) within an AI Project. 

**SUCCESS UPDATE (May 25, 2025)**: All 15 StratOS agents have been successfully deployed to Azure AI Agent Service! 100% of agents are tested and responding correctly. See `backend/agentic/AGENT_DEPLOYMENT_SUCCESS.md` for details on deployment and interaction.

## Current Architecture Direction: Phase 1 Unified MAS
**PHASE 1 FOCUS**: StratOS is implementing a **Unified Multi-Agent System (MAS)** architecture as the first phase of migration to Azure AI Foundry Agent Service. This approach simplifies initial deployment while preparing for future evolution.

**Phase 1**: Single Unified MAS containing all 15 agents with a Main Orchestrator
**Future Phases**: Evolution to 3 specialized systems based on usage patterns and requirements

See `docs/phase_1_architecture.md` for current architecture.
See `docs/phase_1_todo.md` for implementation tasks.
See `docs/phase_1_status.md` for progress tracking.

## IMPORTANT: Backend Development Location
ALL backend development work takes place exclusively under `/backend/agentic/`
- The `/backend/legacy/` folder contains the old implementation for reference only
- Do NOT modify or create files in `/backend/legacy/`
- All new backend code, APIs, and agent implementations go in `/backend/agentic/`

## Testing
- Run backend tests: `cd /path/to/project && source venv/bin/activate && python -m pytest tests/`
- Run frontend tests: `cd frontend && npm test`
- Run strategic canvas tests: `cd frontend/strategic-canvas && npm test`
- Test Docker locally: `cd backend/agentic && ./scripts/test_docker_locally.sh`
- CI workflows must pass before committing

## Architecture Patterns
### Current State (Updated May 24, 2025)
- Backend uses FastAPI with dependency injection for user context
- All services use Cosmos DB with fallback to in-memory storage
- AI features use Semantic Kernel with **plugin architecture** (@kernel_function decorators)
- **Orchestration pattern** implemented with function calling capabilities
- Frontend uses React with TypeScript, Material UI, and Zustand for state

### Target State - Phase 1 (In Progress)
- FastAPI will communicate with Azure AI Foundry Agent Service (Unified MAS)
- Single Main Orchestrator routing to all 15 agents
- Connected Agents for intra-system communication
- Agents deployed as managed services with built-in persistence
- Deterministic routing initially, LLM-based routing as future enhancement

## Azure Integration Status (Updated May 24, 2025)
- Cosmos DB is fully integrated and working
- **Azure OpenAI** is now configured with real credentials from semantic_kernel_multi_agent project
- AI services (Speech, Search) currently mocked - migration to Agent Service in progress
- Check backend/agentic/config/settings.py and .env for environment variables
- Real Azure OpenAI endpoint: https://sk-multi-agent-openai.openai.azure.com/

## Development Workflow - Phase 1 (Updated May 25, 2025)
- **Phase 1 Focus**: Implement Unified MAS with Main Orchestrator
- **Current Status**: 10% complete - agents deployed but not integrated
- **Immediate Priority**: Implement Main Orchestrator with deterministic routing
- **Next Steps**: FastAPI integration layer for Unified MAS
- Use TodoWrite/TodoRead tools to track implementation progress
- Check docs/phase_1_status.md for detailed completion status

## New Agent Development Patterns (From semantic_kernel_multi_agent)
- Create plugins with @kernel_function decorators in `/backend/agentic/agents/*/plugins/`
- Use KernelPlugin.from_object() for plugin registration
- Implement orchestration with AgentOrchestrator for function calling
- Deploy agents using: `bash backend/agentic/scripts/deploy_stratos_agents.sh`
- Test orchestration: `python backend/agentic/scripts/test_orchestration.py`

## Azure Deployment (NEW - May 24)
- Test Docker locally: `cd backend/agentic && ./scripts/test_docker_locally.sh`
- Deploy to Azure: `cd backend/agentic && ./scripts/deploy_to_azure_container_apps.sh`
- Interact with deployed app: `python backend/agentic/scripts/interact_with_azure_app.py health`
- View logs: `az containerapp logs show -n stratos-fastapi -g stratos-container-apps-rg`
- Update deployment: `./scripts/deploy_to_azure_container_apps.sh --tag v1.0.1`
- See `backend/agentic/DEPLOYMENT_GUIDE.md` for detailed instructions

## Common Pitfalls to Avoid
- Don't use 'python' command - always use 'python3'
- Don't install packages globally - always use virtual environment
- Don't modify Azure container names - they're hardcoded in services
- Don't assume AI services are connected - check for mock implementations
- Don't modify existing Semantic Kernel skills - they'll be packaged into agents

## Key Files for Phase 1 Implementation
### Primary Phase 1 Documents
- **docs/phase_1_architecture.md** - Phase 1 Unified MAS architecture guide
- **docs/phase_1_todo.md** - Phase 1 implementation tasks and priorities
- **docs/phase_1_status.md** - Phase 1 progress tracking

### Supporting Files
- backend/agentic/AGENT_DEPLOYMENT_SUCCESS.md - Agent deployment status
- backend/agentic/scripts/INTERACTION_SCRIPTS_README.md - Agent interaction scripts
- backend/agentic/scripts/test_all_agents.py - Agent testing scripts
- backend/agentic/DEPLOYMENT_GUIDE.md - Azure Container Apps deployment
- backend/ai/kernel_service.py - AI orchestration (being migrated)
- backend/ai/skills/* - Semantic Kernel skills (being packaged as agents)

### Reference Documents (Historical Context)
- docs/implementation_status.md - Pre-Phase 1 status
- docs/azure_ai_foundry_integration_plan.md - Original 3-system plan (future phases)
- docs/azure_ai_foundry_todo.md - Original migration tasks
- mvp_status.md - MVP feature tracking