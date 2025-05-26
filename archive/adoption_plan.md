# Adoption Plan: Semantic Kernel Multi-Agent Tools for StratOS

## Executive Summary

This document outlines the adoption of tools, scripts, and patterns from the semantic_kernel_multi_agent project into StratOS's multi-agent architecture.

## 1. Immediate Adoptions (Week 1)

### 1.1 Plugin Architecture Pattern

**What to Adopt:**
- The `@kernel_function` decorator pattern for creating SK plugins
- Plugin registration using `KernelPlugin.from_object()`
- Function calling mechanism for agent delegation

**Implementation Steps:**
1. Refactor existing Semantic Kernel skills into plugin classes
2. Update agent base classes to support plugin registration
3. Implement function calling in router agents

**Example Migration:**
```python
# Current: backend/legacy/ai/skills/subjective/GenerateTags.prompt.txt
# New: backend/agentic/agents/strategic_foundation/plugins/ceo_log_plugin.py

from semantic_kernel.functions import kernel_function

class CEOLogPlugin:
    @kernel_function(
        description="Generate tags for a CEO log entry",
        name="GenerateTags"
    )
    def generate_tags(self, entry: str) -> str:
        # Implementation using existing prompt
        pass
```

### 1.2 Orchestration Pattern

**What to Adopt:**
- Function calling setup from `orchestrate_with_kernel.py`
- Tool definition format for Azure OpenAI
- Message handling for function calls

**Implementation in StratOS:**
```python
# backend/agentic/common/orchestration.py
class AgentOrchestrator:
    async def setup_function_calling(self, kernel, available_functions):
        # Adopt the pattern from orchestrate_with_kernel.py
        pass
```

### 1.3 Deployment Scripts

**What to Adopt:**
- Azure CLI deployment approach from `deploy_agents_az_cli.sh`
- JSON agent definition format
- Deployment info tracking

**New Scripts to Create:**
```bash
# backend/agentic/scripts/deploy_stratos_agents.sh
# Adapted from deploy_agents_az_cli.sh for StratOS agents
```

## 2. Configuration Management (Week 1)

### 2.1 Settings Structure

**What to Adopt:**
- Environment variable management from `settings.py`
- Connection string construction pattern

**Implementation:**
```python
# Update backend/agentic/config/settings.py
class AgentSettings(BaseSettings):
    # Azure AI Foundry settings
    azure_ai_hub_name: str
    azure_ai_project_name: str
    azure_ai_project_host: str
    
    def get_project_connection_string(self) -> str:
        # Adopt connection string pattern
        pass
```

## 3. Agent Factory Pattern (Week 2)

### 3.1 Local Development

**What to Adopt:**
- `LocalAgentFactory` pattern for creating agents during development
- Service creation abstraction

**Implementation:**
```python
# backend/agentic/utils/agent_factory.py
class StratOSAgentFactory:
    @staticmethod
    def create_strategic_foundation_system():
        # Create all agents for this system
        pass
```

### 3.2 Azure Deployment Factory

**What to Adopt:**
- Agent deployment patterns
- Thread management
- Client creation patterns

## 4. Testing Infrastructure (Week 2)

### 4.1 Interactive Testing Scripts

**What to Adopt:**
- `interact_deployed_agents.py` pattern
- Local testing with `local_chat.py`
- API client testing approach

**New Scripts:**
```bash
# backend/agentic/scripts/test_strategic_system.py
# backend/agentic/scripts/test_analysis_system.py
# backend/agentic/scripts/test_planning_system.py
```

## 5. API Server Enhancements (Week 3)

### 5.1 Thread Management

**What to Adopt:**
- Thread lifecycle management from `server.py`
- Background task cleanup
- Thread persistence across conversations

### 5.2 Agent Information Endpoints

**What to Adopt:**
- `/agents` endpoint pattern
- Deployment info tracking
- Agent status monitoring

## 6. Documentation Templates (Ongoing)

**What to Adopt:**
- Deployment guide structure
- Orchestration documentation format
- Project status tracking approach

## Implementation Priority

### Phase 1: Core Infrastructure (Week 1)
1. Plugin architecture migration
2. Orchestration pattern implementation
3. Configuration management update
4. Basic deployment scripts

### Phase 2: Development Tools (Week 2)
1. Agent factory implementation
2. Interactive testing scripts
3. Local development tools
4. API client utilities

### Phase 3: Production Features (Week 3)
1. Thread management in API
2. Monitoring endpoints
3. Deployment automation
4. Documentation updates

## Key Files to Create/Update

### New Files
- `backend/agentic/common/orchestration.py`
- `backend/agentic/utils/agent_factory.py`
- `backend/agentic/scripts/deploy_stratos_agents.sh`
- `backend/agentic/scripts/test_*.py`
- All plugin files for existing skills

### Files to Update
- `backend/agentic/config/settings.py`
- `backend/agentic/common/base_agent.py`
- `backend/agentic/api/routes/agents.py`
- `backend/agentic/services/agent_client.py`

## Migration Checklist

- [ ] Analyze all existing SK skills for plugin conversion
- [ ] Create plugin base class following the pattern
- [ ] Implement orchestration base class
- [ ] Adapt deployment scripts for StratOS agents
- [ ] Create agent factory for each system
- [ ] Implement interactive testing scripts
- [ ] Update API with thread management
- [ ] Create deployment automation
- [ ] Document new patterns and tools
- [ ] Train team on new approaches

## Benefits of Adoption

1. **Proven Patterns**: The semantic_kernel_multi_agent project has solved many challenges we'll face
2. **Function Calling**: Robust implementation of SK function calling for agent delegation
3. **Deployment Tools**: Battle-tested scripts for Azure deployment
4. **Testing Infrastructure**: Interactive tools for agent testing
5. **Documentation**: Clear patterns for documenting multi-agent systems

## Risk Mitigation

1. **Compatibility**: Ensure SK version alignment (1.30.0+)
2. **Azure API Versions**: Use tested API versions (2024-05-01-preview)
3. **Gradual Migration**: Start with one system before migrating all
4. **Backward Compatibility**: Maintain existing functionality during migration