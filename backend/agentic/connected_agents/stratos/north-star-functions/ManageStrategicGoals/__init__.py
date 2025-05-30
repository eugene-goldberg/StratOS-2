"""
Azure Function for managing strategic goals with hierarchy
"""

import azure.functions as func
import json
import logging
from datetime import datetime
from ..shared.cosmos_client import NorthStarCosmosClient
from ..shared.models import StrategicGoalModel

logger = logging.getLogger(__name__)

def main(req: func.HttpRequest) -> func.HttpResponse:
    logger.info('ManageStrategicGoals function processing request')
    
    try:
        # Parse request body
        req_body = req.get_json()
        organization_id = req_body.get('organizationId')
        action = req_body.get('action', 'list').lower()
        goal_id = req_body.get('goalId')
        goal_name = req_body.get('goalName')
        goal_description = req_body.get('goalDescription', '')
        parent_id = req_body.get('parentId')
        target_date = req_body.get('targetDate')
        
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
        
        if 'strategicGoals' not in org_data:
            org_data['strategicGoals'] = {}
        if 'goalHierarchy' not in org_data:
            org_data['goalHierarchy'] = {}
        
        if action == 'create' and goal_name:
            # Create new goal
            goal_id = goal_id or f"goal_{int(datetime.now().timestamp() * 1000)}"
            goal = {
                "id": goal_id,
                "name": goal_name,
                "description": goal_description,
                "parent_id": parent_id,
                "target_date": target_date,
                "created_at": datetime.now().isoformat(),
                "status": "active"
            }
            
            org_data['strategicGoals'][goal_id] = goal
            
            # Update hierarchy
            if parent_id:
                if parent_id not in org_data['goalHierarchy']:
                    org_data['goalHierarchy'][parent_id] = []
                org_data['goalHierarchy'][parent_id].append(goal_id)
            
            # Save to Cosmos DB
            cosmos_client.save_organization_data(org_data)
            
            response = {
                "success": True,
                "action": "create",
                "goal": goal
            }
            
        elif action == 'get' and goal_id:
            # Get specific goal
            goal = org_data['strategicGoals'].get(goal_id)
            if goal:
                # Add children to response
                children = org_data['goalHierarchy'].get(goal_id, [])
                goal_with_children = goal.copy()
                goal_with_children["children"] = children
                
                response = {
                    "success": True,
                    "action": "get",
                    "goal": goal_with_children
                }
            else:
                response = {
                    "success": False,
                    "action": "get",
                    "message": f"Goal '{goal_id}' not found"
                }
                
        elif action == 'list':
            # Build hierarchical view
            goals = org_data['strategicGoals']
            hierarchy = org_data['goalHierarchy']
            
            root_goals = [g for g in goals.values() if not g.get("parent_id")]
            
            def build_tree(goal):
                tree_goal = goal.copy()
                children_ids = hierarchy.get(goal["id"], [])
                tree_goal["children"] = [build_tree(goals[child_id]) 
                                        for child_id in children_ids 
                                        if child_id in goals]
                return tree_goal
            
            hierarchical_goals = [build_tree(g) for g in root_goals]
            
            response = {
                "success": True,
                "action": "list",
                "goals": hierarchical_goals,
                "total_count": len(goals)
            }
            
        elif action == 'update' and goal_id:
            # Update existing goal
            if goal_id in org_data['strategicGoals']:
                goal = org_data['strategicGoals'][goal_id]
                if goal_name:
                    goal['name'] = goal_name
                if goal_description is not None:
                    goal['description'] = goal_description
                if target_date is not None:
                    goal['target_date'] = target_date
                goal['updated_at'] = datetime.now().isoformat()
                
                # Save to Cosmos DB
                cosmos_client.save_organization_data(org_data)
                
                response = {
                    "success": True,
                    "action": "update",
                    "goal": goal
                }
            else:
                response = {
                    "success": False,
                    "action": "update",
                    "message": f"Goal '{goal_id}' not found"
                }
                
        elif action == 'delete' and goal_id:
            # Delete goal and update hierarchy
            if goal_id in org_data['strategicGoals']:
                # Remove from goals
                deleted_goal = org_data['strategicGoals'].pop(goal_id)
                
                # Remove from parent's children
                parent_id = deleted_goal.get('parent_id')
                if parent_id and parent_id in org_data['goalHierarchy']:
                    org_data['goalHierarchy'][parent_id] = [
                        cid for cid in org_data['goalHierarchy'][parent_id] if cid != goal_id
                    ]
                
                # Handle orphaned children
                if goal_id in org_data['goalHierarchy']:
                    orphaned_children = org_data['goalHierarchy'].pop(goal_id)
                    # Make orphaned children root goals
                    for child_id in orphaned_children:
                        if child_id in org_data['strategicGoals']:
                            org_data['strategicGoals'][child_id]['parent_id'] = None
                
                # Save to Cosmos DB
                cosmos_client.save_organization_data(org_data)
                
                response = {
                    "success": True,
                    "action": "delete",
                    "message": f"Goal '{goal_id}' deleted successfully"
                }
            else:
                response = {
                    "success": False,
                    "action": "delete",
                    "message": f"Goal '{goal_id}' not found"
                }
        
        else:
            response = {
                "success": False,
                "error": "Invalid action or missing required parameters"
            }
        
        return func.HttpResponse(
            json.dumps(response, indent=2),
            mimetype="application/json",
            status_code=200
        )
        
    except Exception as e:
        logger.error(f"Error in ManageStrategicGoals: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            mimetype="application/json",
            status_code=500
        )