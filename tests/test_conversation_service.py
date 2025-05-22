import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4, UUID
from datetime import datetime
from typing import List, Optional

from backend.services.conversation_service import ConversationService, conversation_service
from backend.models.conversation import (
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
from fastapi import HTTPException


@pytest_asyncio.fixture
async def service():
    """Create a conversation service instance for testing."""
    service = ConversationService()
    # Force in-memory mode for testing
    service.cosmos_db_available = False
    service.conversations_cache = {}
    service.messages_cache = {}
    return service


@pytest_asyncio.fixture
def user_id():
    """Generate a test user ID."""
    return uuid4()


@pytest_asyncio.fixture
def conversation_data():
    """Create test conversation data."""
    return ConversationCreate(
        title="Test Strategic Discussion",
        conversation_type=ConversationType.STRATEGIC_PLANNING,
        description="Testing conversation creation",
        initial_context={"priority": "high"}
    )


@pytest_asyncio.fixture
def message_data():
    """Create test message data."""
    return ConversationMessageCreate(
        content="This is a test message for strategic planning",
        role=MessageRole.USER,
        metadata={"intent": "question"}
    )


class TestConversationServiceInitialization:
    """Test conversation service initialization."""
    
    def test_service_initialization(self):
        """Test service initializes correctly."""
        service = ConversationService()
        assert hasattr(service, 'logger')
        assert hasattr(service, 'conversations_cache')
        assert hasattr(service, 'messages_cache')
        assert isinstance(service.conversations_cache, dict)
        assert isinstance(service.messages_cache, dict)
    
    def test_cosmos_db_fallback_warning(self):
        """Test warning logged when Cosmos DB unavailable."""
        with patch('backend.services.conversation_service.logging.getLogger') as mock_logger:
            mock_logger_instance = MagicMock()
            mock_logger.return_value = mock_logger_instance
            
            service = ConversationService()
            service.cosmos_db_available = False
            
            # The warning should be logged during initialization
            mock_logger_instance.warning.assert_called()


class TestConversationCRUDOperations:
    """Test conversation CRUD operations."""
    
    @pytest.mark.asyncio
    async def test_create_conversation(self, service: ConversationService, user_id: UUID, conversation_data: ConversationCreate):
        """Test conversation creation."""
        conversation = await service.create_conversation(conversation_data, user_id)
        
        assert isinstance(conversation, Conversation)
        assert conversation.user_id == user_id
        assert conversation.title == conversation_data.title
        assert conversation.conversation_type == conversation_data.conversation_type
        assert conversation.description == conversation_data.description
        assert conversation.context == conversation_data.initial_context
        assert conversation.status == ConversationStatus.ACTIVE
        assert conversation.message_count == 0
        
        # Check it's cached
        assert str(user_id) in service.conversations_cache
        assert str(conversation.id) in service.conversations_cache[str(user_id)]
    
    @pytest.mark.asyncio
    async def test_get_conversation_from_cache(self, service: ConversationService, user_id: UUID, conversation_data: ConversationCreate):
        """Test getting conversation from cache."""
        # Create conversation first
        conversation = await service.create_conversation(conversation_data, user_id)
        
        # Get conversation from cache
        retrieved = await service.get_conversation(conversation.id, user_id)
        
        assert retrieved is not None
        assert retrieved.id == conversation.id
        assert retrieved.title == conversation.title
        assert retrieved.user_id == user_id
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_conversation(self, service: ConversationService, user_id: UUID):
        """Test getting conversation that doesn't exist."""
        nonexistent_id = uuid4()
        result = await service.get_conversation(nonexistent_id, user_id)
        assert result is None
    
    @pytest.mark.asyncio
    async def test_list_conversations_empty(self, service: ConversationService, user_id: UUID):
        """Test listing conversations when none exist."""
        conversations = await service.list_conversations(user_id)
        assert conversations == []
    
    @pytest.mark.asyncio
    async def test_list_conversations_with_data(self, service: ConversationService, user_id: UUID):
        """Test listing conversations with multiple conversations."""
        # Create multiple conversations
        conv1_data = ConversationCreate(title="Conv 1", conversation_type=ConversationType.GENERAL)
        conv2_data = ConversationCreate(title="Conv 2", conversation_type=ConversationType.ANALYSIS_SUPPORT)
        
        conv1 = await service.create_conversation(conv1_data, user_id)
        conv2 = await service.create_conversation(conv2_data, user_id)
        
        # List all conversations
        conversations = await service.list_conversations(user_id)
        
        assert len(conversations) == 2
        titles = [conv.title for conv in conversations]
        assert "Conv 1" in titles
        assert "Conv 2" in titles
    
    @pytest.mark.asyncio
    async def test_list_conversations_with_type_filter(self, service: ConversationService, user_id: UUID):
        """Test listing conversations with type filtering."""
        # Create conversations of different types
        general_data = ConversationCreate(title="General", conversation_type=ConversationType.GENERAL)
        planning_data = ConversationCreate(title="Planning", conversation_type=ConversationType.STRATEGIC_PLANNING)
        
        await service.create_conversation(general_data, user_id)
        await service.create_conversation(planning_data, user_id)
        
        # Filter by type
        planning_conversations = await service.list_conversations(
            user_id, conversation_type=ConversationType.STRATEGIC_PLANNING
        )
        
        assert len(planning_conversations) == 1
        assert planning_conversations[0].title == "Planning"
        assert planning_conversations[0].conversation_type == ConversationType.STRATEGIC_PLANNING
    
    @pytest.mark.asyncio
    async def test_list_conversations_pagination(self, service: ConversationService, user_id: UUID):
        """Test conversation listing with pagination."""
        # Create multiple conversations
        for i in range(5):
            conv_data = ConversationCreate(title=f"Conv {i}")
            await service.create_conversation(conv_data, user_id)
        
        # Test pagination
        page1 = await service.list_conversations(user_id, limit=2, offset=0)
        page2 = await service.list_conversations(user_id, limit=2, offset=2)
        
        assert len(page1) == 2
        assert len(page2) == 2
        
        # Ensure different conversations
        page1_ids = [conv.id for conv in page1]
        page2_ids = [conv.id for conv in page2]
        assert not set(page1_ids).intersection(set(page2_ids))
    
    @pytest.mark.asyncio
    async def test_update_conversation(self, service: ConversationService, user_id: UUID, conversation_data: ConversationCreate):
        """Test conversation update."""
        conversation = await service.create_conversation(conversation_data, user_id)
        
        update_data = ConversationUpdate(
            title="Updated Title",
            description="Updated description",
            status=ConversationStatus.ARCHIVED,
            context={"updated": True}
        )
        
        updated = await service.update_conversation(conversation.id, user_id, update_data)
        
        assert updated is not None
        assert updated.title == "Updated Title"
        assert updated.description == "Updated description"
        assert updated.status == ConversationStatus.ARCHIVED
        assert updated.context["updated"] is True
        assert updated.context["priority"] == "high"  # Original context preserved
        assert updated.updated_at >= conversation.updated_at
    
    @pytest.mark.asyncio
    async def test_update_nonexistent_conversation(self, service: ConversationService, user_id: UUID):
        """Test updating conversation that doesn't exist."""
        nonexistent_id = uuid4()
        update_data = ConversationUpdate(title="Updated")
        
        result = await service.update_conversation(nonexistent_id, user_id, update_data)
        assert result is None
    
    @pytest.mark.asyncio
    async def test_delete_conversation(self, service: ConversationService, user_id: UUID, conversation_data: ConversationCreate):
        """Test conversation deletion."""
        conversation = await service.create_conversation(conversation_data, user_id)
        
        # Add a message to test cascade deletion
        message_data = ConversationMessageCreate(content="Test message")
        await service.add_message(conversation.id, message_data, user_id)
        
        # Delete conversation
        deleted = await service.delete_conversation(conversation.id, user_id)
        assert deleted is True
        
        # Verify conversation is gone
        result = await service.get_conversation(conversation.id, user_id)
        assert result is None
        
        # Verify messages are gone
        messages = await service.get_messages(conversation.id, user_id)
        assert messages == []
    
    @pytest.mark.asyncio
    async def test_delete_nonexistent_conversation(self, service: ConversationService, user_id: UUID):
        """Test deleting conversation that doesn't exist."""
        nonexistent_id = uuid4()
        result = await service.delete_conversation(nonexistent_id, user_id)
        assert result is False


class TestMessageOperations:
    """Test message operations."""
    
    @pytest.mark.asyncio
    async def test_add_message(self, service: ConversationService, user_id: UUID, conversation_data: ConversationCreate, message_data: ConversationMessageCreate):
        """Test adding message to conversation."""
        conversation = await service.create_conversation(conversation_data, user_id)
        
        message = await service.add_message(conversation.id, message_data, user_id)
        
        assert isinstance(message, ConversationMessage)
        assert message.conversation_id == conversation.id
        assert message.role == message_data.role
        assert message.content == message_data.content
        assert message.metadata == message_data.metadata
        assert isinstance(message.timestamp, datetime)
        
        # Check conversation statistics updated
        updated_conversation = await service.get_conversation(conversation.id, user_id)
        assert updated_conversation.message_count == 1
        assert updated_conversation.last_message_at == message.timestamp
    
    @pytest.mark.asyncio
    async def test_add_message_to_nonexistent_conversation(self, service: ConversationService, user_id: UUID, message_data: ConversationMessageCreate):
        """Test adding message to conversation that doesn't exist."""
        nonexistent_id = uuid4()
        
        with pytest.raises(HTTPException) as exc_info:
            await service.add_message(nonexistent_id, message_data, user_id)
        
        assert exc_info.value.status_code == 404
        assert "Conversation not found" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_get_messages(self, service: ConversationService, user_id: UUID, conversation_data: ConversationCreate):
        """Test getting messages from conversation."""
        conversation = await service.create_conversation(conversation_data, user_id)
        
        # Add multiple messages
        messages_added = []
        for i in range(3):
            message_data = ConversationMessageCreate(
                content=f"Message {i}",
                role=MessageRole.USER if i % 2 == 0 else MessageRole.ASSISTANT
            )
            message = await service.add_message(conversation.id, message_data, user_id)
            messages_added.append(message)
        
        # Get messages
        messages = await service.get_messages(conversation.id, user_id)
        
        assert len(messages) == 3
        # Messages should be ordered by timestamp
        for i, message in enumerate(messages):
            assert message.content == f"Message {i}"
    
    @pytest.mark.asyncio
    async def test_get_messages_pagination(self, service: ConversationService, user_id: UUID, conversation_data: ConversationCreate):
        """Test getting messages with pagination."""
        conversation = await service.create_conversation(conversation_data, user_id)
        
        # Add multiple messages
        for i in range(5):
            message_data = ConversationMessageCreate(content=f"Message {i}")
            await service.add_message(conversation.id, message_data, user_id)
        
        # Test pagination
        page1 = await service.get_messages(conversation.id, user_id, limit=2, offset=0)
        page2 = await service.get_messages(conversation.id, user_id, limit=2, offset=2)
        
        assert len(page1) == 2
        assert len(page2) == 2
        assert page1[0].content == "Message 0"
        assert page1[1].content == "Message 1"
        assert page2[0].content == "Message 2"
        assert page2[1].content == "Message 3"
    
    @pytest.mark.asyncio
    async def test_get_messages_from_nonexistent_conversation(self, service: ConversationService, user_id: UUID):
        """Test getting messages from conversation that doesn't exist."""
        nonexistent_id = uuid4()
        messages = await service.get_messages(nonexistent_id, user_id)
        assert messages == []


class TestAIIntegration:
    """Test AI integration methods."""
    
    @pytest.mark.asyncio
    async def test_get_conversation_context(self, service: ConversationService, user_id: UUID, conversation_data: ConversationCreate):
        """Test getting conversation context for AI."""
        conversation = await service.create_conversation(conversation_data, user_id)
        
        # Add some messages
        for i in range(3):
            message_data = ConversationMessageCreate(content=f"Message {i}")
            await service.add_message(conversation.id, message_data, user_id)
        
        context = await service.get_conversation_context(conversation.id, user_id, include_messages=2)
        
        assert isinstance(context, ConversationContext)
        assert context.conversation_id == conversation.id
        assert context.user_id == user_id
        assert context.conversation_type == conversation.conversation_type
        assert len(context.recent_messages) == 2  # Limited by include_messages
        assert context.conversation_summary is None  # No summary yet
    
    @pytest.mark.asyncio
    async def test_get_context_nonexistent_conversation(self, service: ConversationService, user_id: UUID):
        """Test getting context for conversation that doesn't exist."""
        nonexistent_id = uuid4()
        context = await service.get_conversation_context(nonexistent_id, user_id)
        assert context is None
    
    @pytest.mark.asyncio
    async def test_update_conversation_summary(self, service: ConversationService, user_id: UUID, conversation_data: ConversationCreate):
        """Test updating conversation summary."""
        conversation = await service.create_conversation(conversation_data, user_id)
        
        new_summary = "This is a strategic planning discussion about market expansion"
        await service.update_conversation_summary(conversation.id, user_id, new_summary)
        
        updated_conversation = await service.get_conversation(conversation.id, user_id)
        assert updated_conversation.summary == new_summary
        assert updated_conversation.updated_at >= conversation.updated_at
    
    @pytest.mark.asyncio
    @patch('backend.services.conversation_service.kernel_service')
    async def test_generate_ai_response(self, mock_kernel_service, service: ConversationService, user_id: UUID, conversation_data: ConversationCreate):
        """Test generating AI response with conversation memory."""
        # Setup mock
        mock_kernel_service.invoke_semantic_function = AsyncMock(return_value="AI generated response based on conversation context")
        
        conversation = await service.create_conversation(conversation_data, user_id)
        
        # Add some conversation history
        message_data = ConversationMessageCreate(content="Previous message", role=MessageRole.USER)
        await service.add_message(conversation.id, message_data, user_id)
        
        user_message = "What should be our next strategic priority?"
        response = await service.generate_ai_response(conversation.id, user_message, user_id)
        
        assert response == "AI generated response based on conversation context"
        
        # Verify kernel service was called with correct parameters
        mock_kernel_service.invoke_semantic_function.assert_called_once()
        call_args = mock_kernel_service.invoke_semantic_function.call_args
        
        assert call_args[1]['skill_name'] == "conversation"
        assert call_args[1]['function_name'] == "GenerateResponse"
        assert call_args[1]['input_text'] == user_message
        assert 'variables' in call_args[1]
        
        variables = call_args[1]['variables']
        assert 'conversation_history' in variables
        assert 'user_message' in variables
        assert 'conversation_type' in variables
        assert variables['user_message'] == user_message
    
    @pytest.mark.asyncio
    async def test_generate_ai_response_nonexistent_conversation(self, service: ConversationService, user_id: UUID):
        """Test generating AI response for conversation that doesn't exist."""
        nonexistent_id = uuid4()
        
        with pytest.raises(HTTPException) as exc_info:
            await service.generate_ai_response(nonexistent_id, "Test message", user_id)
        
        assert exc_info.value.status_code == 404
        assert "Conversation not found" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    @patch('backend.services.conversation_service.kernel_service')
    async def test_generate_ai_response_error_handling(self, mock_kernel_service, service: ConversationService, user_id: UUID, conversation_data: ConversationCreate):
        """Test AI response generation error handling."""
        # Setup mock to raise exception
        mock_kernel_service.invoke_semantic_function = AsyncMock(side_effect=Exception("AI service error"))
        
        conversation = await service.create_conversation(conversation_data, user_id)
        
        response = await service.generate_ai_response(conversation.id, "Test message", user_id)
        
        assert "I apologize, but I'm having trouble generating a response right now" in response


class TestServiceSingleton:
    """Test service singleton behavior."""
    
    def test_conversation_service_singleton(self):
        """Test that conversation_service is a singleton instance."""
        from backend.services.conversation_service import conversation_service
        assert isinstance(conversation_service, ConversationService)


class TestErrorHandling:
    """Test error handling scenarios."""
    
    @pytest.mark.asyncio
    async def test_database_error_fallback(self, service: ConversationService, user_id: UUID):
        """Test that service falls back to in-memory when database errors occur."""
        # Force database unavailable
        service.cosmos_db_available = False
        
        conversation_data = ConversationCreate(title="Test Conversation")
        conversation = await service.create_conversation(conversation_data, user_id)
        
        # Should work with in-memory cache
        assert conversation.title == "Test Conversation"
        assert str(user_id) in service.conversations_cache
        assert str(conversation.id) in service.conversations_cache[str(user_id)]
    
    @pytest.mark.asyncio
    async def test_user_isolation(self, service: ConversationService):
        """Test that users can't access each other's conversations."""
        user1_id = uuid4()
        user2_id = uuid4()
        
        # Create conversation for user1
        conversation_data = ConversationCreate(title="User 1 Conversation")
        conversation = await service.create_conversation(conversation_data, user1_id)
        
        # User2 should not be able to access user1's conversation
        result = await service.get_conversation(conversation.id, user2_id)
        assert result is None