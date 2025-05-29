"""
CEO Log Agent Configuration - Following Weather Agent Pattern
Manages CEO's subjective inputs using Azure Functions for Cosmos DB operations
"""

# Agent configuration
AGENT_NAME_PREFIX = "CEOLogAgentFinal"

# Model configuration  
MODEL_NAME = "gpt-35-turbo"

# Azure Functions for Cosmos DB integration
AZURE_FUNCTION_BASE = "https://stratos-ceo-log-functions.azurewebsites.net/api"
AZURE_FUNCTION_KEYS = {
    "SaveCEOLog": "I3c897PZMtJp1goBaxPwGlXa3Ni6ZsM09t1F7roTLVZeAzFu69TeKA==",
    "SearchCEOLogs": "uXjWD5crSSJYH_7eL3IcQq_ebEqVqO9D2QaC24UKa_RNAzFuVD7gkg==", 
    "AnalyzeLogs": "1ALdM_XHFGwQ5XtC5BBsnJ-_j_w30lef9DsjGWVrpNJfAzFuEHzbmg==",
    "GetInsights": "Rx3WeFi1SoWXpbiZtsOCBVyswP06bUskqSYKK5HdntHBAzFuqJ56aw=="
}

AGENT_INSTRUCTIONS = f"""You are the CEO Log Agent for StratOS, specializing in processing executive thoughts, observations, and strategic reflections.

## Your Capabilities:
You have access to Azure Functions for CEO log management through the 'call_ceo_log_function' tool. This allows you to:
- Save new log entries with automatic AI analysis
- Search through historical log entries 
- Analyze logs for patterns and insights
- Get recent insights and key metrics

## Function Endpoint Configuration:
- Base URL: {AZURE_FUNCTION_BASE}
- Function Keys are configured per endpoint

## Your Workflow:

1. When asked to save a log entry:
   - Use call_ceo_log_function with operation="SaveCEOLog"
   - Include userId (always "CEO"), content, category, and source
   - Report the entryId returned on success

2. When searching entries:
   - Use call_ceo_log_function with operation="SearchCEOLogs"
   - Include search parameters like query, category, tags, date range

3. When analyzing logs:
   - Use call_ceo_log_function with operation="AnalyzeLogs"
   - Specify focusArea and timeframe

4. When getting insights:
   - Use call_ceo_log_function with operation="GetInsights"
   - This provides recent insights and key metrics

## Valid Categories:
- strategic_planning: Vision, goals, long-term planning
- team_leadership: People, culture, organizational matters
- market_analysis: Customer insights, competition, trends
- risk_assessment: Concerns, threats, mitigation strategies
- innovation: New ideas, technology, transformation
- operations: Process improvements, efficiency
- financial: Budget, revenue, cost considerations
- customer_insights: Direct customer feedback or observations
- general: Cross-functional or uncategorized thoughts

## Response Guidelines:
- Always confirm successful operations with specific details
- Report entry IDs when saving
- Be concise but informative
- Focus on the most relevant information
- Report any errors clearly

Remember: Use the call_ceo_log_function tool to interact with the Azure Functions. The functions handle all Cosmos DB operations."""

# Tool definitions following weather agent pattern
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "call_ceo_log_function",
            "description": "Call the Azure Function for CEO log operations including save, search, analyze, and get insights",
            "parameters": {
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": ["SaveCEOLog", "SearchCEOLogs", "AnalyzeLogs", "GetInsights"],
                        "description": "The operation to perform"
                    },
                    "userId": {
                        "type": "string",
                        "description": "The user ID (always 'CEO' for CEO logs)"
                    },
                    "content": {
                        "type": "string",
                        "description": "The raw content of the log entry (for SaveCEOLog)"
                    },
                    "category": {
                        "type": "string",
                        "enum": ["strategic_planning", "team_leadership", "market_analysis", 
                                 "risk_assessment", "innovation", "operations", "financial", 
                                 "customer_insights", "general"],
                        "description": "Category of the entry (for SaveCEOLog)"
                    },
                    "source": {
                        "type": "string",
                        "description": "Source of the entry - voice, text, etc. (for SaveCEOLog)",
                        "default": "text"
                    },
                    "query": {
                        "type": "string",
                        "description": "Search query text (for SearchCEOLogs)"
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Filter by tags (for SearchCEOLogs)"
                    },
                    "startDate": {
                        "type": "string",
                        "description": "Start date in ISO format (for SearchCEOLogs)"
                    },
                    "endDate": {
                        "type": "string",
                        "description": "End date in ISO format (for SearchCEOLogs)"
                    },
                    "focusArea": {
                        "type": "string",
                        "enum": ["risks", "opportunities", "team", "market", "all"],
                        "description": "Specific area to focus analysis on (for AnalyzeLogs)"
                    },
                    "timeframe": {
                        "type": "string",
                        "enum": ["week", "month", "quarter", "all"],
                        "description": "Timeframe for analysis (for AnalyzeLogs)"
                    }
                },
                "required": ["operation"]
            }
        }
    }
]