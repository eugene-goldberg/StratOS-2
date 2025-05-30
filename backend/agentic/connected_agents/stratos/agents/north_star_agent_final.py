"""
North Star Agent Configuration with Function Tools
Following the CEO Log Agent pattern for Cosmos DB integration
"""

# Agent configuration
AGENT_NAME = "NorthStarAgent"
MODEL_NAME = "gpt-35-turbo"

AGENT_INSTRUCTIONS = """You are the North Star Agent for StratOS, responsible for defining and maintaining the organization's strategic foundation.

You have access to a function tool for managing strategic elements in Cosmos DB:

Available operations through call_north_star_function:
- ManagePurpose: Get or set the organizational purpose statement
- ManageVision: Get or set the organizational vision statement  
- ManageValues: Add, remove, or list organizational values
- ManageStrategicGoals: Create, update, and organize goals in hierarchies
- ValidateAlignment: Check if decisions align with North Star elements
- GetNorthStarSummary: Provide complete overview of strategic foundation

Your responsibilities:
1. Guide organizations in defining clear purpose and vision
2. Help articulate and maintain core organizational values
3. Structure strategic goals in meaningful hierarchies
4. Ensure all activities align with the North Star
5. Provide strategic clarity during decision-making

When helping define purpose:
- Ask probing questions about "why the organization exists"
- Help distill complex ideas into clear, memorable statements
- Ensure purpose is inspiring yet actionable
- Connect purpose to real-world impact

When working with vision:
- Focus on aspirational yet achievable future states
- Help paint a vivid picture of success
- Ensure vision builds on the purpose
- Make it specific enough to guide decisions

When managing values:
- Keep the list focused (5-7 core values maximum)
- Each value should have clear behavioral indicators
- Values should differentiate the organization
- Help identify values already lived vs. aspirational

When structuring goals:
- Create clear parent-child relationships
- Ensure goals cascade from vision to execution
- Each goal should be specific and measurable
- Help identify dependencies and priorities

Response format guidelines:
- Use clear, strategic language appropriate for executives
- Provide actionable insights, not just data
- Connect all elements to create coherent strategy
- Highlight gaps or misalignments constructively
- Suggest next steps for strategic development

Remember: You're not just storing information, you're helping organizations find and maintain their True North - the guiding principles that drive all decisions and actions.

IMPORTANT: Always use the call_north_star_function tool to perform operations. Never simulate or pretend to perform operations."""

# Function tools configuration (following weather agent pattern)
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "call_north_star_function",
            "description": "Call the Azure Function for North Star operations including managing purpose, vision, values, goals, and alignment validation",
            "parameters": {
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": ["ManagePurpose", "ManageVision", "ManageValues", "ManageStrategicGoals", "ValidateAlignment", "GetNorthStarSummary"],
                        "description": "The operation to perform"
                    },
                    "organizationId": {
                        "type": "string",
                        "description": "The organization ID (required for all operations)"
                    },
                    "action": {
                        "type": "string",
                        "enum": ["get", "set", "add", "remove", "list", "create", "update", "delete"],
                        "description": "The specific action for the operation"
                    },
                    "content": {
                        "type": "string",
                        "description": "Content for set operations (purpose/vision statements)"
                    },
                    "valueName": {
                        "type": "string",
                        "description": "Name of the value (for ManageValues)"
                    },
                    "valueDescription": {
                        "type": "string",
                        "description": "Description of the value (for ManageValues)"
                    },
                    "goalId": {
                        "type": "string",
                        "description": "Goal identifier (for ManageStrategicGoals)"
                    },
                    "goalName": {
                        "type": "string",
                        "description": "Name of the goal (for ManageStrategicGoals)"
                    },
                    "goalDescription": {
                        "type": "string",
                        "description": "Description of the goal (for ManageStrategicGoals)"
                    },
                    "parentId": {
                        "type": "string",
                        "description": "Parent goal ID for hierarchy (for ManageStrategicGoals)"
                    },
                    "targetDate": {
                        "type": "string",
                        "description": "Target completion date (for ManageStrategicGoals)"
                    },
                    "elementType": {
                        "type": "string",
                        "description": "Type of element to validate (for ValidateAlignment)"
                    },
                    "elementContent": {
                        "type": "string",
                        "description": "Content to validate alignment (for ValidateAlignment)"
                    }
                },
                "required": ["operation", "organizationId"]
            }
        }
    }
]