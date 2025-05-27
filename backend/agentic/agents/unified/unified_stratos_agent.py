"""
Unified StratOS Agent Configuration
This module defines the complete configuration for a single agent that combines
all StratOS capabilities including orchestration and all specialist functions.
"""

# Agent configuration
UNIFIED_AGENT_CONFIG = {
    "name": "StratOSUnifiedAgent",
    "instructions": """You are the StratOS Unified Agent, a comprehensive strategic planning assistant that combines all capabilities of the StratOS system.

You have direct access to all strategic planning functions through your tools. Analyze the user's request and use the appropriate tool(s) to provide a comprehensive response.

Your integrated capabilities include:
1. CEO Log Management - Record and manage executive thoughts, observations, and strategic notes
2. North Star Alignment - Define and refine vision, mission, values, and strategic goals
3. Memory & Context - Retrieve historical information, patterns, and past decisions
4. Preference Learning - Track and apply user preferences for personalized experiences
5. SWOT/TOWS Analysis - Perform comprehensive strategic analysis
6. Risk & Opportunity Assessment - Identify and evaluate risks and opportunities
7. Subjective-Objective Linking - Connect qualitative insights with quantitative data
8. Strategic Alignment Scoring - Evaluate initiative alignment with goals
9. Initiative Generation - Create strategic initiatives and plans
10. Resource Optimization - Optimize resource allocation and capacity
11. Action Planning - Break down initiatives into executable tasks
12. Canvas Visualization - Create visual strategic representations

When responding to requests:
1. Directly use the appropriate tool(s) rather than routing to other agents
2. Provide comprehensive, actionable responses
3. Combine multiple tools when needed for thorough analysis
4. Maintain context across the conversation

You are empowered to make decisions and provide direct responses using your integrated capabilities.""",
    
    "tools": [
        # CEO Log Management
        {
            "type": "function",
            "function": {
                "name": "manage_ceo_log",
                "description": "Create, update, or retrieve CEO log entries including thoughts, observations, and strategic notes",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": ["create", "update", "retrieve", "list"],
                            "description": "The action to perform on the CEO log"
                        },
                        "content": {
                            "type": "string",
                            "description": "The content of the log entry (for create/update)"
                        },
                        "entry_id": {
                            "type": "string",
                            "description": "The ID of the log entry (for update/retrieve)"
                        },
                        "tags": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Tags to categorize the log entry"
                        }
                    },
                    "required": ["action"]
                }
            }
        },
        
        # North Star Management
        {
            "type": "function",
            "function": {
                "name": "manage_north_star",
                "description": "Define, update, or retrieve vision, mission, values, and strategic goals",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "component": {
                            "type": "string",
                            "enum": ["vision", "mission", "values", "goals", "all"],
                            "description": "Which North Star component to manage"
                        },
                        "action": {
                            "type": "string",
                            "enum": ["set", "get", "refine"],
                            "description": "The action to perform"
                        },
                        "content": {
                            "type": "string",
                            "description": "The content to set or refine"
                        }
                    },
                    "required": ["component", "action"]
                }
            }
        },
        
        # Memory Recall
        {
            "type": "function",
            "function": {
                "name": "recall_memory",
                "description": "Retrieve historical context, patterns, decisions, or information",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "What to search for in organizational memory"
                        },
                        "time_frame": {
                            "type": "string",
                            "description": "Time period to search (e.g., 'last quarter', 'past year')"
                        },
                        "category": {
                            "type": "string",
                            "enum": ["decisions", "patterns", "context", "all"],
                            "description": "Type of memory to recall"
                        }
                    },
                    "required": ["query"]
                }
            }
        },
        
        # SWOT/TOWS Analysis
        {
            "type": "function",
            "function": {
                "name": "perform_swot_analysis",
                "description": "Conduct SWOT analysis and generate TOWS strategies",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "subject": {
                            "type": "string",
                            "description": "What to analyze (product, project, organization, etc.)"
                        },
                        "include_tows": {
                            "type": "boolean",
                            "description": "Whether to generate TOWS strategies",
                            "default": True
                        },
                        "context": {
                            "type": "string",
                            "description": "Additional context for the analysis"
                        }
                    },
                    "required": ["subject"]
                }
            }
        },
        
        # Risk & Opportunity Assessment
        {
            "type": "function",
            "function": {
                "name": "assess_risks_opportunities",
                "description": "Identify and evaluate risks and opportunities",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "scope": {
                            "type": "string",
                            "description": "The scope of assessment (project, market, initiative, etc.)"
                        },
                        "type": {
                            "type": "string",
                            "enum": ["risks", "opportunities", "both"],
                            "description": "What to assess",
                            "default": "both"
                        },
                        "priority_threshold": {
                            "type": "string",
                            "enum": ["high", "medium", "low", "all"],
                            "description": "Minimum priority level to include",
                            "default": "all"
                        }
                    },
                    "required": ["scope"]
                }
            }
        },
        
        # Initiative Generation
        {
            "type": "function",
            "function": {
                "name": "generate_initiatives",
                "description": "Create strategic initiatives based on goals and analysis",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "objective": {
                            "type": "string",
                            "description": "The strategic objective to address"
                        },
                        "constraints": {
                            "type": "string",
                            "description": "Any constraints (budget, time, resources)"
                        },
                        "number": {
                            "type": "integer",
                            "description": "Number of initiatives to generate",
                            "default": 3
                        }
                    },
                    "required": ["objective"]
                }
            }
        },
        
        # Resource Optimization
        {
            "type": "function",
            "function": {
                "name": "optimize_resources",
                "description": "Optimize resource allocation across initiatives",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "initiatives": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of initiatives to optimize resources for"
                        },
                        "resource_type": {
                            "type": "string",
                            "enum": ["budget", "people", "time", "all"],
                            "description": "Type of resource to optimize",
                            "default": "all"
                        },
                        "optimization_goal": {
                            "type": "string",
                            "enum": ["efficiency", "impact", "speed", "balanced"],
                            "description": "Goal of optimization",
                            "default": "balanced"
                        }
                    },
                    "required": ["initiatives"]
                }
            }
        },
        
        # Action Planning
        {
            "type": "function",
            "function": {
                "name": "create_action_plan",
                "description": "Break down initiatives into detailed action plans with tasks and milestones",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "initiative": {
                            "type": "string",
                            "description": "The initiative to create an action plan for"
                        },
                        "timeline": {
                            "type": "string",
                            "description": "Timeline for the plan (e.g., '3 months', 'Q2 2025')"
                        },
                        "detail_level": {
                            "type": "string",
                            "enum": ["high", "medium", "summary"],
                            "description": "Level of detail for the plan",
                            "default": "medium"
                        }
                    },
                    "required": ["initiative"]
                }
            }
        },
        
        # Strategic Alignment Scoring
        {
            "type": "function",
            "function": {
                "name": "score_alignment",
                "description": "Evaluate how well initiatives align with strategic goals",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "initiatives": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Initiatives to score"
                        },
                        "criteria": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Specific criteria to evaluate against"
                        },
                        "include_recommendations": {
                            "type": "boolean",
                            "description": "Include recommendations for improvement",
                            "default": True
                        }
                    },
                    "required": ["initiatives"]
                }
            }
        },
        
        # Preference Learning
        {
            "type": "function",
            "function": {
                "name": "manage_preferences",
                "description": "Learn, store, or apply user preferences",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": ["learn", "apply", "list", "update"],
                            "description": "Action to perform with preferences"
                        },
                        "category": {
                            "type": "string",
                            "description": "Category of preferences (e.g., 'communication', 'analysis', 'reporting')"
                        },
                        "preference": {
                            "type": "string",
                            "description": "The specific preference to manage"
                        }
                    },
                    "required": ["action"]
                }
            }
        },
        
        # Subjective-Objective Linking
        {
            "type": "function",
            "function": {
                "name": "link_subjective_objective",
                "description": "Connect subjective insights with objective data",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "subjective_input": {
                            "type": "string",
                            "description": "The subjective insight or observation"
                        },
                        "data_sources": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Objective data sources to analyze"
                        },
                        "analysis_type": {
                            "type": "string",
                            "enum": ["validate", "correlate", "predict", "explain"],
                            "description": "Type of analysis to perform",
                            "default": "correlate"
                        }
                    },
                    "required": ["subjective_input"]
                }
            }
        },
        
        # Canvas Visualization
        {
            "type": "function",
            "function": {
                "name": "create_canvas_visualization",
                "description": "Create visual strategic planning canvas",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "canvas_type": {
                            "type": "string",
                            "enum": ["business_model", "strategy", "lean", "custom"],
                            "description": "Type of canvas to create"
                        },
                        "elements": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Elements to include in the canvas"
                        },
                        "format": {
                            "type": "string",
                            "enum": ["structured", "mindmap", "flow"],
                            "description": "Visual format of the canvas",
                            "default": "structured"
                        }
                    },
                    "required": ["canvas_type"]
                }
            }
        }
    ]
}

def get_unified_agent_config(model_deployment: str = "gpt-35-turbo") -> dict:
    """
    Get the unified agent configuration with the specified model.
    
    Args:
        model_deployment: The model deployment name to use
        
    Returns:
        Complete agent configuration dictionary
    """
    config = UNIFIED_AGENT_CONFIG.copy()
    config["model"] = model_deployment
    return config