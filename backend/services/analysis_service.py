import uuid
import json
import logging
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
from uuid import UUID

# Use azure.cosmos.aio for asynchronous operations
from azure.cosmos.aio import CosmosClient as AsyncCosmosClient, DatabaseProxy, ContainerProxy 
from azure.cosmos import PartitionKey, exceptions as CosmosExceptions # Keep sync exceptions for now or use a general one
from fastapi import HTTPException

from ..models.analysis import (
    SWOTAnalysis,
    SWOTAnalysisCreate, # Assuming this is the input model
    SWOTItem, 
    SWOTItemCreate, # Assuming this is the input model
    SWOTCategory, 
    Insight, 
    InsightCreate, # Assuming this is the input model
    SOLinkage, 
    SOLinkageCreate,
    LinkageType,
    InsightSource, # For generate_ai_guided_swot_items
    AnalysisSession,
    AnalysisSessionCreate,
    AnalysisSessionUpdate,
    AnalysisSessionStatus,
    AnalysisSessionType,
    GuidanceRequest,
    GuidanceResponse,
    SessionStepState
)
from ..ai.kernel_service import kernel_service

class AnalysisService:
    """Service for managing SWOT/TOWS analysis operations with Cosmos DB integration"""
    
    def __init__(self):
        # Set up logging
        self.logger = logging.getLogger("analysis_service")
        
        # In-memory storage (used as cache and fallback)
        self.active_sessions = {}
        self.analyses_cache = {}
        self.insights_cache = {}
        self.so_linkages_cache = {}
        
        # Initialize database connection flags
        self.cosmos_db_available = False
        self.cosmos_client: Optional[AsyncCosmosClient] = None
        self.database: Optional[DatabaseProxy] = None
        self.analyses_container: Optional[ContainerProxy] = None
        self.sessions_container: Optional[ContainerProxy] = None
        self.so_linkages_container: Optional[ContainerProxy] = None
        self.insights_container: Optional[ContainerProxy] = None
        
        # Cosmos DB connection details from environment variables
        self.cosmos_endpoint = os.getenv("AZURE_COSMOS_ENDPOINT")
        self.cosmos_key = os.getenv("AZURE_COSMOS_KEY")
        self.cosmos_database_name = os.getenv("AZURE_COSMOS_DATABASE_NAME", "stratosdb")

        # Defer actual connection to an async method if needed, or do it here if __init__ can be async
        # For now, keeping it synchronous for setup, but operations will be async.
        # If this service is instantiated per request, __init__ should ideally be async or use a factory.
        # If it's a singleton, an async setup method called at app startup is better.
        self._initialize_cosmos_db_sync()

    def _initialize_cosmos_db_sync(self):
        """Synchronous part of Cosmos DB initialization."""
        if not self.cosmos_endpoint or not self.cosmos_key:
            self.logger.warning("Cosmos DB credentials not found. Using in-memory storage.")
            return

        try:
            self.cosmos_client = AsyncCosmosClient(url=self.cosmos_endpoint, credential=self.cosmos_key)
            self.database = self.cosmos_client.get_database_client(self.cosmos_database_name)
            
            # Container clients (proxies)
            self.analyses_container = self.database.get_container_client("analyses")
            self.sessions_container = self.database.get_container_client("analysis_sessions")
            self.so_linkages_container = self.database.get_container_client("so_linkages")
            self.insights_container = self.database.get_container_client("insights")
            
            # Note: Container creation check/logic would ideally be in an async setup method.
            # For simplicity here, we assume containers exist or are created elsewhere (e.g., app startup).
            # If not, self.database.create_container_if_not_exists (sync) or an async equivalent is needed.
            # The original code had create_container_if_not_exists, which is synchronous.
            # The async equivalent is database_proxy.create_container(...)
            # This part is tricky in a synchronous __init__. A dedicated async setup is better.
            # For now, we'll assume containers are pre-created or handled by an app startup hook.
            
            self.cosmos_db_available = True
            self.logger.info("Cosmos DB client initialized (async proxies ready).")
        except Exception as e:
            self.logger.warning(f"Cosmos DB client initialization failed: {str(e)}. Using in-memory storage.")
            self.cosmos_db_available = False
            self.cosmos_client = None # Ensure client is None if setup fails

    # ----------- Database Operations -----------
    
    async def create_swot_analysis(self, analysis_data: SWOTAnalysisCreate, user_id: UUID) -> SWOTAnalysis:
        """Create a new SWOT analysis in the database"""
        try:
            analysis_id = uuid.uuid4()
            
            analysis = SWOTAnalysis(
                id=analysis_id,
                user_id=user_id, # Assign user_id
                title=analysis_data.title,
                description=analysis_data.description,
                items=[],
                tows_strategies=[],
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            analysis_dict = analysis.model_dump()
            # Ensure UUIDs are strings for Cosmos DB
            analysis_dict["id"] = str(analysis_dict["id"])
            analysis_dict["user_id"] = str(analysis_dict["user_id"])

            if self.cosmos_db_available and self.analyses_container:
                try:
                    await self.analyses_container.create_item(body=analysis_dict)
                    self.logger.info(f"Created SWOT analysis {analysis.id} for user {user_id} in Cosmos DB")
                    self.analyses_cache[str(analysis.id)] = analysis_dict # Cache the dict
                except CosmosExceptions.CosmosHttpResponseError as e:
                    self.logger.error(f"Error saving SWOT analysis to Cosmos DB: {str(e)}")
                    self.analyses_cache[str(analysis.id)] = analysis_dict # Fallback
            else:
                self.analyses_cache[str(analysis.id)] = analysis_dict
            
            return analysis
        except Exception as e:
            self.logger.error(f"Error creating SWOT analysis: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to create SWOT analysis: {str(e)}")
    

    async def get_swot_analysis(self, analysis_id: UUID, user_id: UUID) -> Optional[SWOTAnalysis]:
        """Retrieve a SWOT analysis by ID and user_id (partition key)."""
        cache_key = f"{user_id}_{analysis_id}"
        if cache_key in self.analyses_cache:
            return SWOTAnalysis(**self.analyses_cache[cache_key])

        if self.cosmos_db_available and self.analyses_container:
            try:
                item = await self.analyses_container.read_item(item=str(analysis_id), partition_key=str(user_id))
                # Ensure user_id from item matches for security, though partition key should enforce this
                if item.get("user_id") != str(user_id):
                    self.logger.warning(f"User {user_id} attempted to access SWOT {analysis_id} owned by {item.get('user_id')}")
                    return None
                self.analyses_cache[cache_key] = item
                return SWOTAnalysis(**item)
            except CosmosExceptions.CosmosResourceNotFoundError:
                return None
            except Exception as e:
                self.logger.error(f"Error getting SWOT analysis {analysis_id} for user {user_id}: {e}")
                return None
        return None

    async def list_swot_analyses(self, user_id: UUID, limit: int = 10, offset: int = 0) -> List[SWOTAnalysis]:
        """List SWOT analyses for a specific user."""
        analyses = []
        if self.cosmos_db_available and self.analyses_container:
            query = "SELECT * FROM c WHERE c.user_id = @user_id OFFSET @offset LIMIT @limit"
            parameters = [
                {"name": "@user_id", "value": str(user_id)},
                {"name": "@offset", "value": offset},
                {"name": "@limit", "value": limit}
            ]
            try:
                async for item in self.analyses_container.query_items(
                    query=query, 
                    parameters=parameters, 
                    partition_key=str(user_id) # Query within partition
                ):
                    # item['user_id'] should already be UUID if model is correct, but Cosmos stores strings
                    item['user_id'] = UUID(item['user_id']) if isinstance(item.get('user_id'), str) else item.get('user_id')
                    item['id'] = UUID(item['id']) if isinstance(item.get('id'), str) else item.get('id')
                    analyses.append(SWOTAnalysis(**item))
                    self.analyses_cache[f"{user_id}_{item['id']}"] = item
                return analyses
            except Exception as e:
                self.logger.error(f"Error listing SWOT for user {user_id}: {e}")
                # Fallback to cache if any error
        
        # Fallback to in-memory cache (less efficient for user-specific listing)
        # This part needs to be careful if cache is not user-specific
        user_specific_cached_analyses = []
        for key, val_dict in self.analyses_cache.items():
            if key.startswith(str(user_id)): # Assuming cache key is "user_id_analysis_id"
                 # Ensure it's a dict before passing to SWOTAnalysis
                if isinstance(val_dict, dict):
                    try:
                        user_specific_cached_analyses.append(SWOTAnalysis(**val_dict))
                    except Exception as model_e:
                        self.logger.error(f"Error creating SWOTAnalysis from cache for key {key}: {model_e}")
        
        # Sort and paginate cached results if needed (example, not fully robust)
        user_specific_cached_analyses.sort(key=lambda x: x.created_at, reverse=True) # Example sort
        return user_specific_cached_analyses[offset:offset+limit]


    async def add_swot_item(self, analysis_id: UUID, item_data: SWOTItemCreate, user_id: UUID) -> Optional[SWOTItem]:
        analysis = await self.get_swot_analysis(analysis_id, user_id)
        if not analysis:
            return None

        item = SWOTItem( # SWOTItem does not have user_id directly, it's part of SWOTAnalysis
            category=item_data.category,
            content=item_data.content,
            source=item_data.source,
            source_references=item_data.source_references,
            impact_score=item_data.impact_score,
            certainty_score=item_data.certainty_score,
        )
        analysis.items.append(item)
        analysis.updated_at = datetime.now()
        
        analysis_dict = analysis.model_dump()
        analysis_dict["id"] = str(analysis_dict["id"])
        analysis_dict["user_id"] = str(analysis_dict["user_id"])


        cache_key = f"{user_id}_{analysis_id}"
        self.analyses_cache[cache_key] = analysis_dict
        if self.cosmos_db_available and self.analyses_container:
            try:
                await self.analyses_container.replace_item(
                    item=str(analysis_id), 
                    body=analysis_dict, 
                    partition_key=str(user_id)
                )
            except CosmosExceptions.CosmosHttpResponseError as e:
                self.logger.error(f"Error replacing SWOT item in Cosmos DB: {e}")
                # Cache already updated
        return item

    async def update_swot_item(self, analysis_id: UUID, item_id: UUID, item_data: Dict[str, Any], user_id: UUID) -> Optional[SWOTItem]:
        analysis = await self.get_swot_analysis(analysis_id, user_id)
        if not analysis:
            return None
        
        item_updated = None
        for idx, itm in enumerate(analysis.items):
            if itm.id == item_id:
                updated_fields = itm.model_dump()
                updated_fields.update(item_data)
                analysis.items[idx] = SWOTItem(**updated_fields)
                analysis.updated_at = datetime.now()
                item_updated = analysis.items[idx]
                break
        
        if not item_updated:
            return None

        analysis_dict = analysis.model_dump()
        analysis_dict["id"] = str(analysis_dict["id"])
        analysis_dict["user_id"] = str(analysis_dict["user_id"])

        cache_key = f"{user_id}_{analysis_id}"
        self.analyses_cache[cache_key] = analysis_dict
        if self.cosmos_db_available and self.analyses_container:
            try:
                await self.analyses_container.replace_item(
                    item=str(analysis_id), 
                    body=analysis_dict, 
                    partition_key=str(user_id)
                )
            except CosmosExceptions.CosmosHttpResponseError as e:
                 self.logger.error(f"Error replacing SWOT item in Cosmos DB: {e}")
        return item_updated

    async def delete_swot_item(self, analysis_id: UUID, item_id: UUID, user_id: UUID) -> bool:
        analysis = await self.get_swot_analysis(analysis_id, user_id)
        if not analysis:
            return False
        
        original_len = len(analysis.items)
        analysis.items = [it for it in analysis.items if it.id != item_id]
        
        if len(analysis.items) == original_len:
            return False # Item not found or not deleted
            
        analysis.updated_at = datetime.now()
        analysis_dict = analysis.model_dump()
        analysis_dict["id"] = str(analysis_dict["id"])
        analysis_dict["user_id"] = str(analysis_dict["user_id"])

        cache_key = f"{user_id}_{analysis_id}"
        self.analyses_cache[cache_key] = analysis_dict
        if self.cosmos_db_available and self.analyses_container:
            try:
                await self.analyses_container.replace_item(
                    item=str(analysis_id), 
                    body=analysis_dict, 
                    partition_key=str(user_id)
                )
            except CosmosExceptions.CosmosHttpResponseError as e:
                self.logger.error(f"Error replacing SWOT after item deletion in Cosmos DB: {e}")
                return False # Indicate failure if DB update fails
        return True

    async def create_insight(self, insight_data: InsightCreate, user_id: UUID) -> Insight:
        insight_id = uuid.uuid4()
        insight = Insight(
            id=insight_id,
            user_id=user_id, # Assign user_id
            title=insight_data.title,
            description=insight_data.description,
            insight_type=insight_data.insight_type,
            source=insight_data.source,
            source_references=insight_data.source_references,
            confidence_score=insight_data.confidence_score,
            impact_score=insight_data.impact_score,
            linked_strategic_goals=[UUID(g) for g in insight_data.linked_strategic_goals if g], # Handle None
            supporting_data=insight_data.supporting_data,
            visualization_data=insight_data.visualization_data,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        insight_dict = insight.model_dump()
        insight_dict["id"] = str(insight_dict["id"])
        insight_dict["user_id"] = str(insight_dict["user_id"])
        # Ensure linked_strategic_goals are strings if they exist
        if insight_dict.get("linked_strategic_goals"):
            insight_dict["linked_strategic_goals"] = [str(g) for g in insight_dict["linked_strategic_goals"]]


        cache_key = f"{user_id}_{insight_id}"
        self.insights_cache[cache_key] = insight_dict
        if self.cosmos_db_available and self.insights_container:
            try:
                await self.insights_container.create_item(body=insight_dict)
            except CosmosExceptions.CosmosHttpResponseError as e:
                self.logger.error(f"Error creating insight in Cosmos DB: {e}")
                # Cache already updated
        return insight

    async def get_insight(self, insight_id: UUID, user_id: UUID) -> Optional[Insight]:
        cache_key = f"{user_id}_{insight_id}"
        if cache_key in self.insights_cache:
            return Insight(**self.insights_cache[cache_key])

        if self.cosmos_db_available and self.insights_container:
            try:
                item = await self.insights_container.read_item(item=str(insight_id), partition_key=str(user_id))
                if item.get("user_id") != str(user_id):
                     self.logger.warning(f"User {user_id} attempted to access insight {insight_id} owned by {item.get('user_id')}")
                     return None
                self.insights_cache[cache_key] = item
                return Insight(**item)
            except CosmosExceptions.CosmosResourceNotFoundError:
                return None
            except Exception as e:
                self.logger.error(f"Error getting insight {insight_id} for user {user_id}: {e}")
                return None
        return None

    async def list_insights(
        self, 
        user_id: UUID, 
        limit: int = 20, 
        offset: int = 0,
        insight_type: Optional[Any] = None, # Use Any for InsightType if it's an Enum
        source: Optional[Any] = None, # Use Any for InsightSource
        goal_id: Optional[UUID] = None
    ) -> List[Insight]:
        insights = []
        if self.cosmos_db_available and self.insights_container:
            query_parts = ["SELECT * FROM c WHERE c.user_id = @user_id"]
            parameters = [{"name": "@user_id", "value": str(user_id)}]
            
            if insight_type:
                query_parts.append("AND c.insight_type = @insight_type")
                parameters.append({"name": "@insight_type", "value": insight_type.value if hasattr(insight_type, 'value') else insight_type})
            if source:
                query_parts.append("AND c.source = @source")
                parameters.append({"name": "@source", "value": source.value if hasattr(source, 'value') else source})
            if goal_id: # This requires ARRAY_CONTAINS if linked_strategic_goals is an array
                query_parts.append("AND ARRAY_CONTAINS(c.linked_strategic_goals, @goal_id)")
                parameters.append({"name": "@goal_id", "value": str(goal_id)})

            query = " ".join(query_parts) + " OFFSET @offset LIMIT @limit"
            parameters.extend([
                {"name": "@offset", "value": offset},
                {"name": "@limit", "value": limit}
            ])
            
            try:
                async for item in self.insights_container.query_items(
                    query=query, 
                    parameters=parameters, 
                    partition_key=str(user_id)
                ):
                    item['user_id'] = UUID(item['user_id']) if isinstance(item.get('user_id'), str) else item.get('user_id')
                    item['id'] = UUID(item['id']) if isinstance(item.get('id'), str) else item.get('id')
                    if item.get("linked_strategic_goals"): # Convert UUID strings back
                        item["linked_strategic_goals"] = [UUID(g_id) for g_id in item["linked_strategic_goals"]]
                    insights.append(Insight(**item))
                    self.insights_cache[f"{user_id}_{item['id']}"] = item
                return insights
            except Exception as e:
                self.logger.error(f"Error listing insights for user {user_id}: {e}")

        # Fallback to cache
        user_specific_cached_insights = []
        for key, val_dict in self.insights_cache.items():
            if key.startswith(str(user_id)):
                if isinstance(val_dict, dict):
                    # Apply filters to cached data (simplified example)
                    match = True
                    if insight_type and val_dict.get("insight_type") != (insight_type.value if hasattr(insight_type, 'value') else insight_type):
                        match = False
                    if source and val_dict.get("source") != (source.value if hasattr(source, 'value') else source):
                        match = False
                    if goal_id and str(goal_id) not in (val_dict.get("linked_strategic_goals") or []):
                        match = False
                    if match:
                        try:
                            user_specific_cached_insights.append(Insight(**val_dict))
                        except Exception as model_e:
                            self.logger.error(f"Error creating Insight from cache for key {key}: {model_e}")

        user_specific_cached_insights.sort(key=lambda x: x.created_at, reverse=True)
        return user_specific_cached_insights[offset:offset+limit]


    async def update_insight(self, insight_id: UUID, insight_data: Dict[str, Any], user_id: UUID) -> Optional[Insight]:
        insight = await self.get_insight(insight_id, user_id)
        if not insight:
            return None
        
        updated_fields = insight.model_dump()
        updated_fields.update(insight_data)
        # Ensure user_id is not changed by update_data
        updated_fields["user_id"] = insight.user_id 
        updated_fields["updated_at"] = datetime.now()

        if "linked_strategic_goals" in updated_fields and updated_fields["linked_strategic_goals"]:
             updated_fields["linked_strategic_goals"] = [UUID(g) for g in updated_fields["linked_strategic_goals"] if g]


        updated_insight = Insight(**updated_fields)
        
        insight_dict_to_save = updated_insight.model_dump()
        insight_dict_to_save["id"] = str(insight_dict_to_save["id"])
        insight_dict_to_save["user_id"] = str(insight_dict_to_save["user_id"])
        if insight_dict_to_save.get("linked_strategic_goals"):
            insight_dict_to_save["linked_strategic_goals"] = [str(g) for g in insight_dict_to_save["linked_strategic_goals"]]


        cache_key = f"{user_id}_{insight_id}"
        self.insights_cache[cache_key] = insight_dict_to_save
        if self.cosmos_db_available and self.insights_container:
            try:
                await self.insights_container.replace_item(
                    item=str(insight_id), 
                    body=insight_dict_to_save, 
                    partition_key=str(user_id)
                )
            except CosmosExceptions.CosmosHttpResponseError as e:
                self.logger.error(f"Error updating insight in Cosmos DB: {e}")
        return updated_insight

    async def delete_insight(self, insight_id: UUID, user_id: UUID) -> bool:
        cache_key = f"{user_id}_{insight_id}"
        if cache_key in self.insights_cache:
            del self.insights_cache[cache_key]

        if self.cosmos_db_available and self.insights_container:
            try:
                await self.insights_container.delete_item(item=str(insight_id), partition_key=str(user_id))
                return True
            except CosmosExceptions.CosmosResourceNotFoundError:
                return False # Already deleted or never existed for this user
            except Exception as e:
                self.logger.error(f"Error deleting insight {insight_id} for user {user_id}: {e}")
                return False
        # If only cache was affected and DB not available, consider it deleted from service's perspective
        return not self.cosmos_db_available 


    async def generate_tows_strategies(self, analysis_id: UUID, user_id: UUID) -> List[Dict[str, Any]]:
        """Generate TOWS strategies from a SWOT analysis using the LLM."""
        analysis = await self.get_swot_analysis(analysis_id, user_id)
        if not analysis:
            return []

        # Build SWOT text for the prompt
        strengths = [i.content for i in analysis.items if i.category == SWOTCategory.STRENGTH]
        weaknesses = [i.content for i in analysis.items if i.category == SWOTCategory.WEAKNESS]
        opportunities = [i.content for i in analysis.items if i.category == SWOTCategory.OPPORTUNITY]
        threats = [i.content for i in analysis.items if i.category == SWOTCategory.THREAT]

        swot_text = "Strengths:\n" + "\n".join(strengths) + "\n\n" + \
                    "Weaknesses:\n" + "\n".join(weaknesses) + "\n\n" + \
                    "Opportunities:\n" + "\n".join(opportunities) + "\n\n" + \
                    "Threats:\n" + "\n".join(threats)

        # Invoke semantic function to generate TOWS strategies
        try:
            # Assuming kernel_service methods are already async
            response = await kernel_service.invoke_semantic_function(
                "Analysis", "GenerateTOWS", swot_text # Consider passing user_id or user context if skill needs it
            )
        except Exception as e:
            self.logger.error(f"Error generating TOWS strategies for user {user_id}: {e}")
            return []

        strategies: List[Dict[str, Any]] = []
        current_type = None
        for line in response.splitlines():
            line = line.strip()
            if line.startswith("##"):
                if "S-O" in line: current_type = "SO"
                elif "W-O" in line: current_type = "WO"
                elif "S-T" in line: current_type = "ST"
                elif "W-T" in line: current_type = "WT"
            elif line and line[0].isdigit():
                parts = line.split(" ", 1)
                strategy_text = parts[1] if len(parts) > 1 else line
                strategies.append({"type": current_type, "strategy": strategy_text})

        analysis.tows_strategies = strategies
        analysis.updated_at = datetime.now()
        
        analysis_dict = analysis.model_dump()
        analysis_dict["id"] = str(analysis_dict["id"])
        analysis_dict["user_id"] = str(analysis_dict["user_id"])

        cache_key = f"{user_id}_{analysis_id}"
        self.analyses_cache[cache_key] = analysis_dict
        if self.cosmos_db_available and self.analyses_container:
            try:
                await self.analyses_container.replace_item(
                    item=str(analysis_id), 
                    body=analysis_dict, 
                    partition_key=str(user_id)
                )
            except CosmosExceptions.CosmosHttpResponseError as e:
                self.logger.error(f"Error saving TOWS strategies to Cosmos DB: {e}")
        return strategies

    async def generate_ai_guided_swot_items(self, analysis_id: UUID, user_id: UUID) -> None:
        """Use the LLM to suggest SWOT items for the analysis."""
        analysis = await self.get_swot_analysis(analysis_id, user_id)
        if not analysis:
            return

        prompt_input = f"Title: {analysis.title}\n\nDescription: {analysis.description or ''}"
        try:
            response = await kernel_service.invoke_semantic_function(
                "Analysis", "GenerateSWOT", prompt_input # Consider user context if skill needs it
            )
        except Exception as e:
            self.logger.error(f"Error generating SWOT items for user {user_id}: {e}")
            return

        category = None
        for line in response.splitlines():
            line = line.strip()
            if line.startswith("##"):
                if "Strengths" in line: category = SWOTCategory.STRENGTH
                elif "Weaknesses" in line: category = SWOTCategory.WEAKNESS
                elif "Opportunities" in line: category = SWOTCategory.OPPORTUNITY
                elif "Threats" in line: category = SWOTCategory.THREAT
            elif line.startswith("-") and category is not None:
                content = line.lstrip("- ").strip()
                analysis.items.append(
                    SWOTItem(
                        category=category,
                        content=content,
                        source=InsightSource.AI_GENERATED, # Make sure InsightSource is imported
                    )
                )

        analysis.updated_at = datetime.now()
        analysis_dict = analysis.model_dump()
        analysis_dict["id"] = str(analysis_dict["id"])
        analysis_dict["user_id"] = str(analysis_dict["user_id"])

        cache_key = f"{user_id}_{analysis_id}"
        self.analyses_cache[cache_key] = analysis_dict
        if self.cosmos_db_available and self.analyses_container:
            try:
                await self.analyses_container.replace_item(
                    item=str(analysis_id), 
                    body=analysis_dict, 
                    partition_key=str(user_id)
                )
            except CosmosExceptions.CosmosHttpResponseError as e:
                self.logger.error(f"Error saving AI-guided SWOT items to Cosmos DB: {e}")


    async def generate_insight_explanation(self, insight_id: UUID, user_id: UUID) -> str:
        """Generate an AI-based explanation for the given insight."""
        insight = await self.get_insight(insight_id, user_id)
        if not insight:
            raise HTTPException(status_code=404, detail="Insight not found or not accessible by user")

        prompt = (
            "Explain why the following insight is strategically important.\n"
            f"Title: {insight.title}\n"
            f"Description: {insight.description or ''}"
        )
        try:
            explanation = await kernel_service.generate_completion(prompt, max_tokens=100) # Pass user context if needed
            return explanation.strip()
        except Exception as e:
            self.logger.error(f"Error generating insight explanation for user {user_id}: {e}")
            return f"{insight.title} may impact strategic decisions. (Explanation generation failed)"

    async def generate_insights_from_data(
        self,
        user_id: UUID, # Moved user_id before optional arguments
        data_sources: Dict[str, List[UUID]], # These are IDs of other data entities
        insight_types: Optional[List[Any]] = None, # InsightType
        max_insights: Optional[int] = 5
    ) -> List[Insight]:
        """Generate insights from provided subjective and objective data for a user."""
        # This method needs to fetch actual data based on data_sources IDs,
        # potentially from other services (SubjectiveInputService, ObjectiveDataService),
        # respecting user_id for access control.
        # For now, the LLM prompts are generic.
        
        insights: List[Insight] = []
        subjective_ids = data_sources.get("subjective", [])
        objective_ids = data_sources.get("objective", [])

        for sid in subjective_ids:
            # In a real scenario, fetch subjective note 'sid' for 'user_id'
            # and use its content in the prompt.
            prompt = f"User {user_id} has a subjective note (ID: {sid}). Provide a short strategic insight based on it."
            try:
                desc = await kernel_service.generate_completion(prompt, max_tokens=60)
            except Exception:
                desc = "Observation from CEO log entry"
            
            # Create and save the insight
            new_insight_data = InsightCreate(
                title=f"Insight from subjective note {sid}",
                description=desc.strip(),
                insight_type=InsightType.OPPORTUNITY, # Example
                source=InsightSource.SUBJECTIVE,
                source_references=[{"id": str(sid), "type": "subjective_log"}]
            )
            created_insight = await self.create_insight(new_insight_data, user_id)
            insights.append(created_insight)

            if len(insights) >= max_insights:
                return insights

        for oid in objective_ids:
            # In a real scenario, fetch objective dataset 'oid' for 'user_id'
            # and use its summary/content in the prompt.
            prompt = f"User {user_id} has an objective dataset (ID: {oid}). Summarize a key trend from it."
            try:
                desc = await kernel_service.generate_completion(prompt, max_tokens=60)
            except Exception:
                desc = "Notable pattern detected in dataset"

            new_insight_data = InsightCreate(
                title=f"Trend from objective data {oid}",
                description=desc.strip(),
                insight_type=InsightType.TREND, # Example
                source=InsightSource.OBJECTIVE,
                source_references=[{"id": str(oid), "type": "objective_data"}]
            )
            created_insight = await self.create_insight(new_insight_data, user_id)
            insights.append(created_insight)
            
            if len(insights) >= max_insights:
                break
        return insights[:max_insights]
    
    # ----------- S+O Linkage Methods -----------
    
    async def discover_so_linkages(
        self, 
        user_id: str, # Keep as str as per original, router passes str(current_user.id)
        topic_context: Optional[str] = None,
        subjective_entry_ids: Optional[List[str]] = None, # These are string IDs from router
        objective_dataset_ids: Optional[List[str]] = None, # These are string IDs from router
        date_range_start: Optional[str] = None,
        date_range_end: Optional[str] = None,
        max_linkages_to_find: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Discover potential linkages between subjective and objective data.
        
        Args:
            user_id: String ID of the user requesting the analysis
            topic_context: Optional topic context for the analysis
            subjective_entry_ids: Optional list of specific subjective entry string IDs to analyze
            objective_dataset_ids: Optional list of specific objective dataset string IDs to analyze
            date_range_start: Optional start date for filtering data
            date_range_end: Optional end date for filtering data
            max_linkages_to_find: Maximum number of linkages to find (default: 5)
            
        Returns:
            List of discovered linkages
        """
        self.logger.info(f"Starting S+O linkage discovery for user {user_id}, context: {topic_context}")
        
        # Convert user_id string to UUID for internal use if necessary for other service calls
        user_uuid = UUID(user_id) # Assuming user_id from router is a valid UUID string

        retrieved_s_snippets = []
        retrieved_o_snippets = []

        # 1. Retrieve Subjective Data Snippets
        try:
            subjective_skill = kernel_service.get_skill("StrategicContext") # Skills might need user context
            subjective_function = subjective_skill.get_function("fetch_relevant_subjective_notes")
            
            query_text = topic_context or "general business strategy"
            if subjective_entry_ids: # These are string IDs
                query_text += f" IDs: {', '.join(subjective_entry_ids)}"
            if date_range_start and date_range_end:
                query_text += f" from {date_range_start} to {date_range_end}"
                
            context_vars = kernel_service.create_new_context()
            context_vars["user_id"] = user_id # Pass user_id to skill if it can use it
            context_vars["topic"] = query_text
            
            context_result = await kernel_service.run_async(subjective_function, input_vars=context_vars) # Use input_vars
            subjective_results_text = str(context_result.result if hasattr(context_result, 'result') else context_result)
            
            if "No relevant CEO's Log entries found" in subjective_results_text or not subjective_results_text.strip():
                retrieved_s_snippets = [
                    {"id": "s_fallback_1", "text": f"User {user_id} is concerned about their position in the {topic_context or 'market'}."},
                    {"id": "s_fallback_2", "text": f"User {user_id} believes they should focus more on innovation related to {topic_context or 'their products'}."}
                ]
                self.logger.info(f"Using fallback subjective data for user {user_id}")
            else:
                snippets = subjective_results_text.split("\n\n")
                for i, snippet_text in enumerate(snippets):
                    if not snippet_text.strip(): continue
                    # Simplified parsing, assuming skill returns structured data or just text
                    # If skill returns JSON strings per snippet, parse here.
                    # For now, assume each snippet_text is the content.
                    retrieved_s_snippets.append({"id": f"s_{user_id}_{i+1}", "text": snippet_text.strip()})
        except Exception as e:
            self.logger.error(f"Error retrieving subjective data for user {user_id}: {str(e)}")
            retrieved_s_snippets = [{"id": f"s_error_{user_id}", "text": f"Subjective insight for user {user_id} related to {topic_context or 'business strategy'}."}]

        # 2. Retrieve Objective Data Snippets
        try:
            objective_skill = kernel_service.get_skill("StrategicContext") # Skills might need user context
            objective_function = objective_skill.get_function("fetch_relevant_objective_data")
            
            query_text = topic_context or "general business metrics"
            if objective_dataset_ids: # These are string IDs
                query_text += f" IDs: {', '.join(objective_dataset_ids)}"
            if date_range_start and date_range_end:
                query_text += f" from {date_range_start} to {date_range_end}"
                
            context_vars = kernel_service.create_new_context()
            context_vars["user_id"] = user_id # Pass user_id to skill
            context_vars["topic"] = query_text
            
            context_result = await kernel_service.run_async(objective_function, input_vars=context_vars) # Use input_vars
            objective_results_text = str(context_result.result if hasattr(context_result, 'result') else context_result)

            if "No relevant objective data found" in objective_results_text or not objective_results_text.strip():
                retrieved_o_snippets = [
                    {"id": f"o_fallback_1_{user_id}", "title": "Market Data", "text": f"User {user_id}'s market share in {topic_context or 'the industry'} is 15%."},
                    {"id": f"o_fallback_2_{user_id}", "title": "Financial Metrics", "text": f"User {user_id}'s revenue from {topic_context or 'core products'} increased by 8%."}
                ]
                self.logger.info(f"Using fallback objective data for user {user_id}")
            else:
                # Simplified parsing, similar to subjective snippets
                sections = objective_results_text.split("\n\n")
                for i, section_text in enumerate(sections):
                    if not section_text.strip(): continue
                    # Assume skill returns structured data or just text with titles
                    # For now, assume each section_text is the content with a potential title.
                    title = f"Objective Data {i+1}"
                    text_content = section_text.strip()
                    if ":" in section_text and len(section_text.split("\n")[0]) < 100 : # Heuristic for title
                        title_part, content_part = section_text.split(":", 1)
                        title = title_part.strip()
                        text_content = content_part.strip()
                    retrieved_o_snippets.append({"id": f"o_{user_id}_{i+1}", "title": title, "text": text_content})
        except Exception as e:
            self.logger.error(f"Error retrieving objective data for user {user_id}: {str(e)}")
            retrieved_o_snippets = [{"id": f"o_error_{user_id}", "title": "Business Data", "text": f"Metrics for user {user_id} related to {topic_context or 'business performance'}."}]
        
        if not retrieved_s_snippets:
            retrieved_s_snippets = [{"id": f"s_default_{user_id}", "text": f"CEO's strategic thoughts for user {user_id} on {topic_context or 'the business'}."}]
        if not retrieved_o_snippets:
            retrieved_o_snippets = [{"id": f"o_default_{user_id}", "title": "Key Metrics", "text": f"Performance data for user {user_id} on {topic_context or 'the business'}."}]
        
        self.logger.info(f"Retrieved {len(retrieved_s_snippets)} subjective and {len(retrieved_o_snippets)} objective snippets for user {user_id}")

        # 3. Invoke the SubjectiveObjectiveLinkageSkill
        try:
            subjective_snippets_json = json.dumps(retrieved_s_snippets)
            objective_snippets_json = json.dumps(retrieved_o_snippets)
            
            context_vars = kernel_service.create_new_context()
            context_vars["user_id"] = user_id # Pass user_id to skill
            context_vars["topic_context"] = topic_context or "strategic business analysis"
            context_vars["subjective_snippets_json"] = subjective_snippets_json
            context_vars["objective_snippets_json"] = objective_snippets_json
            
            linkage_skill = kernel_service.get_skill("SubjectiveObjectiveLinkage")
            linkage_function = linkage_skill.get_function("FindPotentialLinkages")
            
            context_result = await kernel_service.run_async(linkage_function, input_vars=context_vars) # Use input_vars
            llm_response_str = str(context_result.result if hasattr(context_result, 'result') else context_result)
            
            discovered_linkages_response = []
            if llm_response_str:
                try:
                    linkage_data_list = json.loads(llm_response_str)
                    for link_data in linkage_data_list:
                        subj_snippet = next((s for s in retrieved_s_snippets if s["id"] == link_data.get("subjective_ref_id")), None)
                        obj_snippet = next((o for o in retrieved_o_snippets if o["id"] == link_data.get("objective_ref_id")), None)
                        
                        if not subj_snippet or not obj_snippet:
                            self.logger.warning(f"Skipping linkage with invalid references for user {user_id}: {link_data}")
                            continue
                        
                        linkage_type_str = link_data.get("linkage_type", "correlation").lower()
                        linkage_type_enum = LinkageType.CORRELATION # Default
                        if linkage_type_str == "contradiction": linkage_type_enum = LinkageType.CONTRADICTION
                        elif linkage_type_str == "emerging_theme": linkage_type_enum = LinkageType.EMERGING_THEME
                        
                        linkage_create_data = SOLinkageCreate(
                            user_id=UUID(user_id), # Convert string user_id to UUID for model
                            topic_context=topic_context,
                            subjective_item_id=subj_snippet["id"],
                            subjective_snippet_text=subj_snippet["text"],
                            objective_item_id=obj_snippet["id"],
                            objective_snippet_text=obj_snippet["text"],
                            objective_item_title=obj_snippet.get("title", "Objective Data"),
                            linkage_type=linkage_type_enum,
                            ai_summary_of_linkage=link_data.get("ai_summary_of_linkage", "Connection found."),
                            ai_prompt_for_ceo=link_data.get("ai_prompt_for_ceo", "Consider this connection.")
                        )
                        
                        saved_linkage = await self._save_so_linkage(linkage_create_data)
                        discovered_linkages_response.append({
                            "linkage_id": str(saved_linkage.id),
                            "subjective_snippet": subj_snippet["text"],
                            "objective_snippet": obj_snippet["text"],
                            "linkage_type": saved_linkage.linkage_type.value, # Use enum value
                            "ai_summary_of_linkage": saved_linkage.ai_summary_of_linkage,
                            "ai_prompt_for_ceo": saved_linkage.ai_prompt_for_ceo
                        })
                except json.JSONDecodeError as e:
                    self.logger.error(f"Error parsing LLM S+O linkage response for user {user_id}: {e} - Response: {llm_response_str}")
                    # Fallback: create one basic linkage if snippets exist
                    if retrieved_s_snippets and retrieved_o_snippets:
                        fallback_link_create = SOLinkageCreate(
                            user_id=UUID(user_id), topic_context=topic_context,
                            subjective_item_id=retrieved_s_snippets[0]["id"], subjective_snippet_text=retrieved_s_snippets[0]["text"],
                            objective_item_id=retrieved_o_snippets[0]["id"], objective_snippet_text=retrieved_o_snippets[0]["text"],
                            objective_item_title=retrieved_o_snippets[0].get("title", "Objective Data"),
                            linkage_type=LinkageType.CORRELATION,
                            ai_summary_of_linkage="Potential connection found (fallback).",
                            ai_prompt_for_ceo="How might this data inform your strategic thinking (fallback)?"
                        )
                        saved_fallback = await self._save_so_linkage(fallback_link_create)
                        discovered_linkages_response.append({
                            "linkage_id": str(saved_fallback.id), "subjective_snippet": saved_fallback.subjective_snippet_text,
                            "objective_snippet": saved_fallback.objective_snippet_text, "linkage_type": saved_fallback.linkage_type.value,
                            "ai_summary_of_linkage": saved_fallback.ai_summary_of_linkage, "ai_prompt_for_ceo": saved_fallback.ai_prompt_for_ceo
                        })
            return discovered_linkages_response
        except Exception as e:
            self.logger.error(f"Error processing S+O linkages for user {user_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error discovering S+O linkages: {str(e)}")

    async def _save_so_linkage(self, linkage_data: SOLinkageCreate) -> SOLinkage:
        """Save an S+O linkage to the database."""
        try:
            linkage = SOLinkage(
                id=uuid.uuid4(),
                user_id=linkage_data.user_id, # Already UUID from SOLinkageCreate
                topic_context=linkage_data.topic_context,
                subjective_item_id=linkage_data.subjective_item_id,
                subjective_snippet_text=linkage_data.subjective_snippet_text,
                objective_item_id=linkage_data.objective_item_id,
                objective_snippet_text=linkage_data.objective_snippet_text,
                objective_item_title=linkage_data.objective_item_title,
                linkage_type=linkage_data.linkage_type,
                ai_summary_of_linkage=linkage_data.ai_summary_of_linkage,
                ai_prompt_for_ceo=linkage_data.ai_prompt_for_ceo,
                created_at=datetime.now()
            )
            
            linkage_dict = linkage.model_dump()
            linkage_dict["id"] = str(linkage_dict["id"])
            linkage_dict["user_id"] = str(linkage_dict["user_id"]) # Stored as string
            linkage_dict["linkage_type"] = linkage_dict["linkage_type"].value # Store enum value

            if self.cosmos_db_available and self.so_linkages_container:
                try:
                    await self.so_linkages_container.create_item(body=linkage_dict)
                    self.logger.info(f"Saved S+O linkage {linkage.id} for user {linkage.user_id} to Cosmos DB")
                except CosmosExceptions.CosmosHttpResponseError as e:
                    self.logger.error(f"Error saving S+O linkage to Cosmos DB: {str(e)}")
                    self.so_linkages_cache[str(linkage.id)] = linkage_dict # Fallback
            else:
                self.so_linkages_cache[str(linkage.id)] = linkage_dict
            
            return linkage
        except Exception as e:
            self.logger.error(f"Error saving S+O linkage: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to save S+O linkage: {str(e)}")

    async def list_so_linkages(
        self,
        user_id: UUID, # Changed to UUID
        topic_context_filter: Optional[str] = None,
        date_range_start: Optional[str] = None,
        date_range_end: Optional[str] = None,
        limit: int = 20,
        offset: int = 0
    ) -> List[SOLinkage]: # Return SOLinkage model, not SOLinkageResponse
        """
        List S+O linkages for a specific user with optional filtering.
        
        Args:
            user_id: UUID of the user
            topic_context_filter: Optional topic context to filter by
            date_range_start: Optional start date for filtering
            date_range_end: Optional end date for filtering
            limit: Maximum number of items to return
            offset: Number of items to skip
            
        Returns:
            List of SOLinkage objects
        """
        linkages: List[SOLinkage] = []
        if self.cosmos_db_available and self.so_linkages_container:
            query_parts = ["SELECT * FROM c WHERE c.user_id = @user_id"]
            parameters = [{"name": "@user_id", "value": str(user_id)}]
            
            if topic_context_filter:
                query_parts.append("AND CONTAINS(c.topic_context, @topic)")
                parameters.append({"name": "@topic", "value": topic_context_filter})
            if date_range_start:
                query_parts.append("AND c.created_at >= @start_date")
                parameters.append({"name": "@start_date", "value": date_range_start})
            if date_range_end:
                query_parts.append("AND c.created_at <= @end_date")
                parameters.append({"name": "@end_date", "value": date_range_end})
            
            query = " ".join(query_parts) + f" ORDER BY c.created_at DESC OFFSET {offset} LIMIT {limit}"
            
            try:
                async for item in self.so_linkages_container.query_items(
                    query=query, parameters=parameters, partition_key=str(user_id)
                ):
                    item['user_id'] = UUID(item['user_id'])
                    item['id'] = UUID(item['id'])
                    item['linkage_type'] = LinkageType(item['linkage_type']) # Convert string to Enum
                    linkages.append(SOLinkage(**item))
                return linkages
            except Exception as e:
                self.logger.error(f"Error listing S+O linkages for user {user_id}: {str(e)}")
        
        # Fallback to cache
        cached_linkages = [SOLinkage(**v) for v in self.so_linkages_cache.values() if v.get("user_id") == str(user_id)]
        # Apply filters to cached_linkages (omitted for brevity, similar to list_insights cache fallback)
        cached_linkages.sort(key=lambda x: x.created_at, reverse=True)
        return cached_linkages[offset:offset+limit]

    async def get_so_linkage(self, linkage_id: UUID, user_id: UUID) -> Optional[SOLinkage]:
        """Get an S+O linkage by ID, ensuring it belongs to the user."""
        cache_key = f"{user_id}_{linkage_id}" # User-specific cache key
        if cache_key in self.so_linkages_cache:
             # Ensure linkage_type is enum if stored as value
            cached_item = self.so_linkages_cache[cache_key].copy()
            if isinstance(cached_item.get("linkage_type"), str):
                cached_item["linkage_type"] = LinkageType(cached_item["linkage_type"])
            return SOLinkage(**cached_item)

        if self.cosmos_db_available and self.so_linkages_container:
            try:
                item = await self.so_linkages_container.read_item(item=str(linkage_id), partition_key=str(user_id))
                if item.get("user_id") != str(user_id): # Double check, though partition key should handle
                    self.logger.warning(f"User {user_id} access denied for linkage {linkage_id}")
                    return None
                
                item['user_id'] = UUID(item['user_id'])
                item['id'] = UUID(item['id'])
                item['linkage_type'] = LinkageType(item['linkage_type'])
                self.so_linkages_cache[cache_key] = item # Cache the raw dict
                return SOLinkage(**item)
            except CosmosExceptions.CosmosResourceNotFoundError:
                return None
            except Exception as e:
                self.logger.error(f"Error getting S+O linkage {linkage_id} for user {user_id}: {str(e)}")
                return None
        return None
    
    async def delete_so_linkage(self, linkage_id: UUID, user_id: UUID) -> bool:
        """Delete an S+O linkage, ensuring it belongs to the user."""
        cache_key = f"{user_id}_{linkage_id}"
        if cache_key in self.so_linkages_cache:
            del self.so_linkages_cache[cache_key]

        if self.cosmos_db_available and self.so_linkages_container:
            try:
                # Verify ownership before delete if read_item wasn't called by router
                # linkage_to_delete = await self.get_so_linkage(linkage_id, user_id) 
                # if not linkage_to_delete: return False # Already handles not found or wrong user

                await self.so_linkages_container.delete_item(item=str(linkage_id), partition_key=str(user_id))
                return True
            except CosmosExceptions.CosmosResourceNotFoundError:
                return False # Already deleted or never existed for this user
            except Exception as e:
                self.logger.error(f"Error deleting S+O linkage {linkage_id} for user {user_id}: {str(e)}")
                return False
        return not self.cosmos_db_available # If only cache was affected

    # ============ SESSION MANAGEMENT METHODS ============
    
    async def create_analysis_session(self, session_data: AnalysisSessionCreate, user_id: UUID) -> AnalysisSession:
        """Create a new guided analysis session"""
        try:
            session_id = uuid.uuid4()
            
            # Initialize step states based on session type
            step_states = self._initialize_step_states(session_data.session_type)
            
            # Determine starting step
            current_step = self._get_initial_step(session_data.session_type)
            
            session = AnalysisSession(
                id=session_id,
                user_id=user_id,
                session_type=session_data.session_type,
                title=session_data.title,
                description=session_data.description,
                topic=session_data.topic,
                company_name=session_data.company_name,
                current_step=current_step,
                step_states=step_states,
                estimated_completion_time=self._estimate_session_time(session_data.session_type)
            )
            
            # Save to database
            await self._save_session_to_db(session)
            
            self.logger.info(f"Created analysis session {session_id} for user {user_id}")
            return session
            
        except Exception as e:
            self.logger.error(f"Error creating analysis session for user {user_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to create analysis session: {str(e)}")
    
    async def get_analysis_session(self, session_id: UUID, user_id: UUID) -> Optional[AnalysisSession]:
        """Get an analysis session by ID"""
        try:
            # Try cache first
            cache_key = f"{user_id}_{session_id}"
            if cache_key in self.active_sessions:
                return self.active_sessions[cache_key]
            
            # Try database
            if self.cosmos_db_available and self.sessions_container:
                try:
                    session_data = await self.sessions_container.read_item(
                        item=str(session_id), 
                        partition_key=str(user_id)
                    )
                    session = self._parse_session_from_db(session_data)
                    self.active_sessions[cache_key] = session
                    return session
                except CosmosExceptions.CosmosResourceNotFoundError:
                    return None
                except Exception as e:
                    self.logger.error(f"Error reading session {session_id}: {str(e)}")
                    return None
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting analysis session {session_id} for user {user_id}: {str(e)}")
            return None
    
    async def get_session_guidance(self, guidance_request: GuidanceRequest, user_id: UUID) -> Optional[GuidanceResponse]:
        """Get AI guidance for a specific session step"""
        try:
            session = await self.get_analysis_session(guidance_request.session_id, user_id)
            if not session:
                raise HTTPException(status_code=404, detail="Analysis session not found")
            
            # Get strategic context
            strategic_context = await self._get_strategic_context(user_id)
            
            # Get relevant subjective and objective data
            subjective_data = await self._get_relevant_subjective_data(user_id, session.topic)
            objective_data = await self._get_relevant_objective_data(user_id, session.topic)
            
            # Get current items for the step
            current_items = self._get_current_items_for_step(session, guidance_request.step_id)
            
            # Use the enhanced contextual prompt generation skill
            from ..ai.skills.analysis_skills.contextual_prompt_generation_skill import ContextualPromptGenerationSkill
            
            skill = ContextualPromptGenerationSkill()
            guidance_json = await skill.generate_session_guidance(
                session_id=str(guidance_request.session_id),
                user_id=str(user_id),
                step_id=guidance_request.step_id,
                topic=session.topic,
                company_name=session.company_name or "",
                session_type=session.session_type.value,
                current_items=json.dumps([item.content if hasattr(item, 'content') else str(item) for item in current_items]),
                strategic_context=json.dumps(strategic_context),
                subjective_data=subjective_data,
                objective_data=objective_data
            )
            
            guidance_data = json.loads(guidance_json)
            
            if "error" in guidance_data:
                raise HTTPException(status_code=500, detail=guidance_data["error"])
            
            # Create response
            response = GuidanceResponse(
                session_id=guidance_request.session_id,
                step_id=guidance_request.step_id,
                guiding_questions=guidance_data.get("guiding_questions", []),
                suggestions=guidance_data.get("suggestions", []),
                examples=guidance_data.get("examples", []),
                next_steps=guidance_data.get("next_steps", []),
                completion_guidance=guidance_data.get("completion_guidance"),
                estimated_time_remaining=guidance_data.get("estimated_time_remaining")
            )
            
            return response
            
        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(f"Error getting session guidance for {guidance_request.session_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to get guidance: {str(e)}")
    
    # ============ SESSION HELPER METHODS ============
    
    async def _save_session_to_db(self, session: AnalysisSession):
        """Save session to database and cache"""
        try:
            cache_key = f"{session.user_id}_{session.id}"
            self.active_sessions[cache_key] = session
            
            if self.cosmos_db_available and self.sessions_container:
                session_dict = session.model_dump()
                session_dict["id"] = str(session.id)
                session_dict["user_id"] = str(session.user_id)
                
                # Convert UUIDs to strings
                for item in session_dict.get("swot_items", []):
                    item["id"] = str(item["id"])
                
                await self.sessions_container.upsert_item(body=session_dict)
                
        except Exception as e:
            self.logger.error(f"Error saving session {session.id}: {str(e)}")
    
    def _initialize_step_states(self, session_type: AnalysisSessionType) -> Dict[str, SessionStepState]:
        """Initialize step states based on session type"""
        step_states = {}
        
        if session_type in [AnalysisSessionType.SWOT, AnalysisSessionType.GUIDED_SWOT]:
            for category in ["strength", "weakness", "opportunity", "threat"]:
                step_states[f"swot_{category}"] = SessionStepState(step_id=f"swot_{category}")
        
        if session_type in [AnalysisSessionType.TOWS, AnalysisSessionType.GUIDED_TOWS]:
            for cell in ["so", "wo", "st", "wt"]:
                step_states[f"tows_{cell}"] = SessionStepState(step_id=f"tows_{cell}")
        
        return step_states
    
    def _get_initial_step(self, session_type: AnalysisSessionType) -> str:
        """Determine the initial step for a session type"""
        if session_type in [AnalysisSessionType.SWOT, AnalysisSessionType.GUIDED_SWOT]:
            return "swot_strength"
        elif session_type in [AnalysisSessionType.TOWS, AnalysisSessionType.GUIDED_TOWS]:
            return "tows_so"
        else:
            return "start"
    
    def _estimate_session_time(self, session_type: AnalysisSessionType) -> int:
        """Estimate completion time in minutes"""
        if session_type in [AnalysisSessionType.SWOT, AnalysisSessionType.GUIDED_SWOT]:
            return 30  # 30 minutes for SWOT
        elif session_type in [AnalysisSessionType.TOWS, AnalysisSessionType.GUIDED_TOWS]:
            return 45  # 45 minutes for TOWS
        else:
            return 20
    
    async def _get_strategic_context(self, user_id: UUID) -> Dict[str, Any]:
        """Get user's strategic context (North Star)"""
        try:
            from ..services.strategic_foundation_service import StrategicFoundationService
            foundation_service = StrategicFoundationService()
            north_star = await foundation_service.get_north_star(user_id)
            
            if north_star:
                return {
                    "purpose": {"statement": north_star.purpose.statement} if north_star.purpose else {},
                    "vision": {"statement": north_star.vision.statement} if north_star.vision else {},
                    "values": [{"name": v.name} for v in north_star.values],
                    "strategic_goals": [{"title": g.title} for g in north_star.strategic_goals]
                }
            return {}
            
        except Exception as e:
            self.logger.error(f"Error getting strategic context for user {user_id}: {str(e)}")
            return {}
    
    async def _get_relevant_subjective_data(self, user_id: UUID, topic: str) -> str:
        """Get relevant subjective data for the topic"""
        try:
            from ..services.subjective_input_service import SubjectiveInputService
            subjective_service = SubjectiveInputService()
            
            # Get recent log entries
            entries = await subjective_service.list_log_entries(user_id, limit=10)
            
            # Filter for entries related to the topic (simple keyword matching)
            relevant_entries = []
            topic_keywords = topic.lower().split()
            
            for entry in entries:
                entry_content = entry.content.lower()
                if any(keyword in entry_content for keyword in topic_keywords):
                    relevant_entries.append(f"- {entry.content[:200]}...")
            
            return "\n".join(relevant_entries[:5]) if relevant_entries else ""
            
        except Exception as e:
            self.logger.error(f"Error getting subjective data for user {user_id}: {str(e)}")
            return ""
    
    async def _get_relevant_objective_data(self, user_id: UUID, topic: str) -> str:
        """Get relevant objective data for the topic"""
        try:
            from ..services.objective_data_service import ObjectiveDataService
            objective_service = ObjectiveDataService()
            
            # Get recent datasets
            datasets = await objective_service.list_datasets(limit=5)
            
            # Create summary of relevant data
            data_summaries = []
            for dataset in datasets:
                if dataset.description:
                    data_summaries.append(f"- {dataset.name}: {dataset.description[:150]}...")
            
            return "\n".join(data_summaries) if data_summaries else ""
            
        except Exception as e:
            self.logger.error(f"Error getting objective data for user {user_id}: {str(e)}")
            return ""
    
    def _get_current_items_for_step(self, session: AnalysisSession, step_id: str) -> List[Any]:
        """Get current items for a specific step"""
        if step_id.startswith("swot_"):
            category = step_id.replace("swot_", "")
            return [item for item in session.swot_items if item.category.value == category]
        elif step_id.startswith("tows_"):
            cell_type = step_id.replace("tows_", "").upper()
            return [strategy for strategy in session.tows_strategies if strategy.get("cell_type") == cell_type]
        else:
            return []

    # Additional Session Management Methods
    
    async def list_analysis_sessions(
        self, 
        user_id: UUID, 
        status_filter: Optional[AnalysisSessionStatus] = None,
        session_type: Optional[AnalysisSessionType] = None,
        limit: int = 10, 
        offset: int = 0
    ) -> List[AnalysisSession]:
        """List analysis sessions for a user with optional filtering"""
        try:
            sessions = []
            
            # If Cosmos DB is available, query from database
            if self.cosmos_db_available and self.sessions_container:
                query = "SELECT * FROM c WHERE c.user_id = @user_id"
                parameters = [{"name": "@user_id", "value": str(user_id)}]
                
                # Add status filter
                if status_filter:
                    query += " AND c.status = @status"
                    parameters.append({"name": "@status", "value": status_filter.value})
                
                # Add session type filter
                if session_type:
                    query += " AND c.session_type = @session_type"
                    parameters.append({"name": "@session_type", "value": session_type.value})
                
                # Add ordering and pagination
                query += " ORDER BY c.updated_at DESC OFFSET @offset LIMIT @limit"
                parameters.extend([
                    {"name": "@offset", "value": offset},
                    {"name": "@limit", "value": limit}
                ])
                
                async for item_data in self.sessions_container.query_items(
                    query=query, parameters=parameters, enable_cross_partition_query=True
                ):
                    sessions.append(AnalysisSession(**item_data))
            else:
                # Use in-memory cache as fallback
                user_sessions = [session for session in self.active_sessions.values() 
                               if session.user_id == user_id]
                
                # Apply filters
                if status_filter:
                    user_sessions = [s for s in user_sessions if s.status == status_filter]
                if session_type:
                    user_sessions = [s for s in user_sessions if s.session_type == session_type]
                
                # Sort by updated_at and apply pagination
                user_sessions.sort(key=lambda x: x.updated_at, reverse=True)
                sessions = user_sessions[offset:offset + limit]
            
            self.logger.info(f"Listed {len(sessions)} analysis sessions for user {user_id}")
            return sessions
            
        except Exception as e:
            self.logger.error(f"Error listing analysis sessions for user {user_id}: {str(e)}")
            return []

    async def update_analysis_session(
        self, 
        session_id: UUID, 
        session_update: AnalysisSessionUpdate, 
        user_id: UUID
    ) -> Optional[AnalysisSession]:
        """Update an analysis session"""
        try:
            # Get existing session
            session = await self.get_analysis_session(session_id, user_id)
            if not session:
                return None
            
            # Apply updates
            if session_update.status is not None:
                session.status = session_update.status
            if session_update.current_step is not None:
                session.current_step = session_update.current_step
            if session_update.title is not None:
                session.title = session_update.title
            if session_update.description is not None:
                session.description = session_update.description
            
            # Update timestamps
            session.updated_at = datetime.now()
            session.last_interaction_at = datetime.now()
            
            # Save to database
            await self._save_session_to_db(session)
            
            self.logger.info(f"Updated analysis session {session_id} for user {user_id}")
            return session
            
        except Exception as e:
            self.logger.error(f"Error updating analysis session {session_id}: {str(e)}")
            return None

    async def delete_analysis_session(self, session_id: UUID, user_id: UUID) -> bool:
        """Delete an analysis session"""
        try:
            # Verify session exists and belongs to user
            session = await self.get_analysis_session(session_id, user_id)
            if not session:
                return False
            
            # Remove from database if available
            if self.cosmos_db_available and self.sessions_container:
                await self.sessions_container.delete_item(
                    item=str(session_id),
                    partition_key=str(user_id)
                )
            
            # Remove from cache
            cache_key = f"{user_id}_{session_id}"
            if cache_key in self.active_sessions:
                del self.active_sessions[cache_key]
            
            self.logger.info(f"Deleted analysis session {session_id} for user {user_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error deleting analysis session {session_id}: {str(e)}")
            return False

    async def request_analysis_guidance(
        self, 
        guidance_request: GuidanceRequest, 
        user_id: UUID
    ) -> GuidanceResponse:
        """Request AI guidance for analysis session - wrapper for get_session_guidance"""
        guidance = await self.get_session_guidance(guidance_request, user_id)
        if not guidance:
            raise HTTPException(status_code=500, detail="Failed to generate guidance")
        return guidance

    async def complete_session_step(
        self, 
        session_id: UUID, 
        step_id: str, 
        user_id: UUID
    ) -> Optional[AnalysisSession]:
        """Mark a session step as completed"""
        try:
            session = await self.get_analysis_session(session_id, user_id)
            if not session:
                return None
            
            # Update step state
            if step_id in session.step_states:
                session.step_states[step_id].is_completed = True
                session.step_states[step_id].completion_percentage = 100.0
            
            # Add to completed steps if not already there
            if step_id not in session.completed_steps:
                session.completed_steps.append(step_id)
            
            # Determine next step based on session type and progress
            session.current_step = self._get_next_step(session, step_id)
            
            # Update timestamps
            session.updated_at = datetime.now()
            session.last_interaction_at = datetime.now()
            
            # Save to database
            await self._save_session_to_db(session)
            
            self.logger.info(f"Completed step {step_id} for session {session_id}")
            return session
            
        except Exception as e:
            self.logger.error(f"Error completing step {step_id} for session {session_id}: {str(e)}")
            return None

    def _get_next_step(self, session: AnalysisSession, completed_step: str) -> str:
        """Determine the next step in the analysis session"""
        if session.session_type in [AnalysisSessionType.SWOT, AnalysisSessionType.GUIDED_SWOT]:
            swot_steps = ["swot_strengths", "swot_weaknesses", "swot_opportunities", "swot_threats"]
            try:
                current_index = swot_steps.index(completed_step)
                if current_index < len(swot_steps) - 1:
                    return swot_steps[current_index + 1]
                else:
                    return "swot_complete"
            except ValueError:
                return session.current_step
        
        elif session.session_type in [AnalysisSessionType.TOWS, AnalysisSessionType.GUIDED_TOWS]:
            tows_steps = ["tows_so", "tows_wo", "tows_st", "tows_wt"]
            try:
                current_index = tows_steps.index(completed_step)
                if current_index < len(tows_steps) - 1:
                    return tows_steps[current_index + 1]
                else:
                    return "tows_complete"
            except ValueError:
                return session.current_step
        
        return session.current_step
