"""
Alert and notification models for risk/opportunity flagging
"""
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, ConfigDict, model_validator

class AlertType(str, Enum):
    """Types of alerts"""
    RISK = "risk"
    OPPORTUNITY = "opportunity"
    INSIGHT = "insight"
    THRESHOLD = "threshold"
    ANOMALY = "anomaly"

class AlertSeverity(str, Enum):
    """Alert severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class AlertStatus(str, Enum):
    """Alert status"""
    NEW = "new"
    VIEWED = "viewed"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"

class RiskCategory(str, Enum):
    """Categories of risks"""
    FINANCIAL = "financial"
    OPERATIONAL = "operational"
    STRATEGIC = "strategic"
    COMPLIANCE = "compliance"
    REPUTATIONAL = "reputational"
    MARKET = "market"
    TECHNOLOGY = "technology"
    HUMAN_RESOURCES = "human_resources"

class OpportunityCategory(str, Enum):
    """Categories of opportunities"""
    MARKET_EXPANSION = "market_expansion"
    COST_REDUCTION = "cost_reduction"
    REVENUE_GROWTH = "revenue_growth"
    EFFICIENCY_IMPROVEMENT = "efficiency_improvement"
    INNOVATION = "innovation"
    PARTNERSHIP = "partnership"
    COMPETITIVE_ADVANTAGE = "competitive_advantage"

class Alert(BaseModel):
    """Alert model"""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    alert_type: AlertType
    severity: AlertSeverity
    status: AlertStatus = Field(default=AlertStatus.NEW)
    
    title: str
    description: str
    
    # Risk/Opportunity specific fields
    category: Optional[str] = None  # RiskCategory or OpportunityCategory
    impact_score: Optional[float] = Field(None, ge=0, le=100)  # 0-100
    likelihood_score: Optional[float] = Field(None, ge=0, le=100)  # 0-100
    risk_score: Optional[float] = Field(None, ge=0, le=100)  # Calculated: impact * likelihood / 100
    
    # Source information
    source_type: str  # e.g., "subjective_input", "objective_data", "analysis"
    source_id: Optional[UUID] = None
    source_details: Optional[Dict[str, Any]] = None
    
    # Detection information
    detection_method: str  # e.g., "ai_analysis", "threshold_breach", "pattern_detection"
    detection_details: Optional[Dict[str, Any]] = None
    confidence_score: Optional[float] = Field(None, ge=0, le=100)
    
    # Recommendations
    recommendations: Optional[List[str]] = None
    related_alerts: Optional[List[UUID]] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    viewed_at: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    
    @model_validator(mode='after')
    def calculate_risk_score(self):
        """Auto-calculate risk score for risk alerts"""
        if self.alert_type == AlertType.RISK and self.impact_score and self.likelihood_score:
            self.risk_score = (self.impact_score * self.likelihood_score) / 100
        return self

class AlertCreate(BaseModel):
    """Schema for creating an alert"""
    user_id: UUID
    alert_type: AlertType
    severity: AlertSeverity
    
    title: str
    description: str
    
    category: Optional[str] = None
    impact_score: Optional[float] = Field(None, ge=0, le=100)
    likelihood_score: Optional[float] = Field(None, ge=0, le=100)
    
    source_type: str
    source_id: Optional[UUID] = None
    source_details: Optional[Dict[str, Any]] = None
    
    detection_method: str
    detection_details: Optional[Dict[str, Any]] = None
    confidence_score: Optional[float] = Field(None, ge=0, le=100)
    
    recommendations: Optional[List[str]] = None
    related_alerts: Optional[List[UUID]] = None

class AlertUpdate(BaseModel):
    """Schema for updating an alert"""
    status: Optional[AlertStatus] = None
    severity: Optional[AlertSeverity] = None
    
    title: Optional[str] = None
    description: Optional[str] = None
    
    impact_score: Optional[float] = Field(None, ge=0, le=100)
    likelihood_score: Optional[float] = Field(None, ge=0, le=100)
    
    recommendations: Optional[List[str]] = None
    related_alerts: Optional[List[UUID]] = None

class AlertFilter(BaseModel):
    """Schema for filtering alerts"""
    user_id: Optional[UUID] = None
    alert_type: Optional[AlertType] = None
    severity: Optional[List[AlertSeverity]] = None
    status: Optional[List[AlertStatus]] = None
    category: Optional[str] = None
    
    min_risk_score: Optional[float] = Field(None, ge=0, le=100)
    max_risk_score: Optional[float] = Field(None, ge=0, le=100)
    
    source_type: Optional[str] = None
    detection_method: Optional[str] = None
    
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    
    limit: int = Field(default=50, le=100)
    offset: int = Field(default=0, ge=0)

class RiskOpportunityDetectionConfig(BaseModel):
    """Configuration for risk/opportunity detection"""
    # Thresholds
    min_confidence_score: float = Field(default=70.0, ge=0, le=100)
    
    # Risk thresholds
    risk_impact_threshold: float = Field(default=50.0, ge=0, le=100)
    risk_likelihood_threshold: float = Field(default=40.0, ge=0, le=100)
    
    # Opportunity thresholds
    opportunity_impact_threshold: float = Field(default=60.0, ge=0, le=100)
    opportunity_likelihood_threshold: float = Field(default=50.0, ge=0, le=100)
    
    # Analysis settings
    lookback_days: int = Field(default=7, ge=1, le=90)
    include_subjective: bool = True
    include_objective: bool = True
    include_swot: bool = True
    
    # Pattern detection
    detect_trends: bool = True
    detect_anomalies: bool = True
    detect_correlations: bool = True