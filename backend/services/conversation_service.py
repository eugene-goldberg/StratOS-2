import os
import logging
import json
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
    ConversationContext
)
from ..ai.kernel_service import kernel_service

class ConversationService:
    def __init__(self):
        self.setup_logging()
        self._initialize_cosmos_db_sync()
        
        # In-memory fallback if Cosmos DB is not available
        if not self.cosmos_db_available:
            self.conversations_cache = {}  # user_id -> {conversation_id: Conversation}
            self.messages_cache = {}       # conversation_id -> [ConversationMessage]
            self.logger.warning("Using in-memory storage as fallback for ConversationService.")

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
        """Get enhanced conversation context for AI interactions."""
        conversation = await self.get_conversation(conversation_id, user_id)
        if not conversation:
            return None

        # Get recent messages
        recent_messages = await self.get_messages(conversation_id, user_id, limit=include_messages)

        # Create conversation context
        context = ConversationContext(
            conversation_id=conversation_id,
            user_id=user_id,
            conversation_type=conversation.conversation_type,
            recent_messages=recent_messages,
            conversation_summary=conversation.summary
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

# Create singleton instance
conversation_service = ConversationService()