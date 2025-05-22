import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4, UUID
from datetime import datetime
from fastapi.testclient import TestClient
from fastapi import status
import json

from backend.main import app
from backend.models.conversation import (
    Conversation,
    ConversationCreate,
    ConversationUpdate,
    ConversationMessage,
    ConversationMessageCreate,
    ConversationType,
    MessageRole,
    ConversationStatus
)


@pytest.fixture
def client(mock_user_id):
    """Create test client with dependency overrides."""
    from backend.dependencies import get_current_user_id
    
    # Override the dependency
    def override_get_current_user_id():
        return mock_user_id
    
    app.dependency_overrides[get_current_user_id] = override_get_current_user_id
    
    test_client = TestClient(app)
    
    yield test_client
    
    # Clean up dependency overrides
    app.dependency_overrides.clear()


@pytest.fixture
def mock_user_id():
    """Mock user ID for testing."""
    # Use a fixed UUID for consistent testing
    return UUID('12345678-1234-5678-9abc-123456789abc')


@pytest.fixture
def auth_headers(mock_user_id):
    """Create authorization headers for testing."""
    # Mock authentication - in real implementation this would be a JWT token
    return {"Authorization": f"Bearer mock-token-{mock_user_id}"}


@pytest.fixture
def conversation_create_data():
    """Create test conversation creation data."""
    return {
        "title": "Test Strategic Discussion",
        "conversation_type": "strategic_planning",
        "description": "Testing conversation creation via API",
        "initial_context": {"priority": "high"}
    }


@pytest.fixture
def message_create_data():
    """Create test message creation data."""
    return {
        "content": "This is a test message for the API",
        "role": "user",
        "metadata": {"intent": "question"}
    }


class TestConversationCRUDEndpoints:
    """Test conversation CRUD API endpoints."""
    
    @patch('backend.routers.conversation.conversation_service')
    def test_create_conversation(self, mock_service, client, mock_user_id, conversation_create_data):
        """Test POST /api/conversations endpoint."""
        # Setup mocks
        mock_conversation = Conversation(
            id=uuid4(),
            user_id=mock_user_id,
            title=conversation_create_data["title"],
            conversation_type=ConversationType.STRATEGIC_PLANNING,
            description=conversation_create_data["description"],
            context=conversation_create_data["initial_context"]
        )
        mock_service.create_conversation = AsyncMock(return_value=mock_conversation)
        
        # Make request
        response = client.post("/api/conversations", json=conversation_create_data)
        
        # Assertions
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["title"] == conversation_create_data["title"]
        assert data["conversation_type"] == "strategic_planning"
        assert data["description"] == conversation_create_data["description"]
        assert data["user_id"] == str(mock_user_id)
        
        # Verify service was called correctly
        mock_service.create_conversation.assert_called_once()
        call_args = mock_service.create_conversation.call_args
        assert call_args[0][1] == mock_user_id  # user_id parameter
    
    @patch('backend.routers.conversation.conversation_service')
    def test_list_conversations(self, mock_service, client, mock_user_id):
        """Test GET /api/conversations endpoint."""
        # Setup mocks
        mock_conversations = [
            Conversation(
                id=uuid4(),
                user_id=mock_user_id,
                title="Conversation 1",
                conversation_type=ConversationType.GENERAL
            ),
            Conversation(
                id=uuid4(),
                user_id=mock_user_id,
                title="Conversation 2",
                conversation_type=ConversationType.STRATEGIC_PLANNING
            )
        ]
        mock_service.list_conversations = AsyncMock(return_value=mock_conversations)
        
        # Make request
        response = client.get("/api/conversations?limit=10&offset=0")
        
        # Assertions
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "conversations" in data
        assert "total_count" in data
        assert "page" in data
        assert "page_size" in data
        assert len(data["conversations"]) == 2
        assert data["conversations"][0]["title"] == "Conversation 1"
        assert data["conversations"][1]["title"] == "Conversation 2"
        
        # Verify service was called twice (once for data, once for count)
        assert mock_service.list_conversations.call_count == 2
        # First call with pagination parameters
        mock_service.list_conversations.assert_any_call(
            mock_user_id, limit=10, offset=0, conversation_type=None
        )
        # Second call for total count
        mock_service.list_conversations.assert_any_call(
            mock_user_id, limit=1000
        )
    
    @patch('backend.routers.conversation.conversation_service')
    def test_list_conversations_with_type_filter(self, mock_service, client, mock_user_id):
        """Test GET /api/conversations with conversation type filter."""
        # Setup mocks
        mock_conversations = [
            Conversation(
                id=uuid4(),
                user_id=mock_user_id,
                title="Strategic Conversation",
                conversation_type=ConversationType.STRATEGIC_PLANNING
            )
        ]
        mock_service.list_conversations = AsyncMock(return_value=mock_conversations)
        
        # Make request with type filter
        response = client.get("/api/conversations?conversation_type=strategic_planning")
        
        # Assertions
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["conversations"]) == 1
        assert data["conversations"][0]["conversation_type"] == "strategic_planning"
        
        # Verify service was called twice (once for data, once for count)
        assert mock_service.list_conversations.call_count == 2
        # First call with type filter and default pagination
        mock_service.list_conversations.assert_any_call(
            mock_user_id, limit=20, offset=0, conversation_type=ConversationType.STRATEGIC_PLANNING
        )
        # Second call for total count
        mock_service.list_conversations.assert_any_call(
            mock_user_id, limit=1000
        )
    
    @patch('backend.routers.conversation.conversation_service')
    def test_get_conversation(self, mock_service, client, mock_user_id):
        """Test GET /api/conversations/{conversation_id} endpoint."""
        # Setup mocks
        conversation_id = uuid4()
        mock_conversation = Conversation(
            id=conversation_id,
            user_id=mock_user_id,
            title="Test Conversation"
        )
        mock_messages = [
            ConversationMessage(
                id=uuid4(),
                conversation_id=conversation_id,
                role=MessageRole.USER,
                content="Test message"
            )
        ]
        mock_service.get_conversation = AsyncMock(return_value=mock_conversation)
        mock_service.get_messages = AsyncMock(return_value=mock_messages)
        
        # Make request
        response = client.get(f"/api/conversations/{conversation_id}?include_recent_messages=5")
        
        # Assertions
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "conversation" in data
        assert "recent_messages" in data
        assert data["conversation"]["id"] == str(conversation_id)
        assert data["conversation"]["title"] == "Test Conversation"
        assert len(data["recent_messages"]) == 1
        assert data["recent_messages"][0]["content"] == "Test message"
        
        # Verify service calls
        mock_service.get_conversation.assert_called_once_with(conversation_id, mock_user_id)
        mock_service.get_messages.assert_called_once_with(conversation_id, mock_user_id, limit=5)
    
    @patch('backend.routers.conversation.conversation_service')
    def test_get_conversation_not_found(self, mock_service, client, mock_user_id):
        """Test GET /api/conversations/{conversation_id} when conversation doesn't exist."""
        # Setup mocks
        conversation_id = uuid4()
        mock_service.get_conversation = AsyncMock(return_value=None)
        
        # Make request
        response = client.get(f"/api/conversations/{conversation_id}")
        
        # Assertions
        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert data["detail"] == "Conversation not found"
    
    @patch('backend.routers.conversation.conversation_service')
    def test_update_conversation(self, mock_service, client, mock_user_id):
        """Test PUT /api/conversations/{conversation_id} endpoint."""
        # Setup mocks
        conversation_id = uuid4()
        updated_conversation = Conversation(
            id=conversation_id,
            user_id=mock_user_id,
            title="Updated Title",
            description="Updated description",
            status=ConversationStatus.ARCHIVED
        )
        mock_service.update_conversation = AsyncMock(return_value=updated_conversation)
        
        update_data = {
            "title": "Updated Title",
            "description": "Updated description",
            "status": "archived"
        }
        
        # Make request
        response = client.put(f"/api/conversations/{conversation_id}", json=update_data)
        
        # Assertions
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["title"] == "Updated Title"
        assert data["description"] == "Updated description"
        assert data["status"] == "archived"
        
        # Verify service was called correctly
        mock_service.update_conversation.assert_called_once()
        call_args = mock_service.update_conversation.call_args
        assert call_args[0][0] == conversation_id
        assert call_args[0][1] == mock_user_id
    
    @patch('backend.routers.conversation.conversation_service')
    def test_update_conversation_not_found(self, mock_service, client, mock_user_id):
        """Test PUT /api/conversations/{conversation_id} when conversation doesn't exist."""
        # Setup mocks
        conversation_id = uuid4()
        mock_service.update_conversation = AsyncMock(return_value=None)
        
        update_data = {"title": "Updated Title"}
        
        # Make request
        response = client.put(f"/api/conversations/{conversation_id}", json=update_data)
        
        # Assertions
        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert data["detail"] == "Conversation not found"
    
    @patch('backend.routers.conversation.conversation_service')
    def test_delete_conversation(self, mock_service, client, mock_user_id):
        """Test DELETE /api/conversations/{conversation_id} endpoint."""
        # Setup mocks
        conversation_id = uuid4()
        mock_service.delete_conversation = AsyncMock(return_value=True)
        
        # Make request
        response = client.delete(f"/api/conversations/{conversation_id}")
        
        # Assertions
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "success"
        assert data["message"] == "Conversation deleted successfully"
        
        # Verify service was called correctly
        mock_service.delete_conversation.assert_called_once_with(conversation_id, mock_user_id)
    
    @patch('backend.routers.conversation.conversation_service')
    def test_delete_conversation_not_found(self, mock_service, client, mock_user_id):
        """Test DELETE /api/conversations/{conversation_id} when conversation doesn't exist."""
        # Setup mocks
        conversation_id = uuid4()
        mock_service.delete_conversation = AsyncMock(return_value=False)
        
        # Make request
        response = client.delete(f"/api/conversations/{conversation_id}")
        
        # Assertions
        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert data["detail"] == "Conversation not found"


class TestMessageEndpoints:
    """Test message-related API endpoints."""
    
    @patch('backend.routers.conversation.conversation_service')
    def test_add_message(self, mock_service, client, mock_user_id, message_create_data):
        """Test POST /api/conversations/{conversation_id}/messages endpoint."""
        # Setup mocks
        conversation_id = uuid4()
        mock_message = ConversationMessage(
            id=uuid4(),
            conversation_id=conversation_id,
            role=MessageRole.USER,
            content=message_create_data["content"],
            metadata=message_create_data["metadata"]
        )
        mock_service.add_message = AsyncMock(return_value=mock_message)
        
        # Make request
        response = client.post(f"/api/conversations/{conversation_id}/messages", json=message_create_data)
        
        # Assertions
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["conversation_id"] == str(conversation_id)
        assert data["role"] == "user"
        assert data["content"] == message_create_data["content"]
        assert data["metadata"] == message_create_data["metadata"]
        
        # Verify service was called correctly
        mock_service.add_message.assert_called_once()
        call_args = mock_service.add_message.call_args
        assert call_args[0][0] == conversation_id
        assert call_args[0][2] == mock_user_id
    
    @patch('backend.routers.conversation.conversation_service')
    def test_get_messages(self, mock_service, client, mock_user_id):
        """Test GET /api/conversations/{conversation_id}/messages endpoint."""
        # Setup mocks
        conversation_id = uuid4()
        mock_conversation = Conversation(
            id=conversation_id,
            user_id=mock_user_id,
            title="Test Conversation",
            message_count=3
        )
        mock_messages = [
            ConversationMessage(
                id=uuid4(),
                conversation_id=conversation_id,
                role=MessageRole.USER,
                content=f"Message {i}"
            ) for i in range(3)
        ]
        mock_service.get_conversation = AsyncMock(return_value=mock_conversation)
        mock_service.get_messages = AsyncMock(return_value=mock_messages)
        
        # Make request
        response = client.get(f"/api/conversations/{conversation_id}/messages?limit=10&offset=0")
        
        # Assertions
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "messages" in data
        assert "total_count" in data
        assert "conversation_id" in data
        assert "page" in data
        assert "page_size" in data
        assert len(data["messages"]) == 3
        assert data["total_count"] == 3
        assert data["conversation_id"] == str(conversation_id)
        
        # Verify service calls
        mock_service.get_conversation.assert_called_once_with(conversation_id, mock_user_id)
        mock_service.get_messages.assert_called_once_with(conversation_id, mock_user_id, limit=10, offset=0)
    
    @patch('backend.routers.conversation.conversation_service')
    def test_get_messages_conversation_not_found(self, mock_service, client, mock_user_id):
        """Test GET /api/conversations/{conversation_id}/messages when conversation doesn't exist."""
        # Setup mocks
        conversation_id = uuid4()
        mock_service.get_conversation = AsyncMock(return_value=None)
        
        # Make request
        response = client.get(f"/api/conversations/{conversation_id}/messages")
        
        # Assertions
        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert data["detail"] == "Conversation not found"


class TestAIChatEndpoint:
    """Test AI chat functionality."""
    
    @patch('backend.routers.conversation.conversation_service')
    def test_chat_with_ai(self, mock_service, client, mock_user_id):
        """Test POST /api/conversations/{conversation_id}/chat endpoint."""
        # Setup mocks
        conversation_id = uuid4()
        
        user_message = ConversationMessage(
            id=uuid4(),
            conversation_id=conversation_id,
            role=MessageRole.USER,
            content="What should be our strategic priority?"
        )
        ai_message = ConversationMessage(
            id=uuid4(),
            conversation_id=conversation_id,
            role=MessageRole.ASSISTANT,
            content="Based on our discussion, I recommend focusing on market expansion."
        )
        
        mock_service.add_message = AsyncMock(side_effect=[user_message, ai_message])
        mock_service.generate_ai_response = AsyncMock(return_value="Based on our discussion, I recommend focusing on market expansion.")
        
        message_data = {
            "content": "What should be our strategic priority?",
            "role": "user"
        }
        
        # Make request
        response = client.post(f"/api/conversations/{conversation_id}/chat", json=message_data)
        
        # Assertions
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "user_message" in data
        assert "ai_response" in data
        assert "conversation_id" in data
        assert data["user_message"]["content"] == message_data["content"]
        assert data["ai_response"]["content"] == "Based on our discussion, I recommend focusing on market expansion."
        assert data["conversation_id"] == str(conversation_id)
        
        # Verify service calls
        assert mock_service.add_message.call_count == 2  # User message + AI response
        mock_service.generate_ai_response.assert_called_once_with(
            conversation_id, message_data["content"], mock_user_id
        )
    
    @patch('backend.routers.conversation.conversation_service')
    def test_chat_with_ai_invalid_role(self, mock_service, client, mock_user_id):
        """Test POST /api/conversations/{conversation_id}/chat with invalid role."""
        # Setup mocks
        conversation_id = uuid4()
        
        message_data = {
            "content": "Test message",
            "role": "assistant"  # Only "user" role allowed for chat endpoint
        }
        
        # Make request
        response = client.post(f"/api/conversations/{conversation_id}/chat", json=message_data)
        
        # Assertions
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "Only user messages are allowed for chat endpoint" in data["detail"]
    
    @patch('backend.routers.conversation.conversation_service')
    def test_chat_ai_error_handling(self, mock_service, client, mock_user_id):
        """Test chat endpoint when AI generation fails."""
        # Setup mocks
        conversation_id = uuid4()
        
        user_message = ConversationMessage(
            id=uuid4(),
            conversation_id=conversation_id,
            role=MessageRole.USER,
            content="Test message"
        )
        
        mock_service.add_message = AsyncMock(return_value=user_message)
        mock_service.generate_ai_response = AsyncMock(side_effect=Exception("AI service error"))
        
        message_data = {
            "content": "Test message",
            "role": "user"
        }
        
        # Make request
        response = client.post(f"/api/conversations/{conversation_id}/chat", json=message_data)
        
        # Assertions
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "user_message" in data
        assert data["ai_response"] is None
        assert "error" in data
        assert "AI service error" in data["error"]


class TestManagementEndpoints:
    """Test conversation management endpoints."""
    
    @patch('backend.routers.conversation.conversation_service')
    @patch('backend.ai.kernel_service.kernel_service')
    def test_summarize_conversation(self, mock_kernel_service, mock_service, client, mock_user_id):
        """Test POST /api/conversations/{conversation_id}/summarize endpoint."""
        # Setup mocks
        conversation_id = uuid4()
        
        mock_conversation = Conversation(
            id=conversation_id,
            user_id=mock_user_id,
            title="Strategic Planning Discussion"
        )
        mock_messages = [
            ConversationMessage(
                id=uuid4(),
                conversation_id=conversation_id,
                role=MessageRole.USER,
                content="What should be our expansion strategy?"
            ),
            ConversationMessage(
                id=uuid4(),
                conversation_id=conversation_id,
                role=MessageRole.ASSISTANT,
                content="Consider market analysis and resource allocation."
            )
        ]
        mock_summary = "## Conversation Summary\n\n**Main Topics**: Strategic Planning\n\n**Key Insights**: Discussion about expansion strategy and market analysis."
        
        mock_service.get_conversation = AsyncMock(return_value=mock_conversation)
        mock_service.get_messages = AsyncMock(return_value=mock_messages)
        mock_service.update_conversation_summary = AsyncMock()
        mock_kernel_service.invoke_semantic_function = AsyncMock(return_value=mock_summary)
        
        # Make request
        response = client.post(f"/api/conversations/{conversation_id}/summarize")
        
        # Assertions
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "conversation_id" in data
        assert "summary" in data
        assert "message_count" in data
        assert "generated_at" in data
        assert data["conversation_id"] == str(conversation_id)
        assert data["summary"] == mock_summary
        assert data["message_count"] == 2
        
        # Verify service calls
        mock_service.get_conversation.assert_called_once_with(conversation_id, mock_user_id)
        mock_service.get_messages.assert_called_once_with(conversation_id, mock_user_id, limit=1000)
        mock_service.update_conversation_summary.assert_called_once_with(conversation_id, mock_user_id, mock_summary)
        mock_kernel_service.invoke_semantic_function.assert_called_once()
    
    @patch('backend.routers.conversation.conversation_service')
    def test_summarize_conversation_not_found(self, mock_service, client, mock_user_id):
        """Test summarize endpoint when conversation doesn't exist."""
        # Setup mocks
        conversation_id = uuid4()
        mock_service.get_conversation = AsyncMock(return_value=None)
        
        # Make request
        response = client.post(f"/api/conversations/{conversation_id}/summarize")
        
        # Assertions
        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert data["detail"] == "Conversation not found"
    
    @patch('backend.routers.conversation.conversation_service')
    def test_summarize_empty_conversation(self, mock_service, client, mock_user_id):
        """Test summarize endpoint when conversation has no messages."""
        # Setup mocks
        conversation_id = uuid4()
        
        mock_conversation = Conversation(
            id=conversation_id,
            user_id=mock_user_id,
            title="Empty Conversation"
        )
        mock_service.get_conversation = AsyncMock(return_value=mock_conversation)
        mock_service.get_messages = AsyncMock(return_value=[])
        
        # Make request
        response = client.post(f"/api/conversations/{conversation_id}/summarize")
        
        # Assertions
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert data["detail"] == "Cannot summarize empty conversation"
    
    @patch('backend.routers.conversation.conversation_service')
    def test_get_conversation_context(self, mock_service, client, mock_user_id):
        """Test GET /api/conversations/{conversation_id}/context endpoint."""
        # Setup mocks
        conversation_id = uuid4()
        
        from backend.models.conversation import ConversationContext
        mock_context = ConversationContext(
            conversation_id=conversation_id,
            user_id=mock_user_id,
            conversation_type=ConversationType.STRATEGIC_PLANNING,
            recent_messages=[],
            conversation_summary="Test summary"
        )
        mock_service.get_conversation_context = AsyncMock(return_value=mock_context)
        
        # Make request
        response = client.get(f"/api/conversations/{conversation_id}/context?include_messages=5")
        
        # Assertions
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["conversation_id"] == str(conversation_id)
        assert data["user_id"] == str(mock_user_id)
        assert data["conversation_type"] == "strategic_planning"
        assert data["conversation_summary"] == "Test summary"
        
        # Verify service call
        mock_service.get_conversation_context.assert_called_once_with(
            conversation_id, mock_user_id, include_messages=5
        )
    
    @patch('backend.routers.conversation.conversation_service')
    def test_get_conversation_context_not_found(self, mock_service, client, mock_user_id):
        """Test context endpoint when conversation doesn't exist."""
        # Setup mocks
        conversation_id = uuid4()
        mock_service.get_conversation_context = AsyncMock(return_value=None)
        
        # Make request
        response = client.get(f"/api/conversations/{conversation_id}/context")
        
        # Assertions
        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert data["detail"] == "Conversation not found"


class TestValidationAndErrors:
    """Test validation and error handling."""
    
    def test_create_conversation_validation_error(self, client, mock_user_id):
        """Test conversation creation with invalid data."""
        
        # Invalid data - empty title
        invalid_data = {
            "title": "",  # Too short
            "conversation_type": "invalid_type"  # Invalid enum
        }
        
        response = client.post("/api/conversations", json=invalid_data)
        
        # Should return validation error
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_add_message_validation_error(self, client, mock_user_id):
        """Test message creation with invalid data."""
        conversation_id = uuid4()
        
        # Invalid data - empty content
        invalid_data = {
            "content": "",  # Too short
            "role": "invalid_role"  # Invalid enum
        }
        
        response = client.post(f"/api/conversations/{conversation_id}/messages", json=invalid_data)
        
        # Should return validation error
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY