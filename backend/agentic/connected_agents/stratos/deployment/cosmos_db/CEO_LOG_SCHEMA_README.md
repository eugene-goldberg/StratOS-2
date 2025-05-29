# CEO Log Cosmos DB Schema Documentation

Generated: 2025-05-28T22:11:05.844087

## Container Configuration
- **Name**: CEOLogs
- **Partition Key**: /userId
- **Default TTL**: -1 (no expiration)

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
