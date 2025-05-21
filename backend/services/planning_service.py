import os
import uuid
import logging
from uuid import UUID
from datetime import datetime
from typing import List, Optional, Dict, Any, Union

from azure.cosmos.aio import CosmosClient as AsyncCosmosClient, DatabaseProxy, ContainerProxy
from azure.cosmos import PartitionKey, exceptions as CosmosExceptions
from fastapi import HTTPException

from ..models.planning import (
    StrategicPlan, StrategicPlanCreate, Initiative, InitiativeCreate,
    Action, ActionCreate, Resource, ResourceCreate, Risk, RiskCreate,
    PlanStatus, InitiativeType
)
from ..ai.kernel_service import kernel_service


class PlanningService:
    """Service for managing strategic planning operations including initiatives and actions."""
    
    def __init__(self):
        self.logger = logging.getLogger("planning_service")
        self.plans_cache = {}
        self.initiatives_cache = {}
        
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
            self.cosmos_db_available = False
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
        initiative_dict["id"] = str(initiative.id)
        if initiative.linked_strategic_goal:
            initiative_dict["linked_strategic_goal"] = str(initiative.linked_strategic_goal)
        
        # Convert nested lists of objects' IDs to strings
        for list_name in ["actions", "resources", "risks"]:
            if list_name in initiative_dict:
                for item_dict in initiative_dict[list_name]:
                    item_dict["id"] = str(item_dict["id"])
        try:
            await self.initiatives_container.replace_item(
                item=str(initiative.id), 
                body=initiative_dict,
                partition_key=str(initiative.id) # Assuming PK is /id
            )
            self.logger.info(f"Saved initiative {initiative.id} to Cosmos DB.")
            self.initiatives_cache[str(initiative.id)] = initiative # Update cache
        except CosmosExceptions.CosmosHttpResponseError as e:
            self.logger.error(f"Error saving initiative {initiative.id} to Cosmos DB: {str(e)}")
            self.initiatives_cache[str(initiative.id)] = initiative # Cache as fallback

    # Initiative CRUD Operations
    async def create_initiative(self, plan_id: UUID, initiative_data: InitiativeCreate) -> Initiative:
        initiative_id = uuid.uuid4()
        current_time = datetime.now()
        
        initiative = Initiative(
            id=initiative_id,
            title=initiative_data.title,
            description=initiative_data.description,
            initiative_type=initiative_data.initiative_type,
            status=initiative_data.status,
            linked_strategic_goal=initiative_data.linked_strategic_goal,
            owner=initiative_data.owner,
            start_date=initiative_data.start_date,
            end_date=initiative_data.end_date,
            actions=[], risks=[], resources=[], key_metrics=[],
            created_at=current_time, updated_at=current_time
        )
        
        initiative_dict_for_db = initiative.dict()
        initiative_dict_for_db["id"] = str(initiative.id)
        if initiative.linked_strategic_goal:
            initiative_dict_for_db["linked_strategic_goal"] = str(initiative.linked_strategic_goal)

        if self.cosmos_db_available and self.initiatives_container:
            try:
                await self.initiatives_container.create_item(body=initiative_dict_for_db)
                self.logger.info(f"Created initiative {initiative_id} for plan {plan_id} in Cosmos DB.")
            except CosmosExceptions.CosmosHttpResponseError as e:
                self.logger.error(f"Error creating initiative in Cosmos DB: {str(e)}")
                self.initiatives_cache[str(initiative_id)] = initiative
        else:
            self.initiatives_cache[str(initiative_id)] = initiative
            self.logger.info(f"Created initiative {initiative_id} for plan {plan_id} in memory.")
        return initiative
    
    async def get_initiative(self, initiative_id: UUID) -> Initiative:
        if str(initiative_id) in self.initiatives_cache:
            return self.initiatives_cache[str(initiative_id)]

        if self.cosmos_db_available and self.initiatives_container:
            try:
                item_data = await self.initiatives_container.read_item(item=str(initiative_id), partition_key=str(initiative_id))
                item_data["id"] = UUID(item_data["id"])
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

    async def list_initiatives(self, plan_id: Optional[UUID] = None) -> List[Initiative]:
        initiatives_list: List[Initiative] = []
        if self.cosmos_db_available and self.initiatives_container:
            query = "SELECT * FROM c" # Simplified: lists all initiatives
            # If plan_id linkage is added to Initiative model:
            # query = "SELECT * FROM c WHERE c.plan_id = @plan_id" if plan_id else "SELECT * FROM c"
            # params = [{"name": "@plan_id", "value": str(plan_id)}] if plan_id else None
            try:
                async for item_data in self.initiatives_container.query_items(query=query, enable_cross_partition_query=True):
                    item_data["id"] = UUID(item_data["id"])
                    if item_data.get("linked_strategic_goal"):
                        item_data["linked_strategic_goal"] = UUID(item_data["linked_strategic_goal"])
                    for list_name in ["actions", "resources", "risks"]:
                        for item_dict in item_data.get(list_name, []):
                            item_dict["id"] = UUID(item_dict["id"])
                    initiatives_list.append(Initiative(**item_data))
                return initiatives_list
            except Exception as e:
                self.logger.error(f"Error listing initiatives from Cosmos DB: {str(e)}")
        return list(self.initiatives_cache.values())

    async def update_initiative(self, initiative_id: UUID, initiative_update_data: Dict[str, Any]) -> Initiative:
        existing_initiative = await self.get_initiative(initiative_id)
        
        update_payload = InitiativeCreate(**initiative_update_data) # Validate with create model
        
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
    
    async def delete_initiative(self, initiative_id: UUID) -> bool:
        await self.get_initiative(initiative_id) # Check existence
        if self.cosmos_db_available and self.initiatives_container:
            try:
                await self.initiatives_container.delete_item(item=str(initiative_id), partition_key=str(initiative_id))
                self.logger.info(f"Deleted initiative from Cosmos DB: {initiative_id}")
                if str(initiative_id) in self.initiatives_cache: del self.initiatives_cache[str(initiative_id)]
                return True
            except CosmosExceptions.CosmosHttpResponseError as e:
                self.logger.error(f"Error deleting initiative from Cosmos DB: {str(e)}")
                return False
        elif str(initiative_id) in self.initiatives_cache: # DB not available, try cache
            del self.initiatives_cache[str(initiative_id)]
            self.logger.info(f"Deleted initiative from memory: {initiative_id}")
            return True
        return False

    # Action, Resource, Risk CRUD Operations (as nested items)
    async def _add_nested_item(self, initiative_id: UUID, item_data: Union[ActionCreate, ResourceCreate, RiskCreate], item_type: str) -> Union[Action, Resource, Risk]:
        initiative = await self.get_initiative(initiative_id)
        item_id = uuid.uuid4()
        current_time = datetime.now()

        item_model_map = {"action": Action, "resource": Resource, "risk": Risk}
        item_list_attr_map = {"action": "actions", "resource": "resources", "risk": "risks"}

        ModelClass = item_model_map[item_type]
        list_attr = item_list_attr_map[item_type]

        item = ModelClass(id=item_id, **item_data.dict(), created_at=current_time, updated_at=current_time)
        
        getattr(initiative, list_attr).append(item)
        initiative.updated_at = current_time
        await self._save_initiative_to_db(initiative)
        return item

    async def create_action(self, initiative_id: UUID, action_data: ActionCreate) -> Action:
        return await self._add_nested_item(initiative_id, action_data, "action")

    async def create_resource(self, initiative_id: UUID, resource_data: ResourceCreate) -> Resource:
        return await self._add_nested_item(initiative_id, resource_data, "resource")

    async def create_risk(self, initiative_id: UUID, risk_data: RiskCreate) -> Risk:
        return await self._add_nested_item(initiative_id, risk_data, "risk")

    async def _update_nested_item(self, initiative_id: UUID, item_id: UUID, item_update_data: Union[ActionCreate, Dict], item_type: str) -> Optional[Union[Action, Resource, Risk]]:
        initiative = await self.get_initiative(initiative_id)
        item_list_attr_map = {"action": "actions", "resource": "resources", "risk": "risks"}
        ModelClass = {"action": Action, "resource": Resource, "risk": Risk}[item_type]
        CreateClass = {"action": ActionCreate, "resource": ResourceCreate, "risk": RiskCreate}[item_type]

        list_attr = item_list_attr_map[item_type]
        item_list = getattr(initiative, list_attr)
        
        item_index = -1
        for i, item in enumerate(item_list):
            if item.id == item_id:
                item_index = i
                break
        
        if item_index == -1:
            raise HTTPException(status_code=404, detail=f"{item_type.capitalize()} with ID {item_id} not found in initiative {initiative_id}")

        # Validate/process update data
        if isinstance(item_update_data, Dict):
            update_payload = CreateClass(**item_update_data)
        else: # Is ActionCreate, ResourceCreate, or RiskCreate
            update_payload = item_update_data

        original_item = item_list[item_index]
        updated_item_data = original_item.dict()
        updated_item_data.update(update_payload.dict(exclude_unset=True)) # Apply updates
        updated_item_data["updated_at"] = datetime.now()
        
        updated_item = ModelClass(**updated_item_data)
        item_list[item_index] = updated_item
        initiative.updated_at = datetime.now()
        await self._save_initiative_to_db(initiative)
        return updated_item

    async def update_action(self, initiative_id: UUID, action_id: UUID, action_data: Dict[str, Any]) -> Action:
        return await self._update_nested_item(initiative_id, action_id, action_data, "action")

    # Placeholder for update_resource and update_risk if needed by router
    # async def update_resource(self, initiative_id: UUID, resource_id: UUID, resource_data: Dict[str, Any]) -> Resource:
    #     return await self._update_nested_item(initiative_id, resource_id, resource_data, "resource")
    # async def update_risk(self, initiative_id: UUID, risk_id: UUID, risk_data: Dict[str, Any]) -> Risk:
    #     return await self._update_nested_item(initiative_id, risk_id, risk_data, "risk")

    async def _delete_nested_item(self, initiative_id: UUID, item_id: UUID, item_type: str) -> bool:
        initiative = await self.get_initiative(initiative_id)
        item_list_attr_map = {"action": "actions", "resource": "resources", "risk": "risks"}
        list_attr = item_list_attr_map[item_type]
        item_list = getattr(initiative, list_attr)
        
        original_len = len(item_list)
        setattr(initiative, list_attr, [item for item in item_list if item.id != item_id])
        
        if len(getattr(initiative, list_attr)) == original_len:
            raise HTTPException(status_code=404, detail=f"{item_type.capitalize()} with ID {item_id} not found.")
            
        initiative.updated_at = datetime.now()
        await self._save_initiative_to_db(initiative)
        return True

    async def delete_action(self, initiative_id: UUID, action_id: UUID) -> bool:
        return await self._delete_nested_item(initiative_id, action_id, "action")
    
    # Placeholder for delete_resource and delete_risk if needed by router
    # async def delete_resource(self, initiative_id: UUID, resource_id: UUID) -> bool:
    #     return await self._delete_nested_item(initiative_id, resource_id, "resource")
    # async def delete_risk(self, initiative_id: UUID, risk_id: UUID) -> bool:
    #     return await self._delete_nested_item(initiative_id, risk_id, "risk")

    # StrategicPlan CRUD Operations
    async def create_strategic_plan(self, plan_data: StrategicPlanCreate) -> StrategicPlan: # Alias for create_plan
        return await self.create_plan(plan_data)

    async def create_plan(self, plan_create: StrategicPlanCreate) -> StrategicPlan:
        plan_id = uuid.uuid4()
        current_time = datetime.now()
        plan = StrategicPlan(id=plan_id, **plan_create.dict(), created_at=current_time, updated_at=current_time)
        
        plan_dict_for_db = plan.dict()
        plan_dict_for_db["id"] = str(plan.id)

        if self.cosmos_db_available and self.plans_container:
            try:
                await self.plans_container.create_item(body=plan_dict_for_db)
                self.logger.info(f"Created strategic plan {plan_id} in Cosmos DB.")
            except CosmosExceptions.CosmosHttpResponseError as e:
                self.logger.error(f"Error creating strategic plan in Cosmos DB: {str(e)}")
                self.plans_cache[str(plan_id)] = plan
        else:
            self.plans_cache[str(plan_id)] = plan
            self.logger.info(f"Created strategic plan {plan_id} in memory.")
        return plan

    async def get_strategic_plan(self, plan_id: UUID) -> StrategicPlan: # Alias for get_plan
        return await self.get_plan(plan_id)

    async def get_plan(self, plan_id: UUID) -> StrategicPlan:
        if str(plan_id) in self.plans_cache:
            return self.plans_cache[str(plan_id)]
        if self.cosmos_db_available and self.plans_container:
            try:
                item_data = await self.plans_container.read_item(item=str(plan_id), partition_key=str(plan_id))
                item_data["id"] = UUID(item_data["id"])
                # If plan has initiatives as direct list, deserialize them too
                # For now, assuming StrategicPlan model does not embed full initiatives from this container
                plan = StrategicPlan(**item_data)
                self.plans_cache[str(plan_id)] = plan
                return plan
            except CosmosExceptions.CosmosResourceNotFoundError:
                raise HTTPException(status_code=404, detail=f"Strategic plan with ID {plan_id} not found")
            except Exception as e:
                self.logger.error(f"Error retrieving plan {plan_id}: {str(e)}")
                raise HTTPException(status_code=500, detail="Error retrieving plan")
        raise HTTPException(status_code=404, detail=f"Plan {plan_id} not found (DB unavailable/not in cache)")

    async def list_strategic_plans(self, status: Optional[PlanStatus] = None, limit: int = 10, offset: int = 0) -> List[StrategicPlan]: # Alias for list_plans
        return await self.list_plans(status, limit, offset)

    async def list_plans(self, status_filter: Optional[PlanStatus] = None, limit: int = 10, offset: int = 0) -> List[StrategicPlan]:
        plans_list: List[StrategicPlan] = []
        if self.cosmos_db_available and self.plans_container:
            query = "SELECT * FROM c"
            params = []
            if status_filter:
                query += " WHERE c.status = @status"
                params.append({"name": "@status", "value": status_filter.value})
            query += f" ORDER BY c.created_at DESC OFFSET {offset} LIMIT {limit}"
            
            try:
                async for item_data in self.plans_container.query_items(query=query, parameters=params, enable_cross_partition_query=True):
                    item_data["id"] = UUID(item_data["id"])
                    plans_list.append(StrategicPlan(**item_data))
                return plans_list
            except Exception as e:
                self.logger.error(f"Error listing plans: {str(e)}")
        
        # Fallback to cache with filtering
        cached_plans = list(self.plans_cache.values())
        if status_filter:
            cached_plans = [p for p in cached_plans if p.status == status_filter]
        cached_plans.sort(key=lambda p: p.created_at, reverse=True)
        return cached_plans[offset : offset + limit]

    async def update_strategic_plan(self, plan_id: UUID, plan_data: Dict[str, Any]) -> StrategicPlan: # Alias for update_plan
        return await self.update_plan(plan_id, plan_data)
        
    async def update_plan(self, plan_id: UUID, plan_update_data: Dict[str, Any]) -> StrategicPlan:
        existing_plan = await self.get_plan(plan_id)
        
        update_payload = StrategicPlanCreate(**plan_update_data) # Validate with create model

        existing_plan.title = update_payload.title
        existing_plan.description = update_payload.description
        existing_plan.status = update_payload.status
        existing_plan.time_horizon = update_payload.time_horizon
        existing_plan.start_date = update_payload.start_date
        existing_plan.end_date = update_payload.end_date
        existing_plan.updated_at = datetime.now()
        
        plan_dict_for_db = existing_plan.dict()
        plan_dict_for_db["id"] = str(existing_plan.id)

        if self.cosmos_db_available and self.plans_container:
            try:
                await self.plans_container.replace_item(item=str(plan_id), body=plan_dict_for_db, partition_key=str(plan_id))
                self.logger.info(f"Updated strategic plan {plan_id} in Cosmos DB.")
            except CosmosExceptions.CosmosHttpResponseError as e:
                self.logger.error(f"Error updating plan in Cosmos DB: {str(e)}")
                self.plans_cache[str(plan_id)] = existing_plan
        else:
            self.plans_cache[str(plan_id)] = existing_plan
            self.logger.info(f"Updated strategic plan {plan_id} in memory.")
        return existing_plan

    async def delete_strategic_plan(self, plan_id: UUID) -> bool: # Alias for delete_plan
        return await self.delete_plan(plan_id)

    async def delete_plan(self, plan_id: UUID) -> bool:
        await self.get_plan(plan_id) # Check existence
        if self.cosmos_db_available and self.plans_container:
            try:
                await self.plans_container.delete_item(item=str(plan_id), partition_key=str(plan_id))
                self.logger.info(f"Deleted strategic plan from Cosmos DB: {plan_id}")
                if str(plan_id) in self.plans_cache: del self.plans_cache[str(plan_id)]
                # Also delete associated initiatives (cascade delete conceptually)
                # This would require listing initiatives by plan_id and deleting them.
                # For now, this is not implemented to keep it simpler.
                return True
            except CosmosExceptions.CosmosHttpResponseError as e:
                self.logger.error(f"Error deleting plan from Cosmos DB: {str(e)}")
                return False
        elif str(plan_id) in self.plans_cache:
             del self.plans_cache[str(plan_id)]
             self.logger.info(f"Deleted strategic plan from memory: {plan_id}")
             return True
        return False

    # ----- Advanced Planning Features (Placeholders/Basic) -----
    async def analyze_plan_alignment(self, plan_id: UUID) -> Dict[str, Any]:
        plan = await self.get_plan(plan_id)
        # This is a placeholder. Real analysis would involve fetching initiatives for this plan.
        # For now, assume plan.initiatives is empty or not part of the direct plan model from DB.
        # If initiatives are fetched separately:
        # initiatives = await self.list_initiatives(plan_id=plan_id) # if list_initiatives supports plan_id filter
        initiatives = [] # Placeholder
        
        if not initiatives: score = 0.0
        else:
            linked = sum(1 for i in initiatives if i.linked_strategic_goal)
            coverage = linked / len(initiatives) if initiatives else 0
            score = round(coverage * 10, 2)
        # LLM adjustment part is omitted for brevity as it's a placeholder.
        return {"plan_id": str(plan_id), "alignment_score": score, "details": "Basic alignment score based on linked goals."}

    async def generate_plan_variants(self, base_plan_id: UUID, num_variants: int = 2, focus_areas: Optional[List[str]] = None) -> List[StrategicPlan]:
        base = await self.get_plan(base_plan_id)
        variants: List[StrategicPlan] = []
        for i in range(num_variants):
            variant_data = StrategicPlanCreate(
                title=f"{base.title} Variant {i+1}",
                description=base.description,
                status=PlanStatus.DRAFT,
                time_horizon=base.time_horizon,
                start_date=base.start_date,
                end_date=base.end_date
            )
            # These variants are created in memory/DB but not deeply fleshed out by AI here.
            variant = await self.create_plan(variant_data) 
            # Add AI recommendations if any
            if focus_areas:
                 variant.ai_recommendations = [f"Focus on {fa}" for fa in focus_areas]
                 await self.update_plan(variant.id, variant.dict()) # Save recommendations
            variants.append(variant)
        return variants

    async def compare_plans(self, plan_ids: List[UUID], comparison_criteria: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
        # Placeholder: more sophisticated comparison needed.
        results = {}
        for pid in plan_ids:
            plan = await self.get_plan(pid)
            # initiatives = await self.list_initiatives(plan_id=pid) # If initiatives are linked
            results[str(pid)] = {
                "title": plan.title,
                "status": plan.status.value,
                # "initiative_count": len(initiatives),
                # "alignment_score": plan.overall_alignment_score or "Not analyzed"
            }
        return {"comparison_results": results}

    async def generate_actions(self, initiative_id: UUID) -> List[Action]:
        initiative = await self.get_initiative(initiative_id)
        new_actions: List[Action] = []
        prompt = f"Suggest three concrete actions for the following initiative:\nTitle: {initiative.title}\nDescription: {initiative.description}"
        try:
            response_str = await kernel_service.generate_completion(prompt, max_tokens=150)
            action_titles = [line.strip('- ').strip() for line in response_str.splitlines() if line.strip()]
        except Exception as e:
            self.logger.error(f"Error generating actions from LLM: {e}")
            action_titles = []

        if not action_titles: # Fallback
            action_titles = [f"Define scope for {initiative.title}", f"Allocate resources for {initiative.title}", f"Set milestones for {initiative.title}"]

        for title in action_titles[:3]:
            action_data = ActionCreate(title=title, description=f"Generated action for {initiative.title}", status="todo")
            # Corrected call:
            action = await self.add_action(initiative_id, action_data)
            new_actions.append(action)
        return new_actions
