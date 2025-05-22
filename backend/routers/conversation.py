from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from uuid import UUID

from ..models.conversation import (
    Conversation,
    ConversationCreate,
    ConversationUpdate,
    ConversationMessage,
    ConversationMessageCreate,
    ConversationType,
    ConversationResponse,
    ConversationListResponse,
    ConversationMessageResponse
)
from ..services.conversation_service import conversation_service
from ..dependencies import get_current_user_id

router = APIRouter(prefix="/conversations", tags=["conversations"])

# Conversation CRUD endpoints
@router.post("/", response_model=Conversation, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    conversation_data: ConversationCreate,
    current_user_id: UUID = Depends(get_current_user_id)
):
    """Create a new conversation."""
    conversation = await conversation_service.create_conversation(conversation_data, current_user_id)
    return conversation

@router.get("/", response_model=ConversationListResponse)
async def list_conversations(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    conversation_type: Optional[ConversationType] = Query(None),
    current_user_id: UUID = Depends(get_current_user_id)
):
    """List conversations for the current user."""
    conversations = await conversation_service.list_conversations(
        current_user_id, limit=limit, offset=offset, conversation_type=conversation_type
    )
    
    # Get total count (simplified - in production you might want a separate count query)
    total_conversations = await conversation_service.list_conversations(current_user_id, limit=1000)
    total_count = len(total_conversations)
    
    return ConversationListResponse(
        conversations=conversations,
        total_count=total_count,
        page=offset // limit + 1,
        page_size=limit
    )

@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: UUID,
    include_recent_messages: int = Query(10, ge=0, le=50),
    current_user_id: UUID = Depends(get_current_user_id)
):
    """Get a specific conversation with recent messages."""
    conversation = await conversation_service.get_conversation(conversation_id, current_user_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    recent_messages = []
    if include_recent_messages > 0:
        recent_messages = await conversation_service.get_messages(
            conversation_id, current_user_id, limit=include_recent_messages
        )
    
    return ConversationResponse(
        conversation=conversation,
        recent_messages=recent_messages
    )

@router.put("/{conversation_id}", response_model=Conversation)
async def update_conversation(
    conversation_id: UUID,
    conversation_data: ConversationUpdate,
    current_user_id: UUID = Depends(get_current_user_id)
):
    """Update a conversation."""
    conversation = await conversation_service.update_conversation(
        conversation_id, current_user_id, conversation_data
    )
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation

@router.delete("/{conversation_id}")
async def delete_conversation(
    conversation_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id)
):
    """Delete a conversation and all its messages."""
    deleted = await conversation_service.delete_conversation(conversation_id, current_user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"status": "success", "message": "Conversation deleted successfully"}

# Message endpoints
@router.post("/{conversation_id}/messages", response_model=ConversationMessage, status_code=status.HTTP_201_CREATED)
async def add_message(
    conversation_id: UUID,
    message_data: ConversationMessageCreate,
    current_user_id: UUID = Depends(get_current_user_id)
):
    """Add a message to a conversation."""
    message = await conversation_service.add_message(conversation_id, message_data, current_user_id)
    return message

@router.get("/{conversation_id}/messages", response_model=ConversationMessageResponse)
async def get_messages(
    conversation_id: UUID,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user_id: UUID = Depends(get_current_user_id)
):
    """Get messages for a conversation."""
    # Verify conversation exists and belongs to user
    conversation = await conversation_service.get_conversation(conversation_id, current_user_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    messages = await conversation_service.get_messages(
        conversation_id, current_user_id, limit=limit, offset=offset
    )
    
    return ConversationMessageResponse(
        messages=messages,
        total_count=conversation.message_count,
        conversation_id=conversation_id,
        page=offset // limit + 1,
        page_size=limit
    )

# AI Chat endpoint
@router.post("/{conversation_id}/chat")
async def chat_with_ai(
    conversation_id: UUID,
    message_data: ConversationMessageCreate,
    current_user_id: UUID = Depends(get_current_user_id)
):
    """Send a message and get an AI response with conversation memory."""
    if message_data.role.value != "user":
        raise HTTPException(status_code=400, detail="Only user messages are allowed for chat endpoint")
    
    # Add user message
    user_message = await conversation_service.add_message(conversation_id, message_data, current_user_id)
    
    # Generate AI response
    try:
        ai_response_content = await conversation_service.generate_ai_response(
            conversation_id, message_data.content, current_user_id
        )
        
        # Add AI response message
        ai_message_data = ConversationMessageCreate(
            content=ai_response_content,
            role="assistant",
            metadata={"generated_at": user_message.timestamp.isoformat()}
        )
        ai_message = await conversation_service.add_message(conversation_id, ai_message_data, current_user_id)
        
        return {
            "user_message": user_message,
            "ai_response": ai_message,
            "conversation_id": conversation_id
        }
    except Exception as e:
        # If AI response fails, still return the user message
        return {
            "user_message": user_message,
            "ai_response": None,
            "error": str(e),
            "conversation_id": conversation_id
        }

# Conversation management endpoints
@router.post("/{conversation_id}/summarize")
async def summarize_conversation(
    conversation_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id)
):
    """Generate or update a conversation summary."""
    conversation = await conversation_service.get_conversation(conversation_id, current_user_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Get all messages for summarization
    messages = await conversation_service.get_messages(conversation_id, current_user_id, limit=1000)
    
    if len(messages) == 0:
        raise HTTPException(status_code=400, detail="Cannot summarize empty conversation")
    
    # Prepare conversation history for AI
    conversation_history = []
    for msg in messages:
        conversation_history.append(f"{msg.role}: {msg.content}")
    
    try:
        # Use conversation skill to generate summary
        from ..ai.kernel_service import kernel_service
        
        ai_variables = {
            "conversation_history": "\n".join(conversation_history),
            "conversation_type": conversation.conversation_type.value,
            "conversation_title": conversation.title
        }
        
        summary = await kernel_service.invoke_semantic_function(
            skill_name="conversation",
            function_name="SummarizeConversation",
            input_text="",
            variables=ai_variables
        )
        
        # Update conversation with new summary
        await conversation_service.update_conversation_summary(conversation_id, current_user_id, str(summary))
        
        return {
            "conversation_id": conversation_id,
            "summary": str(summary),
            "message_count": len(messages),
            "generated_at": conversation.updated_at.isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate summary: {str(e)}")

@router.get("/{conversation_id}/context")
async def get_conversation_context(
    conversation_id: UUID,
    include_messages: int = Query(10, ge=1, le=50),
    current_user_id: UUID = Depends(get_current_user_id)
):
    """Get enhanced conversation context for AI interactions."""
    context = await conversation_service.get_conversation_context(
        conversation_id, current_user_id, include_messages=include_messages
    )
    if not context:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return context