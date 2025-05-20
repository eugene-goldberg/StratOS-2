import os
import uuid
import logging
from uuid import UUID
from datetime import datetime
from typing import List, Optional, Dict, Any, Union

from azure.cosmos import CosmosClient, PartitionKey, exceptions
from fastapi import HTTPException

from ..models.planning import (
    StrategicPlan, StrategicPlanCreate, Initiative, InitiativeCreate,
    Action, ActionCreate, Resource, ResourceCreate, Risk, RiskCreate,
    PlanStatus, InitiativeType
)

class PlanningService:
    """Service for managing strategic planning operations including initiatives and actions."""
    
    def __init__(self):
        # Set up logging
        self.logger = logging.getLogger("planning_service")
        
        # In-memory storage (used as cache and fallback)
        self.plans_cache = {}
        self.initiatives_cache = {}
        self.actions_cache = {}
        self.resources_cache = {}
        self.risks_cache = {}
        
        # Initialize database connection flags
        self.cosmos_db_available = False
        self.database = None
        self.plans_container = None
        self.initiatives_container = None
        
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
            
            # Get or create containers for plans and initiatives
            try:
                self.plans_container = self.database.get_container_client("StrategicPlans")
                self.initiatives_container = self.database.get_container_client("Initiatives")
                self.logger.info("Connected to existing Cosmos DB containers")
            except exceptions.CosmosResourceNotFoundError:
                # Create containers if they don't exist
                self.plans_container = self.database.create_container_if_not_exists(
                    id="StrategicPlans",
                    partition_key=PartitionKey(path="/id"),
                    offer_throughput=400
                )
                self.initiatives_container = self.database.create_container_if_not_exists(
                    id="Initiatives",
                    partition_key=PartitionKey(path="/id"),
                    offer_throughput=400
                )
                self.logger.info("Created Cosmos DB containers for strategic plans and initiatives")
            
            self.cosmos_db_available = True
            self.logger.info("Cosmos DB connection established successfully")
        except Exception as e:
            self.logger.warning(f"Cosmos DB connection failed: {str(e)}. Using in-memory storage.")

    # Initiative CRUD Operations
    
    async def create_initiative(self, initiative_create: InitiativeCreate) -> Initiative:
        """
        Create a new strategic initiative
        
        Args:
            initiative_create: Initiative data to create
            
        Returns:
            The created Initiative object
        """
        # Generate a new ID
        initiative_id = uuid.uuid4()
        
        # Current timestamp
        current_time = datetime.now()
        
        # Construct the Initiative object
            initiative = Initiative(
            id=initiative_id,
            title=initiative_create.title,
            description=initiative_create.description,
            initiative_type=initiative_create.initiative_type,
            status=initiative_create.status,
            linked_strategic_goal=initiative_create.linked_strategic_goal,
            owner=initiative_create.owner,
            start_date=initiative_create.start_date,
            end_date=initiative_create.end_date,
            actions=[],
            risks=[],
            resources=[],
            key_metrics=[],
            created_at=current_time,
            updated_at=current_time
        )
        
        # Store in database or memory
        if self.cosmos_db_available:
            try:
                initiative_dict = initiative.dict()
                # Convert UUID to string for Cosmos DB
                initiative_dict["id"] = str(initiative_dict["id"])
                if initiative_dict.get("strategic_goal_id"):
                    initiative_dict["strategic_goal_id"] = str(initiative_dict["strategic_goal_id"])
                
                # Store in Cosmos DB
                await self.initiatives_container.create_item(body=initiative_dict)
                self.logger.info(f"Created initiative in Cosmos DB: {initiative_id}")
            except Exception as e:
                self.logger.error(f"Error creating initiative in Cosmos DB: {str(e)}")
                # Fallback to in-memory storage
                self.initiatives_cache[initiative_id] = initiative
        else:
            # Store in memory
            self.initiatives_cache[initiative_id] = initiative
            self.logger.info(f"Created initiative in memory: {initiative_id}")
        
        return initiative
    
    async def get_initiative(self, initiative_id: UUID) -> Initiative:
        """
        Get an initiative by ID
        
        Args:
            initiative_id: The UUID of the initiative to retrieve
            
        Returns:
            The Initiative object
            
        Raises:
            HTTPException: If the initiative is not found
        """
        # Try to get from database first
        if self.cosmos_db_available:
            try:
                # Query for the initiative
                query = f"SELECT * FROM c WHERE c.id = @id"
                params = [{"name": "@id", "value": str(initiative_id)}]
                
                results = []
                async for item in self.initiatives_container.query_items(
                    query=query, 
                    parameters=params, 
                    enable_cross_partition_query=True
                ):
                    # Convert string IDs back to UUID
                    item["id"] = UUID(item["id"])
                    if item.get("strategic_goal_id"):
                        item["strategic_goal_id"] = UUID(item["strategic_goal_id"])
                    
                    # Convert action, resource, and risk IDs to UUID
                    for action in item.get("actions", []):
                        action["id"] = UUID(action["id"])
                    
                    for resource in item.get("resources", []):
                        resource["id"] = UUID(resource["id"])
                    
                    for risk in item.get("risks", []):
                        risk["id"] = UUID(risk["id"])
                    
                    # Create Initiative object from dict
                    initiative = Initiative(**item)
                    results.append(initiative)
                
                if results:
                    return results[0]
            except Exception as e:
                self.logger.error(f"Error retrieving initiative from Cosmos DB: {str(e)}")
        
        # Try from memory if not found in database or if database is unavailable
        if initiative_id in self.initiatives_cache:
            return self.initiatives_cache[initiative_id]
        
        # Not found
        raise HTTPException(status_code=404, detail=f"Initiative with ID {initiative_id} not found")
    
    async def list_initiatives(self) -> List[Initiative]:
        """
        List all initiatives
        
        Returns:
            List of Initiative objects
        """
        initiatives = []
        
        # Try to get from database first
        if self.cosmos_db_available:
            try:
                query = "SELECT * FROM c"
                
                async for item in self.initiatives_container.query_items(
                    query=query, 
                    enable_cross_partition_query=True
                ):
                    # Convert string IDs back to UUID
                    item["id"] = UUID(item["id"])
                    if item.get("strategic_goal_id"):
                        item["strategic_goal_id"] = UUID(item["strategic_goal_id"])
                    
                    # Convert action, resource, and risk IDs to UUID
                    for action in item.get("actions", []):
                        action["id"] = UUID(action["id"])
                    
                    for resource in item.get("resources", []):
                        resource["id"] = UUID(resource["id"])
                    
                    for risk in item.get("risks", []):
                        risk["id"] = UUID(risk["id"])
                    
                    # Create Initiative object from dict
                    initiative = Initiative(**item)
                    initiatives.append(initiative)
                
                return initiatives
            except Exception as e:
                self.logger.error(f"Error listing initiatives from Cosmos DB: {str(e)}")
        
        # Return from memory if database is unavailable
        return list(self.initiatives_cache.values())
    
    async def update_initiative(self, initiative_id: UUID, initiative_update: InitiativeCreate) -> Initiative:
        """
        Update an existing initiative
        
        Args:
            initiative_id: ID of the initiative to update
            initiative_update: Updated initiative data
            
        Returns:
            Updated Initiative object
            
        Raises:
            HTTPException: If the initiative is not found
        """
        # Get the existing initiative to update
        try:
            existing_initiative = await self.get_initiative(initiative_id)
        except HTTPException:
            raise HTTPException(status_code=404, detail=f"Initiative with ID {initiative_id} not found")
        
        # Update timestamp
        current_time = datetime.now()
        
        # Create updated initiative object, preserving existing actions, resources, and risks
        updated_initiative = Initiative(
            id=initiative_id,
            title=initiative_update.title,
            description=initiative_update.description,
            initiative_type=initiative_update.initiative_type,
            status=initiative_update.status,
            linked_strategic_goal=initiative_update.linked_strategic_goal,
            owner=initiative_update.owner,
            start_date=initiative_update.start_date,
            end_date=initiative_update.end_date,
            actions=existing_initiative.actions,
            resources=existing_initiative.resources,
            risks=existing_initiative.risks,
            key_metrics=existing_initiative.key_metrics,
            created_at=existing_initiative.created_at,
            updated_at=current_time
        )
        
        # Update in database or memory
        if self.cosmos_db_available:
            try:
                initiative_dict = updated_initiative.dict()
                # Convert UUID to string for Cosmos DB
                initiative_dict["id"] = str(initiative_dict["id"])
                if initiative_dict.get("strategic_goal_id"):
                    initiative_dict["strategic_goal_id"] = str(initiative_dict["strategic_goal_id"])
                
                # Convert action, resource, and risk IDs to strings
                for action in initiative_dict.get("actions", []):
                    action["id"] = str(action["id"])
                
                for resource in initiative_dict.get("resources", []):
                    resource["id"] = str(resource["id"])
                
                for risk in initiative_dict.get("risks", []):
                    risk["id"] = str(risk["id"])
                
                # Update in Cosmos DB
                await self.initiatives_container.replace_item(
                    item=str(initiative_id),
                    body=initiative_dict
                )
                self.logger.info(f"Updated initiative in Cosmos DB: {initiative_id}")
            except Exception as e:
                self.logger.error(f"Error updating initiative in Cosmos DB: {str(e)}")
                # Fallback to in-memory storage
                self.initiatives_cache[initiative_id] = updated_initiative
        else:
            # Update in memory
            self.initiatives_cache[initiative_id] = updated_initiative
            self.logger.info(f"Updated initiative in memory: {initiative_id}")
        
        return updated_initiative
    
    async def delete_initiative(self, initiative_id: UUID) -> bool:
        """
        Delete an initiative by ID
        
        Args:
            initiative_id: ID of the initiative to delete
            
        Returns:
            True if successful, False otherwise
            
        Raises:
            HTTPException: If the initiative is not found
        """
        # Check if initiative exists
        try:
            await self.get_initiative(initiative_id)
        except HTTPException:
            raise HTTPException(status_code=404, detail=f"Initiative with ID {initiative_id} not found")
        
        # Delete from database or memory
        if self.cosmos_db_available:
            try:
                await self.initiatives_container.delete_item(
                    item=str(initiative_id),
                    partition_key=str(initiative_id)
                )
                self.logger.info(f"Deleted initiative from Cosmos DB: {initiative_id}")
            except Exception as e:
                self.logger.error(f"Error deleting initiative from Cosmos DB: {str(e)}")
                # Fallback to in-memory deletion
                if initiative_id in self.initiatives_cache:
                    del self.initiatives_cache[initiative_id]
        else:
            # Delete from memory
            if initiative_id in self.initiatives_cache:
                del self.initiatives_cache[initiative_id]
                self.logger.info(f"Deleted initiative from memory: {initiative_id}")
        
        return True
    
    # Action CRUD Operations
    
    async def add_action(self, initiative_id: UUID, action_create: ActionCreate) -> Action:
        """
        Add an action to an initiative
        
        Args:
            initiative_id: ID of the initiative to add an action to
            action_create: Action data to create
            
        Returns:
            The created Action object
            
        Raises:
            HTTPException: If the initiative is not found
        """
        # Get the initiative
        try:
            initiative = await self.get_initiative(initiative_id)
        except HTTPException:
            raise HTTPException(status_code=404, detail=f"Initiative with ID {initiative_id} not found")
        
        # Generate a new ID for the action
        action_id = uuid.uuid4()
        
        # Current timestamp
        current_time = datetime.now()
        
        # Create the Action object
        action = Action(
            id=action_id,
            title=action_create.title,
            description=action_create.description,
            status=action_create.status,
            start_date=action_create.start_date,
            due_date=action_create.due_date,
            owner=action_create.owner,
            created_at=current_time,
            updated_at=current_time
        )
        
        # Add action to initiative and update
        initiative.actions.append(action)
        initiative.updated_at = current_time
        
        # Update initiative in database or memory
        if self.cosmos_db_available:
            try:
                initiative_dict = initiative.dict()
                # Convert UUID to string for Cosmos DB
                initiative_dict["id"] = str(initiative_dict["id"])
                if initiative_dict.get("strategic_goal_id"):
                    initiative_dict["strategic_goal_id"] = str(initiative_dict["strategic_goal_id"])
                
                # Convert action, resource, and risk IDs to strings
                for action_item in initiative_dict.get("actions", []):
                    action_item["id"] = str(action_item["id"])
                
                for resource in initiative_dict.get("resources", []):
                    resource["id"] = str(resource["id"])
                
                for risk in initiative_dict.get("risks", []):
                    risk["id"] = str(risk["id"])
                
                # Update in Cosmos DB
                await self.initiatives_container.replace_item(
                    item=str(initiative_id),
                    body=initiative_dict
                )
                self.logger.info(f"Added action to initiative in Cosmos DB: {initiative_id}")
            except Exception as e:
                self.logger.error(f"Error adding action to initiative in Cosmos DB: {str(e)}")
                # Fallback to in-memory storage
                self.initiatives_cache[initiative_id] = initiative
        else:
            # Update in memory
            self.initiatives_cache[initiative_id] = initiative
            self.logger.info(f"Added action to initiative in memory: {initiative_id}")
        
        return action
    
    async def update_action(self, initiative_id: UUID, action_id: UUID, action_update: ActionCreate) -> Action:
        """
        Update an action within an initiative
        
        Args:
            initiative_id: ID of the initiative containing the action
            action_id: ID of the action to update
            action_update: Updated action data
            
        Returns:
            Updated Action object
            
        Raises:
            HTTPException: If the initiative or action is not found
        """
        # Get the initiative
        try:
            initiative = await self.get_initiative(initiative_id)
        except HTTPException:
            raise HTTPException(status_code=404, detail=f"Initiative with ID {initiative_id} not found")
        
        # Find the action to update
        action_index = None
        for i, action in enumerate(initiative.actions):
            if action.id == action_id:
                action_index = i
                break
        
        if action_index is None:
            raise HTTPException(status_code=404, detail=f"Action with ID {action_id} not found in initiative {initiative_id}")
        
        # Current timestamp
        current_time = datetime.now()
        
        # Create updated action
        updated_action = Action(
            id=action_id,
            title=action_update.title,
            description=action_update.description,
            status=action_update.status,
            start_date=action_update.start_date,
            due_date=action_update.due_date,
            owner=action_update.owner,
            created_at=initiative.actions[action_index].created_at,
            updated_at=current_time
        )
        
        # Update action in initiative
        initiative.actions[action_index] = updated_action
        initiative.updated_at = current_time
        
        # Update initiative in database or memory
        if self.cosmos_db_available:
            try:
                initiative_dict = initiative.dict()
                # Convert UUID to string for Cosmos DB
                initiative_dict["id"] = str(initiative_dict["id"])
                if initiative_dict.get("strategic_goal_id"):
                    initiative_dict["strategic_goal_id"] = str(initiative_dict["strategic_goal_id"])
                
                # Convert action, resource, and risk IDs to strings
                for action_item in initiative_dict.get("actions", []):
                    action_item["id"] = str(action_item["id"])
                
                for resource in initiative_dict.get("resources", []):
                    resource["id"] = str(resource["id"])
                
                for risk in initiative_dict.get("risks", []):
                    risk["id"] = str(risk["id"])
                
                # Update in Cosmos DB
                await self.initiatives_container.replace_item(
                    item=str(initiative_id),
                    body=initiative_dict
                )
                self.logger.info(f"Updated action in initiative in Cosmos DB: {initiative_id}")
            except Exception as e:
                self.logger.error(f"Error updating action in initiative in Cosmos DB: {str(e)}")
                # Fallback to in-memory storage
                self.initiatives_cache[initiative_id] = initiative
        else:
            # Update in memory
            self.initiatives_cache[initiative_id] = initiative
            self.logger.info(f"Updated action in initiative in memory: {initiative_id}")
        
        return updated_action
    
    async def delete_action(self, initiative_id: UUID, action_id: UUID) -> bool:
        """
        Delete an action from an initiative
        
        Args:
            initiative_id: ID of the initiative containing the action
            action_id: ID of the action to delete
            
        Returns:
            True if successful, False otherwise
            
        Raises:
            HTTPException: If the initiative or action is not found
        """
        # Get the initiative
        try:
            initiative = await self.get_initiative(initiative_id)
        except HTTPException:
            raise HTTPException(status_code=404, detail=f"Initiative with ID {initiative_id} not found")
        
        # Find the action to delete
        action_index = None
        for i, action in enumerate(initiative.actions):
            if action.id == action_id:
                action_index = i
                break
        
        if action_index is None:
            raise HTTPException(status_code=404, detail=f"Action with ID {action_id} not found in initiative {initiative_id}")
        
        # Remove the action
        initiative.actions.pop(action_index)
        initiative.updated_at = datetime.now()
        
        # Update initiative in database or memory
        if self.cosmos_db_available:
            try:
                initiative_dict = initiative.dict()
                # Convert UUID to string for Cosmos DB
                initiative_dict["id"] = str(initiative_dict["id"])
                if initiative_dict.get("strategic_goal_id"):
                    initiative_dict["strategic_goal_id"] = str(initiative_dict["strategic_goal_id"])
                
                # Convert action, resource, and risk IDs to strings
                for action_item in initiative_dict.get("actions", []):
                    action_item["id"] = str(action_item["id"])
                
                for resource in initiative_dict.get("resources", []):
                    resource["id"] = str(resource["id"])
                
                for risk in initiative_dict.get("risks", []):
                    risk["id"] = str(risk["id"])
                
                # Update in Cosmos DB
                await self.initiatives_container.replace_item(
                    item=str(initiative_id),
                    body=initiative_dict
                )
                self.logger.info(f"Deleted action from initiative in Cosmos DB: {initiative_id}")
            except Exception as e:
                self.logger.error(f"Error deleting action from initiative in Cosmos DB: {str(e)}")
                # Fallback to in-memory storage
                self.initiatives_cache[initiative_id] = initiative
        else:
            # Update in memory
            self.initiatives_cache[initiative_id] = initiative
            self.logger.info(f"Deleted action from initiative in memory: {initiative_id}")
        
        return True
    
    # StrategicPlan CRUD Operations
    
    async def create_plan(self, plan_create: StrategicPlanCreate) -> StrategicPlan:
        """
        Create a new strategic plan
        
        Args:
            plan_create: Plan data to create
            
        Returns:
            The created StrategicPlan object
        """
        # Generate a new ID
        plan_id = uuid.uuid4()
        
        # Current timestamp
        current_time = datetime.now()
        
        # Construct the StrategicPlan object
        plan = StrategicPlan(
            id=plan_id,
            title=plan_create.title,
            description=plan_create.description,
            status=plan_create.status,
            time_horizon=plan_create.time_horizon,
            start_date=plan_create.start_date,
            end_date=plan_create.end_date,
            created_at=current_time,
            updated_at=current_time
        )
        
        # Store in database or memory
        if self.cosmos_db_available:
            try:
                plan_dict = plan.dict()
                # Convert UUID to string for Cosmos DB
                plan_dict["id"] = str(plan_dict["id"])
                
                # Store in Cosmos DB
                await self.plans_container.create_item(body=plan_dict)
                self.logger.info(f"Created strategic plan in Cosmos DB: {plan_id}")
            except Exception as e:
                self.logger.error(f"Error creating strategic plan in Cosmos DB: {str(e)}")
                # Fallback to in-memory storage
                self.plans_cache[plan_id] = plan
        else:
            # Store in memory
            self.plans_cache[plan_id] = plan
            self.logger.info(f"Created strategic plan in memory: {plan_id}")
        
        return plan

    # Aliases used by routers
    async def create_strategic_plan(self, plan_create: StrategicPlanCreate) -> StrategicPlan:
        return await self.create_plan(plan_create)
    
    async def get_plan(self, plan_id: UUID) -> StrategicPlan:
        """
        Get a strategic plan by ID
        
        Args:
            plan_id: The UUID of the plan to retrieve
            
        Returns:
            The StrategicPlan object
            
        Raises:
            HTTPException: If the plan is not found
        """
        # Try to get from database first
        if self.cosmos_db_available:
            try:
                # Query for the plan
                query = f"SELECT * FROM c WHERE c.id = @id"
                params = [{"name": "@id", "value": str(plan_id)}]
                
                results = []
                async for item in self.plans_container.query_items(
                    query=query, 
                    parameters=params, 
                    enable_cross_partition_query=True
                ):
                    # Convert string IDs back to UUID
                    item["id"] = UUID(item["id"])
                    
                    # Create StrategicPlan object from dict
                    plan = StrategicPlan(**item)
                    results.append(plan)
                
                if results:
                    return results[0]
            except Exception as e:
                self.logger.error(f"Error retrieving strategic plan from Cosmos DB: {str(e)}")
        
        # Try from memory if not found in database or if database is unavailable
        if plan_id in self.plans_cache:
            return self.plans_cache[plan_id]
        
        # Not found
        raise HTTPException(status_code=404, detail=f"Strategic plan with ID {plan_id} not found")

    async def get_strategic_plan(self, plan_id: UUID) -> StrategicPlan:
        return await self.get_plan(plan_id)
    
    async def list_plans(self) -> List[StrategicPlan]:
        """
        List all strategic plans
        
        Returns:
            List of StrategicPlan objects
        """
        plans = []
        
        # Try to get from database first
        if self.cosmos_db_available:
            try:
                query = "SELECT * FROM c"
                
                async for item in self.plans_container.query_items(
                    query=query, 
                    enable_cross_partition_query=True
                ):
                    # Convert string IDs back to UUID
                    item["id"] = UUID(item["id"])
                    
                    # Create StrategicPlan object from dict
                    plan = StrategicPlan(**item)
                    plans.append(plan)
                
                return plans
            except Exception as e:
                self.logger.error(f"Error listing strategic plans from Cosmos DB: {str(e)}")
        
        # Return from memory if database is unavailable
        return list(self.plans_cache.values())

    async def list_strategic_plans(self) -> List[StrategicPlan]:
        return await self.list_plans()
    
    async def update_plan(self, plan_id: UUID, plan_update: StrategicPlanCreate) -> StrategicPlan:
        """
        Update an existing strategic plan
        
        Args:
            plan_id: ID of the plan to update
            plan_update: Updated plan data
            
        Returns:
            Updated StrategicPlan object
            
        Raises:
            HTTPException: If the plan is not found
        """
        # Get the existing plan to update
        try:
            existing_plan = await self.get_plan(plan_id)
        except HTTPException:
            raise HTTPException(status_code=404, detail=f"Strategic plan with ID {plan_id} not found")
        
        # Update timestamp
        current_time = datetime.now()
        
        # Create updated plan object
        updated_plan = StrategicPlan(
            id=plan_id,
            title=plan_update.title,
            description=plan_update.description,
            status=plan_update.status,
            time_horizon=plan_update.time_horizon,
            start_date=plan_update.start_date,
            end_date=plan_update.end_date,
            created_at=existing_plan.created_at,
            updated_at=current_time
        )
        
        # Update in database or memory
        if self.cosmos_db_available:
            try:
                plan_dict = updated_plan.dict()
                # Convert UUID to string for Cosmos DB
                plan_dict["id"] = str(plan_dict["id"])
                
                # Update in Cosmos DB
                await self.plans_container.replace_item(
                    item=str(plan_id),
                    body=plan_dict
                )
                self.logger.info(f"Updated strategic plan in Cosmos DB: {plan_id}")
            except Exception as e:
                self.logger.error(f"Error updating strategic plan in Cosmos DB: {str(e)}")
                # Fallback to in-memory storage
                self.plans_cache[plan_id] = updated_plan
        else:
            # Update in memory
            self.plans_cache[plan_id] = updated_plan
            self.logger.info(f"Updated strategic plan in memory: {plan_id}")
        
        return updated_plan

    async def update_strategic_plan(self, plan_id: UUID, plan_update: StrategicPlanCreate) -> StrategicPlan:
        return await self.update_plan(plan_id, plan_update)
    
    async def delete_plan(self, plan_id: UUID) -> bool:
        """
        Delete a strategic plan by ID
        
        Args:
            plan_id: ID of the plan to delete
            
        Returns:
            True if successful, False otherwise
            
        Raises:
            HTTPException: If the plan is not found
        """
        # Check if plan exists
        try:
            await self.get_plan(plan_id)
        except HTTPException:
            raise HTTPException(status_code=404, detail=f"Strategic plan with ID {plan_id} not found")
        
        # Delete from database or memory
        if self.cosmos_db_available:
            try:
                await self.plans_container.delete_item(
                    item=str(plan_id),
                    partition_key=str(plan_id)
                )
                self.logger.info(f"Deleted strategic plan from Cosmos DB: {plan_id}")
            except Exception as e:
                self.logger.error(f"Error deleting strategic plan from Cosmos DB: {str(e)}")
                # Fallback to in-memory deletion
                if plan_id in self.plans_cache:
                    del self.plans_cache[plan_id]
        else:
            # Delete from memory
            if plan_id in self.plans_cache:
                del self.plans_cache[plan_id]
                self.logger.info(f"Deleted strategic plan from memory: {plan_id}")
        
        return True

    async def delete_strategic_plan(self, plan_id: UUID) -> bool:
        return await self.delete_plan(plan_id)

    # ----- Advanced Planning Features -----
    async def analyze_plan_alignment(self, plan_id: UUID) -> Dict[str, Any]:
        """Analyze how well initiatives align with strategic goals."""
        plan = await self.get_plan(plan_id)

        if not plan.initiatives:
            score = 0.0
        else:
            linked = sum(1 for i in plan.initiatives if i.linked_strategic_goal)
            score = round((linked / len(plan.initiatives)) * 10, 2)

        plan.overall_alignment_score = score
        self.plans_cache[plan_id] = plan
        if self.cosmos_db_available and self.plans_container:
            try:
                plan_dict = plan.dict()
                plan_dict["id"] = str(plan_dict["id"])
                for initiative in plan_dict.get("initiatives", []):
                    initiative["id"] = str(initiative["id"])
                    if initiative.get("linked_strategic_goal"):
                        initiative["linked_strategic_goal"] = str(initiative["linked_strategic_goal"])
                await self.plans_container.replace_item(item=str(plan_id), body=plan_dict)
            except Exception:
                pass
        return {"plan_id": str(plan_id), "alignment_score": score}

    async def generate_plan_variants(
        self,
        base_plan_id: UUID,
        num_variants: int = 2,
        focus_areas: Optional[List[str]] = None,
    ) -> List[StrategicPlan]:
        base = await self.get_plan(base_plan_id)
        variants: List[StrategicPlan] = []
        for i in range(num_variants):
            variant = StrategicPlan(
                id=uuid.uuid4(),
                title=f"{base.title} Variant {i+1}",
                description=base.description,
                status=PlanStatus.DRAFT,
                time_horizon=base.time_horizon,
                start_date=base.start_date,
                end_date=base.end_date,
                initiatives=[],
                ai_recommendations=[f"Focus on {fa}" for fa in (focus_areas or [])],
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            self.plans_cache[variant.id] = variant
            variants.append(variant)
        return variants

    async def compare_plans(
        self,
        plan_ids: List[UUID],
        comparison_criteria: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Any]:
        plans = [await self.get_plan(pid) for pid in plan_ids]
        comparison = {str(p.id): len(p.initiatives) for p in plans}
        return {"initiative_counts": comparison}

    async def generate_actions(self, initiative_id: UUID) -> List[Action]:
        initiative = await self.get_initiative(initiative_id)
        new_actions: List[Action] = []
        for i in range(3):
            act = Action(
                id=uuid.uuid4(),
                title=f"Auto Action {i+1}",
                description=f"Generated for {initiative.title}",
            )
            initiative.actions.append(act)
            new_actions.append(act)
        self.initiatives_cache[initiative_id] = initiative
        return new_actions
