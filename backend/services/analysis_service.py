import uuid
import json
import logging
import os
from typing import List, Dict, Any, Optional
from datetime import datetime

from azure.cosmos import CosmosClient, PartitionKey, exceptions
from fastapi import HTTPException

from ..models.analysis import SWOTAnalysis, SWOTItem, SWOTCategory, Insight, TOWSStrategy
from ..ai.kernel_service import kernel_service

class AnalysisService:
    """Service for managing SWOT/TOWS analysis operations with Cosmos DB integration"""
    
    def __init__(self):
        # Set up logging
        self.logger = logging.getLogger("analysis_service")
        
        # In-memory storage (used as cache and fallback)
        self.active_sessions = {}  # In-memory cache for active analysis sessions
        self.analyses_cache = {}   # In-memory cache for persisted analyses
        
        # Initialize database connection flags
        self.cosmos_db_available = False
        self.database = None
        self.analyses_container = None
        self.sessions_container = None
        
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
            
            # Get or create containers for analyses and sessions
            try:
                self.analyses_container = self.database.get_container_client("analyses")
                self.sessions_container = self.database.get_container_client("analysis_sessions")
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
                self.logger.info("Created Cosmos DB containers for analyses and sessions")
            
            self.cosmos_db_available = True
            self.logger.info("Cosmos DB connection established successfully")
        except Exception as e:
            self.logger.warning(f"Cosmos DB connection failed: {str(e)}. Using in-memory storage.")
    
    # ----------- Database Operations -----------
    
    async def create_swot_analysis(self, analysis: SWOTAnalysis) -> SWOTAnalysis:
        """Create a new SWOT analysis in the database"""
        try:
            if not analysis.id:
                analysis.id = str(uuid.uuid4())
            
            if not analysis.created_at:
                analysis.created_at = datetime.utcnow().isoformat()
            
            # Prepare the item for Cosmos DB
            analysis_dict = analysis.dict()
            
            if self.cosmos_db_available and self.analyses_container:
                try:
                    # Save to Cosmos DB
                    self.analyses_container.create_item(body=analysis_dict)
                    self.logger.info(f"Created SWOT analysis {analysis.id} in Cosmos DB")
                    
                    # Update cache
                    self.analyses_cache[analysis.id] = analysis_dict
                except Exception as e:
                    self.logger.error(f"Error saving SWOT analysis to Cosmos DB: {str(e)}")
                    # Fallback to in-memory storage
                    self.analyses_cache[analysis.id] = analysis_dict
            else:
                # In-memory storage (for development/testing)
                self.analyses_cache[analysis.id] = analysis_dict
                self.logger.info(f"Created SWOT analysis {analysis.id} in memory")
            
            return analysis
        except Exception as e:
            self.logger.error(f"Error creating SWOT analysis: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to create SWOT analysis: {str(e)}")
    
    async def get_swot_analysis(self, analysis_id: str) -> Optional[SWOTAnalysis]:
        """Retrieve a SWOT analysis by ID"""
        try:
            # Check cache first
            if analysis_id in self.analyses_cache:
                return SWOTAnalysis.parse_obj(self.analyses_cache[analysis_id])
            
            if self.cosmos_db_available and self.analyses_container:
                try:
                    # Query Cosmos DB
                    query = f"SELECT * FROM c WHERE c.id = '{analysis_id}'"
                    items = list(self.analyses_container.query_items(
                        query=query,
                        enable_cross_partition_query=True
                    ))
                    
                    if items:
                        # Update cache
                        self.analyses_cache[analysis_id] = items[0]
                        return SWOTAnalysis.parse_obj(items[0])
                except Exception as e:
                    self.logger.error(f"Error querying SWOT analysis from Cosmos DB: {str(e)}")
            
            return None
        except Exception as e:
            self.logger.error(f"Error retrieving SWOT analysis: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to retrieve SWOT analysis: {str(e)}")
    
    async def update_swot_analysis(self, analysis: SWOTAnalysis) -> SWOTAnalysis:
        """Update an existing SWOT analysis"""
        try:
            if not analysis.id:
                raise ValueError("Analysis ID is required for updates")
            
            analysis.updated_at = datetime.utcnow().isoformat()
            
            # Prepare the item for Cosmos DB
            analysis_dict = analysis.dict()
            
            if self.cosmos_db_available and self.analyses_container:
                try:
                    # Update in Cosmos DB
                    self.analyses_container.replace_item(
                        item=analysis.id,
                        body=analysis_dict
                    )
                    self.logger.info(f"Updated SWOT analysis {analysis.id} in Cosmos DB")
                    
                    # Update cache
                    self.analyses_cache[analysis.id] = analysis_dict
                except exceptions.CosmosResourceNotFoundError:
                    # Item doesn't exist, create it
                    self.analyses_container.create_item(body=analysis_dict)
                    self.logger.info(f"Created new SWOT analysis {analysis.id} in Cosmos DB during update")
                    
                    # Update cache
                    self.analyses_cache[analysis.id] = analysis_dict
                except Exception as e:
                    self.logger.error(f"Error updating SWOT analysis in Cosmos DB: {str(e)}")
                    # Fallback to in-memory storage
                    self.analyses_cache[analysis.id] = analysis_dict
            else:
                # In-memory update
                self.analyses_cache[analysis.id] = analysis_dict
                self.logger.info(f"Updated SWOT analysis {analysis.id} in memory")
            
            return analysis
        except Exception as e:
            self.logger.error(f"Error updating SWOT analysis: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to update SWOT analysis: {str(e)}")
    
    async def delete_swot_analysis(self, analysis_id: str) -> bool:
        """Delete a SWOT analysis by ID"""
        try:
            # Remove from cache
            if analysis_id in self.analyses_cache:
                del self.analyses_cache[analysis_id]
            
            if self.cosmos_db_available and self.analyses_container:
                try:
                    # Delete from Cosmos DB
                    self.analyses_container.delete_item(
                        item=analysis_id,
                        partition_key=None  # This requires the partition key value
                    )
                    self.logger.info(f"Deleted SWOT analysis {analysis_id} from Cosmos DB")
                    return True
                except exceptions.CosmosResourceNotFoundError:
                    self.logger.warning(f"SWOT analysis {analysis_id} not found in Cosmos DB during delete")
                    return False
                except Exception as e:
                    self.logger.error(f"Error deleting SWOT analysis from Cosmos DB: {str(e)}")
                    return False
            else:
                # In-memory deletion
                if analysis_id in self.analyses_cache:
                    del self.analyses_cache[analysis_id]
                    self.logger.info(f"Deleted SWOT analysis {analysis_id} from memory")
                    return True
                return False
            
            return True
        except Exception as e:
            self.logger.error(f"Error deleting SWOT analysis: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to delete SWOT analysis: {str(e)}")
    
    async def list_swot_analyses(self, user_id: str, limit: int = 100, offset: int = 0) -> List[SWOTAnalysis]:
        """List SWOT analyses for a specific user"""
        try:
            analyses = []
            
            if self.cosmos_db_available and self.analyses_container:
                try:
                    # Query Cosmos DB
                    query = f"SELECT * FROM c WHERE c.user_id = '{user_id}' ORDER BY c.created_at DESC OFFSET {offset} LIMIT {limit}"
                    items = list(self.analyses_container.query_items(
                        query=query,
                        partition_key=user_id
                    ))
                    
                    # Convert to Pydantic models
                    analyses = [SWOTAnalysis.parse_obj(item) for item in items]
                    
                    # Update cache
                    for analysis in analyses:
                        self.analyses_cache[analysis.id] = analysis.dict()
                except Exception as e:
                    self.logger.error(f"Error querying SWOT analyses from Cosmos DB: {str(e)}")
                    # Fallback to in-memory filtering
                    analyses = self._filter_analyses_in_memory(user_id, limit, offset)
            else:
                # In-memory filtering
                analyses = self._filter_analyses_in_memory(user_id, limit, offset)
            
            return analyses
        except Exception as e:
            self.logger.error(f"Error listing SWOT analyses: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to list SWOT analyses: {str(e)}")
    
    def _filter_analyses_in_memory(self, user_id: str, limit: int, offset: int) -> List[SWOTAnalysis]:
        """Filter analyses from in-memory cache by user_id with pagination"""
        filtered_analyses = []
        for analysis_data in self.analyses_cache.values():
            analysis = SWOTAnalysis.parse_obj(analysis_data)
            if analysis.user_id == user_id:
                filtered_analyses.append(analysis)
        
        # Sort by created_at (descending)
        filtered_analyses.sort(key=lambda x: x.created_at, reverse=True)
        
        # Apply pagination
        return filtered_analyses[offset:offset+limit]
    
    # ----------- SWOT Item Operations -----------
    
    async def add_swot_item(self, analysis_id: str, item: SWOTItem) -> SWOTAnalysis:
        """Add a SWOT item to an existing analysis"""
        try:
            analysis = await self.get_swot_analysis(analysis_id)
            if not analysis:
                raise ValueError(f"Analysis with ID {analysis_id} not found")
            
            if not item.id:
                item.id = str(uuid.uuid4())
            
            # Find the appropriate category and add the item
            if item.category == SWOTCategory.STRENGTH:
                analysis.strengths.append(item)
            elif item.category == SWOTCategory.WEAKNESS:
                analysis.weaknesses.append(item)
            elif item.category == SWOTCategory.OPPORTUNITY:
                analysis.opportunities.append(item)
            elif item.category == SWOTCategory.THREAT:
                analysis.threats.append(item)
            else:
                raise ValueError(f"Invalid SWOT category: {item.category}")
            
            # Update the analysis
            return await self.update_swot_analysis(analysis)
        except Exception as e:
            self.logger.error(f"Error adding SWOT item: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to add SWOT item: {str(e)}")
    
    async def update_swot_item(self, analysis_id: str, item: SWOTItem) -> SWOTAnalysis:
        """Update a SWOT item in an existing analysis"""
        try:
            analysis = await self.get_swot_analysis(analysis_id)
            if not analysis:
                raise ValueError(f"Analysis with ID {analysis_id} not found")
            
            # Find and update the item in the appropriate category
            if item.category == SWOTCategory.STRENGTH:
                for i, strength in enumerate(analysis.strengths):
                    if strength.id == item.id:
                        analysis.strengths[i] = item
                        break
            elif item.category == SWOTCategory.WEAKNESS:
                for i, weakness in enumerate(analysis.weaknesses):
                    if weakness.id == item.id:
                        analysis.weaknesses[i] = item
                        break
            elif item.category == SWOTCategory.OPPORTUNITY:
                for i, opportunity in enumerate(analysis.opportunities):
                    if opportunity.id == item.id:
                        analysis.opportunities[i] = item
                        break
            elif item.category == SWOTCategory.THREAT:
                for i, threat in enumerate(analysis.threats):
                    if threat.id == item.id:
                        analysis.threats[i] = item
                        break
            else:
                raise ValueError(f"Invalid SWOT category: {item.category}")
            
            # Update the analysis
            return await self.update_swot_analysis(analysis)
        except Exception as e:
            self.logger.error(f"Error updating SWOT item: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to update SWOT item: {str(e)}")
    
    async def delete_swot_item(self, analysis_id: str, item_id: str, category: SWOTCategory) -> SWOTAnalysis:
        """Delete a SWOT item from an existing analysis"""
        try:
            analysis = await self.get_swot_analysis(analysis_id)
            if not analysis:
                raise ValueError(f"Analysis with ID {analysis_id} not found")
            
            # Find and remove the item from the appropriate category
            if category == SWOTCategory.STRENGTH:
                analysis.strengths = [s for s in analysis.strengths if s.id != item_id]
            elif category == SWOTCategory.WEAKNESS:
                analysis.weaknesses = [w for w in analysis.weaknesses if w.id != item_id]
            elif category == SWOTCategory.OPPORTUNITY:
                analysis.opportunities = [o for o in analysis.opportunities if o.id != item_id]
            elif category == SWOTCategory.THREAT:
                analysis.threats = [t for t in analysis.threats if t.id != item_id]
            else:
                raise ValueError(f"Invalid SWOT category: {category}")
            
            # Update the analysis
            return await self.update_swot_analysis(analysis)
        except Exception as e:
            self.logger.error(f"Error deleting SWOT item: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to delete SWOT item: {str(e)}")
    
    # ----------- TOWS Strategy Operations -----------
    
    async def add_tows_strategy(self, analysis_id: str, strategy: TOWSStrategy) -> SWOTAnalysis:
        """Add a TOWS strategy to an existing analysis"""
        try:
            analysis = await self.get_swot_analysis(analysis_id)
            if not analysis:
                raise ValueError(f"Analysis with ID {analysis_id} not found")
            
            if not strategy.id:
                strategy.id = str(uuid.uuid4())
            
            # Add the strategy
            analysis.tows_strategies.append(strategy)
            
            # Update the analysis
            return await self.update_swot_analysis(analysis)
        except Exception as e:
            self.logger.error(f"Error adding TOWS strategy: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to add TOWS strategy: {str(e)}")
    
    async def update_tows_strategy(self, analysis_id: str, strategy: TOWSStrategy) -> SWOTAnalysis:
        """Update a TOWS strategy in an existing analysis"""
        try:
            analysis = await self.get_swot_analysis(analysis_id)
            if not analysis:
                raise ValueError(f"Analysis with ID {analysis_id} not found")
            
            # Find and update the strategy
            for i, s in enumerate(analysis.tows_strategies):
                if s.id == strategy.id:
                    analysis.tows_strategies[i] = strategy
                    break
            
            # Update the analysis
            return await self.update_swot_analysis(analysis)
        except Exception as e:
            self.logger.error(f"Error updating TOWS strategy: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to update TOWS strategy: {str(e)}")
    
    async def delete_tows_strategy(self, analysis_id: str, strategy_id: str) -> SWOTAnalysis:
        """Delete a TOWS strategy from an existing analysis"""
        try:
            analysis = await self.get_swot_analysis(analysis_id)
            if not analysis:
                raise ValueError(f"Analysis with ID {analysis_id} not found")
            
            # Remove the strategy
            analysis.tows_strategies = [s for s in analysis.tows_strategies if s.id != strategy_id]
            
            # Update the analysis
            return await self.update_swot_analysis(analysis)
        except Exception as e:
            self.logger.error(f"Error deleting TOWS strategy: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to delete TOWS strategy: {str(e)}")
    
    # ----------- Insight Operations -----------
    
    async def create_insight(self, analysis_id: str, insight: Insight) -> SWOTAnalysis:
        """Add an insight to an existing analysis"""
        try:
            analysis = await self.get_swot_analysis(analysis_id)
            if not analysis:
                raise ValueError(f"Analysis with ID {analysis_id} not found")
            
            if not insight.id:
                insight.id = str(uuid.uuid4())
            
            # Add the insight
            analysis.insights.append(insight)
            
            # Update the analysis
            return await self.update_swot_analysis(analysis)
        except Exception as e:
            self.logger.error(f"Error creating insight: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to create insight: {str(e)}")
    
    async def update_insight(self, analysis_id: str, insight: Insight) -> SWOTAnalysis:
        """Update an insight in an existing analysis"""
        try:
            analysis = await self.get_swot_analysis(analysis_id)
            if not analysis:
                raise ValueError(f"Analysis with ID {analysis_id} not found")
            
            # Find and update the insight
            for i, ins in enumerate(analysis.insights):
                if ins.id == insight.id:
                    analysis.insights[i] = insight
                    break
            
            # Update the analysis
            return await self.update_swot_analysis(analysis)
        except Exception as e:
            self.logger.error(f"Error updating insight: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to update insight: {str(e)}")
    
    async def delete_insight(self, analysis_id: str, insight_id: str) -> SWOTAnalysis:
        """Delete an insight from an existing analysis"""
        try:
            analysis = await self.get_swot_analysis(analysis_id)
            if not analysis:
                raise ValueError(f"Analysis with ID {analysis_id} not found")
            
            # Remove the insight
            analysis.insights = [i for i in analysis.insights if i.id != insight_id]
            
            # Update the analysis
            return await self.update_swot_analysis(analysis)
        except Exception as e:
            self.logger.error(f"Error deleting insight: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to delete insight: {str(e)}")
    
    # ----------- Session Management -----------
    
    async def _get_session(self, session_id: str) -> Dict[str, Any]:
        """Retrieve a session from memory or database"""
        # Check in-memory cache first
        if session_id in self.active_sessions:
            return self.active_sessions[session_id]
        
        # Try to retrieve from database if not in memory
        if self.cosmos_db_available and self.sessions_container:
            try:
                query = f"SELECT * FROM c WHERE c.id = '{session_id}'"
                items = list(self.sessions_container.query_items(
                    query=query,
                    enable_cross_partition_query=True
                ))
                
                if items:
                    # Store in memory cache for future use
                    self.active_sessions[session_id] = items[0]
                    return items[0]
            except Exception as e:
                self.logger.error(f"Error retrieving session from Cosmos DB: {str(e)}")
        
        return None
    
    async def _save_session(self, session_id: str, session_data: Dict[str, Any]) -> bool:
        """Save a session to memory and database"""
        # Save to in-memory cache
        self.active_sessions[session_id] = session_data
        
        # Save to database if available
        if self.cosmos_db_available and self.sessions_container:
            try:
                try:
                    # Check if session already exists
                    self.sessions_container.replace_item(
                        item=session_id,
                        body=session_data
                    )
                except exceptions.CosmosResourceNotFoundError:
                    # Create new session if it doesn't exist
                    self.sessions_container.create_item(body=session_data)
                return True
            except Exception as e:
                self.logger.error(f"Error saving session to Cosmos DB: {str(e)}")
                return False
        
        return True
    
    # ----------- AI Integration -----------
    
    async def create_swot_session(self, user_id: str, company_name: str, topic: str, description: str = None) -> Dict[str, Any]:
        """Create a new SWOT analysis session"""
        try:
            session_id = str(uuid.uuid4())
            
            # Create basic analysis structure
            analysis = SWOTAnalysis(
                id=session_id,
                user_id=user_id,
                company_name=company_name,
                topic=topic,
                description=description or "",
                strengths=[],
                weaknesses=[],
                opportunities=[],
                threats=[],
                tows_strategies=[],
                insights=[],
                created_at=datetime.utcnow().isoformat()
            )
            
            # Create session data
            session_data = analysis.dict()
            session_data["session_id"] = session_id
            session_data["session_type"] = "swot_analysis"
            session_data["status"] = "active"
            session_data["guidance"] = {
                "current_step": "initial",
                "next_steps": [
                    "Add strengths",
                    "Add weaknesses",
                    "Add opportunities",
                    "Add threats",
                    "Review TOWS matrix",
                    "Generate insights"
                ],
                "completion": 0
            }
            
            # Save session to memory and database
            await self._save_session(session_id, session_data)
            
            # Use the skill to initialize the session
            variables = {
                "user_id": user_id,
                "company_name": company_name,
                "topic": topic,
                "description": description or ""
            }
            
            result = await kernel_service.invoke_semantic_function(
                "SWOTAnalysis", 
                "create_swot_session", 
                "", 
                variables
            )
            
            try:
                # Parse skill result and update guidance
                skill_result = json.loads(result)
                if isinstance(skill_result, dict) and "guidance" in skill_result:
                    session_data["guidance"] = skill_result["guidance"]
                    await self._save_session(session_id, session_data)
            except json.JSONDecodeError:
                self.logger.warning(f"Could not parse skill result as JSON: {result}")
            
            return session_data
        except Exception as e:
            self.logger.error(f"Error creating SWOT session: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to create SWOT session: {str(e)}")
    
    async def add_swot_point(self, session_id: str, category: SWOTCategory, text: str) -> Dict[str, Any]:
        """Add a point to a specific SWOT quadrant"""
        try:
            # Get session data
            session_data = await self._get_session(session_id)
            if not session_data:
                raise ValueError(f"Session {session_id} not found")
            
            # Create a new SWOT item
            item_id = str(uuid.uuid4())
            item = SWOTItem(
                id=item_id,
                category=category,
                text=text,
                created_at=datetime.utcnow().isoformat()
            )
            
            # Use the skill to add the point
            variables = {
                "session_id": session_id,
                "category": category.value,
                "text": text,
                "item_id": item_id
            }
            
            result = await kernel_service.invoke_semantic_function(
                "SWOTAnalysis", 
                "add_swot_point", 
                "", 
                variables
            )
            
            # Add to the session data
            category_map = {
                SWOTCategory.STRENGTH: "strengths",
                SWOTCategory.WEAKNESS: "weaknesses",
                SWOTCategory.OPPORTUNITY: "opportunities",
                SWOTCategory.THREAT: "threats"
            }
            
            category_key = category_map[category]
            if category_key not in session_data:
                session_data[category_key] = []
            
            session_data[category_key].append(item.dict())
            
            # Update guidance if skill provided it
            try:
                skill_result = json.loads(result)
                if isinstance(skill_result, dict) and "guidance" in skill_result:
                    session_data["guidance"] = skill_result["guidance"]
            except json.JSONDecodeError:
                self.logger.warning(f"Could not parse skill result as JSON: {result}")
            
            # Save updated session
            await self._save_session(session_id, session_data)
            
            # Prepare response
            response = {
                "session_id": session_id,
                "item": item.dict(),
                "category": category.value
            }
            
            if "guidance" in session_data:
                response["guidance"] = session_data["guidance"]
            
            return response
        except Exception as e:
            self.logger.error(f"Error adding SWOT point: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to add SWOT point: {str(e)}")
    
    async def add_tows_action(self, session_id: str, strategy_type: str, text: str) -> Dict[str, Any]:
        """Add an action to a specific TOWS cell"""
        try:
            # Get session data
            session_data = await self._get_session(session_id)
            if not session_data:
                raise ValueError(f"Session {session_id} not found")
            
            # Create a new TOWS strategy
            strategy_id = str(uuid.uuid4())
            strategy = TOWSStrategy(
                id=strategy_id,
                strategy_type=strategy_type,
                text=text,
                created_at=datetime.utcnow().isoformat()
            )
            
            # Use the skill to add the TOWS action
            variables = {
                "session_id": session_id,
                "strategy_type": strategy_type,
                "text": text,
                "strategy_id": strategy_id
            }
            
            result = await kernel_service.invoke_semantic_function(
                "SWOTAnalysis", 
                "add_tows_action", 
                "", 
                variables
            )
            
            # Add to the session data
            if "tows_strategies" not in session_data:
                session_data["tows_strategies"] = []
            
            session_data["tows_strategies"].append(strategy.dict())
            
            # Update guidance if skill provided it
            try:
                skill_result = json.loads(result)
                if isinstance(skill_result, dict) and "guidance" in skill_result:
                    session_data["guidance"] = skill_result["guidance"]
            except json.JSONDecodeError:
                self.logger.warning(f"Could not parse skill result as JSON: {result}")
            
            # Save updated session
            await self._save_session(session_id, session_data)
            
            # Prepare response
            response = {
                "session_id": session_id,
                "strategy": strategy.dict()
            }
            
            if "guidance" in session_data:
                response["guidance"] = session_data["guidance"]
            
            return response
        except Exception as e:
            self.logger.error(f"Error adding TOWS action: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to add TOWS action: {str(e)}")
    
    async def get_contextual_swot_prompts(self, session_id: str, category: SWOTCategory) -> Dict[str, Any]:
        """Get AI-generated contextual prompts for a SWOT quadrant"""
        try:
            # Get session data
            session_data = await self._get_session(session_id)
            if not session_data:
                raise ValueError(f"Session {session_id} not found")
            
            # Extract data needed for context
            company_name = session_data.get("company_name", "")
            topic = session_data.get("topic", "")
            
            # Extract current SWOT data
            strengths = session_data.get("strengths", [])
            weaknesses = session_data.get("weaknesses", [])
            opportunities = session_data.get("opportunities", [])
            threats = session_data.get("threats", [])
            
            # Get relevant contextual data
            context_variables = {
                "topic": topic,
                "company_name": company_name,
                "category": category.value,
                "strengths": strengths,
                "weaknesses": weaknesses,
                "opportunities": opportunities,
                "threats": threats
            }
            
            # Get subjective data related to the topic
            subjective_data = await kernel_service.invoke_semantic_function(
                "StrategicContext", 
                "fetch_relevant_subjective_notes", 
                topic, 
                {}
            )
            
            # Get objective data related to the topic
            objective_data = await kernel_service.invoke_semantic_function(
                "StrategicContext", 
                "fetch_relevant_objective_data", 
                topic, 
                {}
            )
            
            # Add context data
            context_variables["subjective_data"] = subjective_data
            context_variables["objective_data"] = objective_data
            
            # Generate contextual prompts
            result = await kernel_service.invoke_semantic_function(
                "ContextualPrompt", 
                "generate_swot_quadrant_prompt", 
                "", 
                context_variables
            )
            
            # Parse and return result
            try:
                guidance_data = json.loads(result)
                
                # Update session with latest guidance if provided
                if isinstance(guidance_data, dict) and "guidance" in guidance_data:
                    if "guidance" not in session_data:
                        session_data["guidance"] = {}
                    
                    session_data["guidance"].update({
                        "current_step": f"adding_{category.value}",
                        "completion": guidance_data["guidance"].get("completion", 0)
                    })
                    
                    await self._save_session(session_id, session_data)
                
                return guidance_data
            except json.JSONDecodeError:
                self.logger.error(f"Error parsing JSON response from ContextualPrompt skill: {result}")
                # Return a basic error response
                return {
                    "error": "Could not generate contextual prompts",
                    "category": category.value
                }
        except Exception as e:
            self.logger.error(f"Error getting contextual SWOT prompts: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to get contextual SWOT prompts: {str(e)}")
    
    async def get_contextual_tows_prompts(self, session_id: str, cell_type: str) -> Dict[str, Any]:
        """Get AI-generated contextual prompts for a TOWS cell"""
        try:
            # Get session data
            session_data = await self._get_session(session_id)
            if not session_data:
                raise ValueError(f"Session {session_id} not found")
            
            # Extract data needed for context
            company_name = session_data.get("company_name", "")
            topic = session_data.get("topic", "")
            
            # Extract current SWOT data
            strengths = session_data.get("strengths", [])
            weaknesses = session_data.get("weaknesses", [])
            opportunities = session_data.get("opportunities", [])
            threats = session_data.get("threats", [])
            
            # Extract current TOWS strategies
            strategies = session_data.get("tows_strategies", [])
            
            # Basic context variables
            context_variables = {
                "topic": topic,
                "company_name": company_name,
                "cell_type": cell_type,
                "strengths": strengths,
                "weaknesses": weaknesses,
                "opportunities": opportunities,
                "threats": threats,
                "strategies": strategies
            }
            
            # Generate contextual prompts for TOWS cell
            result = await kernel_service.invoke_semantic_function(
                "ContextualPrompt", 
                "generate_tows_cell_prompt", 
                "", 
                context_variables
            )
            
            # Parse and return result
            try:
                guidance_data = json.loads(result)
                
                # Update session with latest guidance if provided
                if isinstance(guidance_data, dict) and "guidance" in guidance_data:
                    if "guidance" not in session_data:
                        session_data["guidance"] = {}
                    
                    session_data["guidance"].update({
                        "current_step": f"adding_tows_{cell_type}",
                        "completion": guidance_data["guidance"].get("completion", 0)
                    })
                    
                    await self._save_session(session_id, session_data)
                
                return guidance_data
            except json.JSONDecodeError:
                self.logger.error(f"Error parsing JSON response from ContextualPrompt skill: {result}")
                # Return a basic error response
                return {
                    "error": "Could not generate contextual prompts",
                    "cell_type": cell_type
                }
        except Exception as e:
            self.logger.error(f"Error getting contextual TOWS prompts: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to get contextual TOWS prompts: {str(e)}")
    
    async def get_swot_data(self, session_id: str) -> Dict[str, Any]:
        """Get the current SWOT data for a session"""
        try:
            # Get session data
            session_data = await self._get_session(session_id)
            if not session_data:
                raise ValueError(f"Session {session_id} not found")
            
            # Use the skill to get the SWOT data
            variables = {
                "session_id": session_id
            }
            
            result = await kernel_service.invoke_semantic_function(
                "SWOTAnalysis", 
                "get_swot_data", 
                "", 
                variables
            )
            
            # Create response with actual session data
            swot_data = {
                "session_id": session_id,
                "strengths": session_data.get("strengths", []),
                "weaknesses": session_data.get("weaknesses", []),
                "opportunities": session_data.get("opportunities", []),
                "threats": session_data.get("threats", [])
            }
            
            # Add guidance from skill if available
            try:
                skill_result = json.loads(result)
                if isinstance(skill_result, dict) and "guidance" in skill_result:
                    swot_data["guidance"] = skill_result["guidance"]
                elif "guidance" in session_data:
                    swot_data["guidance"] = session_data["guidance"]
            except json.JSONDecodeError:
                self.logger.warning(f"Could not parse skill result as JSON: {result}")
                if "guidance" in session_data:
                    swot_data["guidance"] = session_data["guidance"]
            
            return swot_data
        except Exception as e:
            self.logger.error(f"Error getting SWOT data: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to get SWOT data: {str(e)}")
    
    async def get_tows_data(self, session_id: str) -> Dict[str, Any]:
        """Get the current TOWS data for a session"""
        try:
            # Get session data
            session_data = await self._get_session(session_id)
            if not session_data:
                raise ValueError(f"Session {session_id} not found")
            
            # Use the skill to get the TOWS data
            variables = {
                "session_id": session_id
            }
            
            result = await kernel_service.invoke_semantic_function(
                "SWOTAnalysis", 
                "get_tows_data", 
                "", 
                variables
            )
            
            # Create response with actual session data
            tows_data = {
                "session_id": session_id,
                "strategies": session_data.get("tows_strategies", [])
            }
            
            # Add guidance from skill if available
            try:
                skill_result = json.loads(result)
                if isinstance(skill_result, dict) and "guidance" in skill_result:
                    tows_data["guidance"] = skill_result["guidance"]
                elif "guidance" in session_data:
                    tows_data["guidance"] = session_data["guidance"]
            except json.JSONDecodeError:
                self.logger.warning(f"Could not parse skill result as JSON: {result}")
                if "guidance" in session_data:
                    tows_data["guidance"] = session_data["guidance"]
            
            return tows_data
        except Exception as e:
            self.logger.error(f"Error getting TOWS data: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to get TOWS data: {str(e)}")
    
    async def save_analysis(self, session_id: str) -> SWOTAnalysis:
        """Save the current session as a persistent SWOT analysis"""
        try:
            # Get session data
            session_data = await self._get_session(session_id)
            if not session_data:
                raise ValueError(f"Session {session_id} not found")
            
            # Use the skill to finalize the session
            variables = {
                "session_id": session_id
            }
            
            await kernel_service.invoke_semantic_function(
                "SWOTAnalysis", 
                "save_analysis", 
                "", 
                variables
            )
            
            # Convert session data to SWOTAnalysis
            analysis = SWOTAnalysis(
                id=session_id,
                user_id=session_data.get("user_id", ""),
                company_name=session_data.get("company_name", ""),
                topic=session_data.get("topic", ""),
                description=session_data.get("description", ""),
                strengths=[SWOTItem.parse_obj(s) for s in session_data.get("strengths", [])],
                weaknesses=[SWOTItem.parse_obj(s) for s in session_data.get("weaknesses", [])],
                opportunities=[SWOTItem.parse_obj(s) for s in session_data.get("opportunities", [])],
                threats=[SWOTItem.parse_obj(s) for s in session_data.get("threats", [])],
                tows_strategies=[TOWSStrategy.parse_obj(s) for s in session_data.get("tows_strategies", [])],
                insights=[Insight.parse_obj(s) for s in session_data.get("insights", [])],
                created_at=session_data.get("created_at", datetime.utcnow().isoformat()),
                updated_at=datetime.utcnow().isoformat()
            )
            
            # Save to database
            saved_analysis = await self.create_swot_analysis(analysis)
            
            # Update session status
            session_data["status"] = "completed"
            await self._save_session(session_id, session_data)
            
            return saved_analysis
        except Exception as e:
            self.logger.error(f"Error saving analysis: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to save analysis: {str(e)}")
    
    async def generate_insights(self, analysis_id: str) -> List[Insight]:
        """Generate insights based on SWOT and TOWS data"""
        try:
            analysis = await self.get_swot_analysis(analysis_id)
            if not analysis:
                raise ValueError(f"Analysis with ID {analysis_id} not found")
            
            # Prepare LLM prompt with the complete analysis data
            prompt = f"""
            I need to generate strategic insights based on the following SWOT analysis and TOWS matrix.
            
            Company: {analysis.company_name}
            Topic: {analysis.topic}
            
            STRENGTHS:
            {', '.join([s.text for s in analysis.strengths])}
            
            WEAKNESSES:
            {', '.join([w.text for w in analysis.weaknesses])}
            
            OPPORTUNITIES:
            {', '.join([o.text for o in analysis.opportunities])}
            
            THREATS:
            {', '.join([t.text for t in analysis.threats])}
            
            TOWS STRATEGIES:
            {', '.join([f"{s.strategy_type}: {s.text}" for s in analysis.tows_strategies])}
            
            Generate 3-5 high-level strategic insights based on this analysis. Each insight should:
            1. Identify a key pattern or theme across multiple elements
            2. Explain why this pattern matters to the company
            3. Suggest a strategic direction based on this pattern
            
            Format each insight as a JSON object with properties:
            - title: A short, descriptive title for the insight
            - description: A detailed explanation of the insight (3-5 sentences)
            - relevance: Why this insight matters to the company's future (2-3 sentences)
            - action_items: 2-3 specific actions the company could take based on this insight
            
            Return the insights as a JSON array.
            """
            
            # Generate completion from the LLM
            result = await kernel_service.generate_completion(prompt, max_tokens=1500)
            
            # Parse the response (handling potential JSON formatting issues)
            insights_data = []
            try:
                # Try to parse the entire response as JSON
                insights_data = json.loads(result)
            except json.JSONDecodeError:
                # If that fails, try to extract JSON from the text response
                self.logger.warning("Failed to parse LLM response as JSON, attempting extraction")
                try:
                    # Look for JSON array in the response
                    import re
                    json_str = re.search(r'\[\s*{.*}\s*\]', result, re.DOTALL)
                    if json_str:
                        insights_data = json.loads(json_str.group(0))
                    else:
                        # Try a more lenient approach
                        result = result.strip()
                        if result.startswith('[') and result.endswith(']'):
                            # Try to fix common JSON issues
                            fixed_json = self._fix_json_formatting(result)
                            insights_data = json.loads(fixed_json)
                        else:
                            raise ValueError("Could not extract JSON from LLM response")
                except Exception as e:
                    self.logger.error(f"Failed to parse insights from LLM response: {str(e)}")
                    raise HTTPException(status_code=500, detail="Failed to generate insights: Could not parse LLM response")
            
            # Convert to Insight objects
            insights = []
            for item in insights_data:
                insight = Insight(
                    id=str(uuid.uuid4()),
                    title=item.get("title", "Untitled Insight"),
                    description=item.get("description", ""),
                    relevance=item.get("relevance", ""),
                    action_items=item.get("action_items", []),
                    created_at=datetime.utcnow().isoformat()
                )
                insights.append(insight)
                
                # Add to the analysis
                analysis.insights.append(insight)
            
            # Update the analysis
            await self.update_swot_analysis(analysis)
            
            return insights
        except Exception as e:
            self.logger.error(f"Error generating insights: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to generate insights: {str(e)}")
    
    async def generate_tows_strategies(self, analysis_id: str) -> List[TOWSStrategy]:
        """Generate TOWS strategies based on SWOT data"""
        try:
            analysis = await self.get_swot_analysis(analysis_id)
            if not analysis:
                raise ValueError(f"Analysis with ID {analysis_id} not found")
            
            # Check if we have data in all SWOT quadrants
            if not (analysis.strengths and analysis.weaknesses and 
                    analysis.opportunities and analysis.threats):
                raise ValueError("All SWOT quadrants must have data to generate TOWS strategies")
            
            # Prepare LLM prompt with the SWOT data
            prompt = f"""
            I need to generate strategies for a TOWS matrix based on the following SWOT analysis.
            
            Company: {analysis.company_name}
            Topic: {analysis.topic}
            
            STRENGTHS:
            {', '.join([s.text for s in analysis.strengths])}
            
            WEAKNESSES:
            {', '.join([w.text for w in analysis.weaknesses])}
            
            OPPORTUNITIES:
            {', '.join([o.text for o in analysis.opportunities])}
            
            THREATS:
            {', '.join([t.text for t in analysis.threats])}
            
            Generate strategies for each of the four TOWS matrix cells:
            1. SO Strategies: Using strengths to capitalize on opportunities
            2. WO Strategies: Overcoming weaknesses by taking advantage of opportunities
            3. ST Strategies: Using strengths to mitigate threats
            4. WT Strategies: Minimizing weaknesses and avoiding threats
            
            Format each strategy as a JSON object with properties:
            - strategy_type: The cell type (SO, WO, ST, or WT)
            - text: A specific, actionable strategy statement (1-2 sentences)
            
            Return the strategies as a JSON array with 2-3 strategies per cell type.
            """
            
            # Generate completion from the LLM
            result = await kernel_service.generate_completion(prompt, max_tokens=1500)
            
            # Parse the response (handling potential JSON formatting issues)
            strategies_data = []
            try:
                # Try to parse the entire response as JSON
                strategies_data = json.loads(result)
            except json.JSONDecodeError:
                # If that fails, try to extract JSON from the text response
                self.logger.warning("Failed to parse LLM response as JSON, attempting extraction")
                try:
                    # Look for JSON array in the response
                    import re
                    json_str = re.search(r'\[\s*{.*}\s*\]', result, re.DOTALL)
                    if json_str:
                        strategies_data = json.loads(json_str.group(0))
                    else:
                        # Try a more lenient approach
                        result = result.strip()
                        if result.startswith('[') and result.endswith(']'):
                            # Try to fix common JSON issues
                            fixed_json = self._fix_json_formatting(result)
                            strategies_data = json.loads(fixed_json)
                        else:
                            raise ValueError("Could not extract JSON from LLM response")
                except Exception as e:
                    self.logger.error(f"Failed to parse strategies from LLM response: {str(e)}")
                    raise HTTPException(status_code=500, detail="Failed to generate strategies: Could not parse LLM response")
            
            # Convert to TOWSStrategy objects
            strategies = []
            for item in strategies_data:
                strategy = TOWSStrategy(
                    id=str(uuid.uuid4()),
                    strategy_type=item.get("strategy_type", "Unknown"),
                    text=item.get("text", ""),
                    created_at=datetime.utcnow().isoformat()
                )
                strategies.append(strategy)
                
                # Add to the analysis
                analysis.tows_strategies.append(strategy)
            
            # Update the analysis
            await self.update_swot_analysis(analysis)
            
            return strategies
        except Exception as e:
            self.logger.error(f"Error generating TOWS strategies: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to generate TOWS strategies: {str(e)}")
    
    def _fix_json_formatting(self, json_str: str) -> str:
        """Fix common JSON formatting issues in LLM responses"""
        # Replace single quotes with double quotes
        json_str = json_str.replace("'", '"')
        
        # Fix missing commas between objects in array
        json_str = re.sub(r'}\s*{', '},{', json_str)
        
        # Fix trailing commas
        json_str = re.sub(r',\s*}', '}', json_str)
        json_str = re.sub(r',\s*\]', ']', json_str)
        
        # Fix missing quotes around property names
        json_str = re.sub(r'([{,])\s*([a-zA-Z0-9_]+)\s*:', r'\1"\2":', json_str)
        
        return json_str