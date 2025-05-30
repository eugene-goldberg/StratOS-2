"""
Azure Function for managing organizational values
"""

import azure.functions as func
import json
import logging
from datetime import datetime
from ..shared.cosmos_client import NorthStarCosmosClient
from ..shared.models import ValueModel

logger = logging.getLogger(__name__)

def main(req: func.HttpRequest) -> func.HttpResponse:
    logger.info('ManageValues function processing request')
    
    try:
        # Parse request body
        req_body = req.get_json()
        organization_id = req_body.get('organizationId')
        action = req_body.get('action', 'list').lower()
        value_name = req_body.get('valueName')
        value_description = req_body.get('valueDescription', '')
        
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
        
        if action == 'add' and value_name:
            # Add new value
            value = {
                "name": value_name,
                "description": value_description,
                "created_at": datetime.now().isoformat()
            }
            
            if 'values' not in org_data:
                org_data['values'] = []
            
            org_data['values'].append(value)
            
            # Save to Cosmos DB
            cosmos_client.save_organization_data(org_data)
            
            response = {
                "success": True,
                "action": "add",
                "value": value,
                "total_values": len(org_data['values'])
            }
            
        elif action == 'remove' and value_name:
            # Remove value
            initial_count = len(org_data.get('values', []))
            org_data['values'] = [v for v in org_data.get('values', []) if v['name'] != value_name]
            removed = initial_count > len(org_data['values'])
            
            if removed:
                # Save to Cosmos DB
                cosmos_client.save_organization_data(org_data)
            
            response = {
                "success": removed,
                "action": "remove",
                "message": f"Value '{value_name}' removed" if removed else f"Value '{value_name}' not found"
            }
            
        elif action == 'list':
            values = org_data.get('values', [])
            response = {
                "success": True,
                "action": "list",
                "values": values,
                "count": len(values)
            }
        
        else:
            response = {
                "success": False,
                "error": "Invalid action. Use 'add', 'remove', or 'list'"
            }
        
        return func.HttpResponse(
            json.dumps(response, indent=2),
            mimetype="application/json",
            status_code=200
        )
        
    except Exception as e:
        logger.error(f"Error in ManageValues: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            mimetype="application/json",
            status_code=500
        )