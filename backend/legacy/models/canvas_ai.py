"""
Canvas AI Models - Data models for AI-powered canvas structuring and analysis.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from uuid import UUID, uuid4
from pydantic import BaseModel, Field
from enum import Enum


class NodeType(str, Enum):
    """Available node types for strategic canvas."""
    BASIC = "basic"
    CEO_LOG = "ceoLog"
    DATA_SNIPPET = "dataSnippet"
    SWOT_S = "swotS"
    SWOT_W = "swotW"
    SWOT_O = "swotO"
    SWOT_T = "swotT"
    RISK = "risk"
    OPPORTUNITY = "opportunity"
    IMAGE = "image"
    # B2 AI Algorithm node types
    GOAL = "goal"
    INITIATIVE = "initiative"
    CHALLENGE = "challenge"
    CAPABILITY = "capability"
    METRIC = "metric"


class ConfidenceLevel(str, Enum):
    """Confidence levels for AI suggestions."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Priority(str, Enum):
    """Priority levels for recommendations."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class RelationshipType(str, Enum):
    """Types of relationships between canvas nodes."""
    CAUSAL = "causal"
    SUPPORTING = "supporting"
    DEPENDENCY = "dependency"
    ALIGNMENT = "alignment"
    CONFLICT = "conflict"
    HIERARCHICAL = "hierarchical"
    TEMPORAL = "temporal"
    RISK_MITIGATION = "risk_mitigation"
    OPPORTUNITY_ENABLEMENT = "opportunity_enablement"


class ConnectionType(str, Enum):
    """Connection types for B2 AI algorithms."""
    SUPPORTS = "supports"
    ENABLES = "enables"
    BLOCKS = "blocks"
    DEPENDS_ON = "depends_on"
    MEASURES = "measures"
    ADDRESSES = "addresses"
    CONFLICTS_WITH = "conflicts_with"
    INFORMS = "informs"


class ThemeImportance(str, Enum):
    """Theme importance levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class OptimizationPriority(str, Enum):
    """Optimization recommendation priorities."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


# Text Structuring Models
class NodeSuggestion(BaseModel):
    """Suggestion for structuring text into a canvas node."""
    suggested_node_type: NodeType
    title: str
    content: str
    rationale: str
    confidence: float = Field(ge=0.0, le=1.0)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ConnectionSuggestion(BaseModel):
    """Suggestion for connecting two nodes."""
    from_node_id: str
    to_node_id: str
    connection_type: ConnectionType
    rationale: str
    confidence: float = Field(ge=0.0, le=1.0)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TextStructureAnalysis(BaseModel):
    """Analysis of unstructured text for structuring."""
    content_type: str
    key_concepts: List[str]
    strategic_relevance: str


class TextStructureSuggestion(BaseModel):
    """Complete text structuring suggestion response."""
    analysis: TextStructureAnalysis
    suggestions: List[NodeSuggestion]
    connections: List[ConnectionSuggestion]
    recommendations: Dict[str, Union[str, List[str]]]


# Connection Analysis Models
class CanvasNode(BaseModel):
    """Canvas node representation for AI analysis."""
    id: str
    title: str
    content: str
    type: NodeType
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CanvasEdge(BaseModel):
    """Canvas edge representation for AI analysis."""
    id: str
    source: str
    target: str
    label: Optional[str] = None
    relationship_type: Optional[RelationshipType] = None


class CanvasData(BaseModel):
    """Complete canvas data for AI analysis."""
    nodes: List[CanvasNode]
    edges: List[CanvasEdge]
    metadata: Dict[str, Any] = Field(default_factory=dict)


class NodeConnectionSuggestion(BaseModel):
    """Detailed connection suggestion between specific nodes."""
    source_node: CanvasNode
    target_node: CanvasNode
    relationship_type: RelationshipType
    relationship_label: str
    confidence: float = Field(ge=0.0, le=1.0)
    rationale: str
    strategic_impact: str
    priority: Priority
    framework_basis: Optional[str] = None


class ConnectionCluster(BaseModel):
    """Cluster of related nodes."""
    theme: str
    nodes: List[str]
    description: str


class ConnectionPatterns(BaseModel):
    """Analysis of connection patterns in the canvas."""
    clusters: List[ConnectionCluster]
    orphaned_nodes: List[str]
    hub_nodes: List[str]
    strategic_flows: List[str]


class ConnectionAnalysis(BaseModel):
    """Complete connection analysis response."""
    total_nodes: int
    existing_connections: int
    connectivity_score: float
    main_themes: List[str]
    connection_gaps: List[str]


class ConnectionRecommendation(BaseModel):
    """High-level recommendation for connections."""
    action: str
    rationale: str
    impact: str


class MissingElement(BaseModel):
    """Suggestion for missing canvas element."""
    element_type: NodeType
    purpose: str
    suggested_content: str


class StrategicInsight(BaseModel):
    """Strategic insight derived from connection analysis."""
    insight: str
    supporting_evidence: List[str]
    actionable_implications: List[str]


class ConnectionSuggestionResponse(BaseModel):
    """Complete connection analysis and suggestions."""
    analysis: ConnectionAnalysis
    suggested_connections: List[NodeConnectionSuggestion]
    connection_patterns: ConnectionPatterns
    recommendations: Dict[str, List[ConnectionRecommendation]]
    strategic_insights: List[StrategicInsight]


# Theme Analysis Models
class ContentTheme(BaseModel):
    """Identified theme in canvas content."""
    theme_name: str
    frequency: int
    nodes_containing: List[str]
    key_concepts: List[str]
    strategic_significance: str
    coverage_assessment: str
    related_frameworks: List[str]


class StrategicElement(BaseModel):
    """Strategic element contributing to a theme."""
    element_type: str
    element_title: str
    contribution_to_theme: str


class StrategicTheme(BaseModel):
    """High-level strategic theme."""
    theme_name: str
    sub_themes: List[str]
    strength: str
    strategic_elements: List[StrategicElement]
    theme_coherence: str
    gaps_in_theme: List[str]


class ThemePattern(BaseModel):
    """Pattern identified in thematic analysis."""
    pattern_type: str
    description: str
    instances: Optional[int] = None
    assessment: str
    recommendation: Optional[str] = None


class ThematicInsight(BaseModel):
    """Insight derived from thematic analysis."""
    insight: str
    supporting_themes: List[str]
    evidence: List[str]
    implications: List[str]
    recommended_actions: List[str]


class ThematicGap(BaseModel):
    """Missing thematic element."""
    missing_theme: str
    importance: Priority
    gap_description: str
    suggested_additions: List[Dict[str, str]]


class ThematicBalance(BaseModel):
    """Balance analysis across different dimensions."""
    dimension_name: str
    scores: Dict[str, int]
    assessment: str


class ThemeAnalysisResponse(BaseModel):
    """Complete theme analysis response."""
    executive_summary: Dict[str, Union[str, List[str]]]
    content_themes: List[ContentTheme]
    strategic_themes: List[StrategicTheme]
    pattern_analysis: Dict[str, List[ThemePattern]]
    thematic_insights: List[ThematicInsight]
    thematic_gaps: List[ThematicGap]
    thematic_balance: Dict[str, ThematicBalance]
    thematic_recommendations: Dict[str, List[Dict[str, Any]]]
    strategic_narrative: Dict[str, str]


# Canvas Optimization Models
class CompletenessAssessment(BaseModel):
    """Assessment of canvas completeness against frameworks."""
    framework_name: str
    score: int = Field(ge=0, le=100)
    details: Dict[str, Any]
    missing_elements: List[str]


class ContentImprovement(BaseModel):
    """Suggested improvement to existing content."""
    node_id: str
    current_issue: str
    suggested_improvement: str
    rationale: str


class CriticalAddition(BaseModel):
    """Critical element to add to canvas."""
    element_type: NodeType
    title: str
    content: str
    rationale: str
    priority: Priority
    estimated_impact: str


class ImplementationAction(BaseModel):
    """Specific action in implementation roadmap."""
    action: str
    effort: str
    impact: str
    timeframe: str


class SuccessMetric(BaseModel):
    """Success metric for optimization."""
    metric: str
    current: Union[int, float, str]
    target: Union[int, float, str]
    measurement: str


class CanvasOptimizationResponse(BaseModel):
    """Complete canvas optimization analysis."""
    executive_summary: Dict[str, Any]
    completeness_assessment: Dict[str, CompletenessAssessment]
    structural_analysis: Dict[str, Any]
    content_quality: Dict[str, Any]
    strategic_alignment: Dict[str, Any]
    optimization_recommendations: Dict[str, List[Any]]
    implementation_roadmap: Dict[str, List[ImplementationAction]]
    success_metrics: Dict[str, List[SuccessMetric]]






# B2 AI Algorithm Models
class ThemeCluster(BaseModel):
    """Theme cluster for theme identification."""
    theme_name: str
    description: str
    related_nodes: List[str]
    confidence: float = Field(ge=0.0, le=1.0)
    strategic_importance: ThemeImportance
    metadata: Dict[str, Any] = Field(default_factory=dict)


class OptimizationRecommendation(BaseModel):
    """Optimization recommendation."""
    category: str
    recommendation: str
    rationale: str
    priority: OptimizationPriority
    confidence: float = Field(ge=0.0, le=1.0)
    implementation_steps: List[str] = Field(default_factory=list)
    estimated_effort: str = "medium"
    expected_impact: str = "medium"
    metadata: Dict[str, Any] = Field(default_factory=dict)


# B2 Request Models
class ThemeIdentificationRequest(BaseModel):
    """Request for theme identification analysis."""
    canvas_elements: Dict[str, Any]
    analysis_scope: str = "comprehensive"
    preferences: Dict[str, Any] = Field(default_factory=dict)


class ThemeAnalysisRequest(BaseModel):
    """Request for theme analysis (alias for compatibility)."""
    canvas_elements: Dict[str, Any]
    analysis_scope: str = "comprehensive"
    preferences: Dict[str, Any] = Field(default_factory=dict)


# Updated request models for B2
class TextStructureRequest(BaseModel):
    """Request for text structuring analysis."""
    text: str
    canvas_context: Dict[str, Any] = Field(default_factory=dict)
    preferences: Dict[str, Any] = Field(default_factory=dict)


class ConnectionAnalysisRequest(BaseModel):
    """Request for connection analysis."""
    nodes: List[Dict[str, Any]]
    canvas_context: Dict[str, Any] = Field(default_factory=dict)
    analysis_depth: str = "standard"


class CanvasOptimizationRequest(BaseModel):
    """Request for canvas optimization."""
    current_canvas: Dict[str, Any]
    optimization_goals: List[str] = Field(default_factory=list)
    strategic_context: Dict[str, Any] = Field(default_factory=dict)


# Response wrapper
class AIAnalysisResponse(BaseModel):
    """Generic AI analysis response wrapper."""
    analysis_id: UUID = Field(default_factory=uuid4)
    analysis_type: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    suggestions: List[Union[NodeSuggestion, ConnectionSuggestion, ThemeCluster, OptimizationRecommendation]] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0, default=0.0)
    processing_time: float = 0.0
    metadata: Dict[str, Any] = Field(default_factory=dict)
    user_id: Optional[UUID] = None
    canvas_id: Optional[str] = None
    success: bool = True
    message: Optional[str] = None
    data: Optional[Union[
        TextStructureSuggestion,
        ConnectionSuggestionResponse, 
        ThemeAnalysisResponse,
        CanvasOptimizationResponse
    ]] = None
    execution_time_ms: Optional[int] = None