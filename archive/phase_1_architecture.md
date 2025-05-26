# StratOS Phase 1 Architecture: Unified Multi-Agent System

*Created: May 25, 2025*  
*Based on phase_1_architecture_recommendation.md with aligned elements from azure_ai_foundry_integration_plan.md*

## Executive Summary

This document defines the Phase 1 architecture for StratOS's migration to Azure AI Foundry Agent Service. Following expert recommendations, we adopt a **Unified Multi-Agent System (MAS)** approach that simplifies initial deployment while establishing a foundation for future evolution into specialized systems. This strategy provides enterprise-grade agent hosting, automatic scaling, built-in persistence, and comprehensive observability while managing complexity through phased implementation.

### Key Architectural Decisions:
- **Phase 1**: Single Unified MAS in AI Foundry with all agents
- **Backend**: FastAPI on Azure Container Apps (primary backend)
- **Orchestration**: Azure AI Foundry's "Connected Agents" for intra-MAS communication
- **Routing**: Deterministic logic initially, with LLM-based routing as future enhancement
- **Security**: Microsoft Entra Agent ID for first-class agent identities
- **Data**: Standard Agent Setup with customer-managed resources (BYOS, BYOSearch, BYO Cosmos DB)
- **Search**: Hybrid search (keyword + vector) in Azure AI Search from the start
- **Deployment**: "Agents-as-Code" with CI/CD pipelines

## 1. Current Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│   FastAPI   │────▶│ KernelService│────▶│ SK Skills       │
│   Backend   │     │ (In-Process) │     │ (Local Execution)│
└─────────────┘     └──────────────┘     └─────────────────┘
                            │
                            ▼
                    ┌──────────────┐
                    │  Cosmos DB   │
                    │ (Manual Mgmt)│
                    └──────────────┘
```

### Current Limitations:
- Agent orchestration handled within FastAPI process
- Manual conversation state management
- Limited scalability (bound to App Service limits)
- Complex deployment and monitoring
- No built-in agent lifecycle management

## 2. Phase 1 Target Architecture: Unified MAS

```
                    ┌─────────────────────┐
                    │   React Web App     │
                    └──────────┬──────────┘
                               │ WebSockets/REST
                    ┌──────────▼──────────┐
                    │FastAPI Backend (ACA)│ ← Primary Backend
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │ AI Foundry Agent    │
                    │ Service Runtime     │
                    │ (Unified MAS)       │
                    │ "Connected Agents"  │
                    └──────────┬──────────┘
                               │
      ┌────────────────────────▼────────────────────────┐
      │           Unified StratOS Agent System          │
      ├─────────────────────────────────────────────────┤
      │ • Main Orchestrator/Router Agent                │
      │ ----------------------------------------------- │
      │   *Foundation Agents Group:*                    │
      │   │ • CEO Log Agent                             │
      │   │ • North Star Agent                          │
      │   │ • Memory Agent                              │
      │   │ • Preference Agent                          │
      │ ----------------------------------------------- │
      │   *Analysis Agents Group:*                      │
      │   │ • SWOT/TOWS Agent                           │
      │   │ • Risk Detection Agent                      │
      │   │ • S+O Linkage Agent                         │
      │   │ • Market Intel Agent (Future)               │
      │ ----------------------------------------------- │
      │   *Planning & Canvas Agents Group:*             │
      │   │ • Initiative Agent                          │
      │   │ • Resource Agent                            │
      │   │ • Canvas Interaction Agent (Core)           │
      │   │ • Alignment Agent                           │
      └────────────────────┬────────────────────────────┘
                           │
          ┌────────────────┴────────────────┐
          │                                 │
  ┌───────▼───────┐  ┌──────────────┐  ┌──▼──────────┐
  │  Cosmos DB    │  │ Azure AI     │  │Azure Monitor│
  │ (Agent State) │  │ Search       │  │ (Metrics)   │
  └───────────────┘  │(Hybrid RAG)  │  └─────────────┘
                    └──────────────┘
```

### Key Benefits of Unified MAS Approach:
- **Reduced initial deployment complexity**: Single system to deploy and manage
- **Faster time-to-market**: Core AI features available sooner
- **Iterative development**: Learn and evolve within AI Foundry environment
- **Clear evolution path**: Foundation for future specialization into distinct systems
- **Lower operational overhead**: One system to monitor and maintain initially

## 3. Architectural Components

### 3.1 Backend Architecture: FastAPI on Azure Container Apps

**Primary Backend**: FastAPI deployed on Azure Container Apps (ACA)
- **Why FastAPI**: Better WebSocket support, stateful connections, superior async handling
- **Why ACA**: Auto-scaling, container orchestration, built-in load balancing
- **Supplementary**: Azure Functions for discrete tool implementations callable by agents

### 3.2 Agent Orchestration: Connected Agents

Leverage Azure AI Foundry's "Connected Agents" feature:
- Agents can call each other as tools within the Unified MAS
- Automatic lifecycle management, retry logic, and state persistence
- Built-in thread management for conversation history
- No need for custom orchestration logic initially

### 3.3 Security: Microsoft Entra Agent ID

Each agent gets a first-class identity:
- Agent-specific Conditional Access policies
- Comprehensive audit logging for agent actions
- RBAC at the agent level
- Secure communication between agents

### 3.4 Data Architecture: Standard Agent Setup

Customer-managed resources pattern:
- **Cosmos DB Containers**:
  - `thread-message-store`: End-user conversations
  - `system-thread-message-store`: Internal system messages
  - `agent-entity-store`: Model inputs/outputs
- **Partition Keys**:
  - Chat history: `thread_id`
  - Agent state: `agent_id`
  - Future: hierarchical partitioning for multi-tenancy

### 3.5 Search Strategy: Hybrid from Day One

Azure AI Search configuration:
- Both keyword and vector search enabled
- Semantic ranking for improved relevance
- Built-in indexers for Cosmos DB integration
- Prepared for RAG patterns

### 3.6 Router Logic: Phased Approach

**Phase 1**: Deterministic routing
- Request type mapping
- Keyword-based routing
- Predefined rules
- Fast and predictable

**Future Enhancement**: Intelligent routing
- LLM-based routing for ambiguous requests
- Learning from usage patterns
- Performance and cost optimization

## 4. Agent Organization Within Unified MAS

### 4.1 Main Orchestrator/Router Agent

Primary entry point for all requests:
```python
class MainOrchestratorAgent:
    """Routes requests to appropriate specialized agents"""
    
    async def route_request(self, request: dict) -> dict:
        # Deterministic routing logic
        request_domain = self._identify_domain(request)
        
        if request_domain == "foundation":
            return await self._route_to_foundation_group(request)
        elif request_domain == "analysis":
            return await self._route_to_analysis_group(request)
        elif request_domain == "planning":
            return await self._route_to_planning_group(request)
        else:
            # Fallback to general assistance
            return await self._provide_general_help(request)
```

### 4.2 Foundation Agents Group

| Agent | Current Skills | Responsibilities |
|-------|----------------|------------------|
| **CEO Log Agent** | `subjective/*` | Voice transcription, tag generation, entry summarization, insight extraction |
| **North Star Agent** | `strategic_foundation/*` | Purpose/Vision/Values management, strategic goal hierarchy |
| **Memory Agent** | `strategic_context_retriever` | Context retrieval, pattern recognition, historical analysis |
| **Preference Agent** | `conversation_patterns` | Feedback tracking, preference updates, personalization |

### 4.3 Analysis Agents Group

| Agent | Current Skills | Responsibilities |
|-------|----------------|------------------|
| **SWOT/TOWS Agent** | `analysis_skills/swot,tows` | Guided SWOT analysis, TOWS strategy generation, session management |
| **Risk Detection Agent** | `risk_opportunity_detection` | Anomaly detection, risk assessment, opportunity identification |
| **S+O Linkage Agent** | `subjective_objective_linkage` | Connect subjective/objective data, pattern discovery |
| **Market Intel Agent** | *Future* | External data integration, market trend analysis |

### 4.4 Planning & Canvas Agents Group

| Agent | Current Skills | Responsibilities |
|-------|----------------|------------------|
| **Initiative Agent** | `planning/generate_initiative` | Create initiatives, generate actions, define milestones |
| **Resource Agent** | `planning/resources` | Resource allocation, capacity planning, utilization tracking |
| **Canvas Interaction Agent** | `canvas/*` | Visual planning support, node management, connection suggestions |
| **Alignment Agent** | `planning/analyze_alignment` | Strategic alignment, goal mapping, impact assessment |

## 5. Implementation Phases

### Phase 1.1: Foundation Setup (Weeks 1-2)

#### Environment Configuration
- [ ] Set up Azure AI Foundry workspace with Standard Agent Setup
- [ ] Configure Agent Service with Microsoft Entra Agent ID
- [ ] Set up customer-managed Cosmos DB with required containers
- [ ] Configure Azure AI Search with hybrid search capabilities
- [ ] Set up Azure Monitor and Application Insights
- [ ] Configure VNet and private endpoints for security

#### Backend Infrastructure
- [ ] Deploy FastAPI to Azure Container Apps
- [ ] Configure WebSocket support for real-time streaming
- [ ] Implement MSAL authentication for React-Backend communication
- [ ] Set up managed identity for Backend-Azure services
- [ ] Create Azure Functions project for tool implementations

#### Agent Development Framework
- [ ] Create base agent template with Semantic Kernel
- [ ] Implement "Agents-as-Code" repository structure
- [ ] Set up agent configuration files (JSON/YAML)
- [ ] Create prompt versioning system
- [ ] Implement Connected Agents integration patterns

### Phase 1.2: Unified MAS Implementation (Weeks 3-4)

#### Main Orchestrator Development
- [ ] Implement deterministic routing logic
- [ ] Create domain identification patterns
- [ ] Set up request preprocessing
- [ ] Implement fallback mechanisms

#### Agent Migration (Grouped Approach)
- [ ] Migrate Foundation Agents Group
  - [ ] CEO Log Agent with existing skills
  - [ ] North Star Agent with strategic foundation skills
  - [ ] Memory Agent with context retrieval
  - [ ] Preference Agent (basic implementation)
- [ ] Migrate Analysis Agents Group
  - [ ] SWOT/TOWS Agent with guided sessions
  - [ ] Risk Detection Agent with alerting
  - [ ] S+O Linkage Agent with correlation
- [ ] Migrate Planning Agents Group
  - [ ] Initiative Agent with generation logic
  - [ ] Resource Agent with allocation
  - [ ] Canvas Interaction Agent (core features)
  - [ ] Alignment Agent with scoring

### Phase 1.3: Integration & Testing (Week 5)

#### System Integration
- [ ] FastAPI integration with Unified MAS
- [ ] End-to-end workflow testing
- [ ] Performance benchmarking
- [ ] Connected Agents communication testing

#### Quality Assurance
- [ ] Individual agent testing
- [ ] Group interaction testing
- [ ] Load testing
- [ ] Failover testing

### Phase 1.4: Production Deployment (Week 6)

#### Deployment Strategy
- [ ] Blue-Green deployment setup
- [ ] Gradual traffic migration
- [ ] Monitoring dashboards
- [ ] Alert configuration

## 6. FastAPI Integration Layer

### 6.1 Agent Service Client
```python
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient

class StratOSAgentClient:
    def __init__(self):
        self.credential = DefaultAzureCredential()
        self.client = AIProjectClient(
            credential=self.credential,
            endpoint=settings.AI_FOUNDRY_ENDPOINT,
            project_id=settings.PROJECT_ID
        )
        self.orchestrator = None
    
    async def initialize(self):
        """Initialize connection to Main Orchestrator"""
        self.orchestrator = await self.client.agents.get("main-orchestrator")
    
    async def invoke(self, request: dict) -> dict:
        """All requests go through Main Orchestrator"""
        thread = await self.client.threads.create()
        
        response = await self.orchestrator.invoke(
            thread_id=thread.id,
            request_body=request
        )
        return response
```

### 6.2 Service Layer Updates
```python
class AnalysisService:
    def __init__(self):
        self.agent_client = StratOSAgentClient()
    
    async def generate_swot(self, user_id: UUID, context: dict) -> SWOTAnalysis:
        result = await self.agent_client.invoke({
            "domain": "analysis",
            "action": "generate_swot",
            "user_id": str(user_id),
            "context": context
        })
        return SWOTAnalysis(**result)
```

## 7. Model Selection Strategy

Optimized for Phase 1 Unified MAS:

| Agent | Model | Rationale |
|-------|-------|-----------|
| Main Orchestrator | GPT-4 | Complex routing decisions |
| CEO Log Agent | GPT-4o | Future multimodal capabilities |
| Analysis Agents | GPT-4 | Advanced reasoning |
| Simple Task Agents | GPT-3.5-Turbo | Cost-effective |
| Constraint Agents | o-series | Optimized reasoning |

## 8. Deployment Configuration

### 8.1 Agent Service Configuration
```json
{
  "agentService": {
    "name": "stratos-unified-mas",
    "location": "eastus",
    "sku": "Standard",
    "properties": {
      "persistenceEnabled": true,
      "standardSetup": {
        "enabled": true,
        "cosmosDb": {
          "customerManaged": true,
          "containers": [
            "thread-message-store",
            "system-thread-message-store",
            "agent-entity-store"
          ]
        },
        "aiSearch": {
          "customerManaged": true,
          "hybridSearch": true
        }
      },
      "identity": {
        "microsoftEntraAgentId": true
      },
      "monitoringEnabled": true,
      "autoScaleEnabled": true,
      "connectedAgents": {
        "enabled": true,
        "agentToAgentCalls": true
      }
    }
  }
}
```

### 8.2 Deployment Script
```bash
#!/bin/bash
# Deploy Unified MAS to AI Foundry

# Package all agents
for agent in $(ls agents/); do
  az ai-foundry agent package \
    --name $agent \
    --source agents/$agent \
    --output ./dist
done

# Deploy as unified system
az ai-foundry agent-system deploy \
  --name stratos-unified-mas \
  --packages ./dist/*.zip \
  --orchestrator main-orchestrator
```

## 9. Monitoring and Operations

### 9.1 Key Metrics
- Agent invocation count (per agent)
- Response time (P50, P95, P99)
- Error rate by agent
- Token usage per agent
- Active thread count

### 9.2 Dashboards
- System health overview
- Agent performance matrix
- Cost tracking
- User activity patterns

## 10. Cost Optimization

### Phase 1 Estimated Costs
| Component | Usage | Monthly Cost |
|-----------|-------|--------------|
| Unified MAS (15 agents) | 100K calls/month | $1,200 |
| Conversation Storage | 15 GB | $40 |
| Monitoring | 20 metrics | $40 |
| **Total** | | **$1,280/month** |

### Optimization Strategies
- Request batching within agent groups
- Caching for common queries
- Async processing for non-critical tasks
- Smart agent hibernation

## 11. Future Evolution Path

### Phase 2: System Specialization (Months 3-6)
- Evaluate usage patterns from Phase 1
- Identify natural boundaries for system separation
- Plan migration to 3 distinct systems if beneficial
- Implement cross-system event bus if needed

### Phase 3: Advanced Features (Months 6-12)
- LLM-based intelligent routing
- Cross-system learning mechanisms
- Dynamic agent creation
- Industry-specific variations

## 12. Success Criteria

### Technical Success
- [ ] All 15 agents deployed and operational
- [ ] <300ms response time for 95% of requests
- [ ] <0.1% error rate
- [ ] Successful Connected Agents communication

### Business Success
- [ ] Core StratOS features fully functional
- [ ] Improved response quality vs. current system
- [ ] Reduced operational complexity
- [ ] Clear path for future enhancements

## 13. Risk Mitigation

### Rollback Strategy
1. **Immediate** (<5 min): Route back to local FastAPI processing
2. **Partial** (<30 min): Keep some agents, rollback others
3. **Full**: Restore from Cosmos DB backups

### Contingency Plans
- Fallback to deterministic responses if agents fail
- Circuit breakers for agent calls
- Graceful degradation patterns

## Conclusion

This Phase 1 architecture provides a pragmatic approach to migrating StratOS to Azure AI Foundry Agent Service. By starting with a Unified MAS, we reduce complexity while gaining the benefits of enterprise-grade agent hosting. The architecture is designed to evolve, with clear paths to more sophisticated multi-system architectures as the platform matures and requirements become clearer through real-world usage.

The key to success is maintaining simplicity in Phase 1 while building on a foundation that supports future growth and specialization.