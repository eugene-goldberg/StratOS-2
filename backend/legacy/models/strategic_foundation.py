from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from uuid import UUID, uuid4

class Purpose(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    statement: str
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class Vision(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    statement: str
    description: Optional[str] = None
    time_horizon: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class Value(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str
    description: str
    examples: Optional[List[str]] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class StrategicGoal(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    title: str
    description: str
    time_frame: Optional[str] = None
    metrics: Optional[List[str]] = None
    target_value: Optional[float] = None
    current_value: Optional[float] = None
    parent_goal_id: Optional[UUID] = None  # For hierarchical goal organization
    sub_goals: List['StrategicGoal'] = []  # Child goals
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class NorthStar(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    purpose: Purpose
    vision: Vision
    values: List[Value] = []
    strategic_goals: List[StrategicGoal] = []
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class NorthStarCreate(BaseModel):
    purpose: str
    purpose_description: Optional[str] = None
    vision: str
    vision_description: Optional[str] = None
    vision_time_horizon: Optional[str] = None
    values: List[dict] = []
    strategic_goals: List[dict] = []

class NorthStarUpdate(BaseModel):
    purpose: Optional[str] = None
    purpose_description: Optional[str] = None
    vision: Optional[str] = None
    vision_description: Optional[str] = None
    vision_time_horizon: Optional[str] = None

# Enable forward references for self-referential model
StrategicGoal.model_rebuild()