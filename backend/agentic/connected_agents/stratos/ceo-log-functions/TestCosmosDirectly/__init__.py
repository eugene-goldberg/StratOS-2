"""Test Cosmos DB directly without proxies"""
import json
import logging
import os
import azure.functions as func
from azure.cosmos import CosmosClient

def main(req: func.HttpRequest) -> func.HttpResponse:
    """Test direct Cosmos connection"""
    logging.info('Testing direct Cosmos connection')
    
    result = {
        "connection": False,
        "database": False,
        "container": False,
        "write": False,
        "read": False,
        "error": None
    }
    
    try:
        # Direct connection without any wrappers
        endpoint = os.environ.get("COSMOS_DB_ENDPOINT")
        key = os.environ.get("COSMOS_DB_KEY")
        
        if not endpoint or not key:
            result["error"] = "Missing credentials"
            return func.HttpResponse(json.dumps(result), status_code=500)
        
        # Create client without proxy
        client = CosmosClient(endpoint, key, connection_verify=False)
        result["connection"] = True
        
        # Get database
        database = client.get_database_client("StratOSData")
        database.read()
        result["database"] = True
        
        # Get container
        container = database.get_container_client("CEOLogs")
        container.read()
        result["container"] = True
        
        # Try to write
        test_item = {
            "id": "test-item-direct",
            "userId": "test-user",
            "type": "test",
            "content": "Direct test"
        }
        
        created = container.upsert_item(body=test_item)
        result["write"] = True
        
        # Try to read
        read_item = container.read_item(item="test-item-direct", partition_key="test-user")
        result["read"] = True
        
        # Clean up
        container.delete_item(item="test-item-direct", partition_key="test-user")
        
        result["success"] = True
        
    except Exception as e:
        result["error"] = str(e)
        result["error_type"] = type(e).__name__
        logging.error(f"Direct test failed: {str(e)}")
    
    return func.HttpResponse(
        json.dumps(result, indent=2),
        mimetype="application/json",
        status_code=200 if result.get("success") else 500
    )