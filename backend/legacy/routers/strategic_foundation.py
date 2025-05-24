from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from uuid import UUID
from ..models.strategic_foundation import (
    NorthStar, 
    NorthStarCreate, 
    NorthStarUpdate, 
    Purpose, 
    Vision, 
    Value, 
    StrategicGoal
)
from ..models.user import UserResponse
from ..services.strategic_foundation_service import StrategicFoundationService
from ..dependencies import get_current_user_id, get_current_active_user

router = APIRouter()
foundation_service = StrategicFoundationService()

@router.post("/north-star", response_model=NorthStar, status_code=status.HTTP_201_CREATED)
async def create_north_star(
    north_star_data: NorthStarCreate, 
    current_user: UserResponse = Depends(get_current_active_user)
):
    """
    Create a new North Star (Purpose, Vision, Values, and Strategic Goals)
    """
    return await foundation_service.create_north_star(north_star_data, current_user.id)

@router.get("/north-star", response_model=NorthStar)
async def get_current_north_star(
    current_user: UserResponse = Depends(get_current_active_user)
):
    """
    Get the current user's North Star
    """
    north_star = await foundation_service.get_north_star(current_user.id)
    if not north_star:
        raise HTTPException(status_code=404, detail="North Star not found")
    return north_star

@router.get("/north-star/{north_star_id}", response_model=NorthStar)
async def get_north_star(
    north_star_id: UUID,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """
    Get a North Star by ID (for admin or sharing purposes)
    """
    # For MVP, users can only access their own North Star
    # In future, could implement sharing or admin access
    if north_star_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied to this North Star")
    
    north_star = await foundation_service.get_north_star(north_star_id)
    if not north_star:
        raise HTTPException(status_code=404, detail="North Star not found")
    return north_star

@router.put("/north-star", response_model=NorthStar)
async def update_current_north_star(
    update_data: NorthStarUpdate,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """
    Update the current user's North Star
    """
    updated = await foundation_service.update_north_star(current_user.id, update_data)
    if not updated:
        raise HTTPException(status_code=404, detail="North Star not found")
    return updated

@router.put("/north-star/{north_star_id}", response_model=NorthStar)
async def update_north_star(
    north_star_id: UUID, 
    update_data: NorthStarUpdate,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """
    Update a North Star by ID (for admin purposes)
    """
    # For MVP, users can only update their own North Star
    if north_star_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied to this North Star")
        
    updated = await foundation_service.update_north_star(north_star_id, update_data)
    if not updated:
        raise HTTPException(status_code=404, detail="North Star not found")
    return updated

@router.post("/north-star/strategic-goals", response_model=StrategicGoal, status_code=status.HTTP_201_CREATED)
async def create_strategic_goal(
    goal_data: dict,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """
    Add a strategic goal to the current user's North Star
    """
    return await foundation_service.add_strategic_goal(current_user.id, goal_data)

@router.get("/north-star/strategic-goals", response_model=List[StrategicGoal])
async def list_strategic_goals(
    hierarchical: bool = Query(False, description="Return goals in hierarchical structure"),
    current_user: UserResponse = Depends(get_current_active_user)
):
    """
    List all strategic goals for the current user's North Star.
    
    Args:
        hierarchical: If True, returns only top-level goals with sub-goals nested.
                     If False, returns flat list of all goals.
    """
    return await foundation_service.list_strategic_goals(current_user.id, hierarchical)

@router.get("/north-star/strategic-goals/{goal_id}", response_model=StrategicGoal)
async def get_strategic_goal(
    goal_id: UUID,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """
    Get a specific strategic goal from the current user's North Star
    """
    goal = await foundation_service.get_strategic_goal(current_user.id, goal_id)
    if not goal:
        raise HTTPException(status_code=404, detail="Strategic goal not found")
    return goal

@router.get("/north-star/strategic-goals/{goal_id}/sub-goals", response_model=List[StrategicGoal])
async def get_sub_goals(
    goal_id: UUID,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """
    Get all direct sub-goals of a specific strategic goal
    """
    return await foundation_service.get_sub_goals(current_user.id, goal_id)

@router.put("/north-star/strategic-goals/{goal_id}", response_model=StrategicGoal)
async def update_strategic_goal(
    goal_id: UUID,
    goal_data: dict,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """
    Update a strategic goal in the current user's North Star
    """
    updated = await foundation_service.update_strategic_goal(current_user.id, goal_id, goal_data)
    if not updated:
        raise HTTPException(status_code=404, detail="Strategic goal not found")
    return updated

@router.delete("/north-star/strategic-goals/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_strategic_goal(
    goal_id: UUID,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """
    Delete a strategic goal from the current user's North Star
    """
    deleted = await foundation_service.delete_strategic_goal(current_user.id, goal_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Strategic goal not found")
    return {"status": "success"}

@router.post("/north-star/values", response_model=Value, status_code=status.HTTP_201_CREATED)
async def create_value(
    value_data: dict,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """
    Add a value to the current user's North Star
    """
    return await foundation_service.add_value(current_user.id, value_data)

@router.get("/north-star/values", response_model=List[Value])
async def list_values(
    current_user: UserResponse = Depends(get_current_active_user)
):
    """
    List all values for the current user's North Star
    """
    return await foundation_service.list_values(current_user.id)

@router.get("/north-star/values/{value_id}", response_model=Value)
async def get_value(
    value_id: UUID,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """
    Get a specific value from the current user's North Star
    """
    value = await foundation_service.get_value(current_user.id, value_id)
    if not value:
        raise HTTPException(status_code=404, detail="Value not found")
    return value

@router.put("/north-star/values/{value_id}", response_model=Value)
async def update_value(
    value_id: UUID,
    value_data: dict,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """
    Update a value in the current user's North Star
    """
    updated = await foundation_service.update_value(current_user.id, value_id, value_data)
    if not updated:
        raise HTTPException(status_code=404, detail="Value not found")
    return updated

@router.delete("/north-star/values/{value_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_value(
    value_id: UUID,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """
    Delete a value from the current user's North Star
    """
    deleted = await foundation_service.delete_value(current_user.id, value_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Value not found")
    return {"status": "success"}