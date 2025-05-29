#!/bin/bash
# Deploy CEO Log Azure Functions

echo "Deploying CEO Log Azure Functions..."
echo "=================================="

cd ceo-log-functions

# Create function app if it doesn't exist
FUNCTION_APP_NAME="stratos-ceo-log-functions"
RESOURCE_GROUP="semantic-kernel-multi-agent-rg"
STORAGE_ACCOUNT="stratosceologfuncstorage"
LOCATION="eastus"

# Check if function app exists
echo "Checking if function app exists..."
if ! az functionapp show --name $FUNCTION_APP_NAME --resource-group $RESOURCE_GROUP &>/dev/null; then
    echo "Creating storage account..."
    az storage account create \
        --name $STORAGE_ACCOUNT \
        --location $LOCATION \
        --resource-group $RESOURCE_GROUP \
        --sku Standard_LRS

    echo "Creating function app..."
    az functionapp create \
        --resource-group $RESOURCE_GROUP \
        --consumption-plan-location $LOCATION \
        --runtime python \
        --runtime-version 3.11 \
        --functions-version 4 \
        --name $FUNCTION_APP_NAME \
        --storage-account $STORAGE_ACCOUNT \
        --os-type Linux
fi

# Set app settings
echo "Setting application settings..."
az functionapp config appsettings set \
    --name $FUNCTION_APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --settings \
    "COSMOS_ENDPOINT=https://stratos-ceo-logs-db.documents.azure.com:443/" \
    "COSMOS_KEY=VAThFP4W5W47q1UK3QHrEw0YuPiHkdFkupVtBItd3PgOiuxlM6F4SqurWmwzN3KjZIUWuDBb5RizACDbZPOSzw==" \
    "COSMOS_DATABASE=StratOSData" \
    "COSMOS_CONTAINER=CEOLogs" \
    "AZURE_OPENAI_ENDPOINT=https://sk-multi-agent-openai.openai.azure.com/" \
    "AZURE_OPENAI_API_KEY=b77c5b137db6465dabdbc34adb136e2c" \
    "AZURE_OPENAI_DEPLOYMENT_NAME=gpt-35-turbo"

# Deploy the functions
echo "Deploying functions..."
func azure functionapp publish $FUNCTION_APP_NAME --python

echo "Deployment complete!"
echo "Function app URL: https://$FUNCTION_APP_NAME.azurewebsites.net"