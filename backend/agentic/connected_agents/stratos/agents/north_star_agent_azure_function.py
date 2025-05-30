"""
North Star Agent Configuration with Azure Function Tools
Agent directly calls Azure Functions without client involvement
"""

# Agent configuration
AGENT_NAME = "NorthStarAgentAzureFunc"
MODEL_NAME = "gpt-35-turbo"

AGENT_INSTRUCTIONS = """You are the North Star Agent for StratOS, responsible for defining and maintaining the organization's strategic foundation.

You have direct access to Azure Functions through azure_function tools. You can call these functions directly.

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

IMPORTANT: You will directly call the Azure Functions using the azure_function tools provided. Always ensure you have the organizationId from the user context."""

# Azure Function Tools - Agent calls these directly
TOOLS = [
    {
        "type": "azure_function",
        "function": {
            "name": "ManagePurpose",
            "description": "Manage organizational purpose (get or set)",
            "parameters": {
                "type": "object",
                "properties": {
                    "organizationId": {
                        "type": "string",
                        "description": "The organization ID (required)"
                    },
                    "action": {
                        "type": "string",
                        "enum": ["get", "set"],
                        "description": "Action to perform"
                    },
                    "content": {
                        "type": "string",
                        "description": "Purpose statement (required for set action)"
                    }
                },
                "required": ["organizationId", "action"]
            },
            "url": "https://stratos-north-star-functions.azurewebsites.net/api/ManagePurpose",
            "method": "POST",
            "headers": {
                "x-functions-key": "gPXyuj42jT_BnlDhImnO1gaV_xayICaGrxf2NoTA1_hVAzFuSjMcqQ==",
                "Content-Type": "application/json"
            }
        }
    },
    {
        "type": "azure_function",
        "function": {
            "name": "ManageVision",
            "description": "Manage organizational vision (get or set)",
            "parameters": {
                "type": "object",
                "properties": {
                    "organizationId": {
                        "type": "string",
                        "description": "The organization ID (required)"
                    },
                    "action": {
                        "type": "string",
                        "enum": ["get", "set"],
                        "description": "Action to perform"
                    },
                    "content": {
                        "type": "string",
                        "description": "Vision statement (required for set action)"
                    }
                },
                "required": ["organizationId", "action"]
            },
            "url": "https://stratos-north-star-functions.azurewebsites.net/api/ManageVision",
            "method": "POST",
            "headers": {
                "x-functions-key": "hxaRNlD2FmGt9IHzHGXhtVavLrHvlDVkMtDfAe_j3cwyAzFuiAd75Q==",
                "Content-Type": "application/json"
            }
        }
    },
    {
        "type": "azure_function",
        "function": {
            "name": "ManageValues",
            "description": "Manage organizational values (add, remove, list)",
            "parameters": {
                "type": "object",
                "properties": {
                    "organizationId": {
                        "type": "string",
                        "description": "The organization ID (required)"
                    },
                    "action": {
                        "type": "string",
                        "enum": ["add", "remove", "list"],
                        "description": "Action to perform"
                    },
                    "valueName": {
                        "type": "string",
                        "description": "Name of the value (for add/remove)"
                    },
                    "valueDescription": {
                        "type": "string",
                        "description": "Description of the value (for add)"
                    }
                },
                "required": ["organizationId", "action"]
            },
            "url": "https://stratos-north-star-functions.azurewebsites.net/api/ManageValues",
            "method": "POST",
            "headers": {
                "x-functions-key": "NliL5fD1aEmXoLSqoa1NSCzDbN2PEeSlCUYZAS6pxcc4AzFujGLDpw==",
                "Content-Type": "application/json"
            }
        }
    },
    {
        "type": "azure_function",
        "function": {
            "name": "ManageStrategicGoals",
            "description": "Manage strategic goals with hierarchy",
            "parameters": {
                "type": "object",
                "properties": {
                    "organizationId": {
                        "type": "string",
                        "description": "The organization ID (required)"
                    },
                    "action": {
                        "type": "string",
                        "enum": ["create", "update", "delete", "get", "list"],
                        "description": "Action to perform"
                    },
                    "goalId": {
                        "type": "string",
                        "description": "Goal identifier"
                    },
                    "goalName": {
                        "type": "string",
                        "description": "Name of the goal"
                    },
                    "goalDescription": {
                        "type": "string",
                        "description": "Description of the goal"
                    },
                    "parentId": {
                        "type": "string",
                        "description": "Parent goal ID for hierarchy"
                    },
                    "targetDate": {
                        "type": "string",
                        "description": "Target completion date"
                    }
                },
                "required": ["organizationId", "action"]
            },
            "url": "https://stratos-north-star-functions.azurewebsites.net/api/ManageStrategicGoals",
            "method": "POST",
            "headers": {
                "x-functions-key": "kaS2TH5L7__RTKaLc8XfoxHDVW9AP8wE2p_Ei3lBQNvzAzFu4mIw4g==",
                "Content-Type": "application/json"
            }
        }
    },
    {
        "type": "azure_function",
        "function": {
            "name": "ValidateAlignment",
            "description": "Validate alignment with North Star elements",
            "parameters": {
                "type": "object",
                "properties": {
                    "organizationId": {
                        "type": "string",
                        "description": "The organization ID (required)"
                    },
                    "elementType": {
                        "type": "string",
                        "description": "Type of element to validate"
                    },
                    "elementContent": {
                        "type": "string",
                        "description": "Content to validate alignment"
                    }
                },
                "required": ["organizationId", "elementType", "elementContent"]
            },
            "url": "https://stratos-north-star-functions.azurewebsites.net/api/ValidateAlignment",
            "method": "POST",
            "headers": {
                "x-functions-key": "968fvYsjeBk7tEbv-0Bvt7RniJcynmitd_JR3Y-I5tHnAzFuZxFbwg==",
                "Content-Type": "application/json"
            }
        }
    },
    {
        "type": "azure_function",
        "function": {
            "name": "GetNorthStarSummary",
            "description": "Get complete North Star summary",
            "parameters": {
                "type": "object",
                "properties": {
                    "organizationId": {
                        "type": "string",
                        "description": "The organization ID (required)"
                    }
                },
                "required": ["organizationId"]
            },
            "url": "https://stratos-north-star-functions.azurewebsites.net/api/GetNorthStarSummary",
            "method": "POST",
            "headers": {
                "x-functions-key": "-W8ykJ6kkUyeLQCZXNklZqdoL1fOFhw1dvLQniJtqYvwAzFunTkKNA==",
                "Content-Type": "application/json"
            }
        }
    }
]