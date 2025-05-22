import os
import uuid
import json
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
    PlanStatus, InitiativeType, ActionStatus
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

        initiative_dict = initiative.model_dump()
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
        
        initiative_dict_for_db = initiative.model_dump()
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

        item = ModelClass(id=item_id, **item_data.model_dump(), created_at=current_time, updated_at=current_time)
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
        updated_item_dict = original_item.model_dump()
        updated_item_dict.update(update_payload.model_dump(exclude_unset=True))
        
        # Handle Enum fields that might be passed as strings
        if item_type == "action" and "status" in item_update_data:
            if isinstance(item_update_data["status"], str):
                updated_item_dict["status"] = ActionStatus(item_update_data["status"])
                
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
        plan = StrategicPlan(id=plan_id, user_id=user_id, **plan_data.model_dump(), created_at=current_time, updated_at=current_time)
        
        plan_dict_for_db = plan.model_dump()
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
        
        plan_dict_for_db = existing_plan.model_dump()
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
            f"As a strategic planning expert, analyze the alignment between this strategic plan and the organization's North Star foundation.\n\n"
            f"STRATEGIC FOUNDATION:\n{north_star_context}\n\n"
            f"STRATEGIC PLAN DETAILS:\n"
            f"Title: {plan.title}\n"
            f"Description: {plan.description or 'N/A'}\n"
            f"Time Horizon: {plan.time_horizon}\n"
            f"Status: {plan.status.value}\n\n"
            f"INITIATIVES ({len(initiatives)} total):\n{initiative_summaries if initiatives else 'No initiatives defined.'}\n\n"
            f"ANALYSIS REQUIREMENTS:\n"
            f"1. PURPOSE ALIGNMENT: How well do the initiatives support the organization's purpose? Identify specific connections and gaps.\n"
            f"2. VISION COHERENCE: Do the initiatives collectively move toward the stated vision? What's missing or misaligned?\n"
            f"3. STRATEGIC GOAL COVERAGE: Which strategic goals are well-supported vs. under-addressed by current initiatives?\n"
            f"4. VALUES INTEGRATION: How do the initiatives reflect and reinforce the organization's core values?\n"
            f"5. OVERALL STRATEGIC COHESION: Do initiatives work synergistically or operate in isolation?\n\n"
            f"Provide detailed qualitative feedback that helps leadership understand:\n"
            f"- Specific strengths in strategic alignment\n"
            f"- Critical gaps that need attention\n"
            f"- Concrete recommendations for improving alignment\n"
            f"- Strategic risks from current misalignments\n\n"
            f"Return as JSON with keys: 'overall_assessment' (Excellent/Good/Fair/Poor), 'purpose_alignment', 'vision_coherence', 'goal_coverage', 'values_integration', 'strategic_cohesion', 'key_strengths', 'critical_gaps', 'recommendations', 'strategic_risks'."
        )
        try:
            response_str = await kernel_service.generate_completion(prompt, max_tokens=1000)
            ai_analysis = json.loads(response_str)
        except Exception as e:
            self.logger.error(f"LLM error in analyze_plan_alignment: {e}")
            ai_analysis = {"overall_assessment": "Error", "purpose_alignment": str(e), "recommendations": []}
        
        # Update plan with score (if model supports it)
        # plan.overall_alignment_score = score # Example
        # await self._save_plan_to_db(plan) # If plan model is updated

        return {"plan_id": str(plan_id), "quantitative_score": score, "ai_analysis": ai_analysis}

    async def generate_plan_variants(self, base_plan_id: UUID, user_id: UUID, num_variants: int = 2, focus_areas: Optional[List[str]] = None) -> List[StrategicPlan]:
        base_plan = await self.get_strategic_plan(base_plan_id, user_id)
        initiatives = await self.list_initiatives(plan_id=base_plan_id, user_id=user_id)
        north_star = await self.foundation_service.get_north_star(user_id)
        variants: List[StrategicPlan] = []

        # Build strategic context
        north_star_context = "No strategic foundation defined."
        if north_star:
            ns_parts = [f"Purpose: {north_star.purpose.statement}"]
            if north_star.vision: ns_parts.append(f"Vision: {north_star.vision.statement}")
            if north_star.values: ns_parts.append(f"Values: {', '.join([v.name for v in north_star.values])}")
            if north_star.strategic_goals: ns_parts.append(f"Strategic Goals: {', '.join([g.title for g in north_star.strategic_goals])}")
            north_star_context = "\n".join(ns_parts)

        initiative_context = "No initiatives defined." if not initiatives else "\n".join([f"- {i.title}: {i.description or 'N/A'}" for i in initiatives])

        prompt_context = (
            f"As a strategic planning expert, generate {num_variants} strategically distinct plan variants that offer meaningfully different approaches to achieving the organization's strategic goals.\n\n"
            f"STRATEGIC FOUNDATION:\n{north_star_context}\n\n"
            f"BASE PLAN ANALYSIS:\n"
            f"Title: {base_plan.title}\n"
            f"Description: {base_plan.description or 'N/A'}\n"
            f"Time Horizon: {base_plan.time_horizon}\n"
            f"Current Initiatives:\n{initiative_context}\n\n"
            f"VARIANT GENERATION FOCUS:\n{', '.join(focus_areas) if focus_areas else 'Generate diverse strategic approaches covering different execution philosophies, risk profiles, and resource allocation strategies.'}\n\n"
            f"REQUIREMENTS FOR EACH VARIANT:\n"
            f"1. STRATEGIC DISTINCTION: Each variant must represent a fundamentally different strategic approach (e.g., aggressive growth vs. steady optimization, technology-led vs. people-first, market expansion vs. vertical integration)\n"
            f"2. PURPOSE ALIGNMENT: All variants must support the core purpose but through different paths\n"
            f"3. FEASIBILITY: Consider different risk tolerances and resource requirements\n"
            f"4. COMPLEMENTARY FOCUS: Variants should explore different strategic dimensions (market, operational, financial, organizational)\n"
            f"5. ACTIONABILITY: Each should suggest a clear strategic direction with implied initiative types\n\n"
            f"For each variant, provide:\n"
            f"- A distinctive title that captures the strategic approach\n"
            f"- A comprehensive description explaining the strategic logic, key differences from the base plan, and expected outcomes\n"
            f"- The strategic rationale for why this approach could be superior in certain conditions\n\n"
            f"Return as a JSON list of objects, each with 'title', 'description', and 'strategic_rationale'."
        )
        try:
            response_str = await kernel_service.generate_completion(prompt_context, max_tokens=400 * num_variants)
            generated_variants_data = json.loads(response_str)
        except Exception as e:
            self.logger.error(f"LLM error in generate_plan_variants: {e}")
            generated_variants_data = []

        for i, variant_data_from_ai in enumerate(generated_variants_data[:num_variants]):
            # Enhanced description that includes strategic rationale
            enhanced_description = variant_data_from_ai.get("description", f"AI generated variant focusing on: {', '.join(focus_areas) if focus_areas else 'alternative approach'}")
            if variant_data_from_ai.get("strategic_rationale"):
                enhanced_description += f"\n\nStrategic Rationale: {variant_data_from_ai['strategic_rationale']}"
            
            variant_create_data = StrategicPlanCreate(
                title=variant_data_from_ai.get("title", f"{base_plan.title} - Strategic Variant {i+1}"),
                description=enhanced_description,
                status=PlanStatus.DRAFT,
                time_horizon=base_plan.time_horizon, # Inherit from base
                start_date=base_plan.start_date,
                end_date=base_plan.end_date
            )
            variant = await self.create_strategic_plan(user_id, variant_create_data)
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

        # Get additional context - handle missing plans gracefully
        plan = None
        if hasattr(initiative, 'plan_id') and initiative.plan_id:
            try:
                plan = await self.get_strategic_plan(initiative.plan_id, user_id)
            except HTTPException:
                # Plan not found - continue without plan context
                plan = None
        north_star = await self.foundation_service.get_north_star(user_id)
        
        # Build strategic context
        strategic_context = "No strategic foundation defined."
        if north_star:
            ns_parts = [f"Purpose: {north_star.purpose.statement}"]
            if north_star.vision: ns_parts.append(f"Vision: {north_star.vision.statement}")
            if north_star.strategic_goals: ns_parts.append(f"Strategic Goals: {', '.join([g.title for g in north_star.strategic_goals])}")
            strategic_context = "\n".join(ns_parts)

        plan_context = f"Plan: {plan.title} - {plan.description}" if plan else "No plan context available."
        
        existing_actions = "\n".join([f"- {action.title}: {action.description or 'N/A'}" for action in initiative.actions]) if initiative.actions else "No existing actions."

        new_actions: List[Action] = []
        prompt = (
            f"As a strategic execution expert, generate 3-4 SMART (Specific, Measurable, Achievable, Relevant, Time-bound) actions for this strategic initiative.\n\n"
            f"STRATEGIC CONTEXT:\n{strategic_context}\n\n"
            f"PLAN CONTEXT:\n{plan_context}\n\n"
            f"INITIATIVE DETAILS:\n"
            f"Title: {initiative.title}\n"
            f"Description: {initiative.description or 'N/A'}\n"
            f"Type: {initiative.initiative_type.value if hasattr(initiative, 'initiative_type') else 'N/A'}\n"
            f"Current Status: {initiative.status.value}\n"
            f"Owner: {initiative.owner or 'Unassigned'}\n"
            f"Timeline: {initiative.start_date} to {initiative.end_date}\n"
            f"Linked Strategic Goal: {initiative.linked_strategic_goal or 'None'}\n\n"
            f"EXISTING ACTIONS:\n{existing_actions}\n\n"
            f"ACTION GENERATION REQUIREMENTS:\n"
            f"1. SPECIFIC: Each action must have a clear, unambiguous deliverable\n"
            f"2. MEASURABLE: Include concrete success criteria or completion indicators\n"
            f"3. ACHIEVABLE: Consider realistic resource and capability constraints\n"
            f"4. RELEVANT: Directly advance the initiative toward its strategic objective\n"
            f"5. TIME-BOUND: Suggest appropriate timeframes relative to the initiative timeline\n"
            f"6. NON-OVERLAPPING: Ensure actions complement rather than duplicate existing ones\n"
            f"7. SEQUENTIAL LOGIC: Consider dependencies and logical execution order\n\n"
            f"For each action, provide:\n"
            f"- A clear action title (what will be accomplished)\n"
            f"- A detailed description including success criteria and approach\n"
            f"- Suggested owner role/department\n"
            f"- Estimated timeline/deadline\n"
            f"- Priority level (High/Medium/Low)\n\n"
            f"Return as a JSON list of objects, each with 'title', 'description', 'suggested_owner', 'estimated_timeline', 'priority'."
        )
        try:
            response_str = await kernel_service.generate_completion(prompt, max_tokens=800)
            action_data_list = json.loads(response_str)
            if not isinstance(action_data_list, list): action_data_list = []
        except Exception as e:
            self.logger.error(f"LLM error generating actions for initiative {initiative_id}: {e}")
            action_data_list = []

        if not action_data_list: # Fallback with SMART structure
            action_data_list = [
                {
                    "title": f"Define detailed scope and requirements for {initiative.title}",
                    "description": f"Create comprehensive scope document with success criteria, deliverables, and constraints for {initiative.title}. Success criteria: Approved scope document by stakeholders within 2 weeks.",
                    "suggested_owner": "Project Manager",
                    "estimated_timeline": "2 weeks",
                    "priority": "High"
                },
                {
                    "title": f"Assemble team and allocate resources for {initiative.title}",
                    "description": f"Identify, recruit, and onboard team members with required skills. Secure budget and resource commitments. Success criteria: Full team assembled and resources committed within 3 weeks.",
                    "suggested_owner": "Initiative Owner",
                    "estimated_timeline": "3 weeks",
                    "priority": "High"
                },
                {
                    "title": f"Establish measurement framework and milestones for {initiative.title}",
                    "description": f"Define KPIs, tracking mechanisms, and key milestones with specific dates. Success criteria: Measurement dashboard deployed and first milestone achieved within 4 weeks.",
                    "suggested_owner": "Data Analyst",
                    "estimated_timeline": "4 weeks",
                    "priority": "Medium"
                }
            ]

        for action_data_dict in action_data_list[:4]: # Max 4 actions
            # Enhanced action creation with SMART details
            enhanced_description = action_data_dict.get("description", f"AI-generated action for '{initiative.title}'")
            if action_data_dict.get("estimated_timeline"):
                enhanced_description += f"\n\nTimeline: {action_data_dict['estimated_timeline']}"
            if action_data_dict.get("suggested_owner"):
                enhanced_description += f"\nSuggested Owner: {action_data_dict['suggested_owner']}"
            if action_data_dict.get("priority"):
                enhanced_description += f"\nPriority: {action_data_dict['priority']}"
            
            action_data = ActionCreate(
                title=action_data_dict.get("title", f"Strategic action for {initiative.title}"),
                description=enhanced_description,
                owner=action_data_dict.get("suggested_owner", "To be assigned"),
                status=ActionStatus.NOT_STARTED
            )
            action = await self.create_action(initiative_id, user_id, action_data)
            new_actions.append(action)
        return new_actions
