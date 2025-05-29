#!/usr/bin/env python3
"""
Deploy CEO Log Agent to Azure AI Agent Service with Azure Function integration.
Following the exact pattern from the weather agent deployment.
"""

import sys
import os
from datetime import datetime
import json

# Add parent directories to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

# Project configuration
AZURE_AI_PROJECT_CONNECTION_STRING = "https://ai.azure.com/api/eastus/agents/v1.0/subscriptions/514bd6d3-2c02-45c6-a86f-29cf262a379a/resourceGroups/semantic-kernel-multi-agent-rg/providers/Microsoft.MachineLearningServices/workspaces/sk-multi-agent-project"
AZURE_OPENAI_DEPLOYMENT_NAME = "gpt-35-turbo"

# Azure Function configuration for CEO Log
FUNCTION_ENDPOINT = "https://stratos-ceo-log-functions.azurewebsites.net/api"
FUNCTION_KEYS = {
    "SaveCEOLog": "I3c897PZMtJp1goBaxPwGlXa3Ni6ZsM09t1F7roTLVZeAzFu69TeKA==",
    "SearchCEOLogs": "uXjWD5crSSJYH_7eL3IcQq_ebEqVqO9D2QaC24UKa_RNAzFuVD7gkg==",
    "AnalyzeLogs": "1ALdM_XHFGwQ5XtC5BBsnJ-_j_w30lef9DsjGWVrpNJfAzFuEHzbmg==",
    "GetInsights": "Rx3WeFi1SoWXpbiZtsOCBVyswP06bUskqSYKK5HdntHBAzFuqJ56aw=="
}

def deploy_ceo_log_agent():
    """Deploy CEO Log Agent to Azure AI Agent Service with Azure Function integration."""
    print("Deploying CEO Log Agent to Azure AI Agent Service")
    print("=" * 70)
    
    # Create client
    credential = DefaultAzureCredential()
    client = AIProjectClient(endpoint=AZURE_AI_PROJECT_CONNECTION_STRING, credential=credential)
    
    # Define tools with function calling and code interpreter
    tools = [
        {
            "type": "code_interpreter"
        },
        {
            "type": "function",
            "function": {
                "name": "call_ceo_function",
                "description": "Call the Azure Function for CEO log operations including save, search, analyze, and get insights",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "operation": {
                            "type": "string",
                            "enum": ["save_log", "search_logs", "analyze_logs", "get_insights"],
                            "description": "The operation to perform"
                        },
                        "userId": {
                            "type": "string",
                            "description": "User ID (default: ceo-001)"
                        },
                        "content": {
                            "type": "string",
                            "description": "Log entry content (for save operation)"
                        },
                        "category": {
                            "type": "string",
                            "enum": ["strategic_planning", "team_leadership", "market_analysis", 
                                    "risk_assessment", "innovation", "operations", "financial", 
                                    "customer_insights", "general"],
                            "description": "Category of the entry"
                        },
                        "query": {
                            "type": "string",
                            "description": "Search query (for search operation)"
                        },
                        "focusArea": {
                            "type": "string",
                            "enum": ["risks", "opportunities", "team", "market", "general"],
                            "description": "Focus area for analysis"
                        },
                        "timeframe": {
                            "type": "string",
                            "enum": ["week", "month", "quarter", "all"],
                            "description": "Timeframe for analysis"
                        },
                        "tags": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Tags for the entry or search filter"
                        },
                        "metadata": {
                            "type": "object",
                            "description": "Additional metadata for the log entry"
                        }
                    },
                    "required": ["operation"]
                }
            }
        }
    ]
    
    # Create comprehensive instructions
    instructions = f"""You are the CEO Log Agent for StratOS, specializing in processing executive thoughts and strategic reflections.

## Your Capabilities:
1. **Azure Function Access**: You can call `call_ceo_function` to interact with Cosmos DB for:
   - Saving new CEO log entries with AI analysis
   - Searching through past entries
   - Analyzing patterns and generating insights  
   - Getting recent metrics and summaries

## Your Workflow:
1. When user wants to save a log entry:
   - Call `call_ceo_function` with operation="save_log"
   - Include userId (default: "ceo-001"), content, category, and optional tags/metadata
   - The function will perform AI analysis and save to Cosmos DB

2. When user wants to search entries:
   - Call `call_ceo_function` with operation="search_logs"
   - Include query and optional filters (category, tags, date range)

3. When user wants analysis:
   - Call `call_ceo_function` with operation="analyze_logs"
   - Include focusArea and timeframe

4. When user wants insights:
   - Call `call_ceo_function` with operation="get_insights"

## Function Endpoint Configuration:
- SaveCEOLog: {FUNCTION_ENDPOINT}/saveceolog?code={FUNCTION_KEYS['SaveCEOLog']}
- SearchCEOLogs: {FUNCTION_ENDPOINT}/searchceologs?code={FUNCTION_KEYS['SearchCEOLogs']}
- AnalyzeLogs: {FUNCTION_ENDPOINT}/analyzelogs?code={FUNCTION_KEYS['AnalyzeLogs']}
- GetInsights: {FUNCTION_ENDPOINT}/getinsights?code={FUNCTION_KEYS['GetInsights']}

## How to make Azure Function calls:
When you need to call an Azure Function, use the code interpreter to make HTTP requests:

```python
import requests
import json

# Example for saving a log entry
def save_ceo_log(content, category, tags=[], metadata={{}}):
    url = "{FUNCTION_ENDPOINT}/saveceolog?code={FUNCTION_KEYS['SaveCEOLog']}"
    payload = {{
        "userId": "ceo-001",
        "content": content,
        "category": category,
        "tags": tags,
        "metadata": metadata
    }}
    response = requests.post(url, json=payload)
    return response.json()

# Example for searching logs
def search_ceo_logs(query, category=None, tags=None):
    url = "{FUNCTION_ENDPOINT}/searchceologs?code={FUNCTION_KEYS['SearchCEOLogs']}"
    payload = {{
        "userId": "ceo-001",
        "query": query
    }}
    if category:
        payload["category"] = category
    if tags:
        payload["tags"] = tags
    response = requests.post(url, json=payload)
    return response.json()

# Example for analyzing logs
def analyze_logs(focus_area="general", timeframe="month"):
    url = "{FUNCTION_ENDPOINT}/analyzelogs?code={FUNCTION_KEYS['AnalyzeLogs']}"
    payload = {{
        "userId": "ceo-001",
        "focusArea": focus_area,
        "timeframe": timeframe
    }}
    response = requests.post(url, json=payload)
    return response.json()

# Example for getting insights
def get_insights():
    url = "{FUNCTION_ENDPOINT}/getinsights?code={FUNCTION_KEYS['GetInsights']}"
    payload = {{
        "userId": "ceo-001"
    }}
    response = requests.post(url, json=payload)
    return response.json()
```

## Response Guidelines:
- Always confirm when entries are saved successfully
- Report if data is from cache (fast) or fresh query
- Highlight urgent items or risks immediately
- Connect insights to strategic objectives
- Suggest next actions when appropriate

## Categories:
- strategic_planning: Vision, goals, long-term planning
- team_leadership: People, culture, organizational matters
- market_analysis: Customer insights, competition, trends
- risk_assessment: Concerns, threats, mitigation strategies
- innovation: New ideas, technology, transformation
- operations: Process improvements, efficiency
- financial: Budget, revenue, cost considerations
- customer_insights: Direct customer feedback
- general: Cross-functional thoughts

Remember: You're helping the CEO think strategically by organizing thoughts and surfacing patterns."""
    
    print("Creating CEO Log Agent with function calling capabilities...")
    
    agent = client.agents.create_agent(
        model=AZURE_OPENAI_DEPLOYMENT_NAME,
        name=f"CEOLogAgent-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
        instructions=instructions,
        tools=tools
    )
    
    print(f"\n✓ CEO Log Agent deployed successfully!")
    print(f"  Agent ID: {agent.id}")
    print(f"  Name: {agent.name}")
    
    # Save deployment info
    deployment_info = {
        "ceo_log_agent": {
            "id": agent.id,
            "name": agent.name,
            "type": "azure_ai_agent_service",
            "has_function_tools": True,
            "has_code_interpreter": True,
            "function_endpoints": {
                "save": f"{FUNCTION_ENDPOINT}/saveceolog",
                "search": f"{FUNCTION_ENDPOINT}/searchceologs",
                "analyze": f"{FUNCTION_ENDPOINT}/analyzelogs",
                "insights": f"{FUNCTION_ENDPOINT}/getinsights"
            },
            "deployed_at": datetime.now().isoformat()
        }
    }
    
    # Save to deployment file
    deployment_file = os.path.join(os.path.dirname(__file__), 'deployment_info.json')
    
    try:
        with open(deployment_file, 'r') as f:
            existing_info = json.load(f)
    except:
        existing_info = {}
    
    existing_info.update(deployment_info)
    
    with open(deployment_file, 'w') as f:
        json.dump(existing_info, f, indent=2)
    
    print("\n📋 Deployment Summary:")
    print(f"- Agent deployed to Azure AI Agent Service")
    print(f"- Agent ID: {agent.id}")
    print(f"- Azure Functions configured:")
    print(f"  • Save CEO Log: {FUNCTION_ENDPOINT}/saveceolog")
    print(f"  • Search Logs: {FUNCTION_ENDPOINT}/searchceologs")
    print(f"  • Analyze Logs: {FUNCTION_ENDPOINT}/analyzelogs")
    print(f"  • Get Insights: {FUNCTION_ENDPOINT}/getinsights")
    print("- Function calling capabilities enabled")
    print("- Code interpreter enabled for HTTP requests")
    print("- Ready to handle CEO log entries with Cosmos DB storage")
    
    print("\n💡 Test the agent with:")
    print("1. 'I need to log a strategic observation about our AI initiative'")
    print("2. 'Search for my entries about digital transformation'")
    print("3. 'Analyze my recent entries for risks and opportunities'")
    print("4. 'What insights do you have from my logs?'")
    
    return agent


def main():
    """Deploy the agent."""
    try:
        agent = deploy_ceo_log_agent()
        
        if agent:
            print("\n" + "=" * 70)
            print("CEO Log Agent - Azure AI Agent Service Deployment Complete")
            print("=" * 70)
            print(f"\nAgent ID: {agent.id}")
            print("\nThe agent is now ready to:")
            print("✓ Save CEO log entries to Cosmos DB with AI analysis")
            print("✓ Search through past entries with advanced filtering")
            print("✓ Analyze patterns and generate strategic insights")
            print("✓ Provide summaries and metrics from CEO logs")
            print("\nUse the agent ID to interact with it through the test scripts.")
    except Exception as e:
        print(f"\n❌ Deployment failed: {str(e)}")
        print("\nTroubleshooting tips:")
        print("1. Ensure Azure credentials are configured")
        print("2. Check that the Azure AI Project exists")
        print("3. Verify the connection string is correct")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())