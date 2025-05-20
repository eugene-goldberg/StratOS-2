import os
import uuid
import logging
from uuid import UUID
from datetime import datetime
from typing import List, Dict, Any, Optional, Union

from azure.cosmos import CosmosClient, PartitionKey, exceptions
from fastapi import HTTPException, status

from ..models.strategic_foundation import (
    Purpose, Vision, Value, StrategicGoal, NorthStar, 
    NorthStarCreate, NorthStarUpdate
)
from ..core.config import settings

class StrategicFoundationService:
    """
    Service for managing strategic foundation components including Purpose, Vision, Values, and Strategic Goals,
    all composed within a single NorthStar document per user.
    """
    
    def __init__(self):
        # Set up logging
        self.logger = logging.getLogger("strategic_foundation_service")
        
        # In-memory storage (used as cache and fallback)
        self.north_stars_cache = {}
        
        # Initialize database connection flags
        self.cosmos_db_available = False
        self.database = None
        self.north_star_container = None
        
        # Try to initialize Cosmos DB connection
        try:
            # Get Cosmos DB connection details from environment variables
            cosmos_endpoint = os.getenv("AZURE_COSMOS_ENDPOINT")
            cosmos_key = os.getenv("AZURE_COSMOS_KEY")
            cosmos_database_name = os.getenv("AZURE_COSMOS_DATABASE_NAME", "stratosdb")
            
            if not cosmos_endpoint or not cosmos_key:
                self.logger.warning("Cosmos DB credentials not found in environment variables. Using in-memory storage.")
                return
            
            # Initialize Cosmos DB client
            self.cosmos_client = CosmosClient(cosmos_endpoint, cosmos_key)
            
            # Get or create database
            self.database = self.cosmos_client.get_database_client(cosmos_database_name)
            
            # Get or create container for North Star configurations
            try:
                self.north_star_container = self.database.get_container_client("NorthStarConfigurations")
                self.logger.info("Connected to existing Cosmos DB NorthStarConfigurations container")
            except exceptions.CosmosResourceNotFoundError:
                # Create container if it doesn't exist
                self.north_star_container = self.database.create_container_if_not_exists(
                    id="NorthStarConfigurations",
                    partition_key=PartitionKey(path="/id"),
                    offer_throughput=400
                )
                self.logger.info("Created Cosmos DB container for North Star configurations")
            
            self.cosmos_db_available = True
            self.logger.info("Cosmos DB connection established successfully")
        except Exception as e:
            self.logger.warning(f"Cosmos DB connection failed: {str(e)}. Using in-memory storage.")
    
    async def get_north_star(self, user_id: UUID) -> Optional[NorthStar]:
        """
        Get the North Star configuration for a specific user
        
        Args:
            user_id: User ID used as document ID
            
        Returns:
            The NorthStar object or None if not found
        """
        # Try to get from database first
        if self.cosmos_db_available:
            try:
                # Query for the NorthStar by user_id
                query = f"SELECT * FROM c WHERE c.id = @id"
                params = [{"name": "@id", "value": str(user_id)}]
                
                results = []
                async for item in self.north_star_container.query_items(
                    query=query, 
                    parameters=params, 
                    enable_cross_partition_query=True
                ):
                    # Convert string IDs back to UUID
                    item["id"] = UUID(item["id"])
                    
                    # Convert nested object IDs to UUID
                    if "purpose" in item:
                        item["purpose"]["id"] = UUID(item["purpose"]["id"])
                    
                    if "vision" in item:
                        item["vision"]["id"] = UUID(item["vision"]["id"])
                    
                    if "values" in item:
                        for value in item["values"]:
                            value["id"] = UUID(value["id"])
                    
                    if "strategic_goals" in item:
                        for goal in item["strategic_goals"]:
                            goal["id"] = UUID(goal["id"])
                    
                    # Create NorthStar object from dict
                    north_star = NorthStar(
                        id=item["id"],
                        purpose=Purpose(**item["purpose"]),
                        vision=Vision(**item["vision"]),
                        values=[Value(**v) for v in item.get("values", [])],
                        strategic_goals=[StrategicGoal(**g) for g in item.get("strategic_goals", [])],
                        created_at=item.get("created_at", datetime.now()),
                        updated_at=item.get("updated_at", datetime.now())
                    )
                    results.append(north_star)
                
                if results:
                    return results[0]
            except Exception as e:
                self.logger.error(f"Error retrieving North Star from Cosmos DB: {str(e)}")
        
        # Try from memory if not found in database or if database is unavailable
        if str(user_id) in self.north_stars_cache:
            return self.north_stars_cache[str(user_id)]
        
        # Not found
        return None
    
    async def create_north_star(self, north_star_data: NorthStarCreate, user_id: UUID) -> NorthStar:
        """
        Create a new North Star for a user
        
        Args:
            north_star_data: Data for creating the North Star
            user_id: User ID used as document ID
            
        Returns:
            The created NorthStar object
        """
        # Check if a North Star already exists for the user
        existing_north_star = await self.get_north_star(user_id)
        if existing_north_star:
            raise HTTPException(status_code=400, detail="North Star already exists for this user")
        
        # Current timestamp
        current_time = datetime.now()
        
        # Create Purpose object
        purpose = Purpose(
            statement=north_star_data.purpose,
            description=north_star_data.purpose_description,
            created_at=current_time,
            updated_at=current_time
        )
        
        # Create Vision object
        vision = Vision(
            statement=north_star_data.vision,
            description=north_star_data.vision_description,
            time_horizon=north_star_data.vision_time_horizon,
            created_at=current_time,
            updated_at=current_time
        )
        
        # Create Values
        values = []
        for value_data in north_star_data.values:
            value = Value(
                name=value_data.get("name", ""),
                description=value_data.get("description", ""),
                examples=value_data.get("examples", None),
                created_at=current_time,
                updated_at=current_time
            )
            values.append(value)
        
        # Create Strategic Goals
        strategic_goals = []
        for goal_data in north_star_data.strategic_goals:
            goal = StrategicGoal(
                title=goal_data.get("title", ""),
                description=goal_data.get("description", ""),
                time_frame=goal_data.get("time_frame", None),
                metrics=goal_data.get("metrics", None),
                target_value=goal_data.get("target_value", None),
                current_value=goal_data.get("current_value", None),
                created_at=current_time,
                updated_at=current_time
            )
            strategic_goals.append(goal)
        
        # Create NorthStar object
        north_star = NorthStar(
            id=user_id,
            purpose=purpose,
            vision=vision,
            values=values,
            strategic_goals=strategic_goals,
            created_at=current_time,
            updated_at=current_time
        )
        
        # Store in database or memory
        if self.cosmos_db_available:
            try:
                north_star_dict = north_star.dict()
                # Convert UUID to string for Cosmos DB
                north_star_dict["id"] = str(north_star_dict["id"])
                north_star_dict["purpose"]["id"] = str(north_star_dict["purpose"]["id"])
                north_star_dict["vision"]["id"] = str(north_star_dict["vision"]["id"])
                
                for value in north_star_dict["values"]:
                    value["id"] = str(value["id"])
                
                for goal in north_star_dict["strategic_goals"]:
                    goal["id"] = str(goal["id"])
                
                # Store in Cosmos DB
                await self.north_star_container.create_item(body=north_star_dict)
                self.logger.info(f"Created North Star in Cosmos DB for user: {user_id}")
            except Exception as e:
                self.logger.error(f"Error creating North Star in Cosmos DB: {str(e)}")
                # Fallback to in-memory storage
                self.north_stars_cache[str(user_id)] = north_star
        else:
            # Store in memory
            self.north_stars_cache[str(user_id)] = north_star
            self.logger.info(f"Created North Star in memory for user: {user_id}")
        
        return north_star
    
    async def update_north_star(self, user_id: UUID, update_data: NorthStarUpdate) -> Optional[NorthStar]:
        """
        Update an existing North Star for a user
        
        Args:
            user_id: User ID used as document ID
            update_data: Data for updating the North Star
            
        Returns:
            The updated NorthStar object or None if not found
        """
        # Get existing North Star
        existing_north_star = await self.get_north_star(user_id)
        if not existing_north_star:
            return None
        
        # Current timestamp
        current_time = datetime.now()
        
        # Update Purpose if provided
        purpose = existing_north_star.purpose
        if update_data.purpose is not None:
            purpose.statement = update_data.purpose
            purpose.updated_at = current_time
        if update_data.purpose_description is not None:
            purpose.description = update_data.purpose_description
            purpose.updated_at = current_time
        
        # Update Vision if provided
        vision = existing_north_star.vision
        if update_data.vision is not None:
            vision.statement = update_data.vision
            vision.updated_at = current_time
        if update_data.vision_description is not None:
            vision.description = update_data.vision_description
            vision.updated_at = current_time
        if update_data.vision_time_horizon is not None:
            vision.time_horizon = update_data.vision_time_horizon
            vision.updated_at = current_time
        
        # Create updated NorthStar object
        updated_north_star = NorthStar(
            id=user_id,
            purpose=purpose,
            vision=vision,
            values=existing_north_star.values,
            strategic_goals=existing_north_star.strategic_goals,
            created_at=existing_north_star.created_at,
            updated_at=current_time
        )
        
        # Update in database or memory
        if self.cosmos_db_available:
            try:
                north_star_dict = updated_north_star.dict()
                # Convert UUID to string for Cosmos DB
                north_star_dict["id"] = str(north_star_dict["id"])
                north_star_dict["purpose"]["id"] = str(north_star_dict["purpose"]["id"])
                north_star_dict["vision"]["id"] = str(north_star_dict["vision"]["id"])
                
                for value in north_star_dict["values"]:
                    value["id"] = str(value["id"])
                
                for goal in north_star_dict["strategic_goals"]:
                    goal["id"] = str(goal["id"])
                
                # Update in Cosmos DB
                await self.north_star_container.replace_item(
                    item=str(user_id),
                    body=north_star_dict
                )
                self.logger.info(f"Updated North Star in Cosmos DB for user: {user_id}")
            except Exception as e:
                self.logger.error(f"Error updating North Star in Cosmos DB: {str(e)}")
                # Fallback to in-memory storage
                self.north_stars_cache[str(user_id)] = updated_north_star
        else:
            # Update in memory
            self.north_stars_cache[str(user_id)] = updated_north_star
            self.logger.info(f"Updated North Star in memory for user: {user_id}")
        
        return updated_north_star
    
    async def create_or_update_north_star(self, user_id: UUID, data: Union[NorthStarCreate, NorthStarUpdate]) -> NorthStar:
        """
        Create a new North Star if it doesn't exist, or update an existing one
        
        Args:
            user_id: User ID used as document ID
            data: Data for creating or updating the North Star
            
        Returns:
            The created or updated NorthStar object
        """
        # Check if a North Star exists for the user
        existing_north_star = await self.get_north_star(user_id)
        
        if existing_north_star:
            # If it exists and we have update data, update it
            if isinstance(data, NorthStarUpdate):
                return await self.update_north_star(user_id, data)
            else:
                # If we have create data but North Star exists, convert to update data
                update_data = NorthStarUpdate(
                    purpose=data.purpose,
                    purpose_description=data.purpose_description,
                    vision=data.vision,
                    vision_description=data.vision_description,
                    vision_time_horizon=data.vision_time_horizon
                )
                # For values and strategic goals, we need a more complex update
                # that we'll handle separately
                updated_north_star = await self.update_north_star(user_id, update_data)
                
                # Update values if provided in create data
                if data.values:
                    # For simplicity in MVP, replace all values
                    updated_north_star.values = []
                    for value_data in data.values:
                        await self.add_value(user_id, value_data)
                
                # Update strategic goals if provided in create data
                if data.strategic_goals:
                    # For simplicity in MVP, replace all goals
                    updated_north_star.strategic_goals = []
                    for goal_data in data.strategic_goals:
                        await self.add_strategic_goal(user_id, goal_data)
                
                return await self.get_north_star(user_id)
        else:
            # If it doesn't exist, create it (must have create data)
            if isinstance(data, NorthStarCreate):
                return await self.create_north_star(data, user_id)
            else:
                # Can't create with just update data
                raise HTTPException(status_code=400, detail="Cannot create a North Star with partial data")
    
    # Value CRUD operations
    
    async def add_value(self, user_id: UUID, value_data: Dict) -> Value:
        """
        Add a value to a user's North Star
        
        Args:
            user_id: User ID of the North Star
            value_data: Data for creating the value
            
        Returns:
            The created Value object
            
        Raises:
            HTTPException: If the North Star is not found
        """
        # Get the North Star
        north_star = await self.get_north_star(user_id)
        if not north_star:
            raise HTTPException(status_code=404, detail="North Star not found")
        
        # Current timestamp
        current_time = datetime.now()
        
        # Create the Value
        value = Value(
            name=value_data.get("name", ""),
            description=value_data.get("description", ""),
            examples=value_data.get("examples", None),
            created_at=current_time,
            updated_at=current_time
        )
        
        # Add value to the North Star
        north_star.values.append(value)
        north_star.updated_at = current_time
        
        # Update North Star in database or memory
        if self.cosmos_db_available:
            try:
                north_star_dict = north_star.dict()
                # Convert UUID to string for Cosmos DB
                north_star_dict["id"] = str(north_star_dict["id"])
                north_star_dict["purpose"]["id"] = str(north_star_dict["purpose"]["id"])
                north_star_dict["vision"]["id"] = str(north_star_dict["vision"]["id"])
                
                for v in north_star_dict["values"]:
                    v["id"] = str(v["id"])
                
                for goal in north_star_dict["strategic_goals"]:
                    goal["id"] = str(goal["id"])
                
                # Update in Cosmos DB
                await self.north_star_container.replace_item(
                    item=str(user_id),
                    body=north_star_dict
                )
                self.logger.info(f"Added value to North Star in Cosmos DB for user: {user_id}")
            except Exception as e:
                self.logger.error(f"Error adding value to North Star in Cosmos DB: {str(e)}")
                # Fallback to in-memory storage
                self.north_stars_cache[str(user_id)] = north_star
        else:
            # Update in memory
            self.north_stars_cache[str(user_id)] = north_star
            self.logger.info(f"Added value to North Star in memory for user: {user_id}")
        
        return value
    
    async def update_value(self, user_id: UUID, value_id: UUID, value_data: Dict) -> Optional[Value]:
        """
        Update a value in a user's North Star
        
        Args:
            user_id: User ID of the North Star
            value_id: ID of the value to update
            value_data: Data for updating the value
            
        Returns:
            The updated Value object or None if not found
            
        Raises:
            HTTPException: If the North Star is not found
        """
        # Get the North Star
        north_star = await self.get_north_star(user_id)
        if not north_star:
            raise HTTPException(status_code=404, detail="North Star not found")
        
        # Find the value to update
        value_index = None
        for i, value in enumerate(north_star.values):
            if value.id == value_id:
                value_index = i
                break
        
        if value_index is None:
            return None
        
        # Current timestamp
        current_time = datetime.now()
        
        # Update the value
        value = north_star.values[value_index]
        if "name" in value_data:
            value.name = value_data["name"]
        if "description" in value_data:
            value.description = value_data["description"]
        if "examples" in value_data:
            value.examples = value_data["examples"]
        value.updated_at = current_time
        
        # Update the North Star
        north_star.values[value_index] = value
        north_star.updated_at = current_time
        
        # Update North Star in database or memory
        if self.cosmos_db_available:
            try:
                north_star_dict = north_star.dict()
                # Convert UUID to string for Cosmos DB
                north_star_dict["id"] = str(north_star_dict["id"])
                north_star_dict["purpose"]["id"] = str(north_star_dict["purpose"]["id"])
                north_star_dict["vision"]["id"] = str(north_star_dict["vision"]["id"])
                
                for v in north_star_dict["values"]:
                    v["id"] = str(v["id"])
                
                for goal in north_star_dict["strategic_goals"]:
                    goal["id"] = str(goal["id"])
                
                # Update in Cosmos DB
                await self.north_star_container.replace_item(
                    item=str(user_id),
                    body=north_star_dict
                )
                self.logger.info(f"Updated value in North Star in Cosmos DB for user: {user_id}")
            except Exception as e:
                self.logger.error(f"Error updating value in North Star in Cosmos DB: {str(e)}")
                # Fallback to in-memory storage
                self.north_stars_cache[str(user_id)] = north_star
        else:
            # Update in memory
            self.north_stars_cache[str(user_id)] = north_star
            self.logger.info(f"Updated value in North Star in memory for user: {user_id}")
        
        return value
    
    async def delete_value(self, user_id: UUID, value_id: UUID) -> bool:
        """
        Delete a value from a user's North Star
        
        Args:
            user_id: User ID of the North Star
            value_id: ID of the value to delete
            
        Returns:
            True if successful, False if value not found
            
        Raises:
            HTTPException: If the North Star is not found
        """
        # Get the North Star
        north_star = await self.get_north_star(user_id)
        if not north_star:
            raise HTTPException(status_code=404, detail="North Star not found")
        
        # Find the value to delete
        original_length = len(north_star.values)
        north_star.values = [v for v in north_star.values if v.id != value_id]
        
        # If no value was deleted, return False
        if len(north_star.values) == original_length:
            return False
        
        # Update timestamp
        north_star.updated_at = datetime.now()
        
        # Update North Star in database or memory
        if self.cosmos_db_available:
            try:
                north_star_dict = north_star.dict()
                # Convert UUID to string for Cosmos DB
                north_star_dict["id"] = str(north_star_dict["id"])
                north_star_dict["purpose"]["id"] = str(north_star_dict["purpose"]["id"])
                north_star_dict["vision"]["id"] = str(north_star_dict["vision"]["id"])
                
                for value in north_star_dict["values"]:
                    value["id"] = str(value["id"])
                
                for goal in north_star_dict["strategic_goals"]:
                    goal["id"] = str(goal["id"])
                
                # Update in Cosmos DB
                await self.north_star_container.replace_item(
                    item=str(user_id),
                    body=north_star_dict
                )
                self.logger.info(f"Deleted value from North Star in Cosmos DB for user: {user_id}")
            except Exception as e:
                self.logger.error(f"Error deleting value from North Star in Cosmos DB: {str(e)}")
                # Fallback to in-memory storage
                self.north_stars_cache[str(user_id)] = north_star
        else:
            # Update in memory
            self.north_stars_cache[str(user_id)] = north_star
            self.logger.info(f"Deleted value from North Star in memory for user: {user_id}")
        
        return True
    
    # Strategic Goal CRUD operations
    
    async def add_strategic_goal(self, user_id: UUID, goal_data: Dict) -> StrategicGoal:
        """
        Add a strategic goal to a user's North Star
        
        Args:
            user_id: User ID of the North Star
            goal_data: Data for creating the strategic goal
            
        Returns:
            The created StrategicGoal object
            
        Raises:
            HTTPException: If the North Star is not found
        """
        # Get the North Star
        north_star = await self.get_north_star(user_id)
        if not north_star:
            raise HTTPException(status_code=404, detail="North Star not found")
        
        # Current timestamp
        current_time = datetime.now()
        
        # Create the Strategic Goal
        goal = StrategicGoal(
            title=goal_data.get("title", ""),
            description=goal_data.get("description", ""),
            time_frame=goal_data.get("time_frame", None),
            metrics=goal_data.get("metrics", None),
            target_value=goal_data.get("target_value", None),
            current_value=goal_data.get("current_value", None),
            created_at=current_time,
            updated_at=current_time
        )
        
        # Add goal to the North Star
        north_star.strategic_goals.append(goal)
        north_star.updated_at = current_time
        
        # Update North Star in database or memory
        if self.cosmos_db_available:
            try:
                north_star_dict = north_star.dict()
                # Convert UUID to string for Cosmos DB
                north_star_dict["id"] = str(north_star_dict["id"])
                north_star_dict["purpose"]["id"] = str(north_star_dict["purpose"]["id"])
                north_star_dict["vision"]["id"] = str(north_star_dict["vision"]["id"])
                
                for value in north_star_dict["values"]:
                    value["id"] = str(value["id"])
                
                for g in north_star_dict["strategic_goals"]:
                    g["id"] = str(g["id"])
                
                # Update in Cosmos DB
                await self.north_star_container.replace_item(
                    item=str(user_id),
                    body=north_star_dict
                )
                self.logger.info(f"Added strategic goal to North Star in Cosmos DB for user: {user_id}")
            except Exception as e:
                self.logger.error(f"Error adding strategic goal to North Star in Cosmos DB: {str(e)}")
                # Fallback to in-memory storage
                self.north_stars_cache[str(user_id)] = north_star
        else:
            # Update in memory
            self.north_stars_cache[str(user_id)] = north_star
            self.logger.info(f"Added strategic goal to North Star in memory for user: {user_id}")
        
        return goal
    
    async def update_strategic_goal(self, user_id: UUID, goal_id: UUID, goal_data: Dict) -> Optional[StrategicGoal]:
        """
        Update a strategic goal in a user's North Star
        
        Args:
            user_id: User ID of the North Star
            goal_id: ID of the strategic goal to update
            goal_data: Data for updating the strategic goal
            
        Returns:
            The updated StrategicGoal object or None if not found
            
        Raises:
            HTTPException: If the North Star is not found
        """
        # Get the North Star
        north_star = await self.get_north_star(user_id)
        if not north_star:
            raise HTTPException(status_code=404, detail="North Star not found")
        
        # Find the strategic goal to update
        goal_index = None
        for i, goal in enumerate(north_star.strategic_goals):
            if goal.id == goal_id:
                goal_index = i
                break
        
        if goal_index is None:
            return None
        
        # Current timestamp
        current_time = datetime.now()
        
        # Update the strategic goal
        goal = north_star.strategic_goals[goal_index]
        if "title" in goal_data:
            goal.title = goal_data["title"]
        if "description" in goal_data:
            goal.description = goal_data["description"]
        if "time_frame" in goal_data:
            goal.time_frame = goal_data["time_frame"]
        if "metrics" in goal_data:
            goal.metrics = goal_data["metrics"]
        if "target_value" in goal_data:
            goal.target_value = goal_data["target_value"]
        if "current_value" in goal_data:
            goal.current_value = goal_data["current_value"]
        goal.updated_at = current_time
        
        # Update the North Star
        north_star.strategic_goals[goal_index] = goal
        north_star.updated_at = current_time
        
        # Update North Star in database or memory
        if self.cosmos_db_available:
            try:
                north_star_dict = north_star.dict()
                # Convert UUID to string for Cosmos DB
                north_star_dict["id"] = str(north_star_dict["id"])
                north_star_dict["purpose"]["id"] = str(north_star_dict["purpose"]["id"])
                north_star_dict["vision"]["id"] = str(north_star_dict["vision"]["id"])
                
                for value in north_star_dict["values"]:
                    value["id"] = str(value["id"])
                
                for g in north_star_dict["strategic_goals"]:
                    g["id"] = str(g["id"])
                
                # Update in Cosmos DB
                await self.north_star_container.replace_item(
                    item=str(user_id),
                    body=north_star_dict
                )
                self.logger.info(f"Updated strategic goal in North Star in Cosmos DB for user: {user_id}")
            except Exception as e:
                self.logger.error(f"Error updating strategic goal in North Star in Cosmos DB: {str(e)}")
                # Fallback to in-memory storage
                self.north_stars_cache[str(user_id)] = north_star
        else:
            # Update in memory
            self.north_stars_cache[str(user_id)] = north_star
            self.logger.info(f"Updated strategic goal in North Star in memory for user: {user_id}")
        
        return goal
    
    async def delete_strategic_goal(self, user_id: UUID, goal_id: UUID) -> bool:
        """
        Delete a strategic goal from a user's North Star
        
        Args:
            user_id: User ID of the North Star
            goal_id: ID of the strategic goal to delete
            
        Returns:
            True if successful, False if strategic goal not found
            
        Raises:
            HTTPException: If the North Star is not found
        """
        # Get the North Star
        north_star = await self.get_north_star(user_id)
        if not north_star:
            raise HTTPException(status_code=404, detail="North Star not found")
        
        # Find the strategic goal to delete
        original_length = len(north_star.strategic_goals)
        north_star.strategic_goals = [g for g in north_star.strategic_goals if g.id != goal_id]
        
        # If no strategic goal was deleted, return False
        if len(north_star.strategic_goals) == original_length:
            return False
        
        # Update timestamp
        north_star.updated_at = datetime.now()
        
        # Update North Star in database or memory
        if self.cosmos_db_available:
            try:
                north_star_dict = north_star.dict()
                # Convert UUID to string for Cosmos DB
                north_star_dict["id"] = str(north_star_dict["id"])
                north_star_dict["purpose"]["id"] = str(north_star_dict["purpose"]["id"])
                north_star_dict["vision"]["id"] = str(north_star_dict["vision"]["id"])
                
                for value in north_star_dict["values"]:
                    value["id"] = str(value["id"])
                
                for goal in north_star_dict["strategic_goals"]:
                    goal["id"] = str(goal["id"])
                
                # Update in Cosmos DB
                await self.north_star_container.replace_item(
                    item=str(user_id),
                    body=north_star_dict
                )
                self.logger.info(f"Deleted strategic goal from North Star in Cosmos DB for user: {user_id}")
            except Exception as e:
                self.logger.error(f"Error deleting strategic goal from North Star in Cosmos DB: {str(e)}")
                # Fallback to in-memory storage
                self.north_stars_cache[str(user_id)] = north_star
        else:
            # Update in memory
            self.north_stars_cache[str(user_id)] = north_star
            self.logger.info(f"Deleted strategic goal from North Star in memory for user: {user_id}")
        
        return True
    
    # Helper methods for retrieving individual components
    
    async def get_strategic_goal(self, user_id: UUID, goal_id: UUID) -> Optional[StrategicGoal]:
        """
        Get a specific strategic goal from a user's North Star
        
        Args:
            user_id: User ID of the North Star
            goal_id: ID of the strategic goal to retrieve
            
        Returns:
            The StrategicGoal object or None if not found
        """
        # Get the North Star
        north_star = await self.get_north_star(user_id)
        if not north_star:
            return None
        
        # Find the strategic goal
        for goal in north_star.strategic_goals:
            if goal.id == goal_id:
                return goal
        
        return None
    
    async def list_strategic_goals(self, user_id: UUID) -> List[StrategicGoal]:
        """
        List all strategic goals for a user's North Star
        
        Args:
            user_id: User ID of the North Star
            
        Returns:
            List of StrategicGoal objects or empty list if North Star not found
        """
        # Get the North Star
        north_star = await self.get_north_star(user_id)
        if not north_star:
            return []
        
        return north_star.strategic_goals
    
    async def get_value(self, user_id: UUID, value_id: UUID) -> Optional[Value]:
        """
        Get a specific value from a user's North Star
        
        Args:
            user_id: User ID of the North Star
            value_id: ID of the value to retrieve
            
        Returns:
            The Value object or None if not found
        """
        # Get the North Star
        north_star = await self.get_north_star(user_id)
        if not north_star:
            return None
        
        # Find the value
        for value in north_star.values:
            if value.id == value_id:
                return value
        
        return None
    
    async def list_values(self, user_id: UUID) -> List[Value]:
        """
        List all values for a user's North Star
        
        Args:
            user_id: User ID of the North Star
            
        Returns:
            List of Value objects or empty list if North Star not found
        """
        # Get the North Star
        north_star = await self.get_north_star(user_id)
        if not north_star:
            return []
        
        return north_star.values