import pytest
import pytest_asyncio
from uuid import uuid4, UUID
from datetime import datetime, date
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import HTTPException

from backend.services.planning_service import PlanningService
from backend.services.strategic_foundation_service import StrategicFoundationService # For mocking
from backend.models.planning import (
    StrategicPlanCreate, StrategicPlan, PlanStatus,
    InitiativeCreate, Initiative, InitiativeType,
    ActionCreate, Action, ActionStatus,
    ResourceCreate, Resource, ResourceType,
    RiskCreate, Risk
)
from backend.models.strategic_foundation import StrategicGoal # For mock foundation_service

@pytest_asyncio.fixture
async def planning_service(monkeypatch):
    service = PlanningService()
    # Force in-memory cache
    service.cosmos_db_available = False
    service.plans_cache = {}
    service.initiatives_cache = {}
    
    # Mock foundation_service dependency
    mock_foundation_service = AsyncMock(spec=StrategicFoundationService)
    # Configure mock methods as needed for tests, e.g., get_strategic_goal
    mock_foundation_service.get_strategic_goal = AsyncMock(return_value=StrategicGoal(id=uuid4(), title="Mock Goal", description=""))
    
    monkeypatch.setattr(service, 'foundation_service', mock_foundation_service)
    
    # Mock kernel_service if used directly by methods under test
    # For now, assume kernel_service calls are in router or will be patched in specific tests
    return service

@pytest_asyncio.fixture
def mock_user_id():
    return uuid4()

@pytest_asyncio.fixture
def mock_plan_id():
    return uuid4()

# --- StrategicPlan Tests ---
@pytest.mark.asyncio
async def test_create_strategic_plan(planning_service: PlanningService, mock_user_id: UUID):
    plan_data = StrategicPlanCreate(title="Test Plan", description="A test strategic plan.")
    
    created_plan = await planning_service.create_strategic_plan(mock_user_id, plan_data)
    
    assert created_plan is not None
    assert created_plan.title == plan_data.title
    assert created_plan.user_id == mock_user_id
    assert str(created_plan.id) in planning_service.plans_cache

@pytest.mark.asyncio
async def test_get_strategic_plan(planning_service: PlanningService, mock_user_id: UUID):
    plan_id = uuid4()
    planning_service.plans_cache[str(plan_id)] = StrategicPlan(
        id=plan_id, user_id=mock_user_id, title="Cached Plan", 
        created_at=datetime.now(), updated_at=datetime.now()
    )
    
    fetched_plan = await planning_service.get_strategic_plan(plan_id, mock_user_id)
    assert fetched_plan is not None
    assert fetched_plan.title == "Cached Plan"

# --- Initiative Tests ---
@pytest.mark.asyncio
async def test_create_initiative(planning_service: PlanningService, mock_plan_id: UUID, mock_user_id: UUID):
    linked_goal_id = uuid4()
    # Ensure foundation_service.get_strategic_goal returns a valid goal for this ID
    planning_service.foundation_service.get_strategic_goal = AsyncMock(
        return_value=StrategicGoal(id=linked_goal_id, title="Test Goal", description="")
    )

    initiative_data = InitiativeCreate(
        title="Test Initiative", 
        description="A test initiative.",
        initiative_type=InitiativeType.STRATEGIC,
        linked_strategic_goal=linked_goal_id 
    )
    
    created_initiative = await planning_service.create_initiative(mock_plan_id, mock_user_id, initiative_data)
    
    assert created_initiative is not None
    assert created_initiative.title == initiative_data.title
    assert created_initiative.user_id == mock_user_id
    assert created_initiative.plan_id == mock_plan_id
    assert created_initiative.linked_strategic_goal == linked_goal_id
    assert str(created_initiative.id) in planning_service.initiatives_cache

@pytest.mark.asyncio
async def test_create_initiative_invalid_goal(planning_service: PlanningService, mock_plan_id: UUID, mock_user_id: UUID):
    # Ensure foundation_service.get_strategic_goal returns None for an invalid goal ID
    planning_service.foundation_service.get_strategic_goal = AsyncMock(return_value=None)
    
    invalid_goal_id = uuid4()
    initiative_data = InitiativeCreate(
        title="Initiative with Invalid Goal",
        description="Test",
        initiative_type=InitiativeType.STRATEGIC,
        linked_strategic_goal=invalid_goal_id
    )
    
    with pytest.raises(HTTPException) as exc_info:
        await planning_service.create_initiative(mock_plan_id, mock_user_id, initiative_data)
    assert exc_info.value.status_code == 400
    assert "not found for user" in exc_info.value.detail


@pytest.mark.asyncio
async def test_get_initiative(planning_service: PlanningService, mock_user_id: UUID, mock_plan_id: UUID):
    initiative_id = uuid4()
    planning_service.initiatives_cache[str(initiative_id)] = Initiative(
        id=initiative_id, user_id=mock_user_id, plan_id=mock_plan_id, 
        title="Cached Initiative", description="Desc", initiative_type=InitiativeType.STRATEGIC,
        created_at=datetime.now(), updated_at=datetime.now()
    )
    
    fetched_initiative = await planning_service.get_initiative(initiative_id)
    assert fetched_initiative is not None
    assert fetched_initiative.title == "Cached Initiative"

# --- Nested Item Tests (Action example) ---
@pytest.mark.asyncio
async def test_add_action_to_initiative(planning_service: PlanningService, mock_user_id: UUID, mock_plan_id: UUID):
    # Create an initiative first
    initiative_data = InitiativeCreate(title="Initiative for Action", description="Desc", initiative_type=InitiativeType.STRATEGIC)
    initiative = await planning_service.create_initiative(mock_plan_id, mock_user_id, initiative_data)
    
    action_data = ActionCreate(title="Test Action", description="Action desc")
    added_action = await planning_service.create_action(initiative.id, mock_user_id, action_data)
    
    assert added_action is not None
    assert added_action.title == "Test Action"
    
    updated_initiative = await planning_service.get_initiative(initiative.id)
    assert len(updated_initiative.actions) == 1
    assert updated_initiative.actions[0].id == added_action.id

@pytest.mark.asyncio
async def test_update_action_in_initiative(planning_service: PlanningService, mock_user_id: UUID, mock_plan_id: UUID):
    initiative = await planning_service.create_initiative(
        mock_plan_id, mock_user_id, 
        InitiativeCreate(title="Init for Update Action", description="D", initiative_type=InitiativeType.STRATEGIC)
    )
    action = await planning_service.create_action(
        initiative.id, mock_user_id, 
        ActionCreate(title="Old Action Title")
    )
    
    update_data = {"title": "New Action Title", "status": ActionStatus.IN_PROGRESS}
    updated_action = await planning_service.update_action(initiative.id, mock_user_id, action.id, update_data)
    
    assert updated_action is not None
    assert updated_action.title == "New Action Title"
    assert updated_action.status == ActionStatus.IN_PROGRESS
    
    refetched_initiative = await planning_service.get_initiative(initiative.id)
    assert refetched_initiative.actions[0].title == "New Action Title"

@pytest.mark.asyncio
async def test_delete_action_from_initiative(planning_service: PlanningService, mock_user_id: UUID, mock_plan_id: UUID):
    initiative = await planning_service.create_initiative(
        mock_plan_id, mock_user_id, 
        InitiativeCreate(title="Init for Delete Action", description="D", initiative_type=InitiativeType.STRATEGIC)
    )
    action = await planning_service.create_action(
        initiative.id, mock_user_id, 
        ActionCreate(title="Action to Delete")
    )
    
    assert len(initiative.actions) == 1
    
    delete_success = await planning_service.delete_action(initiative.id, mock_user_id, action.id)
    assert delete_success is True
    
    refetched_initiative = await planning_service.get_initiative(initiative.id)
    assert len(refetched_initiative.actions) == 0

# Similar tests should be added for Resource and Risk CRUD operations.

# AI Feature Tests (basic examples, mocking kernel_service)
@pytest.mark.asyncio
@patch('backend.services.planning_service.kernel_service', new_callable=AsyncMock)
async def test_generate_actions_for_initiative_ai(mock_ks: AsyncMock, planning_service: PlanningService, mock_user_id: UUID, mock_plan_id: UUID):
    initiative = await planning_service.create_initiative(
        mock_plan_id, mock_user_id,
        InitiativeCreate(title="AI Actions Test", description="Need AI actions", initiative_type=InitiativeType.STRATEGIC)
    )
    
    # Mock kernel_service.generate_completion to return a JSON list of strings
    mock_ks.generate_completion = AsyncMock(return_value=json.dumps(["AI Action 1", "AI Action 2"]))
    
    generated_actions = await planning_service.generate_actions(initiative.id, mock_user_id)
    
    assert len(generated_actions) == 2
    assert generated_actions[0].title == "AI Action 1"
    
    updated_initiative = await planning_service.get_initiative(initiative.id)
    assert len(updated_initiative.actions) == 2 # Check they were added to the initiative

# Add more tests for other AI features, list methods with filters, edge cases, etc.
