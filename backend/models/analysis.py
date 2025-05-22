from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from uuid import UUID, uuid4
from enum import Enum

class InsightType(str, Enum):
    SWOT = "swot"
    CORRELATION = "correlation"
    TREND = "trend"
    ANOMALY = "anomaly"
    OPPORTUNITY = "opportunity"
    RISK = "risk"
    RECOMMENDATION = "recommendation"
    OTHER = "other"

class InsightSource(str, Enum):
    SUBJECTIVE = "subjective"
    OBJECTIVE = "objective"
    COMBINED = "combined"
    AI_GENERATED = "ai_generated"

class LinkageType(str, Enum):
    CORRELATION = "correlation"
    CONTRADICTION = "contradiction"
    EMERGING_THEME = "emerging_theme"

class SWOTCategory(str, Enum):
    STRENGTH = "strength"
    WEAKNESS = "weakness"
    OPPORTUNITY = "opportunity"
    THREAT = "threat"

class AnalysisSessionStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ABANDONED = "abandoned"

class AnalysisSessionType(str, Enum):
    SWOT = "swot"
    TOWS = "tows"
    GUIDED_SWOT = "guided_swot"
    GUIDED_TOWS = "guided_tows"

class TOWSCellType(str, Enum):
    SO = "SO"  # Strengths-Opportunities
    WO = "WO"  # Weaknesses-Opportunities  
    ST = "ST"  # Strengths-Threats
    WT = "WT"  # Weaknesses-Threats

class SWOTItem(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    category: SWOTCategory
    content: str
    source: InsightSource
    source_references: List[Dict[str, Any]] = []  # References to log entries, data points, etc.
    impact_score: Optional[int] = None  # 1-10
    certainty_score: Optional[int] = None  # 1-10
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class SWOTAnalysis(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    user_id: UUID  # Added user_id for ownership and partitioning
    title: str
    description: Optional[str] = None
    items: List[SWOTItem] = []
    tows_strategies: List[Dict[str, Any]] = []  # TOWS matrix strategies
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class SWOTItemCreate(BaseModel):
    category: SWOTCategory
    content: str
    source: InsightSource
    source_references: List[Dict[str, Any]] = []
    impact_score: Optional[int] = None
    certainty_score: Optional[int] = None

class SWOTAnalysisCreate(BaseModel):
    title: str
    description: Optional[str] = None

class SOLinkage(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    topic_context: Optional[str] = None
    subjective_item_id: Optional[str] = None # Could be LogEntry ID or reference to a snippet
    subjective_snippet_text: str
    objective_item_id: Optional[str] = None # Could be DataSet ID, DataPoint ID, or chunk ID
    objective_snippet_text: str
    objective_item_title: Optional[str] = None # e.g., title of the dataset
    linkage_type: LinkageType # "correlation", "contradiction", "emerging_theme"
    ai_summary_of_linkage: str
    ai_prompt_for_ceo: str
    created_at: datetime = Field(default_factory=datetime.now)
    # Optional: user feedback on relevance, user-added notes

class SOLinkageCreate(BaseModel): # For creating a new linkage record
    user_id: UUID
    topic_context: Optional[str] = None
    subjective_item_id: Optional[str] = None
    subjective_snippet_text: str
    objective_item_id: Optional[str] = None
    objective_snippet_text: str
    objective_item_title: Optional[str] = None
    linkage_type: LinkageType
    ai_summary_of_linkage: str
    ai_prompt_for_ceo: str

class SOLinkageResponse(SOLinkage): # For API responses
    pass

class Insight(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    user_id: UUID  # Added user_id for ownership and partitioning
    title: str
    description: str
    insight_type: InsightType
    source: InsightSource
    source_references: List[Dict[str, Any]] = []
    confidence_score: Optional[float] = None  # 0.0 to 1.0
    impact_score: Optional[int] = None  # 1-10
    linked_strategic_goals: List[UUID] = []
    supporting_data: Optional[Dict[str, Any]] = None
    visualization_data: Optional[Dict[str, Any]] = None
    ai_explanation: Optional[str] = None
    ai_recommendations: List[str] = []
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class InsightCreate(BaseModel):
    title: str
    description: str
    insight_type: InsightType
    source: InsightSource
    source_references: List[Dict[str, Any]] = []
    confidence_score: Optional[float] = None
    impact_score: Optional[int] = None
    linked_strategic_goals: List[str] = []
    supporting_data: Optional[Dict[str, Any]] = None
    visualization_data: Optional[Dict[str, Any]] = None

# Analysis Session Models for Interactive SWOT/TOWS

class SessionStepState(BaseModel):
    """State of a specific step in guided analysis"""
    step_id: str  # e.g., "swot_strengths", "tows_so_cell"
    is_completed: bool = False
    items_count: int = 0
    ai_guidance_requested: bool = False
    last_guidance_at: Optional[datetime] = None
    completion_percentage: float = 0.0

class AnalysisSession(BaseModel):
    """Interactive analysis session for guided SWOT/TOWS"""
    id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    session_type: AnalysisSessionType
    status: AnalysisSessionStatus = AnalysisSessionStatus.ACTIVE
    title: str
    description: Optional[str] = None
    
    # Strategic Context
    topic: str
    company_name: Optional[str] = None
    strategic_context: Optional[Dict[str, Any]] = None  # North Star elements, etc.
    
    # Session Progress
    current_step: str  # Current step identifier
    completed_steps: List[str] = []
    step_states: Dict[str, SessionStepState] = {}
    
    # Analysis Data
    swot_items: List[SWOTItem] = []
    tows_strategies: List[Dict[str, Any]] = []
    generated_insights: List[str] = []
    
    # Session Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    last_interaction_at: datetime = Field(default_factory=datetime.now)
    estimated_completion_time: Optional[int] = None  # minutes
    
    # AI Guidance History
    guidance_history: List[Dict[str, Any]] = []

class AnalysisSessionCreate(BaseModel):
    """Request model for creating new analysis session"""
    session_type: AnalysisSessionType
    title: str
    description: Optional[str] = None
    topic: str
    company_name: Optional[str] = None

class AnalysisSessionUpdate(BaseModel):
    """Request model for updating analysis session"""
    status: Optional[AnalysisSessionStatus] = None
    current_step: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None

class GuidanceRequest(BaseModel):
    """Request for AI guidance during analysis session"""
    session_id: UUID
    step_id: str  # Which step needs guidance
    context: Optional[Dict[str, Any]] = None  # Additional context
    
class GuidanceResponse(BaseModel):
    """AI guidance response for analysis session"""
    session_id: UUID
    step_id: str
    guiding_questions: List[str] = []
    suggestions: List[str] = []
    examples: List[str] = []
    next_steps: List[str] = []
    completion_guidance: Optional[str] = None
    estimated_time_remaining: Optional[int] = None  # minutes
