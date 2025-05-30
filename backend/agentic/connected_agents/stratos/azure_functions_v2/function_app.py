import azure.functions as func
import logging
import json
import os
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

from azure.cosmos import CosmosClient
from azure.cosmos.exceptions import CosmosHttpResponseError

# Using v2 Python programming model
app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

# Cosmos DB configuration
COSMOS_ENDPOINT = os.environ.get("COSMOS_ENDPOINT", "https://stratos-ceo-logs-db.documents.azure.com:443/")
COSMOS_KEY = os.environ.get("COSMOS_KEY")
DATABASE_NAME = os.environ.get("COSMOS_DATABASE_NAME", "StratOSData")
CONTAINER_NAME = "NorthStar"

# Global Cosmos client (singleton pattern)
cosmos_client = None
container = None


def get_cosmos_container():
    """Get or create Cosmos container for North Star data."""
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
                partition_key={"paths": ["/organizationId"], "kind": "Hash"}
            )
            logging.info(f"Created new container: {CONTAINER_NAME}")
    
    return container


def get_or_create_organization(container, org_id: str) -> dict:
    """Get existing organization data or create new with defaults."""
    try:
        item = container.read_item(item=org_id, partition_key=org_id)
        return item
    except:
        # Create new organization with default structure
        new_org = {
            "id": org_id,
            "organizationId": org_id,
            "purpose": {"statement": "", "lastUpdated": None},
            "vision": {"statement": "", "lastUpdated": None},
            "values": [],
            "strategicGoals": [],
            "createdAt": datetime.now(timezone.utc).isoformat(),
            "lastUpdated": datetime.now(timezone.utc).isoformat()
        }
        container.create_item(body=new_org)
        return new_org


@app.route(route="north-star-operations", methods=["POST"])
def north_star_operations(req: func.HttpRequest) -> func.HttpResponse:
    """Main endpoint for all North Star operations."""
    logging.info('Processing North Star operation request')
    
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
        
        # Route to appropriate handler
        if operation == "managePurpose":
            result = handle_manage_purpose(req_body, container)
        elif operation == "manageVision":
            result = handle_manage_vision(req_body, container)
        elif operation == "manageValues":
            result = handle_manage_values(req_body, container)
        elif operation == "manageStrategicGoals":
            result = handle_manage_strategic_goals(req_body, container)
        elif operation == "validateAlignment":
            result = handle_validate_alignment(req_body, container)
        elif operation == "getNorthStarSummary":
            result = handle_get_summary(req_body, container)
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


def handle_manage_purpose(req_body: dict, container) -> dict:
    """Handle purpose management operations."""
    org_id = req_body.get('organizationId')
    action = req_body.get('action', 'get')
    
    if not org_id:
        return {"error": "Missing organizationId"}
    
    org_data = get_or_create_organization(container, org_id)
    
    if action == 'set':
        purpose = req_body.get('purpose')
        if not purpose:
            return {"error": "Missing purpose for set action"}
        
        org_data['purpose'] = {
            "statement": purpose,
            "lastUpdated": datetime.now(timezone.utc).isoformat()
        }
        org_data['lastUpdated'] = datetime.now(timezone.utc).isoformat()
        
        container.upsert_item(body=org_data)
        
        return {
            "success": True,
            "organizationId": org_id,
            "purpose": org_data['purpose']
        }
    else:  # get
        return {
            "success": True,
            "organizationId": org_id,
            "purpose": org_data['purpose']
        }


def handle_manage_vision(req_body: dict, container) -> dict:
    """Handle vision management operations."""
    org_id = req_body.get('organizationId')
    action = req_body.get('action', 'get')
    
    if not org_id:
        return {"error": "Missing organizationId"}
    
    org_data = get_or_create_organization(container, org_id)
    
    if action == 'set':
        vision = req_body.get('vision')
        if not vision:
            return {"error": "Missing vision for set action"}
        
        org_data['vision'] = {
            "statement": vision,
            "lastUpdated": datetime.now(timezone.utc).isoformat()
        }
        org_data['lastUpdated'] = datetime.now(timezone.utc).isoformat()
        
        container.upsert_item(body=org_data)
        
        return {
            "success": True,
            "organizationId": org_id,
            "vision": org_data['vision']
        }
    else:  # get
        return {
            "success": True,
            "organizationId": org_id,
            "vision": org_data['vision']
        }


def handle_manage_values(req_body: dict, container) -> dict:
    """Handle values management operations."""
    org_id = req_body.get('organizationId')
    action = req_body.get('action', 'list')
    
    if not org_id:
        return {"error": "Missing organizationId"}
    
    org_data = get_or_create_organization(container, org_id)
    
    if action == 'add':
        value_name = req_body.get('value')
        description = req_body.get('description', '')
        
        if not value_name:
            return {"error": "Missing value name for add action"}
        
        # Check if value already exists
        existing_values = [v['name'] for v in org_data.get('values', [])]
        if value_name in existing_values:
            return {"error": f"Value '{value_name}' already exists"}
        
        new_value = {
            "name": value_name,
            "description": description,
            "createdAt": datetime.now(timezone.utc).isoformat()
        }
        
        org_data['values'].append(new_value)
        org_data['lastUpdated'] = datetime.now(timezone.utc).isoformat()
        
        container.upsert_item(body=org_data)
        
        return {
            "success": True,
            "organizationId": org_id,
            "value": new_value,
            "totalValues": len(org_data['values'])
        }
        
    elif action == 'remove':
        value_name = req_body.get('value')
        
        if not value_name:
            return {"error": "Missing value name for remove action"}
        
        org_data['values'] = [v for v in org_data['values'] if v['name'] != value_name]
        org_data['lastUpdated'] = datetime.now(timezone.utc).isoformat()
        
        container.upsert_item(body=org_data)
        
        return {
            "success": True,
            "organizationId": org_id,
            "removed": value_name,
            "remainingValues": len(org_data['values'])
        }
        
    else:  # list
        return {
            "success": True,
            "organizationId": org_id,
            "values": org_data.get('values', []),
            "count": len(org_data.get('values', []))
        }


def handle_manage_strategic_goals(req_body: dict, container) -> dict:
    """Handle strategic goals management operations."""
    org_id = req_body.get('organizationId')
    action = req_body.get('action', 'list')
    
    if not org_id:
        return {"error": "Missing organizationId"}
    
    org_data = get_or_create_organization(container, org_id)
    
    if action == 'create':
        title = req_body.get('title')
        if not title:
            return {"error": "Missing title for create action"}
        
        new_goal = {
            "id": f"goal_{int(time.time() * 1000)}",
            "title": title,
            "description": req_body.get('description', ''),
            "parentId": req_body.get('parentId'),
            "timeframe": req_body.get('timeframe', ''),
            "metrics": req_body.get('metrics', []),
            "status": "active",
            "createdAt": datetime.now(timezone.utc).isoformat(),
            "lastUpdated": datetime.now(timezone.utc).isoformat()
        }
        
        org_data['strategicGoals'].append(new_goal)
        org_data['lastUpdated'] = datetime.now(timezone.utc).isoformat()
        
        container.upsert_item(body=org_data)
        
        return {
            "success": True,
            "organizationId": org_id,
            "goal": new_goal
        }
        
    elif action == 'update':
        goal_id = req_body.get('goalId')
        if not goal_id:
            return {"error": "Missing goalId for update action"}
        
        # Find and update goal
        for goal in org_data['strategicGoals']:
            if goal['id'] == goal_id:
                if 'title' in req_body:
                    goal['title'] = req_body['title']
                if 'description' in req_body:
                    goal['description'] = req_body['description']
                if 'parentId' in req_body:
                    goal['parentId'] = req_body['parentId']
                if 'timeframe' in req_body:
                    goal['timeframe'] = req_body['timeframe']
                if 'metrics' in req_body:
                    goal['metrics'] = req_body['metrics']
                if 'status' in req_body:
                    goal['status'] = req_body['status']
                    
                goal['lastUpdated'] = datetime.now(timezone.utc).isoformat()
                org_data['lastUpdated'] = datetime.now(timezone.utc).isoformat()
                
                container.upsert_item(body=org_data)
                
                return {
                    "success": True,
                    "organizationId": org_id,
                    "goal": goal
                }
        
        return {"error": f"Goal with id '{goal_id}' not found"}
        
    elif action == 'delete':
        goal_id = req_body.get('goalId')
        if not goal_id:
            return {"error": "Missing goalId for delete action"}
        
        original_count = len(org_data['strategicGoals'])
        org_data['strategicGoals'] = [g for g in org_data['strategicGoals'] if g['id'] != goal_id]
        
        if len(org_data['strategicGoals']) < original_count:
            org_data['lastUpdated'] = datetime.now(timezone.utc).isoformat()
            container.upsert_item(body=org_data)
            
            return {
                "success": True,
                "organizationId": org_id,
                "deleted": goal_id
            }
        
        return {"error": f"Goal with id '{goal_id}' not found"}
        
    elif action == 'get':
        goal_id = req_body.get('goalId')
        if not goal_id:
            return {"error": "Missing goalId for get action"}
        
        for goal in org_data['strategicGoals']:
            if goal['id'] == goal_id:
                return {
                    "success": True,
                    "organizationId": org_id,
                    "goal": goal
                }
        
        return {"error": f"Goal with id '{goal_id}' not found"}
        
    else:  # list
        return {
            "success": True,
            "organizationId": org_id,
            "goals": org_data.get('strategicGoals', []),
            "count": len(org_data.get('strategicGoals', []))
        }


def handle_validate_alignment(req_body: dict, container) -> dict:
    """Handle alignment validation."""
    org_id = req_body.get('organizationId')
    element_type = req_body.get('elementType')
    element_content = req_body.get('elementContent')
    
    if not all([org_id, element_type, element_content]):
        return {"error": "Missing required parameters: organizationId, elementType, elementContent"}
    
    org_data = get_or_create_organization(container, org_id)
    
    # Simple alignment scoring based on keyword matching
    alignment_score = 0.5  # Base score
    recommendations = []
    
    # Check against purpose
    if org_data['purpose']['statement']:
        purpose_words = org_data['purpose']['statement'].lower().split()
        content_words = element_content.lower().split()
        common_words = set(purpose_words) & set(content_words)
        if common_words:
            alignment_score += 0.2
        else:
            recommendations.append("Consider how this aligns with your purpose")
    
    # Check against vision
    if org_data['vision']['statement']:
        vision_words = org_data['vision']['statement'].lower().split()
        content_words = element_content.lower().split()
        common_words = set(vision_words) & set(content_words)
        if common_words:
            alignment_score += 0.2
        else:
            recommendations.append("Ensure this supports your vision")
    
    # Check against values
    if org_data['values']:
        value_names = [v['name'].lower() for v in org_data['values']]
        content_lower = element_content.lower()
        for value in value_names:
            if value in content_lower:
                alignment_score += 0.1
                break
        else:
            recommendations.append("Review alignment with organizational values")
    
    # Determine alignment level
    if alignment_score >= 0.8:
        alignment_level = "strong"
    elif alignment_score >= 0.6:
        alignment_level = "moderate"
    else:
        alignment_level = "weak"
    
    return {
        "success": True,
        "organizationId": org_id,
        "elementType": element_type,
        "alignmentScore": round(alignment_score, 2),
        "alignmentLevel": alignment_level,
        "recommendations": recommendations
    }


def handle_get_summary(req_body: dict, container) -> dict:
    """Get complete North Star summary."""
    org_id = req_body.get('organizationId')
    
    if not org_id:
        return {"error": "Missing organizationId"}
    
    org_data = get_or_create_organization(container, org_id)
    
    # Build hierarchical goal structure
    goals_by_parent = {}
    for goal in org_data.get('strategicGoals', []):
        parent_id = goal.get('parentId', 'root')
        if parent_id not in goals_by_parent:
            goals_by_parent[parent_id] = []
        goals_by_parent[parent_id].append(goal)
    
    def build_goal_tree(parent_id='root'):
        goals = goals_by_parent.get(parent_id, [])
        tree = []
        for goal in goals:
            goal_node = goal.copy()
            goal_node['children'] = build_goal_tree(goal['id'])
            tree.append(goal_node)
        return tree
    
    goal_hierarchy = build_goal_tree()
    
    return {
        "success": True,
        "organizationId": org_id,
        "northStar": {
            "purpose": org_data['purpose'],
            "vision": org_data['vision'],
            "values": org_data['values'],
            "strategicGoals": {
                "total": len(org_data.get('strategicGoals', [])),
                "hierarchy": goal_hierarchy
            }
        },
        "metadata": {
            "createdAt": org_data.get('createdAt'),
            "lastUpdated": org_data.get('lastUpdated')
        }
    }