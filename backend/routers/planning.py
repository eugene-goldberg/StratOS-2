from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional, Dict, Any
from uuid import UUID
from ..models.planning import (
    StrategicPlan,
    StrategicPlanCreate,
    Initiative,
    InitiativeCreate,
    Action,
    ActionCreate,
    Resource,
    ResourceCreate,
    Risk,
    RiskCreate,
    PlanStatus,
    InitiativeType
)
from ..services.planning_service import PlanningService

router = APIRouter()
planning_service = PlanningService()

# Strategic Plan Endpoints

@router.post("/plans", response_model=StrategicPlan, status_code=status.HTTP_201_CREATED)
async def create_strategic_plan(plan_data: StrategicPlanCreate):
    """
    Create a new strategic plan
    """
    return await planning_service.create_strategic_plan(plan_data)

@router.get("/plans/{plan_id}", response_model=StrategicPlan)
async def get_strategic_plan(plan_id: UUID):
    """
    Get a strategic plan by ID
    """
    plan = await planning_service.get_strategic_plan(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Strategic plan not found")
    return plan

@router.get("/plans", response_model=List[StrategicPlan])
async def list_strategic_plans(
    limit: int = 10,
    offset: int = 0,
    status: Optional[PlanStatus] = None
):
    """
    List strategic plans
    """
    return await planning_service.list_strategic_plans(limit, offset, status)

@router.put("/plans/{plan_id}", response_model=StrategicPlan)
async def update_strategic_plan(plan_id: UUID, plan_data: dict):
    """
    Update a strategic plan
    """
    updated = await planning_service.update_strategic_plan(plan_id, plan_data)
    if not updated:
        raise HTTPException(status_code=404, detail="Strategic plan not found")
    return updated

@router.delete("/plans/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_strategic_plan(plan_id: UUID):
    """
    Delete a strategic plan
    """
    deleted = await planning_service.delete_strategic_plan(plan_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Strategic plan not found")
    return {"status": "success"}

# Initiative Endpoints

@router.post("/plans/{plan_id}/initiatives", response_model=Initiative, status_code=status.HTTP_201_CREATED)
async def create_initiative(plan_id: UUID, initiative_data: InitiativeCreate):
    """
    Create a new initiative for a strategic plan
    """
    return await planning_service.create_initiative(plan_id, initiative_data)

@router.get("/initiatives/{initiative_id}", response_model=Initiative)
async def get_initiative(initiative_id: UUID):
    """
    Get an initiative by ID
    """
    initiative = await planning_service.get_initiative(initiative_id)
    if not initiative:
        raise HTTPException(status_code=404, detail="Initiative not found")
    return initiative

@router.put("/initiatives/{initiative_id}", response_model=Initiative)
async def update_initiative(initiative_id: UUID, initiative_data: dict):
    """
    Update an initiative
    """
    updated = await planning_service.update_initiative(initiative_id, initiative_data)
    if not updated:
        raise HTTPException(status_code=404, detail="Initiative not found")
    return updated

@router.delete("/initiatives/{initiative_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_initiative(initiative_id: UUID):
    """
    Delete an initiative
    """
    deleted = await planning_service.delete_initiative(initiative_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Initiative not found")
    return {"status": "success"}

# Action Endpoints

@router.post("/initiatives/{initiative_id}/actions", response_model=Action, status_code=status.HTTP_201_CREATED)
async def create_action(initiative_id: UUID, action_data: ActionCreate):
    """
    Create a new action for an initiative
    """
    return await planning_service.create_action(initiative_id, action_data)

@router.put("/actions/{action_id}", response_model=Action)
async def update_action(action_id: UUID, action_data: dict):
    """
    Update an action
    """
    updated = await planning_service.update_action(action_id, action_data)
    if not updated:
        raise HTTPException(status_code=404, detail="Action not found")
    return updated

@router.delete("/actions/{action_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_action(action_id: UUID):
    """
    Delete an action
    """
    deleted = await planning_service.delete_action(action_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Action not found")
    return {"status": "success"}

# Resource Endpoints

@router.post("/initiatives/{initiative_id}/resources", response_model=Resource, status_code=status.HTTP_201_CREATED)
async def create_resource(initiative_id: UUID, resource_data: ResourceCreate):
    """
    Create a new resource for an initiative
    """
    return await planning_service.create_resource(initiative_id, resource_data)

# Risk Endpoints

@router.post("/initiatives/{initiative_id}/risks", response_model=Risk, status_code=status.HTTP_201_CREATED)
async def create_risk(initiative_id: UUID, risk_data: RiskCreate):
    """
    Create a new risk for an initiative
    """
    return await planning_service.create_risk(initiative_id, risk_data)

# AI-Powered Planning Endpoints

# Analyze strategic plan alignment with company goals
@router.post("/plans/{plan_id}/analyze-alignment", response_model=Dict[str, Any])
async def analyze_plan_alignment(plan_id: UUID):
    """
    Analyze a strategic plan's alignment with the company's WHY and strategic goals
    """
    return await planning_service.analyze_plan_alignment(plan_id)

@router.post("/plans/generate-variants", response_model=List[StrategicPlan])
async def generate_plan_variants(
    base_plan_id: UUID,
    num_variants: int = 2,
    focus_areas: Optional[List[str]] = None
):
    """
    Generate variants of a strategic plan with different approaches
    """
    return await planning_service.generate_plan_variants(base_plan_id, num_variants, focus_areas)

@router.post("/plans/compare", response_model=Dict[str, Any])
async def compare_plans(plan_ids: List[UUID], comparison_criteria: Optional[Dict[str, float]] = None):
    """
    Compare multiple strategic plans across various criteria
    """
    if len(plan_ids) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least two plans are required for comparison"
        )
    
    return await planning_service.compare_plans(plan_ids, comparison_criteria)

@router.post("/initiatives/generate-actions", response_model=List[Action])
async def generate_actions_for_initiative(initiative_id: UUID):
    """
    Generate recommended actions for an initiative
    """
    return await planning_service.generate_actions(initiative_id)