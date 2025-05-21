import os
import logging
import json
import uuid
from typing import List, Optional, Dict, Any
from uuid import UUID
import azure.cognitiveservices.speech as speechsdk
from azure.cosmos.aio import CosmosClient as AsyncCosmosClient, DatabaseProxy, ContainerProxy
from azure.cosmos import PartitionKey, exceptions as CosmosExceptions
from datetime import datetime
from fastapi import HTTPException # For raising HTTP errors

from ..models.subjective_input import (
    LogEntry, 
    LogEntryCreate, 
    LogEntryUpdate, 
    LogEntryTag,
    LogEntryType,
    StrategicCanvas, 
    StrategicCanvasCreate, 
    CanvasElement,
    CanvasElementCreate
)
from ..ai.kernel_service import kernel_service

class SubjectiveInputService:
    def __init__(self):
        self.setup_logging()
        self._initialize_cosmos_db_sync() # Changed from setup_cosmos_db
        self.setup_speech_service()
        
        # In-memory fallback if Cosmos DB is not available
        if not self.cosmos_db_available:
            self.log_entries_cache = {} # user_id -> {entry_id: LogEntry}
            self.canvases_cache = {}    # user_id -> {canvas_id: StrategicCanvas}
            self.logger.warning("Using in-memory storage as fallback for SubjectiveInputService.")

    def setup_logging(self):
        self.logger = logging.getLogger("subjective_input_service")
        # self.logger.setLevel(logging.INFO) # Level setting is usually done globally

    def _initialize_cosmos_db_sync(self):
        """Initialize Azure Cosmos DB connection using async client."""
        self.cosmos_db_available = False
        self.cosmos_client: Optional[AsyncCosmosClient] = None
        self.database: Optional[DatabaseProxy] = None
        self.log_container: Optional[ContainerProxy] = None
        self.canvas_container: Optional[ContainerProxy] = None

        cosmos_endpoint = os.getenv("AZURE_COSMOS_ENDPOINT")
        cosmos_key = os.getenv("AZURE_COSMOS_KEY")
        self.cosmos_database_name = os.getenv("AZURE_COSMOS_DATABASE", "stratosdb") # Consistent DB name
            
        if not cosmos_endpoint or not cosmos_key or not self.cosmos_database_name:
            self.logger.warning("Cosmos DB credentials or database name not found. SubjectiveInputService will use in-memory fallback.")
            return

        try:
            self.cosmos_client = AsyncCosmosClient(url=cosmos_endpoint, credential=cosmos_key)
            self.database = self.cosmos_client.get_database_client(self.cosmos_database_name)
            
            # Get container proxies. Actual creation should be handled at app startup.
            self.log_container = self.database.get_container_client("log_entries") # PK: /user_id
            self.canvas_container = self.database.get_container_client("strategic_canvases") # PK: /user_id
            
            self.cosmos_db_available = True
            self.logger.info("Cosmos DB async client initialized for SubjectiveInputService.")
        except Exception as e:
            self.logger.error(f"Error setting up Cosmos DB for SubjectiveInputService: {str(e)}")
            # Ensure all clients are None if setup fails
            self.cosmos_client = None
            self.database = None
            self.log_container = None
            self.canvas_container = None
    
    def setup_speech_service(self):
        """Initialize Azure Speech Service for voice-to-text"""
        try:
            speech_key = os.getenv("AZURE_SPEECH_KEY")
            speech_region = os.getenv("AZURE_SPEECH_REGION")
            if not speech_key or not speech_region:
                self.logger.warning("Azure Speech Key or Region not configured.")
                self.speech_config = None
                return

            self.speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=speech_region)
            self.speech_config.speech_recognition_language = "en-US"
            self.logger.info("Speech service configured successfully.")
        except Exception as e:
            self.logger.error(f"Error setting up Speech service: {str(e)}")
            self.speech_config = None
            
    async def _save_log_entry_to_db(self, entry: LogEntry):
        if not (self.cosmos_db_available and self.log_container):
            self.logger.warning(f"Cosmos DB not available for log_entries. Caching log entry {entry.id} in memory.")
            self.log_entries_cache.setdefault(str(entry.user_id), {})[str(entry.id)] = entry
            return

        entry_dict = entry.dict()
        entry_dict["id"] = str(entry.id)
        entry_dict["user_id"] = str(entry.user_id) # Partition Key
        for i, tag_dict in enumerate(entry_dict.get("tags", [])):
            tag_dict["id"] = str(tag_dict["id"])
            if tag_dict.get("reference_id"):
                tag_dict["reference_id"] = str(tag_dict["reference_id"])
        
        try:
            # Using upsert_item for create/update simplicity on save
            await self.log_container.upsert_item(body=entry_dict)
            self.logger.info(f"Saved log entry {entry.id} for user {entry.user_id} to Cosmos DB.")
            self.log_entries_cache.setdefault(str(entry.user_id), {})[str(entry.id)] = entry
        except CosmosExceptions.CosmosHttpResponseError as e:
            self.logger.error(f"Error saving log entry {entry.id} to Cosmos DB: {str(e)}")
            self.log_entries_cache.setdefault(str(entry.user_id), {})[str(entry.id)] = entry


    async def _save_canvas_to_db(self, canvas: StrategicCanvas):
        if not (self.cosmos_db_available and self.canvas_container):
            self.logger.warning(f"Cosmos DB not available for canvases. Caching canvas {canvas.id} in memory.")
            self.canvases_cache.setdefault(str(canvas.user_id), {})[str(canvas.id)] = canvas
            return

        canvas_dict = canvas.dict()
        canvas_dict["id"] = str(canvas.id)
        canvas_dict["user_id"] = str(canvas.user_id) # Partition Key
        for i, el_dict in enumerate(canvas_dict.get("elements", [])):
            el_dict["id"] = str(el_dict["id"])
            el_dict["connections"] = [str(c) for c in el_dict.get("connections", [])]

        try:
            await self.canvas_container.upsert_item(body=canvas_dict)
            self.logger.info(f"Saved canvas {canvas.id} for user {canvas.user_id} to Cosmos DB.")
            self.canvases_cache.setdefault(str(canvas.user_id), {})[str(canvas.id)] = canvas
        except CosmosExceptions.CosmosHttpResponseError as e:
            self.logger.error(f"Error saving canvas {canvas.id} to Cosmos DB: {str(e)}")
            self.canvases_cache.setdefault(str(canvas.user_id), {})[str(canvas.id)] = canvas

    # CEO's Log Methods
    async def create_log_entry(self, entry_data: LogEntryCreate, user_id: UUID) -> LogEntry:
        tags = [LogEntryTag(name=tag_name, type="custom") for tag_name in entry_data.tags]
        entry = LogEntry(content=entry_data.content, entry_type=entry_data.entry_type, tags=tags, user_id=user_id)
        await self._save_log_entry_to_db(entry) # Changed to use helper
        return entry
    
    async def create_log_entry_from_voice(self, text_content: str, user_id: UUID) -> LogEntry:
        entry_data = LogEntryCreate(content=text_content, entry_type=LogEntryType.VOICE_NOTE) # Changed type
        return await self.create_log_entry(entry_data, user_id)
    
    async def get_log_entry(self, entry_id: UUID, user_id: Optional[UUID] = None) -> Optional[LogEntry]: # Added user_id for partitioned read
        # Try cache first (assuming cache is user-partitioned or checked)
        if user_id and str(user_id) in self.log_entries_cache and str(entry_id) in self.log_entries_cache[str(user_id)]:
            return self.log_entries_cache[str(user_id)][str(entry_id)]
        
        if self.cosmos_db_available and self.log_container:
            if not user_id: # If user_id not provided, cannot do efficient read
                 self.logger.warning("get_log_entry called without user_id for DB lookup, this will be inefficient or fail if PK is user_id.")
                 # Fallback to cross-partition query if absolutely necessary and PK is not /user_id
                 # query = f"SELECT * FROM c WHERE c.id = '{str(entry_id)}'"
                 # items = [item async for item in self.log_container.query_items(query=query, enable_cross_partition_query=True)]
                 # if not items: return None
                 # item_data = items[0]
                 # This path should be avoided. For now, require user_id for DB read.
                 return None # Or raise error

            try:
                item_data = await self.log_container.read_item(item=str(entry_id), partition_key=str(user_id))
                item_data["id"] = UUID(item_data["id"])
                item_data["user_id"] = UUID(item_data["user_id"])
                for tag_dict in item_data.get("tags", []):
                    tag_dict["id"] = UUID(tag_dict["id"])
                    if tag_dict.get("reference_id"): tag_dict["reference_id"] = UUID(tag_dict["reference_id"])
                entry = LogEntry(**item_data)
                self.log_entries_cache.setdefault(str(user_id), {})[str(entry_id)] = entry
                return entry
            except CosmosExceptions.CosmosResourceNotFoundError:
                return None
            except Exception as e:
                self.logger.error(f"Error getting log entry {entry_id} for user {user_id}: {str(e)}")
                return None
        
        # Fallback to non-user-partitioned cache scan if user_id was None
        if not user_id:
            for user_bucket in self.log_entries_cache.values():
                if str(entry_id) in user_bucket:
                    return user_bucket[str(entry_id)]
        return None

    async def list_log_entries(self, user_id: UUID, limit: int = 20, offset: int = 0, entry_type: Optional[str] = None, tag: Optional[str] = None) -> List[LogEntry]:
        if self.cosmos_db_available and self.log_container:
            query_parts = ["SELECT * FROM c WHERE c.user_id = @user_id"]
            parameters: List[Dict[str, Any]] = [{"name": "@user_id", "value": str(user_id)}]
            
            if entry_type:
                query_parts.append("AND c.entry_type = @entry_type")
                parameters.append({"name": "@entry_type", "value": entry_type})
            if tag: # ARRAY_CONTAINS for searching in an array of objects needs specific syntax
                query_parts.append("AND EXISTS (SELECT VALUE t FROM t IN c.tags WHERE t.name = @tag_name)")
                parameters.append({"name": "@tag_name", "value": tag})

            # Cosmos DB OFFSET LIMIT is not directly on query string but on query_items options for async SDK
            # The query itself should not contain OFFSET LIMIT for async SDK.
            # However, for simplicity and consistency with other services, keeping it in query string.
            # The proper way for async SDK is:
            # results_iterable = self.log_container.query_items(query=query, parameters=parameters, partition_key=str(user_id), max_item_count=limit)
            # items = await results_iterable.to_list() # This would fetch all then slice, or use continuation tokens.
            # For now, let's assume the OFFSET LIMIT in query string works as intended by the sync SDK behavior.
            query = " ".join(query_parts) + f" ORDER BY c.created_at DESC OFFSET {offset} LIMIT {limit}"
            
            entries = []
            try:
                async for item_data in self.log_container.query_items(query=query, parameters=parameters, partition_key=str(user_id)):
                    item_data["id"] = UUID(item_data["id"])
                    item_data["user_id"] = UUID(item_data["user_id"])
                    for t_dict in item_data.get("tags",[]): t_dict["id"] = UUID(t_dict["id"])
                    if t_dict.get("reference_id"): t_dict["reference_id"] = UUID(t_dict["reference_id"])
                    entries.append(LogEntry(**item_data))
                return entries
            except Exception as e:
                self.logger.error(f"Error listing log entries for user {user_id}: {str(e)}")
                # Fallback to cache
        
        # Fallback to in-memory cache
        user_logs = self.log_entries_cache.get(str(user_id), {}).values()
        filtered = []
        for e_obj in user_logs: # e_obj is LogEntry
            if entry_type and e_obj.entry_type.value != entry_type: continue
            if tag and not any(t.name == tag for t in e_obj.tags): continue
            filtered.append(e_obj)
        filtered.sort(key=lambda e_obj: e_obj.created_at, reverse=True)
        return filtered[offset : offset + limit]

    async def update_log_entry(self, entry_id: UUID, entry_data: LogEntryUpdate, user_id: UUID) -> Optional[LogEntry]: # Added user_id
        entry = await self.get_log_entry(entry_id, user_id) # Pass user_id for read
        if not entry: return None
        
        if entry_data.content is not None: entry.content = entry_data.content
        if entry_data.entry_type is not None: entry.entry_type = entry_data.entry_type
        if entry_data.tags is not None:
            entry.tags = [LogEntryTag(name=tag_name, type="custom") for tag_name in entry_data.tags]
        entry.updated_at = datetime.now()
        
        await self._save_log_entry_to_db(entry)
        return entry

    async def delete_log_entry(self, entry_id: UUID, user_id: UUID) -> bool: # Added user_id
        # Ensure entry exists and belongs to user before deleting from cache
        entry_to_delete = await self.get_log_entry(entry_id, user_id)
        if not entry_to_delete: # Handles not found or not owned by user
            return False

        if self.cosmos_db_available and self.log_container:
            try:
                await self.log_container.delete_item(item=str(entry_id), partition_key=str(user_id))
                self.logger.info(f"Deleted log entry {entry_id} for user {user_id} from Cosmos DB.")
                # Remove from cache after successful DB deletion
                if str(user_id) in self.log_entries_cache and str(entry_id) in self.log_entries_cache[str(user_id)]:
                    del self.log_entries_cache[str(user_id)][str(entry_id)]
                return True
            except CosmosExceptions.CosmosResourceNotFoundError: # Should be caught by get_log_entry if PK is correct
                self.logger.warning(f"Log entry {entry_id} for user {user_id} not found in DB for deletion.")
                return False
            except Exception as e:
                self.logger.error(f"Error deleting log entry {entry_id} for user {user_id}: {str(e)}")
                return False
        
        # Fallback to in-memory if DB not available but was found in cache by get_log_entry
        if str(user_id) in self.log_entries_cache and str(entry_id) in self.log_entries_cache[str(user_id)]:
            del self.log_entries_cache[str(user_id)][str(entry_id)]
            self.logger.info(f"Deleted log entry {entry_id} for user {user_id} from memory.")
            return True
        return False # Should not happen if get_log_entry found it
    
    async def update_log_entry_ai_results(self, entry_id: UUID, user_id: UUID, ai_tags: List[str], ai_summary: str, ai_insights: List[str]) -> bool: # Added user_id
        entry = await self.get_log_entry(entry_id, user_id) # Pass user_id for read
        if not entry: return False
            
        entry.ai_generated_tags = ai_tags
        entry.ai_summary = ai_summary
        entry.ai_insights = ai_insights
        entry.updated_at = datetime.now()
        
        await self._save_log_entry_to_db(entry)
        return True
    
    async def process_voice_to_text(self, audio_file) -> str:
        if not self.speech_config:
            self.logger.error("Speech service not configured, cannot process voice to text.")
            return ""
        temp_filename = None
        try:
            temp_filename = f"temp_audio_{uuid.uuid4()}.wav" # Unique filename
            with open(temp_filename, "wb") as f:
                contents = await audio_file.read()
                f.write(contents)
            
            audio_config = speechsdk.AudioConfig(filename=temp_filename)
            speech_recognizer = speechsdk.SpeechRecognizer(speech_config=self.speech_config, audio_config=audio_config)
            result = await speech_recognizer.recognize_once_async() # Use await for async SDK method
            
            os.remove(temp_filename)
            
            if result.reason == speechsdk.ResultReason.RecognizedSpeech: return result.text
            self.logger.warning(f"Speech recognition failed: {result.reason}, Details: {result.no_match_details if result.reason == speechsdk.ResultReason.NoMatch else result.cancellation_details}")
            return ""
        except Exception as e:
            self.logger.error(f"Error processing voice to text: {str(e)}")
            if temp_filename and os.path.exists(temp_filename): os.remove(temp_filename) # Ensure cleanup on error
            return ""
    
    # Strategic Canvas Methods
    async def create_canvas(self, canvas_data: StrategicCanvasCreate, user_id: UUID) -> StrategicCanvas:
        canvas = StrategicCanvas(title=canvas_data.title, description=canvas_data.description, user_id=user_id)
        await self._save_canvas_to_db(canvas)
        return canvas
    
    async def get_canvas(self, canvas_id: UUID, user_id: Optional[UUID] = None) -> Optional[StrategicCanvas]: # Added user_id
        if user_id and str(user_id) in self.canvases_cache and str(canvas_id) in self.canvases_cache[str(user_id)]:
            return self.canvases_cache[str(user_id)][str(canvas_id)]

        if self.cosmos_db_available and self.canvas_container:
            if not user_id: # If user_id not provided, cannot do efficient read
                self.logger.warning("get_canvas called without user_id for DB lookup.")
                return None 
            try:
                item_data = await self.canvas_container.read_item(item=str(canvas_id), partition_key=str(user_id))
                item_data["id"] = UUID(item_data["id"])
                item_data["user_id"] = UUID(item_data["user_id"])
                for el_dict in item_data.get("elements", []):
                    el_dict["id"] = UUID(el_dict["id"])
                    el_dict["connections"] = [UUID(c) for c in el_dict.get("connections", [])]
                canvas = StrategicCanvas(**item_data)
                self.canvases_cache.setdefault(str(user_id), {})[str(canvas_id)] = canvas
                return canvas
            except CosmosExceptions.CosmosResourceNotFoundError:
                return None
            except Exception as e:
                self.logger.error(f"Error getting canvas {canvas_id} for user {user_id}: {str(e)}")
                return None
        
        if not user_id: # Fallback scan if no user_id provided
            for user_bucket in self.canvases_cache.values():
                if str(canvas_id) in user_bucket:
                    return user_bucket[str(canvas_id)]
        return None

    async def list_canvases(self, user_id: UUID, limit: int = 10, offset: int = 0) -> List[StrategicCanvas]:
        if self.cosmos_db_available and self.canvas_container:
            query = "SELECT * FROM c WHERE c.user_id = @user_id ORDER BY c.created_at DESC OFFSET @offset LIMIT @limit"
            parameters = [
                {"name": "@user_id", "value": str(user_id)},
                {"name": "@offset", "value": offset},
                {"name": "@limit", "value": limit}
            ]
            canvases = []
            try:
                async for item_data in self.canvas_container.query_items(query=query, parameters=parameters, partition_key=str(user_id)):
                    item_data["id"] = UUID(item_data["id"])
                    item_data["user_id"] = UUID(item_data["user_id"])
                    for el_dict in item_data.get("elements", []):
                        el_dict["id"] = UUID(el_dict["id"])
                        el_dict["connections"] = [UUID(c) for c in el_dict.get("connections", [])]
                    canvases.append(StrategicCanvas(**item_data))
                return canvases
            except Exception as e:
                self.logger.error(f"Error listing canvases for user {user_id}: {str(e)}")
        
        user_canvases = self.canvases_cache.get(str(user_id), {}).values()
        sorted_canvases = sorted(list(user_canvases), key=lambda c_obj: c_obj.created_at, reverse=True)
        return sorted_canvases[offset : offset + limit]

    async def add_canvas_element(self, canvas_id: UUID, user_id: UUID, element_data: CanvasElementCreate) -> CanvasElement: # Added user_id
        canvas = await self.get_canvas(canvas_id, user_id) # Pass user_id
        if not canvas: raise HTTPException(status_code=404, detail=f"Canvas with ID {canvas_id} not found for user.")
            
        element = CanvasElement(element_type=element_data.element_type, content=element_data.content, position=element_data.position, style=element_data.style, connections=[UUID(c) for c in element_data.connections])
        canvas.elements.append(element)
        canvas.updated_at = datetime.now()
        await self._save_canvas_to_db(canvas)
        return element
    
    async def update_canvas_element(self, canvas_id: UUID, user_id: UUID, element_id: UUID, element_data: dict) -> Optional[CanvasElement]: # Added user_id
        canvas = await self.get_canvas(canvas_id, user_id) # Pass user_id
        if not canvas: return None
            
        element_index = next((i for i, el in enumerate(canvas.elements) if el.id == element_id), -1)
        if element_index == -1: return None
            
        el_to_update = canvas.elements[element_index]
        # Use CanvasElementCreate for validation if possible, or update fields carefully
        if "element_type" in element_data: el_to_update.element_type = element_data["element_type"]
        if "content" in element_data: el_to_update.content = element_data["content"]
        if "position" in element_data: el_to_update.position = element_data["position"]
        if "style" in element_data: el_to_update.style = element_data["style"]
        if "connections" in element_data: el_to_update.connections = [UUID(c) for c in element_data["connections"]]
        el_to_update.updated_at = datetime.now()
        canvas.updated_at = datetime.now()
        
        await self._save_canvas_to_db(canvas)
        return el_to_update
    
    async def delete_canvas_element(self, canvas_id: UUID, user_id: UUID, element_id: UUID) -> bool: # Added user_id
        canvas = await self.get_canvas(canvas_id, user_id) # Pass user_id
        if not canvas: return False
            
        original_len = len(canvas.elements)
        canvas.elements = [el for el in canvas.elements if el.id != element_id]
        if len(canvas.elements) == original_len: return False # Not found
            
        for el in canvas.elements: # Remove connections to the deleted element
            if element_id in el.connections: el.connections.remove(element_id)
        canvas.updated_at = datetime.now()
        await self._save_canvas_to_db(canvas)
        return True
    
    async def get_canvas_ai_assistance(self, canvas_id: UUID, user_id: UUID, prompt: str) -> str: # Added user_id
        canvas = await self.get_canvas(canvas_id, user_id) # Pass user_id
        if not canvas: raise HTTPException(status_code=404, detail="Canvas not found for user.")
            
        canvas_data_for_ai = {"title": canvas.title, "description": canvas.description, "elements": []}
        for el in canvas.elements:
            canvas_data_for_ai["elements"].append({"id": str(el.id), "type": el.element_type, "content": el.content, "connections": [str(c) for c in el.connections]})
        
        context_vars = {"canvas": json.dumps(canvas_data_for_ai), "prompt": prompt, "user_id": str(user_id)}
        try:
            response = await kernel_service.invoke_semantic_function(skill_name="CanvasAssistant", function_name="ProvideAssistance", input_text="", variables=context_vars)
            return str(response.result if hasattr(response, 'result') else response)
        except Exception as e:
            self.logger.error(f"Error getting canvas AI assistance for user {user_id}, canvas {canvas_id}: {str(e)}")
            return f"AI assistance unavailable. Error: {str(e)}"

    # process_voice_note_stream method is removed as the router uses kernel_service directly for streaming.
