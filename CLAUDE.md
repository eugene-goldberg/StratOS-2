Always use python3 instead of python
Always use python3 virtual environment for running tests
**IMPORTANT: Virtual Environment Location**
- you must use the .venv located under the connected_agents folder

Always use python3 instead of python
Always use python3 virtual environment for running tests

## IMPORTANT: Primary Documentation
**ALWAYS READ THESE FOUR MAIN DOCUMENTS:**
- Always read **STATUS.md** FIRST - this is the single source of truth for project status
- Always read **ARCHITECTURE.md** to understand the system design and technical decisions
- Always read **TODO.md** to see current tasks and priorities
- Always read **FEATURE_PLAN.md** to understand the product roadmap

## IMPORTANT: Documentation Update Protocol
After completing ANY task or making significant progress:
1. Update **STATUS.md** - update implementation status and recent accomplishments
2. Update **TODO.md** - mark completed items with ✅ and move to completed section
3. Update **ARCHITECTURE.md** - if any architectural decisions or changes were made
4. Include completion date (e.g., "✅ COMPLETED (May 25)") for tracking

## Reference Documents (For Context Only)
These documents are archived in `/archive/` directory and should only be referenced for historical context:
- All phase_1_*.md files - Historical Phase 1 documentation
- implementation_status.md - Pre-consolidation status
- agentic_implementation_status.md - Backend-specific historical status
- azure_ai_foundry_*.md - Original migration plans

This ensures accurate progress tracking and single source of truth for all documentation.

# StratOS Project-Specific Instructions

## IMPORTANT: Azure Deployment Strategy
**DO NOT use Azure OpenAI Assistants API for any deployments.** StratOS agents must be deployed to Azure AI Agent Service (part of Azure AI Studio) within an AI Project. 

**SUCCESS UPDATE (May 25, 2025)**: All 15 StratOS agents have been successfully deployed to Azure AI Agent Service! 100% of agents are tested and responding correctly. Main Orchestrator uses plugin-based architecture with ID: asst_DvAoA85m6eCsWdOT2bsTxE6i.

## Current Architecture Direction: Single Multi-Agent System
StratOS uses a **Single Multi-Agent System** architecture with a Main Orchestrator that routes requests to 15 specialized agents. This unified approach simplifies deployment and maintenance while providing comprehensive strategic planning capabilities.

**Architecture**: Plugin-based pattern following semantic_kernel_multi_agent
**Routing**: Instruction-based with "ROUTE TO: [Agent] - REASON: [explanation]" format
**Deployment**: All agents deployed to Azure AI Agent Service (OpenAI Assistants)

See **ARCHITECTURE.md** for complete system design.
See **STATUS.md** for current implementation status.
See **TODO.md** for pending tasks.

## IMPORTANT: Backend Development Location
ALL backend development work takes place exclusively under `/backend/agentic/`
- The `/backend/legacy/` folder contains the old implementation for reference only
- Do NOT modify or create files in `/backend/legacy/`
- All new backend code, APIs, and agent implementations go in `/backend/agentic/`
- **YOU MUST REMAIN WITHIN THE connected_agents FOLDER FOR ALL OF YOUR SEARCHES**

## IMPORTANT: Reference Folder Restrictions
- you must not obtain any references from the archive folder
- you must retain the use of ConnectedAhentTool

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
- FastAPI communicates with Azure AI Agent Service
- Main Orchestrator (plugin-based) routes to all 15 agents
- Instruction-based routing due to Azure limitations
- Agents deployed as managed services with built-in persistence
- Thread-based conversation management

## Azure Integration Status (Updated May 24, 2025)
- Cosmos DB is fully integrated and working
- **Azure OpenAI** is now configured with real credentials from semantic_kernel_multi_agent project
- AI services (Speech, Search) currently mocked - migration to Agent Service in progress
- Check backend/agentic/config/settings.py and .env for environment variables
- Real Azure OpenAI endpoint: https://sk-multi-agent-openai.openai.azure.com/

## Development Workflow (Updated May 25, 2025)
- **Current Focus**: Complete FastAPI-Agent integration
- **Status**: Agents deployed, orchestrator routing works, integration pending
- **Immediate Priority**: Parse orchestrator routing and invoke agents
- **Next Steps**: Add conversation state management
- Use TodoWrite/TodoRead tools to track implementation progress
- Check **STATUS.md** for detailed completion status

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
- **Do not make any changes to files located under the semantic_kernel_multi_agent directory**

## Key Files for Understanding
### Primary Documents (Always Current)
- **STATUS.md** - Project status and implementation progress
- **ARCHITECTURE.md** - System architecture and technical decisions
- **TODO.md** - Current tasks and priorities
- **FEATURE_PLAN.md** - Product roadmap and feature development

### Supporting Files
- backend/agentic/scripts/INTERACTION_SCRIPTS_README.md - Agent interaction scripts
- backend/agentic/scripts/test_all_agents.py - Agent testing scripts
- backend/agentic/scripts/test_orchestrator_routing.py - Orchestrator routing tests
- backend/agentic/scripts/deploy_main_orchestrator_plugin_based.py - Deploy Main Orchestrator
- backend/agentic/DEPLOYMENT_GUIDE.md - Azure Container Apps deployment
- backend/ai/kernel_service.py - AI orchestration (being migrated)
- backend/ai/skills/* - Semantic Kernel skills (being packaged as agents)

### Archived Documents (Historical Context Only)
All historical documents have been moved to `/archive/` directory including:
- phase_1_*.md files - Phase 1 implementation docs
- implementation_status.md files - Various status tracking
- azure_ai_foundry_*.md - Original migration plans
- AGENT_DEPLOYMENT_*.md - Deployment logs

## Testing Philosophy
- You will always verify every element of every feature through a set of comprehensive tests run against the fully deployed feature

## CRITICAL: Accountability and Truthful Reporting Instructions

### Evidence-Based Reporting Requirements
NEVER claim success without providing:
- **Actual output logs** showing the execution succeeded
- **Error messages** if they exist (always show errors first)
- **Telemetry traces** proving the flow worked end-to-end
- **Response text** from agents showing they actually responded

### Failure-First Reporting
**ALWAYS start reports with what FAILED or is MISSING:**
1. List all errors and failures FIRST
2. Show what is NOT working
3. Only claim success AFTER showing concrete evidence
4. Never hide or minimize failures

### Specific Success Criteria
Before claiming any feature works, verify ALL of these:
- **Orchestration**: All 15 agents respond when invoked through orchestrator
- **Delegation**: Telemetry shows complete request→orchestrator→specialist→response flow
- **Error-free**: No errors in any logs or traces
- **Evidence**: Actual response text from each agent (not just "success")

### Prohibited Patterns
**NEVER do these things:**
- Create "verification" scripts without showing their actual output
- Say "should work" or "successfully configured" without proof
- Use "✅ Success" without evidence
- Focus on what you built rather than what actually runs
- Hide errors in long outputs
- Claim partial success as complete success

### Required Verification Questions
When implementing features, automatically answer:
1. "What errors occurred when I ran this?"
2. "Show me the exact output that proves this worked"
3. "How many of the required components actually responded?"
4. "What is still broken or missing?"

### Negative Testing Requirements
Always test and report:
- What breaks when you run this?
- Which components are NOT working?
- What's in the failed lists/arrays?
- What error messages appear?

### Example of Proper Reporting
```
❌ FAILURES:
- MainOrchestrator: Failed with "missing function tools" error
- 11/15 agents: Not tested, no evidence they work
- Delegation: Zero successful orchestrator→specialist flows

✅ PARTIAL SUCCESS:
- 4/15 agents respond when invoked directly (not through orchestrator)
- Telemetry system captures traces (but shows failures)

EVIDENCE:
[Actual error output]
[Actual successful response text]
[Telemetry trace showing the failure]
```

**IMPORTANT**: User explicitly requires truthful, evidence-based reporting. Always lead with failures and missing functionality before claiming any success.