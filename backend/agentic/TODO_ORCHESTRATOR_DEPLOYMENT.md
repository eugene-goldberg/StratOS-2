# TODO: Deploy Main Orchestrator with Plugin-Based Architecture

## Overview
Deploy a Main Orchestrator that uses **NO hardcoded routing logic**. The orchestrator must rely entirely on:
1. Its LLM capabilities to understand requests
2. Rich descriptions of available specialist agents  
3. Natural language reasoning to make routing decisions

## Key Principles
- **NO function tools** with hardcoded mappings
- **NO explicit routing rules** in code
- **LLM-driven routing** based on understanding intent
- **Rich agent descriptions** to guide the LLM's decisions

## Detailed TODO Instructions

### 1. Remove Current Orchestrator (with hardcoded function tools)
```bash
# Delete the existing orchestrator that has hardcoded function tools
python backend/agentic/scripts/remove_main_orchestrator.py
```
- This will remove agent ID: `asst_IkSbH3d9TaRWfpOcCCE4QxK4` (the one with function tools)

### 2. Deploy New Plugin-Based Orchestrator

#### 2.1 Update Agent Descriptions in Instructions
Edit `backend/agentic/scripts/deploy_main_orchestrator_plugin_based.py`:

Update the instructions to include **rich, detailed descriptions** of each agent's capabilities:

```python
"instructions": (
    "You are the Main Orchestrator for StratOS, a comprehensive strategy operating system. "
    "Your role is to analyze incoming requests and determine which specialized agent should handle them.\n\n"
    
    "AVAILABLE SPECIALIST AGENTS:\n"
    
    "STRATEGIC FOUNDATION & INSIGHTS SYSTEM:\n"
    "1. CEOLogAgent - Specialized in capturing and organizing CEO's thoughts, observations, strategic notes, "
    "   concerns, ideas, and subjective inputs. Handles categorization of entries (strategic, operational, "
    "   personal, market, team). Perfect for logging important decisions, observations, or thoughts.\n"
    
    "2. CEOMemoryAgent - Retrieves and recalls past CEO log entries, decisions, and strategic context. "
    "   Can search through historical entries by date, category, or content. Use when user asks about "
    "   'what did I say about...', 'my previous thoughts on...', or 'decisions from last quarter'.\n"
    
    "3. CEOPreferenceLearningAgent - Learns and tracks the CEO's preferences, patterns, and typical approaches "
    "   to decision-making. Answers questions like 'what are my typical preferences for...', "
    "   'how do I usually approach...', or personalization requests.\n"
    
    "4. NorthStarAgent - Manages the company's core strategic elements: Purpose, Vision, Mission, Values, "
    "   and Strategic Goals. Handles questions about 'our north star metric', 'company vision', "
    "   'strategic objectives', OKRs, and goal alignment.\n"
    
    "5. InsightSynthesisAgent - Synthesizes insights from multiple sources including strategic decisions, "
    "   market analysis, and internal data. Use for requests like 'synthesize insights from...', "
    "   'what patterns emerge from...', or 'key takeaways from our analysis'.\n"
    
    "ANALYSIS & INTELLIGENCE SYSTEM:\n"
    "6. SWOTTOWSAgent - Performs comprehensive SWOT (Strengths, Weaknesses, Opportunities, Threats) analysis "
    "   and generates TOWS strategies. Use for 'SWOT analysis', 'analyze our strengths and weaknesses', "
    "   'strategic positioning', or 'TOWS matrix' requests.\n"
    
    "7. RiskOpportunityAgent - Dual-purpose agent that identifies and analyzes both risks AND opportunities. "
    "   Handles 'identify risks', 'risk assessment', 'find opportunities', 'market opportunities', "
    "   'potential threats', and impact analysis.\n"
    
    "8. StrategicContextRouter - Routes requests within the strategic foundation domain when the specific "
    "   sub-agent isn't clear. Use for general strategic questions that need further routing.\n"
    
    "9. SOLinkageAgent - Links subjective insights (like CEO observations) with objective data. "
    "   Correlates qualitative insights with quantitative metrics. Use for 'link my observation about...', "
    "   'connect team morale to performance', or 'validate insight with data'.\n"
    
    "PLANNING & EXECUTION SYSTEM:\n"
    "10. PlanningCoordinator - Coordinates complex planning activities across multiple domains. "
    "    Use for 'create a comprehensive plan', 'coordinate planning for...', or multi-faceted planning requests.\n"
    
    "11. InitiativeGenerator - Creates strategic initiatives and action plans based on analysis and goals. "
    "    Handles 'generate initiatives', 'create action plan', 'strategic initiatives based on...', "
    "    or 'how to achieve goal X'.\n"
    
    "12. ResourceOptimizer - Optimizes resource allocation including budget, personnel, time, and equipment. "
    "    Handles 'optimize resources', 'resource allocation', 'capacity planning', or 'budget optimization'.\n"
    
    "13. TimelineStrategist - Creates strategic timelines and roadmaps for initiatives and projects. "
    "    Use for 'create timeline', 'product roadmap', 'milestone planning', or 'delivery schedule'.\n"
    
    "14. DependencyMapper - Maps and analyzes dependencies between initiatives, projects, and resources. "
    "    Handles 'dependency analysis', 'what depends on...', 'critical path', or 'interdependencies'.\n"
    
    "15. ExecutionTracker - Tracks execution progress of strategic initiatives and milestones. "
    "    Use for 'track progress', 'execution status', 'milestone updates', or 'initiative tracking'.\n\n"
    
    "ROUTING APPROACH:\n"
    "1. Carefully read and understand the user's request\n"
    "2. Consider the intent and context of the request\n"
    "3. Match the request to the most appropriate specialist agent based on their capabilities\n"
    "4. If multiple agents could handle it, choose the most specific one\n"
    "5. Explain your routing decision\n\n"
    
    "IMPORTANT: Use your understanding of language and context to make intelligent routing decisions. "
    "Don't rely on keyword matching - understand the intent behind the request."
)
```

#### 2.2 Deploy the New Orchestrator
```bash
python backend/agentic/scripts/deploy_main_orchestrator_plugin_based.py
```

### 3. Create Agent Invocation Handler

Create `backend/agentic/scripts/invoke_specialist_from_orchestrator.py`:

```python
async def parse_orchestrator_response(response: str) -> tuple[str, str]:
    """
    Parse the orchestrator's routing decision.
    Returns: (agent_name, reasoning)
    """
    # The orchestrator should respond with format:
    # "ROUTE TO: [AgentName] - REASON: [reasoning]"
    # But with LLM-based routing, it might vary
    
    # Extract agent name and reasoning using flexible parsing
    # This allows the LLM to express routing naturally
    
async def invoke_specialist_agent(agent_name: str, user_request: str):
    """
    Invoke the actual specialist agent based on orchestrator's decision.
    Map agent names to their deployed IDs.
    """
    agent_mapping = {
        "CEOLogAgent": "asst_N5azTOnrhdlm4K9wC6i9OtHA",
        "CEOMemoryAgent": "asst_ZV2p9TPa2l6XASy0nzl6O1hb",
        "CEOPreferenceLearningAgent": "asst_t3B2YUPgg9Fq9KS6fLQMASFX",
        "NorthStarAgent": "asst_JRJqOxzgJGCAm6vT1JUxglJa",
        "InsightSynthesisAgent": "asst_s4BQq86uPMhXGt5rmIqUHj5M",
        "SWOTTOWSAgent": "asst_g6qgPv2Ke8YcJZ7qBnf7NLFP",
        "RiskOpportunityAgent": "asst_HYttqPOdNXlVC7NkgEXCq5MQ",
        "StrategicContextRouter": "asst_xo3fBCcBHNV0Fc7GUMSaVOVa",
        "SOLinkageAgent": "asst_9xKPvtFVA70P5Y1AvdJ2Y69d",
        "PlanningCoordinator": "asst_TJJvOiJzblHg17rV6ogI9pTR",
        "InitiativeGenerator": "asst_iWTKVDG4xrXja8xhSKq2QDAK",
        "ResourceOptimizer": "asst_LCi9P7YMdeeKzN8nES8xgEUP",
        "TimelineStrategist": "asst_sWPe2cMx4eF2mqXVhVo7kFMq",
        "DependencyMapper": "asst_kGQZGft8ItT0VjBvLtP1VhJd",
        "ExecutionTracker": "asst_M8fmaDQIdUCUeP6HM9x02FRX"
    }
    
    # Get agent ID and invoke
    agent_id = agent_mapping.get(agent_name)
    if agent_id:
        # Invoke the specialist agent
        response = await invoke_agent(agent_id, user_request)
        return response
    else:
        return f"Unknown agent: {agent_name}"
```

### 4. Test the New Orchestrator

Create `backend/agentic/scripts/test_llm_based_orchestration.py`:

```python
# Test various requests to ensure LLM-based routing works
test_cases = [
    {
        "request": "I need to record a strategic decision about expanding into Asia",
        "expected_agent": "CEOLogAgent"
    },
    {
        "request": "What strategic decisions did we make last quarter?",
        "expected_agent": "CEOMemoryAgent"  
    },
    {
        "request": "What are my typical preferences when making expansion decisions?",
        "expected_agent": "CEOPreferenceLearningAgent"
    },
    {
        "request": "What is our north star metric?",
        "expected_agent": "NorthStarAgent"
    },
    {
        "request": "Perform a SWOT analysis for our new product",
        "expected_agent": "SWOTTOWSAgent"
    },
    # ... test all 15 agents
]

# For each test:
# 1. Send request to orchestrator
# 2. Parse orchestrator's routing decision
# 3. Verify it chose the expected agent (or a reasonable alternative)
# 4. Log the LLM's reasoning
```

### 5. Integration with FastAPI

Update `backend/agentic/api/routes/agents.py`:

```python
@router.post("/orchestrate")
async def orchestrate_request(request: OrchestrationRequest):
    """
    Handle orchestration using LLM-based routing.
    """
    # 1. Send request to Main Orchestrator
    orchestrator_response = await invoke_orchestrator(request.message)
    
    # 2. Parse the routing decision (agent name and reasoning)
    agent_name, reasoning = parse_orchestrator_response(orchestrator_response)
    
    # 3. Invoke the chosen specialist agent
    specialist_response = await invoke_specialist_agent(agent_name, request.message)
    
    # 4. Return complete response
    return {
        "routing_decision": {
            "agent": agent_name,
            "reasoning": reasoning
        },
        "response": specialist_response
    }
```

### 6. Telemetry Updates

Ensure telemetry captures:
- Orchestrator's routing decision
- LLM's reasoning for the choice
- Specialist agent invocation
- End-to-end flow

### 7. Documentation

Update documentation to explain:
- The orchestrator uses LLM reasoning, not hardcoded rules
- How to update agent descriptions to improve routing
- The flexibility of natural language routing

## Expected Outcome

After implementation:
1. **No hardcoded routing** - The orchestrator uses its LLM to understand requests
2. **Natural routing decisions** - Based on understanding intent, not keyword matching  
3. **Flexible routing** - Can handle novel requests by understanding context
4. **Explainable decisions** - The LLM explains why it chose each agent
5. **Easy to update** - Just modify agent descriptions in instructions

## Testing Success Criteria

1. All 15 agents can be correctly routed to based on natural language requests
2. The orchestrator provides clear reasoning for its routing decisions
3. Novel/ambiguous requests are handled intelligently
4. No function tool errors or hardcoded function names
5. The system gracefully handles requests that could go to multiple agents