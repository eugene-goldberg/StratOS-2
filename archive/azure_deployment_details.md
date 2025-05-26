# Azure Deployment Details for StratOS Multi-Agent System
*Created: May 24, 2025*
*Deployment Status: ✅ LIVE*

## 🎉 Production Deployment Information

The StratOS Multi-Agent System FastAPI backend has been successfully deployed to Azure Container Apps.

### Live Application URLs

- **Main App URL**: https://stratos-fastapi.gentlesea-48f3e5ad.eastus.azurecontainerapps.io
- **Health Check**: https://stratos-fastapi.gentlesea-48f3e5ad.eastus.azurecontainerapps.io/api/health/
- **API Documentation (Swagger)**: https://stratos-fastapi.gentlesea-48f3e5ad.eastus.azurecontainerapps.io/docs
- **OpenAPI Schema**: https://stratos-fastapi.gentlesea-48f3e5ad.eastus.azurecontainerapps.io/openapi.json

### Azure Resources Created

| Resource Type | Resource Name | Purpose | Status |
|--------------|---------------|---------|---------|
| **Resource Group** | stratos-container-apps-rg | Contains all deployment resources | ✅ Active |
| **Container Registry** | stratosregistry | Stores Docker images | ✅ Active |
| **Container Apps Environment** | stratos-env | Hosting environment | ✅ Active |
| **Container App** | stratos-fastapi | Main application | ✅ Running |
| **Log Analytics Workspace** | workspace-stratoscontainerappsrgxW9p | Monitoring and logs | ✅ Active |

### Container Registry Details

- **Registry Server**: stratosregistry.azurecr.io
- **Registry Username**: stratosregistry
- **Image**: stratosregistry.azurecr.io/stratos-fastapi:latest
- **Architecture**: linux/amd64
- **Creation Date**: 2025-05-24T19:52:18Z

### Container App Configuration

| Setting | Value | Description |
|---------|-------|-------------|
| **Min Replicas** | 1 | Minimum number of instances |
| **Max Replicas** | 3 | Maximum for auto-scaling |
| **CPU** | 0.5 cores | Per instance allocation |
| **Memory** | 1.0 GB | Per instance allocation |
| **Target Port** | 8000 | Internal container port |
| **Ingress** | External | Public accessibility |
| **Region** | East US | Deployment location |

### Environment Variables Configured

- `AZURE_OPENAI_ENDPOINT`: https://sk-multi-agent-openai.openai.azure.com/
- `AZURE_OPENAI_API_KEY`: [Configured]
- `AZURE_OPENAI_DEPLOYMENT_NAME`: gpt-35-turbo
- `AZURE_OPENAI_API_VERSION`: 2023-05-15
- `ENVIRONMENT`: production

### Deployment Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Internet                              │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTPS
         ┌─────────────▼─────────────┐
         │   Azure Container Apps    │
         │  (stratos-fastapi)        │
         │  • Auto-scaling (1-3)     │
         │  • Health checks          │
         │  • Load balancing         │
         └─────────────┬─────────────┘
                       │
         ┌─────────────▼─────────────┐
         │  Azure Container Registry │
         │  (stratosregistry)        │
         │  • Docker images          │
         │  • Version control        │
         └───────────────────────────┘
```

## Management Commands

### View Application Logs
```bash
# Real-time logs
az containerapp logs show -n stratos-fastapi -g stratos-container-apps-rg --follow

# Last 100 lines
az containerapp logs show -n stratos-fastapi -g stratos-container-apps-rg --tail 100
```

### Update Deployment
```bash
# Deploy new version
cd backend/agentic
./scripts/deploy_to_azure_container_apps.sh --tag v1.0.1

# Or manually update image
az containerapp update \
    -n stratos-fastapi \
    -g stratos-container-apps-rg \
    --image stratosregistry.azurecr.io/stratos-fastapi:v1.0.1
```

### Scale Application
```bash
# Manual scaling
az containerapp update \
    -n stratos-fastapi \
    -g stratos-container-apps-rg \
    --min-replicas 2 \
    --max-replicas 5

# Update CPU/Memory
az containerapp update \
    -n stratos-fastapi \
    -g stratos-container-apps-rg \
    --cpu 1.0 \
    --memory 2.0Gi
```

### Monitor Application
```bash
# Get current status
az containerapp show -n stratos-fastapi -g stratos-container-apps-rg

# List all revisions
az containerapp revision list -n stratos-fastapi -g stratos-container-apps-rg -o table

# Get metrics
az monitor metrics list \
    --resource /subscriptions/514bd6d3-2c02-45c6-a86f-29cf262a379a/resourceGroups/stratos-container-apps-rg/providers/Microsoft.App/containerApps/stratos-fastapi \
    --metric "Requests" \
    --interval PT1H
```

## Docker Image Management

### Build and Push New Version
```bash
# Build for linux/amd64
cd backend/agentic
docker buildx build --platform linux/amd64 -t stratosregistry.azurecr.io/stratos-fastapi:v1.0.1 .

# Push to registry
docker push stratosregistry.azurecr.io/stratos-fastapi:v1.0.1
```

### Registry Management
```bash
# List images
az acr repository list --name stratosregistry -o table

# Show tags
az acr repository show-tags --name stratosregistry --repository stratos-fastapi

# Delete old images
az acr repository delete --name stratosregistry --image stratos-fastapi:old-tag
```

## Troubleshooting

### Common Issues and Solutions

1. **503 Service Unavailable**
   - Check if container is running: `az containerapp revision list -n stratos-fastapi -g stratos-container-apps-rg`
   - View logs for errors: `az containerapp logs show -n stratos-fastapi -g stratos-container-apps-rg`

2. **Image Pull Errors**
   - Verify registry credentials are correct
   - Check image exists: `az acr repository show --name stratosregistry --repository stratos-fastapi`

3. **Environment Variable Issues**
   - Update env vars: `az containerapp update -n stratos-fastapi -g stratos-container-apps-rg --set-env-vars KEY=value`

4. **Scaling Issues**
   - Check resource limits in the Container Apps Environment
   - Review scaling rules and metrics

## Cost Optimization

### Current Estimated Costs (Monthly)
- **Container Apps**: ~$10-30 (based on usage)
- **Container Registry (Basic)**: ~$5
- **Log Analytics**: ~$2-5
- **Total**: ~$17-40/month

### Cost Saving Tips
1. Use minimum replicas = 0 for dev/test environments
2. Clean up old container images regularly
3. Set appropriate resource limits (CPU/Memory)
4. Use consumption plan for predictable workloads

## Security Considerations

1. **Network Security**
   - External ingress is enabled (required for public access)
   - Consider adding IP restrictions if needed
   - Use Azure Front Door for additional security

2. **Secrets Management**
   - API keys are stored as environment variables
   - Consider migrating to Azure Key Vault references
   - Rotate credentials regularly

3. **Container Security**
   - Images are scanned by ACR
   - Non-root user (stratos) runs the container
   - Regular base image updates recommended

## Next Steps

1. **Enable Application Insights**
   ```bash
   az containerapp update \
       -n stratos-fastapi \
       -g stratos-container-apps-rg \
       --dapr-app-id stratos \
       --dapr-app-insights
   ```

2. **Add Custom Domain**
   ```bash
   az containerapp hostname add \
       -n stratos-fastapi \
       -g stratos-container-apps-rg \
       --hostname api.stratos.example.com
   ```

3. **Implement CI/CD**
   - Set up GitHub Actions for automated deployments
   - Use Azure DevOps pipelines
   - Implement proper versioning strategy

## Support and Monitoring

- **Azure Portal**: [Container Apps Overview](https://portal.azure.com/#resource/subscriptions/514bd6d3-2c02-45c6-a86f-29cf262a379a/resourceGroups/stratos-container-apps-rg/providers/Microsoft.App/containerApps/stratos-fastapi/overview)
- **Subscription ID**: 514bd6d3-2c02-45c6-a86f-29cf262a379a
- **Tenant ID**: 5acd02e3-dfea-4b7c-aab5-1633ffe0403a

---

*This deployment was created on May 24, 2025, and represents the first production deployment of the StratOS Multi-Agent System.*