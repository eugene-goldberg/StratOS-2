import os
import uuid
import logging
from uuid import UUID
from datetime import datetime
from typing import List, Optional, Dict, Any, Union

from azure.cosmos.aio import CosmosClient as AsyncCosmosClient, DatabaseProxy, ContainerProxy
from azure.cosmos import PartitionKey, exceptions as CosmosExceptions
from fastapi import HTTPException, Depends # Added Depends

from ..models.planning import (
    StrategicPlan, StrategicPlanCreate, Initiative, InitiativeCreate,
    Action, ActionCreate, Resource, ResourceCreate, Risk, RiskCreate,
    PlanStatus, InitiativeType
)
from ..ai.kernel_service import kernel_service
from ..services.strategic_foundation_service import StrategicFoundationService
from ..dependencies import get_current_user_id # For user context in AI methods if needed directly

class PlanningService:
    """Service for managing strategic planning operations including initiatives and actions."""
    
    def __init__(self):
        self.logger = logging.getLogger("planning_service")
        self.plans_cache = {}
        self.initiatives_cache = {}
        self.foundation_service = StrategicFoundationService()
        
        self.cosmos_db_available = False
        self.cosmos_client: Optional[AsyncCosmosClient] = None
        self.database: Optional[DatabaseProxy] = None
        self.plans_container: Optional[ContainerProxy] = None
        self.initiatives_container: Optional[ContainerProxy] = None
        
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
            self.plans_container = self.database.get_container_client("StrategicPlans")
            self.initiatives_container = self.database.get_container_client("Initiatives")
            self.cosmos_db_available = True
            self.logger.info("Cosmos DB async client initialized for PlanningService.")
        except Exception as e:
            self.logger.warning(f"Cosmos DB async client initialization failed: {str(e)}. Using in-memory storage.")
            self.cosmos_db_available = False # Ensure this is set on failure
            self.cosmos_client = None
            self.database = None
            self.plans_container = None
            self.initiatives_container = None

    async def _save_initiative_to_db(self, initiative: Initiative):
        if not (self.cosmos_db_available and self.initiatives_container):
            self.logger.warning(f"Cosmos DB not available. Caching initiative {initiative.id} in memory only.")
            self.initiatives_cache[str(initiative.id)] = initiative
            return

        initiative_dict = initiative.dict()
        initiative_dict["id"] = str(initiative.id) # PK
        # Assuming Initiative model has user_id and plan_id for partitioning/querying
        if hasattr(initiative, 'user_id') and initiative.user_id:
             initiative_dict["user_id"] = str(initiative.user_id)
        if hasattr(initiative, 'plan_id') and initiative.plan_id:
             initiative_dict["plan_id"] = str(initiative.plan_id)
        if initiative.linked_strategic_goal:
            initiative_dict["linked_strategic_goal"] = str(initiative.linked_strategic_goal)
        
        for list_name in ["actions", "resources", "risks"]:
            if list_name in initiative_dict:
                for item_dict in initiative_dict[list_name]:
                    item_dict["id"] = str(item_dict["id"])
        try:
            # Initiatives container is partitioned by /id (initiative's own ID)
            await self.initiatives_container.upsert_item(body=initiative_dict)
            self.logger.info(f"Saved initiative {initiative.id} to Cosmos DB.")
            self.initiatives_cache[str(initiative.id)] = initiative
        except CosmosExceptions.CosmosHttpResponseError as e:
            self.logger.error(f"Error saving initiative {initiative.id} to Cosmos DB: {str(e)}")
            self.initiatives_cache[str(initiative.id)] = initiative

    # Initiative CRUD Operations
    async def create_initiative(self, plan_id: UUID, user_id: UUID, initiative_data: InitiativeCreate) -> Initiative:
        if initiative_data.linked_strategic_goal:
            goal = await self.foundation_service.get_strategic_goal(user_id, initiative_data.linked_strategic_goal)
            if not goal:
                raise HTTPException(status_code=400, detail=f"Linked strategic goal ID {initiative_data.linked_strategic_goal} not found for user.")

        initiative_id = uuid.uuid4()
        current_time = datetime.now()
        
        initiative = Initiative(
            id=initiative_id,
            plan_id=plan_id, # Assuming Initiative model will have plan_id
            user_id=user_id, # Assuming Initiative model will have user_id
            title=initiative_data.title, description=initiative_data.description,
            initiative_type=initiative_data.initiative_type, status=initiative_data.status,
            linked_strategic_goal=initiative_data.linked_strategic_goal,
            owner=initiative_data.owner, start_date=initiative_data.start_date, end_date=initiative_data.end_date,
            actions=[], risks=[], resources=[], key_metrics=[],
            created_at=current_time, updated_at=current_time
        )
        
        initiative_dict_for_db = initiative.dict()
        initiative_dict_for_db["id"] = str(initiative.id)
        initiative_dict_for_db["plan_id"] = str(initiative.plan_id)
        initiative_dict_for_db["user_id"] = str(initiative.user_id)
        if initiative.linked_strategic_goal:
            initiative_dict_for_db["linked_strategic_goal"] = str(initiative.linked_strategic_goal)

        if self.cosmos_db_available and self.initiatives_container:
            try:
                await self.initiatives_container.create_item(body=initiative_dict_for_db)
                self.logger.info(f"Created initiative {initiative_id} for plan {plan_id}, user {user_id} in Cosmos DB.")
            except CosmosExceptions.CosmosHttpResponseError as e:
                self.logger.error(f"Error creating initiative in Cosmos DB: {str(e)}")
                self.initiatives_cache[str(initiative_id)] = initiative
        else:
            self.initiatives_cache[str(initiative_id)] = initiative
            self.logger.info(f"Created initiative {initiative_id} for plan {plan_id}, user {user_id} in memory.")
        return initiative
    
    async def get_initiative(self, initiative_id: UUID) -> Initiative: # user_id for PK if /user_id is PK
        # If Initiatives are partitioned by /id, user_id is not needed for read_item's partition_key
        # but might be needed for cache key or further auth checks if not handled by router.
        # Assuming /id is PK for Initiatives container.
        if str(initiative_id) in self.initiatives_cache:
            return self.initiatives_cache[str(initiative_id)]

        if self.cosmos_db_available and self.initiatives_container:
            try:
                item_data = await self.initiatives_container.read_item(item=str(initiative_id), partition_key=str(initiative_id))
                item_data["id"] = UUID(item_data["id"])
                if item_data.get("plan_id"): item_data["plan_id"] = UUID(item_data["plan_id"])
                if item_data.get("user_id"): item_data["user_id"] = UUID(item_data["user_id"])
                if item_data.get("linked_strategic_goal"):
                    item_data["linked_strategic_goal"] = UUID(item_data["linked_strategic_goal"])
                for list_name in ["actions", "resources", "risks"]:
                    for item_dict in item_data.get(list_name, []):
                        item_dict["id"] = UUID(item_dict["id"])
                initiative = Initiative(**item_data)
                self.initiatives_cache[str(initiative_id)] = initiative
                return initiative
            except CosmosExceptions.CosmosResourceNotFoundError:
                raise HTTPException(status_code=404, detail=f"Initiative with ID {initiative_id} not found")
            except Exception as e:
                self.logger.error(f"Error retrieving initiative {initiative_id} from Cosmos DB: {str(e)}")
                raise HTTPException(status_code=500, detail="Error retrieving initiative")
        raise HTTPException(status_code=404, detail=f"Initiative {initiative_id} not found (DB unavailable/not in cache)")

    async def list_initiatives(self, plan_id: Optional[UUID] = None, user_id: Optional[UUID] = None) -> List[Initiative]:
        # Assuming Initiatives are partitioned by /id, so plan_id/user_id filtering requires query.
        # If partitioned by /user_id, then user_id would be PK for query.
        # If partitioned by /plan_id, then plan_id would be PK for query.
        # Current setup: partitioned by /id.
        initiatives_list: List[Initiative] = []
        if self.cosmos_db_available and self.initiatives_container:
            query = "SELECT * FROM c"
            params: List[Dict[str,Any]] = []
            conditions = []
            if plan_id: 
                conditions.append("c.plan_id = @plan_id")
                params.append({"name": "@plan_id", "value": str(plan_id)})
            if user_id:
                conditions.append("c.user_id = @user_id")
                params.append({"name": "@user_id", "value": str(user_id)})
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
                
            try:
                async for item_data in self.initiatives_container.query_items(query=query, parameters=params, enable_cross_partition_query=True):
                    item_data["id"] = UUID(item_data["id"])
                    if item_data.get("plan_id"): item_data["plan_id"] = UUID(item_data["plan_id"])
                    if item_data.get("user_id"): item_data["user_id"] = UUID(item_data["user_id"])
                    if item_data.get("linked_strategic_goal"): item_data["linked_strategic_goal"] = UUID(item_data["linked_strategic_goal"])
                    for list_name in ["actions", "resources", "risks"]:
                        for item_dict in item_data.get(list_name, []): item_dict["id"] = UUID(item_dict["id"])
                    initiatives_list.append(Initiative(**item_data))
                return initiatives_list
            except Exception as e:
                self.logger.error(f"Error listing initiatives: {str(e)}")
        
        # Fallback to cache
        cached_values = list(self.initiatives_cache.values())
        if plan_id: cached_values = [i for i in cached_values if hasattr(i, 'plan_id') and i.plan_id == plan_id]
        if user_id: cached_values = [i for i in cached_values if hasattr(i, 'user_id') and i.user_id == user_id]
        return cached_values

    async def update_initiative(self, initiative_id: UUID, user_id: UUID, initiative_update_data: Dict[str, Any]) -> Initiative:
        existing_initiative = await self.get_initiative(initiative_id) # Assumes get_initiative checks ownership or is fine
        if not (hasattr(existing_initiative, 'user_id') and existing_initiative.user_id == user_id):
             raise HTTPException(status_code=403, detail="User not authorized to update this initiative.")

        if "linked_strategic_goal" in initiative_update_data and initiative_update_data["linked_strategic_goal"]:
            goal_id_to_check = UUID(initiative_update_data["linked_strategic_goal"])
            goal = await self.foundation_service.get_strategic_goal(user_id, goal_id_to_check)
            if not goal:
                raise HTTPException(status_code=400, detail=f"Linked strategic goal ID {goal_id_to_check} not found for user.")
        
        update_payload = InitiativeCreate(**initiative_update_data)
        
        existing_initiative.title = update_payload.title
        existing_initiative.description = update_payload.description
        existing_initiative.initiative_type = update_payload.initiative_type
        existing_initiative.status = update_payload.status
        existing_initiative.linked_strategic_goal = update_payload.linked_strategic_goal
        existing_initiative.owner = update_payload.owner
        existing_initiative.start_date = update_payload.start_date
        existing_initiative.end_date = update_payload.end_date
        existing_initiative.updated_at = datetime.now()
        
        await self._save_initiative_to_db(existing_initiative)
        return existing_initiative
    
    async def delete_initiative(self, initiative_id: UUID, user_id: UUID) -> bool:
        # Add user_id check if Initiative model has user_id and it's not the PK
        initiative_to_delete = await self.get_initiative(initiative_id)
        if not (hasattr(initiative_to_delete, 'user_id') and initiative_to_delete.user_id == user_id):
            raise HTTPException(status_code=403, detail="User not authorized to delete this initiative.")

        if self.cosmos_db_available and self.initiatives_container:
            try:
                await self.initiatives_container.delete_item(item=str(initiative_id), partition_key=str(initiative_id))
                self.logger.info(f"Deleted initiative from Cosmos DB: {initiative_id}")
                if str(initiative_id) in self.initiatives_cache: del self.initiatives_cache[str(initiative_id)]
                return True
            except CosmosExceptions.CosmosHttpResponseError as e:
                self.logger.error(f"Error deleting initiative from Cosmos DB: {str(e)}")
                return False
        elif str(initiative_id) in self.initiatives_cache:
            del self.initiatives_cache[str(initiative_id)]
            self.logger.info(f"Deleted initiative from memory: {initiative_id}")
            return True
        return False

    # Nested Item Operations (Action, Resource, Risk)
    async def _add_nested_item(self, initiative_id: UUID, user_id: UUID, item_data: Union[ActionCreate, ResourceCreate, RiskCreate], item_type: str) -> Union[Action, Resource, Risk]:
        initiative = await self.get_initiative(initiative_id)
        if not (hasattr(initiative, 'user_id') and initiative.user_id == user_id):
            raise HTTPException(status_code=403, detail=f"User not authorized to modify this initiative's {item_type}s.")

        item_id = uuid.uuid4()
        current_time = datetime.now()
        ModelClass = {"action": Action, "resource": Resource, "risk": Risk}[item_type]
        list_attr = {"action": "actions", "resource": "resources", "risk": "risks"}[item_type]

        item = ModelClass(id=item_id, **item_data.dict(), created_at=current_time, updated_at=current_time)
        getattr(initiative, list_attr).append(item)
        initiative.updated_at = current_time
        await self._save_initiative_to_db(initiative)
        return item

    async def create_action(self, initiative_id: UUID, user_id: UUID, action_data: ActionCreate) -> Action:
        return await self._add_nested_item(initiative_id, user_id, action_data, "action")

    async def create_resource(self, initiative_id: UUID, user_id: UUID, resource_data: ResourceCreate) -> Resource:
        return await self._add_nested_item(initiative_id, user_id, resource_data, "resource")

    async def create_risk(self, initiative_id: UUID, user_id: UUID, risk_data: RiskCreate) -> Risk:
        return await self._add_nested_item(initiative_id, user_id, risk_data, "risk")

    async def _update_nested_item(self, initiative_id: UUID, user_id: UUID, item_id: UUID, item_update_data: Dict[str, Any], item_type: str) -> Optional[Union[Action, Resource, Risk]]:
        initiative = await self.get_initiative(initiative_id)
        if not (hasattr(initiative, 'user_id') and initiative.user_id == user_id):
            raise HTTPException(status_code=403, detail=f"User not authorized to modify this initiative's {item_type}s.")

        ModelClass = {"action": Action, "resource": Resource, "risk": Risk}[item_type]
        CreateClass = {"action": ActionCreate, "resource": ResourceCreate, "risk": RiskCreate}[item_type]
        list_attr = {"action": "actions", "resource": "resources", "risk": "risks"}[item_type]
        item_list = getattr(initiative, list_attr)
        
        item_index = next((i for i, item in enumerate(item_list) if item.id == item_id), -1)
        if item_index == -1:
            raise HTTPException(status_code=404, detail=f"{item_type.capitalize()} ID {item_id} not found in initiative {initiative_id}")

        update_payload = CreateClass(**item_update_data)
        original_item = item_list[item_index]
        updated_item_dict = original_item.dict()
        updated_item_dict.update(update_payload.dict(exclude_unset=True))
        updated_item_dict["updated_at"] = datetime.now()
        
        updated_item = ModelClass(**updated_item_dict)
        item_list[item_index] = updated_item
        initiative.updated_at = datetime.now()
        await self._save_initiative_to_db(initiative)
        return updated_item

    async def update_action(self, initiative_id: UUID, user_id: UUID, action_id: UUID, action_data: Dict[str, Any]) -> Action:
        return await self._update_nested_item(initiative_id, user_id, action_id, action_data, "action")

    async def _delete_nested_item(self, initiative_id: UUID, user_id: UUID, item_id: UUID, item_type: str) -> bool:
        initiative = await self.get_initiative(initiative_id)
        if not (hasattr(initiative, 'user_id') and initiative.user_id == user_id):
            raise HTTPException(status_code=403, detail=f"User not authorized to modify this initiative's {item_type}s.")

        list_attr = {"action": "actions", "resource": "resources", "risk": "risks"}[item_type]
        item_list = getattr(initiative, list_attr)
        original_len = len(item_list)
        setattr(initiative, list_attr, [item for item in item_list if item.id != item_id])
        
        if len(getattr(initiative, list_attr)) == original_len:
            raise HTTPException(status_code=404, detail=f"{item_type.capitalize()} ID {item_id} not found.")
            
        initiative.updated_at = datetime.now()
        await self._save_initiative_to_db(initiative)
        return True

    async def delete_action(self, initiative_id: UUID, user_id: UUID, action_id: UUID) -> bool:
        return await self._delete_nested_item(initiative_id, user_id, action_id, "action")

    # StrategicPlan CRUD Operations (assuming user_id is part of StrategicPlan model for ownership)
    async def create_strategic_plan(self, user_id: UUID, plan_data: StrategicPlanCreate) -> StrategicPlan:
        plan_id = uuid.uuid4()
        current_time = datetime.now()
        plan = StrategicPlan(id=plan_id, user_id=user_id, **plan_data.dict(), created_at=current_time, updated_at=current_time)
        
        plan_dict_for_db = plan.dict()
        plan_dict_for_db["id"] = str(plan.id)
        plan_dict_for_db["user_id"] = str(plan.user_id)

        if self.cosmos_db_available and self.plans_container:
            try:
                await self.plans_container.create_item(body=plan_dict_for_db)
            except CosmosExceptions.CosmosHttpResponseError as e:
                self.logger.error(f"Error creating plan: {str(e)}")
                self.plans_cache[str(plan_id)] = plan # Fallback
        else:
            self.plans_cache[str(plan_id)] = plan
        return plan

    async def get_strategic_plan(self, plan_id: UUID, user_id: UUID) -> StrategicPlan:
        # Plans container partitioned by /id (plan's own ID)
        # Ownership check via user_id field in the document.
        if str(plan_id) in self.plans_cache and self.plans_cache[str(plan_id)].user_id == user_id:
            return self.plans_cache[str(plan_id)]
        if self.cosmos_db_available and self.plans_container:
            try:
                item_data = await self.plans_container.read_item(item=str(plan_id), partition_key=str(plan_id))
                if UUID(item_data.get("user_id")) != user_id:
                    raise HTTPException(status_code=403, detail="User not authorized to access this plan.")
                item_data["id"] = UUID(item_data["id"])
                item_data["user_id"] = UUID(item_data["user_id"])
                plan = StrategicPlan(**item_data)
                self.plans_cache[str(plan_id)] = plan
                return plan
            except CosmosExceptions.CosmosResourceNotFoundError:
                raise HTTPException(status_code=404, detail=f"Plan {plan_id} not found.")
            except Exception as e:
                self.logger.error(f"Error getting plan {plan_id}: {str(e)}")
                raise HTTPException(status_code=500, detail="Error retrieving plan.")
        raise HTTPException(status_code=404, detail=f"Plan {plan_id} not found (DB or cache).")

    async def list_strategic_plans(self, user_id: UUID, status: Optional[PlanStatus] = None, limit: int = 10, offset: int = 0) -> List[StrategicPlan]:
        # Query by user_id. This will be cross-partition if /id is PK for StrategicPlans.
        # If StrategicPlans was partitioned by /user_id, this would be more efficient.
        # For now, assuming /id is PK as per original code.
        plans_list: List[StrategicPlan] = []
        if self.cosmos_db_available and self.plans_container:
            query_parts = ["SELECT * FROM c WHERE c.user_id = @user_id"]
            params: List[Dict[str,Any]] = [{"name": "@user_id", "value": str(user_id)}]
            if status:
                query_parts.append("AND c.status = @status")
                params.append({"name": "@status", "value": status.value})
            # OFFSET/LIMIT in Cosmos query string is not standard for async SDK, but let's try
            query = " ".join(query_parts) + f" ORDER BY c.created_at DESC OFFSET {offset} LIMIT {limit}"
            try:
                async for item_data in self.plans_container.query_items(query=query, parameters=params, enable_cross_partition_query=True): # Must be cross-partition
                    item_data["id"] = UUID(item_data["id"])
                    item_data["user_id"] = UUID(item_data["user_id"])
                    plans_list.append(StrategicPlan(**item_data))
                return plans_list
            except Exception as e:
                self.logger.error(f"Error listing plans for user {user_id}: {str(e)}")
        
        cached_plans = [p for p in self.plans_cache.values() if p.user_id == user_id]
        if status: cached_plans = [p for p in cached_plans if p.status == status]
        cached_plans.sort(key=lambda p: p.created_at, reverse=True)
        return cached_plans[offset : offset + limit]
        
    async def update_strategic_plan(self, plan_id: UUID, user_id: UUID, plan_data: Dict[str, Any]) -> StrategicPlan:
        existing_plan = await self.get_strategic_plan(plan_id, user_id) # Ensures ownership
        
        update_payload = StrategicPlanCreate(**plan_data)
        existing_plan.title = update_payload.title
        existing_plan.description = update_payload.description
        existing_plan.status = update_payload.status
        existing_plan.time_horizon = update_payload.time_horizon
        existing_plan.start_date = update_payload.start_date
        existing_plan.end_date = update_payload.end_date
        existing_plan.updated_at = datetime.now()
        
        plan_dict_for_db = existing_plan.dict()
        plan_dict_for_db["id"] = str(existing_plan.id)
        plan_dict_for_db["user_id"] = str(existing_plan.user_id)

        if self.cosmos_db_available and self.plans_container:
            try:
                await self.plans_container.replace_item(item=str(plan_id), body=plan_dict_for_db, partition_key=str(plan_id))
            except CosmosExceptions.CosmosHttpResponseError as e:
                self.logger.error(f"Error updating plan {plan_id}: {str(e)}")
                self.plans_cache[str(plan_id)] = existing_plan # Fallback
        else:
            self.plans_cache[str(plan_id)] = existing_plan
        return existing_plan

    async def delete_strategic_plan(self, plan_id: UUID, user_id: UUID) -> bool:
        await self.get_strategic_plan(plan_id, user_id) # Ensures ownership & existence
        if self.cosmos_db_available and self.plans_container:
            try:
                await self.plans_container.delete_item(item=str(plan_id), partition_key=str(plan_id))
                if str(plan_id) in self.plans_cache: del self.plans_cache[str(plan_id)]
                # TODO: Consider deleting associated initiatives
                return True
            except CosmosExceptions.CosmosHttpResponseError as e:
                self.logger.error(f"Error deleting plan {plan_id}: {str(e)}")
                return False
        elif str(plan_id) in self.plans_cache:
             del self.plans_cache[str(plan_id)]
             return True
        return False

    # ----- AI-Powered Planning Features -----
    async def analyze_plan_alignment(self, plan_id: UUID, user_id: UUID) -> Dict[str, Any]:
        plan = await self.get_strategic_plan(plan_id, user_id)
        initiatives = await self.list_initiatives(plan_id=plan_id, user_id=user_id) # Fetch initiatives for this plan and user
        
        # Basic quantitative score
        score = 0.0
        if initiatives:
            linked_initiatives = sum(1 for i in initiatives if i.linked_strategic_goal)
            score = round((linked_initiatives / len(initiatives)) * 10, 2) if initiatives else 0.0

        # Qualitative analysis with LLM
        initiative_summaries = "\n".join([f"- {i.title}: {i.description or 'No description.'}" for i in initiatives])
        north_star = await self.foundation_service.get_north_star(user_id)
        north_star_context = "User's North Star is not defined."
        if north_star:
            ns_parts = [f"Purpose: {north_star.purpose.statement}"]
            if north_star.vision: ns_parts.append(f"Vision: {north_star.vision.statement}")
            if north_star.strategic_goals: ns_parts.append(f"Goals: {', '.join([g.title for g in north_star.strategic_goals])}")
            north_star_context = "\n".join(ns_parts)

        prompt = (
            f"Analyze the alignment of the following strategic plan initiatives with the user's North Star.\n"
            f"User's North Star:\n{north_star_context}\n\n"
            f"Plan Title: {plan.title}\nPlan Description: {plan.description or 'N/A'}\n"
            f"Initiatives:\n{initiative_summaries if initiatives else 'No initiatives defined.'}\n\n"
            f"Provide: \n1. An overall alignment assessment (Good, Fair, Poor). \n2. A brief explanation for the assessment. \n3. Suggest 1-2 areas for improvement if alignment is not Good."
            f"Return as a JSON object with keys 'assessment', 'explanation', 'suggestions'."
        )
        try:
            response_str = await kernel_service.generate_completion(prompt, max_tokens=300)
            ai_analysis = json.loads(response_str)
        except Exception as e:
            self.logger.error(f"LLM error in analyze_plan_alignment: {e}")
            ai_analysis = {"assessment": "Error", "explanation": str(e), "suggestions": []}
        
        # Update plan with score (if model supports it)
        # plan.overall_alignment_score = score # Example
        # await self._save_plan_to_db(plan) # If plan model is updated

        return {"plan_id": str(plan_id), "quantitative_score": score, "ai_analysis": ai_analysis}

    async def generate_plan_variants(self, base_plan_id: UUID, user_id: UUID, num_variants: int = 2, focus_areas: Optional[List[str]] = None) -> List[StrategicPlan]:
        base_plan = await self.get_strategic_plan(base_plan_id, user_id)
        variants: List[StrategicPlan] = []

        prompt_context = (
            f"Base Plan Title: {base_plan.title}\n"
            f"Base Plan Description: {base_plan.description or 'N/A'}\n"
            f"Base Plan Time Horizon: {base_plan.time_horizon}\n"
            f"Focus Areas for Variants: {', '.join(focus_areas) if focus_areas else 'General strategic alternatives'}\n"
            f"Generate {num_variants} distinct strategic plan variant summaries (title, description) based on the base plan and focus areas."
            f"Return as a JSON list of objects, each with 'title' and 'description'."
        )
        try:
            response_str = await kernel_service.generate_completion(prompt_context, max_tokens=200 * num_variants)
            generated_variants_data = json.loads(response_str)
        except Exception as e:
            self.logger.error(f"LLM error in generate_plan_variants: {e}")
            generated_variants_data = []

        for i, variant_data_from_ai in enumerate(generated_variants_data[:num_variants]):
            variant_create_data = StrategicPlanCreate(
                title=variant_data_from_ai.get("title", f"{base_plan.title} - AI Variant {i+1}"),
                description=variant_data_from_ai.get("description", f"AI generated variant focusing on: {', '.join(focus_areas) if focus_areas else 'alternative approach'}"),
                status=PlanStatus.DRAFT,
                time_horizon=base_plan.time_horizon, # Inherit from base
                start_date=base_plan.start_date,
                end_date=base_plan.end_date
            )
            variant = await self.create_strategic_plan(user_id, variant_create_data)
            if focus_areas and hasattr(variant, 'ai_recommendations'): # If model supports this field
                 variant.ai_recommendations = [f"Generated based on focus: {fa}" for fa in focus_areas]
                 await self.update_strategic_plan(variant.id, user_id, variant.dict())
            variants.append(variant)
        return variants

    async def compare_plans(self, plan_ids: List[UUID], user_id: UUID, comparison_criteria: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
        plans_data = []
        for pid in plan_ids:
            plan = await self.get_strategic_plan(pid, user_id)
            initiatives = await self.list_initiatives(plan_id=pid, user_id=user_id)
            plans_data.append({
                "id": str(plan.id), "title": plan.title, "description": plan.description,
                "status": plan.status.value, "initiative_count": len(initiatives),
                # "alignment_score": getattr(plan, 'overall_alignment_score', 'N/A') # If field exists
            })
        
        prompt = (
            f"Compare the following strategic plans based on the provided data and criteria (if any).\n"
            f"Plans Data:\n{json.dumps(plans_data)}\n"
            f"Comparison Criteria (optional weights): {json.dumps(comparison_criteria) if comparison_criteria else 'General comparison'}\n"
            f"Provide a comparative summary, highlighting strengths and weaknesses of each. Identify which plan seems strongest and why."
            f"Return as a JSON object with keys 'summary' and 'recommendation'."
        )
        try:
            response_str = await kernel_service.generate_completion(prompt, max_tokens=500)
            ai_comparison = json.loads(response_str)
        except Exception as e:
            self.logger.error(f"LLM error in compare_plans: {e}")
            ai_comparison = {"summary": "Error in AI comparison.", "recommendation": "Unable to recommend."}
        
        return {"plans_compared": [str(pid) for pid in plan_ids], "ai_comparison": ai_comparison}

    async def generate_actions(self, initiative_id: UUID, user_id: UUID) -> List[Action]:
        initiative = await self.get_initiative(initiative_id) # Assuming get_initiative checks ownership via user_id if needed
        if not (hasattr(initiative, 'user_id') and initiative.user_id == user_id):
             raise HTTPException(status_code=403, detail="User not authorized for this initiative.")

        new_actions: List[Action] = []
        prompt = (
            f"Suggest three concrete, actionable steps for the following strategic initiative:\n"
            f"Initiative Title: {initiative.title}\n"
            f"Initiative Description: {initiative.description or 'N/A'}\n"
            f"Current Status: {initiative.status.value}\n"
            f"Desired Outcome: (Infer from title and description)\n"
            f"Return as a JSON list of strings, where each string is an action title."
        )
        try:
            response_str = await kernel_service.generate_completion(prompt, max_tokens=200)
            action_titles = json.loads(response_str)
            if not isinstance(action_titles, list): action_titles = []
        except Exception as e:
            self.logger.error(f"LLM error generating actions for initiative {initiative_id}: {e}")
            action_titles = []

        if not action_titles: # Fallback
            action_titles = [f"Define detailed scope for {initiative.title}", f"Assign team and resources for {initiative.title}", f"Establish key milestones for {initiative.title}"]

        for title in action_titles[:3]: # Max 3 actions
            action_data = ActionCreate(title=title, description=f"AI-generated action for '{initiative.title}'", status="todo")
            action = await self.create_action(initiative_id, user_id, action_data)
            new_actions.append(action)
        return new_actions
