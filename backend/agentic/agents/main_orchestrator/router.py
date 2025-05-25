"""Deterministic routing logic for Main Orchestrator."""

import re
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
import logging

from .config import (
    TaskType, AgentName, TASK_AGENT_MAPPING, 
    KEYWORD_PATTERNS, WORKFLOW_DEFINITIONS,
    ERROR_MESSAGES
)
from .domain_patterns import Domain, DomainIdentifier


logger = logging.getLogger(__name__)


class RoutingDecision:
    """Represents a routing decision made by the router."""
    
    def __init__(self,
                 route_type: str,  # "agent", "workflow", "error", "clarification"
                 target: Optional[str] = None,  # Agent name or workflow name
                 params: Optional[Dict] = None,
                 confidence: float = 1.0,
                 reasoning: str = "",
                 error_message: Optional[str] = None,
                 clarification_needed: bool = False,
                 clarification_question: Optional[str] = None):
        self.route_type = route_type
        self.target = target
        self.params = params or {}
        self.confidence = confidence
        self.reasoning = reasoning
        self.error_message = error_message
        self.clarification_needed = clarification_needed
        self.clarification_question = clarification_question
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "route_type": self.route_type,
            "target": self.target,
            "params": self.params,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "error_message": self.error_message,
            "clarification_needed": self.clarification_needed,
            "clarification_question": self.clarification_question
        }


class DeterministicRouter:
    """
    Deterministic router for the Main Orchestrator.
    Routes requests to appropriate agents or workflows based on rules.
    """
    
    def __init__(self):
        self.domain_identifier = DomainIdentifier()
        self._compile_keyword_patterns()
    
    def _compile_keyword_patterns(self):
        """Pre-compile keyword patterns for efficiency."""
        self.compiled_patterns = {}
        for agent, keywords in KEYWORD_PATTERNS.items():
            # Create a single regex pattern for all keywords of an agent
            pattern = r'\b(' + '|'.join(re.escape(kw) for kw in keywords) + r')\b'
            self.compiled_patterns[agent] = re.compile(pattern, re.IGNORECASE)
    
    def route(self, 
              request: Dict,
              session_context: Optional[Dict] = None) -> RoutingDecision:
        """
        Route a request to the appropriate agent or workflow.
        
        Args:
            request: The incoming request with fields like task_type, user_query, payload
            session_context: Optional session context with conversation history
            
        Returns:
            RoutingDecision object with routing information
        """
        try:
            # 1. Try explicit task type routing first
            if "task_type" in request and request["task_type"]:
                decision = self._route_by_task_type(request)
                if decision.route_type != "error":
                    return decision
            
            # 2. Check for workflow patterns
            decision = self._check_workflow_patterns(request, session_context)
            if decision and decision.route_type == "workflow":
                return decision
            
            # 3. Try state-based routing
            if session_context:
                decision = self._route_by_state(request, session_context)
                if decision and decision.route_type != "error":
                    return decision
            
            # 4. Try keyword/pattern matching
            decision = self._route_by_keywords(request)
            if decision.route_type != "error":
                return decision
            
            # 5. Try domain-based routing as last resort
            decision = self._route_by_domain(request, session_context)
            if decision.route_type != "error":
                return decision
            
            # 6. No route found - need clarification
            return self._create_clarification_decision(request)
            
        except Exception as e:
            logger.error(f"Error in routing: {str(e)}")
            return RoutingDecision(
                route_type="error",
                error_message=ERROR_MESSAGES["general_error"],
                reasoning=f"Routing error: {str(e)}"
            )
    
    def _route_by_task_type(self, request: Dict) -> RoutingDecision:
        """Route based on explicit task type."""
        task_type_str = request.get("task_type", "").upper()
        
        try:
            task_type = TaskType(task_type_str)
        except ValueError:
            # Unknown task type
            return RoutingDecision(
                route_type="error",
                error_message=f"Unknown task type: {task_type_str}",
                reasoning="Task type not recognized"
            )
        
        # Check if it's a workflow task
        if "WORKFLOW" in task_type_str:
            return self._create_workflow_decision(task_type_str, request)
        
        # Map to agent
        agent = TASK_AGENT_MAPPING.get(task_type)
        if agent:
            return RoutingDecision(
                route_type="agent",
                target=agent.value,
                params=request.get("payload", {}),
                confidence=1.0,
                reasoning=f"Explicit task type mapping: {task_type.value} -> {agent.value}"
            )
        
        return RoutingDecision(
            route_type="error",
            error_message=f"No agent mapping for task type: {task_type.value}",
            reasoning="Task type has no configured agent"
        )
    
    def _check_workflow_patterns(self, 
                               request: Dict,
                               session_context: Optional[Dict]) -> Optional[RoutingDecision]:
        """Check if request matches workflow patterns."""
        text = self._extract_searchable_text(request)
        
        # Check for explicit workflow keywords
        workflow_keywords = {
            "strategic planning": "STRATEGIC_PLANNING_WORKFLOW",
            "full review": "FULL_STRATEGIC_REVIEW_WORKFLOW",
            "strategic review": "FULL_STRATEGIC_REVIEW_WORKFLOW",
            "new initiative planning": "NEW_INITIATIVE_PLANNING_WORKFLOW",
            "comprehensive planning": "STRATEGIC_PLANNING_WORKFLOW"
        }
        
        text_lower = text.lower()
        for keyword, workflow_name in workflow_keywords.items():
            if keyword in text_lower:
                return self._create_workflow_decision(workflow_name, request)
        
        return None
    
    def _route_by_state(self,
                       request: Dict,
                       session_context: Dict) -> Optional[RoutingDecision]:
        """Route based on session state/context."""
        # Check for active workflow
        active_workflow = session_context.get("active_workflow")
        if active_workflow:
            # Continue the active workflow
            return RoutingDecision(
                route_type="workflow",
                target=active_workflow,
                params={
                    **request.get("payload", {}),
                    "workflow_state": session_context.get("workflow_state", {})
                },
                confidence=0.9,
                reasoning=f"Continuing active workflow: {active_workflow}"
            )
        
        # Check for context-specific routing
        last_agent = session_context.get("last_agent_used")
        if last_agent == "SWOTTOWSAgent" and "swot" in self._extract_searchable_text(request).lower():
            return RoutingDecision(
                route_type="agent",
                target=AgentName.SWOT_TOWS_AGENT.value,
                params={
                    **request.get("payload", {}),
                    "session_id": session_context.get("session_id")
                },
                confidence=0.85,
                reasoning="Continuing SWOT analysis based on session context"
            )
        
        # Check for initiative context
        if session_context.get("last_viewed_initiative") and "task" in self._extract_searchable_text(request).lower():
            return RoutingDecision(
                route_type="agent",
                target=AgentName.ACTION_PLANNING_AGENT.value,
                params={
                    "initiative_id": session_context["last_viewed_initiative"],
                    "task_details": request.get("user_query", request.get("payload"))
                },
                confidence=0.8,
                reasoning="Adding task to last viewed initiative"
            )
        
        return None
    
    def _route_by_keywords(self, request: Dict) -> RoutingDecision:
        """Route based on keyword pattern matching."""
        text = self._extract_searchable_text(request)
        if not text:
            return RoutingDecision(
                route_type="error",
                error_message="No text content to analyze",
                reasoning="Request contains no analyzable text"
            )
        
        # Score each agent based on keyword matches
        agent_scores: Dict[str, int] = {}
        
        for agent, pattern in self.compiled_patterns.items():
            matches = pattern.findall(text)
            if matches:
                agent_scores[agent] = len(matches)
        
        if not agent_scores:
            return RoutingDecision(
                route_type="error",
                error_message="No keyword matches found",
                reasoning="Text doesn't match any agent keywords"
            )
        
        # Select agent with highest score
        best_agent = max(agent_scores.items(), key=lambda x: x[1])
        agent_name, score = best_agent
        
        # Calculate confidence based on score
        confidence = min(score * 0.2, 1.0)  # Each match adds 0.2 confidence
        
        return RoutingDecision(
            route_type="agent",
            target=agent_name,
            params=request.get("payload", {}),
            confidence=confidence,
            reasoning=f"Keyword matching: {score} matches for {agent_name}"
        )
    
    def _route_by_domain(self,
                        request: Dict,
                        session_context: Optional[Dict]) -> RoutingDecision:
        """Route based on domain identification."""
        domain, confidence = self.domain_identifier.identify_domain(request, session_context)
        
        if domain == Domain.UNKNOWN:
            return RoutingDecision(
                route_type="error",
                error_message="Unable to identify request domain",
                reasoning=f"Domain identification confidence too low: {confidence}"
            )
        
        # Map domain to a default agent
        domain_agent_mapping = {
            Domain.FOUNDATION: AgentName.MEMORY_AGENT,  # General foundation queries
            Domain.ANALYSIS: AgentName.SWOT_TOWS_AGENT,  # General analysis
            Domain.PLANNING: AgentName.INITIATIVE_AGENT,  # General planning
            Domain.WORKFLOW: "STRATEGIC_PLANNING_WORKFLOW"  # Default workflow
        }
        
        target = domain_agent_mapping.get(domain)
        if not target:
            return RoutingDecision(
                route_type="error",
                error_message=f"No default agent for domain: {domain.value}",
                reasoning="Domain has no default agent configured"
            )
        
        route_type = "workflow" if domain == Domain.WORKFLOW else "agent"
        target_str = target if isinstance(target, str) else target.value
        
        return RoutingDecision(
            route_type=route_type,
            target=target_str,
            params=request.get("payload", {}),
            confidence=confidence * 0.7,  # Reduce confidence for domain-based routing
            reasoning=f"Domain-based routing: {domain.value} -> {target_str}"
        )
    
    def _create_workflow_decision(self, 
                                 workflow_name: str,
                                 request: Dict) -> RoutingDecision:
        """Create a workflow routing decision."""
        # Clean up workflow name
        if workflow_name.startswith("TaskType."):
            workflow_name = workflow_name.replace("TaskType.", "")
        
        workflow_def = WORKFLOW_DEFINITIONS.get(workflow_name)
        if not workflow_def:
            return RoutingDecision(
                route_type="error",
                error_message=f"Unknown workflow: {workflow_name}",
                reasoning="Workflow not defined"
            )
        
        # Check required parameters
        missing_params = []
        params = request.get("payload", {})
        
        for required_param in workflow_def.get("required_params", []):
            if required_param not in params and required_param not in request:
                missing_params.append(required_param)
        
        if missing_params:
            return RoutingDecision(
                route_type="error",
                error_message=ERROR_MESSAGES["missing_required_params"].format(
                    params=", ".join(missing_params)
                ),
                reasoning=f"Workflow missing required parameters: {missing_params}"
            )
        
        # Prepare workflow parameters
        workflow_params = {
            **params,
            "user_id": request.get("user_id"),
            "workflow_name": workflow_name,
            "workflow_definition": workflow_def
        }
        
        return RoutingDecision(
            route_type="workflow",
            target=workflow_name,
            params=workflow_params,
            confidence=1.0,
            reasoning=f"Executing workflow: {workflow_name}"
        )
    
    def _create_clarification_decision(self, request: Dict) -> RoutingDecision:
        """Create a clarification decision when routing is ambiguous."""
        text = self._extract_searchable_text(request)
        
        # Try to identify potential agents based on partial matches
        potential_agents = []
        for agent, pattern in self.compiled_patterns.items():
            if pattern.search(text):
                potential_agents.append(agent)
        
        if len(potential_agents) > 1:
            # Multiple potential matches - ask for clarification
            agent_descriptions = {
                "CEOLogAgent": "create a new log entry",
                "SWOTTOWSAgent": "perform strategic analysis",
                "InitiativeGenerationAgent": "create a new initiative",
                "MemoryAgent": "search or retrieve information"
            }
            
            options = []
            for agent in potential_agents[:3]:  # Limit to 3 options
                if agent in agent_descriptions:
                    options.append(agent_descriptions[agent])
            
            question = f"I found multiple ways to help. Would you like to: {', '.join(options)}?"
            
            return RoutingDecision(
                route_type="clarification",
                clarification_needed=True,
                clarification_question=question,
                confidence=0.0,
                reasoning=f"Multiple potential agents: {potential_agents}"
            )
        
        # No matches at all
        return RoutingDecision(
            route_type="clarification",
            clarification_needed=True,
            clarification_question="I'm not sure how to help with that. Could you please provide more details about what you'd like to do?",
            confidence=0.0,
            reasoning="No matching agents or workflows found"
        )
    
    def _extract_searchable_text(self, request: Dict) -> str:
        """Extract all searchable text from request."""
        text_parts = []
        
        # User query is primary source
        if "user_query" in request:
            text_parts.append(str(request["user_query"]))
        
        # Extract from payload
        payload = request.get("payload", {})
        if isinstance(payload, str):
            text_parts.append(payload)
        elif isinstance(payload, dict):
            for key, value in payload.items():
                if isinstance(value, str) and len(value) < 1000:  # Avoid huge texts
                    text_parts.append(value)
        
        # Include task type for context
        if "task_type" in request:
            text_parts.append(request["task_type"].replace("_", " "))
        
        return " ".join(text_parts)