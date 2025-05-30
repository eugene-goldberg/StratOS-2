# Complete Implementation Guide: Azure AI Agents with Direct HTTP Calls

This guide provides detailed step-by-step instructions for implementing Azure AI Agents that make direct HTTP calls to Azure Functions without client intervention.

## Table of Contents
1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Part 1: Azure Function Development](#part-1-azure-function-development)
4. [Part 2: Azure Function Deployment](#part-2-azure-function-deployment)
5. [Part 3: OpenAPI Specification](#part-3-openapi-specification)
6. [Part 4: Azure AI Connection Setup](#part-4-azure-ai-connection-setup)
7. [Part 5: Agent Deployment](#part-5-agent-deployment)
8. [Part 6: Testing and Verification](#part-6-testing-and-verification)
9. [Troubleshooting](#troubleshooting)

## Overview

### Architecture
```
User Request → Azure AI Agent → Azure AI Service (makes HTTP call) → Azure Function → Cosmos DB
                                            ↓
                                   No client intervention
```

### Key Concept
Azure AI Agents with OpenAPI tools execute HTTP calls **server-side** through the Azure AI Service infrastructure, not through your client code.

## Prerequisites

### Required Tools
```bash
# Install Azure CLI
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

# Install Azure Functions Core Tools
brew tap azure/functions
brew install azure-functions-core-tools@4

# Install Python packages
pip install azure-ai-projects azure-identity azure-cosmos azure-ai-ml
```

### Environment Setup
```bash
# Login to Azure
az login

# Set subscription (if multiple)
az account set --subscription "YOUR_SUBSCRIPTION_ID"

# Set environment variables
export AZURE_SUBSCRIPTION_ID="your-subscription-id"
export AZURE_RESOURCE_GROUP="your-resource-group"
export COSMOS_ENDPOINT="https://your-cosmos.documents.azure.com:443/"
export COSMOS_KEY="your-cosmos-key"
export AZURE_AI_PROJECT_CONNECTION_STRING="your-ai-project-connection"
```

## Part 1: Azure Function Development

### Step 1.1: Create Function Structure

```bash
mkdir azure_functions
cd azure_functions
```

### Step 1.2: Create Function App File

Create `function_app.py`:

```python
import azure.functions as func
import logging
import json
import os
import time
from datetime import datetime, timezone
from typing import Dict, Any

from azure.cosmos import CosmosClient
from azure.cosmos.exceptions import CosmosHttpResponseError

# Using v2 Python programming model
app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

# Cosmos DB configuration
COSMOS_ENDPOINT = os.environ.get("COSMOS_ENDPOINT")
COSMOS_KEY = os.environ.get("COSMOS_KEY")
DATABASE_NAME = os.environ.get("COSMOS_DATABASE_NAME", "YourDatabase")
CONTAINER_NAME = "YourContainer"

# Global Cosmos client (singleton pattern)
cosmos_client = None
container = None


def get_cosmos_container():
    """Get or create Cosmos container."""
    global cosmos_client, container
    
    if container is None:
        cosmos_client = CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)
        database = cosmos_client.get_database_client(DATABASE_NAME)
        
        try:
            container = database.get_container_client(CONTAINER_NAME)
            container.read()
            logging.info(f"Connected to existing container: {CONTAINER_NAME}")
        except:
            # Create if doesn't exist
            container = database.create_container(
                id=CONTAINER_NAME,
                partition_key={"paths": ["/partitionKey"], "kind": "Hash"}
            )
            logging.info(f"Created new container: {CONTAINER_NAME}")
    
    return container


@app.route(route="your-function", methods=["POST"])
def your_function(req: func.HttpRequest) -> func.HttpResponse:
    """Main function endpoint."""
    logging.info('Processing request')
    
    try:
        req_body = req.get_json()
    except ValueError:
        return func.HttpResponse(
            json.dumps({"error": "Invalid JSON"}),
            status_code=400,
            mimetype="application/json"
        )
    
    operation = req_body.get('operation')
    
    if not operation:
        return func.HttpResponse(
            json.dumps({"error": "Missing operation parameter"}),
            status_code=400,
            mimetype="application/json"
        )
    
    try:
        container = get_cosmos_container()
        
        # Handle different operations
        if operation == "create":
            result = handle_create(req_body, container)
        elif operation == "read":
            result = handle_read(req_body, container)
        elif operation == "update":
            result = handle_update(req_body, container)
        elif operation == "delete":
            result = handle_delete(req_body, container)
        else:
            result = {"error": f"Unknown operation: {operation}"}
            
        return func.HttpResponse(
            json.dumps(result),
            mimetype="application/json",
            status_code=200 if "error" not in result else 400
        )
        
    except Exception as e:
        logging.error(f"Error: {e}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json"
        )


def handle_create(req_body: dict, container) -> dict:
    """Handle create operation."""
    data = req_body.get('data', {})
    data['id'] = f"{data.get('type', 'item')}_{int(time.time() * 1000)}"
    data['timestamp'] = datetime.now(timezone.utc).isoformat()
    
    result = container.create_item(body=data)
    return {"success": True, "id": result['id']}


def handle_read(req_body: dict, container) -> dict:
    """Handle read operation."""
    query = req_body.get('query', "SELECT * FROM c")
    parameters = req_body.get('parameters', [])
    
    items = list(container.query_items(
        query=query,
        parameters=parameters,
        enable_cross_partition_query=True
    ))
    
    return {"success": True, "items": items, "count": len(items)}


def handle_update(req_body: dict, container) -> dict:
    """Handle update operation."""
    item_id = req_body.get('id')
    partition_key = req_body.get('partitionKey')
    updates = req_body.get('updates', {})
    
    if not item_id or not partition_key:
        return {"error": "Missing id or partitionKey"}
    
    item = container.read_item(item=item_id, partition_key=partition_key)
    item.update(updates)
    
    result = container.replace_item(item=item_id, body=item)
    return {"success": True, "id": result['id']}


def handle_delete(req_body: dict, container) -> dict:
    """Handle delete operation."""
    item_id = req_body.get('id')
    partition_key = req_body.get('partitionKey')
    
    if not item_id or not partition_key:
        return {"error": "Missing id or partitionKey"}
    
    container.delete_item(item=item_id, partition_key=partition_key)
    return {"success": True, "id": item_id}
```

### Step 1.3: Create Configuration Files

Create `host.json`:
```json
{
  "version": "2.0",
  "logging": {
    "applicationInsights": {
      "samplingSettings": {
        "isEnabled": true,
        "excludedTypes": "Request"
      }
    }
  },
  "extensionBundle": {
    "id": "Microsoft.Azure.Functions.ExtensionBundle",
    "version": "[4.*, 5.0.0)"
  }
}
```

Create `requirements.txt`:
```
azure-functions
azure-cosmos>=4.5.0
```

Create `local.settings.json` (for local testing):
```json
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "UseDevelopmentStorage=true",
    "FUNCTIONS_WORKER_RUNTIME": "python",
    "COSMOS_ENDPOINT": "https://your-cosmos.documents.azure.com:443/",
    "COSMOS_KEY": "your-key",
    "COSMOS_DATABASE_NAME": "YourDatabase"
  }
}
```

## Part 2: Azure Function Deployment

### Step 2.1: Create Function App in Azure

```bash
# Create storage account (if needed)
az storage account create \
  --name yourstorageaccount \
  --location westus2 \
  --resource-group $AZURE_RESOURCE_GROUP \
  --sku Standard_LRS

# Create function app
az functionapp create \
  --resource-group $AZURE_RESOURCE_GROUP \
  --consumption-plan-location westus2 \
  --runtime python \
  --runtime-version 3.11 \
  --functions-version 4 \
  --name your-function-app \
  --storage-account yourstorageaccount \
  --os-type Linux
```

### Step 2.2: Configure Function App Settings

```bash
# Set environment variables
az functionapp config appsettings set \
  --name your-function-app \
  --resource-group $AZURE_RESOURCE_GROUP \
  --settings \
    COSMOS_ENDPOINT="$COSMOS_ENDPOINT" \
    COSMOS_KEY="$COSMOS_KEY" \
    COSMOS_DATABASE_NAME="YourDatabase"
```

### Step 2.3: Deploy Function Code

```bash
# From azure_functions directory
func azure functionapp publish your-function-app
```

### Step 2.4: Get Function Key

```bash
# Get the function key
FUNCTION_KEY=$(az functionapp function keys list \
  --name your-function-app \
  --resource-group $AZURE_RESOURCE_GROUP \
  --function-name your-function \
  --query "default" \
  --output tsv)

echo "Function Key: $FUNCTION_KEY"
```

### Step 2.5: Test Function Directly

```bash
# Test the function
curl -X POST https://your-function-app.azurewebsites.net/api/your-function \
  -H "x-functions-key: $FUNCTION_KEY" \
  -H "Content-Type: application/json" \
  -d '{"operation": "read", "query": "SELECT * FROM c"}'
```

## Part 3: OpenAPI Specification

### Step 3.1: Create OpenAPI Spec

Create `openapi_spec.json`:

```json
{
  "openapi": "3.0.0",
  "info": {
    "title": "Your Function API",
    "version": "1.0.0",
    "description": "Azure Function for data operations"
  },
  "servers": [
    {
      "url": "https://your-function-app.azurewebsites.net"
    }
  ],
  "paths": {
    "/api/your-function": {
      "post": {
        "operationId": "executeOperation",
        "summary": "Execute data operation",
        "description": "Perform CRUD operations on data",
        "requestBody": {
          "required": true,
          "content": {
            "application/json": {
              "schema": {
                "type": "object",
                "properties": {
                  "operation": {
                    "type": "string",
                    "enum": ["create", "read", "update", "delete"],
                    "description": "The operation to perform"
                  },
                  "data": {
                    "type": "object",
                    "description": "Data for create operation"
                  },
                  "query": {
                    "type": "string",
                    "description": "Query for read operation"
                  },
                  "parameters": {
                    "type": "array",
                    "description": "Query parameters"
                  },
                  "id": {
                    "type": "string",
                    "description": "Item ID for update/delete"
                  },
                  "partitionKey": {
                    "type": "string",
                    "description": "Partition key value"
                  },
                  "updates": {
                    "type": "object",
                    "description": "Updates for update operation"
                  }
                },
                "required": ["operation"]
              }
            }
          }
        },
        "responses": {
          "200": {
            "description": "Successful operation",
            "content": {
              "application/json": {
                "schema": {
                  "type": "object",
                  "properties": {
                    "success": {
                      "type": "boolean"
                    },
                    "id": {
                      "type": "string"
                    },
                    "items": {
                      "type": "array"
                    },
                    "count": {
                      "type": "integer"
                    }
                  }
                }
              }
            }
          },
          "400": {
            "description": "Bad Request"
          },
          "500": {
            "description": "Internal Server Error"
          }
        },
        "security": [
          {
            "function_key": []
          }
        ]
      }
    }
  },
  "components": {
    "securitySchemes": {
      "function_key": {
        "type": "apiKey",
        "name": "x-functions-key",
        "in": "header",
        "description": "API key for accessing the Azure Function"
      }
    }
  }
}
```

## Part 4: Azure AI Connection Setup

### Step 4.1: Create Connection YAML

Create `connection.yml`:

```yaml
$schema: https://azuremlschemas.azureedge.net/latest/workspaceConnection.schema.json
name: YourFunctionConnection
type: custom
target: https://your-function-app.azurewebsites.net
credentials:
  type: api_key
  key: <YOUR_FUNCTION_KEY>
metadata:
  x-functions-key: <YOUR_FUNCTION_KEY>
```

### Step 4.2: Create Connection in Azure

```bash
# Replace <YOUR_FUNCTION_KEY> with actual key
sed -i "s/<YOUR_FUNCTION_KEY>/$FUNCTION_KEY/g" connection.yml

# Create the connection
az ml connection create \
  --file connection.yml \
  --resource-group $AZURE_RESOURCE_GROUP \
  --workspace-name your-ai-workspace
```

## Part 5: Agent Deployment

### Step 5.1: Create Agent Deployment Script

Create `deploy_agent.py`:

```python
#!/usr/bin/env python3
"""
Deploy Azure AI Agent with OpenAPI tool for server-side HTTP execution
"""

import os
import json
from datetime import datetime
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient


def deploy_agent():
    """Deploy agent with OpenAPI specification."""
    
    print("=" * 70)
    print("AGENT DEPLOYMENT - SERVER-SIDE HTTP EXECUTION")
    print("=" * 70)
    
    # Configuration
    agent_name = f"DataAgent-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    model_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-35-turbo")
    connection_string = os.getenv("AZURE_AI_PROJECT_CONNECTION_STRING")
    
    # Agent instructions
    agent_instructions = """
You are a data management agent with direct access to Azure Functions for data operations.

When users request data operations:
1. Use the executeOperation tool to perform the requested action
2. The Azure AI Service will make HTTP calls directly to the Azure Function
3. No client intervention is required

For create operations: use operation="create" with data
For read operations: use operation="read" with optional query
For update operations: use operation="update" with id, partitionKey, and updates
For delete operations: use operation="delete" with id and partitionKey

Always provide clear feedback about the operation results.
"""
    
    # Load OpenAPI specification
    with open("openapi_spec.json", "r") as f:
        openapi_spec = json.load(f)
    
    # Define OpenAPI tool with authentication
    tools = [
        {
            "type": "openapi",
            "openapi": {
                "name": "data_api",
                "spec": openapi_spec,
                "auth": {
                    "type": "api_key",
                    "security_scheme": {
                        "connection_id": "YourFunctionConnection"
                    }
                }
            }
        }
    ]
    
    try:
        # Initialize client
        credential = DefaultAzureCredential()
        client = AIProjectClient(
            endpoint=connection_string,
            credential=credential
        )
        
        print(f"\nCreating agent: {agent_name}")
        print(f"Model: {model_name}")
        print(f"Tools: OpenAPI specification (server-side execution)")
        
        # Create the agent
        agent = client.agents.create_agent(
            model=model_name,
            name=agent_name,
            instructions=agent_instructions,
            tools=tools
        )
        
        print(f"\n✅ Agent deployed successfully!")
        print(f"Agent ID: {agent.id}")
        print(f"Agent Name: {agent_name}")
        
        # Save deployment info
        deployment_info = {
            "agent_id": agent.id,
            "agent_name": agent_name,
            "deployed_at": datetime.now().isoformat(),
            "model": model_name,
            "server_side_execution": True
        }
        
        with open("deployment_info.json", "w") as f:
            json.dump(deployment_info, f, indent=2)
        
        print(f"\nDeployment info saved to deployment_info.json")
        
        print("\n" + "=" * 70)
        print("IMPORTANT: Server-side Execution Enabled")
        print("=" * 70)
        print("✓ Agent uses OpenAPI tools exclusively")
        print("✓ Azure AI Service makes HTTP calls directly")
        print("✓ No client-side function execution required")
        print("✓ Use create_and_process() for autonomous operation")
        
        return agent.id
        
    except Exception as e:
        print(f"\n❌ Deployment failed: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    # Ensure environment variables are set
    required_vars = [
        "AZURE_AI_PROJECT_CONNECTION_STRING",
        "AZURE_OPENAI_DEPLOYMENT_NAME"
    ]
    
    missing = [var for var in required_vars if not os.getenv(var)]
    if missing:
        print(f"Error: Missing environment variables: {missing}")
        print("\nSet them with:")
        for var in missing:
            print(f"export {var}='your-value'")
        exit(1)
    
    deploy_agent()
```

### Step 5.2: Deploy the Agent

```bash
# Run deployment
python deploy_agent.py
```

## Part 6: Testing and Verification

### Step 6.1: Create Test Script

Create `test_agent.py`:

```python
#!/usr/bin/env python3
"""
Test agent with server-side HTTP execution
"""

import os
import json
import time
from datetime import datetime
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential


def test_agent():
    """Test agent server-side execution."""
    
    # Load deployment info
    with open("deployment_info.json", "r") as f:
        deployment_info = json.load(f)
        agent_id = deployment_info["agent_id"]
    
    print(f"\n{'='*70}")
    print(f"TESTING SERVER-SIDE EXECUTION")
    print(f"Agent ID: {agent_id}")
    print(f"{'='*70}")
    
    # Initialize client
    credential = DefaultAzureCredential()
    client = AIProjectClient(
        endpoint=os.getenv("AZURE_AI_PROJECT_CONNECTION_STRING"),
        credential=credential
    )
    
    # Test operations
    test_cases = [
        {
            "name": "Create Operation",
            "message": "Create a new item with type 'test' and name 'Server Test'"
        },
        {
            "name": "Read Operation",
            "message": "Read all items of type 'test'"
        }
    ]
    
    for test in test_cases:
        print(f"\n{'='*50}")
        print(f"Test: {test['name']}")
        print(f"{'='*50}")
        
        try:
            # Create thread
            thread = client.agents.threads.create()
            
            # Add message
            client.agents.messages.create(
                thread_id=thread.id,
                role="user",
                content=test["message"]
            )
            
            print(f"Thread ID: {thread.id}")
            print("Executing with create_and_process()...")
            
            start_time = time.time()
            
            # Execute with server-side processing
            run = client.agents.runs.create_and_process(
                thread_id=thread.id,
                agent_id=agent_id
            )
            
            elapsed = time.time() - start_time
            print(f"\nRun completed in {elapsed:.2f} seconds")
            print(f"Status: {run.status}")
            
            if run.status == "completed":
                print("✅ SUCCESS: Server-side execution completed")
                
                # Get response
                messages = client.agents.messages.list(thread_id=thread.id)
                for msg in messages:
                    if msg.role == "assistant":
                        print(f"\nAgent response:")
                        print(f"{msg.content[0].text.value}")
                        break
                        
            elif run.status == "requires_action":
                print("❌ FAILED: Agent requires client action")
                print("This indicates the tool is not executing server-side")
                
            elif run.status == "failed":
                print(f"❌ Run failed: {run.last_error}")
            
            # Clean up
            client.agents.threads.delete(thread_id=thread.id)
            
        except Exception as e:
            print(f"Error: {e}")
        
        time.sleep(2)
    
    print(f"\n\n{'='*70}")
    print("VERIFICATION COMPLETE")
    print(f"{'='*70}")
    print("\nIf all tests show 'Server-side execution completed':")
    print("✓ Azure AI Service is making HTTP calls directly")
    print("✓ No client intervention required")
    print("✓ OpenAPI tools are working correctly")


if __name__ == "__main__":
    test_agent()
```

### Step 6.2: Run Tests

```bash
# Test the agent
python test_agent.py
```

### Step 6.3: Verify Server-Side Execution

Expected output:
```
Status: RunStatus.COMPLETED
✅ SUCCESS: Server-side execution completed
```

If you see `RunStatus.REQUIRES_ACTION`, the tool is NOT executing server-side.

## Troubleshooting

### Common Issues and Solutions

#### 1. Agent enters "requires_action" state

**Cause**: Mixed tool types or incorrect configuration

**Solution**:
- Ensure agent has ONLY OpenAPI tools (no function tools)
- Verify connection is properly created
- Check authentication configuration

#### 2. Authentication failures

**Cause**: Missing or incorrect connection

**Solution**:
```bash
# Verify connection exists
az ml connection list \
  --resource-group $AZURE_RESOURCE_GROUP \
  --workspace-name your-ai-workspace

# Recreate if needed
az ml connection delete --name YourFunctionConnection ...
az ml connection create --file connection.yml ...
```

#### 3. Function not responding

**Cause**: Function app not running or misconfigured

**Solution**:
```bash
# Check function app status
az functionapp show \
  --name your-function-app \
  --resource-group $AZURE_RESOURCE_GROUP \
  --query state

# Restart if needed
az functionapp restart \
  --name your-function-app \
  --resource-group $AZURE_RESOURCE_GROUP

# Check logs
az webapp log tail \
  --name your-function-app \
  --resource-group $AZURE_RESOURCE_GROUP
```

#### 4. Cosmos DB connection issues

**Cause**: Incorrect credentials or firewall

**Solution**:
- Verify Cosmos DB endpoint and key
- Check firewall rules allow Azure services
- Test connection directly from Function App

### Debugging Tips

1. **Enable detailed logging**:
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

2. **Inspect agent configuration**:
   ```python
   agent = client.agents.get_agent(agent_id=agent_id)
   print(json.dumps(agent.tools, indent=2))
   ```

3. **Monitor Function App logs**:
   ```bash
   func azure functionapp logstream your-function-app
   ```

4. **Test function directly**:
   ```bash
   curl -X POST https://your-function-app.azurewebsites.net/api/your-function \
     -H "x-functions-key: $FUNCTION_KEY" \
     -H "Content-Type: application/json" \
     -d '{"operation": "read"}'
   ```

## Best Practices

1. **Use environment variables** for all sensitive data
2. **Implement proper error handling** in Azure Functions
3. **Use connection pooling** for database connections
4. **Monitor performance** with Application Insights
5. **Test incrementally** - verify each component before integration
6. **Document your API** thoroughly in OpenAPI spec
7. **Use create_and_process()** for server-side execution
8. **Avoid mixing tool types** in the same agent

## Summary

This implementation enables Azure AI Agents to make direct HTTP calls to Azure Functions without client intervention. The key is using OpenAPI tools exclusively and ensuring proper authentication through Azure ML connections. The Azure AI Service handles all HTTP communication, retry logic, and error handling automatically.