"""
Azure Function for getting complete North Star summary
"""

import azure.functions as func
import json
import logging
from ..shared.cosmos_client import NorthStarCosmosClient

logger = logging.getLogger(__name__)

def main(req: func.HttpRequest) -> func.HttpResponse:
    logger.info('GetNorthStarSummary function processing request')
    
    try:
        # Parse request body
        req_body = req.get_json()
        organization_id = req_body.get('organizationId')
        
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
        
        # Build summary
        summary = {
            "organizationId": organization_id,
            "purpose": org_data['purpose']['statement'] if org_data.get('purpose') else None,
            "vision": org_data['vision']['statement'] if org_data.get('vision') else None,
            "values": [v['name'] for v in org_data.get('values', [])],
            "strategic_goals_count": len(org_data.get('strategicGoals', {})),
            "top_level_goals": [],
            "last_updated": None,
            "completeness": {
                "has_purpose": bool(org_data.get('purpose')),
                "has_vision": bool(org_data.get('vision')),
                "has_values": bool(org_data.get('values')),
                "has_goals": bool(org_data.get('strategicGoals')),
                "percentage": 0
            }
        }
        
        # Get top-level goals
        if org_data.get('strategicGoals'):
            root_goals = [g for g in org_data['strategicGoals'].values() if not g.get('parent_id')]
            summary['top_level_goals'] = [g['name'] for g in root_goals[:5]]  # Top 5 root goals
        
        # Calculate last updated
        update_times = []
        if org_data.get('purpose') and org_data['purpose'].get('updated_at'):
            update_times.append(org_data['purpose']['updated_at'])
        if org_data.get('vision') and org_data['vision'].get('updated_at'):
            update_times.append(org_data['vision']['updated_at'])
        for value in org_data.get('values', []):
            if value.get('created_at'):
                update_times.append(value['created_at'])
        for goal in org_data.get('strategicGoals', {}).values():
            if goal.get('created_at'):
                update_times.append(goal['created_at'])
            if goal.get('updated_at'):
                update_times.append(goal['updated_at'])
        
        if update_times:
            summary['last_updated'] = max(update_times)
        
        # Calculate completeness percentage
        completeness_score = sum([
            summary['completeness']['has_purpose'],
            summary['completeness']['has_vision'],
            summary['completeness']['has_values'],
            summary['completeness']['has_goals']
        ])
        summary['completeness']['percentage'] = int((completeness_score / 4) * 100)
        
        # Add insights
        insights = []
        if not summary['completeness']['has_purpose']:
            insights.append("Start by defining your organizational purpose - why do you exist?")
        elif not summary['completeness']['has_vision']:
            insights.append("Next, articulate your vision - what future are you creating?")
        elif not summary['completeness']['has_values']:
            insights.append("Define your core values to guide decision-making")
        elif not summary['completeness']['has_goals']:
            insights.append("Create strategic goals to operationalize your vision")
        elif summary['strategic_goals_count'] < 3:
            insights.append("Consider adding more strategic goals to comprehensively cover your vision")
        else:
            insights.append("Your North Star foundation is well-established. Keep it updated and aligned.")
        
        summary['insights'] = insights
        
        return func.HttpResponse(
            json.dumps(summary, indent=2),
            mimetype="application/json",
            status_code=200
        )
        
    except Exception as e:
        logger.error(f"Error in GetNorthStarSummary: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            mimetype="application/json",
            status_code=500
        )