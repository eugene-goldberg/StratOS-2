#!/bin/bash

# Deploy North Star Azure Functions
echo "Deploying North Star Azure Functions..."

# Variables
RESOURCE_GROUP="semantic-kernel-multi-agent-rg"
STORAGE_ACCOUNT="stratosnorthstarfunc"
FUNCTION_APP_NAME="stratos-north-star-functions"
LOCATION="eastus"
COSMOS_CONNECTION_STRING="AccountEndpoint=https://stratos-ceo-logs-db.documents.azure.com:443/;AccountKey=VAThFP4W5W47q1UK3QHrEw0YuPiHkdFkupVtBItd3PgOiuxlM6F4SqurWmwzN3KjZIUWuDBb5RizACDbZPOSzw==;"

# Create storage account if it doesn't exist
echo "Creating storage account..."
az storage account create \
    --name $STORAGE_ACCOUNT \
    --location $LOCATION \
    --resource-group $RESOURCE_GROUP \
    --sku Standard_LRS

# Create function app
echo "Creating function app..."
az functionapp create \
    --resource-group $RESOURCE_GROUP \
    --consumption-plan-location $LOCATION \
    --runtime python \
    --runtime-version 3.11 \
    --functions-version 4 \
    --name $FUNCTION_APP_NAME \
    --storage-account $STORAGE_ACCOUNT

# Configure app settings
echo "Configuring app settings..."
az functionapp config appsettings set \
    --name $FUNCTION_APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --settings "COSMOS_CONNECTION_STRING=$COSMOS_CONNECTION_STRING"

# Deploy the functions
echo "Deploying functions code..."
cd /Users/eugene/dev/ai/stratos-2/StratOS-2/backend/agentic/connected_agents/stratos/north-star-functions
func azure functionapp publish $FUNCTION_APP_NAME --python

echo "Deployment complete!"
echo "Function App URL: https://$FUNCTION_APP_NAME.azurewebsites.net"

# Get function keys
echo "Getting function keys..."
for func in ManagePurpose ManageVision ManageValues ManageStrategicGoals ValidateAlignment GetNorthStarSummary; do
    echo "Key for $func:"
    az functionapp function keys list \
        --name $FUNCTION_APP_NAME \
        --resource-group $RESOURCE_GROUP \
        --function-name $func \
        --query "default" -o tsv
done