#\!/bin/bash

# Azure Application Insights Setup for StratOS Multi-Agent System

# Define variables
RESOURCE_GROUP="semantic-kernel-multi-agent-rg"
LOCATION="eastus"
APP_INSIGHTS_NAME="stratos-multi-agent-appinsights"
AI_PROJECT_NAME="sk-multi-agent-project"
AI_HUB_NAME="sk-multi-agent-hub"

echo "🔍 Setting up Application Insights for StratOS Multi-Agent System"
echo "=================================================="

# Create Application Insights resource
echo "Creating Application Insights resource..."
az monitor app-insights component create \
    --app "$APP_INSIGHTS_NAME" \
    -g "$RESOURCE_GROUP" \
    --location "$LOCATION" \
    --kind "web" \
    --application-type "web" \
    -o table

# Get the connection string
echo ""
echo "Getting Application Insights connection string..."
APP_INSIGHTS_CONNECTION_STRING=$(az monitor app-insights component show \
    --app "$APP_INSIGHTS_NAME" \
    -g "$RESOURCE_GROUP" \
    --query "connectionString" \
    -o tsv)

echo ""
echo "✅ Application Insights created successfully\!"
echo "Connection String: $APP_INSIGHTS_CONNECTION_STRING"

# Save to environment file
echo ""
echo "Saving connection string to .env file..."
echo "APPLICATIONINSIGHTS_CONNECTION_STRING=\"$APP_INSIGHTS_CONNECTION_STRING\"" >> ../../.env

echo ""
echo "📊 Application Insights Details:"
echo "- Name: $APP_INSIGHTS_NAME"
echo "- Resource Group: $RESOURCE_GROUP"
echo "- Location: $LOCATION"

# Get the instrumentation key as well
INSTRUMENTATION_KEY=$(az monitor app-insights component show \
    --app "$APP_INSIGHTS_NAME" \
    -g "$RESOURCE_GROUP" \
    --query "instrumentationKey" \
    -o tsv)

echo "- Instrumentation Key: $INSTRUMENTATION_KEY"

echo ""
echo "✅ Setup complete\! Next steps:"
echo "1. Install OpenTelemetry packages: pip install azure-monitor-opentelemetry opentelemetry-instrumentation-httpx"
echo "2. Initialize tracing in your agent code"
echo "3. Redeploy agents with the new connection string"
