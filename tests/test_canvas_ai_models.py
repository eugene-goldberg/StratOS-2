"""
Test suite for Canvas AI models and data structures.
"""

import pytest
from pydantic import ValidationError
from uuid import uuid4, UUID
from datetime import datetime
from typing import Dict, List, Any

from backend.models.canvas_ai import (
    # Enums
    NodeType, ConfidenceLevel, Priority, RelationshipType,
    # Text Structuring Models
    NodeSuggestion, ConnectionSuggestion, TextStructureAnalysis, TextStructureSuggestion,
    # Connection Analysis Models
    CanvasNode, CanvasEdge, CanvasData, NodeConnectionSuggestion, ConnectionCluster,
    ConnectionPatterns, ConnectionAnalysis, ConnectionRecommendation, MissingElement,
    StrategicInsight, ConnectionSuggestionResponse,
    # Theme Analysis Models
    ContentTheme, StrategicElement, StrategicTheme, ThemePattern, ThematicInsight,
    ThematicGap, ThematicBalance, ThemeAnalysisResponse,
    # Optimization Models
    CompletenessAssessment, ContentImprovement, CriticalAddition, ImplementationAction,
    SuccessMetric, CanvasOptimizationResponse,
    # Request Models
    TextStructureRequest, ConnectionAnalysisRequest, ThemeAnalysisRequest,
    CanvasOptimizationRequest,
    # Response Models
    AIAnalysisResponse
)


class TestEnums:
    """Test enum types."""
    
    def test_node_type_enum(self):
        """Test NodeType enum values."""
        assert NodeType.BASIC == "basic"
        assert NodeType.CEO_LOG == "ceoLog"
        assert NodeType.SWOT_S == "swotS"
        assert len(NodeType) == 10  # Ensure all types are defined
    
    def test_confidence_level_enum(self):
        """Test ConfidenceLevel enum values."""
        assert ConfidenceLevel.LOW == "low"
        assert ConfidenceLevel.MEDIUM == "medium"
        assert ConfidenceLevel.HIGH == "high"
    
    def test_priority_enum(self):
        """Test Priority enum values."""
        assert Priority.LOW == "low"
        assert Priority.MEDIUM == "medium"
        assert Priority.HIGH == "high"
    
    def test_relationship_type_enum(self):
        """Test RelationshipType enum values."""
        assert RelationshipType.CAUSAL == "causal"
        assert RelationshipType.SUPPORTING == "supporting"
        assert len(RelationshipType) == 9  # Ensure all types are defined


class TestTextStructuringModels:
    """Test text structuring related models."""
    
    def test_node_suggestion_creation(self):
        """Test NodeSuggestion model creation."""
        suggestion = NodeSuggestion(
            suggested_node_type=NodeType.BASIC,
            title="Test Node",
            content="Test content",
            rationale="This is a test",
            confidence=0.85,
            metadata={"category": "test"}
        )
        
        assert suggestion.suggested_node_type == NodeType.BASIC
        assert suggestion.title == "Test Node"
        assert suggestion.confidence == 0.85
        assert suggestion.metadata["category"] == "test"
    
    def test_node_suggestion_validation(self):
        """Test NodeSuggestion validation rules."""
        # Test invalid confidence (out of range)
        with pytest.raises(ValidationError):
            NodeSuggestion(
                suggested_node_type=NodeType.BASIC,
                title="Test",
                content="Content",
                rationale="Rationale",
                confidence=1.5  # Invalid: > 1.0
            )
        
        with pytest.raises(ValidationError):
            NodeSuggestion(
                suggested_node_type=NodeType.BASIC,
                title="Test",
                content="Content", 
                rationale="Rationale",
                confidence=-0.1  # Invalid: < 0.0
            )
    
    def test_connection_suggestion_creation(self):
        """Test ConnectionSuggestion model creation."""
        connection = ConnectionSuggestion(
            node1_title="Node 1",
            node2_title="Node 2",
            relationship="supports",
            rationale="Node 1 supports Node 2"
        )
        
        assert connection.node1_title == "Node 1"
        assert connection.relationship == "supports"
    
    def test_text_structure_analysis_creation(self):
        """Test TextStructureAnalysis model creation."""
        analysis = TextStructureAnalysis(
            content_type="strategic_planning",
            key_concepts=["goals", "initiatives", "metrics"],
            strategic_relevance="High relevance to strategic planning"
        )
        
        assert analysis.content_type == "strategic_planning"
        assert len(analysis.key_concepts) == 3
        assert "goals" in analysis.key_concepts
    
    def test_text_structure_suggestion_creation(self):
        """Test complete TextStructureSuggestion model."""
        analysis = TextStructureAnalysis(
            content_type="goals",
            key_concepts=["revenue", "growth"],
            strategic_relevance="Core strategic objective"
        )
        
        suggestion = NodeSuggestion(
            suggested_node_type=NodeType.BASIC,
            title="Revenue Growth",
            content="Increase revenue by 25%",
            rationale="Clear strategic goal",
            confidence=0.9
        )
        
        complete_suggestion = TextStructureSuggestion(
            analysis=analysis,
            suggestions=[suggestion],
            connections=[],
            recommendations={"primary_action": "Create goal node"}
        )
        
        assert complete_suggestion.analysis.content_type == "goals"
        assert len(complete_suggestion.suggestions) == 1
        assert complete_suggestion.suggestions[0].confidence == 0.9


class TestConnectionAnalysisModels:
    """Test connection analysis related models."""
    
    def test_canvas_node_creation(self):
        """Test CanvasNode model creation."""
        node = CanvasNode(
            id="node_1",
            title="Strategic Goal",
            content="Increase market share",
            type=NodeType.BASIC,
            metadata={"priority": "high"}
        )
        
        assert node.id == "node_1"
        assert node.type == NodeType.BASIC
        assert node.metadata["priority"] == "high"
    
    def test_canvas_edge_creation(self):
        """Test CanvasEdge model creation."""
        edge = CanvasEdge(
            id="edge_1",
            source="node_1",
            target="node_2",
            label="supports",
            relationship_type=RelationshipType.SUPPORTING
        )
        
        assert edge.source == "node_1"
        assert edge.relationship_type == RelationshipType.SUPPORTING
    
    def test_canvas_data_creation(self):
        """Test CanvasData model creation."""
        node1 = CanvasNode(
            id="node_1",
            title="Goal 1",
            content="Content 1",
            type=NodeType.BASIC
        )
        
        node2 = CanvasNode(
            id="node_2", 
            title="Goal 2",
            content="Content 2",
            type=NodeType.BASIC
        )
        
        edge = CanvasEdge(
            id="edge_1",
            source="node_1",
            target="node_2"
        )
        
        canvas_data = CanvasData(
            nodes=[node1, node2],
            edges=[edge],
            metadata={"canvas_id": "test_canvas"}
        )
        
        assert len(canvas_data.nodes) == 2
        assert len(canvas_data.edges) == 1
        assert canvas_data.metadata["canvas_id"] == "test_canvas"
    
    def test_node_connection_suggestion_creation(self):
        """Test NodeConnectionSuggestion model creation."""
        source_node = CanvasNode(
            id="node_1",
            title="Strength",
            content="Strong brand",
            type=NodeType.SWOT_S
        )
        
        target_node = CanvasNode(
            id="node_2",
            title="Opportunity", 
            content="Market expansion",
            type=NodeType.SWOT_O
        )
        
        suggestion = NodeConnectionSuggestion(
            source_node=source_node,
            target_node=target_node,
            relationship_type=RelationshipType.SUPPORTING,
            relationship_label="enables",
            confidence=0.8,
            rationale="Strong brand enables market expansion",
            strategic_impact="Leverages strength for opportunity",
            priority=Priority.HIGH,
            framework_basis="SWOT analysis"
        )
        
        assert suggestion.relationship_type == RelationshipType.SUPPORTING
        assert suggestion.confidence == 0.8
        assert suggestion.priority == Priority.HIGH
        assert suggestion.framework_basis == "SWOT analysis"


class TestThemeAnalysisModels:
    """Test theme analysis related models."""
    
    def test_content_theme_creation(self):
        """Test ContentTheme model creation."""
        theme = ContentTheme(
            theme_name="Digital Transformation",
            frequency=5,
            nodes_containing=["node_1", "node_2", "node_3"],
            key_concepts=["technology", "automation", "digital"],
            strategic_significance="Critical for competitive advantage",
            coverage_assessment="comprehensive",
            related_frameworks=["Value Chain", "Porter's Five Forces"]
        )
        
        assert theme.theme_name == "Digital Transformation"
        assert theme.frequency == 5
        assert len(theme.nodes_containing) == 3
        assert "technology" in theme.key_concepts
    
    def test_strategic_element_creation(self):
        """Test StrategicElement model creation."""
        element = StrategicElement(
            element_type="goal",
            element_title="Digital Platform Launch",
            contribution_to_theme="Core digital transformation initiative"
        )
        
        assert element.element_type == "goal"
        assert element.element_title == "Digital Platform Launch"
    
    def test_strategic_theme_creation(self):
        """Test StrategicTheme model creation."""
        element = StrategicElement(
            element_type="initiative",
            element_title="Cloud Migration",
            contribution_to_theme="Enables digital infrastructure"
        )
        
        theme = StrategicTheme(
            theme_name="Technology Modernization",
            sub_themes=["cloud", "automation", "data analytics"],
            strength="high",
            strategic_elements=[element],
            theme_coherence="Well-developed theme with clear direction",
            gaps_in_theme=["Mobile strategy needs strengthening"]
        )
        
        assert theme.theme_name == "Technology Modernization"
        assert len(theme.sub_themes) == 3
        assert theme.strength == "high"
        assert len(theme.strategic_elements) == 1


class TestOptimizationModels:
    """Test canvas optimization related models."""
    
    def test_completeness_assessment_creation(self):
        """Test CompletenessAssessment model creation."""
        assessment = CompletenessAssessment(
            framework_name="SWOT Analysis",
            score=75,
            details={
                "strengths": 3,
                "weaknesses": 2,
                "opportunities": 4,
                "threats": 1
            },
            missing_elements=["More threats needed", "Weakness analysis incomplete"]
        )
        
        assert assessment.framework_name == "SWOT Analysis"
        assert assessment.score == 75
        assert assessment.details["strengths"] == 3
        assert len(assessment.missing_elements) == 2
    
    def test_content_improvement_creation(self):
        """Test ContentImprovement model creation."""
        improvement = ContentImprovement(
            node_id="node_123",
            current_issue="Content too vague",
            suggested_improvement="Add specific metrics and timeline",
            rationale="Specific goals are more actionable"
        )
        
        assert improvement.node_id == "node_123"
        assert improvement.current_issue == "Content too vague"
    
    def test_critical_addition_creation(self):
        """Test CriticalAddition model creation."""
        addition = CriticalAddition(
            element_type=NodeType.RISK,
            title="Cybersecurity Risk",
            content="Potential data breach exposure",
            rationale="Critical risk not addressed in current canvas",
            priority=Priority.HIGH,
            estimated_impact="Could prevent initiative success"
        )
        
        assert addition.element_type == NodeType.RISK
        assert addition.priority == Priority.HIGH
    
    def test_implementation_action_creation(self):
        """Test ImplementationAction model creation."""
        action = ImplementationAction(
            action="Add SWOT threat analysis",
            effort="medium",
            impact="high",
            timeframe="1-2 weeks"
        )
        
        assert action.action == "Add SWOT threat analysis"
        assert action.effort == "medium"
    
    def test_success_metric_creation(self):
        """Test SuccessMetric model creation."""
        metric = SuccessMetric(
            metric="Framework Completeness",
            current=75,
            target=90,
            measurement="Percentage of framework elements covered"
        )
        
        assert metric.metric == "Framework Completeness"
        assert metric.current == 75
        assert metric.target == 90


class TestRequestModels:
    """Test API request models."""
    
    def test_text_structure_request_creation(self):
        """Test TextStructureRequest model creation."""
        request = TextStructureRequest(
            text="We need to improve our customer satisfaction through better service delivery",
            canvas_context={"existing_nodes": 5},
            north_star_context={"purpose": "Customer excellence"}
        )
        
        assert "customer satisfaction" in request.text
        assert request.canvas_context["existing_nodes"] == 5
        assert request.north_star_context["purpose"] == "Customer excellence"
    
    def test_connection_analysis_request_creation(self):
        """Test ConnectionAnalysisRequest model creation."""
        node = CanvasNode(
            id="node_1",
            title="Test Node",
            content="Test content",
            type=NodeType.BASIC
        )
        
        canvas_data = CanvasData(nodes=[node], edges=[])
        
        request = ConnectionAnalysisRequest(
            canvas_data=canvas_data,
            selected_nodes=["node_1"],
            north_star_context={"vision": "Be the market leader"}
        )
        
        assert len(request.canvas_data.nodes) == 1
        assert request.selected_nodes == ["node_1"]
    
    def test_theme_analysis_request_creation(self):
        """Test ThemeAnalysisRequest model creation."""
        node = CanvasNode(
            id="node_1",
            title="Innovation",
            content="Drive innovation",
            type=NodeType.BASIC
        )
        
        canvas_data = CanvasData(nodes=[node], edges=[])
        
        request = ThemeAnalysisRequest(
            canvas_data=canvas_data,
            analysis_scope="comprehensive",
            north_star_context={"values": ["innovation", "excellence"]}
        )
        
        assert len(request.canvas_data.nodes) == 1
        assert request.analysis_scope == "comprehensive"
    
    def test_canvas_optimization_request_creation(self):
        """Test CanvasOptimizationRequest model creation."""
        node = CanvasNode(
            id="node_1",
            title="Goal",
            content="Achieve excellence",
            type=NodeType.BASIC
        )
        
        canvas_data = CanvasData(nodes=[node], edges=[])
        
        request = CanvasOptimizationRequest(
            canvas_data=canvas_data,
            current_objectives=["Growth", "Innovation"],
            north_star_context={"purpose": "Excellence"}
        )
        
        assert len(request.canvas_data.nodes) == 1
        assert "Growth" in request.current_objectives


class TestResponseModels:
    """Test API response models."""
    
    def test_ai_analysis_response_creation(self):
        """Test AIAnalysisResponse model creation."""
        user_id = uuid4()
        
        response = AIAnalysisResponse(
            analysis_type="text_structure",
            user_id=user_id,
            canvas_id="canvas_123",
            success=True,
            message="Analysis completed successfully",
            execution_time_ms=1500
        )
        
        assert response.analysis_type == "text_structure"
        assert response.user_id == user_id
        assert response.success is True
        assert response.execution_time_ms == 1500
        assert isinstance(response.analysis_id, UUID)
        assert isinstance(response.timestamp, datetime)
    
    def test_ai_analysis_response_with_data(self):
        """Test AIAnalysisResponse with actual data."""
        user_id = uuid4()
        
        # Create test data
        analysis = TextStructureAnalysis(
            content_type="goal",
            key_concepts=["revenue"],
            strategic_relevance="Core business objective"
        )
        
        suggestion = NodeSuggestion(
            suggested_node_type=NodeType.BASIC,
            title="Revenue Target",
            content="Increase revenue by 20%",
            rationale="Clear measurable goal",
            confidence=0.9
        )
        
        text_data = TextStructureSuggestion(
            analysis=analysis,
            suggestions=[suggestion],
            connections=[],
            recommendations={"primary_action": "Create goal node"}
        )
        
        response = AIAnalysisResponse(
            analysis_type="text_structure",
            user_id=user_id,
            data=text_data,
            success=True
        )
        
        assert response.success is True
        assert response.data is not None
        assert response.data.analysis.content_type == "goal"
        assert len(response.data.suggestions) == 1


class TestModelDefaults:
    """Test model default values and optional fields."""
    
    def test_canvas_node_defaults(self):
        """Test CanvasNode default values."""
        node = CanvasNode(
            id="node_1",
            title="Test",
            content="Content",
            type=NodeType.BASIC
        )
        
        assert node.metadata == {}  # Default empty dict
    
    def test_canvas_edge_defaults(self):
        """Test CanvasEdge default values."""
        edge = CanvasEdge(
            id="edge_1",
            source="node_1",
            target="node_2"
        )
        
        assert edge.label is None
        assert edge.relationship_type is None
    
    def test_ai_analysis_response_defaults(self):
        """Test AIAnalysisResponse default values."""
        user_id = uuid4()
        
        response = AIAnalysisResponse(
            analysis_type="test",
            user_id=user_id
        )
        
        assert response.success is True  # Default
        assert response.message is None
        assert response.data is None
        assert response.execution_time_ms is None
        assert isinstance(response.analysis_id, UUID)
        assert isinstance(response.timestamp, datetime)


class TestModelValidation:
    """Test model validation rules."""
    
    def test_completeness_assessment_score_validation(self):
        """Test CompletenessAssessment score validation."""
        # Valid scores
        assessment = CompletenessAssessment(
            framework_name="Test",
            score=50,
            details={},
            missing_elements=[]
        )
        assert assessment.score == 50
        
        # Test boundary values
        assessment_min = CompletenessAssessment(
            framework_name="Test",
            score=0,
            details={},
            missing_elements=[]
        )
        assert assessment_min.score == 0
        
        assessment_max = CompletenessAssessment(
            framework_name="Test",
            score=100,
            details={},
            missing_elements=[]
        )
        assert assessment_max.score == 100
        
        # Invalid scores should raise validation errors
        with pytest.raises(ValidationError):
            CompletenessAssessment(
                framework_name="Test",
                score=-1,  # Invalid: < 0
                details={},
                missing_elements=[]
            )
        
        with pytest.raises(ValidationError):
            CompletenessAssessment(
                framework_name="Test", 
                score=101,  # Invalid: > 100
                details={},
                missing_elements=[]
            )
    
    def test_required_fields_validation(self):
        """Test that required fields are enforced."""
        # NodeSuggestion missing required fields
        with pytest.raises(ValidationError):
            NodeSuggestion(
                # Missing suggested_node_type
                title="Test",
                content="Content",
                rationale="Rationale"
            )
        
        with pytest.raises(ValidationError):
            NodeSuggestion(
                suggested_node_type=NodeType.BASIC,
                # Missing title
                content="Content",
                rationale="Rationale"
            )
    
    def test_empty_string_validation(self):
        """Test behavior with empty strings."""
        # Should allow empty strings where not explicitly forbidden
        node = CanvasNode(
            id="node_1",
            title="",  # Empty title should be allowed
            content="",  # Empty content should be allowed
            type=NodeType.BASIC
        )
        
        assert node.title == ""
        assert node.content == ""