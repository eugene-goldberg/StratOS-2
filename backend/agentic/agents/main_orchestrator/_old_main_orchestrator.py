#!/usr/bin/env python3
"""
Main Orchestrator Agent that routes requests to all StratOS specialized agents.
This implementation follows the exact pattern from semantic_kernel_multi_agent.
"""

from semantic_kernel import Kernel
from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion

from ..strategic_foundation.ceo_log_agent import CEOLogAgent
from ..strategic_foundation.north_star_agent import NorthStarAgent
from ..strategic_foundation.memory_recall_agent import MemoryRecallAgent
from ..strategic_foundation.preference_learning_agent import PreferenceLearningAgent
from ..analysis_intelligence.swot_tows_agent import SWOTTOWSAgent
from ..analysis_intelligence.risk_opportunity_agent import RiskOpportunityAgent
from ..analysis_intelligence.so_linkage_agent import SOLinkageAgent
from ..planning_execution.alignment_scoring_agent import AlignmentScoringAgent
from ..planning_execution.initiative_generation_agent import InitiativeGenerationAgent
from ..planning_execution.resource_optimization_agent import ResourceOptimizationAgent
from ..planning_execution.action_planning_agent import ActionPlanningAgent
from ..planning_execution.canvas_visualization_agent import CanvasVisualizationAgent

class MainOrchestratorAgent:
    """
    Orchestrator agent that routes requests to appropriate specialist agents.
    """
    
    def __init__(self, service=None):
        """
        Initialize orchestrator with all specialist agents
        
        Args:
            service: An optional pre-configured service
        """
        if service is None:
            # Create a new service if none is provided
            service = AzureChatCompletion()
        
        # Create a kernel with filters for debugging
        kernel = Kernel()
        
        # Create specialist agents
        ceo_log_agent = CEOLogAgent(service).get_agent()
        north_star_agent = NorthStarAgent(service).get_agent()
        memory_recall_agent = MemoryRecallAgent(service).get_agent()
        preference_learning_agent = PreferenceLearningAgent(service).get_agent()
        swot_tows_agent = SWOTTOWSAgent(service).get_agent()
        risk_opportunity_agent = RiskOpportunityAgent(service).get_agent()
        so_linkage_agent = SOLinkageAgent(service).get_agent()
        alignment_scoring_agent = AlignmentScoringAgent(service).get_agent()
        initiative_generation_agent = InitiativeGenerationAgent(service).get_agent()
        resource_optimization_agent = ResourceOptimizationAgent(service).get_agent()
        action_planning_agent = ActionPlanningAgent(service).get_agent()
        canvas_visualization_agent = CanvasVisualizationAgent(service).get_agent()
        
        # Create the orchestrator agent with the plugins
        plugins = [
            ceo_log_agent, north_star_agent, memory_recall_agent, preference_learning_agent,
            swot_tows_agent, risk_opportunity_agent, so_linkage_agent, alignment_scoring_agent,
            initiative_generation_agent, resource_optimization_agent, action_planning_agent,
            canvas_visualization_agent
        ]
        
        self.agent = ChatCompletionAgent(
            service=service,
            kernel=kernel,
            name="MainOrchestratorAgent",
            instructions=(
                "You are a triage agent that routes user requests to the appropriate specialist agent in the StratOS system. "
                
                "If the request is about CEO notes, observations, or subjective inputs, direct it to the CEOLogAgent. "
                
                "If the request is about vision, mission, values, purpose, or strategic goals, direct it to the NorthStarAgent. "
                
                "If the request is about retrieving past context, patterns, or historical information, direct it to the MemoryRecallAgent. "
                
                "If the request is about user preferences or personalization, direct it to the PreferenceLearningAgent. "
                
                "If the request involves SWOT analysis or TOWS strategies, direct it to the SWOTTOWSAgent. "
                
                "If the request is about risk assessment or opportunity identification, direct it to the RiskOpportunityAgent. "
                
                "If the request is about linking subjective insights with objective data, direct it to the SOLinkageAgent. "
                
                "If the request is about strategic alignment assessment or scoring, direct it to the AlignmentScoringAgent. "
                
                "If the request is about creating strategic initiatives or high-level planning, direct it to the InitiativeGenerationAgent. "
                
                "If the request involves resource allocation, optimization, or capacity planning, direct it to the ResourceOptimizationAgent. "
                
                "If the request is about detailed action planning, task breakdown, progress tracking, dependencies, milestones, or KPIs, direct it to the ActionPlanningAgent. "
                
                "If the request is about strategic canvas, visualization, or visual planning, direct it to the CanvasVisualizationAgent. "
                
                "Your job is to determine which specialist can best answer the query and route "
                "accordingly. Do not try to answer questions yourself - your role is purely to route "
                "requests to the appropriate specialist. Always clarify which agent you're routing to "
                "and why it's the most appropriate choice."
            ),
            plugins=plugins,
        )
    
    def get_agent(self):
        """Get the underlying ChatCompletionAgent"""
        return self.agent