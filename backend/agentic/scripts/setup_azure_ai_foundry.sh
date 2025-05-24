#!/bin/bash
# Setup Azure AI Foundry infrastructure for StratOS agents

set -e

echo "===== Setting up Azure AI Foundry Infrastructure for StratOS ====="

# Load environment variables
if [ -f ../.env ]; then
    echo "Loading environment variables from .env file..."
    export $(grep -v '^#' ../.env | xargs)
fi

# Check required environment variables
if [ -z "$AZURE_SUBSCRIPTION_ID" ]; then
    echo "ERROR: AZURE_SUBSCRIPTION_ID is not set"
    exit 1
fi

if [ -z "$AZURE_RESOURCE_GROUP" ]; then
    echo "ERROR: AZURE_RESOURCE_GROUP is not set"
    exit 1
fi

# Set variables
LOCATION=${AZURE_LOCATION:-"eastus"}
AI_HUB_NAME=${AZURE_AI_HUB_NAME:-"sk-multi-agent-hub"}
AI_PROJECT_NAME=${AZURE_AI_PROJECT_NAME:-"sk-multi-agent-project"}
OPENAI_NAME="stratos-openai-$(date +%s)"
SEARCH_NAME="stratos-search-$(date +%s)"
STORAGE_NAME="stratosstorage$(date +%s)"

echo "Configuration:"
echo "  Subscription: $AZURE_SUBSCRIPTION_ID"
echo "  Resource Group: $AZURE_RESOURCE_GROUP"
echo "  Location: $LOCATION"
echo "  AI Hub: $AI_HUB_NAME"
echo "  AI Project: $AI_PROJECT_NAME"

# Set subscription
echo "Setting subscription..."
az account set --subscription "$AZURE_SUBSCRIPTION_ID"

# Create resource group if it doesn't exist
echo "Creating resource group..."
az group create --name "$AZURE_RESOURCE_GROUP" --location "$LOCATION" || echo "Resource group already exists"

# Create storage account for AI Hub
echo "Creating storage account..."
az storage account create \
    --name "$STORAGE_NAME" \
    --resource-group "$AZURE_RESOURCE_GROUP" \
    --location "$LOCATION" \
    --sku Standard_LRS \
    --kind StorageV2 || echo "Storage account creation failed, continuing..."

# Create Azure OpenAI service
echo "Creating Azure OpenAI service..."
az cognitiveservices account create \
    --name "$OPENAI_NAME" \
    --resource-group "$AZURE_RESOURCE_GROUP" \
    --location "$LOCATION" \
    --kind OpenAI \
    --sku S0 \
    --yes || echo "OpenAI service already exists"

# Deploy GPT-4 model
echo "Deploying GPT-4 model..."
az cognitiveservices account deployment create \
    --name "$OPENAI_NAME" \
    --resource-group "$AZURE_RESOURCE_GROUP" \
    --deployment-name "gpt-4" \
    --model-name "gpt-4" \
    --model-version "0613" \
    --model-format OpenAI \
    --sku-name "Standard" \
    --sku-capacity 10 || echo "GPT-4 deployment failed, continuing..."

# Create Azure AI Search service
echo "Creating Azure AI Search service..."
az search service create \
    --name "$SEARCH_NAME" \
    --resource-group "$AZURE_RESOURCE_GROUP" \
    --location "$LOCATION" \
    --sku basic || echo "Search service already exists"

# Create AI Hub
echo "Creating AI Hub..."
az ml workspace create \
    --name "$AI_HUB_NAME" \
    --resource-group "$AZURE_RESOURCE_GROUP" \
    --location "$LOCATION" \
    --kind hub \
    --storage-account "$STORAGE_NAME" || echo "AI Hub already exists"

# Create AI Project
echo "Creating AI Project..."
az ml workspace create \
    --name "$AI_PROJECT_NAME" \
    --resource-group "$AZURE_RESOURCE_GROUP" \
    --location "$LOCATION" \
    --kind project \
    --hub-id "/subscriptions/$AZURE_SUBSCRIPTION_ID/resourceGroups/$AZURE_RESOURCE_GROUP/providers/Microsoft.MachineLearningServices/workspaces/$AI_HUB_NAME" || echo "AI Project already exists"

# Get connection strings and keys
echo "Getting connection information..."
OPENAI_ENDPOINT=$(az cognitiveservices account show \
    --name "$OPENAI_NAME" \
    --resource-group "$AZURE_RESOURCE_GROUP" \
    --query "properties.endpoint" -o tsv)

OPENAI_KEY=$(az cognitiveservices account keys list \
    --name "$OPENAI_NAME" \
    --resource-group "$AZURE_RESOURCE_GROUP" \
    --query "key1" -o tsv)

SEARCH_ENDPOINT=$(az search service show \
    --name "$SEARCH_NAME" \
    --resource-group "$AZURE_RESOURCE_GROUP" \
    --query "properties.endpoint" -o tsv)

SEARCH_KEY=$(az search admin-key show \
    --service-name "$SEARCH_NAME" \
    --resource-group "$AZURE_RESOURCE_GROUP" \
    --query "primaryKey" -o tsv)

# Update .env file
echo "Updating .env file..."
cat > ../.env.new << EOF
# Azure OpenAI Service Configuration
AZURE_OPENAI_ENDPOINT=$OPENAI_ENDPOINT
AZURE_OPENAI_API_KEY=$OPENAI_KEY
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4

# Azure AI Foundry Configuration
AZURE_AI_HUB_NAME=$AI_HUB_NAME
AZURE_AI_PROJECT_NAME=$AI_PROJECT_NAME
AZURE_AI_PROJECT_HOST=$LOCATION.api.azureml.ms
AZURE_SUBSCRIPTION_ID=$AZURE_SUBSCRIPTION_ID
AZURE_RESOURCE_GROUP=$AZURE_RESOURCE_GROUP
AZURE_AI_PROJECT_CONNECTION_STRING=$LOCATION.api.azureml.ms/discovery;$AZURE_SUBSCRIPTION_ID;$AZURE_RESOURCE_GROUP;$AI_HUB_NAME/$AI_PROJECT_NAME

# Azure AI Search Configuration
AZURE_SEARCH_ENDPOINT=$SEARCH_ENDPOINT
AZURE_SEARCH_API_KEY=$SEARCH_KEY
AZURE_SEARCH_INDEX_NAME=stratos-index

# Service Principal credentials (keep existing)
$(grep "AZURE_CLIENT_ID\|AZURE_CLIENT_SECRET\|AZURE_TENANT_ID" ../.env)
EOF

echo ""
echo "===== Azure AI Foundry Infrastructure Setup Complete ====="
echo ""
echo "Resources created:"
echo "  - Resource Group: $AZURE_RESOURCE_GROUP"
echo "  - AI Hub: $AI_HUB_NAME"
echo "  - AI Project: $AI_PROJECT_NAME"
echo "  - OpenAI Service: $OPENAI_NAME"
echo "  - AI Search Service: $SEARCH_NAME"
echo ""
echo "Next steps:"
echo "1. Review the updated .env.new file"
echo "2. Back up your current .env file: cp .env .env.backup"
echo "3. Apply the new configuration: mv .env.new .env"
echo "4. Run the agent deployment script: ./scripts/deploy_stratos_agents.sh"