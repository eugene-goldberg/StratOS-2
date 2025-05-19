import os
import logging
import json
from typing import List, Optional, Dict, Any
from uuid import UUID
import azure.cognitiveservices.speech as speechsdk
from azure.cosmos import CosmosClient, PartitionKey
from datetime import datetime

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
        self.setup_cosmos_db()
        self.setup_speech_service()
        
    def setup_logging(self):
        self.logger = logging.getLogger("subjective_input_service")
        self.logger.setLevel(logging.INFO)
        
    def setup_cosmos_db(self):
        """Initialize Azure Cosmos DB connection"""
        try:
            # Get connection info from environment variables
            cosmos_endpoint = os.getenv("AZURE_COSMOS_ENDPOINT")
            cosmos_key = os.getenv("AZURE_COSMOS_KEY")
            cosmos_database = os.getenv("AZURE_COSMOS_DATABASE")
            
            # Initialize Cosmos client
            self.cosmos_client = CosmosClient(cosmos_endpoint, cosmos_key)
            self.database = self.cosmos_client.get_database_client(cosmos_database)
            
            # Get or create containers
            self.log_container = self.database.get_container_client("log_entries")
            self.canvas_container = self.database.get_container_client("strategic_canvases")
            
            self.logger.info("Cosmos DB connection established successfully")
        except Exception as e:
            self.logger.error(f"Error setting up Cosmos DB: {str(e)}")
            # Using in-memory storage as fallback for development
            self.log_entries = []
            self.canvases = []
            self.logger.warning("Using in-memory storage as fallback")
    
    def setup_speech_service(self):
        """Initialize Azure Speech Service for voice-to-text"""
        try:
            # Get connection info from environment variables
            speech_key = os.getenv("AZURE_SPEECH_KEY")
            speech_region = os.getenv("AZURE_SPEECH_REGION")
            
            # Store config for later use
            self.speech_config = speechsdk.SpeechConfig(
                subscription=speech_key, 
                region=speech_region
            )
            self.speech_config.speech_recognition_language = "en-US"
            
            self.logger.info("Speech service configured successfully")
        except Exception as e:
            self.logger.error(f"Error setting up Speech service: {str(e)}")
            
    # CEO's Log Methods

    async def create_log_entry(self, entry_data: LogEntryCreate, user_id: UUID) -> LogEntry:
        """Create a new log entry"""
        try:
            # Convert basic tag strings to LogEntryTag objects
            tags = []
            for tag_name in entry_data.tags:
                tags.append(LogEntryTag(
                    name=tag_name,
                    type="custom"
                ))
            
            # Create new log entry
            entry = LogEntry(
                content=entry_data.content,
                entry_type=entry_data.entry_type,
                tags=tags,
                user_id=user_id
            )
            
            # Save to Cosmos DB
            if hasattr(self, 'log_container'):
                entry_dict = entry.dict()
                # Convert UUID to string for Cosmos
                entry_dict["id"] = str(entry.id)
                entry_dict["user_id"] = str(entry.user_id)
                for i, tag in enumerate(entry_dict["tags"]):
                    entry_dict["tags"][i]["id"] = str(tag["id"])
                    if tag["reference_id"]:
                        entry_dict["tags"][i]["reference_id"] = str(tag["reference_id"])
                
                await self.log_container.create_item(entry_dict)
            else:
                # Fallback to in-memory storage
                self.log_entries.append(entry)
                
            self.logger.info(f"Created log entry with ID: {entry.id}")
            return entry
        except Exception as e:
            self.logger.error(f"Error creating log entry: {str(e)}")
            raise
    
    async def create_log_entry_from_voice(self, text_content: str, user_id: UUID) -> LogEntry:
        """Create a log entry from transcribed voice"""
        try:
            # Create entry data
            entry_data = LogEntryCreate(
                content=text_content,
                entry_type=LogEntryType.OTHER
            )
            
            # Create the log entry
            entry = await self.create_log_entry(entry_data, user_id)
            
            return entry
        except Exception as e:
            self.logger.error(f"Error creating log entry from voice: {str(e)}")
            raise
    
    async def get_log_entry(self, entry_id: UUID) -> Optional[LogEntry]:
        """Get a log entry by ID"""
        try:
            if hasattr(self, 'log_container'):
                query = f"SELECT * FROM c WHERE c.id = '{str(entry_id)}'"
                items = list(self.log_container.query_items(
                    query=query,
                    enable_cross_partition_query=True
                ))
                
                if not items:
                    return None
                
                # Convert Cosmos DB item to LogEntry model
                entry_dict = items[0]
                # Convert string UUIDs back to UUID objects
                entry_dict["id"] = UUID(entry_dict["id"])
                entry_dict["user_id"] = UUID(entry_dict["user_id"])
                for i, tag in enumerate(entry_dict["tags"]):
                    entry_dict["tags"][i]["id"] = UUID(tag["id"])
                    if tag["reference_id"]:
                        entry_dict["tags"][i]["reference_id"] = UUID(tag["reference_id"])
                
                return LogEntry(**entry_dict)
            else:
                # Fallback to in-memory storage
                for entry in self.log_entries:
                    if entry.id == entry_id:
                        return entry
                return None
        except Exception as e:
            self.logger.error(f"Error getting log entry: {str(e)}")
            return None
    
    async def list_log_entries(
        self, 
        user_id: UUID, 
        limit: int = 20, 
        offset: int = 0,
        entry_type: Optional[str] = None,
        tag: Optional[str] = None
    ) -> List[LogEntry]:
        """List log entries with optional filtering"""
        try:
            if hasattr(self, 'log_container'):
                # Build query based on filters
                query = f"SELECT * FROM c WHERE c.user_id = '{str(user_id)}'"
                
                if entry_type:
                    query += f" AND c.entry_type = '{entry_type}'"
                
                if tag:
                    query += f" AND ARRAY_CONTAINS(c.tags, {{'name': '{tag}'}})"
                
                # Add sorting and pagination
                query += f" ORDER BY c.created_at DESC OFFSET {offset} LIMIT {limit}"
                
                items = list(self.log_container.query_items(
                    query=query,
                    enable_cross_partition_query=True
                ))
                
                # Convert Cosmos DB items to LogEntry models
                entries = []
                for item in items:
                    # Convert string UUIDs back to UUID objects
                    item["id"] = UUID(item["id"])
                    item["user_id"] = UUID(item["user_id"])
                    for i, tag in enumerate(item["tags"]):
                        item["tags"][i]["id"] = UUID(tag["id"])
                        if tag["reference_id"]:
                            item["tags"][i]["reference_id"] = UUID(tag["reference_id"])
                    
                    entries.append(LogEntry(**item))
                
                return entries
            else:
                # Fallback to in-memory storage
                filtered_entries = [e for e in self.log_entries if e.user_id == user_id]
                
                if entry_type:
                    filtered_entries = [e for e in filtered_entries if e.entry_type == entry_type]
                
                if tag:
                    filtered_entries = [e for e in filtered_entries if any(t.name == tag for t in e.tags)]
                
                # Sort by created_at descending
                filtered_entries.sort(key=lambda e: e.created_at, reverse=True)
                
                # Apply pagination
                paginated_entries = filtered_entries[offset:offset + limit]
                
                return paginated_entries
        except Exception as e:
            self.logger.error(f"Error listing log entries: {str(e)}")
            return []
    
    async def update_log_entry(self, entry_id: UUID, entry_data: LogEntryUpdate) -> Optional[LogEntry]:
        """Update a log entry"""
        try:
            # Get existing entry
            entry = await self.get_log_entry(entry_id)
            if not entry:
                return None
            
            # Update fields that are provided
            if entry_data.content is not None:
                entry.content = entry_data.content
            
            if entry_data.entry_type is not None:
                entry.entry_type = entry_data.entry_type
            
            if entry_data.tags is not None:
                # Convert tag strings to LogEntryTag objects
                tags = []
                for tag_name in entry_data.tags:
                    tags.append(LogEntryTag(
                        name=tag_name,
                        type="custom"
                    ))
                entry.tags = tags
            
            # Update timestamp
            entry.updated_at = datetime.now()
            
            # Save to database
            if hasattr(self, 'log_container'):
                entry_dict = entry.dict()
                # Convert UUID to string for Cosmos
                entry_dict["id"] = str(entry.id)
                entry_dict["user_id"] = str(entry.user_id)
                for i, tag in enumerate(entry_dict["tags"]):
                    entry_dict["tags"][i]["id"] = str(tag["id"])
                    if tag["reference_id"]:
                        entry_dict["tags"][i]["reference_id"] = str(tag["reference_id"])
                
                await self.log_container.replace_item(
                    item=str(entry_id),
                    body=entry_dict
                )
            else:
                # Fallback to in-memory storage
                for i, e in enumerate(self.log_entries):
                    if e.id == entry_id:
                        self.log_entries[i] = entry
                        break
            
            self.logger.info(f"Updated log entry with ID: {entry_id}")
            return entry
        except Exception as e:
            self.logger.error(f"Error updating log entry: {str(e)}")
            return None
    
    async def delete_log_entry(self, entry_id: UUID) -> bool:
        """Delete a log entry"""
        try:
            if hasattr(self, 'log_container'):
                await self.log_container.delete_item(
                    item=str(entry_id),
                    partition_key=str(entry_id)
                )
            else:
                # Fallback to in-memory storage
                self.log_entries = [e for e in self.log_entries if e.id != entry_id]
            
            self.logger.info(f"Deleted log entry with ID: {entry_id}")
            return True
        except Exception as e:
            self.logger.error(f"Error deleting log entry: {str(e)}")
            return False
    
    async def update_log_entry_ai_results(
        self, 
        entry_id: UUID, 
        ai_tags: List[str], 
        ai_summary: str, 
        ai_insights: List[str]
    ) -> bool:
        """Update a log entry with AI-generated results"""
        try:
            # Get existing entry
            entry = await self.get_log_entry(entry_id)
            if not entry:
                return False
            
            # Update AI fields
            entry.ai_generated_tags = ai_tags
            entry.ai_summary = ai_summary
            entry.ai_insights = ai_insights
            entry.updated_at = datetime.now()
            
            # Save to database
            if hasattr(self, 'log_container'):
                entry_dict = entry.dict()
                # Convert UUID to string for Cosmos
                entry_dict["id"] = str(entry.id)
                entry_dict["user_id"] = str(entry.user_id)
                for i, tag in enumerate(entry_dict["tags"]):
                    entry_dict["tags"][i]["id"] = str(tag["id"])
                    if tag["reference_id"]:
                        entry_dict["tags"][i]["reference_id"] = str(tag["reference_id"])
                
                await self.log_container.replace_item(
                    item=str(entry_id),
                    body=entry_dict
                )
            else:
                # Fallback to in-memory storage
                for i, e in enumerate(self.log_entries):
                    if e.id == entry_id:
                        self.log_entries[i] = entry
                        break
            
            self.logger.info(f"Updated log entry AI results for ID: {entry_id}")
            return True
        except Exception as e:
            self.logger.error(f"Error updating log entry AI results: {str(e)}")
            return False
    
    async def process_voice_to_text(self, audio_file) -> str:
        """Process audio file to text using Azure Speech Services"""
        try:
            # Create temporary file to store the audio
            temp_filename = f"temp_audio_{datetime.now().timestamp()}.wav"
            
            with open(temp_filename, "wb") as f:
                contents = await audio_file.read()
                f.write(contents)
            
            # Configure audio config
            audio_config = speechsdk.AudioConfig(filename=temp_filename)
            
            # Create speech recognizer
            speech_recognizer = speechsdk.SpeechRecognizer(
                speech_config=self.speech_config, 
                audio_config=audio_config
            )
            
            # Start recognition
            result = speech_recognizer.recognize_once_async().get()
            
            # Clean up temporary file
            os.remove(temp_filename)
            
            if result.reason == speechsdk.ResultReason.RecognizedSpeech:
                return result.text
            else:
                self.logger.warning(f"Speech recognition failed: {result.reason}")
                return ""
        except Exception as e:
            self.logger.error(f"Error processing voice to text: {str(e)}")
            return ""
    
    async def process_voice_note_stream(self, audio_stream) -> str:
        """Process streaming audio to text using Azure Speech Services"""
        try:
            # Configure audio stream config
            pull_stream = speechsdk.audio.PullAudioInputStream(
                pull_stream_callback=lambda size: audio_stream.read(size),
                stream_format=speechsdk.audio.AudioStreamFormat(
                    samples_per_second=16000,
                    bits_per_sample=16,
                    channels=1
                )
            )
            
            audio_config = speechsdk.audio.AudioConfig(stream=pull_stream)
            
            # Create speech recognizer
            speech_recognizer = speechsdk.SpeechRecognizer(
                speech_config=self.speech_config, 
                audio_config=audio_config
            )
            
            # Start recognition
            result = speech_recognizer.recognize_once_async().get()
            
            if result.reason == speechsdk.ResultReason.RecognizedSpeech:
                return result.text
            else:
                self.logger.warning(f"Speech recognition failed: {result.reason}")
                return ""
        except Exception as e:
            self.logger.error(f"Error processing voice stream to text: {str(e)}")
            return ""
    
    # Strategic Canvas Methods
    
    async def create_canvas(self, canvas_data: StrategicCanvasCreate, user_id: UUID) -> StrategicCanvas:
        """Create a new strategic canvas"""
        try:
            # Create new canvas
            canvas = StrategicCanvas(
                title=canvas_data.title,
                description=canvas_data.description,
                user_id=user_id
            )
            
            # Save to Cosmos DB
            if hasattr(self, 'canvas_container'):
                canvas_dict = canvas.dict()
                # Convert UUID to string for Cosmos
                canvas_dict["id"] = str(canvas.id)
                canvas_dict["user_id"] = str(canvas.user_id)
                
                await self.canvas_container.create_item(canvas_dict)
            else:
                # Fallback to in-memory storage
                self.canvases.append(canvas)
                
            self.logger.info(f"Created strategic canvas with ID: {canvas.id}")
            return canvas
        except Exception as e:
            self.logger.error(f"Error creating strategic canvas: {str(e)}")
            raise
    
    async def get_canvas(self, canvas_id: UUID) -> Optional[StrategicCanvas]:
        """Get a strategic canvas by ID"""
        try:
            if hasattr(self, 'canvas_container'):
                query = f"SELECT * FROM c WHERE c.id = '{str(canvas_id)}'"
                items = list(self.canvas_container.query_items(
                    query=query,
                    enable_cross_partition_query=True
                ))
                
                if not items:
                    return None
                
                # Convert Cosmos DB item to StrategicCanvas model
                canvas_dict = items[0]
                # Convert string UUIDs back to UUID objects
                canvas_dict["id"] = UUID(canvas_dict["id"])
                canvas_dict["user_id"] = UUID(canvas_dict["user_id"])
                
                # Convert element UUIDs
                for i, element in enumerate(canvas_dict["elements"]):
                    canvas_dict["elements"][i]["id"] = UUID(element["id"])
                    canvas_dict["elements"][i]["connections"] = [UUID(c) for c in element["connections"]]
                
                return StrategicCanvas(**canvas_dict)
            else:
                # Fallback to in-memory storage
                for canvas in self.canvases:
                    if canvas.id == canvas_id:
                        return canvas
                return None
        except Exception as e:
            self.logger.error(f"Error getting strategic canvas: {str(e)}")
            return None
    
    async def list_canvases(self, user_id: UUID, limit: int = 10, offset: int = 0) -> List[StrategicCanvas]:
        """List strategic canvases"""
        try:
            if hasattr(self, 'canvas_container'):
                query = f"SELECT * FROM c WHERE c.user_id = '{str(user_id)}' ORDER BY c.created_at DESC OFFSET {offset} LIMIT {limit}"
                items = list(self.canvas_container.query_items(
                    query=query,
                    enable_cross_partition_query=True
                ))
                
                # Convert Cosmos DB items to StrategicCanvas models
                canvases = []
                for item in items:
                    # Convert string UUIDs back to UUID objects
                    item["id"] = UUID(item["id"])
                    item["user_id"] = UUID(item["user_id"])
                    
                    # Convert element UUIDs
                    for i, element in enumerate(item["elements"]):
                        item["elements"][i]["id"] = UUID(element["id"])
                        item["elements"][i]["connections"] = [UUID(c) for c in element["connections"]]
                    
                    canvases.append(StrategicCanvas(**item))
                
                return canvases
            else:
                # Fallback to in-memory storage
                filtered_canvases = [c for c in self.canvases if c.user_id == user_id]
                
                # Sort by created_at descending
                filtered_canvases.sort(key=lambda c: c.created_at, reverse=True)
                
                # Apply pagination
                paginated_canvases = filtered_canvases[offset:offset + limit]
                
                return paginated_canvases
        except Exception as e:
            self.logger.error(f"Error listing strategic canvases: {str(e)}")
            return []
    
    async def add_canvas_element(self, canvas_id: UUID, element_data: CanvasElementCreate) -> CanvasElement:
        """Add an element to a strategic canvas"""
        try:
            # Get the canvas
            canvas = await self.get_canvas(canvas_id)
            if not canvas:
                raise ValueError(f"Canvas with ID {canvas_id} not found")
            
            # Create the new element
            element = CanvasElement(
                element_type=element_data.element_type,
                content=element_data.content,
                position=element_data.position,
                style=element_data.style,
                connections=[UUID(c) for c in element_data.connections]
            )
            
            # Add to canvas
            canvas.elements.append(element)
            canvas.updated_at = datetime.now()
            
            # Save to database
            if hasattr(self, 'canvas_container'):
                canvas_dict = canvas.dict()
                # Convert UUID to string for Cosmos
                canvas_dict["id"] = str(canvas.id)
                canvas_dict["user_id"] = str(canvas.user_id)
                
                # Convert element UUIDs to strings
                for i, element in enumerate(canvas_dict["elements"]):
                    canvas_dict["elements"][i]["id"] = str(element["id"])
                    canvas_dict["elements"][i]["connections"] = [str(c) for c in element["connections"]]
                
                await self.canvas_container.replace_item(
                    item=str(canvas_id),
                    body=canvas_dict
                )
            else:
                # Fallback to in-memory storage
                for i, c in enumerate(self.canvases):
                    if c.id == canvas_id:
                        self.canvases[i] = canvas
                        break
            
            self.logger.info(f"Added element to canvas {canvas_id}: {element.id}")
            return element
        except Exception as e:
            self.logger.error(f"Error adding canvas element: {str(e)}")
            raise
    
    async def update_canvas_element(self, canvas_id: UUID, element_id: UUID, element_data: dict) -> Optional[CanvasElement]:
        """Update a canvas element"""
        try:
            # Get the canvas
            canvas = await self.get_canvas(canvas_id)
            if not canvas:
                return None
            
            # Find the element
            element_index = None
            for i, element in enumerate(canvas.elements):
                if element.id == element_id:
                    element_index = i
                    break
            
            if element_index is None:
                return None
            
            # Update the element
            for key, value in element_data.items():
                if key == 'connections' and value:
                    # Convert connection strings to UUIDs
                    canvas.elements[element_index].connections = [UUID(c) for c in value]
                elif key in ['content', 'position', 'style'] and value:
                    setattr(canvas.elements[element_index], key, value)
                elif key == 'element_type' and value:
                    canvas.elements[element_index].element_type = value
            
            # Update timestamp
            canvas.elements[element_index].updated_at = datetime.now()
            canvas.updated_at = datetime.now()
            
            # Save to database
            if hasattr(self, 'canvas_container'):
                canvas_dict = canvas.dict()
                # Convert UUID to string for Cosmos
                canvas_dict["id"] = str(canvas.id)
                canvas_dict["user_id"] = str(canvas.user_id)
                
                # Convert element UUIDs to strings
                for i, element in enumerate(canvas_dict["elements"]):
                    canvas_dict["elements"][i]["id"] = str(element["id"])
                    canvas_dict["elements"][i]["connections"] = [str(c) for c in element["connections"]]
                
                await self.canvas_container.replace_item(
                    item=str(canvas_id),
                    body=canvas_dict
                )
            else:
                # Fallback to in-memory storage
                for i, c in enumerate(self.canvases):
                    if c.id == canvas_id:
                        self.canvases[i] = canvas
                        break
            
            self.logger.info(f"Updated element {element_id} in canvas {canvas_id}")
            return canvas.elements[element_index]
        except Exception as e:
            self.logger.error(f"Error updating canvas element: {str(e)}")
            return None
    
    async def delete_canvas_element(self, canvas_id: UUID, element_id: UUID) -> bool:
        """Delete a canvas element"""
        try:
            # Get the canvas
            canvas = await self.get_canvas(canvas_id)
            if not canvas:
                return False
            
            # Find and remove the element
            canvas.elements = [e for e in canvas.elements if e.id != element_id]
            canvas.updated_at = datetime.now()
            
            # Update connections to this element in other elements
            for element in canvas.elements:
                if element_id in element.connections:
                    element.connections.remove(element_id)
            
            # Save to database
            if hasattr(self, 'canvas_container'):
                canvas_dict = canvas.dict()
                # Convert UUID to string for Cosmos
                canvas_dict["id"] = str(canvas.id)
                canvas_dict["user_id"] = str(canvas.user_id)
                
                # Convert element UUIDs to strings
                for i, element in enumerate(canvas_dict["elements"]):
                    canvas_dict["elements"][i]["id"] = str(element["id"])
                    canvas_dict["elements"][i]["connections"] = [str(c) for c in element["connections"]]
                
                await self.canvas_container.replace_item(
                    item=str(canvas_id),
                    body=canvas_dict
                )
            else:
                # Fallback to in-memory storage
                for i, c in enumerate(self.canvases):
                    if c.id == canvas_id:
                        self.canvases[i] = canvas
                        break
            
            self.logger.info(f"Deleted element {element_id} from canvas {canvas_id}")
            return True
        except Exception as e:
            self.logger.error(f"Error deleting canvas element: {str(e)}")
            return False
    
    async def get_canvas_ai_assistance(self, canvas_id: UUID, prompt: str) -> str:
        """Get AI assistance for a strategic canvas"""
        try:
            # Get the canvas
            canvas = await self.get_canvas(canvas_id)
            if not canvas:
                raise ValueError(f"Canvas with ID {canvas_id} not found")
            
            # Prepare canvas data for the AI
            canvas_data = {
                "title": canvas.title,
                "description": canvas.description,
                "elements": []
            }
            
            for element in canvas.elements:
                element_data = {
                    "id": str(element.id),
                    "type": element.element_type,
                    "content": element.content,
                    "connections": [str(c) for c in element.connections]
                }
                canvas_data["elements"].append(element_data)
            
            # Create the context for the AI
            context = {
                "canvas": json.dumps(canvas_data),
                "prompt": prompt
            }
            
            # Generate response using Semantic Kernel
            response = await kernel_service.invoke_semantic_function(
                skill_name="CanvasAssistant",
                function_name="ProvideAssistance",
                input_text="",
                variables=context
            )
            
            return response
        except Exception as e:
            self.logger.error(f"Error getting canvas AI assistance: {str(e)}")
            return f"I'm sorry, I couldn't provide assistance at this time. Error: {str(e)}"