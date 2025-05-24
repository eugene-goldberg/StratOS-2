from pydantic import BaseModel, Field
from uuid import UUID, uuid4
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum

class ConversationType(str, Enum):
    GENERAL = "general"
    STRATEGIC_PLANNING = "strategic_planning"
    ANALYSIS_SUPPORT = "analysis_support"
    CANVAS_COLLABORATION = "canvas_collaboration"
    CEO_LOG_DISCUSSION = "ceo_log_discussion"

class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

class ConversationStatus(str, Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    PAUSED = "paused"

# Base models for API requests
class ConversationCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    conversation_type: ConversationType = ConversationType.GENERAL
    description: Optional[str] = Field(None, max_length=1000)
    initial_context: Optional[Dict[str, Any]] = None

class ConversationUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    status: Optional[ConversationStatus] = None
    context: Optional[Dict[str, Any]] = None

class ConversationMessageCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=10000)
    role: MessageRole = MessageRole.USER
    metadata: Optional[Dict[str, Any]] = None

# Core models
class ConversationMessage(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    conversation_id: UUID
    role: MessageRole
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)
    
    class Config:
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat()
        }

class Conversation(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    title: str
    description: Optional[str] = None
    conversation_type: ConversationType = ConversationType.GENERAL
    status: ConversationStatus = ConversationStatus.ACTIVE
    
    # Context and memory
    context: Dict[str, Any] = Field(default_factory=dict)
    summary: Optional[str] = None
    
    # Relationships
    related_analysis_session_id: Optional[UUID] = None
    related_canvas_id: Optional[UUID] = None
    related_log_entry_ids: List[UUID] = Field(default_factory=list)
    
    # Statistics
    message_count: int = 0
    last_message_at: Optional[datetime] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat()
        }

# Response models
class ConversationResponse(BaseModel):
    conversation: Conversation
    recent_messages: List[ConversationMessage] = Field(default_factory=list)
    
class ConversationListResponse(BaseModel):
    conversations: List[Conversation]
    total_count: int
    page: int
    page_size: int

class ConversationMessageResponse(BaseModel):
    messages: List[ConversationMessage]
    total_count: int
    conversation_id: UUID
    page: int
    page_size: int

# AI Integration models
class ConversationContext(BaseModel):
    """Enhanced context for AI interactions including conversation memory"""
    conversation_id: UUID
    user_id: UUID
    conversation_type: ConversationType
    
    # Recent conversation history
    recent_messages: List[ConversationMessage] = Field(default_factory=list)
    conversation_summary: Optional[str] = None
    
    # Strategic context
    north_star_context: Optional[Dict[str, Any]] = None
    recent_log_entries: List[Dict[str, Any]] = Field(default_factory=list)
    active_analysis_sessions: List[Dict[str, Any]] = Field(default_factory=list)
    active_canvas_data: Optional[Dict[str, Any]] = None
    
    # User preferences and patterns
    user_preferences: Dict[str, Any] = Field(default_factory=dict)
    conversation_patterns: Dict[str, Any] = Field(default_factory=dict)

class AIResponseWithMemory(BaseModel):
    """AI response that includes memory updates"""
    response_content: str
    conversation_id: UUID
    should_update_summary: bool = False
    new_summary: Optional[str] = None
    context_updates: Dict[str, Any] = Field(default_factory=dict)
    related_entities: List[Dict[str, Any]] = Field(default_factory=list)