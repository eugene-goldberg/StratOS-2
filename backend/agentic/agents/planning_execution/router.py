"""Planning & Execution System Router

Routes requests to appropriate planning and execution agents based on intent.
"""

import asyncio
import json
from typing import Dict, Any, List, Optional
from semantic_kernel import Kernel
from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.contents import ChatMessageContent, AuthorRole

from common.base_agent import BaseStratosAgent


class PlanningCoordinator(BaseStratosAgent):
    """Orchestrates routing for the Planning & Execution System"""
    
    def __init__(self):
        super().__init__(
            name="Planning Coordinator",
            description="Routes planning and execution requests to specialized agents",
            model="gpt-4o"  # Use advanced model for routing decisions
        )
        
        # Define available agents and their capabilities
        self.agent_capabilities = {
            "initiative_generation": {
                "agent": "InitiativeGenerationAgent",
                "description": "Creates strategic initiatives aligned with goals and generates action plans",
                "keywords": ["initiative", "project", "program", "strategic plan", "create plan", "new initiative"]
            },
            "resource_optimization": {
                "agent": "ResourceOptimizationAgent", 
                "description": "Optimizes resource allocation across initiatives and tracks utilization",
                "keywords": ["resource", "allocation", "budget", "capacity", "optimize", "utilization", "assign"]
            },
            "canvas_visualization": {
                "agent": "CanvasVisualizationAgent",
                "description": "Manages strategic canvas operations, visualization, and voice commands",
                "keywords": ["canvas", "visualize", "diagram", "flow", "nodes", "connections", "layout", "voice command"]
            },
            "alignment_scoring": {
                "agent": "AlignmentScoringAgent",
                "description": "Scores strategic alignment and validates plans against North Star",
                "keywords": ["alignment", "score", "validate", "assess", "fit", "north star", "strategic fit"]
            },
            "action_planning": {
                "agent": "ActionPlanningAgent",
                "description": "Breaks down initiatives into actionable tasks with dependencies",
                "keywords": ["action", "task", "breakdown", "steps", "dependencies", "timeline", "milestone"]
            }
        }
        
    async def _create_routing_agent(self) -> ChatCompletionAgent:
        """Create the routing agent with specific instructions"""
        
        instructions = f"""You are the Planning Coordinator for the StratOS Planning & Execution System.
        
Your role is to:
1. Understand the user's planning or execution request
2. Route to the most appropriate specialized agent
3. Provide clear context for the selected agent

Available agents:
{json.dumps(self.agent_capabilities, indent=2)}

Routing guidelines:
- For creating new initiatives or strategic plans -> initiative_generation
- For resource allocation, optimization, or tracking -> resource_optimization
- For canvas visualization, diagramming, or voice commands -> canvas_visualization
- For assessing strategic fit or alignment scores -> alignment_scoring
- For breaking down initiatives into tasks -> action_planning
- If unclear, ask clarifying questions

Always respond with a JSON object containing:
{{
    "selected_agent": "agent_name",
    "reasoning": "why this agent was selected",
    "context": "relevant context to pass to the agent",
    "clarification_needed": false,
    "clarification_question": null
}}"""

        return ChatCompletionAgent(
            service_id="planning_router",
            kernel=self.kernel,
            name="PlanningRouter",
            instructions=instructions
        )
        
    async def process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process planning request and route to appropriate agent"""
        
        try:
            # Extract request details
            user_query = request.get("query", "")
            context = request.get("context", {})
            user_id = request.get("user_id")
            
            # Create routing agent
            router = await self._create_routing_agent()
            
            # Prepare routing request
            routing_prompt = f"""
User Query: {user_query}
Context: {json.dumps(context, indent=2)}

Analyze this request and determine which specialized planning agent should handle it.
"""
            
            # Get routing decision
            response = await router.invoke(routing_prompt)
            
            try:
                routing_decision = json.loads(response.content)
            except json.JSONDecodeError:
                # Fallback if response isn't valid JSON
                routing_decision = {
                    "selected_agent": "initiative_generation",  # Default to initiative
                    "reasoning": "Could not parse routing decision, defaulting to initiative generation",
                    "context": user_query,
                    "clarification_needed": False
                }
            
            # Check if clarification is needed
            if routing_decision.get("clarification_needed", False):
                return {
                    "status": "clarification_needed",
                    "message": routing_decision.get("clarification_question", "Could you please clarify your planning request?"),
                    "suggestions": self._get_example_queries()
                }
            
            # Route to selected agent
            selected_agent = routing_decision.get("selected_agent")
            
            if selected_agent not in self.agent_capabilities:
                return {
                    "status": "error",
                    "message": f"Unknown agent: {selected_agent}",
                    "available_agents": list(self.agent_capabilities.keys())
                }
            
            # Prepare agent request
            agent_request = {
                "query": user_query,
                "context": routing_decision.get("context", ""),
                "user_id": user_id,
                "original_context": context,
                "routing_reason": routing_decision.get("reasoning", "")
            }
            
            # Import and instantiate the selected agent
            if selected_agent == "initiative_generation":
                from .initiative_generation_agent import InitiativeGenerationAgent
                agent = InitiativeGenerationAgent()
            elif selected_agent == "resource_optimization":
                from .resource_optimization_agent import ResourceOptimizationAgent
                agent = ResourceOptimizationAgent()
            elif selected_agent == "canvas_visualization":
                from .canvas_visualization_agent import CanvasVisualizationAgent
                agent = CanvasVisualizationAgent()
            elif selected_agent == "alignment_scoring":
                from .alignment_scoring_agent import AlignmentScoringAgent
                agent = AlignmentScoringAgent()
            elif selected_agent == "action_planning":
                from .action_planning_agent import ActionPlanningAgent
                agent = ActionPlanningAgent()
            
            # Process with selected agent
            result = await agent.process(agent_request)
            
            # Add routing metadata
            result["routing_metadata"] = {
                "selected_agent": selected_agent,
                "reasoning": routing_decision.get("reasoning"),
                "router": self.name
            }
            
            return result
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Planning routing failed: {str(e)}",
                "suggestions": self._get_example_queries()
            }
    
    def _get_example_queries(self) -> List[str]:
        """Get example queries for each agent type"""
        return [
            "Create a new initiative for digital transformation",
            "Optimize resource allocation across our projects",
            "Visualize our strategic plan on the canvas",
            "Score the alignment of our Q3 initiatives",
            "Break down the marketing initiative into tasks",
            "Show resource utilization dashboard"
        ]