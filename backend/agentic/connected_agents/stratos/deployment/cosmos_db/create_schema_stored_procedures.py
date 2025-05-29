#!/usr/bin/env python3
"""
Create Schema and Stored Procedures for CEO Log Cosmos DB
This script creates optimized queries, stored procedures, and triggers
"""

import os
import json
import asyncio
from datetime import datetime
from azure.cosmos.aio import CosmosClient
from azure.identity.aio import DefaultAzureCredential
from azure.keyvault.secrets.aio import SecretClient
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CosmosSchemaManager:
    def __init__(self):
        self.config = {
            "database_name": "StratOSData",
            "container_name": "CEOLogs",
            "key_vault_name": "stratos-keyvault"
        }
        self.client = None
        self.database = None
        self.container = None
    
    async def initialize(self):
        """Initialize Cosmos DB connection"""
        try:
            # Get credentials from Key Vault
            credential = DefaultAzureCredential()
            keyvault_url = f"https://{self.config['key_vault_name']}.vault.azure.net"
            
            async with SecretClient(vault_url=keyvault_url, credential=credential) as secret_client:
                endpoint_secret = await secret_client.get_secret("cosmos-db-endpoint")
                endpoint = endpoint_secret.value
            
            # Initialize Cosmos client with Azure AD auth
            self.client = CosmosClient(endpoint, credential=credential)
            self.database = self.client.get_database_client(self.config['database_name'])
            self.container = self.database.get_container_client(self.config['container_name'])
            
            logger.info("✅ Connected to Cosmos DB")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Cosmos DB: {e}")
            raise
    
    async def create_stored_procedures(self):
        """Create stored procedures for complex operations"""
        logger.info("\n📝 Creating Stored Procedures...")
        
        stored_procedures = [
            {
                "id": "bulkCreateLogs",
                "body": """
function bulkCreateLogs(logs) {
    var context = getContext();
    var collection = context.getCollection();
    var response = context.getResponse();
    var created = 0;
    var errors = [];
    
    if (!logs || !logs.length) {
        response.setBody({ created: 0, errors: ["No logs provided"] });
        return;
    }
    
    // Process each log
    for (var i = 0; i < logs.length; i++) {
        var log = logs[i];
        
        // Add server-side timestamp
        log.createdAt = new Date().toISOString();
        log.modifiedAt = log.createdAt;
        
        // Validate required fields
        if (!log.userId || !log.logEntry || !log.logEntry.content) {
            errors.push({ index: i, error: "Missing required fields" });
            continue;
        }
        
        // Create document
        var accepted = collection.createDocument(
            collection.getSelfLink(),
            log,
            function(err, doc) {
                if (err) {
                    errors.push({ index: i, error: err.message });
                } else {
                    created++;
                }
            }
        );
        
        if (!accepted) {
            errors.push({ index: i, error: "Rate limit exceeded" });
            break;
        }
    }
    
    response.setBody({
        created: created,
        total: logs.length,
        errors: errors
    });
}
"""
            },
            {
                "id": "getLogsSummary",
                "body": """
function getLogsSummary(userId, days) {
    var context = getContext();
    var collection = context.getCollection();
    var response = context.getResponse();
    
    var cutoffDate = new Date();
    cutoffDate.setDate(cutoffDate.getDate() - (days || 30));
    var cutoffISO = cutoffDate.toISOString();
    
    var query = {
        query: "SELECT c.timestamp, c.logEntry.sentiment, c.tags, c.strategicThemes FROM c WHERE c.userId = @userId AND c.timestamp >= @cutoff",
        parameters: [
            { name: "@userId", value: userId },
            { name: "@cutoff", value: cutoffISO }
        ]
    };
    
    var summary = {
        totalLogs: 0,
        sentimentCounts: { positive: 0, negative: 0, neutral: 0 },
        topTags: {},
        topThemes: {},
        dailyCounts: {}
    };
    
    var accepted = collection.queryDocuments(
        collection.getSelfLink(),
        query,
        function(err, docs) {
            if (err) {
                throw err;
            }
            
            docs.forEach(function(doc) {
                summary.totalLogs++;
                
                // Count sentiment
                var sentiment = doc.logEntry.sentiment || "neutral";
                summary.sentimentCounts[sentiment]++;
                
                // Count tags
                if (doc.tags) {
                    doc.tags.forEach(function(tag) {
                        summary.topTags[tag] = (summary.topTags[tag] || 0) + 1;
                    });
                }
                
                // Count themes
                if (doc.strategicThemes) {
                    doc.strategicThemes.forEach(function(theme) {
                        summary.topThemes[theme] = (summary.topThemes[theme] || 0) + 1;
                    });
                }
                
                // Daily counts
                var date = doc.timestamp.substring(0, 10);
                summary.dailyCounts[date] = (summary.dailyCounts[date] || 0) + 1;
            });
            
            // Sort and limit top items
            summary.topTags = Object.entries(summary.topTags)
                .sort((a, b) => b[1] - a[1])
                .slice(0, 10)
                .reduce((obj, [key, val]) => ({ ...obj, [key]: val }), {});
            
            summary.topThemes = Object.entries(summary.topThemes)
                .sort((a, b) => b[1] - a[1])
                .slice(0, 10)
                .reduce((obj, [key, val]) => ({ ...obj, [key]: val }), {});
            
            response.setBody(summary);
        }
    );
    
    if (!accepted) {
        throw new Error("Query was not accepted");
    }
}
"""
            },
            {
                "id": "searchLogsWithHighlights",
                "body": """
function searchLogsWithHighlights(userId, searchTerm, limit) {
    var context = getContext();
    var collection = context.getCollection();
    var response = context.getResponse();
    
    var query = {
        query: "SELECT TOP @limit c.id, c.timestamp, c.logEntry, c.tags FROM c WHERE c.userId = @userId AND CONTAINS(LOWER(c.logEntry.content), LOWER(@search)) ORDER BY c.timestamp DESC",
        parameters: [
            { name: "@limit", value: limit || 50 },
            { name: "@userId", value: userId },
            { name: "@search", value: searchTerm }
        ]
    };
    
    var results = [];
    
    var accepted = collection.queryDocuments(
        collection.getSelfLink(),
        query,
        function(err, docs) {
            if (err) {
                throw err;
            }
            
            docs.forEach(function(doc) {
                // Highlight search term in content
                var content = doc.logEntry.content;
                var regex = new RegExp("(" + searchTerm + ")", "gi");
                var highlighted = content.replace(regex, "<mark>$1</mark>");
                
                results.push({
                    id: doc.id,
                    timestamp: doc.timestamp,
                    content: doc.logEntry.content,
                    highlightedContent: highlighted,
                    snippet: getSnippet(content, searchTerm, 150),
                    tags: doc.tags || []
                });
            });
            
            response.setBody({
                searchTerm: searchTerm,
                resultCount: results.length,
                results: results
            });
        }
    );
    
    if (!accepted) {
        throw new Error("Query was not accepted");
    }
    
    function getSnippet(content, term, length) {
        var index = content.toLowerCase().indexOf(term.toLowerCase());
        if (index === -1) return content.substring(0, length) + "...";
        
        var start = Math.max(0, index - 50);
        var end = Math.min(content.length, index + term.length + 100);
        
        var snippet = content.substring(start, end);
        if (start > 0) snippet = "..." + snippet;
        if (end < content.length) snippet = snippet + "...";
        
        return snippet;
    }
}
"""
            },
            {
                "id": "aggregateStrategicInsights",
                "body": """
function aggregateStrategicInsights(userId, startDate, endDate) {
    var context = getContext();
    var collection = context.getCollection();
    var response = context.getResponse();
    
    var query = {
        query: "SELECT c.analysis, c.strategicThemes, c.logEntry.sentiment FROM c WHERE c.userId = @userId AND c.timestamp >= @start AND c.timestamp <= @end",
        parameters: [
            { name: "@userId", value: userId },
            { name: "@start", value: startDate },
            { name: "@end", value: endDate }
        ]
    };
    
    var insights = {
        keyInsights: {},
        actionItems: {},
        riskFactors: {},
        sentimentTrend: [],
        themeEvolution: {}
    };
    
    var accepted = collection.queryDocuments(
        collection.getSelfLink(),
        query,
        function(err, docs) {
            if (err) {
                throw err;
            }
            
            docs.forEach(function(doc) {
                // Aggregate insights
                if (doc.analysis) {
                    if (doc.analysis.keyInsights) {
                        doc.analysis.keyInsights.forEach(function(insight) {
                            insights.keyInsights[insight] = (insights.keyInsights[insight] || 0) + 1;
                        });
                    }
                    
                    if (doc.analysis.actionItems) {
                        doc.analysis.actionItems.forEach(function(item) {
                            insights.actionItems[item] = (insights.actionItems[item] || 0) + 1;
                        });
                    }
                    
                    if (doc.analysis.riskFactors) {
                        doc.analysis.riskFactors.forEach(function(risk) {
                            insights.riskFactors[risk] = (insights.riskFactors[risk] || 0) + 1;
                        });
                    }
                }
            });
            
            // Sort by frequency
            insights.keyInsights = sortObject(insights.keyInsights, 10);
            insights.actionItems = sortObject(insights.actionItems, 10);
            insights.riskFactors = sortObject(insights.riskFactors, 5);
            
            response.setBody(insights);
        }
    );
    
    if (!accepted) {
        throw new Error("Query was not accepted");
    }
    
    function sortObject(obj, limit) {
        return Object.entries(obj)
            .sort((a, b) => b[1] - a[1])
            .slice(0, limit)
            .map(([key, count]) => ({ text: key, count: count }));
    }
}
"""
            }
        ]
        
        # Create each stored procedure
        for sp in stored_procedures:
            try:
                # Check if exists
                try:
                    existing = await self.container.scripts.get_stored_procedure(sp['id'])
                    logger.info(f"  ℹ️  Stored procedure '{sp['id']}' already exists")
                    
                    # Replace if exists
                    await self.container.scripts.replace_stored_procedure(
                        sp['id'],
                        body=sp['body']
                    )
                    logger.info(f"  ✅ Updated stored procedure: {sp['id']}")
                except:
                    # Create new
                    await self.container.scripts.create_stored_procedure(body=sp)
                    logger.info(f"  ✅ Created stored procedure: {sp['id']}")
                    
            except Exception as e:
                logger.error(f"  ❌ Error with stored procedure '{sp['id']}': {e}")
    
    async def create_triggers(self):
        """Create pre and post triggers"""
        logger.info("\n🔧 Creating Triggers...")
        
        triggers = [
            {
                "id": "validateLogEntry",
                "body": """
function validateLogEntry() {
    var context = getContext();
    var request = context.getRequest();
    var doc = request.getBody();
    
    // Validation rules
    if (!doc.userId) {
        throw new Error("userId is required");
    }
    
    if (!doc.logEntry || !doc.logEntry.content) {
        throw new Error("logEntry.content is required");
    }
    
    if (doc.logEntry.content.length > 5000) {
        throw new Error("logEntry.content cannot exceed 5000 characters");
    }
    
    // Set defaults
    if (!doc.timestamp) {
        doc.timestamp = new Date().toISOString();
    }
    
    if (!doc.logEntry.sentiment) {
        doc.logEntry.sentiment = "neutral";
    }
    
    if (!doc.tags) {
        doc.tags = [];
    }
    
    if (!doc.strategicThemes) {
        doc.strategicThemes = [];
    }
    
    // Ensure arrays
    if (!Array.isArray(doc.tags)) {
        doc.tags = [doc.tags];
    }
    
    if (!Array.isArray(doc.strategicThemes)) {
        doc.strategicThemes = [doc.strategicThemes];
    }
    
    // Update request
    request.setBody(doc);
}
""",
                "triggerType": "Pre",
                "triggerOperation": "Create"
            },
            {
                "id": "updateModifiedTime",
                "body": """
function updateModifiedTime() {
    var context = getContext();
    var request = context.getRequest();
    var doc = request.getBody();
    
    // Update modified timestamp
    doc.modifiedAt = new Date().toISOString();
    
    // Track version
    doc.version = (doc.version || 0) + 1;
    
    request.setBody(doc);
}
""",
                "triggerType": "Pre",
                "triggerOperation": "Replace"
            }
        ]
        
        # Create each trigger
        for trigger in triggers:
            try:
                # Check if exists
                try:
                    existing = await self.container.scripts.get_trigger(trigger['id'])
                    logger.info(f"  ℹ️  Trigger '{trigger['id']}' already exists")
                    
                    # Replace if exists
                    await self.container.scripts.replace_trigger(
                        trigger['id'],
                        body=trigger['body'],
                        trigger_type=trigger['triggerType'],
                        trigger_operation=trigger['triggerOperation']
                    )
                    logger.info(f"  ✅ Updated trigger: {trigger['id']}")
                except:
                    # Create new
                    await self.container.scripts.create_trigger(
                        body=trigger
                    )
                    logger.info(f"  ✅ Created trigger: {trigger['id']}")
                    
            except Exception as e:
                logger.error(f"  ❌ Error with trigger '{trigger['id']}': {e}")
    
    async def create_sample_documents(self):
        """Create sample CEO log documents for testing"""
        logger.info("\n📄 Creating Sample Documents...")
        
        sample_logs = [
            {
                "userId": "sample-user",
                "timestamp": "2025-05-28T10:00:00Z",
                "logEntry": {
                    "content": "Had an excellent meeting with the engineering team about our AI integration strategy. The team demonstrated strong alignment on the technical roadmap, and we identified key milestones for Q3. Need to allocate additional resources for the machine learning infrastructure.",
                    "sentiment": "positive",
                    "confidence": 0.92
                },
                "tags": ["team-meeting", "ai-strategy", "engineering", "q3-planning"],
                "strategicThemes": ["ai-transformation", "team-alignment", "resource-planning"],
                "metadata": {
                    "source": "voice-note",
                    "duration": 180,
                    "location": "conference-room-a"
                },
                "analysis": {
                    "keyInsights": [
                        "Strong team alignment on AI roadmap",
                        "Q3 milestones clearly defined"
                    ],
                    "actionItems": [
                        "Allocate ML infrastructure budget",
                        "Schedule follow-up with engineering leads"
                    ],
                    "riskFactors": ["Resource constraints for ML infrastructure"]
                }
            },
            {
                "userId": "sample-user",
                "timestamp": "2025-05-27T15:30:00Z",
                "logEntry": {
                    "content": "Customer feedback session revealed strong demand for predictive analytics features. Several enterprise clients expressed willingness to participate in beta testing. This validates our strategic pivot towards AI-powered insights.",
                    "sentiment": "positive",
                    "confidence": 0.88
                },
                "tags": ["customer-feedback", "product-strategy", "beta-testing", "analytics"],
                "strategicThemes": ["customer-focus", "product-innovation", "market-validation"],
                "metadata": {
                    "source": "meeting-notes",
                    "attendees": 12,
                    "followUpRequired": True
                },
                "analysis": {
                    "keyInsights": [
                        "Strong market demand for predictive analytics",
                        "Enterprise clients ready for beta participation"
                    ],
                    "actionItems": [
                        "Prepare beta testing framework",
                        "Identify beta client selection criteria"
                    ],
                    "riskFactors": []
                }
            },
            {
                "userId": "sample-user",
                "timestamp": "2025-05-26T09:15:00Z",
                "logEntry": {
                    "content": "Concerns about competitive pressure in the AI space. Need to accelerate our time to market while maintaining quality standards. Considering strategic partnerships to enhance our capabilities.",
                    "sentiment": "negative",
                    "confidence": 0.75
                },
                "tags": ["competition", "strategy", "partnerships", "time-to-market"],
                "strategicThemes": ["competitive-analysis", "strategic-partnerships", "acceleration"],
                "metadata": {
                    "source": "reflection",
                    "priority": "high"
                },
                "analysis": {
                    "keyInsights": [
                        "Competitive pressure increasing in AI market",
                        "Time to market is critical factor"
                    ],
                    "actionItems": [
                        "Evaluate potential strategic partners",
                        "Review and optimize development timeline"
                    ],
                    "riskFactors": [
                        "Competitive disadvantage if delayed",
                        "Quality risks from acceleration"
                    ]
                }
            }
        ]
        
        # Create sample documents
        created = 0
        for log in sample_logs:
            try:
                # Add ID and timestamps
                log['id'] = f"sample-{created + 1}"
                log['createdAt'] = datetime.utcnow().isoformat()
                log['modifiedAt'] = log['createdAt']
                log['createdBy'] = "SampleDataGenerator"
                
                # Create document
                await self.container.create_item(body=log)
                created += 1
                logger.info(f"  ✅ Created sample log: {log['id']}")
                
            except Exception as e:
                if "Conflict" in str(e):
                    logger.info(f"  ℹ️  Sample log already exists: {log['id']}")
                else:
                    logger.error(f"  ❌ Error creating sample log: {e}")
        
        logger.info(f"\n  Created {created} sample documents")
    
    def generate_schema_documentation(self):
        """Generate schema documentation"""
        logger.info("\n📚 Generating Schema Documentation...")
        
        schema_doc = {
            "schemaVersion": "1.0",
            "lastUpdated": datetime.utcnow().isoformat(),
            "container": {
                "name": "CEOLogs",
                "partitionKey": "/userId",
                "uniqueKeys": [],
                "defaultTTL": -1
            },
            "documentSchema": {
                "id": {
                    "type": "string",
                    "description": "Unique identifier for the log entry",
                    "required": True
                },
                "userId": {
                    "type": "string",
                    "description": "User identifier (partition key)",
                    "required": True
                },
                "timestamp": {
                    "type": "string",
                    "format": "ISO 8601",
                    "description": "When the log entry was created",
                    "required": True
                },
                "logEntry": {
                    "type": "object",
                    "required": True,
                    "properties": {
                        "content": {
                            "type": "string",
                            "maxLength": 5000,
                            "description": "The actual log content",
                            "required": True
                        },
                        "sentiment": {
                            "type": "string",
                            "enum": ["positive", "negative", "neutral"],
                            "default": "neutral"
                        },
                        "confidence": {
                            "type": "number",
                            "minimum": 0,
                            "maximum": 1,
                            "description": "Confidence score for sentiment analysis"
                        }
                    }
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "User-defined tags for categorization"
                },
                "strategicThemes": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "AI-identified strategic themes"
                },
                "metadata": {
                    "type": "object",
                    "description": "Additional metadata about the log entry"
                },
                "analysis": {
                    "type": "object",
                    "properties": {
                        "keyInsights": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "actionItems": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "riskFactors": {
                            "type": "array",
                            "items": {"type": "string"}
                        }
                    }
                },
                "createdBy": {
                    "type": "string",
                    "default": "CEOLogAgent"
                },
                "createdAt": {
                    "type": "string",
                    "format": "ISO 8601",
                    "description": "Server timestamp when created"
                },
                "modifiedAt": {
                    "type": "string",
                    "format": "ISO 8601",
                    "description": "Server timestamp when last modified"
                },
                "version": {
                    "type": "integer",
                    "description": "Document version number"
                }
            },
            "storedProcedures": [
                {
                    "name": "bulkCreateLogs",
                    "description": "Bulk create multiple log entries",
                    "parameters": ["logs: Array<LogEntry>"],
                    "returns": "{ created: number, errors: Array }"
                },
                {
                    "name": "getLogsSummary",
                    "description": "Get summary statistics for user's logs",
                    "parameters": ["userId: string", "days: number"],
                    "returns": "{ totalLogs, sentimentCounts, topTags, topThemes, dailyCounts }"
                },
                {
                    "name": "searchLogsWithHighlights",
                    "description": "Search logs with highlighted results",
                    "parameters": ["userId: string", "searchTerm: string", "limit: number"],
                    "returns": "{ searchTerm, resultCount, results: Array }"
                },
                {
                    "name": "aggregateStrategicInsights",
                    "description": "Aggregate strategic insights over time period",
                    "parameters": ["userId: string", "startDate: string", "endDate: string"],
                    "returns": "{ keyInsights, actionItems, riskFactors, sentimentTrend, themeEvolution }"
                }
            ],
            "triggers": [
                {
                    "name": "validateLogEntry",
                    "type": "Pre",
                    "operation": "Create",
                    "description": "Validates and normalizes log entries before creation"
                },
                {
                    "name": "updateModifiedTime",
                    "type": "Pre",
                    "operation": "Replace",
                    "description": "Updates modification timestamp and version"
                }
            ],
            "indexes": [
                {
                    "kind": "Range",
                    "paths": ["/timestamp/?", "/userId/?"]
                },
                {
                    "kind": "Composite",
                    "paths": [
                        {"path": "/timestamp", "order": "descending"},
                        {"path": "/userId", "order": "ascending"}
                    ]
                }
            ]
        }
        
        # Save schema documentation
        with open('ceo_log_schema_documentation.json', 'w') as f:
            json.dump(schema_doc, f, indent=2)
        
        logger.info("  ✅ Schema documentation saved to ceo_log_schema_documentation.json")
        
        # Generate markdown documentation
        md_content = f"""# CEO Log Cosmos DB Schema Documentation

Generated: {datetime.utcnow().isoformat()}

## Container Configuration
- **Name**: {schema_doc['container']['name']}
- **Partition Key**: {schema_doc['container']['partitionKey']}
- **Default TTL**: {schema_doc['container']['defaultTTL']} (no expiration)

## Document Schema

### Required Fields
- `id` (string): Unique identifier
- `userId` (string): User identifier (partition key)
- `timestamp` (ISO 8601): Creation timestamp
- `logEntry.content` (string): Log content (max 5000 chars)

### Optional Fields
- `tags` (array): User-defined tags
- `strategicThemes` (array): AI-identified themes
- `metadata` (object): Additional metadata
- `analysis` (object): AI-generated insights

## Stored Procedures

### bulkCreateLogs
Bulk create multiple log entries with validation.
- **Parameters**: Array of log entries
- **Returns**: Creation summary with error details

### getLogsSummary
Generate summary statistics for a user's logs.
- **Parameters**: userId, days (lookback period)
- **Returns**: Comprehensive statistics object

### searchLogsWithHighlights
Full-text search with result highlighting.
- **Parameters**: userId, searchTerm, limit
- **Returns**: Search results with snippets

### aggregateStrategicInsights
Aggregate insights over a time period.
- **Parameters**: userId, startDate, endDate
- **Returns**: Aggregated insights and trends

## Triggers

### validateLogEntry (Pre-Create)
- Validates required fields
- Sets default values
- Ensures data consistency

### updateModifiedTime (Pre-Replace)
- Updates modification timestamp
- Increments version number

## Query Examples

```sql
-- Get recent logs for a user
SELECT * FROM c 
WHERE c.userId = 'user123' 
  AND c.timestamp >= '2025-05-01T00:00:00Z'
ORDER BY c.timestamp DESC

-- Search logs by content
SELECT * FROM c 
WHERE c.userId = 'user123' 
  AND CONTAINS(c.logEntry.content, 'AI strategy')

-- Get logs by strategic theme
SELECT * FROM c 
WHERE c.userId = 'user123' 
  AND ARRAY_CONTAINS(c.strategicThemes, 'ai-transformation')
```
"""
        
        with open('CEO_LOG_SCHEMA_README.md', 'w') as f:
            f.write(md_content)
        
        logger.info("  ✅ Schema README saved to CEO_LOG_SCHEMA_README.md")
    
    async def run(self):
        """Execute all schema creation steps"""
        try:
            await self.initialize()
            await self.create_stored_procedures()
            await self.create_triggers()
            await self.create_sample_documents()
            self.generate_schema_documentation()
            
            logger.info("\n✅ SCHEMA SETUP COMPLETE!")
            logger.info("All stored procedures, triggers, and sample data created.")
            
        except Exception as e:
            logger.error(f"\n❌ Schema setup failed: {e}")
            raise
        finally:
            if self.client:
                await self.client.close()

if __name__ == "__main__":
    manager = CosmosSchemaManager()
    asyncio.run(manager.run())