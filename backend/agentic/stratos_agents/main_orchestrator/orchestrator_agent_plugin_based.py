#!/usr/bin/env python3
"""
Main Orchestrator Agent for StratOS using plugin-based architecture.
Following the pattern from semantic_kernel_multi_agent example.
"""

from semantic_kernel import Kernel
from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)

class StratOSSpecialistAgent:
    """Base class for StratOS specialist agents that can be used as plugins"""
    
    def __init__(self, agent_id: str, agent_name: str, service=None):
        """
        Initialize a specialist agent
        
        Args:
            agent_id: The Azure AI Agent Service ID
            agent_name: Human-friendly name for the agent
            service: An optional pre-configured service
        """
        self.agent_id = agent_id
        self.agent_name = agent_name
        
        if service is None:
            service = AzureChatCompletion()
            
        # Create the agent with specific instructions for routing
        self.agent = ChatCompletionAgent(
            service=service,
            name=agent_name,
            instructions=f"You are {agent_name}, a specialized agent in the StratOS system. Your agent ID is {agent_id}."
        )
    
    def get_agent(self):
        """Get the underlying ChatCompletionAgent"""
        return self.agent


class MainOrchestratorAgent:
    """
    Main Orchestrator agent that routes requests to appropriate StratOS specialist agents.
    Uses the plugin pattern from semantic_kernel_multi_agent.
    """
    
    def __init__(self, service=None, specialist_agents: Optional[List[dict]] = None):
        """
        Initialize orchestrator with specialist agents as plugins
        
        Args:
            service: An optional pre-configured service
            specialist_agents: List of dicts with agent info [{agent_id, agent_name}, ...]
        """
        if service is None:
            service = AzureChatCompletion()
        
        # Create a kernel for the orchestrator
        kernel = Kernel()
        
        # Create specialist agents and collect them
        agent_plugins = []
        agent_descriptions = []
        
        if specialist_agents:
            for agent_info in specialist_agents:
                agent_id = agent_info['agent_id']
                agent_name = agent_info['agent_name']
                
                # Create specialist agent
                specialist = StratOSSpecialistAgent(agent_id, agent_name, service)
                agent_plugins.append(specialist.get_agent())
                
                # Build description for instructions
                agent_descriptions.append(f"- {agent_name}: {agent_info.get('description', 'Specialized agent')}")
        
        # Build comprehensive routing instructions
        agent_list = "\n".join(agent_descriptions)
        
        # Create the orchestrator agent with all specialist agents as plugins
        self.agent = ChatCompletionAgent(
            service=service,
            kernel=kernel,
            name="MainOrchestrator",
            instructions=(
                "You are the Main Orchestrator for StratOS, a comprehensive strategy operating system. "
                "Your role is to analyze incoming requests and delegate them to the appropriate specialized agent.\n\n"
                
                "AVAILABLE SPECIALIST AGENTS:\n"
                f"{agent_list}\n\n"
                
                "ROUTING APPROACH:\n"
                "1. Analyze the user's request to understand their intent\n"
                "2. Identify which specialized agent is best suited to handle the request\n"
                "3. Route the request to that agent by invoking them\n"
                "4. Return the specialized agent's response to the user\n\n"
                
                "ROUTING GUIDELINES:\n"
                "- For CEO notes, observations, or log entries → CEOLogAgent\n"
                "- For questions about vision, mission, values → NorthStarAgent\n"
                "- For SWOT analysis requests → SWOTTOWSAgent\n"
                "- For risk assessment → RiskOpportunityAgent (handles risks)\n"
                "- For opportunity identification → RiskOpportunityAgent (handles opportunities)\n"
                "- For linking insights with data → SOLinkageAgent\n"
                "- For creating initiatives or action plans → InitiativeGenerationAgent\n"
                "- For resource allocation or optimization → ResourceOptimizationAgent\n"
                "- For strategic canvas or visualization → CanvasVisualizationAgent\n"
                "- For alignment assessment → AlignmentScoringAgent\n"
                "- For detailed execution planning → ActionPlanningAgent\n"
                "- For retrieving past context or patterns → MemoryRecallAgent\n"
                "- For user preference tracking → PreferenceLearningAgent\n\n"
                
                "Do not try to answer questions yourself - your role is purely to route "
                "requests to the appropriate specialist. Always explain which agent you're "
                "routing to and why before invoking it."
            ),
            plugins=agent_plugins,  # All specialist agents as plugins
        )
        
        logger.info(f"MainOrchestrator created with {len(agent_plugins)} specialist agent plugins")
    
    def get_agent(self):
        """Get the underlying ChatCompletionAgent"""
        return self.agent


def create_main_orchestrator_for_deployment():
    """
    Create the Main Orchestrator configured for all StratOS agents.
    This will be used for deployment to Azure AI Agent Service.
    """
    # Define all StratOS specialist agents
    specialist_agents = [
        {
            "agent_id": "CEOLogAgent",
            "agent_name": "CEOLogAgent",
            "description": "Handles CEO's subjective inputs, notes, observations, and concerns"
        },
        {
            "agent_id": "NorthStarAgent", 
            "agent_name": "NorthStarAgent",
            "description": "Manages Purpose, Vision, Values, and Strategic Goals"
        },
        {
            "agent_id": "SWOTTOWSAgent",
            "agent_name": "SWOTTOWSAgent", 
            "description": "Performs SWOT analysis and generates TOWS strategies"
        },
        {
            "agent_id": "RiskOpportunityAgent",
            "agent_name": "OpportunityScoutAgent",
            "description": "Identifies opportunities from market analysis"
        },
        {
            "agent_id": "RiskOpportunityAgent",
            "agent_name": "RiskRadarAgent",
            "description": "Detects and analyzes risks"
        },
        {
            "agent_id": "SOLinkageAgent",
            "agent_name": "CompetitorInsightsAgent",
            "description": "Provides competitive intelligence"
        },
        {
            "agent_id": "InitiativeGenerationAgent",
            "agent_name": "StrategicInitiativesAgent",
            "description": "Creates strategic initiatives and action plans"
        },
        {
            "agent_id": "ResourceOptimizationAgent",
            "agent_name": "ResourceOptimizerAgent",
            "description": "Manages resource allocation and capacity planning"
        },
        {
            "agent_id": "ActionPlanningAgent",
            "agent_name": "ExecutionTrackerAgent",
            "description": "Tracks execution progress and milestones"
        },
        {
            "agent_id": "CanvasVisualizationAgent",
            "agent_name": "CanvasAgent",
            "description": "Handles visual strategic planning on canvas"
        },
        {
            "agent_id": "AlignmentScoringAgent",
            "agent_name": "ConversationAgent",
            "description": "Manages strategic conversations and alignment"
        },
        {
            "agent_id": "MemoryRecallAgent",
            "agent_name": "MemoryRecallAgent",
            "description": "Retrieves context, patterns, and historical information"
        },
        {
            "agent_id": "PreferenceLearningAgent",
            "agent_name": "PreferenceLearningAgent",
            "description": "Tracks user preferences and personalizes experiences"
        }
    ]
    
    # Create and return the orchestrator
    orchestrator = MainOrchestratorAgent(specialist_agents=specialist_agents)
    return orchestrator.get_agent()