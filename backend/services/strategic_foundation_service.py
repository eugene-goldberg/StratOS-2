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
        for g_dict in north_star_dict.get("strategic_goals", []): g_dict["id"] = str(g_dict["id"])
        
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
                    for goal_dict in item_data["strategic_goals"]: goal_dict["id"] = UUID(goal_dict["id"])
                
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
        strategic_goals = [StrategicGoal(title=g.get("title",""), description=g.get("description",""), time_frame=g.get("time_frame"), metrics=g.get("metrics"), target_value=g.get("target_value"), current_value=g.get("current_value"), created_at=current_time, updated_at=current_time) for g in north_star_data.strategic_goals]
        
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
        new_goal = StrategicGoal(
            title=goal_data.get("title", "Unnamed Goal"),
            description=goal_data.get("description"),
            time_frame=goal_data.get("time_frame"),
            metrics=goal_data.get("metrics"),
            target_value=goal_data.get("target_value"),
            current_value=goal_data.get("current_value"),
            created_at=current_time, updated_at=current_time
        )
        north_star.strategic_goals.append(new_goal)
        north_star.updated_at = current_time
        await self._save_north_star_to_db(north_star)
        return new_goal

    async def update_strategic_goal(self, user_id: UUID, goal_id: UUID, goal_data: Dict) -> Optional[StrategicGoal]:
        north_star = await self.get_north_star(user_id)
        if not north_star: return None

        goal_to_update = next((g for g in north_star.strategic_goals if g.id == goal_id), None)
        if not goal_to_update: return None

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
        return next((goal for goal in north_star.strategic_goals if goal.id == goal_id), None)
    
    async def list_strategic_goals(self, user_id: UUID) -> List[StrategicGoal]:
        north_star = await self.get_north_star(user_id)
        return north_star.strategic_goals if north_star else []
    
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
