"""Domain identification patterns for routing requests."""

import re
from typing import Dict, List, Optional, Tuple
from enum import Enum


class Domain(Enum):
    """High-level domains in StratOS."""
    FOUNDATION = "foundation"  # Strategic foundation & insights
    ANALYSIS = "analysis"      # Analysis & intelligence
    PLANNING = "planning"      # Planning & execution
    WORKFLOW = "workflow"      # Multi-step workflows
    UNKNOWN = "unknown"


class DomainIdentifier:
    """Identifies the domain of a request based on patterns and context."""
    
    def __init__(self):
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Compile regex patterns for efficient matching."""
        # Foundation domain patterns
        self.foundation_patterns = [
            re.compile(r'\b(ceo|log|note|remember|observation|concern)\b', re.IGNORECASE),
            re.compile(r'\b(purpose|vision|values?|north\s*star|pvv)\b', re.IGNORECASE),
            re.compile(r'\b(memory|recall|retrieve|what did i|find information)\b', re.IGNORECASE),
            re.compile(r'\b(preference|customize|personalize|setting)\b', re.IGNORECASE),
        ]
        
        # Analysis domain patterns
        self.analysis_patterns = [
            re.compile(r'\b(swot|tows|strength|weakness|opportunit|threat)\b', re.IGNORECASE),
            re.compile(r'\b(risk|danger|vulnerabilit|threat detection)\b', re.IGNORECASE),
            re.compile(r'\b(analy[sz]e|assess|evaluate|review)\b', re.IGNORECASE),
            re.compile(r'\b(link|connect|correlat|pattern|relationship)\b', re.IGNORECASE),
        ]
        
        # Planning domain patterns
        self.planning_patterns = [
            re.compile(r'\b(initiative|plan|project|strategy|action)\b', re.IGNORECASE),
            re.compile(r'\b(resource|budget|allocat|capacity|team)\b', re.IGNORECASE),
            re.compile(r'\b(canvas|visuali[sz]e|mind\s*map|diagram)\b', re.IGNORECASE),
            re.compile(r'\b(align|fit|goal|objective|metric)\b', re.IGNORECASE),
            re.compile(r'\b(timeline|milestone|task|deadline)\b', re.IGNORECASE),
        ]
        
        # Workflow patterns
        self.workflow_patterns = [
            re.compile(r'\b(workflow|process|comprehensive|full|complete)\b', re.IGNORECASE),
            re.compile(r'\b(strategic\s*(planning|review))\b', re.IGNORECASE),
            re.compile(r'\b(step.by.step|guide me|walk me through)\b', re.IGNORECASE),
        ]
    
    def identify_domain(self, 
                       request: Dict,
                       session_context: Optional[Dict] = None) -> Tuple[Domain, float]:
        """
        Identify the domain of a request.
        
        Args:
            request: The incoming request dictionary
            session_context: Optional session context
            
        Returns:
            Tuple of (Domain, confidence_score)
        """
        # Check for explicit task type first
        task_type = request.get("task_type", "").upper()
        if task_type:
            domain, confidence = self._domain_from_task_type(task_type)
            if domain != Domain.UNKNOWN:
                return domain, confidence
        
        # Analyze text content
        text_to_analyze = self._extract_text_content(request)
        if not text_to_analyze:
            return Domain.UNKNOWN, 0.0
        
        # Score each domain
        scores = {
            Domain.FOUNDATION: self._score_domain(text_to_analyze, self.foundation_patterns),
            Domain.ANALYSIS: self._score_domain(text_to_analyze, self.analysis_patterns),
            Domain.PLANNING: self._score_domain(text_to_analyze, self.planning_patterns),
            Domain.WORKFLOW: self._score_domain(text_to_analyze, self.workflow_patterns),
        }
        
        # Consider session context
        if session_context:
            scores = self._adjust_scores_with_context(scores, session_context)
        
        # Find the highest scoring domain
        max_domain = max(scores.items(), key=lambda x: x[1])
        domain, score = max_domain
        
        # Normalize confidence score (0-1)
        confidence = min(score / 10.0, 1.0) if score > 0 else 0.0
        
        # If confidence is too low, return UNKNOWN
        if confidence < 0.3:
            return Domain.UNKNOWN, confidence
        
        return domain, confidence
    
    def _domain_from_task_type(self, task_type: str) -> Tuple[Domain, float]:
        """Map task type to domain."""
        # Foundation tasks
        foundation_tasks = [
            "CREATE_CEO_LOG", "GET_CEO_LOGS", "SEARCH_CEO_LOGS",
            "GET_NORTH_STAR_DETAILS", "UPDATE_NORTH_STAR",
            "MEMORY_QUERY", "SAVE_MEMORY",
            "UPDATE_PREFERENCES", "GET_PREFERENCES"
        ]
        
        # Analysis tasks
        analysis_tasks = [
            "START_SWOT_ANALYSIS", "CONTINUE_SWOT_ANALYSIS",
            "DETECT_RISKS", "LINK_SUBJECTIVE_OBJECTIVE"
        ]
        
        # Planning tasks
        planning_tasks = [
            "CREATE_INITIATIVE", "UPDATE_INITIATIVE",
            "ALLOCATE_RESOURCES", "CHECK_ALIGNMENT",
            "CREATE_ACTION_PLAN", "CANVAS_OPERATION",
            "CREATE_CANVAS_NODE", "CONNECT_CANVAS_NODES"
        ]
        
        # Workflow tasks
        workflow_tasks = [
            "EXECUTE_STRATEGIC_PLANNING_WORKFLOW",
            "FULL_STRATEGIC_REVIEW_WORKFLOW",
            "NEW_INITIATIVE_PLANNING_WORKFLOW"
        ]
        
        if task_type in foundation_tasks:
            return Domain.FOUNDATION, 1.0
        elif task_type in analysis_tasks:
            return Domain.ANALYSIS, 1.0
        elif task_type in planning_tasks:
            return Domain.PLANNING, 1.0
        elif task_type in workflow_tasks:
            return Domain.WORKFLOW, 1.0
        else:
            return Domain.UNKNOWN, 0.0
    
    def _extract_text_content(self, request: Dict) -> str:
        """Extract all text content from request for analysis."""
        text_parts = []
        
        # Add user query
        if "user_query" in request:
            text_parts.append(request["user_query"])
        
        # Add payload text if it's a string
        payload = request.get("payload", {})
        if isinstance(payload, str):
            text_parts.append(payload)
        elif isinstance(payload, dict):
            # Extract text fields from payload
            for key, value in payload.items():
                if isinstance(value, str) and key in ["text", "query", "description", "content"]:
                    text_parts.append(value)
        
        return " ".join(text_parts)
    
    def _score_domain(self, text: str, patterns: List[re.Pattern]) -> float:
        """Score how well text matches domain patterns."""
        score = 0.0
        for pattern in patterns:
            matches = pattern.findall(text)
            score += len(matches)
        return score
    
    def _adjust_scores_with_context(self, 
                                   scores: Dict[Domain, float],
                                   session_context: Dict) -> Dict[Domain, float]:
        """Adjust domain scores based on session context."""
        # Boost score if there's an active workflow
        active_workflow = session_context.get("active_workflow")
        if active_workflow:
            if "SWOT" in active_workflow:
                scores[Domain.ANALYSIS] *= 1.5
            elif "PLANNING" in active_workflow:
                scores[Domain.PLANNING] *= 1.5
            elif "WORKFLOW" in active_workflow:
                scores[Domain.WORKFLOW] *= 2.0
        
        # Boost based on last interaction
        last_agent = session_context.get("last_agent_used")
        if last_agent:
            if last_agent in ["CEOLogAgent", "NorthStarAgent", "MemoryAgent", "PreferenceAgent"]:
                scores[Domain.FOUNDATION] *= 1.3
            elif last_agent in ["SWOTTOWSAgent", "RiskDetectionAgent", "S_O_LinkageAgent"]:
                scores[Domain.ANALYSIS] *= 1.3
            elif last_agent in ["InitiativeGenerationAgent", "ResourceAgent", "CanvasInteractionAgent", "AlignmentAgent"]:
                scores[Domain.PLANNING] *= 1.3
        
        return scores
    
    def get_domain_description(self, domain: Domain) -> str:
        """Get a human-readable description of a domain."""
        descriptions = {
            Domain.FOUNDATION: "Strategic Foundation & Insights - Managing core strategy elements, CEO logs, and preferences",
            Domain.ANALYSIS: "Analysis & Intelligence - Performing SWOT analysis, risk detection, and data correlation",
            Domain.PLANNING: "Planning & Execution - Creating initiatives, allocating resources, and strategic planning",
            Domain.WORKFLOW: "Multi-step Workflows - Comprehensive processes involving multiple agents",
            Domain.UNKNOWN: "Unknown domain - Unable to classify the request"
        }
        return descriptions.get(domain, "Unknown domain")