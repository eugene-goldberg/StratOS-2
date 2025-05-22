import pytest
import pytest_asyncio
from uuid import UUID, uuid4
from datetime import datetime
from backend.models.strategic_foundation import StrategicGoal, NorthStar, Purpose, Vision
from backend.services.strategic_foundation_service import StrategicFoundationService


@pytest.mark.asyncio
class TestHierarchicalGoals:
    """Test hierarchical goal organization functionality"""
    
    @pytest_asyncio.fixture
    async def service(self):
        """Create a test service instance"""
        return StrategicFoundationService()
    
    @pytest_asyncio.fixture
    async def test_north_star(self, service):
        """Create a test NorthStar with some goals"""
        user_id = uuid4()
        current_time = datetime.now()
        
        # Create a simple NorthStar
        north_star = NorthStar(
            id=user_id,
            purpose=Purpose(
                statement="Test Purpose",
                created_at=current_time,
                updated_at=current_time
            ),
            vision=Vision(
                statement="Test Vision",
                created_at=current_time,
                updated_at=current_time
            ),
            values=[],
            strategic_goals=[],
            created_at=current_time,
            updated_at=current_time
        )
        
        # Save to service cache
        service.north_stars_cache[str(user_id)] = north_star
        
        return user_id, north_star
    
    async def test_add_goal_with_parent(self, service, test_north_star):
        """Test adding a goal with a parent goal"""
        user_id, north_star = test_north_star
        
        # Add parent goal
        parent_goal_data = {
            "title": "Parent Goal",
            "description": "This is a parent goal"
        }
        parent_goal = await service.add_strategic_goal(user_id, parent_goal_data)
        
        # Add child goal
        child_goal_data = {
            "title": "Child Goal",
            "description": "This is a child goal",
            "parent_goal_id": str(parent_goal.id)
        }
        child_goal = await service.add_strategic_goal(user_id, child_goal_data)
        
        # Verify child has parent_goal_id set
        assert child_goal.parent_goal_id == parent_goal.id
        
        # Verify child is in parent's sub_goals
        updated_parent = await service.get_strategic_goal(user_id, parent_goal.id)
        assert len(updated_parent.sub_goals) == 1
        assert updated_parent.sub_goals[0].id == child_goal.id
    
    async def test_list_goals_hierarchical(self, service, test_north_star):
        """Test listing goals in hierarchical structure"""
        user_id, north_star = test_north_star
        
        # Add parent goals
        parent1 = await service.add_strategic_goal(user_id, {
            "title": "Parent 1",
            "description": "First parent"
        })
        parent2 = await service.add_strategic_goal(user_id, {
            "title": "Parent 2", 
            "description": "Second parent"
        })
        
        # Add child goals
        child1 = await service.add_strategic_goal(user_id, {
            "title": "Child 1",
            "description": "Child of parent 1",
            "parent_goal_id": str(parent1.id)
        })
        child2 = await service.add_strategic_goal(user_id, {
            "title": "Child 2",
            "description": "Child of parent 1",
            "parent_goal_id": str(parent1.id)
        })
        child3 = await service.add_strategic_goal(user_id, {
            "title": "Child 3",
            "description": "Child of parent 2",
            "parent_goal_id": str(parent2.id)
        })
        
        # Get hierarchical list
        hierarchical_goals = await service.list_strategic_goals(user_id, hierarchical=True)
        
        # Should only return top-level goals
        assert len(hierarchical_goals) == 2
        assert all(goal.parent_goal_id is None for goal in hierarchical_goals)
        
        # Check sub-goals are properly nested
        parent1_result = next(g for g in hierarchical_goals if g.id == parent1.id)
        assert len(parent1_result.sub_goals) == 2
        
        parent2_result = next(g for g in hierarchical_goals if g.id == parent2.id)
        assert len(parent2_result.sub_goals) == 1
        
        # Get flat list
        flat_goals = await service.list_strategic_goals(user_id, hierarchical=False)
        assert len(flat_goals) == 5  # 2 parents + 3 children
    
    async def test_update_goal_parent(self, service, test_north_star):
        """Test updating a goal's parent"""
        user_id, north_star = test_north_star
        
        # Create goals
        parent1 = await service.add_strategic_goal(user_id, {
            "title": "Parent 1",
            "description": "First parent"
        })
        parent2 = await service.add_strategic_goal(user_id, {
            "title": "Parent 2",
            "description": "Second parent"
        })
        child = await service.add_strategic_goal(user_id, {
            "title": "Child",
            "description": "Mobile child",
            "parent_goal_id": str(parent1.id)
        })
        
        # Verify initial state
        updated_parent1 = await service.get_strategic_goal(user_id, parent1.id)
        assert len(updated_parent1.sub_goals) == 1
        
        # Move child to parent2
        await service.update_strategic_goal(user_id, child.id, {
            "parent_goal_id": str(parent2.id)
        })
        
        # Verify child moved
        updated_parent1 = await service.get_strategic_goal(user_id, parent1.id)
        updated_parent2 = await service.get_strategic_goal(user_id, parent2.id)
        updated_child = await service.get_strategic_goal(user_id, child.id)
        
        assert len(updated_parent1.sub_goals) == 0
        assert len(updated_parent2.sub_goals) == 1
        assert updated_child.parent_goal_id == parent2.id
    
    async def test_get_sub_goals(self, service, test_north_star):
        """Test getting sub-goals of a specific goal"""
        user_id, north_star = test_north_star
        
        # Create parent and children
        parent = await service.add_strategic_goal(user_id, {
            "title": "Parent",
            "description": "Parent goal"
        })
        
        child1 = await service.add_strategic_goal(user_id, {
            "title": "Child 1",
            "description": "First child",
            "parent_goal_id": str(parent.id)
        })
        child2 = await service.add_strategic_goal(user_id, {
            "title": "Child 2",
            "description": "Second child",
            "parent_goal_id": str(parent.id)
        })
        
        # Get sub-goals
        sub_goals = await service.get_sub_goals(user_id, parent.id)
        
        assert len(sub_goals) == 2
        assert all(goal.parent_goal_id == parent.id for goal in sub_goals)
        
    async def test_nested_hierarchy(self, service, test_north_star):
        """Test multi-level nested hierarchy"""
        user_id, north_star = test_north_star
        
        # Create 3-level hierarchy
        level1 = await service.add_strategic_goal(user_id, {
            "title": "Level 1",
            "description": "Top level goal"
        })
        
        level2 = await service.add_strategic_goal(user_id, {
            "title": "Level 2",
            "description": "Middle level goal",
            "parent_goal_id": str(level1.id)
        })
        
        level3 = await service.add_strategic_goal(user_id, {
            "title": "Level 3",
            "description": "Bottom level goal",
            "parent_goal_id": str(level2.id)
        })
        
        # Verify hierarchy
        updated_level1 = await service.get_strategic_goal(user_id, level1.id)
        assert len(updated_level1.sub_goals) == 1
        assert updated_level1.sub_goals[0].id == level2.id
        
        # Check nested sub-goal
        assert len(updated_level1.sub_goals[0].sub_goals) == 1
        assert updated_level1.sub_goals[0].sub_goals[0].id == level3.id