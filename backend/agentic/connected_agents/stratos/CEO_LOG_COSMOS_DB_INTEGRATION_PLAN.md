# CEO Log Agent Cosmos DB Integration Plan

## Executive Summary

This plan outlines the integration of Azure Cosmos DB with the StratOS CEO Log Agent, adapting the proven Azure Functions bridge pattern from the COSMOS_DB_INTEGRATION_GUIDE.md. The integration will enable persistent storage, advanced querying, and analytics for CEO log entries while maintaining the security and sandboxed execution model of Azure AI Agent Service.

## Architecture Overview

```
┌─────────────────┐     ┌───────────────────┐     ┌────────────────┐     ┌─────────────┐
│  CEO Log Agent  │────▶│  Azure Functions  │────▶│   Cosmos DB    │────▶│  Analytics  │
│  (AI Service)   │◀────│   (Bridge API)    │◀────│  (NoSQL Store) │     │  Dashboard  │
└─────────────────┘     └───────────────────┘     └────────────────┘     └─────────────┘
      Tools:                 Operations:               Collections:           Features:
   - SaveCEOLog           - Create Entry           - ceoLogEntries       - Power BI
   - SearchCEOLogs        - Update Entry           - logAnalytics        - Insights
   - AnalyzeLogs          - Query Entries          - userPreferences     - Trends
   - GetInsights          - Bulk Operations        - strategicThemes     - Reports
```

## Phase 1: Foundation Setup (Week 1)

### 1.1 Cosmos DB Configuration

```json
{
  "databaseId": "StratOSDatabase",
  "containers": [
    {
      "id": "ceoLogEntries",
      "partitionKey": "/userId",
      "uniqueKeys": ["/id"],
      "ttl": -1,
      "indexingPolicy": {
        "automatic": true,
        "includedPaths": [
          {
            "path": "/*",
            "indexes": [
              {
                "kind": "Range",
                "dataType": "String"
              },
              {
                "kind": "Range",
                "dataType": "Number"
              }
            ]
          }
        ],
        "compositeIndexes": [
          [
            {"path": "/userId", "order": "ascending"},
            {"path": "/timestamp", "order": "descending"}
          ],
          [
            {"path": "/userId", "order": "ascending"},
            {"path": "/tags/*", "order": "ascending"}
          ]
        ]
      }
    },
    {
      "id": "logAnalytics",
      "partitionKey": "/userId",
      "ttl": 2592000,  // 30 days for analytics cache
      "indexingPolicy": {
        "automatic": true
      }
    }
  ]
}
```

### 1.2 Data Schema (Based on existing models)

```typescript
interface CEOLogEntry {
  // Core fields (from ceo_log_models.py)
  id: string;                    // Unique identifier
  userId: string;                // Partition key
  timestamp: string;             // ISO 8601 format
  
  // Content
  logEntry: {
    content: string;             // Max 5000 chars
    sentiment: 'positive' | 'negative' | 'neutral';
    confidence: number;          // 0-1
  };
  
  // Organization
  category: string;              // From agent config categories
  tags: string[];               // User and AI-generated
  strategicThemes: string[];    // AI-identified themes
  
  // Metadata
  metadata: {
    source?: string;            // voice, text, meeting
    duration?: number;          // For voice entries
    location?: string;
    device?: string;
    sessionId?: string;         // Group related logs
    isVoice: boolean;
    wordCount: number;
  };
  
  // AI Analysis
  analysis: {
    keyInsights: string[];
    actionItems: string[];
    riskFactors: string[];
    opportunities: string[];
    summary: string;            // 30-50 word summary
    hasActionItems: boolean;
    isUrgent: boolean;
    involvesRisk: boolean;
    strategicRelevance: boolean;
  };
  
  // System fields
  createdBy: string;            // "CEOLogAgent"
  createdAt: string;            // Server timestamp
  modifiedAt: string;
  version: number;
  
  // TTL for archival
  _ttl?: number;               // Optional TTL in seconds
}
```

## Phase 2: Azure Functions Implementation (Week 1-2)

### 2.1 Function App Structure

```
ceo-log-functions/
├── SaveCEOLog/
│   ├── function.json
│   └── index.ts
├── SearchCEOLogs/
│   ├── function.json
│   └── index.ts
├── AnalyzeLogs/
│   ├── function.json
│   └── index.ts
├── GetInsights/
│   ├── function.json
│   └── index.ts
├── BulkOperations/
│   ├── function.json
│   └── index.ts
├── shared/
│   ├── cosmosClient.ts
│   ├── validation.ts
│   ├── analytics.ts
│   └── cache.ts
├── host.json
├── local.settings.json
└── package.json
```

### 2.2 Core Functions

#### SaveCEOLog Function
```typescript
import { AzureFunction, Context, HttpRequest } from "@azure/functions";
import { CosmosClient } from "@azure/cosmos";
import { v4 as uuidv4 } from "uuid";

const httpTrigger: AzureFunction = async function (
  context: Context,
  req: HttpRequest
): Promise<void> {
  const { userId, content, category, tags, metadata } = req.body;
  
  // Validate required fields
  if (!userId || !content) {
    context.res = {
      status: 400,
      body: { error: "Missing required fields: userId and content" }
    };
    return;
  }
  
  // Generate AI analysis (would call Azure OpenAI)
  const analysis = await analyzeContent(content);
  
  // Create entry
  const entry: CEOLogEntry = {
    id: uuidv4(),
    userId,
    timestamp: new Date().toISOString(),
    logEntry: {
      content,
      sentiment: analysis.sentiment,
      confidence: analysis.confidence
    },
    category: category || "general",
    tags: [...(tags || []), ...analysis.generatedTags],
    strategicThemes: analysis.themes,
    metadata: {
      ...metadata,
      wordCount: content.split(/\s+/).length
    },
    analysis: {
      summary: analysis.summary,
      keyInsights: analysis.insights,
      actionItems: analysis.actionItems,
      riskFactors: analysis.risks,
      opportunities: analysis.opportunities,
      hasActionItems: analysis.actionItems.length > 0,
      isUrgent: analysis.isUrgent,
      involvesRisk: analysis.risks.length > 0,
      strategicRelevance: analysis.themes.length > 0
    },
    createdBy: "CEOLogAgent",
    createdAt: new Date().toISOString(),
    modifiedAt: new Date().toISOString(),
    version: 1
  };
  
  // Save to Cosmos DB
  const container = await getContainer("ceoLogEntries");
  const { resource } = await container.items.create(entry);
  
  // Invalidate relevant caches
  await invalidateCache(userId, ["summary", "insights"]);
  
  context.res = {
    status: 201,
    body: {
      success: true,
      entryId: resource.id,
      summary: analysis.summary,
      tags: entry.tags.slice(0, 5),
      metadata: {
        hasActionItems: analysis.actionItems.length > 0,
        isUrgent: analysis.isUrgent,
        involvesRisk: analysis.risks.length > 0
      }
    }
  };
};
```

#### SearchCEOLogs Function
```typescript
const searchFunction: AzureFunction = async function (
  context: Context,
  req: HttpRequest
): Promise<void> {
  const { userId, query, category, tags, limit = 10, offset = 0 } = req.query;
  
  // Build Cosmos DB query
  let querySpec = {
    query: "SELECT * FROM c WHERE c.userId = @userId",
    parameters: [{ name: "@userId", value: userId }]
  };
  
  // Add search conditions
  if (query) {
    querySpec.query += " AND CONTAINS(LOWER(c.logEntry.content), LOWER(@query))";
    querySpec.parameters.push({ name: "@query", value: query });
  }
  
  if (category) {
    querySpec.query += " AND c.category = @category";
    querySpec.parameters.push({ name: "@category", value: category });
  }
  
  if (tags && tags.length > 0) {
    querySpec.query += " AND ARRAY_CONTAINS(c.tags, @tag)";
    querySpec.parameters.push({ name: "@tag", value: tags[0] });
  }
  
  querySpec.query += " ORDER BY c.timestamp DESC OFFSET @offset LIMIT @limit";
  querySpec.parameters.push(
    { name: "@offset", value: parseInt(offset) },
    { name: "@limit", value: parseInt(limit) }
  );
  
  // Execute query with caching
  const cacheKey = `search_${userId}_${JSON.stringify(req.query)}`;
  const cached = await getCache(cacheKey);
  
  if (cached) {
    context.res = { body: cached };
    return;
  }
  
  const container = await getContainer("ceoLogEntries");
  const { resources } = await container.items.query(querySpec).fetchAll();
  
  // Calculate relevance scores
  const results = resources.map(entry => ({
    id: entry.id,
    summary: entry.analysis.summary,
    category: entry.category,
    tags: entry.tags.slice(0, 3),
    timestamp: entry.timestamp,
    relevanceScore: calculateRelevance(entry, query),
    metadata: {
      hasActionItems: entry.analysis.hasActionItems,
      isUrgent: entry.analysis.isUrgent,
      sentiment: entry.logEntry.sentiment
    }
  }));
  
  const response = {
    query,
    totalResults: results.length,
    results: results.sort((a, b) => b.relevanceScore - a.relevanceScore),
    searchCompletedAt: new Date().toISOString()
  };
  
  await setCache(cacheKey, response, 300); // 5 min cache
  
  context.res = { body: response };
};
```

### 2.3 Performance Optimizations

#### Caching Strategy
```typescript
interface CacheEntry {
  key: string;
  value: any;
  expiresAt: number;
  type: 'search' | 'analytics' | 'summary';
}

// Use Cosmos DB container with TTL for caching
async function getCache(key: string): Promise<any> {
  try {
    const container = await getContainer("logAnalytics");
    const { resource } = await container.item(key, key).read();
    
    if (resource && resource.expiresAt > Date.now()) {
      return resource.value;
    }
  } catch (error) {
    // Cache miss
  }
  return null;
}

async function setCache(
  key: string, 
  value: any, 
  ttlSeconds: number = 300
): Promise<void> {
  const container = await getContainer("logAnalytics");
  await container.items.upsert({
    id: key,
    key,
    value,
    expiresAt: Date.now() + (ttlSeconds * 1000),
    _ttl: ttlSeconds
  });
}
```

## Phase 3: Agent Tool Definitions (Week 2)

### 3.1 Updated Tool Configurations

```python
# tools_config.py
CEO_LOG_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "SaveCEOLog",
            "description": "Save a CEO log entry to persistent storage with AI analysis",
            "parameters": {
                "type": "object",
                "properties": {
                    "userId": {
                        "type": "string",
                        "description": "Unique user identifier"
                    },
                    "content": {
                        "type": "string",
                        "description": "The CEO log content (max 5000 chars)"
                    },
                    "category": {
                        "type": "string",
                        "enum": [
                            "strategic_planning", "team_leadership", 
                            "market_analysis", "risk_assessment",
                            "innovation", "operations", "financial",
                            "customer_insights", "general"
                        ],
                        "description": "Log entry category"
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional user-defined tags"
                    },
                    "metadata": {
                        "type": "object",
                        "properties": {
                            "source": {"type": "string"},
                            "isVoice": {"type": "boolean"},
                            "sessionId": {"type": "string"}
                        }
                    }
                },
                "required": ["userId", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "SearchCEOLogs",
            "description": "Search CEO log entries with advanced filtering",
            "parameters": {
                "type": "object",
                "properties": {
                    "userId": {
                        "type": "string",
                        "description": "User ID to search within"
                    },
                    "query": {
                        "type": "string",
                        "description": "Search keywords or phrases"
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
                    "dateRange": {
                        "type": "object",
                        "properties": {
                            "start": {"type": "string", "format": "date-time"},
                            "end": {"type": "string", "format": "date-time"}
                        }
                    },
                    "limit": {
                        "type": "integer",
                        "default": 10,
                        "minimum": 1,
                        "maximum": 100
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
            "description": "Analyze CEO logs for patterns, insights, and trends",
            "parameters": {
                "type": "object",
                "properties": {
                    "userId": {
                        "type": "string",
                        "description": "User ID to analyze"
                    },
                    "timeframe": {
                        "type": "string",
                        "enum": ["week", "month", "quarter", "year", "all"],
                        "default": "month"
                    },
                    "focusArea": {
                        "type": "string",
                        "enum": ["risks", "opportunities", "team", "market", "general"],
                        "description": "Specific area to focus analysis on"
                    }
                },
                "required": ["userId"]
            }
        }
    }
]
```

### 3.2 Agent Deployment Script Update

```python
# deploy_ceo_log_agent_cosmos.py
import os
from openai import AzureOpenAI
from azure.identity import DefaultAzureCredential

def deploy_ceo_log_agent_with_cosmos():
    """Deploy CEO Log Agent with Cosmos DB integration tools"""
    
    client = AzureOpenAI(
        api_key=os.environ["AZURE_OPENAI_API_KEY"],
        api_version="2024-02-15-preview",
        azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"]
    )
    
    # Enhanced instructions with Cosmos DB awareness
    instructions = """You are the CEO Log Agent for StratOS with persistent storage capabilities via Cosmos DB.

ENHANCED CAPABILITIES:
1. All log entries are permanently stored in Cosmos DB
2. Full-text search across all historical entries
3. Advanced analytics and pattern recognition
4. Automatic tagging and categorization with AI
5. Performance tracking and insights generation

When saving entries:
- Use SaveCEOLog to persist entries with full analysis
- The system automatically generates tags, sentiment, and insights
- Entries are indexed for fast retrieval

When searching:
- Use SearchCEOLogs for powerful querying capabilities
- Can search by content, tags, categories, or date ranges
- Results include relevance scores

When analyzing:
- Use AnalyzeLogs for trend analysis and insights
- Identifies patterns across time periods
- Generates actionable recommendations

Remember: All data is securely stored and can be accessed across sessions."""
    
    # Create assistant with Cosmos DB tools
    assistant = client.beta.assistants.create(
        name="CEOLogAgent-CosmosDB",
        instructions=instructions,
        model="gpt-35-turbo",
        tools=CEO_LOG_TOOLS
    )
    
    print(f"CEO Log Agent deployed with Cosmos DB: {assistant.id}")
    return assistant.id
```

## Phase 4: Testing & Validation (Week 2-3)

### 4.1 Test Scenarios

```python
# test_ceo_log_cosmos_integration.py
import asyncio
from datetime import datetime, timedelta

async def test_full_integration():
    """Test complete CEO Log Cosmos DB integration"""
    
    test_cases = [
        {
            "name": "Save and Retrieve",
            "action": "save",
            "content": "We need to accelerate our AI transformation strategy. The market is moving faster than anticipated.",
            "expected": ["AI", "transformation", "strategy", "market"]
        },
        {
            "name": "Search by Category",
            "action": "search",
            "category": "strategic_planning",
            "expected_min_results": 1
        },
        {
            "name": "Analyze Trends",
            "action": "analyze",
            "timeframe": "month",
            "focusArea": "risks",
            "expected_insights": True
        },
        {
            "name": "Bulk Performance",
            "action": "bulk_save",
            "count": 100,
            "expected_time_ms": 5000
        }
    ]
    
    results = []
    for test in test_cases:
        start_time = datetime.now()
        
        if test["action"] == "save":
            result = await save_ceo_log(test["content"])
            assert all(tag in result["tags"] for tag in test["expected"])
            
        elif test["action"] == "search":
            result = await search_ceo_logs(category=test["category"])
            assert len(result["results"]) >= test["expected_min_results"]
            
        elif test["action"] == "analyze":
            result = await analyze_logs(
                timeframe=test["timeframe"],
                focusArea=test["focusArea"]
            )
            assert result.get("insights") is not None
            
        elif test["action"] == "bulk_save":
            tasks = [
                save_ceo_log(f"Test entry {i}")
                for i in range(test["count"])
            ]
            await asyncio.gather(*tasks)
            
        duration = (datetime.now() - start_time).total_seconds() * 1000
        
        results.append({
            "test": test["name"],
            "passed": True,
            "duration_ms": duration
        })
    
    return results
```

### 4.2 Performance Benchmarks

Expected performance metrics based on the guide:
- Single save operation: < 200ms
- Search with cache hit: < 50ms
- Search without cache: < 300ms
- Analytics generation: < 500ms
- Bulk operations (100 items): < 5 seconds

## Phase 5: Migration & Deployment (Week 3)

### 5.1 Data Migration Strategy

```python
# migrate_existing_logs.py
async def migrate_in_memory_to_cosmos():
    """Migrate existing in-memory logs to Cosmos DB"""
    
    # 1. Export from current plugin storage
    existing_logs = await export_plugin_logs()
    
    # 2. Transform to Cosmos DB schema
    transformed_logs = []
    for log in existing_logs:
        transformed = {
            "id": log.get("id"),
            "userId": "default_user",  # Add user context
            "timestamp": log.get("created_at"),
            "logEntry": {
                "content": log.get("content"),
                "sentiment": "neutral",
                "confidence": 0.5
            },
            "category": log.get("category", "general"),
            "tags": log.get("tags", []),
            "strategicThemes": [],
            "metadata": {
                "isVoice": log.get("is_voice", False),
                "wordCount": len(log.get("content", "").split())
            },
            "analysis": {
                "summary": log.get("summary", ""),
                "hasActionItems": log.get("metadata", {}).get("has_action_items", False),
                "isUrgent": log.get("metadata", {}).get("is_urgent", False),
                "involvesRisk": log.get("metadata", {}).get("involves_risk", False)
            },
            "createdBy": "CEOLogAgent",
            "createdAt": log.get("created_at"),
            "modifiedAt": log.get("created_at"),
            "version": 1
        }
        transformed_logs.append(transformed)
    
    # 3. Bulk insert to Cosmos DB
    await bulk_insert_logs(transformed_logs)
    
    print(f"Migrated {len(transformed_logs)} logs to Cosmos DB")
```

### 5.2 Deployment Steps

1. **Azure Resources Setup**
   ```bash
   # Create Resource Group
   az group create --name stratos-ceo-log-rg --location eastus
   
   # Create Cosmos DB Account
   az cosmosdb create \
     --name stratos-ceo-logs \
     --resource-group stratos-ceo-log-rg \
     --kind GlobalDocumentDB \
     --default-consistency-level Session \
     --enable-automatic-failover false
   
   # Create Database and Containers
   az cosmosdb sql database create \
     --account-name stratos-ceo-logs \
     --resource-group stratos-ceo-log-rg \
     --name StratOSDatabase
   
   # Create Function App
   az functionapp create \
     --name ceo-log-functions \
     --resource-group stratos-ceo-log-rg \
     --storage-account stratosceologstore \
     --runtime node \
     --runtime-version 18 \
     --functions-version 4
   ```

2. **Deploy Functions**
   ```bash
   cd ceo-log-functions
   npm install
   func azure functionapp publish ceo-log-functions
   ```

3. **Update Agent Configuration**
   ```python
   # Update agent with Function URLs
   FUNCTION_BASE_URL = "https://ceo-log-functions.azurewebsites.net/api"
   
   tools = [
       {
           "type": "function",
           "function": {
               "name": "SaveCEOLog",
               "url": f"{FUNCTION_BASE_URL}/SaveCEOLog?code={FUNCTION_KEY}"
           }
       }
       # ... other tools
   ]
   ```

## Phase 6: Monitoring & Analytics (Week 4)

### 6.1 Application Insights Integration

```typescript
// telemetry.ts
import { TelemetryClient } from "applicationinsights";

const telemetryClient = new TelemetryClient(process.env.APPINSIGHTS_INSTRUMENTATIONKEY);

export function trackCEOLogOperation(
  operation: string,
  userId: string,
  success: boolean,
  duration: number,
  metadata?: any
) {
  telemetryClient.trackEvent({
    name: `CEOLog.${operation}`,
    properties: {
      userId,
      success: success.toString(),
      ...metadata
    },
    measurements: {
      duration
    }
  });
  
  // Track metrics
  telemetryClient.trackMetric({
    name: `CEOLog.${operation}.Duration`,
    value: duration
  });
}
```

### 6.2 Analytics Dashboard

Create Power BI dashboard with:
- Log entry trends over time
- Sentiment analysis visualization
- Top strategic themes
- Action items tracking
- Risk heat map
- User engagement metrics

## Implementation Timeline

| Week | Phase | Deliverables |
|------|-------|--------------|
| 1 | Foundation | Cosmos DB setup, schema design, initial Functions |
| 2 | Core Development | All Functions implemented, agent tools updated |
| 3 | Testing & Migration | Full testing suite, data migration complete |
| 4 | Analytics & Polish | Monitoring setup, dashboard creation, optimization |

## Success Metrics

1. **Performance**
   - Average response time < 300ms
   - 99.9% uptime
   - Support for 1000+ concurrent users

2. **Functionality**
   - 100% data persistence
   - Full-text search accuracy > 95%
   - AI insights generation < 2 seconds

3. **User Experience**
   - Seamless agent interactions
   - Rich analytics and insights
   - Cross-session continuity

## Conclusion

This integration plan transforms the CEO Log Agent from an in-memory system to a fully persistent, scalable solution backed by Cosmos DB. The Azure Functions bridge pattern ensures secure, high-performance operations while maintaining the sandboxed execution model of Azure AI Agent Service.

The phased approach allows for incremental development and testing, ensuring a smooth transition with minimal disruption to existing functionality. Upon completion, the CEO Log Agent will provide enterprise-grade logging, search, and analytics capabilities essential for strategic decision-making.