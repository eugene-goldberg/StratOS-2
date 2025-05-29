#!/usr/bin/env python3
"""Update CEO Log Agent with Azure Functions tools"""

import asyncio
import json
from azure.ai.projects.aio import AIProjectClient
from azure.identity.aio import DefaultAzureCredential

# Configuration
PROJECT_CONNECTION_STRING = "eastus2.api.azureml.ms;0a7a2d58-80d4-4d62-9c71-f87740c9b9f1;semantic-kernel-multi-agent;semantic-kernel-multi-agent-rg"

# Azure Functions configuration
AZURE_FUNCTION_BASE = "https://stratos-ceo-log-functions.azurewebsites.net/api"
AZURE_FUNCTION_KEYS = {
    "SaveCEOLog": "I3c897PZMtJp1goBaxPwGlXa3Ni6ZsM09t1F7roTLVZeAzFu69TeKA==",
    "SearchCEOLogs": "uXjWD5crSSJYH_7eL3IcQq_ebEqVqO9D2QaC24UKa_RNAzFuVD7gkg==",
    "AnalyzeLogs": "1ALdM_XHFGwQ5XtC5BBsnJ-_j_w30lef9DsjGWVrpNJfAzFuEHzbmg==",
    "GetInsights": "Rx3WeFi1SoWXpbiZtsOCBVyswP06bUskqSYKK5HdntHBAzFuqJ56aw=="
}

# Tool definitions with Azure Function URLs
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "SaveCEOLog",
            "description": "Save a new CEO log entry with automatic AI analysis, tagging, and categorization. Call the Azure Function to persist to Cosmos DB.",
            "parameters": {
                "type": "object",
                "properties": {
                    "userId": {
                        "type": "string",
                        "description": "The user ID of the CEO"
                    },
                    "content": {
                        "type": "string",
                        "description": "The raw content of the log entry"
                    },
                    "category": {
                        "type": "string",
                        "description": "Category of the entry",
                        "enum": ["strategic_planning", "team_leadership", "market_analysis", 
                                 "risk_assessment", "innovation", "operations", "financial", 
                                 "customer_insights", "general"]
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Additional tags for the entry"
                    },
                    "metadata": {
                        "type": "object",
                        "description": "Additional metadata",
                        "properties": {
                            "source": {"type": "string"},
                            "device": {"type": "string"},
                            "isVoice": {"type": "boolean"}
                        }
                    }
                },
                "required": ["userId", "content", "category"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "SearchCEOLogs",
            "description": "Search through CEO log entries with advanced filtering and caching. Call the Azure Function to query Cosmos DB.",
            "parameters": {
                "type": "object",
                "properties": {
                    "userId": {
                        "type": "string",
                        "description": "The user ID to search logs for"
                    },
                    "query": {
                        "type": "string",
                        "description": "Search query text"
                    },
                    "category": {
                        "type": "string",
                        "description": "Filter by category"
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Filter by tags"
                    },
                    "startDate": {
                        "type": "string",
                        "description": "Start date for date range filter (ISO format)"
                    },
                    "endDate": {
                        "type": "string",
                        "description": "End date for date range filter (ISO format)"
                    }
                },
                "required": ["userId"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "AnalyzeLogs",
            "description": "Analyze CEO logs for patterns, insights, and recommendations. Call the Azure Function to process entries from Cosmos DB.",
            "parameters": {
                "type": "object",
                "properties": {
                    "userId": {
                        "type": "string",
                        "description": "The user ID to analyze logs for"
                    },
                    "focusArea": {
                        "type": "string",
                        "description": "Specific area to focus analysis on",
                        "enum": ["risks", "opportunities", "team", "market", "all"]
                    },
                    "timeframe": {
                        "type": "string",
                        "description": "Timeframe for analysis",
                        "enum": ["week", "month", "quarter", "all"]
                    }
                },
                "required": ["userId"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "GetInsights",
            "description": "Get recent insights and key metrics from CEO logs. Call the Azure Function to retrieve summary from Cosmos DB.",
            "parameters": {
                "type": "object",
                "properties": {
                    "userId": {
                        "type": "string",
                        "description": "The user ID to get insights for"
                    }
                },
                "required": ["userId"]
            }
        }
    }
]

# Updated instructions with Azure Function integration
INSTRUCTIONS = """You are the CEO Log Agent for StratOS, specializing in processing executive thoughts, observations, and strategic reflections.

You have access to Azure Functions that manage CEO log entries in Cosmos DB:

Available Azure Functions:
- SaveCEOLog: Saves entries to Cosmos DB with AI analysis at {base}/saveceolog
- SearchCEOLogs: Searches entries in Cosmos DB at {base}/searchceologs  
- AnalyzeLogs: Analyzes patterns across entries at {base}/analyzelogs
- GetInsights: Gets summary insights at {base}/getinsights

When a user requests a tool action, you MUST:
1. Extract the required parameters from the user's message
2. Call the appropriate Azure Function with the parameters
3. Process and present the response

IMPORTANT: Each function requires a userId parameter. Use "ceo-001" as the default userId unless specified.

Function URLs and Keys:
{function_config}

Your responsibilities:
1. Process CEO's subjective inputs with strategic awareness
2. Identify patterns, risks, and opportunities across entries
3. Generate actionable insights from reflections
4. Maintain confidentiality while highlighting critical information
5. Connect thoughts to organizational North Star and goals

When processing new entries:
1. Listen carefully to capture the full context
2. Determine the appropriate category based on content
3. Call SaveCEOLog to persist to Cosmos DB
4. Present the analysis results including generated tags and insights

Example interactions:

User: "I'm concerned about our competitor's new AI product launch. We need to accelerate our innovation timeline."
You: [Call SaveCEOLog with category="market_analysis", then present the saved entry details and analysis]

User: "Show me all my entries about team challenges this week"
You: [Call SearchCEOLogs with query="team challenges", then present the results]

User: "Analyze my recent entries for risks and opportunities"
You: [Call AnalyzeLogs with focusArea="all", then present the insights and recommendations]

Response format guidelines:
- Be concise but comprehensive
- Highlight urgent items or risks immediately
- Connect insights to strategic objectives
- Suggest next actions when appropriate
- Maintain professional executive communication style

Remember: You're not just storing information, you're helping the CEO think strategically by organizing thoughts and surfacing patterns."""

async def update_ceo_agent():
    """Update the CEO Log Agent with Azure Functions tools"""
    
    # Format function config for instructions
    function_config = json.dumps({
        "base": AZURE_FUNCTION_BASE,
        "keys": AZURE_FUNCTION_KEYS
    }, indent=2)
    
    formatted_instructions = INSTRUCTIONS.format(
        base=AZURE_FUNCTION_BASE,
        function_config=function_config
    )
    
    async with DefaultAzureCredential() as credential:
        # Use environment variables instead
        import os
        os.environ['AZURE_PROJECT_CONNECTION_STRING'] = PROJECT_CONNECTION_STRING
        
        from azure.ai.projects import AIProjectClient
        client = AIProjectClient.from_connection_string(
            credential=credential,
            conn_str=PROJECT_CONNECTION_STRING
        )
        
        # Find CEO Log Agent
        agents = client.agents.list_agents()
        ceo_agent = None
        
        async for agent in agents:
            if agent.name == "CEOLogAgent":
                ceo_agent = agent
                break
        
        if not ceo_agent:
            print("❌ CEO Log Agent not found")
            return
        
        print(f"✅ Found CEO Log Agent: {ceo_agent.id}")
        
        # Update the agent with new tools and instructions
        updated_agent = await client.agents.update_agent(
            assistant_id=ceo_agent.id,
            instructions=formatted_instructions,
            tools=TOOLS
        )
        
        print("✅ CEO Log Agent updated with Azure Functions integration")
        print(f"   - Tools: {len(TOOLS)} functions configured")
        print(f"   - Base URL: {AZURE_FUNCTION_BASE}")
        print("\n📝 Updated Instructions Preview:")
        print(formatted_instructions[:500] + "...")

if __name__ == "__main__":
    asyncio.run(update_ceo_agent())