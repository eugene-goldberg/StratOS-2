#!/bin/bash

# Query telemetry data from Application Insights

APP_INSIGHTS_NAME="stratos-multi-agent-appinsights"
RESOURCE_GROUP="semantic-kernel-multi-agent-rg"

echo "🔍 Querying Telemetry Data from Application Insights"
echo "=================================================="

# Function to run a query
run_query() {
    local query="$1"
    local description="$2"
    
    echo ""
    echo "📊 $description"
    echo "Query: $query"
    echo "-----------------"
    
    az monitor app-insights query \
        --app "$APP_INSIGHTS_NAME" \
        -g "$RESOURCE_GROUP" \
        --analytics-query "$query" \
        -o table
}

# 1. Get recent traces
run_query \
    "traces | where timestamp > ago(1h) | order by timestamp desc | take 10 | project timestamp, message, severityLevel, customDimensions" \
    "Recent Traces (Last Hour)"

# 2. Get agent operations
run_query \
    "customEvents | where timestamp > ago(1h) | where name contains 'agent' or name contains 'orchestrator' | order by timestamp desc | take 10" \
    "Recent Agent Operations"

# 3. Get exceptions/errors
run_query \
    "exceptions | where timestamp > ago(24h) | order by timestamp desc | take 10 | project timestamp, message, type, severityLevel" \
    "Recent Exceptions (Last 24 Hours)"

# 4. Get performance metrics
run_query \
    "performanceCounters | where timestamp > ago(1h) | summarize avg(value) by name | order by name" \
    "Performance Metrics (Average Last Hour)"

# 5. Get operation counts by agent
run_query \
    "requests | where timestamp > ago(1h) | summarize count() by cloud_RoleName | order by count_ desc" \
    "Operation Counts by Agent"

# 6. Get average duration by operation
run_query \
    "requests | where timestamp > ago(1h) | summarize avg(duration), percentile(duration, 95) by name | order by avg_duration desc" \
    "Average Duration by Operation"

echo ""
echo "✅ Query complete!"
echo ""
echo "📈 For more detailed analysis:"
echo "1. Go to Azure Portal > Application Insights > stratos-multi-agent-appinsights"
echo "2. Use the Analytics blade for custom queries"
echo "3. Check Application Map for service dependencies"
echo "4. Use Transaction Search for specific traces"