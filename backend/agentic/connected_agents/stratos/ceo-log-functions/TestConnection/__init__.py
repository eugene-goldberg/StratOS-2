import logging
import os
import json
import azure.functions as func
from azure.cosmos import CosmosClient, exceptions

def main(req: func.HttpRequest) -> func.HttpResponse:
    """Test Cosmos DB connection and configuration"""
    logging.info('Testing Cosmos DB connection')
    
    results = {
        "env_vars": {},
        "cosmos_connection": False,
        "database_exists": False,
        "containers": [],
        "error": None
    }
    
    # Check environment variables
    env_vars = [
        "COSMOS_DB_ENDPOINT", "COSMOS_DB_KEY", "COSMOS_DB_DATABASE_ID",
        "COSMOS_DB_CONTAINER_ID", "COSMOS_DB_ANALYTICS_CONTAINER_ID",
        "AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_KEY", "AZURE_OPENAI_DEPLOYMENT"
    ]
    
    for var in env_vars:
        value = os.environ.get(var)
        results["env_vars"][var] = "SET" if value else "NOT SET"
        if var == "COSMOS_DB_ENDPOINT" and value:
            results["env_vars"][var] = value  # Show endpoint for debugging
    
    # Try to connect to Cosmos DB
    try:
        endpoint = os.environ.get("COSMOS_DB_ENDPOINT")
        key = os.environ.get("COSMOS_DB_KEY")
        database_id = os.environ.get("COSMOS_DB_DATABASE_ID", "StratOSData")
        
        if endpoint and key:
            client = CosmosClient(endpoint, key)
            results["cosmos_connection"] = True
            
            # Check database
            try:
                database = client.get_database_client(database_id)
                database.read()
                results["database_exists"] = True
                
                # List containers
                for container in database.list_containers():
                    results["containers"].append(container['id'])
                    
            except exceptions.CosmosResourceNotFoundError:
                results["error"] = f"Database '{database_id}' not found"
                
        else:
            results["error"] = "Missing COSMOS_DB_ENDPOINT or COSMOS_DB_KEY"
            
    except Exception as e:
        results["error"] = str(e)
        logging.error(f"Connection test failed: {str(e)}")
    
    return func.HttpResponse(
        json.dumps(results, indent=2),
        mimetype="application/json",
        status_code=200
    )