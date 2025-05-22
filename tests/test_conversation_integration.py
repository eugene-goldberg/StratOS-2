import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4, UUID
from datetime import datetime

from backend.services.conversation_service import ConversationService
from backend.models.conversation import (
    ConversationCreate,
    ConversationMessageCreate,
    ConversationType,
    MessageRole,
    ConversationStatus
)
from backend.ai.kernel_service import kernel_service


class TestConversationIntegrationFlow:
    """Test complete conversation workflows end-to-end."""
    
    @pytest_asyncio.fixture
    async def service(self):
        """Create conversation service for integration testing."""
        service = ConversationService()
        service.cosmos_db_available = False  # Use in-memory for testing
        service.conversations_cache = {}
        service.messages_cache = {}
        return service
    
    @pytest_asyncio.fixture
    def user_id(self):
        """Generate test user ID."""
        return uuid4()
    
    @pytest.mark.asyncio
    async def test_complete_strategic_planning_conversation(self, service: ConversationService, user_id: UUID):
        """Test a complete strategic planning conversation flow."""
        
        # Step 1: Create a strategic planning conversation
        conversation_data = ConversationCreate(
            title="Q4 Strategic Planning Session",
            conversation_type=ConversationType.STRATEGIC_PLANNING,
            description="Planning for Q4 expansion strategy",
            initial_context={"quarter": "Q4", "focus": "expansion"}
        )
        
        conversation = await service.create_conversation(conversation_data, user_id)
        assert conversation.title == "Q4 Strategic Planning Session"
        assert conversation.conversation_type == ConversationType.STRATEGIC_PLANNING
        assert conversation.context["quarter"] == "Q4"
        
        # Step 2: User asks initial strategic question
        user_message_1 = ConversationMessageCreate(
            content="What should be our strategic priorities for Q4 expansion?",
            role=MessageRole.USER
        )
        
        message_1 = await service.add_message(conversation.id, user_message_1, user_id)
        assert message_1.content == "What should be our strategic priorities for Q4 expansion?"
        assert message_1.role == MessageRole.USER
        
        # Step 3: Generate AI response with conversation memory
        ai_response_1 = await service.generate_ai_response(
            conversation.id,
            "What should be our strategic priorities for Q4 expansion?",
            user_id
        )
        
        assert isinstance(ai_response_1, str)
        assert len(ai_response_1) > 0
        assert "strategic" in ai_response_1.lower()
        
        # Step 4: Add AI response as message
        ai_message_1 = ConversationMessageCreate(
            content=ai_response_1,
            role=MessageRole.ASSISTANT,
            metadata={"generated_by": "ai", "conversation_turn": 1}
        )
        
        ai_msg_1 = await service.add_message(conversation.id, ai_message_1, user_id)
        assert ai_msg_1.role == MessageRole.ASSISTANT
        
        # Step 5: User follows up with more specific question
        user_message_2 = ConversationMessageCreate(
            content="How should we prioritize between market expansion and product development?",
            role=MessageRole.USER
        )
        
        message_2 = await service.add_message(conversation.id, user_message_2, user_id)
        
        # Step 6: Generate second AI response (should have context from previous exchange)
        ai_response_2 = await service.generate_ai_response(
            conversation.id,
            "How should we prioritize between market expansion and product development?",
            user_id
        )
        
        assert isinstance(ai_response_2, str)
        assert len(ai_response_2) > 0
        # Should be different from first response
        assert ai_response_2 != ai_response_1
        
        # Step 7: Add second AI response
        ai_message_2 = ConversationMessageCreate(
            content=ai_response_2,
            role=MessageRole.ASSISTANT,
            metadata={"generated_by": "ai", "conversation_turn": 2}
        )
        
        await service.add_message(conversation.id, ai_message_2, user_id)
        
        # Step 8: Verify conversation state
        updated_conversation = await service.get_conversation(conversation.id, user_id)
        assert updated_conversation.message_count == 4  # 2 user + 2 AI messages
        assert updated_conversation.last_message_at is not None
        
        # Step 9: Get conversation context for AI
        context = await service.get_conversation_context(conversation.id, user_id, include_messages=4)
        assert context is not None
        assert len(context.recent_messages) == 4
        assert context.conversation_type == ConversationType.STRATEGIC_PLANNING
        
        # Step 10: Generate conversation summary
        all_messages = await service.get_messages(conversation.id, user_id, limit=10)
        assert len(all_messages) == 4
        
        # Verify message order and content
        assert all_messages[0].role == MessageRole.USER
        assert all_messages[1].role == MessageRole.ASSISTANT
        assert all_messages[2].role == MessageRole.USER
        assert all_messages[3].role == MessageRole.ASSISTANT
        
        # Verify conversation continuity
        assert "expansion" in all_messages[0].content.lower()
        assert "prioritize" in all_messages[2].content.lower()
    
    @pytest.mark.asyncio
    async def test_multi_conversation_user_isolation(self, service: ConversationService):
        """Test that multiple users can have separate conversations."""
        user_1 = uuid4()
        user_2 = uuid4()
        
        # User 1 creates a conversation
        conv_data_1 = ConversationCreate(
            title="User 1 Strategic Planning",
            conversation_type=ConversationType.STRATEGIC_PLANNING
        )
        conv_1 = await service.create_conversation(conv_data_1, user_1)
        
        # User 2 creates a conversation
        conv_data_2 = ConversationCreate(
            title="User 2 Analysis Session",
            conversation_type=ConversationType.ANALYSIS_SUPPORT
        )
        conv_2 = await service.create_conversation(conv_data_2, user_2)
        
        # Add messages to each conversation
        msg_1 = ConversationMessageCreate(content="User 1 message", role=MessageRole.USER)
        msg_2 = ConversationMessageCreate(content="User 2 message", role=MessageRole.USER)
        
        await service.add_message(conv_1.id, msg_1, user_1)
        await service.add_message(conv_2.id, msg_2, user_2)
        
        # Verify isolation: User 1 cannot access User 2's conversation
        user_1_access_to_conv_2 = await service.get_conversation(conv_2.id, user_1)
        assert user_1_access_to_conv_2 is None
        
        # Verify isolation: User 2 cannot access User 1's conversation
        user_2_access_to_conv_1 = await service.get_conversation(conv_1.id, user_2)
        assert user_2_access_to_conv_1 is None
        
        # Verify each user can access their own conversations
        user_1_convs = await service.list_conversations(user_1)
        user_2_convs = await service.list_conversations(user_2)
        
        assert len(user_1_convs) == 1
        assert len(user_2_convs) == 1
        assert user_1_convs[0].title == "User 1 Strategic Planning"
        assert user_2_convs[0].title == "User 2 Analysis Session"
    
    @pytest.mark.asyncio
    async def test_conversation_type_specific_ai_responses(self, service: ConversationService, user_id: UUID):
        """Test that AI responses are tailored to conversation types."""
        
        # Test different conversation types
        test_cases = [
            {
                "type": ConversationType.ANALYSIS_SUPPORT,
                "title": "SWOT Analysis Help",
                "user_message": "Help me with SWOT analysis",
                "expected_keywords": ["swot", "analysis", "strengths", "weaknesses"]
            },
            {
                "type": ConversationType.CANVAS_COLLABORATION,
                "title": "Strategic Canvas Design",
                "user_message": "How do I use the Strategic Canvas?",
                "expected_keywords": ["canvas", "visual", "elements", "connections"]
            },
            {
                "type": ConversationType.CEO_LOG_DISCUSSION,
                "title": "Leadership Insights",
                "user_message": "How should I document strategic decisions?",
                "expected_keywords": ["log", "decision", "leadership", "insights"]
            }
        ]
        
        for test_case in test_cases:
            # Create conversation of specific type
            conv_data = ConversationCreate(
                title=test_case["title"],
                conversation_type=test_case["type"]
            )
            conversation = await service.create_conversation(conv_data, user_id)
            
            # Add user message
            user_msg = ConversationMessageCreate(
                content=test_case["user_message"],
                role=MessageRole.USER
            )
            await service.add_message(conversation.id, user_msg, user_id)
            
            # Generate AI response
            ai_response = await service.generate_ai_response(
                conversation.id,
                test_case["user_message"],
                user_id
            )
            
            # Verify response is tailored to conversation type
            assert isinstance(ai_response, str)
            assert len(ai_response) > 0
            
            # Check that response contains relevant keywords
            response_lower = ai_response.lower()
            keywords_found = [kw for kw in test_case["expected_keywords"] if kw in response_lower]
            assert len(keywords_found) > 0, f"Response for {test_case['type']} should contain keywords {test_case['expected_keywords']}, but only found {keywords_found}"
    
    @pytest.mark.asyncio
    async def test_conversation_context_builds_over_time(self, service: ConversationService, user_id: UUID):
        """Test that conversation context accumulates and influences AI responses."""
        
        # Create conversation
        conv_data = ConversationCreate(
            title="Market Analysis Discussion",
            conversation_type=ConversationType.ANALYSIS_SUPPORT
        )
        conversation = await service.create_conversation(conv_data, user_id)
        
        # Series of related messages to build context
        conversation_flow = [
            "I need to analyze our competitive position",
            "What competitors should I focus on?",
            "How do I assess their strengths?",
            "Now I want to identify our opportunities against these competitors"
        ]
        
        ai_responses = []
        
        for i, user_message_content in enumerate(conversation_flow):
            # Add user message
            user_msg = ConversationMessageCreate(
                content=user_message_content,
                role=MessageRole.USER
            )
            await service.add_message(conversation.id, user_msg, user_id)
            
            # Generate AI response
            ai_response = await service.generate_ai_response(
                conversation.id,
                user_message_content,
                user_id
            )
            ai_responses.append(ai_response)
            
            # Add AI response
            ai_msg = ConversationMessageCreate(
                content=ai_response,
                role=MessageRole.ASSISTANT
            )
            await service.add_message(conversation.id, ai_msg, user_id)
        
        # Verify context builds over time
        assert len(ai_responses) == 4
        
        # Later responses should be more contextual
        # The 4th response should potentially reference the competitive analysis context
        final_response = ai_responses[3].lower()
        assert any(keyword in final_response for keyword in ["competitor", "competitive", "analysis", "strength"])
        
        # Get final conversation context
        context = await service.get_conversation_context(conversation.id, user_id)
        assert len(context.recent_messages) == 8  # 4 user + 4 AI messages
        assert context.conversation_type == ConversationType.ANALYSIS_SUPPORT
    
    @pytest.mark.asyncio
    async def test_conversation_update_and_management(self, service: ConversationService, user_id: UUID):
        """Test conversation management operations."""
        
        # Create conversation
        conv_data = ConversationCreate(
            title="Initial Title",
            conversation_type=ConversationType.GENERAL,
            description="Initial description"
        )
        conversation = await service.create_conversation(conv_data, user_id)
        
        # Add some messages
        for i in range(3):
            msg = ConversationMessageCreate(content=f"Message {i}", role=MessageRole.USER)
            await service.add_message(conversation.id, msg, user_id)
        
        # Update conversation
        from backend.models.conversation import ConversationUpdate
        update_data = ConversationUpdate(
            title="Updated Strategic Discussion",
            description="Updated description with more details",
            status=ConversationStatus.ACTIVE,
            context={"phase": "planning", "priority": "high"}
        )
        
        updated_conv = await service.update_conversation(conversation.id, user_id, update_data)
        assert updated_conv is not None
        assert updated_conv.title == "Updated Strategic Discussion"
        assert updated_conv.description == "Updated description with more details"
        assert updated_conv.context["phase"] == "planning"
        assert updated_conv.context["priority"] == "high"
        assert updated_conv.message_count == 3
        
        # Update conversation summary
        test_summary = "This conversation focused on strategic planning and decision-making frameworks."
        await service.update_conversation_summary(conversation.id, user_id, test_summary)
        
        final_conv = await service.get_conversation(conversation.id, user_id)
        assert final_conv.summary == test_summary
        
        # Test conversation listing with updated data
        conversations = await service.list_conversations(user_id)
        assert len(conversations) == 1
        assert conversations[0].title == "Updated Strategic Discussion"
    
    @pytest.mark.asyncio
    async def test_conversation_deletion_cascade(self, service: ConversationService, user_id: UUID):
        """Test that deleting a conversation also deletes associated messages."""
        
        # Create conversation
        conv_data = ConversationCreate(title="Conversation to Delete")
        conversation = await service.create_conversation(conv_data, user_id)
        
        # Add multiple messages
        message_ids = []
        for i in range(5):
            msg = ConversationMessageCreate(content=f"Message {i}", role=MessageRole.USER)
            added_msg = await service.add_message(conversation.id, msg, user_id)
            message_ids.append(added_msg.id)
        
        # Verify messages exist
        messages_before = await service.get_messages(conversation.id, user_id)
        assert len(messages_before) == 5
        
        # Delete conversation
        deleted = await service.delete_conversation(conversation.id, user_id)
        assert deleted is True
        
        # Verify conversation is gone
        conv_after = await service.get_conversation(conversation.id, user_id)
        assert conv_after is None
        
        # Verify messages are gone
        messages_after = await service.get_messages(conversation.id, user_id)
        assert len(messages_after) == 0
        
        # Verify conversation not in user's list
        user_conversations = await service.list_conversations(user_id)
        conv_ids = [conv.id for conv in user_conversations]
        assert conversation.id not in conv_ids


class TestConversationErrorScenarios:
    """Test error handling in conversation workflows."""
    
    @pytest_asyncio.fixture
    async def service(self):
        """Create conversation service for error testing."""
        service = ConversationService()
        service.cosmos_db_available = False
        service.conversations_cache = {}
        service.messages_cache = {}
        return service
    
    @pytest.mark.asyncio
    async def test_ai_response_error_recovery(self, service: ConversationService):
        """Test graceful handling when AI response generation fails."""
        user_id = uuid4()
        
        # Create conversation
        conv_data = ConversationCreate(title="Error Test Conversation")
        conversation = await service.create_conversation(conv_data, user_id)
        
        # Add user message
        user_msg = ConversationMessageCreate(content="Test message", role=MessageRole.USER)
        await service.add_message(conversation.id, user_msg, user_id)
        
        # Mock kernel service to raise exception
        with patch('backend.services.conversation_service.kernel_service') as mock_kernel:
            mock_kernel.invoke_semantic_function = AsyncMock(side_effect=Exception("AI service error"))
            
            # Generate AI response (should handle error gracefully)
            ai_response = await service.generate_ai_response(
                conversation.id,
                "Test message",
                user_id
            )
            
            # Should return error message instead of crashing
            assert isinstance(ai_response, str)
            assert "trouble generating a response" in ai_response.lower()
    
    @pytest.mark.asyncio
    async def test_concurrent_message_addition(self, service: ConversationService):
        """Test handling concurrent message additions to same conversation."""
        user_id = uuid4()
        
        # Create conversation
        conv_data = ConversationCreate(title="Concurrent Test")
        conversation = await service.create_conversation(conv_data, user_id)
        
        # Simulate concurrent message additions
        import asyncio
        
        async def add_messages_batch(batch_id: int):
            messages = []
            for i in range(3):
                msg = ConversationMessageCreate(
                    content=f"Batch {batch_id} Message {i}",
                    role=MessageRole.USER
                )
                added_msg = await service.add_message(conversation.id, msg, user_id)
                messages.append(added_msg)
            return messages
        
        # Run concurrent batches
        batch_results = await asyncio.gather(
            add_messages_batch(1),
            add_messages_batch(2),
            add_messages_batch(3)
        )
        
        # Verify all messages were added
        all_messages = await service.get_messages(conversation.id, user_id)
        assert len(all_messages) == 9  # 3 batches × 3 messages
        
        # Verify conversation count is updated
        updated_conv = await service.get_conversation(conversation.id, user_id)
        assert updated_conv.message_count == 9


class TestConversationPerformance:
    """Test conversation performance with larger datasets."""
    
    @pytest_asyncio.fixture
    async def service(self):
        """Create conversation service for performance testing."""
        service = ConversationService()
        service.cosmos_db_available = False
        service.conversations_cache = {}
        service.messages_cache = {}
        return service
    
    @pytest.mark.asyncio
    async def test_large_conversation_handling(self, service: ConversationService):
        """Test handling conversations with many messages."""
        user_id = uuid4()
        
        # Create conversation
        conv_data = ConversationCreate(title="Large Conversation Test")
        conversation = await service.create_conversation(conv_data, user_id)
        
        # Add many messages
        message_count = 50
        for i in range(message_count):
            msg = ConversationMessageCreate(
                content=f"Message {i}: This is a longer message to test performance with substantial content that might be typical in real strategic conversations.",
                role=MessageRole.USER if i % 2 == 0 else MessageRole.ASSISTANT
            )
            await service.add_message(conversation.id, msg, user_id)
        
        # Test retrieval performance
        import time
        start_time = time.time()
        
        # Get all messages
        all_messages = await service.get_messages(conversation.id, user_id, limit=100)
        
        # Get conversation context
        context = await service.get_conversation_context(conversation.id, user_id, include_messages=20)
        
        end_time = time.time()
        
        # Verify results
        assert len(all_messages) == message_count
        assert len(context.recent_messages) == 20
        
        # Performance should be reasonable (less than 1 second for in-memory operations)
        operation_time = end_time - start_time
        assert operation_time < 1.0, f"Operations took {operation_time} seconds, should be under 1 second"
    
    @pytest.mark.asyncio
    async def test_many_conversations_per_user(self, service: ConversationService):
        """Test handling users with many conversations."""
        user_id = uuid4()
        
        # Create many conversations
        conversation_count = 25
        conversations = []
        
        for i in range(conversation_count):
            conv_data = ConversationCreate(
                title=f"Conversation {i}",
                conversation_type=ConversationType.GENERAL if i % 2 == 0 else ConversationType.STRATEGIC_PLANNING
            )
            conv = await service.create_conversation(conv_data, user_id)
            conversations.append(conv)
            
            # Add a few messages to each
            for j in range(3):
                msg = ConversationMessageCreate(content=f"Conv {i} Message {j}")
                await service.add_message(conv.id, msg, user_id)
        
        # Test listing performance
        import time
        start_time = time.time()
        
        # List all conversations
        all_conversations = await service.list_conversations(user_id, limit=50)
        
        # Test pagination
        page_1 = await service.list_conversations(user_id, limit=10, offset=0)
        page_2 = await service.list_conversations(user_id, limit=10, offset=10)
        
        # Test filtering
        planning_conversations = await service.list_conversations(
            user_id, conversation_type=ConversationType.STRATEGIC_PLANNING
        )
        
        end_time = time.time()
        
        # Verify results
        assert len(all_conversations) == conversation_count
        assert len(page_1) == 10
        assert len(page_2) == 10
        assert len(planning_conversations) == conversation_count // 2  # Half are strategic planning
        
        # Performance should be reasonable
        operation_time = end_time - start_time
        assert operation_time < 2.0, f"Operations took {operation_time} seconds, should be under 2 seconds"