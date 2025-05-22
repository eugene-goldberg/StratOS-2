import pytest
from pydantic import ValidationError
from uuid import uuid4, UUID
from datetime import datetime
from typing import Dict, Any

from backend.models.conversation import (
    Conversation,
    ConversationCreate,
    ConversationUpdate,
    ConversationMessage,
    ConversationMessageCreate,
    ConversationType,
    MessageRole,
    ConversationStatus,
    ConversationContext,
    ConversationResponse,
    ConversationListResponse,
    ConversationMessageResponse,
    AIResponseWithMemory
)


class TestConversationEnums:
    """Test conversation enum types."""
    
    def test_conversation_type_enum(self):
        """Test ConversationType enum values."""
        assert ConversationType.GENERAL == "general"
        assert ConversationType.STRATEGIC_PLANNING == "strategic_planning"
        assert ConversationType.ANALYSIS_SUPPORT == "analysis_support"
        assert ConversationType.CANVAS_COLLABORATION == "canvas_collaboration"
        assert ConversationType.CEO_LOG_DISCUSSION == "ceo_log_discussion"
    
    def test_message_role_enum(self):
        """Test MessageRole enum values."""
        assert MessageRole.USER == "user"
        assert MessageRole.ASSISTANT == "assistant"
        assert MessageRole.SYSTEM == "system"
    
    def test_conversation_status_enum(self):
        """Test ConversationStatus enum values."""
        assert ConversationStatus.ACTIVE == "active"
        assert ConversationStatus.ARCHIVED == "archived"
        assert ConversationStatus.PAUSED == "paused"


class TestConversationCreateModel:
    """Test ConversationCreate model validation."""
    
    def test_valid_conversation_create(self):
        """Test valid conversation creation data."""
        data = ConversationCreate(
            title="Strategic Planning Session",
            conversation_type=ConversationType.STRATEGIC_PLANNING,
            description="Planning for Q4 expansion",
            initial_context={"priority": "high"}
        )
        
        assert data.title == "Strategic Planning Session"
        assert data.conversation_type == ConversationType.STRATEGIC_PLANNING
        assert data.description == "Planning for Q4 expansion"
        assert data.initial_context == {"priority": "high"}
    
    def test_minimal_conversation_create(self):
        """Test conversation creation with minimal required fields."""
        data = ConversationCreate(title="Test Conversation")
        
        assert data.title == "Test Conversation"
        assert data.conversation_type == ConversationType.GENERAL
        assert data.description is None
        assert data.initial_context is None
    
    def test_conversation_create_title_validation(self):
        """Test title field validation."""
        # Empty title should fail
        with pytest.raises(ValidationError) as exc_info:
            ConversationCreate(title="")
        assert "String should have at least 1 character" in str(exc_info.value)
        
        # Title too long should fail
        long_title = "x" * 201
        with pytest.raises(ValidationError) as exc_info:
            ConversationCreate(title=long_title)
        assert "String should have at most 200 characters" in str(exc_info.value)
    
    def test_conversation_create_description_validation(self):
        """Test description field validation."""
        # Description too long should fail
        long_description = "x" * 1001
        with pytest.raises(ValidationError) as exc_info:
            ConversationCreate(
                title="Test",
                description=long_description
            )
        assert "String should have at most 1000 characters" in str(exc_info.value)


class TestConversationMessageCreateModel:
    """Test ConversationMessageCreate model validation."""
    
    def test_valid_message_create(self):
        """Test valid message creation data."""
        data = ConversationMessageCreate(
            content="This is a test message",
            role=MessageRole.USER,
            metadata={"priority": "high"}
        )
        
        assert data.content == "This is a test message"
        assert data.role == MessageRole.USER
        assert data.metadata == {"priority": "high"}
    
    def test_minimal_message_create(self):
        """Test message creation with minimal required fields."""
        data = ConversationMessageCreate(content="Test message")
        
        assert data.content == "Test message"
        assert data.role == MessageRole.USER  # Default role
        assert data.metadata is None
    
    def test_message_content_validation(self):
        """Test message content field validation."""
        # Empty content should fail
        with pytest.raises(ValidationError) as exc_info:
            ConversationMessageCreate(content="")
        assert "String should have at least 1 character" in str(exc_info.value)
        
        # Content too long should fail
        long_content = "x" * 10001
        with pytest.raises(ValidationError) as exc_info:
            ConversationMessageCreate(content=long_content)
        assert "String should have at most 10000 characters" in str(exc_info.value)


class TestConversationModel:
    """Test Conversation model functionality."""
    
    def test_conversation_creation_with_defaults(self):
        """Test conversation creation with default values."""
        user_id = uuid4()
        conversation = Conversation(
            user_id=user_id,
            title="Test Conversation"
        )
        
        assert isinstance(conversation.id, UUID)
        assert conversation.user_id == user_id
        assert conversation.title == "Test Conversation"
        assert conversation.description is None
        assert conversation.conversation_type == ConversationType.GENERAL
        assert conversation.status == ConversationStatus.ACTIVE
        assert conversation.context == {}
        assert conversation.summary is None
        assert conversation.message_count == 0
        assert conversation.last_message_at is None
        assert isinstance(conversation.created_at, datetime)
        assert isinstance(conversation.updated_at, datetime)
    
    def test_conversation_with_all_fields(self):
        """Test conversation creation with all fields."""
        user_id = uuid4()
        canvas_id = uuid4()
        log_entry_id = uuid4()
        
        conversation = Conversation(
            user_id=user_id,
            title="Full Conversation",
            description="Test description",
            conversation_type=ConversationType.CANVAS_COLLABORATION,
            status=ConversationStatus.ACTIVE,
            context={"theme": "strategy"},
            summary="Test summary",
            related_canvas_id=canvas_id,
            related_log_entry_ids=[log_entry_id],
            message_count=5
        )
        
        assert conversation.title == "Full Conversation"
        assert conversation.description == "Test description"
        assert conversation.conversation_type == ConversationType.CANVAS_COLLABORATION
        assert conversation.status == ConversationStatus.ACTIVE
        assert conversation.context == {"theme": "strategy"}
        assert conversation.summary == "Test summary"
        assert conversation.related_canvas_id == canvas_id
        assert conversation.related_log_entry_ids == [log_entry_id]
        assert conversation.message_count == 5
    
    def test_conversation_json_serialization(self):
        """Test conversation JSON serialization."""
        user_id = uuid4()
        conversation = Conversation(
            user_id=user_id,
            title="JSON Test"
        )
        
        json_data = conversation.model_dump()
        
        assert isinstance(json_data["id"], UUID)
        assert isinstance(json_data["user_id"], UUID)
        assert isinstance(json_data["created_at"], datetime)
        assert json_data["title"] == "JSON Test"


class TestConversationMessageModel:
    """Test ConversationMessage model functionality."""
    
    def test_message_creation_with_defaults(self):
        """Test message creation with default values."""
        conversation_id = uuid4()
        message = ConversationMessage(
            conversation_id=conversation_id,
            role=MessageRole.USER,
            content="Test message"
        )
        
        assert isinstance(message.id, UUID)
        assert message.conversation_id == conversation_id
        assert message.role == MessageRole.USER
        assert message.content == "Test message"
        assert message.metadata == {}
        assert isinstance(message.timestamp, datetime)
    
    def test_message_with_metadata(self):
        """Test message creation with metadata."""
        conversation_id = uuid4()
        metadata = {"intent": "question", "priority": "high"}
        
        message = ConversationMessage(
            conversation_id=conversation_id,
            role=MessageRole.ASSISTANT,
            content="AI response",
            metadata=metadata
        )
        
        assert message.role == MessageRole.ASSISTANT
        assert message.content == "AI response"
        assert message.metadata == metadata
    
    def test_message_json_serialization(self):
        """Test message JSON serialization."""
        conversation_id = uuid4()
        message = ConversationMessage(
            conversation_id=conversation_id,
            role=MessageRole.USER,
            content="Test"
        )
        
        json_data = message.model_dump()
        
        assert isinstance(json_data["id"], UUID)
        assert isinstance(json_data["conversation_id"], UUID)
        assert isinstance(json_data["timestamp"], datetime)


class TestConversationContextModel:
    """Test ConversationContext model functionality."""
    
    def test_conversation_context_creation(self):
        """Test conversation context creation."""
        conversation_id = uuid4()
        user_id = uuid4()
        
        context = ConversationContext(
            conversation_id=conversation_id,
            user_id=user_id,
            conversation_type=ConversationType.ANALYSIS_SUPPORT
        )
        
        assert context.conversation_id == conversation_id
        assert context.user_id == user_id
        assert context.conversation_type == ConversationType.ANALYSIS_SUPPORT
        assert context.recent_messages == []
        assert context.conversation_summary is None
        assert context.north_star_context is None
        assert context.recent_log_entries == []
        assert context.active_analysis_sessions == []
        assert context.active_canvas_data is None
        assert context.user_preferences == {}
        assert context.conversation_patterns == {}
    
    def test_conversation_context_with_data(self):
        """Test conversation context with full data."""
        conversation_id = uuid4()
        user_id = uuid4()
        
        message = ConversationMessage(
            conversation_id=conversation_id,
            role=MessageRole.USER,
            content="Test message"
        )
        
        context = ConversationContext(
            conversation_id=conversation_id,
            user_id=user_id,
            conversation_type=ConversationType.STRATEGIC_PLANNING,
            recent_messages=[message],
            conversation_summary="Test summary",
            north_star_context={"purpose": "test"},
            recent_log_entries=[{"id": "1", "content": "log"}],
            active_analysis_sessions=[{"id": "1", "type": "swot"}],
            active_canvas_data={"title": "canvas"},
            user_preferences={"theme": "dark"},
            conversation_patterns={"frequency": "daily"}
        )
        
        assert len(context.recent_messages) == 1
        assert context.recent_messages[0].content == "Test message"
        assert context.conversation_summary == "Test summary"
        assert context.north_star_context == {"purpose": "test"}
        assert context.recent_log_entries == [{"id": "1", "content": "log"}]
        assert context.active_analysis_sessions == [{"id": "1", "type": "swot"}]
        assert context.active_canvas_data == {"title": "canvas"}
        assert context.user_preferences == {"theme": "dark"}
        assert context.conversation_patterns == {"frequency": "daily"}


class TestResponseModels:
    """Test response model functionality."""
    
    def test_conversation_response(self):
        """Test ConversationResponse model."""
        user_id = uuid4()
        conversation = Conversation(user_id=user_id, title="Test")
        
        response = ConversationResponse(
            conversation=conversation,
            recent_messages=[]
        )
        
        assert response.conversation.title == "Test"
        assert response.recent_messages == []
    
    def test_conversation_list_response(self):
        """Test ConversationListResponse model."""
        user_id = uuid4()
        conversations = [
            Conversation(user_id=user_id, title="Conv 1"),
            Conversation(user_id=user_id, title="Conv 2")
        ]
        
        response = ConversationListResponse(
            conversations=conversations,
            total_count=2,
            page=1,
            page_size=10
        )
        
        assert len(response.conversations) == 2
        assert response.total_count == 2
        assert response.page == 1
        assert response.page_size == 10
    
    def test_conversation_message_response(self):
        """Test ConversationMessageResponse model."""
        conversation_id = uuid4()
        messages = [
            ConversationMessage(conversation_id=conversation_id, role=MessageRole.USER, content="Test")
        ]
        
        response = ConversationMessageResponse(
            messages=messages,
            total_count=1,
            conversation_id=conversation_id,
            page=1,
            page_size=50
        )
        
        assert len(response.messages) == 1
        assert response.total_count == 1
        assert response.conversation_id == conversation_id
        assert response.page == 1
        assert response.page_size == 50


class TestConversationUpdateModel:
    """Test ConversationUpdate model functionality."""
    
    def test_conversation_update_partial(self):
        """Test partial conversation update."""
        update = ConversationUpdate(
            title="Updated Title",
            status=ConversationStatus.ARCHIVED
        )
        
        assert update.title == "Updated Title"
        assert update.description is None
        assert update.status == ConversationStatus.ARCHIVED
        assert update.context is None
    
    def test_conversation_update_full(self):
        """Test full conversation update."""
        update = ConversationUpdate(
            title="Updated Title",
            description="Updated description",
            status=ConversationStatus.PAUSED,
            context={"updated": True}
        )
        
        assert update.title == "Updated Title"
        assert update.description == "Updated description"
        assert update.status == ConversationStatus.PAUSED
        assert update.context == {"updated": True}


class TestAIResponseWithMemoryModel:
    """Test AIResponseWithMemory model functionality."""
    
    def test_ai_response_with_memory(self):
        """Test AI response with memory model."""
        conversation_id = uuid4()
        
        response = AIResponseWithMemory(
            response_content="AI generated response",
            conversation_id=conversation_id,
            should_update_summary=True,
            new_summary="Updated summary",
            context_updates={"learning": "pattern"},
            related_entities=[{"type": "canvas", "id": "123"}]
        )
        
        assert response.response_content == "AI generated response"
        assert response.conversation_id == conversation_id
        assert response.should_update_summary is True
        assert response.new_summary == "Updated summary"
        assert response.context_updates == {"learning": "pattern"}
        assert response.related_entities == [{"type": "canvas", "id": "123"}]
    
    def test_ai_response_minimal(self):
        """Test AI response with minimal fields."""
        conversation_id = uuid4()
        
        response = AIResponseWithMemory(
            response_content="Simple response",
            conversation_id=conversation_id
        )
        
        assert response.response_content == "Simple response"
        assert response.conversation_id == conversation_id
        assert response.should_update_summary is False
        assert response.new_summary is None
        assert response.context_updates == {}
        assert response.related_entities == []