import pytest
import pytest_asyncio
from uuid import uuid4, UUID
from fastapi import HTTPException

from backend.services.strategic_foundation_service import StrategicFoundationService
from backend.models.strategic_foundation import (
    NorthStarCreate, 
    NorthStarUpdate,
    Purpose, Vision, Value, StrategicGoal # For type checking and direct creation in tests
)

@pytest_asyncio.fixture
async def foundation_service():
    service = StrategicFoundationService()
    # Ensure in-memory cache is used for tests
    service.cosmos_db_available = False
    service.north_stars_cache = {} # Reset cache for each test
    return service

@pytest.mark.asyncio
async def test_create_north_star_success(foundation_service: StrategicFoundationService):
    user_id = uuid4()
    north_star_data = NorthStarCreate(
        purpose="To innovate boldly.",
        purpose_description="Driving change through innovation.",
        vision="To be the #1 innovator.",
        vision_description="Leading the market by 2030.",
        vision_time_horizon="2030",
        values=[{"name": "Innovation", "description": "Always innovate."}],
        strategic_goals=[{"title": "Launch Product X", "description": "Launch by Q4."}]
    )
    
    created_ns = await foundation_service.create_north_star(north_star_data, user_id)
    
    assert created_ns is not None
    assert created_ns.id == user_id
    assert created_ns.purpose.statement == north_star_data.purpose
    assert len(created_ns.values) == 1
    assert created_ns.values[0].name == "Innovation"
    assert len(created_ns.strategic_goals) == 1
    assert created_ns.strategic_goals[0].title == "Launch Product X"
    
    # Verify in cache
    assert str(user_id) in foundation_service.north_stars_cache

@pytest.mark.asyncio
async def test_create_north_star_already_exists(foundation_service: StrategicFoundationService):
    user_id = uuid4()
    north_star_data = NorthStarCreate(purpose="Initial purpose", vision="Initial vision")
    await foundation_service.create_north_star(north_star_data, user_id)
    
    with pytest.raises(HTTPException) as exc_info:
        await foundation_service.create_north_star(north_star_data, user_id)
    assert exc_info.value.status_code == 400
    assert "already exists" in exc_info.value.detail

@pytest.mark.asyncio
async def test_get_north_star_success(foundation_service: StrategicFoundationService):
    user_id = uuid4()
    north_star_data = NorthStarCreate(purpose="Test purpose", vision="Test vision")
    await foundation_service.create_north_star(north_star_data, user_id)
    
    fetched_ns = await foundation_service.get_north_star(user_id)
    assert fetched_ns is not None
    assert fetched_ns.id == user_id
    assert fetched_ns.purpose.statement == "Test purpose"

@pytest.mark.asyncio
async def test_get_north_star_not_found(foundation_service: StrategicFoundationService):
    user_id = uuid4()
    fetched_ns = await foundation_service.get_north_star(user_id)
    assert fetched_ns is None

@pytest.mark.asyncio
async def test_update_north_star_purpose_vision(foundation_service: StrategicFoundationService):
    user_id = uuid4()
    initial_data = NorthStarCreate(purpose="Old Purpose", vision="Old Vision")
    await foundation_service.create_north_star(initial_data, user_id)
    
    update_data = NorthStarUpdate(purpose="New Purpose", vision_description="New Vision Description")
    updated_ns = await foundation_service.update_north_star(user_id, update_data)
    
    assert updated_ns is not None
    assert updated_ns.purpose.statement == "New Purpose"
    assert updated_ns.vision.statement == "Old Vision" # Original vision statement
    assert updated_ns.vision.description == "New Vision Description"
    assert updated_ns.updated_at > updated_ns.created_at

@pytest.mark.asyncio
async def test_manage_values(foundation_service: StrategicFoundationService):
    user_id = uuid4()
    ns_data = NorthStarCreate(purpose="P", vision="V")
    await foundation_service.create_north_star(ns_data, user_id)
    
    # Add value
    value_data = {"name": "Integrity", "description": "Be honest."}
    added_value = await foundation_service.add_value(user_id, value_data)
    assert added_value.name == "Integrity"
    
    north_star = await foundation_service.get_north_star(user_id)
    assert len(north_star.values) == 1
    value_id = north_star.values[0].id
    
    # Update value
    updated_value_data = {"name": "True Integrity", "description": "Always be honest."}
    updated_value = await foundation_service.update_value(user_id, value_id, updated_value_data)
    assert updated_value.name == "True Integrity"
    assert updated_value.description == "Always be honest."
    
    north_star = await foundation_service.get_north_star(user_id)
    assert north_star.values[0].name == "True Integrity"
    
    # List values
    values_list = await foundation_service.list_values(user_id)
    assert len(values_list) == 1
    assert values_list[0].name == "True Integrity"

    # Get specific value
    specific_value = await foundation_service.get_value(user_id, value_id)
    assert specific_value is not None
    assert specific_value.name == "True Integrity"

    # Delete value
    delete_success = await foundation_service.delete_value(user_id, value_id)
    assert delete_success is True
    north_star = await foundation_service.get_north_star(user_id)
    assert len(north_star.values) == 0

@pytest.mark.asyncio
async def test_manage_strategic_goals(foundation_service: StrategicFoundationService):
    user_id = uuid4()
    ns_data = NorthStarCreate(purpose="P", vision="V")
    await foundation_service.create_north_star(ns_data, user_id)
    
    # Add goal
    goal_data = {"title": "Increase Market Share", "description": "Target 20%."}
    added_goal = await foundation_service.add_strategic_goal(user_id, goal_data)
    assert added_goal.title == "Increase Market Share"
    
    north_star = await foundation_service.get_north_star(user_id)
    assert len(north_star.strategic_goals) == 1
    goal_id = north_star.strategic_goals[0].id
    
    # Update goal
    updated_goal_data = {"title": "Aggressively Increase Market Share", "target_value": "25%"}
    updated_goal = await foundation_service.update_strategic_goal(user_id, goal_id, updated_goal_data)
    assert updated_goal.title == "Aggressively Increase Market Share"
    assert updated_goal.target_value == "25%"
    
    north_star = await foundation_service.get_north_star(user_id)
    assert north_star.strategic_goals[0].title == "Aggressively Increase Market Share"

    # List goals
    goals_list = await foundation_service.list_strategic_goals(user_id)
    assert len(goals_list) == 1
    assert goals_list[0].title == "Aggressively Increase Market Share"

    # Get specific goal
    specific_goal = await foundation_service.get_strategic_goal(user_id, goal_id)
    assert specific_goal is not None
    assert specific_goal.title == "Aggressively Increase Market Share"

    # Delete goal
    delete_success = await foundation_service.delete_strategic_goal(user_id, goal_id)
    assert delete_success is True
    north_star = await foundation_service.get_north_star(user_id)
    assert len(north_star.strategic_goals) == 0
