Always use python3 instead of python
Always use python3 virtual environment for running tests
Always read docs/implementation_status.md to understand the current status of this project
Always read docs/azure_ai_foundry_integration_plan.md to understand the multi-agent architecture
Always read docs/azure_ai_foundry_todo.md to track agent migration progress
Always read docs/multi_agent_best_practices.md for implementation guidelines and patterns
Always read docs/Deep_Research_Multi-Agent_Systems_Azure_Best_Practices.md for research findings
Always read ToDo.md to understand current priorities and tasks
Always read backend/agentic/agentic_implementation_status.md to understand what is implemented and next steps
Always maintain close cohesion between ToDo.md and agentic_implementation_status.md - update both files when tasks are completed or priorities change, ensuring session continuity

# StratOS Project-Specific Instructions

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
- CI workflows must pass before committing

## Architecture Patterns
### Current State
- Backend uses FastAPI with dependency injection for user context
- All services use Cosmos DB with fallback to in-memory storage
- AI features use Semantic Kernel with prompt templates in .txt files
- Frontend uses React with TypeScript, Material UI, and Zustand for state

### Target State (In Progress)
- FastAPI will communicate with Azure AI Foundry Agent Service
- 3 independent multi-agent systems with specialized routers
- Event-driven communication via Azure Service Bus
- Agents packaged and deployed as managed services
- Built-in conversation persistence and monitoring

## Azure Integration Status
- Cosmos DB is fully integrated and working
- AI services (OpenAI, Speech, Search) currently mocked - migration to Agent Service in progress
- Check backend/core/config.py for environment variables needed
- Mock implementations allow full functionality without Azure services

## Development Workflow
- Phase 2 is 89% complete - only CEO Preference Learning needs implementation
- Primary focus: Azure AI Foundry Agent Service integration (4 phases)
- Use TodoWrite/TodoRead tools to track implementation progress
- Check mvp_status.md for detailed feature completion status

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
- backend/ai/kernel_service.py - AI orchestration (being migrated to agents)
- backend/ai/skills/* - Semantic Kernel skills (to be packaged as agents)
- backend/core/db_setup.py - Database initialization