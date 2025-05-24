from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime
from uuid import UUID, uuid4
from enum import Enum

class LogEntryType(str, Enum):
    IDEA = "idea"
    OBSERVATION = "observation"
    CONCERN = "concern"
    REFLECTION = "reflection"
    QUESTION = "question"
    OTHER = "other"

class StrategyReferenceType(str, Enum):
    PURPOSE = "purpose"
    VISION = "vision"
    VALUE = "value"
    GOAL = "goal"
    CUSTOM = "custom"

class LogEntryTag(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str
    type: StrategyReferenceType = StrategyReferenceType.CUSTOM
    reference_id: Optional[UUID] = None  # If it references a strategic element
    strategic_element_data: Optional[Dict[str, Any]] = None  # Cache of referenced element

class LogEntry(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    content: str
    entry_type: LogEntryType = LogEntryType.OTHER
    tags: List[LogEntryTag] = []
    sentiment: Optional[float] = None  # -1.0 to 1.0 (negative to positive)
    ai_generated_tags: List[str] = []
    ai_summary: Optional[str] = None
    ai_insights: Optional[List[str]] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    user_id: UUID

class LogEntryCreate(BaseModel):
    content: str
    entry_type: LogEntryType = LogEntryType.OTHER
    tags: List[str] = []
    
class LogEntryUpdate(BaseModel):
    content: Optional[str] = None
    entry_type: Optional[LogEntryType] = None
    tags: Optional[List[str]] = None

class CanvasElement(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    element_type: str  # "text", "image", "connection", etc.
    content: Dict[str, Any]
    position: Dict[str, float]
    style: Optional[Dict[str, Any]] = None
    connections: List[UUID] = []
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
class StrategicCanvas(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    title: str
    description: Optional[str] = None
    elements: List[CanvasElement] = []
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    user_id: UUID

class CanvasElementCreate(BaseModel):
    element_type: str
    content: Dict[str, Any]
    position: Dict[str, float]
    style: Optional[Dict[str, Any]] = None
    connections: List[str] = []

class StrategicCanvasCreate(BaseModel):
    title: str
    description: Optional[str] = None