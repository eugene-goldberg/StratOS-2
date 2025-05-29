# CEO Log Agent Cosmos DB Integration Plan

## Executive Summary
This plan outlines the complete implementation strategy for enabling the CEO Log connected agent to read and write data to Azure Cosmos DB. The integration will allow persistent storage of CEO log entries, enabling historical analysis, pattern recognition, and strategic insights.

## Architecture Overview

### Current State
- CEO Log Agent is deployed as a connected agent in Azure AI Agent Service
- Agent receives delegated queries from the orchestrator
- Currently operates without persistent storage

### Target State
- CEO Log Agent will store all log entries in Cosmos DB
- Support CRUD operations (Create, Read, Update, Delete)
- Enable querying by date, tags, sentiment, and strategic themes
- Maintain audit trail of all CEO communications

## Phase 1: Cosmos DB Infrastructure Setup

### 1.1 Provision Cosmos DB Account
**Task**: Create Cosmos DB account in Azure
```bash
# Azure CLI commands
az cosmosdb create \
  --name stratos-ceo-logs-db \
  --resource-group semantic-kernel-multi-agent-rg \
  --locations regionName=eastus failoverPriority=0 \
  --default-consistency-level Session \
  --enable-free-tier false
```

**Configuration Details**:
- API: Core (SQL)
- Consistency Level: Session (balance between consistency and performance)
- Region: East US (same as AI Agent Service)
- Throughput: Start with 400 RU/s (can scale as needed)

### 1.2 Create Database and Container
**Task**: Set up database structure
```bash
# Create database
az cosmosdb sql database create \
  --account-name stratos-ceo-logs-db \
  --resource-group semantic-kernel-multi-agent-rg \
  --name StratOSData

# Create container for CEO logs
az cosmosdb sql container create \
  --account-name stratos-ceo-logs-db \
  --resource-group semantic-kernel-multi-agent-rg \
  --database-name StratOSData \
  --name CEOLogs \
  --partition-key-path /userId \
  --throughput 400
```

**Container Schema**:
```json
{
  "id": "unique-guid",
  "userId": "user-identifier",
  "timestamp": "2025-05-28T20:30:00Z",
  "logEntry": {
    "content": "Team meeting went well. Discussed Q2 roadmap and AI strategy.",
    "sentiment": "positive",
    "confidence": 0.85
  },
  "tags": ["team-meeting", "roadmap", "ai-strategy", "q2-planning"],
  "strategicThemes": ["ai-transformation", "team-alignment"],
  "metadata": {
    "source": "voice-input",
    "duration": 45,
    "location": "headquarters"
  },
  "analysis": {
    "keyInsights": ["Strong team alignment on AI strategy"],
    "actionItems": ["Review Q2 milestones", "Schedule AI training"],
    "riskFactors": []
  },
  "createdBy": "CEOLogAgent",
  "createdAt": "2025-05-28T20:30:00Z",
  "modifiedAt": "2025-05-28T20:30:00Z",
  "_etag": "cosmos-db-etag"
}
```

### 1.3 Configure Access and Security
**Task**: Set up secure access
1. Enable Azure AD authentication
2. Create service principal for CEO Log Agent
3. Assign Cosmos DB Data Contributor role
4. Store connection string in Key Vault

```bash
# Get connection string
az cosmosdb keys list \
  --name stratos-ceo-logs-db \
  --resource-group semantic-kernel-multi-agent-rg \
  --type connection-strings

# Store in Key Vault
az keyvault secret set \
  --vault-name stratos-keyvault \
  --name cosmos-db-connection-string \
  --value "<connection-string>"
```

## Phase 2: Code Dependencies and Setup

### 2.1 Add Required Dependencies
**File**: `/backend/agentic/connected_agents/stratos/requirements.txt`
```txt
# Existing dependencies...

# Cosmos DB SDK
azure-cosmos>=4.5.1
azure-identity>=1.16.0
azure-keyvault-secrets>=4.8.0

# Data validation and serialization
pydantic>=2.6.0
python-dateutil>=2.9.0

# Async support
aiohttp>=3.9.0
```

### 2.2 Create Cosmos DB Client Module
**File**: `/backend/agentic/connected_agents/stratos/services/cosmos_db_service.py`
```python
"""
Cosmos DB Service for CEO Log Agent
Handles all database operations with async support
"""

import os
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
from uuid import uuid4

from azure.cosmos.aio import CosmosClient
from azure.cosmos import exceptions
from azure.identity.aio import DefaultAzureCredential
from azure.keyvault.secrets.aio import SecretClient
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)

class CEOLogEntry(BaseModel):
    """Data model for CEO log entries"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    userId: str
    timestamp: datetime
    logEntry: Dict[str, Any]
    tags: List[str] = []
    strategicThemes: List[str] = []
    metadata: Dict[str, Any] = {}
    analysis: Dict[str, Any] = {}
    createdBy: str = "CEOLogAgent"
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    modifiedAt: datetime = Field(default_factory=datetime.utcnow)

class CosmosDBService:
    """Service for interacting with Cosmos DB"""
    
    def __init__(self):
        self.client = None
        self.database = None
        self.container = None
        self.initialized = False
        
    async def initialize(self):
        """Initialize Cosmos DB connection"""
        if self.initialized:
            return
            
        try:
            # Get connection string from Key Vault
            credential = DefaultAzureCredential()
            keyvault_url = os.getenv("AZURE_KEYVAULT_URL")
            
            async with SecretClient(
                vault_url=keyvault_url,
                credential=credential
            ) as secret_client:
                secret = await secret_client.get_secret("cosmos-db-connection-string")
                connection_string = secret.value
            
            # Initialize Cosmos client
            self.client = CosmosClient.from_connection_string(
                connection_string,
                credential=credential
            )
            
            # Get database and container references
            self.database = self.client.get_database_client("StratOSData")
            self.container = self.database.get_container_client("CEOLogs")
            
            self.initialized = True
            logger.info("Cosmos DB service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Cosmos DB: {e}")
            raise
    
    async def create_log_entry(self, log_data: Dict[str, Any]) -> CEOLogEntry:
        """Create a new CEO log entry"""
        await self.initialize()
        
        try:
            # Create log entry model
            log_entry = CEOLogEntry(**log_data)
            
            # Insert into Cosmos DB
            response = await self.container.create_item(
                body=log_entry.model_dump()
            )
            
            logger.info(f"Created log entry: {log_entry.id}")
            return log_entry
            
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"Cosmos DB error creating log: {e}")
            raise
    
    async def get_log_entries(
        self,
        user_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        tags: Optional[List[str]] = None,
        limit: int = 100
    ) -> List[CEOLogEntry]:
        """Retrieve CEO log entries with filters"""
        await self.initialize()
        
        try:
            # Build query
            query = "SELECT * FROM c WHERE c.userId = @userId"
            parameters = [{"name": "@userId", "value": user_id}]
            
            if start_date:
                query += " AND c.timestamp >= @startDate"
                parameters.append({
                    "name": "@startDate",
                    "value": start_date.isoformat()
                })
            
            if end_date:
                query += " AND c.timestamp <= @endDate"
                parameters.append({
                    "name": "@endDate",
                    "value": end_date.isoformat()
                })
            
            if tags:
                query += " AND ARRAY_CONTAINS(c.tags, @tag)"
                parameters.append({"name": "@tag", "value": tags[0]})
            
            query += " ORDER BY c.timestamp DESC"
            query += f" OFFSET 0 LIMIT {limit}"
            
            # Execute query
            items = []
            async for item in self.container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True
            ):
                items.append(CEOLogEntry(**item))
            
            logger.info(f"Retrieved {len(items)} log entries")
            return items
            
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"Cosmos DB error retrieving logs: {e}")
            raise
    
    async def update_log_entry(
        self,
        log_id: str,
        user_id: str,
        updates: Dict[str, Any]
    ) -> CEOLogEntry:
        """Update an existing log entry"""
        await self.initialize()
        
        try:
            # Get existing item
            existing = await self.container.read_item(
                item=log_id,
                partition_key=user_id
            )
            
            # Apply updates
            for key, value in updates.items():
                if key not in ["id", "userId", "createdAt", "createdBy"]:
                    existing[key] = value
            
            existing["modifiedAt"] = datetime.utcnow().isoformat()
            
            # Update in Cosmos DB
            response = await self.container.replace_item(
                item=log_id,
                body=existing
            )
            
            logger.info(f"Updated log entry: {log_id}")
            return CEOLogEntry(**response)
            
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"Cosmos DB error updating log: {e}")
            raise
    
    async def delete_log_entry(self, log_id: str, user_id: str) -> bool:
        """Delete a log entry"""
        await self.initialize()
        
        try:
            await self.container.delete_item(
                item=log_id,
                partition_key=user_id
            )
            
            logger.info(f"Deleted log entry: {log_id}")
            return True
            
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"Cosmos DB error deleting log: {e}")
            raise
    
    async def search_logs_by_content(
        self,
        user_id: str,
        search_term: str,
        limit: int = 50
    ) -> List[CEOLogEntry]:
        """Search logs by content"""
        await self.initialize()
        
        try:
            query = """
            SELECT * FROM c 
            WHERE c.userId = @userId 
            AND CONTAINS(LOWER(c.logEntry.content), LOWER(@searchTerm))
            ORDER BY c.timestamp DESC
            """
            
            parameters = [
                {"name": "@userId", "value": user_id},
                {"name": "@searchTerm", "value": search_term}
            ]
            
            items = []
            async for item in self.container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True,
                max_item_count=limit
            ):
                items.append(CEOLogEntry(**item))
            
            logger.info(f"Found {len(items)} logs matching '{search_term}'")
            return items
            
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"Cosmos DB error searching logs: {e}")
            raise
    
    async def get_strategic_themes_summary(
        self,
        user_id: str,
        days: int = 30
    ) -> Dict[str, int]:
        """Get summary of strategic themes over time period"""
        await self.initialize()
        
        try:
            # Calculate date range
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            query = """
            SELECT VALUE c.strategicThemes
            FROM c 
            WHERE c.userId = @userId 
            AND c.timestamp >= @startDate
            """
            
            parameters = [
                {"name": "@userId", "value": user_id},
                {"name": "@startDate", "value": start_date.isoformat()}
            ]
            
            # Count themes
            theme_counts = {}
            async for themes in self.container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True
            ):
                for theme in themes:
                    theme_counts[theme] = theme_counts.get(theme, 0) + 1
            
            logger.info(f"Analyzed {len(theme_counts)} strategic themes")
            return dict(sorted(
                theme_counts.items(),
                key=lambda x: x[1],
                reverse=True
            ))
            
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"Cosmos DB error analyzing themes: {e}")
            raise
    
    async def close(self):
        """Close Cosmos DB connection"""
        if self.client:
            await self.client.close()
            self.initialized = False
            logger.info("Cosmos DB connection closed")

# Singleton instance
cosmos_service = CosmosDBService()
```

## Phase 3: CEO Log Agent Integration

### 3.1 Update CEO Log Agent Configuration
**File**: `/backend/agentic/connected_agents/stratos/agents/ceo_log_agent_config.py`
```python
# Add to existing configuration

# Cosmos DB settings
COSMOS_DB_ENABLED = True
COSMOS_DB_CONTAINER = "CEOLogs"
COSMOS_DB_DATABASE = "StratOSData"

# Update agent instructions to mention persistence
AGENT_INSTRUCTIONS = """You are the CEO Log Agent for StratOS, responsible for capturing, analyzing, and managing strategic CEO communications and insights.

IMPORTANT: All log entries are automatically persisted to the database for historical analysis and pattern recognition.

Core Functions:
1. Create and store CEO log entries with strategic insights
2. Retrieve historical logs based on date, tags, or content
3. Analyze patterns and themes across log entries
4. Generate summaries and extract action items

When processing requests:
- For new logs: Extract content, sentiment, tags, and strategic themes before storing
- For queries: Search the database and provide relevant historical context
- For analysis: Aggregate data to identify patterns and trends

Database Operations:
- CREATE: Store new log entries with full metadata
- READ: Retrieve logs by date range, tags, or search terms
- UPDATE: Modify existing logs with new insights
- DELETE: Remove logs (with audit trail)
- ANALYZE: Generate strategic summaries and trend analysis

Always confirm successful database operations in your response.
"""
```

### 3.2 Enhance CEO Log Plugin with Cosmos DB
**File**: `/backend/agentic/connected_agents/stratos/agents/ceo_log_plugin_enhanced.py`
```python
"""
Enhanced CEO Log Plugin with Cosmos DB Integration
"""

import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from semantic_kernel.skill_definition import (
    sk_function,
    sk_function_context_parameter
)
from semantic_kernel.orchestration.sk_context import SKContext

from ..services.cosmos_db_service import cosmos_service, CEOLogEntry

logger = logging.getLogger(__name__)

class CEOLogPlugin:
    """CEO Log plugin with Cosmos DB persistence"""
    
    def __init__(self):
        self.name = "CEOLogPlugin"
        self.description = "Manages CEO strategic logs with database persistence"
    
    @sk_function(
        description="Create and store a new CEO log entry",
        name="create_log_entry"
    )
    @sk_function_context_parameter(
        name="content",
        description="The CEO log content to store"
    )
    @sk_function_context_parameter(
        name="tags",
        description="Comma-separated tags for the log entry"
    )
    @sk_function_context_parameter(
        name="sentiment",
        description="Sentiment of the log (positive/negative/neutral)"
    )
    async def create_log_entry(self, context: SKContext) -> str:
        """Create and persist a new CEO log entry"""
        try:
            content = context.variables.get("content", "")
            tags = context.variables.get("tags", "").split(",") if context.variables.get("tags") else []
            sentiment = context.variables.get("sentiment", "neutral")
            user_id = context.variables.get("user_id", "default-user")
            
            # Extract strategic themes from content
            strategic_themes = self._extract_themes(content)
            
            # Prepare log entry
            log_data = {
                "userId": user_id,
                "timestamp": datetime.utcnow(),
                "logEntry": {
                    "content": content,
                    "sentiment": sentiment,
                    "confidence": 0.85
                },
                "tags": [tag.strip() for tag in tags],
                "strategicThemes": strategic_themes,
                "metadata": {
                    "source": "connected-agent",
                    "agentVersion": "1.0"
                },
                "analysis": {
                    "keyInsights": self._extract_insights(content),
                    "actionItems": self._extract_action_items(content)
                }
            }
            
            # Store in Cosmos DB
            log_entry = await cosmos_service.create_log_entry(log_data)
            
            return f"""✅ CEO Log Entry Created Successfully!

**Log ID**: {log_entry.id}
**Timestamp**: {log_entry.timestamp}
**Content**: {content}
**Tags**: {', '.join(log_entry.tags)}
**Strategic Themes**: {', '.join(log_entry.strategicThemes)}
**Sentiment**: {sentiment}

The log has been securely stored in the database for future analysis."""
            
        except Exception as e:
            logger.error(f"Error creating log entry: {e}")
            return f"❌ Error creating log entry: {str(e)}"
    
    @sk_function(
        description="Retrieve CEO log entries",
        name="get_log_entries"
    )
    @sk_function_context_parameter(
        name="days",
        description="Number of days to look back (default: 7)"
    )
    @sk_function_context_parameter(
        name="tags",
        description="Filter by specific tags (comma-separated)"
    )
    @sk_function_context_parameter(
        name="limit",
        description="Maximum number of entries to return"
    )
    async def get_log_entries(self, context: SKContext) -> str:
        """Retrieve CEO log entries from database"""
        try:
            user_id = context.variables.get("user_id", "default-user")
            days = int(context.variables.get("days", "7"))
            tags = context.variables.get("tags", "").split(",") if context.variables.get("tags") else None
            limit = int(context.variables.get("limit", "10"))
            
            # Calculate date range
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            # Retrieve from Cosmos DB
            logs = await cosmos_service.get_log_entries(
                user_id=user_id,
                start_date=start_date,
                end_date=end_date,
                tags=tags,
                limit=limit
            )
            
            if not logs:
                return "No CEO log entries found for the specified criteria."
            
            # Format response
            response = f"📋 **CEO Log Entries** (Last {days} days)\n\n"
            
            for log in logs:
                response += f"""**{log.timestamp.strftime('%Y-%m-%d %H:%M')}**
Content: {log.logEntry['content']}
Tags: {', '.join(log.tags)}
Themes: {', '.join(log.strategicThemes)}
Sentiment: {log.logEntry.get('sentiment', 'neutral')}
---
"""
            
            response += f"\nTotal entries: {len(logs)}"
            return response
            
        except Exception as e:
            logger.error(f"Error retrieving log entries: {e}")
            return f"❌ Error retrieving log entries: {str(e)}"
    
    @sk_function(
        description="Search CEO logs by content",
        name="search_logs"
    )
    @sk_function_context_parameter(
        name="search_term",
        description="Term to search for in log content"
    )
    @sk_function_context_parameter(
        name="limit",
        description="Maximum number of results"
    )
    async def search_logs(self, context: SKContext) -> str:
        """Search CEO logs by content"""
        try:
            user_id = context.variables.get("user_id", "default-user")
            search_term = context.variables.get("search_term", "")
            limit = int(context.variables.get("limit", "20"))
            
            if not search_term:
                return "Please provide a search term."
            
            # Search in Cosmos DB
            logs = await cosmos_service.search_logs_by_content(
                user_id=user_id,
                search_term=search_term,
                limit=limit
            )
            
            if not logs:
                return f"No CEO log entries found containing '{search_term}'."
            
            # Format response
            response = f"🔍 **Search Results** for '{search_term}'\n\n"
            
            for log in logs:
                # Highlight search term in content
                content = log.logEntry['content']
                highlighted = content.replace(
                    search_term,
                    f"**{search_term}**"
                )
                
                response += f"""**{log.timestamp.strftime('%Y-%m-%d')}**: {highlighted[:150]}...
Tags: {', '.join(log.tags[:3])}
---
"""
            
            response += f"\nFound {len(logs)} matching entries"
            return response
            
        except Exception as e:
            logger.error(f"Error searching logs: {e}")
            return f"❌ Error searching logs: {str(e)}"
    
    @sk_function(
        description="Analyze strategic themes from CEO logs",
        name="analyze_themes"
    )
    @sk_function_context_parameter(
        name="days",
        description="Number of days to analyze (default: 30)"
    )
    async def analyze_themes(self, context: SKContext) -> str:
        """Analyze strategic themes from CEO logs"""
        try:
            user_id = context.variables.get("user_id", "default-user")
            days = int(context.variables.get("days", "30"))
            
            # Get theme summary from Cosmos DB
            theme_summary = await cosmos_service.get_strategic_themes_summary(
                user_id=user_id,
                days=days
            )
            
            if not theme_summary:
                return f"No strategic themes found in the last {days} days."
            
            # Format response
            response = f"📊 **Strategic Themes Analysis** (Last {days} days)\n\n"
            
            # Top themes
            response += "**Most Frequent Themes:**\n"
            for theme, count in list(theme_summary.items())[:10]:
                bar = "█" * min(count, 20)
                response += f"{theme}: {bar} ({count})\n"
            
            # Theme insights
            response += "\n**Key Insights:**\n"
            if "ai-transformation" in theme_summary:
                response += "• Strong focus on AI transformation initiatives\n"
            if "team-alignment" in theme_summary:
                response += "• Emphasis on team alignment and collaboration\n"
            if "customer-focus" in theme_summary:
                response += "• Customer-centric strategic direction\n"
            
            return response
            
        except Exception as e:
            logger.error(f"Error analyzing themes: {e}")
            return f"❌ Error analyzing themes: {str(e)}"
    
    @sk_function(
        description="Generate a strategic summary from recent CEO logs",
        name="generate_summary"
    )
    @sk_function_context_parameter(
        name="days",
        description="Number of days to summarize (default: 7)"
    )
    async def generate_summary(self, context: SKContext) -> str:
        """Generate strategic summary from recent logs"""
        try:
            user_id = context.variables.get("user_id", "default-user")
            days = int(context.variables.get("days", "7"))
            
            # Get recent logs
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            logs = await cosmos_service.get_log_entries(
                user_id=user_id,
                start_date=start_date,
                end_date=end_date,
                limit=50
            )
            
            if not logs:
                return f"No CEO log entries found in the last {days} days."
            
            # Aggregate insights
            all_insights = []
            all_actions = []
            sentiment_counts = {"positive": 0, "negative": 0, "neutral": 0}
            
            for log in logs:
                if "analysis" in log.analysis:
                    all_insights.extend(log.analysis.get("keyInsights", []))
                    all_actions.extend(log.analysis.get("actionItems", []))
                sentiment = log.logEntry.get("sentiment", "neutral")
                sentiment_counts[sentiment] += 1
            
            # Format summary
            response = f"""📊 **CEO Strategic Summary** ({days}-Day Overview)

**Activity Summary:**
• Total log entries: {len(logs)}
• Positive sentiment: {sentiment_counts['positive']} ({sentiment_counts['positive']/len(logs)*100:.0f}%)
• Negative sentiment: {sentiment_counts['negative']} ({sentiment_counts['negative']/len(logs)*100:.0f}%)
• Neutral sentiment: {sentiment_counts['neutral']} ({sentiment_counts['neutral']/len(logs)*100:.0f}%)

**Key Strategic Insights:**
"""
            
            # Add top insights
            for insight in list(set(all_insights))[:5]:
                response += f"• {insight}\n"
            
            response += "\n**Priority Action Items:**\n"
            for action in list(set(all_actions))[:5]:
                response += f"• {action}\n"
            
            return response
            
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return f"❌ Error generating summary: {str(e)}"
    
    def _extract_themes(self, content: str) -> List[str]:
        """Extract strategic themes from content"""
        themes = []
        content_lower = content.lower()
        
        # Theme detection logic
        theme_keywords = {
            "ai-transformation": ["ai", "artificial intelligence", "machine learning", "automation"],
            "team-alignment": ["team", "collaboration", "alignment", "together"],
            "customer-focus": ["customer", "client", "user experience", "satisfaction"],
            "innovation": ["innovation", "innovative", "new approach", "breakthrough"],
            "growth": ["growth", "expansion", "scaling", "increase"],
            "efficiency": ["efficiency", "optimization", "streamline", "improve"],
            "digital-strategy": ["digital", "technology", "platform", "systems"]
        }
        
        for theme, keywords in theme_keywords.items():
            if any(keyword in content_lower for keyword in keywords):
                themes.append(theme)
        
        return themes[:5]  # Limit to 5 themes
    
    def _extract_insights(self, content: str) -> List[str]:
        """Extract key insights from content"""
        # Simple insight extraction - in production, use NLP
        insights = []
        
        sentences = content.split(".")
        for sentence in sentences:
            if any(word in sentence.lower() for word in ["important", "key", "critical", "success"]):
                insights.append(sentence.strip())
        
        return insights[:3]
    
    def _extract_action_items(self, content: str) -> List[str]:
        """Extract action items from content"""
        # Simple action item extraction
        actions = []
        
        action_keywords = ["need to", "should", "must", "will", "plan to", "going to"]
        sentences = content.split(".")
        
        for sentence in sentences:
            if any(keyword in sentence.lower() for keyword in action_keywords):
                actions.append(sentence.strip())
        
        return actions[:3]
```

## Phase 4: Testing Strategy

### 4.1 Unit Tests for Cosmos DB Service
**File**: `/backend/agentic/connected_agents/stratos/tests/test_cosmos_db_service.py`
```python
"""
Unit tests for Cosmos DB service
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock

from ..services.cosmos_db_service import CosmosDBService, CEOLogEntry

@pytest.fixture
async def cosmos_service():
    """Create test cosmos service instance"""
    service = CosmosDBService()
    # Mock the initialization
    service.initialized = True
    service.container = AsyncMock()
    return service

@pytest.mark.asyncio
async def test_create_log_entry(cosmos_service):
    """Test creating a log entry"""
    # Arrange
    test_data = {
        "userId": "test-user",
        "timestamp": datetime.utcnow(),
        "logEntry": {
            "content": "Test CEO log",
            "sentiment": "positive"
        },
        "tags": ["test", "unit-test"]
    }
    
    cosmos_service.container.create_item = AsyncMock(
        return_value={"id": "test-id", **test_data}
    )
    
    # Act
    result = await cosmos_service.create_log_entry(test_data)
    
    # Assert
    assert result.userId == "test-user"
    assert result.tags == ["test", "unit-test"]
    cosmos_service.container.create_item.assert_called_once()

@pytest.mark.asyncio
async def test_get_log_entries(cosmos_service):
    """Test retrieving log entries"""
    # Arrange
    mock_items = [
        {
            "id": "1",
            "userId": "test-user",
            "timestamp": datetime.utcnow().isoformat(),
            "logEntry": {"content": "Log 1"},
            "tags": ["tag1"]
        }
    ]
    
    cosmos_service.container.query_items = AsyncMock(
        return_value=AsyncIterator(mock_items)
    )
    
    # Act
    result = await cosmos_service.get_log_entries(
        user_id="test-user",
        limit=10
    )
    
    # Assert
    assert len(result) == 1
    assert result[0].id == "1"

@pytest.mark.asyncio
async def test_search_logs_by_content(cosmos_service):
    """Test searching logs by content"""
    # Arrange
    search_term = "strategy"
    mock_items = [
        {
            "id": "1",
            "userId": "test-user",
            "timestamp": datetime.utcnow().isoformat(),
            "logEntry": {"content": "Our AI strategy is evolving"},
            "tags": []
        }
    ]
    
    cosmos_service.container.query_items = AsyncMock(
        return_value=AsyncIterator(mock_items)
    )
    
    # Act
    result = await cosmos_service.search_logs_by_content(
        user_id="test-user",
        search_term=search_term,
        limit=10
    )
    
    # Assert
    assert len(result) == 1
    assert search_term in result[0].logEntry["content"]

# Helper class for async iteration
class AsyncIterator:
    def __init__(self, items):
        self.items = items
        self.index = 0
    
    def __aiter__(self):
        return self
    
    async def __anext__(self):
        if self.index >= len(self.items):
            raise StopAsyncIteration
        item = self.items[self.index]
        self.index += 1
        return item
```

### 4.2 Integration Test for CEO Log Agent
**File**: `/backend/agentic/connected_agents/stratos/tests/test_ceo_log_cosmos_integration.py`
```python
"""
Integration test for CEO Log Agent with Cosmos DB
"""

import asyncio
import json
import os
from datetime import datetime
from pathlib import Path

from azure.ai.projects.aio import AIProjectClient
from azure.identity.aio import DefaultAzureCredential
from dotenv import load_dotenv

# Load environment
load_dotenv()

async def test_ceo_log_cosmos_integration():
    """Test CEO Log Agent with Cosmos DB operations"""
    
    print("\n" + "="*60)
    print("CEO LOG AGENT - COSMOS DB INTEGRATION TEST")
    print("="*60)
    
    # Load deployment info
    deployment_file = Path(__file__).parent.parent / "archive/stratos_deployment_info.json"
    with open(deployment_file, 'r') as f:
        deployment_info = json.load(f)
    
    orchestrator_id = deployment_info["orchestrator"]["id"]
    connection_string = os.getenv("AZURE_AI_PROJECT_CONNECTION_STRING")
    
    async with DefaultAzureCredential() as credential:
        async with AIProjectClient(
            endpoint=connection_string,
            credential=credential
        ) as client:
            
            # Test 1: Create a new log entry
            print("\n1️⃣ TEST: Create CEO Log Entry")
            print("-" * 40)
            
            thread = await client.agents.create_thread()
            
            create_query = """
            Create a CEO log entry:
            "Had productive meeting with engineering team. Decided to accelerate AI integration 
            in our core platform. Team morale is high. Need to review resource allocation for Q3."
            
            Tags: team-meeting, ai-strategy, resource-planning
            Sentiment: positive
            """
            
            message = await client.agents.create_message(
                thread_id=thread.id,
                role="user",
                content=create_query
            )
            
            run = await client.agents.create_run(
                thread_id=thread.id,
                assistant_id=orchestrator_id
            )
            
            # Wait for completion
            while run.status in ["queued", "in_progress"]:
                await asyncio.sleep(1)
                run = await client.agents.get_run(
                    thread_id=thread.id,
                    run_id=run.id
                )
            
            # Get response
            messages = await client.agents.list_messages(thread_id=thread.id)
            for msg in messages.data:
                if msg.role == "assistant" and msg.run_id == run.id:
                    print("Response:")
                    print(msg.content[0].text.value)
                    break
            
            # Test 2: Retrieve recent logs
            print("\n2️⃣ TEST: Retrieve Recent CEO Logs")
            print("-" * 40)
            
            retrieve_query = "Show me CEO log entries from the last 7 days"
            
            thread2 = await client.agents.create_thread()
            message2 = await client.agents.create_message(
                thread_id=thread2.id,
                role="user",
                content=retrieve_query
            )
            
            run2 = await client.agents.create_run(
                thread_id=thread2.id,
                assistant_id=orchestrator_id
            )
            
            while run2.status in ["queued", "in_progress"]:
                await asyncio.sleep(1)
                run2 = await client.agents.get_run(
                    thread_id=thread2.id,
                    run_id=run2.id
                )
            
            messages2 = await client.agents.list_messages(thread_id=thread2.id)
            for msg in messages2.data:
                if msg.role == "assistant" and msg.run_id == run2.id:
                    print("Response:")
                    print(msg.content[0].text.value[:500] + "...")
                    break
            
            # Test 3: Search logs
            print("\n3️⃣ TEST: Search CEO Logs")
            print("-" * 40)
            
            search_query = "Search CEO logs for entries about AI strategy"
            
            thread3 = await client.agents.create_thread()
            message3 = await client.agents.create_message(
                thread_id=thread3.id,
                role="user",
                content=search_query
            )
            
            run3 = await client.agents.create_run(
                thread_id=thread3.id,
                assistant_id=orchestrator_id
            )
            
            while run3.status in ["queued", "in_progress"]:
                await asyncio.sleep(1)
                run3 = await client.agents.get_run(
                    thread_id=thread3.id,
                    run_id=run3.id
                )
            
            messages3 = await client.agents.list_messages(thread_id=thread3.id)
            for msg in messages3.data:
                if msg.role == "assistant" and msg.run_id == run3.id:
                    print("Response:")
                    print(msg.content[0].text.value[:500] + "...")
                    break
            
            # Test 4: Analyze themes
            print("\n4️⃣ TEST: Analyze Strategic Themes")
            print("-" * 40)
            
            analyze_query = "Analyze strategic themes from my CEO logs over the past 30 days"
            
            thread4 = await client.agents.create_thread()
            message4 = await client.agents.create_message(
                thread_id=thread4.id,
                role="user",
                content=analyze_query
            )
            
            run4 = await client.agents.create_run(
                thread_id=thread4.id,
                assistant_id=orchestrator_id
            )
            
            while run4.status in ["queued", "in_progress"]:
                await asyncio.sleep(1)
                run4 = await client.agents.get_run(
                    thread_id=thread4.id,
                    run_id=run4.id
                )
            
            messages4 = await client.agents.list_messages(thread_id=thread4.id)
            for msg in messages4.data:
                if msg.role == "assistant" and msg.run_id == run4.id:
                    print("Response:")
                    print(msg.content[0].text.value)
                    break
    
    print("\n" + "="*60)
    print("INTEGRATION TEST COMPLETED")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(test_ceo_log_cosmos_integration())
```

## Phase 5: Deployment and Monitoring

### 5.1 Update Deployment Script
**File**: `/backend/agentic/connected_agents/stratos/deployment/deploy_ceo_log_with_cosmos.py`
```python
"""
Deploy CEO Log Agent with Cosmos DB Integration
"""

import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(env_path)

# Add Cosmos DB configuration to environment
COSMOS_ENV_VARS = {
    "AZURE_COSMOS_ENDPOINT": "https://stratos-ceo-logs-db.documents.azure.com:443/",
    "AZURE_KEYVAULT_URL": "https://stratos-keyvault.vault.azure.net/",
    "COSMOS_DB_ENABLED": "true"
}

async def update_ceo_log_deployment():
    """Update CEO Log Agent deployment with Cosmos DB config"""
    
    print("Updating CEO Log Agent deployment with Cosmos DB...")
    
    # Update environment variables
    with open(env_path, 'a') as f:
        f.write("\n# Cosmos DB Configuration\n")
        for key, value in COSMOS_ENV_VARS.items():
            f.write(f"{key}={value}\n")
    
    print("✅ Environment variables updated")
    
    # Deploy updated agent
    from deploy_all_stratos_agents_v2 import deploy_all_stratos_agents
    await deploy_all_stratos_agents()
    
    print("✅ CEO Log Agent redeployed with Cosmos DB integration")

if __name__ == "__main__":
    asyncio.run(update_ceo_log_deployment())
```

### 5.2 Monitoring and Alerts
**File**: `/backend/agentic/connected_agents/stratos/monitoring/cosmos_db_monitor.py`
```python
"""
Monitor Cosmos DB operations for CEO Log Agent
"""

import asyncio
from datetime import datetime, timedelta
from azure.monitor.query import LogsQueryClient
from azure.identity import DefaultAzureCredential

class CosmosDBMonitor:
    """Monitor Cosmos DB operations"""
    
    def __init__(self):
        self.credential = DefaultAzureCredential()
        self.logs_client = LogsQueryClient(self.credential)
        self.workspace_id = os.getenv("LOG_ANALYTICS_WORKSPACE_ID")
    
    async def check_operation_metrics(self):
        """Check Cosmos DB operation metrics"""
        
        query = """
        AzureDiagnostics
        | where ResourceType == "DOCUMENTDB"
        | where Resource == "stratos-ceo-logs-db"
        | summarize 
            TotalRequests = count(),
            AvgLatency = avg(duration_s),
            Errors = countif(statusCode_s >= 400)
            by bin(TimeGenerated, 5m)
        | order by TimeGenerated desc
        | take 20
        """
        
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=1)
        
        response = await self.logs_client.query_workspace(
            workspace_id=self.workspace_id,
            query=query,
            timespan=(start_time, end_time)
        )
        
        return response.tables[0].rows if response.tables else []
    
    async def check_throughput_usage(self):
        """Monitor RU consumption"""
        
        query = """
        AzureMetrics
        | where ResourceType == "DOCUMENTDB"
        | where MetricName == "TotalRequestUnits"
        | summarize AvgRU = avg(Total) by bin(TimeGenerated, 5m)
        | order by TimeGenerated desc
        | take 20
        """
        
        # Execute query and return results
        # Similar implementation as above
```

## Phase 6: Documentation and Training

### 6.1 User Documentation
Create comprehensive documentation for:
1. CEO Log Agent Cosmos DB features
2. Query examples and best practices
3. Data retention and privacy policies
4. Performance optimization tips

### 6.2 API Documentation
Document all new functions:
- `create_log_entry`: Parameters, response format
- `get_log_entries`: Query options, filters
- `search_logs`: Search syntax, limitations
- `analyze_themes`: Analysis capabilities
- `generate_summary`: Summary options

## Implementation Timeline

### Week 1: Infrastructure Setup
- Day 1-2: Provision Cosmos DB resources
- Day 3-4: Configure security and access
- Day 5: Set up monitoring

### Week 2: Code Implementation
- Day 1-2: Implement Cosmos DB service
- Day 3-4: Update CEO Log plugin
- Day 5: Integration testing

### Week 3: Testing and Deployment
- Day 1-2: Unit and integration tests
- Day 3: Performance testing
- Day 4: Deployment to staging
- Day 5: Production deployment

### Week 4: Monitoring and Optimization
- Day 1-2: Monitor performance
- Day 3-4: Optimize queries
- Day 5: Documentation completion

## Success Criteria

1. **Functional Requirements**
   - ✅ CEO Log Agent successfully stores entries in Cosmos DB
   - ✅ All CRUD operations work correctly
   - ✅ Search and analytics functions operational
   - ✅ Data persistence across sessions

2. **Performance Requirements**
   - ✅ Query response time < 2 seconds
   - ✅ Write operations < 1 second
   - ✅ Support for 1000+ log entries per user

3. **Security Requirements**
   - ✅ Encrypted data at rest and in transit
   - ✅ Role-based access control
   - ✅ Audit trail for all operations

4. **Monitoring Requirements**
   - ✅ Real-time operation metrics
   - ✅ Alerts for errors and performance issues
   - ✅ Usage analytics dashboard

## Risk Mitigation

1. **Data Loss Prevention**
   - Enable Cosmos DB backup
   - Implement retry logic
   - Add data validation

2. **Performance Issues**
   - Start with adequate RU allocation
   - Implement caching for frequent queries
   - Monitor and scale as needed

3. **Security Concerns**
   - Use managed identities
   - Regular security audits
   - Encrypt sensitive data fields

## Conclusion

This comprehensive plan provides a structured approach to integrating Cosmos DB with the CEO Log connected agent. Following this plan will enable persistent storage, advanced querying, and strategic analysis capabilities while maintaining security and performance standards.