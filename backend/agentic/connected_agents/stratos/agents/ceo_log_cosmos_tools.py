"""
CEO Log Agent Tools Configuration for Cosmos DB Integration
Defines Azure Functions-based tools for persistent storage
"""

# Azure Functions base URL (to be configured with actual deployment)
FUNCTION_BASE_URL = "https://ceo-log-functions.azurewebsites.net/api"
FUNCTION_KEY = ""  # To be set from environment variable

CEO_LOG_COSMOS_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "SaveCEOLog",
            "description": "Save a CEO log entry to Cosmos DB with AI-powered analysis and categorization",
            "parameters": {
                "type": "object",
                "properties": {
                    "userId": {
                        "type": "string",
                        "description": "Unique user identifier (required)"
                    },
                    "content": {
                        "type": "string",
                        "description": "The CEO log entry content (max 5000 characters)"
                    },
                    "category": {
                        "type": "string",
                        "enum": [
                            "strategic_planning",
                            "team_leadership",
                            "market_analysis",
                            "risk_assessment",
                            "innovation",
                            "operations",
                            "financial",
                            "customer_insights",
                            "general"
                        ],
                        "description": "Category for the log entry (defaults to 'general')"
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional user-defined tags to supplement AI-generated tags"
                    },
                    "metadata": {
                        "type": "object",
                        "properties": {
                            "source": {
                                "type": "string",
                                "description": "Source of the log entry (e.g., 'voice', 'text', 'meeting')"
                            },
                            "isVoice": {
                                "type": "boolean",
                                "description": "Whether this entry was transcribed from voice"
                            },
                            "sessionId": {
                                "type": "string",
                                "description": "Session ID to group related log entries"
                            },
                            "duration": {
                                "type": "integer",
                                "description": "Duration in seconds for voice entries"
                            },
                            "location": {
                                "type": "string",
                                "description": "Location where the log was created"
                            },
                            "device": {
                                "type": "string",
                                "description": "Device used to create the log"
                            }
                        },
                        "description": "Optional metadata about the log entry"
                    }
                },
                "required": ["userId", "content"]
            },
            # URL to be injected at deployment time
            "url": f"{FUNCTION_BASE_URL}/SaveCEOLog"
        }
    },
    {
        "type": "function",
        "function": {
            "name": "SearchCEOLogs",
            "description": "Search CEO log entries with advanced filtering, full-text search, and relevance scoring",
            "parameters": {
                "type": "object",
                "properties": {
                    "userId": {
                        "type": "string",
                        "description": "User ID to search within (required)"
                    },
                    "query": {
                        "type": "string",
                        "description": "Search keywords or phrases to find in content or summaries"
                    },
                    "category": {
                        "type": "string",
                        "enum": [
                            "strategic_planning",
                            "team_leadership",
                            "market_analysis",
                            "risk_assessment",
                            "innovation",
                            "operations",
                            "financial",
                            "customer_insights",
                            "general"
                        ],
                        "description": "Filter results by specific category"
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Filter by one or more tags (matches any)"
                    },
                    "dateRange": {
                        "type": "object",
                        "properties": {
                            "start": {
                                "type": "string",
                                "format": "date-time",
                                "description": "Start date for filtering (ISO 8601 format)"
                            },
                            "end": {
                                "type": "string",
                                "format": "date-time",
                                "description": "End date for filtering (ISO 8601 format)"
                            }
                        },
                        "description": "Optional date range filter"
                    },
                    "limit": {
                        "type": "integer",
                        "default": 10,
                        "minimum": 1,
                        "maximum": 100,
                        "description": "Maximum number of results to return"
                    },
                    "offset": {
                        "type": "integer",
                        "default": 0,
                        "minimum": 0,
                        "description": "Number of results to skip for pagination"
                    }
                },
                "required": ["userId"]
            },
            "url": f"{FUNCTION_BASE_URL}/SearchCEOLogs"
        }
    },
    {
        "type": "function",
        "function": {
            "name": "AnalyzeLogs",
            "description": "Analyze CEO logs for patterns, insights, trends, and actionable recommendations",
            "parameters": {
                "type": "object",
                "properties": {
                    "userId": {
                        "type": "string",
                        "description": "User ID to analyze (required)"
                    },
                    "timeframe": {
                        "type": "string",
                        "enum": ["week", "month", "quarter", "year", "all"],
                        "default": "month",
                        "description": "Time period to analyze"
                    },
                    "focusArea": {
                        "type": "string",
                        "enum": ["risks", "opportunities", "team", "market", "general"],
                        "default": "general",
                        "description": "Specific area to focus the analysis on"
                    }
                },
                "required": ["userId"]
            },
            "url": f"{FUNCTION_BASE_URL}/AnalyzeLogs"
        }
    }
]

# Enhanced instructions for CEO Log Agent with Cosmos DB
CEO_LOG_COSMOS_INSTRUCTIONS = """You are the CEO Log Agent for StratOS with advanced persistent storage capabilities powered by Cosmos DB and Azure Functions.

ENHANCED CAPABILITIES:
1. **Persistent Storage**: All log entries are permanently stored in Cosmos DB with enterprise-grade reliability
2. **AI-Powered Analysis**: Automatic sentiment analysis, tag generation, and insight extraction
3. **Full-Text Search**: Search across all historical entries with relevance scoring
4. **Advanced Analytics**: Pattern recognition, trend analysis, and actionable recommendations
5. **Performance**: Sub-second response times with intelligent caching

WHEN SAVING ENTRIES:
- Use SaveCEOLog to persist entries with comprehensive AI analysis
- The system automatically:
  - Analyzes sentiment with confidence scores
  - Generates relevant tags and strategic themes
  - Extracts action items, risks, and opportunities
  - Creates concise summaries
  - Marks urgent items for immediate attention
- Always specify the appropriate category for better organization
- Add custom tags to supplement AI-generated ones when relevant

WHEN SEARCHING:
- Use SearchCEOLogs for powerful querying capabilities
- Search by content, tags, categories, or date ranges
- Results include relevance scores and key metadata
- Use pagination (limit/offset) for large result sets
- Combine filters for precise results

WHEN ANALYZING:
- Use AnalyzeLogs for strategic insights and trends
- Choose appropriate timeframe (week/month/quarter/year)
- Select focus area for targeted analysis:
  - risks: Risk patterns and mitigation needs
  - opportunities: Growth potential and innovation
  - team: Organizational health and culture
  - market: Competitive landscape and customer insights
  - general: Comprehensive strategic overview
- Receive actionable recommendations based on patterns

RESPONSE GUIDELINES:
- Be concise but comprehensive in responses
- Highlight urgent items or risks immediately
- Connect insights to strategic objectives
- Suggest next actions when appropriate
- Maintain professional executive communication style

EXAMPLE INTERACTIONS:

User: "I'm concerned about our competitor's new AI product launch. We need to accelerate our innovation timeline."
You: I'll save this strategic observation about competitive pressure and innovation urgency.
[Use SaveCEOLog with category="market_analysis"]
[Response includes: entry saved confirmation, AI-generated tags like "competitor", "AI", "innovation", "urgent", summary, and risk indicator]

User: "Show me all my entries about team challenges from the last month"
You: I'll search for team-related entries from the past month.
[Use SearchCEOLogs with query="team challenges", timeframe last 30 days]
[Present relevant entries with summaries, relevance scores, and patterns identified]

User: "Analyze my logs this quarter focusing on risks"
You: I'll analyze your quarterly logs with a focus on risk patterns.
[Use AnalyzeLogs with timeframe="quarter", focusArea="risks"]
[Present risk themes, frequency, recommendations for mitigation, and urgent items]

Remember: You're not just storing information, you're helping the CEO think strategically by organizing thoughts, surfacing patterns, and generating actionable insights from their reflections. All data is securely stored and accessible across sessions, building a comprehensive strategic knowledge base over time."""