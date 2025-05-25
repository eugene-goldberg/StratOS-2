Always use python3 instead of python
Always use python3 virtual environment for running tests
Always read docs/implementation_status.md to understand the current status of this project
Always read docs/azure_ai_foundry_integration_plan.md to understand the multi-agent architecture
Always read docs/azure_ai_foundry_todo.md to track agent migration progress
Always read docs/multi_agent_best_practices.md for implementation guidelines and patterns
Always read docs/Deep_Research_Multi-Agent_Systems_Azure_Best_Practices.md for research findings
Always read ToDo.md to understand current priorities and tasks
Always read backend/agentic/agentic_implementation_status.md to understand what is implemented and next steps
Always read backend/agentic/AGENT_DEPLOYMENT_SUCCESS.md to understand agent deployment status and interaction capabilities
Always read backend/agentic/scripts/INTERACTION_SCRIPTS_README.md to understand available agent interaction scripts
Always maintain close cohesion between ToDo.md and agentic_implementation_status.md - update both files when tasks are completed or priorities change, ensuring session continuity

## IMPORTANT: Documentation Update Protocol
After completing ANY task or making significant progress:
1. Update ToDo.md - mark completed items with ✅ and date
2. Update backend/agentic/agentic_implementation_status.md - update progress percentages and component status
3. Update docs/implementation_status.md - add major milestones and architecture changes
4. Ensure all three documents are consistent with each other
5. Include completion date (e.g., "✅ COMPLETED (May 24)") for tracking

This ensures accurate progress tracking and session continuity between different Claude sessions.

# StratOS Project-Specific Instructions

## IMPORTANT: Azure Deployment Strategy
**DO NOT use Azure OpenAI Assistants API for any deployments.** StratOS agents must be deployed to Azure AI Agent Service (part of Azure AI Studio) within an AI Project. 

**SUCCESS UPDATE (May 25, 2025)**: All 15 StratOS agents have been successfully deployed to Azure AI Agent Service! 100% of agents are tested and responding correctly. See `backend/agentic/AGENT_DEPLOYMENT_SUCCESS.md` for details on deployment and interaction.

## Current Architecture Direction: Azure AI Foundry Agent Service
StratOS is migrating from in-process Semantic Kernel to Azure AI Foundry Agent Service with a **3 Multi-Agent System Architecture**:
1. **Strategic Foundation & Insights System** (WHY/WHAT) - 5 agents
2. **Analysis & Intelligence System** (ANALYZE) - 4 agents  
3. **Planning & Execution System** (PLAN/HOW) - 6 agents

See `docs/azure_ai_foundry_integration_plan.md` for detailed architecture.
See `docs/azure_ai_foundry_todo.md` for implementation tasks.

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

### Target State (In Progress)
- FastAPI will communicate with Azure AI Foundry Agent Service
- 3 independent multi-agent systems with specialized routers
- Event-driven communication via Azure Service Bus
- Agents packaged and deployed as managed services
- Built-in conversation persistence and monitoring

## Azure Integration Status (Updated May 24, 2025)
- Cosmos DB is fully integrated and working
- **Azure OpenAI** is now configured with real credentials from semantic_kernel_multi_agent project
- AI services (Speech, Search) currently mocked - migration to Agent Service in progress
- Check backend/agentic/config/settings.py and .env for environment variables
- Real Azure OpenAI endpoint: https://sk-multi-agent-openai.openai.azure.com/

## Development Workflow (Updated May 24, 2025)
- Phase 2 is 89% complete - only CEO Preference Learning needs implementation
- **Adopted semantic_kernel_multi_agent patterns**: plugin architecture, orchestration, deployment scripts
- **Azure Container Apps deployment tools created**: Docker configuration and deployment automation ready
- Primary focus: Complete remaining Strategic Foundation agents (Memory & Preference)
- Use TodoWrite/TodoRead tools to track implementation progress
- Check mvp_status.md for detailed feature completion status

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

## Key Files for Understanding
- docs/implementation_status.md - Current implementation status
- docs/azure_ai_foundry_integration_plan.md - Multi-agent system architecture
- docs/azure_ai_foundry_todo.md - Agent migration task list
- docs/architecture.md - System architecture overview
- mvp_status.md - MVP feature tracking
- **backend/agentic/AGENT_DEPLOYMENT_SUCCESS.md** - Agent deployment status and test results
- **backend/agentic/agentic_implementation_status.md** - Detailed implementation progress
- **backend/agentic/scripts/INTERACTION_SCRIPTS_README.md** - Guide for agent interaction scripts
- **backend/agentic/adoption_plan.md** - Guide for adopting semantic_kernel_multi_agent patterns
- **backend/agentic/common/orchestration.py** - Orchestration framework implementation
- **backend/agentic/agents/strategic_foundation/plugins/** - Example plugin implementations
- **backend/agentic/scripts/** - Deployment and testing scripts
- **backend/agentic/scripts/test_all_agents.py** - Comprehensive agent testing (100% success)
- **backend/agentic/scripts/demo_agent_interaction.py** - Simple agent interaction demo
- **backend/agentic/DEPLOYMENT_GUIDE.md** - Azure Container Apps deployment guide
- **backend/agentic/Dockerfile** - Production Docker configuration
- backend/ai/kernel_service.py - AI orchestration (being migrated to agents)
- backend/ai/skills/* - Semantic Kernel skills (to be packaged as agents)
- backend/core/db_setup.py - Database initialization