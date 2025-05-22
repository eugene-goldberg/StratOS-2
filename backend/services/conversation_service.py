import os
import logging
import json
import asyncio
from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID
from datetime import datetime, timedelta
from azure.cosmos.aio import CosmosClient as AsyncCosmosClient, DatabaseProxy, ContainerProxy
from azure.cosmos import PartitionKey, exceptions as CosmosExceptions
from fastapi import HTTPException

from ..models.conversation import (
    Conversation,
    ConversationCreate,
    ConversationUpdate,
    ConversationMessage,
    ConversationMessageCreate,
    ConversationType,
    MessageRole,
    ConversationStatus,
    ConversationContext,
    AIResponseWithMemory
)
from ..ai.kernel_service import kernel_service

class ConversationService:
    def setup_logging(self):
        self.logger = logging.getLogger("conversation_service")

    def _initialize_cosmos_db_sync(self):
        """Initialize Azure Cosmos DB connection using async client."""
        self.cosmos_db_available = False
        self.cosmos_client: Optional[AsyncCosmosClient] = None
        self.database: Optional[DatabaseProxy] = None
        self.conversations_container: Optional[ContainerProxy] = None
        self.messages_container: Optional[ContainerProxy] = None

        cosmos_endpoint = os.getenv("AZURE_COSMOS_ENDPOINT")
        cosmos_key = os.getenv("AZURE_COSMOS_KEY")
        self.cosmos_database_name = os.getenv("AZURE_COSMOS_DATABASE", "stratosdb")
            
        if not cosmos_endpoint or not cosmos_key or not self.cosmos_database_name:
            self.logger.warning("Cosmos DB credentials or database name not found. ConversationService will use in-memory fallback.")
            return

        try:
            self.cosmos_client = AsyncCosmosClient(url=cosmos_endpoint, credential=cosmos_key)
            self.database = self.cosmos_client.get_database_client(self.cosmos_database_name)
            
            # Get container proxies
            self.conversations_container = self.database.get_container_client("conversations")  # PK: /user_id
            self.messages_container = self.database.get_container_client("conversation_messages")  # PK: /conversation_id
            
            self.cosmos_db_available = True
            self.logger.info("Cosmos DB async client initialized for ConversationService.")
        except Exception as e:
            self.logger.error(f"Error setting up Cosmos DB for ConversationService: {str(e)}")
            self.cosmos_client = None
            self.database = None
            self.conversations_container = None
            self.messages_container = None

    async def _save_conversation_to_db(self, conversation: Conversation):
        """Save conversation to database with fallback to memory."""
        if not (self.cosmos_db_available and self.conversations_container):
            self.logger.warning(f"Cosmos DB not available for conversations. Caching conversation {conversation.id} in memory.")
            self.conversations_cache.setdefault(str(conversation.user_id), {})[str(conversation.id)] = conversation
            return

        conversation_dict = conversation.model_dump()
        conversation_dict["id"] = str(conversation.id)
        conversation_dict["user_id"] = str(conversation.user_id)

        try:
            await self.conversations_container.upsert_item(body=conversation_dict)
            self.logger.info(f"Saved conversation {conversation.id} for user {conversation.user_id} to Cosmos DB.")
            self.conversations_cache.setdefault(str(conversation.user_id), {})[str(conversation.id)] = conversation
        except CosmosExceptions.CosmosHttpResponseError as e:
            self.logger.error(f"Error saving conversation {conversation.id} to Cosmos DB: {str(e)}")
            self.conversations_cache.setdefault(str(conversation.user_id), {})[str(conversation.id)] = conversation

    async def _save_message_to_db(self, message: ConversationMessage):
        """Save message to database with fallback to memory."""
        if not (self.cosmos_db_available and self.messages_container):
            self.logger.warning(f"Cosmos DB not available for messages. Caching message {message.id} in memory.")
            if str(message.conversation_id) not in self.messages_cache:
                self.messages_cache[str(message.conversation_id)] = []
            self.messages_cache[str(message.conversation_id)].append(message)
            return

        message_dict = message.model_dump()
        message_dict["id"] = str(message.id)
        message_dict["conversation_id"] = str(message.conversation_id)

        try:
            await self.messages_container.upsert_item(body=message_dict)
            self.logger.info(f"Saved message {message.id} for conversation {message.conversation_id} to Cosmos DB.")
            if str(message.conversation_id) not in self.messages_cache:
                self.messages_cache[str(message.conversation_id)] = []
            self.messages_cache[str(message.conversation_id)].append(message)
        except CosmosExceptions.CosmosHttpResponseError as e:
            self.logger.error(f"Error saving message {message.id} to Cosmos DB: {str(e)}")
            if str(message.conversation_id) not in self.messages_cache:
                self.messages_cache[str(message.conversation_id)] = []
            self.messages_cache[str(message.conversation_id)].append(message)

    # Conversation CRUD operations
    async def create_conversation(self, conversation_data: ConversationCreate, user_id: UUID) -> Conversation:
        """Create a new conversation."""
        conversation = Conversation(
            user_id=user_id,
            title=conversation_data.title,
            description=conversation_data.description,
            conversation_type=conversation_data.conversation_type,
            context=conversation_data.initial_context or {}
        )
        
        await self._save_conversation_to_db(conversation)
        return conversation

    async def get_conversation(self, conversation_id: UUID, user_id: UUID) -> Optional[Conversation]:
        """Get a conversation by ID."""
        # Try cache first
        if str(user_id) in self.conversations_cache and str(conversation_id) in self.conversations_cache[str(user_id)]:
            return self.conversations_cache[str(user_id)][str(conversation_id)]

        if self.cosmos_db_available and self.conversations_container:
            try:
                item_data = await self.conversations_container.read_item(item=str(conversation_id), partition_key=str(user_id))
                item_data["id"] = UUID(item_data["id"])
                item_data["user_id"] = UUID(item_data["user_id"])
                
                conversation = Conversation(**item_data)
                self.conversations_cache.setdefault(str(user_id), {})[str(conversation_id)] = conversation
                return conversation
            except CosmosExceptions.CosmosResourceNotFoundError:
                return None
            except Exception as e:
                self.logger.error(f"Error getting conversation {conversation_id} for user {user_id}: {str(e)}")
                return None
        
        return None

    async def list_conversations(self, user_id: UUID, limit: int = 20, offset: int = 0, conversation_type: Optional[ConversationType] = None) -> List[Conversation]:
        """List conversations for a user."""
        if self.cosmos_db_available and self.conversations_container:
            query_parts = ["SELECT * FROM c WHERE c.user_id = @user_id"]
            parameters = [{"name": "@user_id", "value": str(user_id)}]
            
            if conversation_type:
                query_parts.append("AND c.conversation_type = @conversation_type")
                parameters.append({"name": "@conversation_type", "value": conversation_type.value})

            query = " ".join(query_parts) + f" ORDER BY c.updated_at DESC OFFSET {offset} LIMIT {limit}"
            
            conversations = []
            try:
                async for item_data in self.conversations_container.query_items(query=query, parameters=parameters, partition_key=str(user_id)):
                    item_data["id"] = UUID(item_data["id"])
                    item_data["user_id"] = UUID(item_data["user_id"])
                    conversations.append(Conversation(**item_data))
                return conversations
            except Exception as e:
                self.logger.error(f"Error listing conversations for user {user_id}: {str(e)}")
        
        # Fallback to in-memory cache
        user_conversations = self.conversations_cache.get(str(user_id), {}).values()
        filtered = []
        for conv in user_conversations:
            if conversation_type and conv.conversation_type != conversation_type:
                continue
            filtered.append(conv)
        
        filtered.sort(key=lambda c: c.updated_at, reverse=True)
        return filtered[offset:offset + limit]

    async def update_conversation(self, conversation_id: UUID, user_id: UUID, conversation_data: ConversationUpdate) -> Optional[Conversation]:
        """Update a conversation."""
        conversation = await self.get_conversation(conversation_id, user_id)
        if not conversation:
            return None

        if conversation_data.title is not None:
            conversation.title = conversation_data.title
        if conversation_data.description is not None:
            conversation.description = conversation_data.description
        if conversation_data.status is not None:
            conversation.status = conversation_data.status
        if conversation_data.context is not None:
            conversation.context.update(conversation_data.context)
        
        conversation.updated_at = datetime.now()
        await self._save_conversation_to_db(conversation)
        return conversation

    async def delete_conversation(self, conversation_id: UUID, user_id: UUID) -> bool:
        """Delete a conversation and all its messages."""
        conversation = await self.get_conversation(conversation_id, user_id)
        if not conversation:
            return False

        # Delete all messages first
        await self.delete_all_messages(conversation_id)

        # Delete conversation
        if self.cosmos_db_available and self.conversations_container:
            try:
                await self.conversations_container.delete_item(item=str(conversation_id), partition_key=str(user_id))
                self.logger.info(f"Deleted conversation {conversation_id} for user {user_id} from Cosmos DB.")
            except Exception as e:
                self.logger.error(f"Error deleting conversation {conversation_id}: {str(e)}")
                return False

        # Remove from cache
        if str(user_id) in self.conversations_cache and str(conversation_id) in self.conversations_cache[str(user_id)]:
            del self.conversations_cache[str(user_id)][str(conversation_id)]
        
        return True

    # Message operations
    async def add_message(self, conversation_id: UUID, message_data: ConversationMessageCreate, user_id: UUID) -> ConversationMessage:
        """Add a message to a conversation."""
        # Verify conversation exists and belongs to user
        conversation = await self.get_conversation(conversation_id, user_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        message = ConversationMessage(
            conversation_id=conversation_id,
            role=message_data.role,
            content=message_data.content,
            metadata=message_data.metadata or {}
        )

        await self._save_message_to_db(message)

        # Update conversation statistics
        conversation.message_count += 1
        conversation.last_message_at = message.timestamp
        conversation.updated_at = datetime.now()
        await self._save_conversation_to_db(conversation)

        return message

    async def get_messages(self, conversation_id: UUID, user_id: UUID, limit: int = 50, offset: int = 0) -> List[ConversationMessage]:
        """Get messages for a conversation."""
        # Verify conversation belongs to user
        conversation = await self.get_conversation(conversation_id, user_id)
        if not conversation:
            return []

        # Try cache first
        if str(conversation_id) in self.messages_cache:
            messages = self.messages_cache[str(conversation_id)]
            # Sort by timestamp and apply pagination
            messages.sort(key=lambda m: m.timestamp)
            return messages[offset:offset + limit]

        if self.cosmos_db_available and self.messages_container:
            query = "SELECT * FROM c WHERE c.conversation_id = @conversation_id ORDER BY c.timestamp ASC OFFSET @offset LIMIT @limit"
            parameters = [
                {"name": "@conversation_id", "value": str(conversation_id)},
                {"name": "@offset", "value": offset},
                {"name": "@limit", "value": limit}
            ]

            messages = []
            try:
                async for item_data in self.messages_container.query_items(query=query, parameters=parameters, partition_key=str(conversation_id)):
                    item_data["id"] = UUID(item_data["id"])
                    item_data["conversation_id"] = UUID(item_data["conversation_id"])
                    messages.append(ConversationMessage(**item_data))
                
                # Cache the messages
                if str(conversation_id) not in self.messages_cache:
                    self.messages_cache[str(conversation_id)] = []
                self.messages_cache[str(conversation_id)].extend(messages)
                
                return messages
            except Exception as e:
                self.logger.error(f"Error getting messages for conversation {conversation_id}: {str(e)}")

        return []

    async def delete_all_messages(self, conversation_id: UUID):
        """Delete all messages for a conversation."""
        if self.cosmos_db_available and self.messages_container:
            # This is a simplified deletion - in production, you might want batch operations
            query = "SELECT c.id FROM c WHERE c.conversation_id = @conversation_id"
            parameters = [{"name": "@conversation_id", "value": str(conversation_id)}]
            
            try:
                async for item in self.messages_container.query_items(query=query, parameters=parameters, partition_key=str(conversation_id)):
                    await self.messages_container.delete_item(item=item["id"], partition_key=str(conversation_id))
            except Exception as e:
                self.logger.error(f"Error deleting messages for conversation {conversation_id}: {str(e)}")

        # Clear cache
        if str(conversation_id) in self.messages_cache:
            del self.messages_cache[str(conversation_id)]

    # AI Integration methods
    async def get_conversation_context(self, conversation_id: UUID, user_id: UUID, include_messages: int = 10) -> Optional[ConversationContext]:
        """Get enhanced conversation context for AI interactions with deep memory."""
        conversation = await self.get_conversation(conversation_id, user_id)
        if not conversation:
            return None

        # Get recent messages
        recent_messages = await self.get_messages(conversation_id, user_id, limit=include_messages)

        # Enrich context with strategic data
        north_star_context = await self._get_north_star_context(user_id)
        recent_log_entries = await self._get_recent_log_entries(user_id, limit=5)
        active_analysis_sessions = await self._get_active_analysis_sessions(user_id)
        active_canvas_data = await self._get_active_canvas_data(user_id)
        
        # Get user conversation patterns and preferences
        user_preferences = await self._get_user_conversation_preferences(user_id)
        conversation_patterns = await self._analyze_conversation_patterns(user_id, conversation_id)

        # Create enriched conversation context
        context = ConversationContext(
            conversation_id=conversation_id,
            user_id=user_id,
            conversation_type=conversation.conversation_type,
            recent_messages=recent_messages,
            conversation_summary=conversation.summary,
            north_star_context=north_star_context,
            recent_log_entries=recent_log_entries,
            active_analysis_sessions=active_analysis_sessions,
            active_canvas_data=active_canvas_data,
            user_preferences=user_preferences,
            conversation_patterns=conversation_patterns
        )

        return context

    async def update_conversation_summary(self, conversation_id: UUID, user_id: UUID, new_summary: str):
        """Update conversation summary."""
        conversation = await self.get_conversation(conversation_id, user_id)
        if conversation:
            conversation.summary = new_summary
            conversation.updated_at = datetime.now()
            await self._save_conversation_to_db(conversation)

    async def generate_ai_response(self, conversation_id: UUID, user_message: str, user_id: UUID) -> str:
        """Generate AI response with conversation memory."""
        # Get conversation context
        context = await self.get_conversation_context(conversation_id, user_id)
        if not context:
            raise HTTPException(status_code=404, detail="Conversation not found")

        # Prepare context for AI
        conversation_history = []
        for msg in context.recent_messages:
            conversation_history.append(f"{msg.role}: {msg.content}")

        context_text = "\n".join(conversation_history[-10:])  # Last 10 messages
        
        # Generate AI response using kernel service
        try:
            ai_variables = {
                "conversation_history": context_text,
                "user_message": user_message,
                "conversation_type": context.conversation_type.value,
                "summary": context.conversation_summary or "No previous summary"
            }
            
            # Use a general conversation skill or the existing canvas skill
            response = await kernel_service.invoke_semantic_function(
                skill_name="conversation", 
                function_name="GenerateResponse", 
                input_text=user_message, 
                variables=ai_variables
            )
            return str(response)
        except Exception as e:
            self.logger.error(f"Error generating AI response: {str(e)}")
            return "I apologize, but I'm having trouble generating a response right now. Please try again."

    # Enhanced memory management methods
    async def _get_north_star_context(self, user_id: UUID) -> Optional[Dict[str, Any]]:
        """Get user's North Star context for conversation memory."""
        try:
            # Import here to avoid circular imports
            from .strategic_foundation_service import StrategicFoundationService
            foundation_service = StrategicFoundationService()
            
            north_star = await foundation_service.get_north_star(user_id)
            if north_star:
                return {
                    "purpose": north_star.purpose.statement if north_star.purpose else None,
                    "vision": north_star.vision.statement if north_star.vision else None,
                    "values": [{"name": v.name, "description": v.description} for v in north_star.values[:3]],
                    "goals": [{"title": g.title, "description": g.description} for g in north_star.strategic_goals[:5]]
                }
        except Exception as e:
            self.logger.warning(f"Could not retrieve North Star context for user {user_id}: {e}")
        return None

    async def _get_recent_log_entries(self, user_id: UUID, limit: int = 5) -> List[Dict[str, Any]]:
        """Get recent CEO log entries for conversation context."""
        try:
            from .subjective_input_service import SubjectiveInputService
            log_service = SubjectiveInputService()
            
            # Get recent entries (this would need to be implemented in the service)
            # For now, return empty list as a placeholder
            return []
        except Exception as e:
            self.logger.warning(f"Could not retrieve recent log entries for user {user_id}: {e}")
            return []

    async def _get_active_analysis_sessions(self, user_id: UUID) -> List[Dict[str, Any]]:
        """Get active analysis sessions for conversation context."""
        try:
            from .analysis_service import AnalysisService
            analysis_service = AnalysisService()
            
            # This would need analysis session tracking - placeholder for now
            return []
        except Exception as e:
            self.logger.warning(f"Could not retrieve analysis sessions for user {user_id}: {e}")
            return []

    async def _get_active_canvas_data(self, user_id: UUID) -> Optional[Dict[str, Any]]:
        """Get active canvas data for conversation context."""
        try:
            # This would integrate with canvas service when available
            return None
        except Exception as e:
            self.logger.warning(f"Could not retrieve canvas data for user {user_id}: {e}")
            return None

    async def _get_user_conversation_preferences(self, user_id: UUID) -> Dict[str, Any]:
        """Get user conversation preferences and patterns."""
        try:
            # Check if preferences exist in context cache
            cache_key = f"preferences_{user_id}"
            if cache_key in self.context_cache:
                return self.context_cache[cache_key]
            
            # Default preferences - could be enhanced with actual user preference tracking
            preferences = {
                "communication_style": "collaborative",
                "detail_level": "moderate",
                "focus_areas": ["strategic_planning", "decision_making"],
                "preferred_frameworks": ["SWOT", "strategic_canvas"],
                "feedback_frequency": "regular"
            }
            
            # Cache for future use
            self.context_cache[cache_key] = preferences
            return preferences
            
        except Exception as e:
            self.logger.warning(f"Could not retrieve preferences for user {user_id}: {e}")
            return {}

    async def _analyze_conversation_patterns(self, user_id: UUID, conversation_id: UUID) -> Dict[str, Any]:
        """Analyze conversation patterns to improve AI responses."""
        try:
            # Get conversation history to analyze patterns
            messages = await self.get_messages(conversation_id, user_id, limit=50)
            
            if not messages:
                return {}
            
            # Analyze patterns
            user_messages = [m for m in messages if m.role == MessageRole.USER]
            assistant_messages = [m for m in messages if m.role == MessageRole.ASSISTANT]
            
            patterns = {
                "message_count": len(messages),
                "user_message_count": len(user_messages),
                "assistant_message_count": len(assistant_messages),
                "avg_user_message_length": sum(len(m.content) for m in user_messages) / len(user_messages) if user_messages else 0,
                "conversation_topics": self._extract_conversation_topics(messages),
                "question_frequency": sum(1 for m in user_messages if '?' in m.content) / len(user_messages) if user_messages else 0,
                "last_interaction": messages[-1].timestamp.isoformat() if messages else None
            }
            
            return patterns
            
        except Exception as e:
            self.logger.warning(f"Could not analyze conversation patterns for user {user_id}: {e}")
            return {}

    def _extract_conversation_topics(self, messages: List[ConversationMessage]) -> List[str]:
        """Extract key topics from conversation messages."""
        topics = []
        strategic_keywords = {
            "swot": "SWOT Analysis",
            "goal": "Strategic Goals", 
            "objective": "Strategic Goals",
            "canvas": "Strategic Canvas",
            "planning": "Strategic Planning",
            "decision": "Decision Making",
            "analysis": "Analysis",
            "risk": "Risk Management",
            "opportunity": "Opportunity Analysis",
            "vision": "Vision & Purpose",
            "values": "Values & Culture"
        }
        
        content_text = " ".join([m.content.lower() for m in messages[-10:]])  # Last 10 messages
        
        for keyword, topic in strategic_keywords.items():
            if keyword in content_text and topic not in topics:
                topics.append(topic)
        
        return topics[:5]  # Return top 5 topics

    async def generate_ai_response_with_memory(self, conversation_id: UUID, user_message: str, user_id: UUID) -> AIResponseWithMemory:
        """Generate AI response with enhanced memory and context updates."""
        # Get enriched conversation context
        context = await self.get_conversation_context(conversation_id, user_id)
        if not context:
            raise HTTPException(status_code=404, detail="Conversation not found")

        # Build comprehensive context for AI
        context_prompt = self._build_ai_context_prompt(context, user_message)
        
        # Generate AI response using enhanced context
        try:
            ai_variables = {
                "conversation_history": context_prompt,
                "user_message": user_message,
                "conversation_type": context.conversation_type.value,
                "north_star_context": json.dumps(context.north_star_context) if context.north_star_context else "{}",
                "user_preferences": json.dumps(context.user_preferences),
                "conversation_patterns": json.dumps(context.conversation_patterns)
            }
            
            response_content = await kernel_service.invoke_semantic_function(
                skill_name="conversation", 
                function_name="GenerateResponse", 
                input_text=user_message, 
                variables=ai_variables
            )
            
            # Determine if conversation summary should be updated
            should_update_summary = await self._should_update_summary(context)
            new_summary = None
            if should_update_summary:
                new_summary = await self._generate_conversation_summary(context, user_message, response_content)
            
            # Prepare context updates
            context_updates = await self._prepare_context_updates(context, user_message, response_content)
            
            return AIResponseWithMemory(
                response_content=str(response_content),
                conversation_id=conversation_id,
                should_update_summary=should_update_summary,
                new_summary=new_summary,
                context_updates=context_updates,
                related_entities=self._extract_related_entities(user_message, response_content)
            )
            
        except Exception as e:
            self.logger.error(f"Error generating AI response with memory: {str(e)}")
            return AIResponseWithMemory(
                response_content="I apologize, but I'm having trouble generating a response right now. Please try again.",
                conversation_id=conversation_id
            )

    def _build_ai_context_prompt(self, context: ConversationContext, user_message: str) -> str:
        """Build comprehensive context prompt for AI."""
        prompt_parts = []
        
        # Add conversation history
        if context.recent_messages:
            prompt_parts.append("CONVERSATION HISTORY:")
            for msg in context.recent_messages[-8:]:  # Last 8 messages
                prompt_parts.append(f"{msg.role}: {msg.content}")
        
        # Add strategic context
        if context.north_star_context:
            prompt_parts.append("\nSTRATEGIC CONTEXT:")
            if context.north_star_context.get("purpose"):
                prompt_parts.append(f"Purpose: {context.north_star_context['purpose']}")
            if context.north_star_context.get("vision"):
                prompt_parts.append(f"Vision: {context.north_star_context['vision']}")
            if context.north_star_context.get("goals"):
                goals = [g["title"] for g in context.north_star_context["goals"][:3]]
                prompt_parts.append(f"Key Goals: {', '.join(goals)}")
        
        # Add conversation patterns
        if context.conversation_patterns:
            topics = context.conversation_patterns.get("conversation_topics", [])
            if topics:
                prompt_parts.append(f"\nDISCUSSION TOPICS: {', '.join(topics)}")
        
        # Add user preferences
        if context.user_preferences:
            style = context.user_preferences.get("communication_style", "collaborative")
            detail = context.user_preferences.get("detail_level", "moderate")
            prompt_parts.append(f"\nUSER PREFERENCES: {style} style, {detail} detail level")
        
        return "\n".join(prompt_parts)

    async def _should_update_summary(self, context: ConversationContext) -> bool:
        """Determine if conversation summary should be updated."""
        # Update summary every 10 messages or if no summary exists
        message_count = len(context.recent_messages)
        return message_count % 10 == 0 or not context.conversation_summary

    async def _generate_conversation_summary(self, context: ConversationContext, user_message: str, ai_response: str) -> str:
        """Generate updated conversation summary."""
        try:
            # Build context for summarization
            conversation_text = "\n".join([f"{m.role}: {m.content}" for m in context.recent_messages[-20:]])
            conversation_text += f"\nuser: {user_message}\nassistant: {ai_response}"
            
            summary_variables = {
                "conversation_history": conversation_text,
                "conversation_type": context.conversation_type.value,
                "previous_summary": context.conversation_summary or "No previous summary"
            }
            
            new_summary = await kernel_service.invoke_semantic_function(
                skill_name="conversation",
                function_name="SummarizeConversation",
                input_text=conversation_text,
                variables=summary_variables
            )
            
            return str(new_summary)
            
        except Exception as e:
            self.logger.error(f"Error generating conversation summary: {e}")
            return context.conversation_summary or "Conversation about strategic planning and AI assistance."

    async def _prepare_context_updates(self, context: ConversationContext, user_message: str, ai_response: str) -> Dict[str, Any]:
        """Prepare context updates based on the conversation."""
        updates = {}
        
        # Update conversation patterns
        topics = self._extract_conversation_topics([
            ConversationMessage(conversation_id=context.conversation_id, role=MessageRole.USER, content=user_message),
            ConversationMessage(conversation_id=context.conversation_id, role=MessageRole.ASSISTANT, content=ai_response)
        ])
        
        if topics:
            updates["recent_topics"] = topics
        
        # Track user engagement patterns
        updates["last_interaction_type"] = "question" if "?" in user_message else "statement"
        updates["message_length"] = len(user_message)
        
        return updates

    def _extract_related_entities(self, user_message: str, ai_response: str) -> List[Dict[str, Any]]:
        """Extract related entities mentioned in the conversation."""
        entities = []
        
        # Look for strategic entities in the conversation
        entity_patterns = {
            "goal": ["goal", "objective", "target"],
            "initiative": ["initiative", "project", "action"],
            "risk": ["risk", "threat", "challenge"],
            "opportunity": ["opportunity", "chance", "potential"],
            "metric": ["metric", "kpi", "measure", "indicator"]
        }
        
        combined_text = f"{user_message} {ai_response}".lower()
        
        for entity_type, keywords in entity_patterns.items():
            for keyword in keywords:
                if keyword in combined_text:
                    entities.append({
                        "type": entity_type,
                        "keyword": keyword,
                        "context": "mentioned in conversation"
                    })
                    break  # Only add once per entity type
        
        return entities

    def __init__(self):
        """Initialize the Conversation Service with enhanced memory capabilities."""
        # Initialize base service properties
        self.cosmos_client = None
        self.database = None
        self.conversations_container = None
        self.messages_container = None
        self.cosmos_db_available = False
        
        # Caches for performance
        self.conversations_cache = {}
        self.messages_cache = {}
        self.context_cache = {}  # Enhanced context memory cache
        
        # Logger
        self.logger = logging.getLogger("conversation_service")
        
        # Initialize database connection (fallback to sync method for now)
        self._initialize_cosmos_db_sync()

# Create singleton instance
conversation_service = ConversationService()