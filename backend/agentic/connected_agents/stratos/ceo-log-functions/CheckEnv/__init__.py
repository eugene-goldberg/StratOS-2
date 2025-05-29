"""Check environment variables"""
import json
import os
import azure.functions as func

def main(req: func.HttpRequest) -> func.HttpResponse:
    """Check environment variables"""
    
    env_vars = {}
    
    # Check for proxy-related variables
    proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 'NO_PROXY', 'no_proxy']
    for var in proxy_vars:
        if var in os.environ:
            env_vars[var] = "SET (value hidden)"
    
    # Check Azure-related variables
    azure_vars = [
        'AZURE_OPENAI_ENDPOINT',
        'AZURE_OPENAI_KEY',
        'AZURE_OPENAI_DEPLOYMENT',
        'COSMOS_DB_ENDPOINT',
        'COSMOS_DB_DATABASE_ID',
        'COSMOS_DB_CONTAINER_ID'
    ]
    
    for var in azure_vars:
        if var in os.environ:
            if 'KEY' in var or 'PASSWORD' in var:
                env_vars[var] = "SET (value hidden)"
            else:
                env_vars[var] = os.environ.get(var)
    
    # Python version
    import sys
    env_vars['python_version'] = sys.version
    
    # Azure cosmos version
    try:
        import azure.cosmos
        env_vars['azure_cosmos_version'] = azure.cosmos.__version__
    except:
        env_vars['azure_cosmos_version'] = "Not available"
    
    # OpenAI version
    try:
        import openai
        env_vars['openai_version'] = openai.__version__
    except:
        env_vars['openai_version'] = "Not available"
    
    return func.HttpResponse(
        json.dumps(env_vars, indent=2),
        mimetype="application/json",
        status_code=200
    )