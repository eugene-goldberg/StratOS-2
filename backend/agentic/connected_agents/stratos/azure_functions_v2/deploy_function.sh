#!/bin/bash
set -e

# Configuration
RESOURCE_GROUP="semantic-kernel-multi-agent-rg"
STORAGE_ACCOUNT="stratosnorthstarv2"
FUNCTION_APP_NAME="stratos-north-star-v2"
LOCATION="westus2"

# Get environment variables
source ../../../.env

echo "========================================"
echo "DEPLOYING NORTH STAR AZURE FUNCTIONS V2"
echo "========================================"

# Check if logged in to Azure
if ! az account show &>/dev/null; then
    echo "Not logged in to Azure. Please run 'az login' first."
    exit 1
fi

# Create storage account if it doesn't exist
echo "Checking storage account..."
if ! az storage account show --name $STORAGE_ACCOUNT --resource-group $RESOURCE_GROUP &>/dev/null; then
    echo "Creating storage account: $STORAGE_ACCOUNT"
    az storage account create \
        --name $STORAGE_ACCOUNT \
        --location $LOCATION \
        --resource-group $RESOURCE_GROUP \
        --sku Standard_LRS
else
    echo "Storage account already exists: $STORAGE_ACCOUNT"
fi

# Create function app if it doesn't exist
echo "Checking function app..."
if ! az functionapp show --name $FUNCTION_APP_NAME --resource-group $RESOURCE_GROUP &>/dev/null; then
    echo "Creating function app: $FUNCTION_APP_NAME"
    az functionapp create \
        --resource-group $RESOURCE_GROUP \
        --consumption-plan-location $LOCATION \
        --runtime python \
        --runtime-version 3.11 \
        --functions-version 4 \
        --name $FUNCTION_APP_NAME \
        --storage-account $STORAGE_ACCOUNT \
        --os-type Linux
else
    echo "Function app already exists: $FUNCTION_APP_NAME"
fi

# Configure app settings
echo "Configuring app settings..."
az functionapp config appsettings set \
    --name $FUNCTION_APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --settings \
    COSMOS_ENDPOINT="https://stratos-ceo-logs-db.documents.azure.com:443/" \
    COSMOS_KEY="$COSMOS_KEY" \
    COSMOS_DATABASE_NAME="StratOSData"

# Deploy the function
echo "Deploying function code..."
func azure functionapp publish $FUNCTION_APP_NAME

# Get function key
echo "Getting function key..."
FUNCTION_KEY=$(az functionapp function keys list \
    --name $FUNCTION_APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --function-name north-star-operations \
    --query "default" \
    --output tsv)

echo ""
echo "========================================"
echo "DEPLOYMENT COMPLETE"
echo "========================================"
echo "Function App: $FUNCTION_APP_NAME"
echo "URL: https://$FUNCTION_APP_NAME.azurewebsites.net/api/north-star-operations"
echo "Function Key: $FUNCTION_KEY"
echo ""
echo "Test with:"
echo "curl -X POST https://$FUNCTION_APP_NAME.azurewebsites.net/api/north-star-operations \\"
echo "  -H \"x-functions-key: $FUNCTION_KEY\" \\"
echo "  -H \"Content-Type: application/json\" \\"
echo "  -d '{\"operation\": \"getNorthStarSummary\", \"organizationId\": \"test-org\"}'"