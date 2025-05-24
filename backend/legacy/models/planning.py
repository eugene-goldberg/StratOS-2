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

class ResourceStatus(str, Enum):
    AVAILABLE = "available"
    ALLOCATED = "allocated"
    PARTIALLY_ALLOCATED = "partially_allocated"
    OVER_ALLOCATED = "over_allocated"
    UNAVAILABLE = "unavailable"

class Risk(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    title: str
    description: str
    probability: int  # 1-10
    impact: int  # 1-10
    mitigation_strategy: Optional[str] = None
    
class ResourceAllocation(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    initiative_id: UUID
    action_id: Optional[UUID] = None
    allocated_quantity: float
    allocation_date: datetime = Field(default_factory=datetime.now)
    release_date: Optional[datetime] = None
    notes: Optional[str] = None

class Resource(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str
    type: ResourceType
    quantity: Optional[float] = None
    unit: Optional[str] = None
    cost: Optional[float] = None
    # Advanced tracking fields
    total_quantity: Optional[float] = None  # Total available quantity
    allocated_quantity: Optional[float] = Field(default=0.0)  # Currently allocated
    status: ResourceStatus = ResourceStatus.AVAILABLE
    allocations: List[ResourceAllocation] = []
    availability_start: Optional[datetime] = None
    availability_end: Optional[datetime] = None
    cost_per_unit: Optional[float] = None
    utilization_rate: Optional[float] = None  # Percentage of resource being used
    tags: List[str] = []
    constraints: Optional[str] = None  # Any constraints on resource usage
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
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
    plan_id: UUID # Link to the parent StrategicPlan
    user_id: UUID # Owner of the initiative/plan
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
    user_id: UUID # Owner of the plan
    title: str
    description: Optional[str] = None
    status: PlanStatus = PlanStatus.DRAFT
    time_horizon: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
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
    total_quantity: Optional[float] = None
    availability_start: Optional[datetime] = None
    availability_end: Optional[datetime] = None
    cost_per_unit: Optional[float] = None
    tags: List[str] = []
    constraints: Optional[str] = None

class ResourceUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[ResourceType] = None
    quantity: Optional[float] = None
    unit: Optional[str] = None
    cost: Optional[float] = None
    total_quantity: Optional[float] = None
    availability_start: Optional[datetime] = None
    availability_end: Optional[datetime] = None
    cost_per_unit: Optional[float] = None
    tags: Optional[List[str]] = None
    constraints: Optional[str] = None

class ResourceAllocationCreate(BaseModel):
    resource_id: UUID
    initiative_id: UUID
    action_id: Optional[UUID] = None
    allocated_quantity: float
    notes: Optional[str] = None

class ResourceAllocationRelease(BaseModel):
    allocation_id: UUID
    release_date: Optional[datetime] = None
    notes: Optional[str] = None
    
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
    # linked_strategic_goal should be UUID if it's an ID
    linked_strategic_goal: Optional[UUID] = None 
    owner: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: PlanStatus = PlanStatus.DRAFT
    
class StrategicPlanCreate(BaseModel):
    title: str
    description: Optional[str] = None
    status: PlanStatus = PlanStatus.DRAFT
    time_horizon: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
