"""
Azure Function for managing organizational purpose
"""

import azure.functions as func
import json
import logging
from datetime import datetime
from ..shared.cosmos_client import NorthStarCosmosClient
from ..shared.models import PurposeModel

logger = logging.getLogger(__name__)

def main(req: func.HttpRequest) -> func.HttpResponse:
    logger.info('ManagePurpose function processing request')
    
    try:
        # Parse request body
        req_body = req.get_json()
        organization_id = req_body.get('organizationId')
        action = req_body.get('action', 'get').lower()
        content = req_body.get('content')
        
        if not organization_id:
            return func.HttpResponse(
                json.dumps({"error": "organizationId is required"}),
                mimetype="application/json",
                status_code=400
            )
        
        # Initialize Cosmos client
        cosmos_client = NorthStarCosmosClient()
        
        # Get current organization data
        org_data = cosmos_client.get_organization_data(organization_id)
        
        if action == 'set' and content:
            # Create or update purpose
            current_version = 0
            if org_data.get('purpose'):
                current_version = org_data['purpose'].get('version', 0)
            
            org_data['purpose'] = {
                'statement': content,
                'updated_at': datetime.now().isoformat(),
                'version': current_version + 1
            }
            
            # Save to Cosmos DB
            cosmos_client.save_organization_data(org_data)
            
            response = {
                "success": True,
                "action": "set",
                "purpose": org_data['purpose']
            }
            
        elif action == 'get':
            if org_data.get('purpose'):
                response = {
                    "success": True,
                    "action": "get",
                    "purpose": org_data['purpose']
                }
            else:
                response = {
                    "success": False,
                    "action": "get",
                    "message": "No purpose statement defined yet"
                }
        
        else:
            response = {
                "success": False,
                "error": "Invalid action. Use 'get' or 'set'"
            }
        
        return func.HttpResponse(
            json.dumps(response, indent=2),
            mimetype="application/json",
            status_code=200
        )
        
    except Exception as e:
        logger.error(f"Error in ManagePurpose: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            mimetype="application/json",
            status_code=500
        )