"""Strategic Context Router - Routes requests within Strategic Foundation system.

This router handles:
- CEO log entries
- North Star queries
- Memory operations
- Preference updates
"""

from typing import Dict, Any, Optional
from semantic_kernel import Kernel
from semantic_kernel.functions import KernelFunctionFromPrompt
from ...common.base_agent import RouterAgent, BaseStratosAgent


class StrategicContextRouter(RouterAgent):
    """Routes requests within the Strategic Foundation & Insights system."""
    
    def __init__(self, kernel: Kernel, specialized_agents: Dict[str, BaseStratosAgent]):
        """Initialize Strategic Context Router.
        
        Args:
            kernel: Semantic Kernel instance
            specialized_agents: Dictionary of specialized agents
        """
        instructions = """
You are the Strategic Context Router for the Strategic Foundation & Insights System.
Your role is to analyze incoming requests and route them to the appropriate specialized agent.

Available agents and their responsibilities:
- CEOLogAgent: Handles CEO log entries, voice transcription, tag generation, summarization
- NorthStarAgent: Manages purpose, vision, values, and strategic goals
- MemoryRecallAgent: Performs context retrieval, pattern recognition, and semantic search
- PreferenceLearningAgent: Tracks feedback, updates preferences, and handles personalization

Analyze the request type, content, and intent to determine the best agent to handle it.
"""
        
        super().__init__(
            name="StrategicContextRouter",
            instructions=instructions,
            kernel=kernel,
            specialized_agents=specialized_agents,
            description="Routes requests within Strategic Foundation system"
        )
        
        # Create routing function
        self._create_routing_function(kernel)
    
    def _create_routing_function(self, kernel: Kernel):
        """Create the routing decision function."""
        agent_list = "\n".join([f"- {name}: {agent.description}" 
                               for name, agent in self.specialized_agents.items()])
        
        self.routing_function = KernelFunctionFromPrompt(
            function_name="route_strategic_request",
            prompt=f"""
Analyze the request and determine which agent should handle it.

Available agents:
{agent_list}

Request type: {{{{$request_type}}}}
Request content: {{{{$request_content}}}}

ROUTING RULES:
1. CEO log operations (entries, voice, transcription) → CEOLogAgent
2. Strategic elements (purpose, vision, values, goals) → NorthStarAgent  
3. Context retrieval, search, pattern analysis → MemoryRecallAgent
4. Preference tracking, personalization, feedback → PreferenceLearningAgent

Respond with ONLY the agent name (e.g., CEOLogAgent):
""",
            kernel=kernel
        )
    
    async def route_request(self, request: Dict[str, Any]) -> str:
        """Determine which agent should handle the request.
        
        Args:
            request: Incoming request with type and content
            
        Returns:
            Name of agent to handle request
        """
        request_type = request.get("type", "unknown")
        
        # Quick routing for common types
        if request_type in ["ceo_log", "voice_entry", "transcription"]:
            return "CEOLogAgent"
        elif request_type in ["north_star", "vision", "values", "goals"]:
            return "NorthStarAgent"
        elif request_type in ["memory_query", "context_search", "pattern_analysis"]:
            return "MemoryRecallAgent"
        elif request_type in ["preference_update", "feedback", "personalization"]:
            return "PreferenceLearningAgent"
        
        # Use LLM for complex routing
        result = await self.routing_function.invoke(
            request_type=request_type,
            request_content=str(request.get("content", ""))
        )
        
        agent_name = result.value[0].strip() if result.value else "CEOLogAgent"
        
        # Validate agent name
        if agent_name not in self.specialized_agents:
            # Fallback to CEO Log Agent for unknown routes
            agent_name = "CEOLogAgent"
        
        return agent_name