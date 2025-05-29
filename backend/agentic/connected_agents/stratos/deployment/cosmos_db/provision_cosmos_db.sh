#!/bin/bash

# ============================================================================
# Provision Cosmos DB for CEO Log Agent
# This script creates and configures all necessary Cosmos DB resources
# ============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_step() {
    echo -e "\n${BLUE}============================================================${NC}"
    echo -e "${GREEN}$1${NC}"
    echo -e "${BLUE}============================================================${NC}\n"
}

print_info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Configuration variables
RESOURCE_GROUP="semantic-kernel-multi-agent-rg"
COSMOS_ACCOUNT_NAME="stratos-ceo-logs-db"
LOCATION="eastus"
DATABASE_NAME="StratOSData"
CONTAINER_NAME="CEOLogs"
PARTITION_KEY="/userId"
THROUGHPUT=400
KEY_VAULT_NAME="stratos-keyvault"

# Check if logged in to Azure
print_step "Checking Azure CLI authentication"
if ! az account show &> /dev/null; then
    print_error "Not logged in to Azure. Please run 'az login' first."
    exit 1
fi

SUBSCRIPTION_ID=$(az account show --query id -o tsv)
print_success "Logged in to Azure subscription: $SUBSCRIPTION_ID"

# 1. Create Cosmos DB Account
print_step "STEP 1: Creating Cosmos DB Account"
print_info "Account Name: $COSMOS_ACCOUNT_NAME"
print_info "Resource Group: $RESOURCE_GROUP"
print_info "Location: $LOCATION"

# Check if Cosmos DB account already exists
if az cosmosdb show --name $COSMOS_ACCOUNT_NAME --resource-group $RESOURCE_GROUP &> /dev/null; then
    print_info "Cosmos DB account already exists. Skipping creation."
else
    print_info "Creating Cosmos DB account (this may take 5-10 minutes)..."
    
    az cosmosdb create \
        --name $COSMOS_ACCOUNT_NAME \
        --resource-group $RESOURCE_GROUP \
        --locations regionName=$LOCATION failoverPriority=0 isZoneRedundant=False \
        --default-consistency-level Session \
        --enable-automatic-failover false \
        --enable-multiple-write-locations false \
        --kind GlobalDocumentDB \
        --disable-key-based-metadata-write-access false \
        --tags "project=stratos" "component=ceo-log-agent" "environment=production"
    
    print_success "Cosmos DB account created successfully!"
fi

# 2. Create Database
print_step "STEP 2: Creating Database"
print_info "Database Name: $DATABASE_NAME"

# Check if database exists
DB_EXISTS=$(az cosmosdb sql database exists \
    --account-name $COSMOS_ACCOUNT_NAME \
    --resource-group $RESOURCE_GROUP \
    --name $DATABASE_NAME \
    --output tsv)

if [ "$DB_EXISTS" = "true" ]; then
    print_info "Database already exists. Skipping creation."
else
    print_info "Creating database..."
    
    az cosmosdb sql database create \
        --account-name $COSMOS_ACCOUNT_NAME \
        --resource-group $RESOURCE_GROUP \
        --name $DATABASE_NAME
    
    print_success "Database created successfully!"
fi

# 3. Create Container
print_step "STEP 3: Creating Container"
print_info "Container Name: $CONTAINER_NAME"
print_info "Partition Key: $PARTITION_KEY"
print_info "Throughput: $THROUGHPUT RU/s"

# Check if container exists
CONTAINER_EXISTS=$(az cosmosdb sql container exists \
    --account-name $COSMOS_ACCOUNT_NAME \
    --resource-group $RESOURCE_GROUP \
    --database-name $DATABASE_NAME \
    --name $CONTAINER_NAME \
    --output tsv)

if [ "$CONTAINER_EXISTS" = "true" ]; then
    print_info "Container already exists. Skipping creation."
else
    print_info "Creating container..."
    
    # Create indexing policy file
    cat > indexing-policy.json << EOF
{
    "indexingMode": "consistent",
    "automatic": true,
    "includedPaths": [
        {
            "path": "/*"
        }
    ],
    "excludedPaths": [
        {
            "path": "/\"_etag\"/?"
        }
    ],
    "compositeIndexes": [
        [
            {
                "path": "/timestamp",
                "order": "descending"
            },
            {
                "path": "/userId",
                "order": "ascending"
            }
        ]
    ]
}
EOF
    
    az cosmosdb sql container create \
        --account-name $COSMOS_ACCOUNT_NAME \
        --resource-group $RESOURCE_GROUP \
        --database-name $DATABASE_NAME \
        --name $CONTAINER_NAME \
        --partition-key-path $PARTITION_KEY \
        --throughput $THROUGHPUT \
        --idx @indexing-policy.json
    
    # Clean up temp file
    rm indexing-policy.json
    
    print_success "Container created successfully!"
fi

# 4. Configure Security - Enable Azure AD authentication
print_step "STEP 4: Configuring Security"
print_info "Enabling Azure AD authentication..."

# Get current user's object ID
CURRENT_USER_ID=$(az ad signed-in-user show --query id -o tsv)
print_info "Current user Object ID: $CURRENT_USER_ID"

# Assign Cosmos DB Built-in Data Contributor role
print_info "Assigning Cosmos DB Data Contributor role..."

COSMOS_RESOURCE_ID="/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.DocumentDB/databaseAccounts/$COSMOS_ACCOUNT_NAME"

# Check if role assignment exists
ASSIGNMENT_EXISTS=$(az cosmosdb sql role assignment list \
    --account-name $COSMOS_ACCOUNT_NAME \
    --resource-group $RESOURCE_GROUP \
    --query "[?principalId=='$CURRENT_USER_ID' && roleDefinitionId.contains('00000000-0000-0000-0000-000000000002')].id" \
    --output tsv)

if [ -z "$ASSIGNMENT_EXISTS" ]; then
    az cosmosdb sql role assignment create \
        --account-name $COSMOS_ACCOUNT_NAME \
        --resource-group $RESOURCE_GROUP \
        --role-definition-id "00000000-0000-0000-0000-000000000002" \
        --principal-id $CURRENT_USER_ID \
        --scope $COSMOS_RESOURCE_ID
    
    print_success "Role assignment created!"
else
    print_info "Role assignment already exists."
fi

# 5. Store Connection String in Key Vault
print_step "STEP 5: Storing Credentials in Key Vault"

# Check if Key Vault exists
if ! az keyvault show --name $KEY_VAULT_NAME --resource-group $RESOURCE_GROUP &> /dev/null; then
    print_info "Creating Key Vault..."
    
    az keyvault create \
        --name $KEY_VAULT_NAME \
        --resource-group $RESOURCE_GROUP \
        --location $LOCATION \
        --enable-rbac-authorization false
    
    print_success "Key Vault created!"
else
    print_info "Key Vault already exists."
fi

# Get connection strings
print_info "Retrieving connection strings..."

PRIMARY_CONNECTION_STRING=$(az cosmosdb keys list \
    --name $COSMOS_ACCOUNT_NAME \
    --resource-group $RESOURCE_GROUP \
    --type connection-strings \
    --query "connectionStrings[0].connectionString" \
    -o tsv)

# Store in Key Vault
print_info "Storing connection string in Key Vault..."

az keyvault secret set \
    --vault-name $KEY_VAULT_NAME \
    --name "cosmos-db-connection-string" \
    --value "$PRIMARY_CONNECTION_STRING" \
    --description "Cosmos DB connection string for CEO Log Agent" \
    > /dev/null

print_success "Connection string stored in Key Vault!"

# Get Cosmos DB endpoint for Azure AD auth
COSMOS_ENDPOINT=$(az cosmosdb show \
    --name $COSMOS_ACCOUNT_NAME \
    --resource-group $RESOURCE_GROUP \
    --query documentEndpoint \
    -o tsv)

az keyvault secret set \
    --vault-name $KEY_VAULT_NAME \
    --name "cosmos-db-endpoint" \
    --value "$COSMOS_ENDPOINT" \
    --description "Cosmos DB endpoint for Azure AD authentication" \
    > /dev/null

print_success "Cosmos DB endpoint stored in Key Vault!"

# 6. Create Service Principal for CEO Log Agent
print_step "STEP 6: Creating Service Principal for CEO Log Agent"

SP_NAME="stratos-ceo-log-agent-sp"

# Check if service principal exists
SP_EXISTS=$(az ad sp list --display-name $SP_NAME --query "[0].appId" -o tsv)

if [ -z "$SP_EXISTS" ]; then
    print_info "Creating service principal..."
    
    SP_RESULT=$(az ad sp create-for-rbac \
        --name $SP_NAME \
        --role "Cosmos DB Built-in Data Contributor" \
        --scopes $COSMOS_RESOURCE_ID \
        --years 2)
    
    # Extract credentials
    CLIENT_ID=$(echo $SP_RESULT | jq -r '.appId')
    CLIENT_SECRET=$(echo $SP_RESULT | jq -r '.password')
    TENANT_ID=$(echo $SP_RESULT | jq -r '.tenant')
    
    # Store in Key Vault
    az keyvault secret set \
        --vault-name $KEY_VAULT_NAME \
        --name "ceo-log-sp-client-id" \
        --value "$CLIENT_ID" \
        > /dev/null
    
    az keyvault secret set \
        --vault-name $KEY_VAULT_NAME \
        --name "ceo-log-sp-client-secret" \
        --value "$CLIENT_SECRET" \
        > /dev/null
    
    az keyvault secret set \
        --vault-name $KEY_VAULT_NAME \
        --name "ceo-log-sp-tenant-id" \
        --value "$TENANT_ID" \
        > /dev/null
    
    print_success "Service principal created and credentials stored!"
else
    print_info "Service principal already exists: $SP_EXISTS"
fi

# 7. Output Summary
print_step "PROVISIONING COMPLETE! 🎉"

echo -e "${GREEN}Summary of created resources:${NC}"
echo "================================"
echo "Cosmos DB Account: $COSMOS_ACCOUNT_NAME"
echo "Database: $DATABASE_NAME"
echo "Container: $CONTAINER_NAME"
echo "Partition Key: $PARTITION_KEY"
echo "Throughput: $THROUGHPUT RU/s"
echo "Key Vault: $KEY_VAULT_NAME"
echo "Service Principal: $SP_NAME"
echo ""
echo "Endpoint: $COSMOS_ENDPOINT"
echo ""
echo -e "${YELLOW}Connection details stored in Key Vault:${NC}"
echo "- cosmos-db-connection-string"
echo "- cosmos-db-endpoint"
echo "- ceo-log-sp-client-id"
echo "- ceo-log-sp-client-secret"
echo "- ceo-log-sp-tenant-id"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo "1. Update the CEO Log Agent configuration with Key Vault URL"
echo "2. Deploy the updated CEO Log Agent"
echo "3. Test the Cosmos DB integration"

# Save configuration for reference
cat > cosmos_db_config.json << EOF
{
    "cosmosAccount": "$COSMOS_ACCOUNT_NAME",
    "database": "$DATABASE_NAME",
    "container": "$CONTAINER_NAME",
    "partitionKey": "$PARTITION_KEY",
    "endpoint": "$COSMOS_ENDPOINT",
    "keyVault": "$KEY_VAULT_NAME",
    "resourceGroup": "$RESOURCE_GROUP",
    "throughput": $THROUGHPUT,
    "provisionedDate": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
}
EOF

print_info "Configuration saved to cosmos_db_config.json"