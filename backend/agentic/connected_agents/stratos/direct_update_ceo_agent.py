#!/usr/bin/env python3
"""Update CEO Log Agent with direct OpenAI client"""

import os
from openai import OpenAI
import json

# Configuration
AZURE_FUNCTION_BASE = "https://stratos-ceo-log-functions.azurewebsites.net/api"
AZURE_FUNCTION_KEYS = {
    "SaveCEOLog": "I3c897PZMtJp1goBaxPwGlXa3Ni6ZsM09t1F7roTLVZeAzFu69TeKA==",
    "SearchCEOLogs": "uXjWD5crSSJYH_7eL3IcQq_ebEqVqO9D2QaC24UKa_RNAzFuVD7gkg==",
    "AnalyzeLogs": "1ALdM_XHFGwQ5XtC5BBsnJ-_j_w30lef9DsjGWVrpNJfAzFuEHzbmg==",
    "GetInsights": "Rx3WeFi1SoWXpbiZtsOCBVyswP06bUskqSYKK5HdntHBAzFuqJ56aw=="
}

# Function tools that call Azure Functions
FUNCTION_TOOLS = [
    {
        "type": "function", 
        "function": {
            "name": "SaveCEOLog",
            "description": f"Save a CEO log entry. Makes HTTP POST to {AZURE_FUNCTION_BASE}/saveceolog",
            "parameters": {
                "type": "object",
                "properties": {
                    "userId": {"type": "string", "description": "User ID (use 'ceo-001' as default)"},
                    "content": {"type": "string", "description": "Log entry content"},
                    "category": {
                        "type": "string",
                        "enum": ["strategic_planning", "team_leadership", "market_analysis", 
                                "risk_assessment", "innovation", "operations", "financial", 
                                "customer_insights", "general"]
                    },
                    "tags": {"type": "array", "items": {"type": "string"}},
                    "metadata": {"type": "object"}
                },
                "required": ["userId", "content", "category"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "SearchCEOLogs", 
            "description": f"Search CEO logs. Makes HTTP POST to {AZURE_FUNCTION_BASE}/searchceologs",
            "parameters": {
                "type": "object",
                "properties": {
                    "userId": {"type": "string", "description": "User ID (use 'ceo-001' as default)"},
                    "query": {"type": "string", "description": "Search query"},
                    "category": {"type": "string"},
                    "tags": {"type": "array", "items": {"type": "string"}},
                    "startDate": {"type": "string"},
                    "endDate": {"type": "string"}
                },
                "required": ["userId"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "AnalyzeLogs",
            "description": f"Analyze CEO logs. Makes HTTP POST to {AZURE_FUNCTION_BASE}/analyzelogs", 
            "parameters": {
                "type": "object",
                "properties": {
                    "userId": {"type": "string", "description": "User ID (use 'ceo-001' as default)"},
                    "focusArea": {
                        "type": "string",
                        "enum": ["risks", "opportunities", "team", "market", "all"]
                    },
                    "timeframe": {
                        "type": "string", 
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
            "description": f"Get insights from CEO logs. Makes HTTP GET to {AZURE_FUNCTION_BASE}/getinsights",
            "parameters": {
                "type": "object",
                "properties": {
                    "userId": {"type": "string", "description": "User ID (use 'ceo-001' as default)"}
                },
                "required": ["userId"]
            }
        }
    }
]

# Code interpreter for making HTTP calls
CODE_INTERPRETER_INSTRUCTIONS = f"""
When you need to call any of the CEO Log functions, make HTTP requests to the Azure Functions:

Base URL: {AZURE_FUNCTION_BASE}
Function Keys: {json.dumps(AZURE_FUNCTION_KEYS, indent=2)}

For each function call:
1. Construct the appropriate URL with function key
2. Make HTTP request with the parameters
3. Parse and return the response

Example for SaveCEOLog:
```python
import requests
url = "{AZURE_FUNCTION_BASE}/saveceolog?code={AZURE_FUNCTION_KEYS['SaveCEOLog']}"
payload = {{
    "userId": "ceo-001",
    "content": "...",
    "category": "...",
    "tags": [],
    "metadata": {{}}
}}
response = requests.post(url, json=payload)
result = response.json()
```
"""

# Get OpenAI API key from environment
api_key = os.environ.get("OPENAI_API_KEY")
if not api_key:
    print("Please set OPENAI_API_KEY environment variable")
    exit(1)

client = OpenAI(api_key=api_key)

# Find the CEO Log Agent
assistants = client.beta.assistants.list()
ceo_agent = None

for assistant in assistants.data:
    if assistant.name == "CEOLogAgent":
        ceo_agent = assistant
        break

if not ceo_agent:
    print("❌ CEO Log Agent not found")
    exit(1)

print(f"✅ Found CEO Log Agent: {ceo_agent.id}")

# Update with code interpreter and function definitions
updated_instructions = f"""You are the CEO Log Agent for StratOS.

{CODE_INTERPRETER_INSTRUCTIONS}

Your responsibilities:
1. Process CEO's subjective inputs with strategic awareness
2. Save entries to Cosmos DB using the Azure Functions
3. Search and analyze entries to identify patterns
4. Generate actionable insights from reflections

When processing requests:
- For new entries: Call SaveCEOLog function
- For searches: Call SearchCEOLogs function  
- For analysis: Call AnalyzeLogs function
- For insights: Call GetInsights function

Always use "ceo-001" as the default userId unless specified otherwise.
"""

# Update the assistant
updated = client.beta.assistants.update(
    ceo_agent.id,
    instructions=updated_instructions,
    tools=[{"type": "code_interpreter"}] + FUNCTION_TOOLS,
    model="gpt-4-turbo"
)

print("✅ CEO Log Agent updated successfully!")
print(f"   - Code interpreter enabled")
print(f"   - {len(FUNCTION_TOOLS)} function tools configured")
print(f"   - Azure Functions base: {AZURE_FUNCTION_BASE}")