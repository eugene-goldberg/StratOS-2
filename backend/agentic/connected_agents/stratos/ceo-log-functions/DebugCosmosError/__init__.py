"""Debug the CosmosClient proxy error"""
import json
import logging
import os
import sys
import azure.functions as func

def main(req: func.HttpRequest) -> func.HttpResponse:
    """Debug cosmos error"""
    logging.info('Debugging Cosmos error')
    
    result = {
        "proxy_vars": {},
        "sys_modules": [],
        "direct_test": False,
        "shared_import": False,
        "error": None
    }
    
    # Check proxy vars
    proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 'NO_PROXY', 'no_proxy']
    for var in proxy_vars:
        if var in os.environ:
            result["proxy_vars"][var] = os.environ.get(var)
    
    # Check loaded modules
    cosmos_modules = [mod for mod in sys.modules.keys() if 'cosmos' in mod or 'azure' in mod]
    result["sys_modules"] = cosmos_modules[:10]  # First 10
    
    # Test direct client
    try:
        from azure.cosmos import CosmosClient
        endpoint = os.environ.get("COSMOS_DB_ENDPOINT")
        key = os.environ.get("COSMOS_DB_KEY")
        
        # Try direct without connection_verify
        client1 = CosmosClient(endpoint, key, connection_verify=False)
        result["direct_test"] = True
        
    except Exception as e:
        result["direct_error"] = f"{type(e).__name__}: {str(e)}"
    
    # Test import from shared
    try:
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from shared.cosmos_client import get_cosmos_client
        
        # See what happens when we call it
        client = get_cosmos_client()
        result["shared_import"] = True
        
    except Exception as e:
        result["shared_error"] = f"{type(e).__name__}: {str(e)}"
        import traceback
        result["shared_traceback"] = traceback.format_exc()
    
    return func.HttpResponse(
        json.dumps(result, indent=2),
        mimetype="application/json",
        status_code=200
    )