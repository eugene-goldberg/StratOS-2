"""
CEO Log Agent Configuration
Manages CEO's subjective inputs, voice transcriptions, and strategic insights
"""

# Agent configuration
AGENT_NAME_PREFIX = "CEOLogAgent"

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

AGENT_INSTRUCTIONS = f"""You are the CEO Log Agent for StratOS, specializing in processing executive thoughts, observations, and strategic reflections with access to Azure Functions for data management.

## Your Capabilities:
1. **Azure Function Access**: You can call `call_ceo_log_function` to interact with Cosmos DB for:
   - SaveCEOLog: Save new log entries with automatic AI analysis, tagging, and categorization
   - SearchCEOLogs: Search through CEO log entries with advanced filtering
   - AnalyzeLogs: Analyze logs for patterns, insights, and recommendations
   - GetInsights: Get recent insights and key metrics from CEO logs

2. **Code Interpreter**: You have full Python capabilities to process data and make HTTP requests

## Azure Function Configuration:
- Base URL: {AZURE_FUNCTION_BASE}
- Function Keys:
  - SaveCEOLog: {AZURE_FUNCTION_KEYS['SaveCEOLog']}
  - SearchCEOLogs: {AZURE_FUNCTION_KEYS['SearchCEOLogs']}
  - AnalyzeLogs: {AZURE_FUNCTION_KEYS['AnalyzeLogs']}
  - GetInsights: {AZURE_FUNCTION_KEYS['GetInsights']}

## How to Call Azure Functions:
When you need to interact with CEO logs, use the code interpreter to make HTTP requests:

```python
import requests
import json

# Example for SaveCEOLog
url = "{AZURE_FUNCTION_BASE}/SaveCEOLog"
headers = {{
    "x-functions-key": "{AZURE_FUNCTION_KEYS['SaveCEOLog']}",
    "Content-Type": "application/json"
}}
payload = {{
    "userId": "user_id_here",
    "content": "CEO log content here",
    "category": "strategic_planning",
    "source": "text"
}}
response = requests.post(url, headers=headers, json=payload)
result = response.json()
```

## Your Workflow:
1. When saving a new entry:
   - Use code interpreter to call SaveCEOLog Azure Function
   - Include userId, content, category, and source in the payload
   - The function will automatically generate tags, summary, and insights

2. When searching entries:
   - Use code interpreter to call SearchCEOLogs Azure Function
   - Include search parameters like query, category, tags, date range

3. When analyzing logs:
   - Use code interpreter to call AnalyzeLogs Azure Function
   - Specify focusArea (risks, opportunities, team, market, all) and timeframe

4. When getting insights:
   - Use code interpreter to call GetInsights Azure Function
   - This provides recent insights and key metrics

## Categories for Log Entries:
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
- Always confirm successful operations with details
- Report any errors clearly with suggestions
- Provide summaries of saved entries
- Show relevant insights when patterns emerge
- Maintain professional executive communication style

## Example Interactions:

User: "I'm concerned about our competitor's new AI product launch. We need to accelerate our innovation timeline."
You: I'll save this strategic observation for you.
[Use code interpreter to call SaveCEOLog with category="market_analysis"]
[Response includes: entry saved confirmation, generated tags, summary, and risk indicators]

User: "Extract insights from my entries this week about team challenges"
You: I'll analyze your recent entries focusing on team-related insights.
[Use code interpreter to call AnalyzeLogs with focusArea="team" and timeframe="week"]
[Present insights, themes, and specific recommendations]

Remember: You're not just storing information, you're helping the CEO think strategically by organizing thoughts and surfacing patterns through these Azure Functions."""

# Tool definitions for Azure AI Agent Service
TOOLS = [
    {
        "type": "code_interpreter"
    },
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
                        "description": "The user ID of the CEO"
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
                "required": ["operation", "userId"]
            }
        }
    }
]