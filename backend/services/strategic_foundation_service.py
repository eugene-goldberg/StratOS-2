import os
import uuid
import logging
from uuid import UUID
from datetime import datetime
from typing import List, Dict, Any, Optional, Union

from azure.cosmos.aio import CosmosClient as AsyncCosmosClient, DatabaseProxy, ContainerProxy
from azure.cosmos import PartitionKey, exceptions as CosmosExceptions
from fastapi import HTTPException, status

from ..models.strategic_foundation import (
    Purpose, Vision, Value, StrategicGoal, NorthStar, 
    NorthStarCreate, NorthStarUpdate
)
from ..core.config import settings # Assuming settings might be used, though not directly in this snippet

class StrategicFoundationService:
    """
    Service for managing strategic foundation components including Purpose, Vision, Values, and Strategic Goals,
    all composed within a single NorthStar document per user.
    """
    
    def __init__(self):
        self.logger = logging.getLogger("strategic_foundation_service")
        self.north_stars_cache = {} # Stores NorthStar objects, keyed by str(user_id)
        
        self.cosmos_db_available = False
        self.cosmos_client: Optional[AsyncCosmosClient] = None
        self.database: Optional[DatabaseProxy] = None
        self.north_star_container: Optional[ContainerProxy] = None
        
        self.cosmos_endpoint = os.getenv("AZURE_COSMOS_ENDPOINT")
        self.cosmos_key = os.getenv("AZURE_COSMOS_KEY")
        self.cosmos_database_name = os.getenv("AZURE_COSMOS_DATABASE_NAME", "stratosdb")

        self._initialize_cosmos_db_sync()

    def _convert_goal_ids_to_str(self, goals: List[Dict]):
        """Recursively convert goal IDs to strings for Cosmos DB storage."""
        for goal in goals:
            goal["id"] = str(goal["id"])
            if goal.get("parent_goal_id"):
                goal["parent_goal_id"] = str(goal["parent_goal_id"])
            if goal.get("sub_goals"):
                self._convert_goal_ids_to_str(goal["sub_goals"])
    
    async def _find_goal_recursive(self, goals: List[StrategicGoal], goal_id: UUID) -> Optional[StrategicGoal]:
        """Recursively find a goal by ID in the goal hierarchy."""
        for goal in goals:
            if goal.id == goal_id:
                return goal
            # Search in sub-goals
            found = await self._find_goal_recursive(goal.sub_goals, goal_id)
            if found:
                return found
        return None
    
    def _build_goal_hierarchy(self, goals: List[StrategicGoal]) -> List[StrategicGoal]:
        """Build hierarchical structure from flat list of goals."""
        # Create a map of all goals by ID
        goal_map = {goal.id: goal for goal in goals}
        
        # Separate top-level goals (no parent)
        top_level_goals = []
        
        for goal in goals:
            if goal.parent_goal_id and goal.parent_goal_id in goal_map:
                # Add to parent's sub_goals
                parent = goal_map[goal.parent_goal_id]
                if goal not in parent.sub_goals:
                    parent.sub_goals.append(goal)
            else:
                # No parent or parent not found, add to top level
                if goal.parent_goal_id:
                    self.logger.warning(f"Parent goal {goal.parent_goal_id} not found for goal {goal.id}")
                top_level_goals.append(goal)
        
        return top_level_goals

    def _convert_goal_ids_to_uuid(self, goals: List[Dict]):
        """Recursively convert goal IDs from strings to UUIDs when retrieving from Cosmos DB."""
        for goal in goals:
            goal["id"] = UUID(goal["id"])
            if goal.get("parent_goal_id"):
                goal["parent_goal_id"] = UUID(goal["parent_goal_id"])
            if goal.get("sub_goals"):
                self._convert_goal_ids_to_uuid(goal["sub_goals"])

    def _initialize_cosmos_db_sync(self):
        if not self.cosmos_endpoint or not self.cosmos_key:
            self.logger.warning("Cosmos DB credentials not found. Using in-memory storage.")
            self.cosmos_db_available = False
            return

        try:
            self.cosmos_client = AsyncCosmosClient(url=self.cosmos_endpoint, credential=self.cosmos_key)
            self.database = self.cosmos_client.get_database_client(self.cosmos_database_name)
            self.north_star_container = self.database.get_container_client("NorthStarConfigurations")
            # Assuming container "NorthStarConfigurations" with PartitionKey(path="/id") is created at app startup
            self.cosmos_db_available = True
            self.logger.info("Cosmos DB async client initialized for StrategicFoundationService.")
        except Exception as e:
            self.logger.warning(f"Cosmos DB async client initialization failed: {str(e)}. Using in-memory storage.")
            self.cosmos_db_available = False
            self.cosmos_client = None
            self.database = None
            self.north_star_container = None
            
    async def _save_north_star_to_db(self, north_star: NorthStar):
        """Helper to save/update NorthStar document in Cosmos DB and cache."""
        if not (self.cosmos_db_available and self.north_star_container):
            self.logger.warning(f"Cosmos DB not available. Caching NorthStar for user {north_star.id} in memory only.")
            self.north_stars_cache[str(north_star.id)] = north_star
            return

        north_star_dict = north_star.model_dump()
        # Ensure all UUIDs are strings for Cosmos DB
        north_star_dict["id"] = str(north_star.id)
        if north_star.purpose: north_star_dict["purpose"]["id"] = str(north_star.purpose.id)
        if north_star.vision: north_star_dict["vision"]["id"] = str(north_star.vision.id)
        for v_dict in north_star_dict.get("values", []): v_dict["id"] = str(v_dict["id"])
        for g_dict in north_star_dict.get("strategic_goals", []): 
            g_dict["id"] = str(g_dict["id"])
            if g_dict.get("parent_goal_id"):
                g_dict["parent_goal_id"] = str(g_dict["parent_goal_id"])
            # Convert sub_goals recursively
            self._convert_goal_ids_to_str(g_dict.get("sub_goals", []))
        
        try:
            await self.north_star_container.upsert_item(body=north_star_dict) # Upsert is safer for create/update
            self.logger.info(f"Saved North Star for user {north_star.id} to Cosmos DB.")
            self.north_stars_cache[str(north_star.id)] = north_star # Update cache
        except CosmosExceptions.CosmosHttpResponseError as e:
            self.logger.error(f"Error saving North Star for user {north_star.id} to Cosmos DB: {str(e)}")
            self.north_stars_cache[str(north_star.id)] = north_star # Cache as fallback


    async def get_north_star(self, user_id: UUID) -> Optional[NorthStar]:
        if str(user_id) in self.north_stars_cache:
            return self.north_stars_cache[str(user_id)]

        if self.cosmos_db_available and self.north_star_container:
            try:
                # NorthStar document ID is the user_id, which is also the partition key
                item_data = await self.north_star_container.read_item(item=str(user_id), partition_key=str(user_id))
                
                # Convert string IDs back to UUID
                item_data["id"] = UUID(item_data["id"])
                if "purpose" in item_data and item_data["purpose"]:
                    item_data["purpose"]["id"] = UUID(item_data["purpose"]["id"])
                if "vision" in item_data and item_data["vision"]:
                    item_data["vision"]["id"] = UUID(item_data["vision"]["id"])
                if "values" in item_data:
                    for value_dict in item_data["values"]: value_dict["id"] = UUID(value_dict["id"])
                if "strategic_goals" in item_data:
                    self._convert_goal_ids_to_uuid(item_data["strategic_goals"])
                
                north_star = NorthStar(**item_data)
                self.north_stars_cache[str(user_id)] = north_star
                return north_star
            except CosmosExceptions.CosmosResourceNotFoundError:
                return None # Not found is a valid case
            except Exception as e:
                self.logger.error(f"Error retrieving North Star for user {user_id} from Cosmos DB: {str(e)}")
                # Do not raise HTTPException here, let router handle it based on None return
        return None
    
    async def create_north_star(self, north_star_data: NorthStarCreate, user_id: UUID) -> NorthStar:
        existing_north_star = await self.get_north_star(user_id)
        if existing_north_star:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="North Star already exists for this user")
        
        current_time = datetime.now()
        purpose = Purpose(statement=north_star_data.purpose, description=north_star_data.purpose_description, created_at=current_time, updated_at=current_time)
        vision = Vision(statement=north_star_data.vision, description=north_star_data.vision_description, time_horizon=north_star_data.vision_time_horizon, created_at=current_time, updated_at=current_time)
        values = [Value(name=v.get("name",""), description=v.get("description",""), examples=v.get("examples"), created_at=current_time, updated_at=current_time) for v in north_star_data.values]
        strategic_goals = []
        for g in north_star_data.strategic_goals:
            parent_id = g.get("parent_goal_id")
            if parent_id and isinstance(parent_id, str):
                parent_id = UUID(parent_id)
            strategic_goals.append(StrategicGoal(
                title=g.get("title", ""),
                description=g.get("description", ""),
                time_frame=g.get("time_frame"),
                metrics=g.get("metrics"),
                target_value=g.get("target_value"),
                current_value=g.get("current_value"),
                parent_goal_id=parent_id,
                created_at=current_time,
                updated_at=current_time
            ))
        
        north_star = NorthStar(
            id=user_id, purpose=purpose, vision=vision, values=values, strategic_goals=strategic_goals,
            created_at=current_time, updated_at=current_time
        )
        
        await self._save_north_star_to_db(north_star)
        return north_star
    
    async def update_north_star(self, user_id: UUID, update_data: NorthStarUpdate) -> Optional[NorthStar]:
        existing_north_star = await self.get_north_star(user_id)
        if not existing_north_star:
            return None # Let router handle 404
        
        current_time = datetime.now()
        changes_made = False

        if update_data.purpose is not None and existing_north_star.purpose.statement != update_data.purpose:
            existing_north_star.purpose.statement = update_data.purpose
            existing_north_star.purpose.updated_at = current_time
            changes_made = True
        if update_data.purpose_description is not None and existing_north_star.purpose.description != update_data.purpose_description:
            existing_north_star.purpose.description = update_data.purpose_description
            existing_north_star.purpose.updated_at = current_time
            changes_made = True
        
        if update_data.vision is not None and existing_north_star.vision.statement != update_data.vision:
            existing_north_star.vision.statement = update_data.vision
            existing_north_star.vision.updated_at = current_time
            changes_made = True
        if update_data.vision_description is not None and existing_north_star.vision.description != update_data.vision_description:
            existing_north_star.vision.description = update_data.vision_description
            existing_north_star.vision.updated_at = current_time
            changes_made = True
        if update_data.vision_time_horizon is not None and existing_north_star.vision.time_horizon != update_data.vision_time_horizon:
            existing_north_star.vision.time_horizon = update_data.vision_time_horizon
            existing_north_star.vision.updated_at = current_time
            changes_made = True
        
        if changes_made:
            existing_north_star.updated_at = current_time
            await self._save_north_star_to_db(existing_north_star)
            
        return existing_north_star

    # Value CRUD operations (as part of NorthStar document)
    async def add_value(self, user_id: UUID, value_data: Dict) -> Value:
        north_star = await self.get_north_star(user_id)
        if not north_star:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="North Star not found to add value")
        
        current_time = datetime.now()
        new_value = Value(
            name=value_data.get("name", "Unnamed Value"), 
            description=value_data.get("description"),
            examples=value_data.get("examples"),
            created_at=current_time, updated_at=current_time
        )
        north_star.values.append(new_value)
        north_star.updated_at = current_time
        await self._save_north_star_to_db(north_star)
        return new_value
    
    async def update_value(self, user_id: UUID, value_id: UUID, value_data: Dict) -> Optional[Value]:
        north_star = await self.get_north_star(user_id)
        if not north_star: return None

        value_to_update = next((v for v in north_star.values if v.id == value_id), None)
        if not value_to_update: return None
            
        if "name" in value_data: value_to_update.name = value_data["name"]
        if "description" in value_data: value_to_update.description = value_data["description"]
        if "examples" in value_data: value_to_update.examples = value_data["examples"]
        value_to_update.updated_at = datetime.now()
        north_star.updated_at = datetime.now()
        
        await self._save_north_star_to_db(north_star)
        return value_to_update
    
    async def delete_value(self, user_id: UUID, value_id: UUID) -> bool:
        north_star = await self.get_north_star(user_id)
        if not north_star: return False
        
        original_len = len(north_star.values)
        north_star.values = [v for v in north_star.values if v.id != value_id]
        if len(north_star.values) == original_len: return False # Not found
            
        north_star.updated_at = datetime.now()
        await self._save_north_star_to_db(north_star)
        return True

    # Strategic Goal CRUD operations (as part of NorthStar document)
    async def add_strategic_goal(self, user_id: UUID, goal_data: Dict) -> StrategicGoal:
        north_star = await self.get_north_star(user_id)
        if not north_star:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="North Star not found to add goal")

        current_time = datetime.now()
        parent_goal_id = goal_data.get("parent_goal_id")
        
        # Convert string UUID to UUID object if provided
        if parent_goal_id and isinstance(parent_goal_id, str):
            parent_goal_id = UUID(parent_goal_id)
        
        new_goal = StrategicGoal(
            title=goal_data.get("title", "Unnamed Goal"),
            description=goal_data.get("description"),
            time_frame=goal_data.get("time_frame"),
            metrics=goal_data.get("metrics"),
            target_value=goal_data.get("target_value"),
            current_value=goal_data.get("current_value"),
            parent_goal_id=parent_goal_id,
            created_at=current_time, updated_at=current_time
        )
        
        # If there's a parent goal, add this as a sub-goal to the parent
        if parent_goal_id:
            parent_goal = await self._find_goal_recursive(north_star.strategic_goals, parent_goal_id)
            if parent_goal:
                parent_goal.sub_goals.append(new_goal)
            else:
                # If parent not found, still add to top level but log warning
                self.logger.warning(f"Parent goal {parent_goal_id} not found, adding goal to top level")
                north_star.strategic_goals.append(new_goal)
        else:
            # No parent, add to top level
            north_star.strategic_goals.append(new_goal)
        
        north_star.updated_at = current_time
        await self._save_north_star_to_db(north_star)
        return new_goal

    async def update_strategic_goal(self, user_id: UUID, goal_id: UUID, goal_data: Dict) -> Optional[StrategicGoal]:
        north_star = await self.get_north_star(user_id)
        if not north_star: return None

        # Find goal recursively in the hierarchy
        goal_to_update = await self._find_goal_recursive(north_star.strategic_goals, goal_id)
        if not goal_to_update: return None

        # Handle parent_goal_id changes
        if "parent_goal_id" in goal_data:
            new_parent_id = goal_data["parent_goal_id"]
            if new_parent_id and isinstance(new_parent_id, str):
                new_parent_id = UUID(new_parent_id)
            
            # If parent is changing, we need to reorganize the hierarchy
            if new_parent_id != goal_to_update.parent_goal_id:
                # Remove from current parent's sub_goals if it has a parent
                if goal_to_update.parent_goal_id:
                    current_parent = await self._find_goal_recursive(north_star.strategic_goals, goal_to_update.parent_goal_id)
                    if current_parent:
                        current_parent.sub_goals = [g for g in current_parent.sub_goals if g.id != goal_id]
                
                # Update parent_goal_id
                goal_to_update.parent_goal_id = new_parent_id
                
                # Add to new parent's sub_goals if new parent exists
                if new_parent_id:
                    new_parent = await self._find_goal_recursive(north_star.strategic_goals, new_parent_id)
                    if new_parent:
                        new_parent.sub_goals.append(goal_to_update)

        if "title" in goal_data: goal_to_update.title = goal_data["title"]
        if "description" in goal_data: goal_to_update.description = goal_data["description"]
        if "time_frame" in goal_data: goal_to_update.time_frame = goal_data["time_frame"]
        if "metrics" in goal_data: goal_to_update.metrics = goal_data["metrics"]
        if "target_value" in goal_data: goal_to_update.target_value = goal_data["target_value"]
        if "current_value" in goal_data: goal_to_update.current_value = goal_data["current_value"]
        goal_to_update.updated_at = datetime.now()
        north_star.updated_at = datetime.now()
        
        await self._save_north_star_to_db(north_star)
        return goal_to_update

    async def delete_strategic_goal(self, user_id: UUID, goal_id: UUID) -> bool:
        north_star = await self.get_north_star(user_id)
        if not north_star: return False
        
        original_len = len(north_star.strategic_goals)
        north_star.strategic_goals = [g for g in north_star.strategic_goals if g.id != goal_id]
        if len(north_star.strategic_goals) == original_len: return False # Not found
            
        north_star.updated_at = datetime.now()
        await self._save_north_star_to_db(north_star)
        return True
    
    # Helper methods for retrieving individual components from the cached/retrieved NorthStar
    async def get_strategic_goal(self, user_id: UUID, goal_id: UUID) -> Optional[StrategicGoal]:
        north_star = await self.get_north_star(user_id)
        if not north_star: return None
        return await self._find_goal_recursive(north_star.strategic_goals, goal_id)
    
    async def list_strategic_goals(self, user_id: UUID, hierarchical: bool = False) -> List[StrategicGoal]:
        north_star = await self.get_north_star(user_id)
        if not north_star:
            return []
        
        if hierarchical:
            # Return only top-level goals with their sub-goals nested
            return [goal for goal in north_star.strategic_goals if not goal.parent_goal_id]
        else:
            # Return flat list of all goals - need to collect from hierarchy
            all_goals = []
            
            def collect_goals(goals: List[StrategicGoal]):
                for goal in goals:
                    all_goals.append(goal)
                    collect_goals(goal.sub_goals)
            
            collect_goals(north_star.strategic_goals)
            return all_goals
    
    async def get_sub_goals(self, user_id: UUID, parent_goal_id: UUID) -> List[StrategicGoal]:
        """Get all direct sub-goals of a specific goal."""
        north_star = await self.get_north_star(user_id)
        if not north_star:
            return []
        
        parent_goal = await self._find_goal_recursive(north_star.strategic_goals, parent_goal_id)
        if not parent_goal:
            return []
        
        return parent_goal.sub_goals
    
    async def get_value(self, user_id: UUID, value_id: UUID) -> Optional[Value]:
        north_star = await self.get_north_star(user_id)
        if not north_star: return None
        return next((value for value in north_star.values if value.id == value_id), None)
    
    async def list_values(self, user_id: UUID) -> List[Value]:
        north_star = await self.get_north_star(user_id)
        return north_star.values if north_star else []

    # create_or_update_north_star method is removed as its logic is complex and
    # better handled by distinct create and update flows, especially for sub-components.
    # The router should call create_north_star or update_north_star (for Purpose/Vision)
    # and then use add/update/delete methods for Values and StrategicGoals.
