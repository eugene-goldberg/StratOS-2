#!/bin/bash
# Deploy StratOS FastAPI backend to Azure Container Apps
# This script handles the complete deployment process

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Default values
RESOURCE_GROUP="stratos-container-apps-rg"
LOCATION="eastus"
REGISTRY_NAME="stratosregistry"
CONTAINER_APP_NAME="stratos-fastapi"
CONTAINER_APP_ENV="stratos-env"
IMAGE_TAG="latest"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --resource-group)
            RESOURCE_GROUP="$2"
            shift 2
            ;;
        --location)
            LOCATION="$2"
            shift 2
            ;;
        --registry-name)
            REGISTRY_NAME="$2"
            shift 2
            ;;
        --app-name)
            CONTAINER_APP_NAME="$2"
            shift 2
            ;;
        --tag)
            IMAGE_TAG="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [options]"
            echo "Options:"
            echo "  --resource-group  Resource group name (default: stratos-container-apps-rg)"
            echo "  --location        Azure location (default: eastus)"
            echo "  --registry-name   Container registry name (default: stratosregistry)"
            echo "  --app-name        Container app name (default: stratos-fastapi)"
            echo "  --tag             Docker image tag (default: latest)"
            echo "  --help            Show this help message"
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

print_status "Starting StratOS FastAPI deployment to Azure Container Apps"
echo "Configuration:"
echo "  Resource Group: $RESOURCE_GROUP"
echo "  Location: $LOCATION"
echo "  Registry: $REGISTRY_NAME"
echo "  App Name: $CONTAINER_APP_NAME"
echo "  Image Tag: $IMAGE_TAG"
echo ""

# Check if logged in to Azure
print_status "Checking Azure login status..."
if ! az account show &>/dev/null; then
    print_error "Not logged in to Azure. Please run 'az login' first."
    exit 1
fi

SUBSCRIPTION_ID=$(az account show --query id -o tsv)
print_status "Using subscription: $SUBSCRIPTION_ID"

# Load environment variables
if [ -f ../.env ]; then
    print_status "Loading environment variables from .env file..."
    export $(grep -v '^#' ../.env | xargs)
else
    print_error ".env file not found in parent directory"
    exit 1
fi

# Step 1: Create Resource Group
print_status "Creating resource group '$RESOURCE_GROUP' in $LOCATION..."
az group create --name $RESOURCE_GROUP --location $LOCATION --output none

# Step 2: Create Container Registry
print_status "Creating Azure Container Registry '$REGISTRY_NAME'..."
az acr create \
    --resource-group $RESOURCE_GROUP \
    --name $REGISTRY_NAME \
    --sku Basic \
    --admin-enabled true \
    --output none

# Get registry credentials
print_status "Getting registry credentials..."
REGISTRY_SERVER=$(az acr show --name $REGISTRY_NAME --query loginServer -o tsv)
REGISTRY_USERNAME=$(az acr credential show --name $REGISTRY_NAME --query username -o tsv)
REGISTRY_PASSWORD=$(az acr credential show --name $REGISTRY_NAME --query passwords[0].value -o tsv)

# Step 3: Build and push Docker image
print_status "Building Docker image..."
cd ..
docker build -t $CONTAINER_APP_NAME:$IMAGE_TAG .

print_status "Tagging image for Azure Container Registry..."
docker tag $CONTAINER_APP_NAME:$IMAGE_TAG $REGISTRY_SERVER/$CONTAINER_APP_NAME:$IMAGE_TAG

print_status "Logging in to Azure Container Registry..."
echo $REGISTRY_PASSWORD | docker login $REGISTRY_SERVER -u $REGISTRY_USERNAME --password-stdin

print_status "Pushing image to registry..."
docker push $REGISTRY_SERVER/$CONTAINER_APP_NAME:$IMAGE_TAG

# Step 4: Create Container Apps Environment
print_status "Checking if Container Apps Environment exists..."
if ! az containerapp env show --name $CONTAINER_APP_ENV --resource-group $RESOURCE_GROUP &>/dev/null; then
    print_status "Creating Container Apps Environment..."
    az containerapp env create \
        --name $CONTAINER_APP_ENV \
        --resource-group $RESOURCE_GROUP \
        --location $LOCATION \
        --output none
else
    print_status "Container Apps Environment already exists"
fi

# Step 5: Create or update Container App
print_status "Deploying Container App..."

# Prepare environment variables for the container
ENV_VARS="AZURE_OPENAI_ENDPOINT=$AZURE_OPENAI_ENDPOINT \
AZURE_OPENAI_API_KEY=$AZURE_OPENAI_API_KEY \
AZURE_OPENAI_DEPLOYMENT_NAME=$AZURE_OPENAI_DEPLOYMENT_NAME \
AZURE_AI_HUB_NAME=$AZURE_AI_HUB_NAME \
AZURE_AI_PROJECT_NAME=$AZURE_AI_PROJECT_NAME \
AZURE_AI_PROJECT_HOST=$AZURE_AI_PROJECT_HOST \
AZURE_SUBSCRIPTION_ID=$AZURE_SUBSCRIPTION_ID \
AZURE_RESOURCE_GROUP=$AZURE_RESOURCE_GROUP \
AZURE_CLIENT_ID=$AZURE_CLIENT_ID \
AZURE_TENANT_ID=$AZURE_TENANT_ID \
AZURE_CLIENT_SECRET=$AZURE_CLIENT_SECRET \
ENVIRONMENT=production"

# Check if app exists
if az containerapp show --name $CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP &>/dev/null; then
    print_status "Updating existing Container App..."
    az containerapp update \
        --name $CONTAINER_APP_NAME \
        --resource-group $RESOURCE_GROUP \
        --image $REGISTRY_SERVER/$CONTAINER_APP_NAME:$IMAGE_TAG \
        --set-env-vars $ENV_VARS \
        --output none
else
    print_status "Creating new Container App..."
    az containerapp create \
        --name $CONTAINER_APP_NAME \
        --resource-group $RESOURCE_GROUP \
        --environment $CONTAINER_APP_ENV \
        --image $REGISTRY_SERVER/$CONTAINER_APP_NAME:$IMAGE_TAG \
        --target-port 8000 \
        --ingress 'external' \
        --registry-server $REGISTRY_SERVER \
        --registry-username $REGISTRY_USERNAME \
        --registry-password $REGISTRY_PASSWORD \
        --set-env-vars $ENV_VARS \
        --cpu 0.5 \
        --memory 1.0 \
        --min-replicas 1 \
        --max-replicas 3 \
        --output none
fi

# Step 6: Get the app URL
print_status "Getting Container App URL..."
APP_URL=$(az containerapp show \
    --name $CONTAINER_APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --query properties.configuration.ingress.fqdn -o tsv)

# Step 7: Save deployment info
print_status "Saving deployment information..."
cat > ../deployment_info_azure.json << EOF
{
    "deployment_time": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
    "subscription_id": "$SUBSCRIPTION_ID",
    "resource_group": "$RESOURCE_GROUP",
    "location": "$LOCATION",
    "container_registry": "$REGISTRY_SERVER",
    "container_app_name": "$CONTAINER_APP_NAME",
    "container_app_env": "$CONTAINER_APP_ENV",
    "app_url": "https://$APP_URL",
    "image": "$REGISTRY_SERVER/$CONTAINER_APP_NAME:$IMAGE_TAG",
    "api_endpoints": {
        "health": "https://$APP_URL/health",
        "docs": "https://$APP_URL/docs",
        "agents": "https://$APP_URL/api/v1/agents"
    }
}
EOF

# Step 8: Test the deployment
print_status "Waiting for app to be ready..."
sleep 30

print_status "Testing health endpoint..."
if curl -s "https://$APP_URL/health" | grep -q "healthy"; then
    print_status "Health check passed!"
else
    print_warning "Health check failed. The app might still be starting up."
fi

# Print summary
echo ""
print_status "Deployment completed successfully!"
echo ""
echo "========================================="
echo "Deployment Summary:"
echo "========================================="
echo "App URL: https://$APP_URL"
echo "API Docs: https://$APP_URL/docs"
echo "Health Check: https://$APP_URL/health"
echo ""
echo "Resource Group: $RESOURCE_GROUP"
echo "Container Registry: $REGISTRY_SERVER"
echo "Container App: $CONTAINER_APP_NAME"
echo ""
echo "To view logs:"
echo "  az containerapp logs show -n $CONTAINER_APP_NAME -g $RESOURCE_GROUP"
echo ""
echo "To update the app:"
echo "  $0 --tag <new-tag>"
echo "========================================="