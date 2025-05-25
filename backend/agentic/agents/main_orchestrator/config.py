"""Configuration for Main Orchestrator Agent."""

from typing import Dict, List
from enum import Enum


class TaskType(Enum):
    """Supported task types for deterministic routing."""
    # CEO Log Tasks
    CREATE_CEO_LOG = "CREATE_CEO_LOG"
    GET_CEO_LOGS = "GET_CEO_LOGS"
    SEARCH_CEO_LOGS = "SEARCH_CEO_LOGS"
    
    # North Star Tasks
    GET_NORTH_STAR_DETAILS = "GET_NORTH_STAR_DETAILS"
    UPDATE_NORTH_STAR = "UPDATE_NORTH_STAR"
    
    # Memory Tasks
    MEMORY_QUERY = "MEMORY_QUERY"
    SAVE_MEMORY = "SAVE_MEMORY"
    
    # Preference Tasks
    UPDATE_PREFERENCES = "UPDATE_PREFERENCES"
    GET_PREFERENCES = "GET_PREFERENCES"
    
    # Analysis Tasks
    START_SWOT_ANALYSIS = "START_SWOT_ANALYSIS"
    CONTINUE_SWOT_ANALYSIS = "CONTINUE_SWOT_ANALYSIS"
    DETECT_RISKS = "DETECT_RISKS"
    LINK_SUBJECTIVE_OBJECTIVE = "LINK_SUBJECTIVE_OBJECTIVE"
    
    # Planning Tasks
    CREATE_INITIATIVE = "CREATE_INITIATIVE"
    UPDATE_INITIATIVE = "UPDATE_INITIATIVE"
    ALLOCATE_RESOURCES = "ALLOCATE_RESOURCES"
    CHECK_ALIGNMENT = "CHECK_ALIGNMENT"
    CREATE_ACTION_PLAN = "CREATE_ACTION_PLAN"
    
    # Canvas Tasks
    CANVAS_OPERATION = "CANVAS_OPERATION"
    CREATE_CANVAS_NODE = "CREATE_CANVAS_NODE"
    CONNECT_CANVAS_NODES = "CONNECT_CANVAS_NODES"
    
    # Workflow Tasks
    EXECUTE_STRATEGIC_PLANNING_WORKFLOW = "EXECUTE_STRATEGIC_PLANNING_WORKFLOW"
    FULL_STRATEGIC_REVIEW_WORKFLOW = "FULL_STRATEGIC_REVIEW_WORKFLOW"
    NEW_INITIATIVE_PLANNING_WORKFLOW = "NEW_INITIATIVE_PLANNING_WORKFLOW"
    
    # Generic
    PROCESS_USER_QUERY = "PROCESS_USER_QUERY"
    GENERAL_QUERY = "GENERAL_QUERY"


class AgentName(Enum):
    """Available agents in the Unified MAS."""
    # Foundation Agents
    CEO_LOG_AGENT = "CEOLogAgent"
    NORTH_STAR_AGENT = "NorthStarAgent"
    MEMORY_AGENT = "MemoryAgent"
    PREFERENCE_AGENT = "PreferenceAgent"
    
    # Analysis Agents
    SWOT_TOWS_AGENT = "SWOTTOWSAgent"
    RISK_DETECTION_AGENT = "RiskDetectionAgent"
    SO_LINKAGE_AGENT = "S_O_LinkageAgent"
    
    # Planning Agents
    INITIATIVE_AGENT = "InitiativeGenerationAgent"
    RESOURCE_AGENT = "ResourceAgent"
    CANVAS_AGENT = "CanvasInteractionAgent"
    ALIGNMENT_AGENT = "AlignmentAgent"
    ACTION_PLANNING_AGENT = "ActionPlanningAgent"
    
    # Router Agents (sub-routers, not used in Phase 1 but defined for completeness)
    STRATEGIC_CONTEXT_ROUTER = "StrategicContextRouter"
    ANALYSIS_ORCHESTRATOR = "AnalysisOrchestrator"
    PLANNING_COORDINATOR = "PlanningCoordinator"


# Task Type to Agent Mapping
TASK_AGENT_MAPPING: Dict[TaskType, AgentName] = {
    # CEO Log Tasks
    TaskType.CREATE_CEO_LOG: AgentName.CEO_LOG_AGENT,
    TaskType.GET_CEO_LOGS: AgentName.CEO_LOG_AGENT,
    TaskType.SEARCH_CEO_LOGS: AgentName.CEO_LOG_AGENT,
    
    # North Star Tasks
    TaskType.GET_NORTH_STAR_DETAILS: AgentName.NORTH_STAR_AGENT,
    TaskType.UPDATE_NORTH_STAR: AgentName.NORTH_STAR_AGENT,
    
    # Memory Tasks
    TaskType.MEMORY_QUERY: AgentName.MEMORY_AGENT,
    TaskType.SAVE_MEMORY: AgentName.MEMORY_AGENT,
    
    # Preference Tasks
    TaskType.UPDATE_PREFERENCES: AgentName.PREFERENCE_AGENT,
    TaskType.GET_PREFERENCES: AgentName.PREFERENCE_AGENT,
    
    # Analysis Tasks
    TaskType.START_SWOT_ANALYSIS: AgentName.SWOT_TOWS_AGENT,
    TaskType.CONTINUE_SWOT_ANALYSIS: AgentName.SWOT_TOWS_AGENT,
    TaskType.DETECT_RISKS: AgentName.RISK_DETECTION_AGENT,
    TaskType.LINK_SUBJECTIVE_OBJECTIVE: AgentName.SO_LINKAGE_AGENT,
    
    # Planning Tasks
    TaskType.CREATE_INITIATIVE: AgentName.INITIATIVE_AGENT,
    TaskType.UPDATE_INITIATIVE: AgentName.INITIATIVE_AGENT,
    TaskType.ALLOCATE_RESOURCES: AgentName.RESOURCE_AGENT,
    TaskType.CHECK_ALIGNMENT: AgentName.ALIGNMENT_AGENT,
    TaskType.CREATE_ACTION_PLAN: AgentName.ACTION_PLANNING_AGENT,
    
    # Canvas Tasks
    TaskType.CANVAS_OPERATION: AgentName.CANVAS_AGENT,
    TaskType.CREATE_CANVAS_NODE: AgentName.CANVAS_AGENT,
    TaskType.CONNECT_CANVAS_NODES: AgentName.CANVAS_AGENT,
}


# Keyword patterns for routing when task_type is generic
KEYWORD_PATTERNS: Dict[str, List[str]] = {
    AgentName.CEO_LOG_AGENT.value: [
        "new log", "remember this", "note", "observation", "concern",
        "log entry", "ceo log", "add to log", "my thoughts"
    ],
    AgentName.NORTH_STAR_AGENT.value: [
        "purpose", "vision", "values", "goals", "north star",
        "strategic goals", "company mission", "pvv"
    ],
    AgentName.MEMORY_AGENT.value: [
        "recall", "what did i say about", "find information on",
        "remember when", "search memory", "retrieve", "context"
    ],
    AgentName.PREFERENCE_AGENT.value: [
        "preference", "customize", "personalize", "my settings",
        "feedback", "like", "dislike"
    ],
    AgentName.SWOT_TOWS_AGENT.value: [
        "swot", "tows", "strengths", "weaknesses", "opportunities",
        "threats", "strategic analysis", "swot analysis"
    ],
    AgentName.RISK_DETECTION_AGENT.value: [
        "risk", "threat detection", "potential problem", "danger",
        "vulnerability", "risk assessment"
    ],
    AgentName.SO_LINKAGE_AGENT.value: [
        "connect insights to data", "link subjective objective",
        "correlation", "pattern", "connection between"
    ],
    AgentName.INITIATIVE_AGENT.value: [
        "initiative", "plan", "project", "new action", "strategy execution",
        "create initiative", "strategic initiative"
    ],
    AgentName.RESOURCE_AGENT.value: [
        "resources", "budget", "assign team", "allocation",
        "capacity", "resource planning"
    ],
    AgentName.CANVAS_AGENT.value: [
        "canvas", "visualize", "mind map", "draw connection",
        "strategic canvas", "visual planning"
    ],
    AgentName.ALIGNMENT_AGENT.value: [
        "align", "strategic fit", "goal alignment", "alignment score",
        "check alignment", "initiative alignment"
    ],
    AgentName.ACTION_PLANNING_AGENT.value: [
        "action plan", "task breakdown", "timeline", "milestones",
        "dependencies", "project plan"
    ],
}


# Workflow definitions
WORKFLOW_DEFINITIONS = {
    "STRATEGIC_PLANNING_WORKFLOW": {
        "description": "Comprehensive strategic planning process",
        "steps": [
            {"agent": AgentName.MEMORY_AGENT, "action": "gather_context"},
            {"agent": AgentName.SWOT_TOWS_AGENT, "action": "perform_analysis"},
            {"agent": AgentName.INITIATIVE_AGENT, "action": "generate_initiatives"},
            {"agent": AgentName.MEMORY_AGENT, "action": "save_plan_summary"}
        ],
        "required_params": ["user_id", "planning_scope"],
        "optional_params": ["time_horizon", "focus_areas"]
    },
    "FULL_STRATEGIC_REVIEW_WORKFLOW": {
        "description": "Full strategic review including logs, alignment, and analysis",
        "steps": [
            {"agent": AgentName.CEO_LOG_AGENT, "action": "review_recent_logs"},
            {"agent": AgentName.NORTH_STAR_AGENT, "action": "check_alignment"},
            {"agent": AgentName.SWOT_TOWS_AGENT, "action": "perform_swot"},
            {"agent": AgentName.INITIATIVE_AGENT, "action": "ideate_initiatives"}
        ],
        "required_params": ["user_id", "time_period"],
        "optional_params": ["specific_focus_area"]
    },
    "NEW_INITIATIVE_PLANNING_WORKFLOW": {
        "description": "Guide through creating a new strategic initiative",
        "steps": [
            {"agent": AgentName.INITIATIVE_AGENT, "action": "create_initiative"},
            {"agent": AgentName.RESOURCE_AGENT, "action": "plan_resources"},
            {"agent": AgentName.ALIGNMENT_AGENT, "action": "score_alignment"},
            {"agent": AgentName.ACTION_PLANNING_AGENT, "action": "create_action_plan"}
        ],
        "required_params": ["user_id", "initiative_title"],
        "optional_params": ["related_goal_id", "initial_budget"]
    }
}


# Error messages
ERROR_MESSAGES = {
    "no_route_found": "I couldn't understand your request. Could you please be more specific?",
    "agent_not_available": "The requested service is temporarily unavailable. Please try again.",
    "missing_required_params": "Your request is missing some required information: {params}",
    "workflow_error": "There was an error executing the workflow. Please try again.",
    "general_error": "An unexpected error occurred. Please try again or contact support."
}


# Retry configuration
RETRY_CONFIG = {
    "max_retries": 3,
    "backoff_factor": 2,  # Exponential backoff
    "retry_exceptions": [
        "ConnectionError",
        "TimeoutError",
        "ServiceUnavailable"
    ]
}