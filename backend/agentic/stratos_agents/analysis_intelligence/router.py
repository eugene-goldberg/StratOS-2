"""Analysis & Intelligence System Router

Routes requests to appropriate analysis agents based on intent.
"""

import asyncio
import json
from typing import Dict, Any, List, Optional
from semantic_kernel import Kernel
from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.contents import ChatMessageContent, AuthorRole

from common.base_agent import BaseStratosAgent


class AnalysisOrchestrator(BaseStratosAgent):
    """Orchestrates routing for the Analysis & Intelligence System"""
    
    def __init__(self):
        super().__init__(
            name="Analysis Orchestrator",
            description="Routes analysis requests to specialized agents",
            model="gpt-4o"  # Use advanced model for routing decisions
        )
        
        # Define available agents and their capabilities
        self.agent_capabilities = {
            "swot_tows": {
                "agent": "SwotTowsAgent",
                "description": "Handles SWOT analysis, TOWS strategy generation, and guided analysis sessions",
                "keywords": ["swot", "tows", "strength", "weakness", "opportunity", "threat", "strategy", "guided analysis"]
            },
            "risk_opportunity": {
                "agent": "RiskOpportunityAgent", 
                "description": "Detects and analyzes risks and opportunities from various data sources",
                "keywords": ["risk", "opportunity", "threat detection", "chance", "potential", "alert", "warning"]
            },
            "so_linkage": {
                "agent": "SOLinkageAgent",
                "description": "Discovers connections between subjective insights and objective data",
                "keywords": ["linkage", "connection", "correlation", "pattern", "subjective objective", "insight", "relationship"]
            }
        }
        
    async def _create_routing_agent(self) -> ChatCompletionAgent:
        """Create the routing agent with specific instructions"""
        
        instructions = f"""You are the Analysis Orchestrator for the StratOS Analysis & Intelligence System.
        
Your role is to:
1. Understand the user's analysis request
2. Route to the most appropriate specialized agent
3. Provide clear context for the selected agent

Available agents:
{json.dumps(self.agent_capabilities, indent=2)}

Routing guidelines:
- For SWOT analysis, strategy generation, or guided sessions -> swot_tows
- For risk detection, opportunity identification, or alerts -> risk_opportunity  
- For finding connections between subjective and objective data -> so_linkage
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
            service_id="analysis_router",
            kernel=self.kernel,
            name="AnalysisRouter",
            instructions=instructions
        )
        
    async def process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process analysis request and route to appropriate agent"""
        
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

Analyze this request and determine which specialized analysis agent should handle it.
"""
            
            # Get routing decision
            response = await router.invoke(routing_prompt)
            
            try:
                routing_decision = json.loads(response.content)
            except json.JSONDecodeError:
                # Fallback if response isn't valid JSON
                routing_decision = {
                    "selected_agent": "swot_tows",  # Default to SWOT
                    "reasoning": "Could not parse routing decision, defaulting to SWOT analysis",
                    "context": user_query,
                    "clarification_needed": False
                }
            
            # Check if clarification is needed
            if routing_decision.get("clarification_needed", False):
                return {
                    "status": "clarification_needed",
                    "message": routing_decision.get("clarification_question", "Could you please clarify your analysis request?"),
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
            if selected_agent == "swot_tows":
                from .swot_tows_agent import SwotTowsAgent
                agent = SwotTowsAgent()
            elif selected_agent == "risk_opportunity":
                from .risk_opportunity_agent import RiskOpportunityAgent
                agent = RiskOpportunityAgent()
            elif selected_agent == "so_linkage":
                from .so_linkage_agent import SOLinkageAgent
                agent = SOLinkageAgent()
            
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
                "message": f"Analysis routing failed: {str(e)}",
                "suggestions": self._get_example_queries()
            }
    
    def _get_example_queries(self) -> List[str]:
        """Get example queries for each agent type"""
        return [
            "Generate a SWOT analysis for our new product launch",
            "What are the key risks in our current strategy?",
            "Find connections between customer feedback and sales data",
            "Start a guided SWOT analysis session",
            "Identify opportunities from market trends",
            "Show correlations between employee sentiment and productivity"
        ]