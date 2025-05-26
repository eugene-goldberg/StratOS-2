# StratOS Multi-Agent System Best Practices Guide
*Created: May 24, 2025*

## Overview
This document outlines best practices for implementing StratOS's multi-agent system using Semantic Kernel Python SDK, Azure AI Foundry Agent Service, and related Azure services.

## 1. Multi-Agent System Architecture with Semantic Kernel

### 1.1 Agent Design Principles
- **Single Purpose Agents**: Design each agent with a specific role to maximize performance
- **Composable Units**: Agents should be composable with Model, Instructions, and Tools
- **Stateless Design**: Keep agents stateless; use external storage (Cosmos DB) for state

### 1.2 Python SDK Implementation Pattern
```python
from semantic_kernel.agents import AzureAIAgent
from azure.identity import DefaultAzureCredential

# Best practice: Use async context managers
async with (
    DefaultAzureCredential() as creds,
    AzureAIAgent.create_client(credential=creds, endpoint="<your-endpoint>") as client,
):
    # Your operational code here
    pass
```

### 1.3 Multi-Agent Orchestration
- Start by building singleton agents with Azure AI Agent Service
- Use Semantic Kernel's AgentGroupChat for multi-agent collaboration
- Implement proper selection and termination strategies
- Leverage built-in thread management and state persistence

## 2. Azure AI Foundry Agent Service Deployment

### 2.1 Production-Ready Foundation
- **Runtime Management**: Agent Service manages threads, orchestrates tool calls, enforces content safety
- **Built-in Features**: Automatic retry logic, thread-level visibility, Application Insights integration
- **State Management**: Conversation history automatically persisted using threads

### 2.2 Security and Trust
- **Identity**: Use Microsoft Entra ID for authentication
- **RBAC**: Implement Role-Based Access Control
- **Content Filters**: Enable content safety filters
- **Network Isolation**: Use private endpoints and VNet integration
- **Encryption**: Data encrypted at rest and in transit

### 2.3 Observability
- **OpenTelemetry**: Use OpenTelemetry-based tracing for monitoring
- **Application Insights**: Full integration for telemetry and debugging
- **Thread Visibility**: Full thread-level visibility for agent decisions
- **Custom Metrics**: Instrument custom metrics for agent performance

## 3. Azure OpenAI Integration

### 3.1 Model Selection
- Choose appropriate models for each agent's specific task
- Consider using different models for routing vs. specialized agents
- Implement token usage tracking and cost management

### 3.2 Prompt Engineering
- Use Semantic Kernel's prompt templates
- Implement prompt versioning and A/B testing
- Maintain prompt libraries for consistency

### 3.3 Performance Optimization
- Implement caching for repeated queries
- Use streaming for real-time responses
- Batch requests where appropriate

## 4. Azure Service Integration Patterns

### 4.1 Cosmos DB Integration
- **Agent State**: Save agent state as persistent memory
- **Conversation History**: Store user conversations for analysis
- **Pattern**: Use Cosmos DB containers per agent system
- **Best Practice**: Implement proper partition keys for scalability

### 4.2 Azure AI Search Integration
- **Hybrid Search**: Combine vector and text search capabilities
- **Indexing**: Use built-in indexers for Cosmos DB data
- **Knowledge Retrieval**: Central retrieval system for RAG applications
- **Memory Connectors**: Connect agents to knowledge sources

### 4.3 Speech Services Integration
- **Voice Input**: Process audio through Speech-to-Text
- **Voice Output**: Use Text-to-Speech for responses
- **Real-time**: Implement continuous recognition for streaming
- **Custom Models**: Train custom speech models for domain terms

### 4.4 Event-Driven Architecture
- **Azure Service Bus**: Use for cross-system communication
- **Event Patterns**: Implement pub/sub for agent coordination
- **Async Processing**: Handle long-running tasks asynchronously

## 5. Web App Integration

### 5.1 Recommended Architecture: FastAPI on Azure Functions

#### Why This Combination?
- **Serverless Benefits**: Auto-scaling, pay-per-use, scales to zero
- **Async Support**: Native async/await for AI operations
- **Framework Features**: FastAPI's dependency injection, auto-documentation
- **Azure Integration**: First-class support for Azure services

#### Implementation Pattern
```python
# main.py
from fastapi import FastAPI
from azure.functions import AsgiRequest, AsgiResponse
import azure.functions as func

app = FastAPI()

# Your FastAPI routes here
@app.post("/agent/invoke")
async def invoke_agent(request: AgentRequest):
    # Invoke Azure AI Agent Service
    pass

# Azure Function wrapper
async def main(req: func.HttpRequest) -> func.HttpResponse:
    return await AsgiResponse(app, req)
```

### 5.2 Authentication Pattern
```python
from azure.identity import DefaultAzureCredential
from fastapi import Depends, Security
from fastapi.security import HTTPBearer

security = HTTPBearer()

async def get_current_user(token: str = Security(security)):
    # Validate token with Microsoft Entra ID
    return user

@app.post("/agent/invoke")
async def invoke_agent(
    request: AgentRequest,
    user = Depends(get_current_user)
):
    # User-scoped agent invocation
    pass
```

### 5.3 Agent Client Integration
```python
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

class AgentServiceClient:
    def __init__(self):
        self.credential = DefaultAzureCredential()
        self.client = AIProjectClient(
            credential=self.credential,
            endpoint=settings.AI_FOUNDRY_ENDPOINT,
            project_id=settings.PROJECT_ID
        )
    
    async def invoke_strategic_foundation(self, request: dict):
        # Invoke Strategic Foundation system
        agent = self.client.agents.get("strategic-foundation-router")
        response = await agent.invoke(request)
        return response
```

### 5.4 Alternative Architectures

#### Azure Container Apps
- For containerized deployments with more control
- Better for long-running processes
- Supports KEDA scaling

#### Azure App Service
- Traditional web app hosting
- Good for existing .NET/Python apps
- Integrated deployment slots

## 6. Interface Structure: Web App ↔ Agent Systems

### 6.1 Communication Pattern
```
Web App (FastAPI/Functions)
    ↓ (REST API)
Agent Service Client
    ↓ (Azure AI SDK)
Azure AI Agent Service
    ↓ (Internal routing)
Multi-Agent Systems (3 systems)
    ↓ (Tool calls)
Azure Services (Cosmos, Search, etc.)
```

### 6.2 Request/Response Pattern
```python
# Web app sends structured requests
request = {
    "system": "strategic-foundation",
    "type": "ceo_log",
    "action": "create_entry",
    "data": {
        "text": "...",
        "category": "strategic"
    },
    "user_context": {
        "user_id": "...",
        "tenant_id": "..."
    }
}

# Agent system returns structured response
response = {
    "status": "success",
    "data": {
        "entry_id": "...",
        "tags": [...],
        "summary": "...",
        "insights": [...]
    },
    "metadata": {
        "agent": "CEOLogAgent",
        "duration_ms": 250,
        "tokens_used": 150
    }
}
```

### 6.3 Error Handling
- Implement circuit breakers for agent calls
- Use exponential backoff for retries
- Provide graceful degradation
- Log all errors to Application Insights

## 7. Deployment Best Practices

### 7.1 Infrastructure as Code
- Use Bicep templates for all resources
- Version control infrastructure code
- Implement staging environments

### 7.2 CI/CD Pipeline
```yaml
# GitHub Actions example
- name: Deploy Agents
  run: |
    # Deploy each agent system
    az ai-foundry agent deploy \
      --name strategic-foundation \
      --package ./agents/strategic_foundation
```

### 7.3 Monitoring and Alerts
- Set up alerts for high error rates (>5%)
- Monitor response times (<300ms target)
- Track token usage and costs
- Monitor agent utilization

## 8. Development Workflow

### 8.1 Local Development
1. Use Azure AI Foundry SDK locally
2. Mock external services when needed
3. Use development Azure resources
4. Test with small models first

### 8.2 Testing Strategy
- Unit tests for individual agents
- Integration tests for agent groups
- End-to-end tests for workflows
- Performance tests for scalability

### 8.3 Deployment Stages
1. Development: Frequent deployments, smaller models
2. Staging: Production-like, full testing
3. Production: Blue-green deployment, monitoring

## 9. Cost Optimization

### 9.1 Agent Design
- Minimize inter-agent communication
- Use appropriate model sizes
- Implement request batching
- Cache common queries

### 9.2 Resource Management
- Use consumption-based pricing
- Implement auto-scaling policies
- Monitor and optimize token usage
- Use reserved capacity for predictable workloads

## 10. Summary of Key Decisions

### Technology Stack
- **Runtime**: Azure AI Foundry Agent Service
- **SDK**: Semantic Kernel Python
- **Web Framework**: FastAPI on Azure Functions
- **State Storage**: Cosmos DB
- **Search**: Azure AI Search
- **Events**: Azure Service Bus
- **Monitoring**: Application Insights

### Architecture Patterns
- 3 Multi-Agent Systems (Strategic, Analysis, Planning)
- Router + Specialized Agents per system
- Event-driven cross-system communication
- Serverless web app integration

### Security Model
- Microsoft Entra ID authentication
- Managed identities for service-to-service
- Network isolation with private endpoints
- Content filtering and safety measures

This architecture provides a scalable, secure, and maintainable foundation for StratOS's AI-powered strategic planning platform.