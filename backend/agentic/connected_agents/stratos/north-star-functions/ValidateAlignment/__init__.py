"""
Azure Function for validating alignment with North Star elements
"""

import azure.functions as func
import json
import logging
from ..shared.cosmos_client import NorthStarCosmosClient
from ..shared.models import AlignmentValidationModel

logger = logging.getLogger(__name__)

def main(req: func.HttpRequest) -> func.HttpResponse:
    logger.info('ValidateAlignment function processing request')
    
    try:
        # Parse request body
        req_body = req.get_json()
        organization_id = req_body.get('organizationId')
        element_type = req_body.get('elementType')
        element_content = req_body.get('elementContent')
        
        if not organization_id or not element_type or not element_content:
            return func.HttpResponse(
                json.dumps({"error": "organizationId, elementType, and elementContent are required"}),
                mimetype="application/json",
                status_code=400
            )
        
        # Initialize Cosmos client
        cosmos_client = NorthStarCosmosClient()
        
        # Get current organization data
        org_data = cosmos_client.get_organization_data(organization_id)
        
        alignment_score = 0.0
        alignment_factors = []
        recommendations = []
        
        # Check if North Star elements exist
        has_purpose = bool(org_data.get('purpose'))
        has_vision = bool(org_data.get('vision'))
        has_values = bool(org_data.get('values'))
        has_goals = bool(org_data.get('strategicGoals'))
        
        if not has_purpose:
            recommendations.append("Define organizational purpose first")
        if not has_vision:
            recommendations.append("Define organizational vision first")
        if not has_values:
            recommendations.append("Define organizational values first")
        if not has_goals:
            recommendations.append("Create strategic goals to guide alignment")
        
        # Calculate alignment score based on available elements
        if has_purpose and has_vision:
            alignment_score = 0.5  # Base score for having fundamental elements
            alignment_factors.append("Organization has defined purpose and vision")
            
            # Check content alignment (simplified - in production would use AI)
            if element_type == "goal":
                alignment_score += 0.3
                alignment_factors.append("Goal-type elements typically align with strategic direction")
            elif element_type == "initiative":
                alignment_score += 0.2
                alignment_factors.append("Initiative supports strategic execution")
            elif element_type == "decision":
                alignment_score += 0.1
                alignment_factors.append("Decision requires careful alignment validation")
        
        # Check value alignment
        if has_values and len(org_data['values']) > 0:
            # In production, would analyze content against values
            value_names = [v['name'] for v in org_data['values'][:3]]
            if value_names:
                alignment_factors.append(f"Consider alignment with values: {', '.join(value_names)}")
                alignment_score += 0.1
        
        # Check goal alignment
        if has_goals and len(org_data['strategicGoals']) > 0:
            # In production, would find related goals
            goal_count = len(org_data['strategicGoals'])
            alignment_factors.append(f"Evaluated against {goal_count} strategic goals")
            alignment_score += 0.1
        
        # Provide specific recommendations
        if alignment_score < 0.7:
            if element_type == "goal":
                recommendations.append("Ensure goal directly supports the organizational vision")
                recommendations.append("Link goal to existing strategic goals hierarchy")
            elif element_type == "initiative":
                recommendations.append("Clarify how this initiative advances strategic goals")
                recommendations.append("Identify which values this initiative demonstrates")
            elif element_type == "decision":
                recommendations.append("Evaluate decision impact on strategic goals")
                recommendations.append("Ensure decision reflects organizational values")
        
        # Ensure score is between 0 and 1
        alignment_score = min(max(alignment_score, 0.0), 1.0)
        
        response = {
            "element_type": element_type,
            "alignment_score": round(alignment_score, 2),
            "alignment_factors": alignment_factors,
            "recommendations": recommendations,
            "is_aligned": alignment_score >= 0.7,
            "north_star_completeness": {
                "has_purpose": has_purpose,
                "has_vision": has_vision,
                "has_values": has_values,
                "has_goals": has_goals
            }
        }
        
        return func.HttpResponse(
            json.dumps(response, indent=2),
            mimetype="application/json",
            status_code=200
        )
        
    except Exception as e:
        logger.error(f"Error in ValidateAlignment: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            mimetype="application/json",
            status_code=500
        )