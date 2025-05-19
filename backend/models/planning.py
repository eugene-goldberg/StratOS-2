from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from uuid import UUID, uuid4
from enum import Enum

class PlanStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"
    ABANDONED = "abandoned"

class ActionStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    DELAYED = "delayed"

class InitiativeType(str, Enum):
    STRATEGIC = "strategic"
    TACTICAL = "tactical"
    OPERATIONAL = "operational"
    TRANSFORMATIONAL = "transformational"

class ResourceType(str, Enum):
    FINANCIAL = "financial"
    HUMAN = "human"
    TECHNOLOGY = "technology"
    PHYSICAL = "physical"
    TIME = "time"
    OTHER = "other"

class Risk(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    title: str
    description: str
    probability: int  # 1-10
    impact: int  # 1-10
    mitigation_strategy: Optional[str] = None
    
class Resource(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str
    type: ResourceType
    quantity: Optional[float] = None
    unit: Optional[str] = None
    cost: Optional[float] = None
    
class Action(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    title: str
    description: Optional[str] = None
    status: ActionStatus = ActionStatus.NOT_STARTED
    owner: Optional[str] = None
    start_date: Optional[date] = None
    due_date: Optional[date] = None
    dependencies: List[UUID] = []
    resources: List[Resource] = []
    progress: Optional[int] = None  # 0-100%
    risks: List[Risk] = []
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class Initiative(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    title: str
    description: str
    initiative_type: InitiativeType
    status: PlanStatus = PlanStatus.DRAFT
    linked_strategic_goal: Optional[UUID] = None
    alignment_score: Optional[int] = None  # 1-10, how well it aligns with strategic goals
    feasibility_score: Optional[int] = None  # 1-10
    impact_score: Optional[int] = None  # 1-10
    owner: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    actions: List[Action] = []
    risks: List[Risk] = []
    resources: List[Resource] = []
    key_metrics: List[Dict[str, Any]] = []
    why_alignment: Optional[str] = None  # Alignment with purpose/vision/values
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class StrategicPlan(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    title: str
    description: Optional[str] = None
    status: PlanStatus = PlanStatus.DRAFT
    time_horizon: Optional[str] = None
    initiatives: List[Initiative] = []
    overall_alignment_score: Optional[float] = None
    overall_feasibility_score: Optional[float] = None
    overall_impact_score: Optional[float] = None
    ai_recommendations: List[str] = []
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class ActionCreate(BaseModel):
    title: str
    description: Optional[str] = None
    owner: Optional[str] = None
    start_date: Optional[date] = None
    due_date: Optional[date] = None
    dependencies: List[str] = []
    
class ResourceCreate(BaseModel):
    name: str
    type: ResourceType
    quantity: Optional[float] = None
    unit: Optional[str] = None
    cost: Optional[float] = None
    
class RiskCreate(BaseModel):
    title: str
    description: str
    probability: int
    impact: int
    mitigation_strategy: Optional[str] = None

class InitiativeCreate(BaseModel):
    title: str
    description: str
    initiative_type: InitiativeType
    linked_strategic_goal: Optional[str] = None
    owner: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    
class StrategicPlanCreate(BaseModel):
    title: str
    description: Optional[str] = None
    time_horizon: Optional[str] = None