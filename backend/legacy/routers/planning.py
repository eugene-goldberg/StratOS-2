from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional, Dict, Any
from uuid import UUID

from ..models.user import UserResponse
from ..dependencies import get_current_active_user # get_current_user_id can be removed if UserResponse is always used
from ..models.planning import (
    StrategicPlan, StrategicPlanCreate,
    Initiative, InitiativeCreate,
    Action, ActionCreate,
    Resource, ResourceCreate, ResourceUpdate,
    ResourceAllocation, ResourceAllocationCreate, ResourceAllocationRelease,
    Risk, RiskCreate,
    PlanStatus, InitiativeType, ResourceType
)
from ..services.planning_service import PlanningService

router = APIRouter(dependencies=[Depends(get_current_active_user)])
planning_service = PlanningService()

# Strategic Plan Endpoints
@router.post("/plans", response_model=StrategicPlan, status_code=status.HTTP_201_CREATED)
async def create_strategic_plan(plan_data: StrategicPlanCreate, current_user: UserResponse = Depends(get_current_active_user)):
    return await planning_service.create_strategic_plan(current_user.id, plan_data)

@router.get("/plans/{plan_id}", response_model=StrategicPlan)
async def get_strategic_plan(plan_id: UUID, current_user: UserResponse = Depends(get_current_active_user)):
    plan = await planning_service.get_strategic_plan(plan_id, current_user.id)
    if not plan:
        raise HTTPException(status_code=404, detail="Strategic plan not found or not accessible")
    return plan

@router.get("/plans", response_model=List[StrategicPlan])
async def list_strategic_plans(
    current_user: UserResponse = Depends(get_current_active_user),
    status_filter: Optional[PlanStatus] = None, # Renamed for clarity from 'status'
    limit: int = 10,
    offset: int = 0
):
    return await planning_service.list_strategic_plans(current_user.id, status_filter, limit, offset)

@router.put("/plans/{plan_id}", response_model=StrategicPlan)
async def update_strategic_plan(plan_id: UUID, plan_data: Dict[str, Any], current_user: UserResponse = Depends(get_current_active_user)):
    updated = await planning_service.update_strategic_plan(plan_id, current_user.id, plan_data)
    if not updated:
        raise HTTPException(status_code=404, detail="Strategic plan not found or not accessible")
    return updated

@router.delete("/plans/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_strategic_plan(plan_id: UUID, current_user: UserResponse = Depends(get_current_active_user)):
    deleted = await planning_service.delete_strategic_plan(plan_id, current_user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Strategic plan not found or not accessible")
    return {"status": "success"}

# Initiative Endpoints
@router.post("/plans/{plan_id}/initiatives", response_model=Initiative, status_code=status.HTTP_201_CREATED)
async def create_initiative(plan_id: UUID, initiative_data: InitiativeCreate, current_user: UserResponse = Depends(get_current_active_user)):
    # Ensure user owns the plan before adding an initiative
    await get_strategic_plan(plan_id, current_user) 
    return await planning_service.create_initiative(plan_id, current_user.id, initiative_data)

@router.get("/initiatives/{initiative_id}", response_model=Initiative)
async def get_initiative(initiative_id: UUID, current_user: UserResponse = Depends(get_current_active_user)):
    # The service's get_initiative might need user_id if initiatives are not globally unique
    # or if direct access to an initiative requires checking ownership of its parent plan.
    initiative = await planning_service.get_initiative(initiative_id) 
    if not initiative:
        raise HTTPException(status_code=404, detail="Initiative not found")
    # Add authorization check: e.g., check if initiative.user_id == current_user.id
    # This requires Initiative model to have user_id, and service to populate it.
    if not (hasattr(initiative, 'user_id') and initiative.user_id == current_user.id):
         # Or check if plan linked to initiative is owned by user
         # plan = await planning_service.get_strategic_plan(initiative.plan_id, current_user.id)
         # if not plan: raise HTTPException(status_code=403, detail="Not authorized to access this initiative")
         pass # Placeholder for proper auth check
    return initiative

@router.put("/initiatives/{initiative_id}", response_model=Initiative)
async def update_initiative(initiative_id: UUID, initiative_data: Dict[str, Any], current_user: UserResponse = Depends(get_current_active_user)):
    updated = await planning_service.update_initiative(initiative_id, current_user.id, initiative_data)
    if not updated:
        raise HTTPException(status_code=404, detail="Initiative not found or not accessible")
    return updated

@router.delete("/initiatives/{initiative_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_initiative(initiative_id: UUID, current_user: UserResponse = Depends(get_current_active_user)):
    deleted = await planning_service.delete_initiative(initiative_id, current_user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Initiative not found or not accessible")
    return {"status": "success"}

# Action Endpoints (Nested under Initiatives)
@router.post("/initiatives/{initiative_id}/actions", response_model=Action, status_code=status.HTTP_201_CREATED)
async def create_action_for_initiative(initiative_id: UUID, action_data: ActionCreate, current_user: UserResponse = Depends(get_current_active_user)):
    return await planning_service.create_action(initiative_id, current_user.id, action_data)

@router.put("/initiatives/{initiative_id}/actions/{action_id}", response_model=Action)
async def update_action_in_initiative(initiative_id: UUID, action_id: UUID, action_data: Dict[str, Any], current_user: UserResponse = Depends(get_current_active_user)):
    updated = await planning_service.update_action(initiative_id, current_user.id, action_id, action_data)
    if not updated:
        raise HTTPException(status_code=404, detail="Action not found or not accessible")
    return updated

@router.delete("/initiatives/{initiative_id}/actions/{action_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_action_from_initiative(initiative_id: UUID, action_id: UUID, current_user: UserResponse = Depends(get_current_active_user)):
    deleted = await planning_service.delete_action(initiative_id, current_user.id, action_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Action not found or not accessible")
    return {"status": "success"}

# Resource Endpoints (Nested under Initiatives)
@router.post("/initiatives/{initiative_id}/resources", response_model=Resource, status_code=status.HTTP_201_CREATED)
async def create_resource_for_initiative(initiative_id: UUID, resource_data: ResourceCreate, current_user: UserResponse = Depends(get_current_active_user)):
    return await planning_service.create_resource(initiative_id, current_user.id, resource_data)

@router.put("/initiatives/{initiative_id}/resources/{resource_id}", response_model=Resource)
async def update_resource_in_initiative(initiative_id: UUID, resource_id: UUID, resource_data: ResourceUpdate, current_user: UserResponse = Depends(get_current_active_user)):
    updated = await planning_service.update_resource(initiative_id, current_user.id, resource_id, resource_data)
    if not updated:
        raise HTTPException(status_code=404, detail="Resource not found or not accessible")
    return updated

@router.delete("/initiatives/{initiative_id}/resources/{resource_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_resource_from_initiative(initiative_id: UUID, resource_id: UUID, current_user: UserResponse = Depends(get_current_active_user)):
    deleted = await planning_service.delete_resource(initiative_id, current_user.id, resource_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Resource not found or not accessible")
    return {"status": "success"}

# Risk Endpoints (Nested under Initiatives)
@router.post("/initiatives/{initiative_id}/risks", response_model=Risk, status_code=status.HTTP_201_CREATED)
async def create_risk_for_initiative(initiative_id: UUID, risk_data: RiskCreate, current_user: UserResponse = Depends(get_current_active_user)):
    return await planning_service.create_risk(initiative_id, current_user.id, risk_data)

# AI-Powered Planning Endpoints
@router.post("/plans/{plan_id}/analyze-alignment", response_model=Dict[str, Any])
async def analyze_plan_alignment(plan_id: UUID, current_user: UserResponse = Depends(get_current_active_user)):
    return await planning_service.analyze_plan_alignment(plan_id, current_user.id)

@router.post("/plans/generate-variants", response_model=List[StrategicPlan])
async def generate_plan_variants(
    base_plan_id: UUID,
    current_user: UserResponse = Depends(get_current_active_user),
    num_variants: int = 2,
    focus_areas: Optional[List[str]] = None
):
    return await planning_service.generate_plan_variants(base_plan_id, current_user.id, num_variants, focus_areas)

@router.post("/plans/compare", response_model=Dict[str, Any])
async def compare_plans(
    plan_ids: List[UUID], 
    current_user: UserResponse = Depends(get_current_active_user),
    comparison_criteria: Optional[Dict[str, float]] = None
):
    if len(plan_ids) < 2:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="At least two plans are required for comparison")
    return await planning_service.compare_plans(plan_ids, current_user.id, comparison_criteria)

@router.post("/initiatives/{initiative_id}/generate-actions", response_model=List[Action])
async def generate_actions_for_initiative(initiative_id: UUID, current_user: UserResponse = Depends(get_current_active_user)):
    return await planning_service.generate_actions(initiative_id, current_user.id)

# Advanced Resource Tracking Endpoints
@router.post("/resources/allocate", response_model=ResourceAllocation, status_code=status.HTTP_201_CREATED)
async def allocate_resource(allocation_data: ResourceAllocationCreate, current_user: UserResponse = Depends(get_current_active_user)):
    return await planning_service.allocate_resource(current_user.id, allocation_data)

@router.post("/resources/release", status_code=status.HTTP_204_NO_CONTENT)
async def release_resource_allocation(release_data: ResourceAllocationRelease, current_user: UserResponse = Depends(get_current_active_user)):
    released = await planning_service.release_resource_allocation(current_user.id, release_data)
    if not released:
        raise HTTPException(status_code=404, detail="Allocation not found or could not be released")
    return {"status": "success"}

@router.get("/resources/utilization", response_model=Dict[str, Any])
async def get_resource_utilization(
    current_user: UserResponse = Depends(get_current_active_user),
    resource_type: Optional[ResourceType] = None
):
    return await planning_service.get_resource_utilization(current_user.id, resource_type)

@router.get("/initiatives/{initiative_id}/resource-conflicts", response_model=List[Dict[str, Any]])
async def check_resource_conflicts(initiative_id: UUID, current_user: UserResponse = Depends(get_current_active_user)):
    return await planning_service.check_resource_conflicts(current_user.id, initiative_id)
