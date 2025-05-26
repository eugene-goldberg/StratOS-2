# StratOS Architecture Document
*Last Updated: May 26, 2025 - Main Orchestrator Tool Calling Pattern Implemented*

## System Overview

StratOS is an AI-powered strategic planning platform that uses a single multi-agent system architecture. The system consists of a Main Orchestrator that routes requests to 15 specialized agents, organized into three logical domains.

## Architecture Diagram

```
┌─────────────────┐
│   React Frontend │
└────────┬────────┘
         │ HTTPS/WSS
         ▼
┌─────────────────┐
│  FastAPI Backend │
│  (Azure Container│
│      Apps)       │
└────────┬────────┘
         │ Agent API
         ▼
┌─────────────────┐
│ Main Orchestrator│
│ (Plugin-Based)   │
└────────┬────────┘
         │ Routes to
         ▼
┌─────────────────────────────────────────┐
│        15 Specialist Agents              │
├─────────────────┬───────────────────────┤
│Strategic (5)    │Analysis (4)│Planning(6)│
└─────────────────┴───────────────────────┘
```

## Core Architecture Principles

1. **Single Multi-Agent System**: One Main Orchestrator routes to all specialist agents
2. **Plugin-Based Architecture**: Following semantic_kernel_multi_agent patterns
3. **Instruction-Based Routing**: Orchestrator provides routing decisions as text
4. **Stateless Agents**: Each agent interaction is independent
5. **Async-First**: All operations are asynchronous for scalability

## Component Details

### Frontend Architecture
- **Framework**: React 18+ with TypeScript
- **State Management**: Zustand for client state
- **UI Components**: Material-UI v5
- **Communication**: REST API + WebSocket for real-time updates
- **Authentication**: MSAL.js for Azure AD integration

### Backend Architecture

#### FastAPI Application
```python
backend/agentic/
├── main.py                 # Application entry point
├── api/
│   ├── routes/            # API endpoints
│   │   ├── agents.py      # Agent interaction endpoints
│   │   ├── health.py      # Health checks
│   │   └── websocket.py   # WebSocket support
│   └── middleware/        # Cross-cutting concerns
│       ├── auth.py        # MSAL authentication
│       └── error.py       # Global error handling
├── config/
│   └── settings.py        # Environment configuration
├── services/
│   └── agent_client.py    # Agent communication service
└── common/
    └── base_agent.py      # Base agent abstractions
```

#### Key Design Patterns
- **Dependency Injection**: FastAPI's built-in DI for services
- **Repository Pattern**: Data access abstraction
- **Service Layer**: Business logic separation
- **DTO Pattern**: Pydantic models for validation

### Multi-Agent System Architecture

#### Main Orchestrator
- **Current ID**: `asst_IkSbH3d9TaRWfpOcCCE4QxK4` (deployed May 26, 2025)
- **Implementation**: Function tool-based orchestration (VERIFIED WORKING)
- **Tool Calling Pattern**: 
  - Orchestrator has 15 function tool definitions (one per specialist agent)
  - Returns `requires_action` status with tool calls when delegation needed
  - Client handles tool calls by invoking specialist agents
  - Results submitted back to orchestrator for final response
- **Following**: semantic_kernel_multi_agent pattern for tool-based delegation
- **Verified**: All tool calls routing correctly to appropriate agents
- **Test Script**: test_complete_orchestration_flow.py demonstrates full working system
- **Previous Approach**: Connected Agents pattern (abandoned due to unpredictable behavior)

#### Agent Organization

**Strategic Foundation & Insights Domain**
1. **CEOLogAgent**: Personal insights and observations
2. **NorthStarAgent**: Vision, mission, values, goals
3. **MemoryRecallAgent**: Historical context retrieval
4. **PreferenceLearningAgent**: User preference tracking
5. **StrategicContextRouter**: Domain-specific routing

**Analysis & Intelligence Domain**
1. **SWOTTOWSAgent**: SWOT analysis and strategies
2. **RiskOpportunityAgent**: Risk and opportunity assessment
3. **SOLinkageAgent**: Subjective-objective data linking
4. **AnalysisOrchestrator**: Complex analysis coordination

**Planning & Execution Domain**
1. **InitiativeGenerationAgent**: Strategic initiative creation
2. **ResourceOptimizationAgent**: Resource allocation
3. **ActionPlanningAgent**: Detailed action plans
4. **AlignmentScoringAgent**: Goal alignment scoring
5. **CanvasVisualizationAgent**: Visual planning
6. **PlanningCoordinator**: Planning orchestration

### Data Architecture

#### Current State (Development)
- **Primary Storage**: In-memory with persistence fallback
- **Session Management**: Thread-based conversations
- **Caching**: Local memory cache

#### Target State (Production)
- **Primary Storage**: Azure Cosmos DB
- **Search**: Azure AI Search with hybrid capabilities
- **Caching**: Azure Redis Cache
- **File Storage**: Azure Blob Storage

### Integration Architecture

#### Agent Communication Flow (Current Implementation - Being Updated)
1. User request → FastAPI endpoint
2. FastAPI → Main Orchestrator (asst_IkSbH3d9TaRWfpOcCCE4QxK4)
3. Main Orchestrator analyzes and returns tool call (invoke_agent_name)
4. FastAPI parses tool call and invokes specified specialist agent
5. Specialist agent processes request and returns response
6. FastAPI submits tool output back to Main Orchestrator
7. Main Orchestrator formulates final response
8. Final response → FastAPI → User

**Key Implementation Details**: 
- Main Orchestrator uses function calling pattern (verified working)
- Each specialist agent has a corresponding function tool (invoke_agent_name)
- FastAPI handles tool execution without making routing decisions
- The orchestrator determines which agent to use via tool calls
- Tool calling provides better control and debuggability than Connected Agents
- This pattern aligns with industry standards and semantic_kernel_multi_agent approach

#### External Integrations
- **Azure OpenAI**: LLM capabilities (via Assistants API)
- **Azure AD**: Authentication and authorization
- **Azure Speech**: Voice input processing
- **Power BI**: Analytics embedding (planned)

### Security Architecture

#### Authentication & Authorization
- **Frontend**: MSAL.js with PKCE flow
- **Backend**: MSAL Python with bearer tokens
- **Development**: Bypass mode for testing
- **Production**: Full Azure AD integration

#### Data Security
- **Encryption at Rest**: Azure-managed keys
- **Encryption in Transit**: TLS 1.3
- **API Security**: Rate limiting, CORS policies
- **Secrets Management**: Azure Key Vault (planned)

### Deployment Architecture

#### Current Deployment
- **Backend**: Azure Container Apps
- **Frontend**: Azure Static Web Apps (planned)
- **Agents**: Azure AI Agent Service (OpenAI Assistants)
- **Region**: East US

#### Infrastructure as Code
```yaml
Resources:
  - Container Apps Environment
  - Container Registry
  - AI Services
  - Cosmos DB (planned)
  - Redis Cache (planned)
```

### Performance Considerations

#### Scalability
- **Horizontal Scaling**: Container Apps auto-scaling
- **Agent Concurrency**: Parallel agent invocations
- **Connection Pooling**: Reusable HTTP clients
- **Async Operations**: Non-blocking I/O throughout

#### Optimization Strategies
- **Response Caching**: Common queries cached
- **Batch Operations**: Group related agent calls
- **Streaming Responses**: WebSocket for real-time
- **Lazy Loading**: On-demand resource fetching

### Monitoring & Observability

#### Current Implementation
- **Health Checks**: /health endpoint
- **Basic Logging**: Console output
- **Error Tracking**: Exception middleware

#### Planned Enhancements
- **Application Insights**: Full telemetry
- **Distributed Tracing**: Cross-agent tracking
- **Custom Metrics**: Business KPIs
- **Log Aggregation**: Centralized logging

## Technology Stack Summary

### Frontend
- React 18+, TypeScript 5+
- Material-UI v5, React Flow
- Zustand, React Query
- MSAL.js, Axios

### Backend
- Python 3.11+, FastAPI
- Semantic Kernel, Pydantic
- MSAL Python, aiohttp
- Docker, uvicorn

### Infrastructure
- Azure Container Apps
- Azure AI Agent Service
- Azure AD, Key Vault
- GitHub Actions (CI/CD)

### AI/ML
- GPT-3.5/4 models
- Semantic Kernel SDK
- Vector embeddings
- RAG pattern (planned)

## Architectural Decisions Record

### ADR-001: Single Multi-Agent System
- **Status**: Accepted
- **Context**: Choice between 3 separate systems vs unified system
- **Decision**: Single system with Main Orchestrator
- **Rationale**: Simpler deployment, easier maintenance, clearer routing

### ADR-002: Tool Calling Pattern
- **Status**: Accepted (May 26, 2025)
- **Context**: Choice between Connected Agents vs Tool Calling patterns
- **Decision**: Function tool calling with explicit tool definitions
- **Rationale**: More reliable, better control, easier debugging than Connected Agents

### ADR-003: FastAPI over Azure Functions
- **Status**: Accepted
- **Context**: Backend framework selection
- **Decision**: FastAPI on Container Apps
- **Rationale**: Better WebSocket support, more control, easier debugging

### ADR-004: Zustand over Redux
- **Status**: Accepted
- **Context**: Frontend state management
- **Decision**: Zustand for simplicity
- **Rationale**: Less boilerplate, TypeScript-first, better DX

### ADR-005: Tool Calling over Connected Agents
- **Status**: Accepted (May 26, 2025)
- **Context**: Main Orchestrator delegation mechanism
- **Decision**: Use function tools with requires_action pattern
- **Rationale**: Connected Agents proved unreliable; tool calling is industry standard

## Future Architecture Considerations

1. **Event-Driven Architecture**: Consider Azure Service Bus for agent communication
2. **Microservices Split**: Separate agent domains into services if needed
3. **GraphQL Gateway**: Unified API layer for complex queries
4. **Edge Deployment**: Regional agent instances for latency
5. **Federated Learning**: Privacy-preserving model updates