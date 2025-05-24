# StratOS FastAPI Deployment Guide

This guide covers deploying the StratOS FastAPI backend to Azure Container Apps.

## Prerequisites

1. Azure CLI installed and logged in (`az login`)
2. Docker installed and running
3. Environment variables configured in `.env` file
4. Python 3.11+ (for local testing)

## Quick Start

### 1. Test Locally with Docker

```bash
# Test Docker build and run locally
./scripts/test_docker_locally.sh
```

This will:
- Build the Docker image
- Run it locally on port 8000
- Test the health endpoint

### 2. Deploy to Azure Container Apps

```bash
# Deploy to Azure (uses default settings)
./scripts/deploy_to_azure_container_apps.sh
```

This will:
- Create a resource group
- Create an Azure Container Registry
- Build and push the Docker image
- Create a Container Apps environment
- Deploy the FastAPI app
- Output the public URL

### 3. Interact with Deployed App

```bash
# Check health
python scripts/interact_with_azure_app.py health

# List agents
python scripts/interact_with_azure_app.py agents

# Create CEO log entry
python scripts/interact_with_azure_app.py ceo-log "Strategic meeting notes"

# Set organizational purpose
python scripts/interact_with_azure_app.py set-purpose "Empower organizations with AI"

# Get North Star summary
python scripts/interact_with_azure_app.py north-star
```

## Deployment Options

### Custom Resource Group and Location

```bash
./scripts/deploy_to_azure_container_apps.sh \
    --resource-group my-rg \
    --location westus2
```

### Custom Container Registry

```bash
./scripts/deploy_to_azure_container_apps.sh \
    --registry-name myregistry
```

### Deploy with Specific Tag

```bash
./scripts/deploy_to_azure_container_apps.sh \
    --tag v1.0.0
```

## Architecture

```
┌─────────────────┐
│   Azure CLI     │
└────────┬────────┘
         │
    ┌────▼────┐
    │ Deploy  │
    │ Script  │
    └────┬────┘
         │
    ┌────▼──────────────────────────┐
    │   Azure Container Registry    │
    │   (stores Docker images)      │
    └────┬──────────────────────────┘
         │
    ┌────▼──────────────────────────┐
    │   Azure Container Apps        │
    │   ┌────────────────────┐      │
    │   │  StratOS FastAPI   │      │
    │   │  - Auto-scaling    │      │
    │   │  - HTTPS endpoint  │      │
    │   │  - Env variables   │      │
    │   └────────────────────┘      │
    └───────────────────────────────┘
```

## Files Created

### Docker Files
- `Dockerfile` - Multi-stage build for production
- `.dockerignore` - Excludes unnecessary files
- `docker-compose.yml` - Local development setup

### Deployment Scripts
- `scripts/deploy_to_azure_container_apps.sh` - Main deployment script
- `scripts/test_docker_locally.sh` - Local Docker testing
- `scripts/interact_with_azure_app.py` - API interaction tool

### Generated Files
- `deployment_info_azure.json` - Contains deployment details and URLs

## Monitoring

### View Logs

```bash
# Get the values from deployment_info_azure.json
RESOURCE_GROUP="stratos-container-apps-rg"
APP_NAME="stratos-fastapi"

# View streaming logs
az containerapp logs show -n $APP_NAME -g $RESOURCE_GROUP --follow

# View recent logs
az containerapp logs show -n $APP_NAME -g $RESOURCE_GROUP --tail 100
```

### Check App Status

```bash
# Get app details
az containerapp show -n $APP_NAME -g $RESOURCE_GROUP

# Get revision list
az containerapp revision list -n $APP_NAME -g $RESOURCE_GROUP -o table
```

## Updating the App

### Deploy New Version

1. Make code changes
2. Deploy with new tag:
```bash
./scripts/deploy_to_azure_container_apps.sh --tag v1.0.1
```

### Scale the App

```bash
# Scale to specific replica count
az containerapp update -n $APP_NAME -g $RESOURCE_GROUP \
    --min-replicas 2 --max-replicas 5

# Update CPU/Memory
az containerapp update -n $APP_NAME -g $RESOURCE_GROUP \
    --cpu 1.0 --memory 2.0
```

## Troubleshooting

### Check Health Endpoint

```bash
# Using deployment info
APP_URL=$(jq -r .app_url deployment_info_azure.json)
curl "$APP_URL/health"
```

### Common Issues

1. **Build fails**: Check Docker daemon is running
2. **Push fails**: Ensure ACR login succeeded
3. **App won't start**: Check logs for startup errors
4. **502 errors**: App might still be starting, wait a minute

### Clean Up Resources

```bash
# Delete the entire resource group
RESOURCE_GROUP="stratos-container-apps-rg"
az group delete --name $RESOURCE_GROUP --yes
```

## Security Considerations

1. **Secrets**: All sensitive values are passed as environment variables
2. **Network**: Container Apps provides built-in HTTPS
3. **Authentication**: MSAL middleware configured (dev bypass available)
4. **Registry**: Uses admin credentials (consider service principal for production)

## Cost Optimization

- Container Apps charges per vCPU and memory seconds
- Minimum configuration: 0.5 vCPU, 1GB memory
- Auto-scaling configured (1-3 replicas)
- Consider using consumption plan for dev/test

## Next Steps

1. Set up custom domain
2. Configure Azure Front Door for global distribution
3. Add Application Insights for monitoring
4. Implement CI/CD pipeline
5. Set up staging environments