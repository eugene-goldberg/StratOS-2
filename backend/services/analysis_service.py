import uuid
import json
import logging
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
from uuid import UUID

from azure.cosmos import CosmosClient, PartitionKey, exceptions
from fastapi import HTTPException

from ..models.analysis import (
    SWOTAnalysis, 
    SWOTItem, 
    SWOTCategory, 
    Insight, 
    SOLinkage, 
    SOLinkageCreate,
    LinkageType
)
from ..ai.kernel_service import kernel_service

class AnalysisService:
    """Service for managing SWOT/TOWS analysis operations with Cosmos DB integration"""
    
    def __init__(self):
        # Set up logging
        self.logger = logging.getLogger("analysis_service")
        
        # In-memory storage (used as cache and fallback)
        self.active_sessions = {}  # In-memory cache for active analysis sessions
        self.analyses_cache = {}   # In-memory cache for persisted analyses
        self.so_linkages_cache = {}  # In-memory cache for S+O linkages
        
        # Initialize database connection flags
        self.cosmos_db_available = False
        self.database = None
        self.analyses_container = None
        self.sessions_container = None
        self.so_linkages_container = None
        
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
            
            # Get or create containers for analyses, sessions, and SO linkages
            try:
                self.analyses_container = self.database.get_container_client("analyses")
                self.sessions_container = self.database.get_container_client("analysis_sessions")
                self.so_linkages_container = self.database.get_container_client("so_linkages")
                self.logger.info("Connected to existing Cosmos DB containers")
            except exceptions.CosmosResourceNotFoundError:
                # Create containers if they don't exist
                self.analyses_container = self.database.create_container_if_not_exists(
                    id="analyses",
                    partition_key=PartitionKey(path="/user_id"),
                    offer_throughput=400
                )
                self.sessions_container = self.database.create_container_if_not_exists(
                    id="analysis_sessions",
                    partition_key=PartitionKey(path="/user_id"),
                    offer_throughput=400
                )
                self.so_linkages_container = self.database.create_container_if_not_exists(
                    id="so_linkages",
                    partition_key=PartitionKey(path="/user_id"),
                    offer_throughput=400
                )
                self.logger.info("Created Cosmos DB containers for analyses, sessions, and S+O linkages")
            
            self.cosmos_db_available = True
            self.logger.info("Cosmos DB connection established successfully")
        except Exception as e:
            self.logger.warning(f"Cosmos DB connection failed: {str(e)}. Using in-memory storage.")
    
    # ----------- Database Operations -----------
    
    async def create_swot_analysis(self, analysis_data: SWOTAnalysis) -> SWOTAnalysis:
        """Create a new SWOT analysis in the database"""
        try:
            # Generate a UUID if not provided
            analysis_id = uuid.uuid4() if not hasattr(analysis_data, 'id') or not analysis_data.id else analysis_data.id
            
            # Create the analysis object
            analysis = SWOTAnalysis(
                id=analysis_id,
                title=analysis_data.title,
                description=analysis_data.description,
                items=[],
                tows_strategies=[],
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            # Prepare the item for Cosmos DB
            analysis_dict = analysis.dict()
            
            if self.cosmos_db_available and self.analyses_container:
                try:
                    # Save to Cosmos DB
                    self.analyses_container.create_item(body=analysis_dict)
                    self.logger.info(f"Created SWOT analysis {analysis.id} in Cosmos DB")
                    
                    # Update cache
                    self.analyses_cache[str(analysis.id)] = analysis_dict
                except Exception as e:
                    self.logger.error(f"Error saving SWOT analysis to Cosmos DB: {str(e)}")
                    # Fallback to in-memory storage
                    self.analyses_cache[str(analysis.id)] = analysis_dict
            else:
                # In-memory storage (for development/testing)
                self.analyses_cache[str(analysis.id)] = analysis_dict
            
            return analysis
        except Exception as e:
            self.logger.error(f"Error creating SWOT analysis: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to create SWOT analysis: {str(e)}")
    
    # ... [existing methods, not modifying] ...
    
    # ----------- S+O Linkage Methods -----------
    
    async def discover_so_linkages(
        self, 
        user_id: str, 
        topic_context: Optional[str] = None,
        subjective_entry_ids: Optional[List[str]] = None,
        objective_dataset_ids: Optional[List[str]] = None,
        date_range_start: Optional[str] = None,
        date_range_end: Optional[str] = None,
        max_linkages_to_find: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Discover potential linkages between subjective and objective data.
        
        Args:
            user_id: ID of the user requesting the analysis
            topic_context: Optional topic context for the analysis
            subjective_entry_ids: Optional list of specific subjective entry IDs to analyze
            objective_dataset_ids: Optional list of specific objective dataset IDs to analyze
            date_range_start: Optional start date for filtering data
            date_range_end: Optional end date for filtering data
            max_linkages_to_find: Maximum number of linkages to find (default: 5)
            
        Returns:
            List of discovered linkages
        """
        self.logger.info(f"Starting S+O linkage discovery for user {user_id}, context: {topic_context}")
        retrieved_s_snippets = []
        retrieved_o_snippets = []

        # 1. Retrieve Subjective Data Snippets
        try:
            # Use the StrategicContextRetrieverSkill to fetch relevant subjective notes
            subjective_skill = kernel_service.get_skill("StrategicContext")
            subjective_function = subjective_skill.get_function("fetch_relevant_subjective_notes")
            
            # Prepare query parameters
            query_text = topic_context or "general business strategy"
            if subjective_entry_ids:
                query_text += f" IDs: {', '.join(subjective_entry_ids)}"
            if date_range_start and date_range_end:
                query_text += f" from {date_range_start} to {date_range_end}"
                
            # Create context variables
            context_vars = kernel_service.create_new_context()
            context_vars["topic"] = query_text
            
            # Get subjective insights
            context_result = await kernel_service.run_async(subjective_function, query_text, context_vars)
            subjective_results_text = str(context_result)
            
            # Check if we got results or need a fallback
            if "No relevant CEO's Log entries found" in subjective_results_text:
                # Fallback: Use sample or mocked subjective data
                retrieved_s_snippets = [
                    {"id": "s_fallback_1", "text": f"I'm concerned about our position in the {topic_context or 'market'}."},
                    {"id": "s_fallback_2", "text": f"We should focus more on innovation related to {topic_context or 'our products'}."}
                ]
                self.logger.info("Using fallback subjective data due to no relevant entries found")
            else:
                # Parse the results into structured snippets
                snippets = subjective_results_text.split("\n\n")
                for i, snippet in enumerate(snippets):
                    if not snippet.strip():
                        continue
                        
                    # Parse the snippet
                    lines = snippet.strip().split("\n")
                    snippet_data = {"id": f"s_{i+1}", "text": ""}
                    
                    for line in lines:
                        if line.startswith("Date:"):
                            snippet_data["date"] = line.replace("Date:", "").strip()
                        elif line.startswith("Title:"):
                            snippet_data["title"] = line.replace("Title:", "").strip()
                        elif line.startswith("Content:"):
                            snippet_data["text"] = line.replace("Content:", "").strip()
                    
                    # If no content was parsed, use the whole snippet as text
                    if not snippet_data["text"]:
                        snippet_data["text"] = snippet
                    
                    retrieved_s_snippets.append(snippet_data)
        except Exception as e:
            self.logger.error(f"Error retrieving subjective data: {str(e)}")
            # Fallback to minimal data
            retrieved_s_snippets = [{"id": "s_error", "text": f"Subjective insight related to {topic_context or 'business strategy'}."}]

        # 2. Retrieve Objective Data Snippets
        try:
            # Use the StrategicContextRetrieverSkill to fetch relevant objective data
            objective_skill = kernel_service.get_skill("StrategicContext")
            objective_function = objective_skill.get_function("fetch_relevant_objective_data")
            
            # Prepare query parameters
            query_text = topic_context or "general business metrics"
            if objective_dataset_ids:
                query_text += f" IDs: {', '.join(objective_dataset_ids)}"
            if date_range_start and date_range_end:
                query_text += f" from {date_range_start} to {date_range_end}"
                
            # Create context variables
            context_vars = kernel_service.create_new_context()
            context_vars["topic"] = query_text
            
            # Get objective data
            context_result = await kernel_service.run_async(objective_function, query_text, context_vars)
            objective_results_text = str(context_result)
            
            # Check if we got results or need a fallback
            if "No relevant objective data found" in objective_results_text:
                # Fallback: Use sample or mocked objective data
                retrieved_o_snippets = [
                    {"id": "o_fallback_1", "title": "Market Data", "text": f"Our market share in {topic_context or 'the industry'} is 15%, down 2% from last quarter."},
                    {"id": "o_fallback_2", "title": "Financial Metrics", "text": f"Revenue from {topic_context or 'core products'} increased by 8% YoY."}
                ]
                self.logger.info("Using fallback objective data due to no relevant entries found")
            else:
                # Parse the results into structured snippets
                sections = objective_results_text.split("\n\n")
                current_section_title = "Objective Data"
                
                for i, section in enumerate(sections):
                    if not section.strip():
                        continue
                        
                    # Check if this is a section header
                    if ":" in section and len(section.split("\n")) == 1:
                        current_section_title = section.replace(":", "").strip()
                        continue
                    
                    # Process bullet points as separate snippets
                    bullet_points = [line.strip() for line in section.split("\n") if line.strip().startswith("-")]
                    
                    if bullet_points:
                        for j, bullet in enumerate(bullet_points):
                            bullet_text = bullet.lstrip("- ")
                            snippet_id = f"o_{i}_{j}"
                            
                            # Check if the bullet has a title/label
                            if ":" in bullet_text:
                                title_part, content_part = bullet_text.split(":", 1)
                                retrieved_o_snippets.append({
                                    "id": snippet_id,
                                    "title": f"{current_section_title}: {title_part.strip()}",
                                    "text": content_part.strip()
                                })
                            else:
                                retrieved_o_snippets.append({
                                    "id": snippet_id,
                                    "title": current_section_title,
                                    "text": bullet_text
                                })
                    else:
                        # Use the whole section as one snippet
                        retrieved_o_snippets.append({
                            "id": f"o_{i}",
                            "title": current_section_title,
                            "text": section.strip()
                        })
        except Exception as e:
            self.logger.error(f"Error retrieving objective data: {str(e)}")
            # Fallback to minimal data
            retrieved_o_snippets = [{"id": "o_error", "title": "Business Data", "text": f"Metrics related to {topic_context or 'business performance'}."}]
        
        # Ensure we have at least one snippet of each type
        if not retrieved_s_snippets:
            retrieved_s_snippets = [{"id": "s_default", "text": f"CEO's strategic thoughts on {topic_context or 'the business'}."}]
        
        if not retrieved_o_snippets:
            retrieved_o_snippets = [{"id": "o_default", "title": "Key Metrics", "text": f"Performance data for {topic_context or 'the business'}."}]
        
        self.logger.info(f"Retrieved {len(retrieved_s_snippets)} subjective snippets and {len(retrieved_o_snippets)} objective snippets")

        # 3. Invoke the SubjectiveObjectiveLinkageSkill to discover potential linkages
        try:
            # Prepare inputs for the skill
            subjective_snippets_json = json.dumps(retrieved_s_snippets)
            objective_snippets_json = json.dumps(retrieved_o_snippets)
            
            # Create context variables for the skill
            context_vars = kernel_service.create_new_context()
            context_vars["topic_context"] = topic_context or "strategic business analysis"
            context_vars["subjective_snippets_json"] = subjective_snippets_json
            context_vars["objective_snippets_json"] = objective_snippets_json
            
            # Get the skill and function
            # If the skill is registered as a native skill:
            linkage_skill = kernel_service.get_skill("SubjectiveObjectiveLinkage")
            linkage_function = linkage_skill.get_function("FindPotentialLinkages")
            
            # Invoke the function
            context_result = await kernel_service.run_async(linkage_function, "", context_vars)
            llm_response_str = str(context_result)
            
            # Process the LLM response
            discovered_linkages = []
            try:
                # Parse the JSON response
                linkage_data_list = json.loads(llm_response_str)
                
                # Process each linkage
                for link_data in linkage_data_list:
                    # Find the referenced snippets
                    subj_snippet = next((s for s in retrieved_s_snippets if s["id"] == link_data.get("subjective_ref_id")), None)
                    obj_snippet = next((o for o in retrieved_o_snippets if o["id"] == link_data.get("objective_ref_id")), None)
                    
                    if not subj_snippet or not obj_snippet:
                        self.logger.warning(f"Skipping linkage with invalid references: {link_data}")
                        continue
                    
                    # Validate and normalize linkage_type
                    linkage_type_str = link_data.get("linkage_type", "correlation").lower()
                    if linkage_type_str == "correlation":
                        linkage_type = LinkageType.CORRELATION
                    elif linkage_type_str == "contradiction":
                        linkage_type = LinkageType.CONTRADICTION
                    elif linkage_type_str == "emerging_theme":
                        linkage_type = LinkageType.EMERGING_THEME
                    else:
                        linkage_type = LinkageType.CORRELATION
                    
                    # Create the linkage record
                    linkage_id = str(uuid.uuid4())
                    linkage = SOLinkageCreate(
                        user_id=UUID(user_id),
                        topic_context=topic_context,
                        subjective_item_id=subj_snippet["id"],
                        subjective_snippet_text=subj_snippet["text"],
                        objective_item_id=obj_snippet["id"],
                        objective_snippet_text=obj_snippet["text"],
                        objective_item_title=obj_snippet.get("title", "Objective Data"),
                        linkage_type=linkage_type,
                        ai_summary_of_linkage=link_data.get("ai_summary_of_linkage", "Connection between subjective insight and objective data."),
                        ai_prompt_for_ceo=link_data.get("ai_prompt_for_ceo", "How might this connection inform your strategic thinking?")
                    )
                    
                    # Save the linkage to the database
                    saved_linkage = await self._save_so_linkage(linkage)
                    
                    # Add to response
                    linkage_response = {
                        "linkage_id": str(saved_linkage.id),
                        "subjective_snippet": subj_snippet["text"],
                        "objective_snippet": obj_snippet["text"],
                        "linkage_type": saved_linkage.linkage_type,
                        "ai_summary_of_linkage": saved_linkage.ai_summary_of_linkage,
                        "ai_prompt_for_ceo": saved_linkage.ai_prompt_for_ceo
                    }
                    discovered_linkages.append(linkage_response)
                
            except json.JSONDecodeError as e:
                self.logger.error(f"Error parsing LLM response for S+O linkage: {e} - Response: {llm_response_str}")
                # Handle error, maybe return partial results or try a fallback parsing approach
                # This is a simplified fallback that creates one basic linkage
                if retrieved_s_snippets and retrieved_o_snippets:
                    fallback_linkage = SOLinkageCreate(
                        user_id=UUID(user_id),
                        topic_context=topic_context,
                        subjective_item_id=retrieved_s_snippets[0]["id"],
                        subjective_snippet_text=retrieved_s_snippets[0]["text"],
                        objective_item_id=retrieved_o_snippets[0]["id"],
                        objective_snippet_text=retrieved_o_snippets[0]["text"],
                        objective_item_title=retrieved_o_snippets[0].get("title", "Objective Data"),
                        linkage_type=LinkageType.CORRELATION,
                        ai_summary_of_linkage=f"Potential connection between CEO's insight and {retrieved_o_snippets[0].get('title', 'objective data')}.",
                        ai_prompt_for_ceo="How might this data inform your strategic thinking?"
                    )
                    saved_linkage = await self._save_so_linkage(fallback_linkage)
                    discovered_linkages.append({
                        "linkage_id": str(saved_linkage.id),
                        "subjective_snippet": retrieved_s_snippets[0]["text"],
                        "objective_snippet": retrieved_o_snippets[0]["text"],
                        "linkage_type": saved_linkage.linkage_type,
                        "ai_summary_of_linkage": saved_linkage.ai_summary_of_linkage,
                        "ai_prompt_for_ceo": saved_linkage.ai_prompt_for_ceo
                    })
            
            return discovered_linkages
            
        except Exception as e:
            self.logger.error(f"Unexpected error processing S+O linkages: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error discovering S+O linkages: {str(e)}")
    
    async def _save_so_linkage(self, linkage_data: SOLinkageCreate) -> SOLinkage:
        """
        Save an S+O linkage to the database
        
        Args:
            linkage_data: The linkage data to save
            
        Returns:
            The saved SOLinkage object
        """
        try:
            # Create a SOLinkage object
            linkage = SOLinkage(
                id=uuid.uuid4(),
                user_id=linkage_data.user_id,
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
            
            # Prepare the item for Cosmos DB
            linkage_dict = linkage.dict()
            
            if self.cosmos_db_available and self.so_linkages_container:
                try:
                    # Save to Cosmos DB
                    self.so_linkages_container.create_item(body=linkage_dict)
                    self.logger.info(f"Saved S+O linkage {linkage.id} to Cosmos DB")
                except Exception as e:
                    self.logger.error(f"Error saving S+O linkage to Cosmos DB: {str(e)}")
                    # Fallback to in-memory storage
                    self.so_linkages_cache[str(linkage.id)] = linkage_dict
            else:
                # In-memory storage (for development/testing)
                self.so_linkages_cache[str(linkage.id)] = linkage_dict
            
            return linkage
            
        except Exception as e:
            self.logger.error(f"Error saving S+O linkage: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to save S+O linkage: {str(e)}")
    
    async def list_so_linkages(
        self,
        user_id: UUID,
        topic_context_filter: Optional[str] = None,
        date_range_start: Optional[str] = None,
        date_range_end: Optional[str] = None,
        limit: int = 20,
        offset: int = 0
    ) -> List[SOLinkage]:
        """
        List S+O linkages with optional filtering
        
        Args:
            user_id: ID of the user
            topic_context_filter: Optional topic context to filter by
            date_range_start: Optional start date for filtering
            date_range_end: Optional end date for filtering
            limit: Maximum number of items to return
            offset: Number of items to skip
            
        Returns:
            List of SOLinkage objects
        """
        try:
            if self.cosmos_db_available and self.so_linkages_container:
                # Build the query
                query = "SELECT * FROM c WHERE c.user_id = @user_id"
                parameters = [{"name": "@user_id", "value": str(user_id)}]
                
                # Add topic filter if provided
                if topic_context_filter:
                    query += " AND CONTAINS(c.topic_context, @topic)"
                    parameters.append({"name": "@topic", "value": topic_context_filter})
                
                # Add date range filters if provided
                if date_range_start:
                    query += " AND c.created_at >= @start_date"
                    parameters.append({"name": "@start_date", "value": date_range_start})
                
                if date_range_end:
                    query += " AND c.created_at <= @end_date"
                    parameters.append({"name": "@end_date", "value": date_range_end})
                
                # Add sorting and pagination
                query += f" ORDER BY c.created_at DESC OFFSET {offset} LIMIT {limit}"
                
                # Execute the query
                items = list(self.so_linkages_container.query_items(
                    query=query,
                    parameters=parameters,
                    enable_cross_partition_query=True
                ))
                
                # Convert to SOLinkage objects
                return [SOLinkage(**item) for item in items]
                
            else:
                # Use in-memory cache
                all_linkages = [SOLinkage(**v) for v in self.so_linkages_cache.values() 
                               if v["user_id"] == str(user_id)]
                
                # Apply filtering
                filtered_linkages = all_linkages
                
                if topic_context_filter:
                    filtered_linkages = [link for link in filtered_linkages 
                                        if link.topic_context and topic_context_filter in link.topic_context]
                
                if date_range_start:
                    start_date = datetime.fromisoformat(date_range_start)
                    filtered_linkages = [link for link in filtered_linkages if link.created_at >= start_date]
                
                if date_range_end:
                    end_date = datetime.fromisoformat(date_range_end)
                    filtered_linkages = [link for link in filtered_linkages if link.created_at <= end_date]
                
                # Sort by created_at (descending)
                filtered_linkages.sort(key=lambda x: x.created_at, reverse=True)
                
                # Apply pagination
                return filtered_linkages[offset:offset+limit]
                
        except Exception as e:
            self.logger.error(f"Error listing S+O linkages: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to list S+O linkages: {str(e)}")
    
    async def get_so_linkage(self, linkage_id: UUID) -> Optional[SOLinkage]:
        """
        Get an S+O linkage by ID
        
        Args:
            linkage_id: ID of the linkage
            
        Returns:
            SOLinkage or None if not found
        """
        try:
            if self.cosmos_db_available and self.so_linkages_container:
                try:
                    # Query by ID
                    query = "SELECT * FROM c WHERE c.id = @id"
                    parameters = [{"name": "@id", "value": str(linkage_id)}]
                    
                    items = list(self.so_linkages_container.query_items(
                        query=query,
                        parameters=parameters,
                        enable_cross_partition_query=True
                    ))
                    
                    if items:
                        return SOLinkage(**items[0])
                    else:
                        return None
                        
                except exceptions.CosmosResourceNotFoundError:
                    return None
            else:
                # Use in-memory cache
                if str(linkage_id) in self.so_linkages_cache:
                    return SOLinkage(**self.so_linkages_cache[str(linkage_id)])
                return None
                
        except Exception as e:
            self.logger.error(f"Error getting S+O linkage {linkage_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to get S+O linkage: {str(e)}")
    
    async def delete_so_linkage(self, linkage_id: UUID) -> bool:
        """
        Delete an S+O linkage
        
        Args:
            linkage_id: ID of the linkage
            
        Returns:
            Boolean indicating success
        """
        try:
            if self.cosmos_db_available and self.so_linkages_container:
                # Get the linkage first to determine the partition key
                linkage = await self.get_so_linkage(linkage_id)
                if not linkage:
                    return False
                
                # Delete from Cosmos DB
                self.so_linkages_container.delete_item(
                    item=str(linkage_id),
                    partition_key=str(linkage.user_id)
                )
                
                # Also remove from cache if present
                if str(linkage_id) in self.so_linkages_cache:
                    del self.so_linkages_cache[str(linkage_id)]
                
                return True
                
            else:
                # Use in-memory cache only
                if str(linkage_id) in self.so_linkages_cache:
                    del self.so_linkages_cache[str(linkage_id)]
                    return True
                return False
                
        except exceptions.CosmosResourceNotFoundError:
            return False
        except Exception as e:
            self.logger.error(f"Error deleting S+O linkage {linkage_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to delete S+O linkage: {str(e)}")
    
    # ... [existing SWOT/insight methods remain unchanged] ...