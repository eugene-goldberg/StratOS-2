Always use python3 instead of python
Always use python3 virtual environment for running tests
Always read docs/implementation_status.md to understand the current status of this project

# StratOS Project-Specific Instructions

## Testing
- Run backend tests: `cd /path/to/project && source venv/bin/activate && python -m pytest tests/`
- Run frontend tests: `cd frontend && npm test`
- Run strategic canvas tests: `cd frontend/strategic-canvas && npm test`
- CI workflows must pass before committing

## Architecture Patterns
- Backend uses FastAPI with dependency injection for user context
- All services use Cosmos DB with fallback to in-memory storage
- AI features use Semantic Kernel with prompt templates in .txt files
- Frontend uses React with TypeScript, Material UI, and Zustand for state

## Azure Integration Status
- Cosmos DB is fully integrated and working
- All AI services (OpenAI, Speech, Search) are mocked but structured for easy integration
- Check backend/core/config.py for environment variables needed
- Mock implementations allow full functionality without Azure services

## Development Workflow
- Phase 2 is 89% complete - only CEO Preference Learning needs implementation
- External Azure AI service integration is the main remaining task
- Use TodoWrite/TodoRead tools to track implementation progress
- Check mvp_status.md for detailed feature completion status

## Common Pitfalls to Avoid
- Don't use 'python' command - always use 'python3'
- Don't install packages globally - always use virtual environment
- Don't modify Azure container names - they're hardcoded in services
- Don't assume AI services are connected - check for mock implementations

## Key Files for Understanding
- docs/implementation_status.md - Current implementation status
- docs/architecture.md - System architecture overview
- mvp_status.md - MVP feature tracking
- backend/ai/kernel_service.py - AI orchestration (currently mocked)
- backend/core/db_setup.py - Database initialization