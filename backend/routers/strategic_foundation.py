from fastapi import APIRouter, Depends, HTTPException, status
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
from ..services.strategic_foundation_service import StrategicFoundationService

router = APIRouter()
foundation_service = StrategicFoundationService()

@router.post("/north-star", response_model=NorthStar, status_code=status.HTTP_201_CREATED)
async def create_north_star(north_star_data: NorthStarCreate):
    """
    Create a new North Star (Purpose, Vision, Values, and Strategic Goals)
    """
    return await foundation_service.create_north_star(north_star_data)

@router.get("/north-star/{north_star_id}", response_model=NorthStar)
async def get_north_star(north_star_id: UUID):
    """
    Get a North Star by ID
    """
    north_star = await foundation_service.get_north_star(north_star_id)
    if not north_star:
        raise HTTPException(status_code=404, detail="North Star not found")
    return north_star

@router.put("/north-star/{north_star_id}", response_model=NorthStar)
async def update_north_star(north_star_id: UUID, update_data: NorthStarUpdate):
    """
    Update a North Star by ID
    """
    updated = await foundation_service.update_north_star(north_star_id, update_data)
    if not updated:
        raise HTTPException(status_code=404, detail="North Star not found")
    return updated

@router.post("/strategic-goals", response_model=StrategicGoal, status_code=status.HTTP_201_CREATED)
async def create_strategic_goal(goal_data: dict, north_star_id: UUID):
    """
    Add a strategic goal to a North Star
    """
    return await foundation_service.add_strategic_goal(north_star_id, goal_data)

@router.put("/strategic-goals/{goal_id}", response_model=StrategicGoal)
async def update_strategic_goal(goal_id: UUID, goal_data: dict):
    """
    Update a strategic goal
    """
    updated = await foundation_service.update_strategic_goal(goal_id, goal_data)
    if not updated:
        raise HTTPException(status_code=404, detail="Strategic goal not found")
    return updated

@router.delete("/strategic-goals/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_strategic_goal(goal_id: UUID):
    """
    Delete a strategic goal
    """
    deleted = await foundation_service.delete_strategic_goal(goal_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Strategic goal not found")
    return {"status": "success"}

@router.post("/values", response_model=Value, status_code=status.HTTP_201_CREATED)
async def create_value(value_data: dict, north_star_id: UUID):
    """
    Add a value to a North Star
    """
    return await foundation_service.add_value(north_star_id, value_data)

@router.put("/values/{value_id}", response_model=Value)
async def update_value(value_id: UUID, value_data: dict):
    """
    Update a value
    """
    updated = await foundation_service.update_value(value_id, value_data)
    if not updated:
        raise HTTPException(status_code=404, detail="Value not found")
    return updated

@router.delete("/values/{value_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_value(value_id: UUID):
    """
    Delete a value
    """
    deleted = await foundation_service.delete_value(value_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Value not found")
    return {"status": "success"}