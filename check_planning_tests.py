#!/usr/bin/env python3
"""
Script to check test_planning_service.py
"""
import sys
import os
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from uuid import UUID, uuid4

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import conftest_helper to set up mocks
import tests.conftest_helper

# Mock essential planning models
class StrategicPlan:
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', uuid4())
        self.user_id = kwargs.get('user_id', uuid4())
        self.title = kwargs.get('title', 'Test Plan')
        self.description = kwargs.get('description', '')
        self.created_at = kwargs.get('created_at', datetime.now())
        self.updated_at = kwargs.get('updated_at', datetime.now())
        self.initiatives = kwargs.get('initiatives', [])
    
    def model_dump(self, **kwargs):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'description': self.description,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'initiatives': self.initiatives
        }

class StrategicPlanCreate:
    def __init__(self, **kwargs):
        self.title = kwargs.get('title', 'New Plan')
        self.description = kwargs.get('description', '')

class Initiative:
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', uuid4())
        self.user_id = kwargs.get('user_id', uuid4())
        self.plan_id = kwargs.get('plan_id', uuid4()) 
        self.title = kwargs.get('title', 'Test Initiative')
        self.description = kwargs.get('description', '')
        self.initiative_type = kwargs.get('initiative_type', 'STRATEGIC')
        self.linked_strategic_goal = kwargs.get('linked_strategic_goal')
        self.actions = kwargs.get('actions', [])
        self.resources = kwargs.get('resources', [])
        self.risks = kwargs.get('risks', [])
        self.created_at = kwargs.get('created_at', datetime.now())
        self.updated_at = kwargs.get('updated_at', datetime.now())
    
    def model_dump(self, **kwargs):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'plan_id': self.plan_id,
            'title': self.title,
            'description': self.description,
            'initiative_type': self.initiative_type,
            'linked_strategic_goal': self.linked_strategic_goal,
            'actions': self.actions,
            'resources': self.resources,
            'risks': self.risks,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

class InitiativeCreate:
    def __init__(self, **kwargs):
        self.title = kwargs.get('title', 'New Initiative')
        self.description = kwargs.get('description', '')
        self.initiative_type = kwargs.get('initiative_type', 'STRATEGIC')
        self.linked_strategic_goal = kwargs.get('linked_strategic_goal')

class Action:
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', uuid4())
        self.title = kwargs.get('title', 'Test Action')
        self.description = kwargs.get('description', '')
        self.status = kwargs.get('status', 'not_started')
        self.due_date = kwargs.get('due_date')
        self.created_at = kwargs.get('created_at', datetime.now())
        self.updated_at = kwargs.get('updated_at', datetime.now())

class ActionCreate:
    def __init__(self, **kwargs):
        self.title = kwargs.get('title', 'New Action')
        self.description = kwargs.get('description', '')
        self.status = kwargs.get('status', 'not_started')
        self.due_date = kwargs.get('due_date')

class StrategicGoal:
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', uuid4())
        self.title = kwargs.get('title', 'Test Goal')
        self.description = kwargs.get('description', '')

# Set up mock models
sys.modules['backend.models.planning'] = MagicMock()
sys.modules['backend.models.planning'].StrategicPlanCreate = StrategicPlanCreate
sys.modules['backend.models.planning'].StrategicPlan = StrategicPlan
sys.modules['backend.models.planning'].InitiativeCreate = InitiativeCreate
sys.modules['backend.models.planning'].Initiative = Initiative
sys.modules['backend.models.planning'].ActionCreate = ActionCreate
sys.modules['backend.models.planning'].Action = Action
sys.modules['backend.models.planning'].PlanStatus = MagicMock()
sys.modules['backend.models.planning'].InitiativeType = MagicMock()
sys.modules['backend.models.planning'].ActionStatus = MagicMock()
sys.modules['backend.models.planning'].ResourceCreate = MagicMock()
sys.modules['backend.models.planning'].Resource = MagicMock()
sys.modules['backend.models.planning'].ResourceType = MagicMock()
sys.modules['backend.models.planning'].RiskCreate = MagicMock()
sys.modules['backend.models.planning'].Risk = MagicMock()

sys.modules['backend.models.strategic_foundation'] = MagicMock()
sys.modules['backend.models.strategic_foundation'].StrategicGoal = StrategicGoal

# Create mock PlanningService
class MockPlanningService:
    def __init__(self):
        self.plans_cache = {}
        self.initiatives_cache = {}
        self.cosmos_db_available = False
        self.foundation_service = MagicMock()
        
    async def create_strategic_plan(self, user_id, plan_data):
        plan = StrategicPlan(
            user_id=user_id,
            title=plan_data.title,
            description=plan_data.description,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        self.plans_cache[str(plan.id)] = plan
        return plan
    
    async def get_strategic_plan(self, plan_id, user_id):
        return self.plans_cache.get(str(plan_id))
    
    async def create_initiative(self, plan_id, user_id, initiative_data):
        initiative = Initiative(
            user_id=user_id,
            plan_id=plan_id,
            title=initiative_data.title,
            description=initiative_data.description,
            initiative_type=initiative_data.initiative_type,
            linked_strategic_goal=initiative_data.linked_strategic_goal
        )
        self.initiatives_cache[str(initiative.id)] = initiative
        return initiative
    
    async def get_initiative(self, initiative_id):
        return self.initiatives_cache.get(str(initiative_id))
    
    async def create_action(self, initiative_id, user_id, action_data):
        initiative = await self.get_initiative(initiative_id)
        if not initiative:
            return None
        
        action = Action(
            title=action_data.title,
            description=action_data.description
        )
        
        if not hasattr(initiative, 'actions'):
            initiative.actions = []
        
        initiative.actions.append(action)
        return action
    
    async def update_action(self, initiative_id, user_id, action_id, update_data):
        initiative = await self.get_initiative(initiative_id)
        if not initiative or not initiative.actions:
            return None
        
        action = next((a for a in initiative.actions if a.id == action_id), None)
        if not action:
            return None
        
        for key, value in update_data.items():
            setattr(action, key, value)
        
        action.updated_at = datetime.now()
        return action
    
    async def delete_action(self, initiative_id, user_id, action_id):
        initiative = await self.get_initiative(initiative_id)
        if not initiative or not initiative.actions:
            return False
        
        action = next((a for a in initiative.actions if a.id == action_id), None)
        if not action:
            return False
        
        initiative.actions.remove(action)
        return True
    
    async def generate_actions(self, initiative_id, user_id):
        initiative = await self.get_initiative(initiative_id)
        if not initiative:
            return []
        
        # Simulate actions generated by an AI
        generated_actions = [
            Action(title="Define scope", description="AI-generated action"),
            Action(title="Assign team", description="AI-generated action"),
            Action(title="Set milestones", description="AI-generated action")
        ]
        
        if not hasattr(initiative, 'actions'):
            initiative.actions = []
        
        initiative.actions.extend(generated_actions)
        return generated_actions

# Mock PlanningService in the backend module
sys.modules['backend.services.planning_service'] = MagicMock()
sys.modules['backend.services.planning_service'].PlanningService = MockPlanningService

sys.modules['backend.services.strategic_foundation_service'] = MagicMock()
sys.modules['backend.services.strategic_foundation_service'].StrategicFoundationService = MagicMock()

# Try to inspect the test file
def check_planning_tests():
    try:
        # Import the test module
        from tests import test_planning_service
        
        # Find all test functions
        test_functions = []
        for name in dir(test_planning_service):
            if name.startswith('test_'):
                test_functions.append(name)
        
        print(f"Found {len(test_functions)} test functions in test_planning_service.py")
        print(f"Test functions: {', '.join(test_functions)}")
        
        print("\nCheck complete - all PlanningService tests could be parsed!")
        
    except Exception as e:
        print(f"Error importing test_planning_service.py: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_planning_tests()