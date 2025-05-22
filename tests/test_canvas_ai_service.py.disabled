"""
Test suite for Canvas AI Service layer.
"""

import pytest
import pytest_asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4, UUID
from typing import Dict, Any

from backend.services.canvas_ai_service import CanvasAIService, canvas_ai_service
from backend.models.canvas_ai import (
    TextStructureRequest, ConnectionAnalysisRequest, ThemeAnalysisRequest, 
    CanvasOptimizationRequest, CanvasData, CanvasNode, CanvasEdge, NodeType,
    AIAnalysisResponse, TextStructureSuggestion, ConnectionSuggestionResponse,
    ThemeAnalysisResponse, CanvasOptimizationResponse
)


@pytest_asyncio.fixture
async def service():
    """Create a CanvasAIService instance for testing."""
    return CanvasAIService()


@pytest_asyncio.fixture
def user_id():
    """Generate a test user ID."""
    return uuid4()


@pytest_asyncio.fixture
def sample_canvas_data():
    """Create sample canvas data for testing."""
    nodes = [
        CanvasNode(
            id="node_1",
            title="Strategic Goal",
            content="Increase market share by 20% in 2024",
            type=NodeType.BASIC,
            metadata={"priority": "high"}
        ),
        CanvasNode(
            id="node_2", 
            title="Market Research",
            content="Conduct comprehensive market analysis",
            type=NodeType.BASIC,
            metadata={"status": "in_progress"}
        ),
        CanvasNode(
            id="node_3",
            title="Brand Strength",
            content="Strong brand recognition in target market",
            type=NodeType.SWOT_S,
            metadata={"framework": "SWOT"}
        )
    ]
    
    edges = [
        CanvasEdge(
            id="edge_1",
            source="node_2",
            target="node_1",
            label="supports"
        )
    ]
    
    return CanvasData(
        nodes=nodes,
        edges=edges,
        metadata={"canvas_id": "test_canvas_123"}
    )


@pytest_asyncio.fixture
def mock_ai_response():
    """Mock AI service response."""
    return {
        "analysis": {
            "content_type": "strategic_goal",
            "key_concepts": ["market_share", "growth", "target"],
            "strategic_relevance": "Core business objective"
        },
        "suggestions": [
            {
                "suggested_node_type": "basic",
                "title": "Market Share Goal",
                "content": "Increase market share by 20%",
                "rationale": "Clear measurable objective",
                "confidence": 0.9,
                "metadata": {"category": "goal"}
            }
        ],
        "connections": [],
        "recommendations": {
            "primary_action": "Create goal node",
            "additional_actions": ["Add timeline", "Define metrics"],
            "missing_elements": ["Success metrics"]
        }
    }


class TestCanvasAIServiceInitialization:
    """Test CanvasAIService initialization."""
    
    def test_service_initialization(self):
        """Test service initializes correctly."""
        service = CanvasAIService()
        assert hasattr(service, 'logger')
    
    def test_service_singleton(self):
        """Test that canvas_ai_service singleton is properly configured."""
        assert isinstance(canvas_ai_service, CanvasAIService)


class TestTextStructuring:
    """Test text structuring functionality."""
    
    @pytest.mark.asyncio
    @patch('backend.services.canvas_ai_service.kernel_service')
    async def test_structure_text_success(self, mock_kernel_service, service, user_id, mock_ai_response):
        """Test successful text structuring."""
        # Setup mock
        mock_kernel_service.invoke_semantic_function = AsyncMock(
            return_value=json.dumps(mock_ai_response)
        )
        
        # Create request
        request = TextStructureRequest(
            text="We need to increase our market share by 20% this year",
            canvas_context={"existing_nodes": 3},
            north_star_context={"purpose": "Market leadership"}
        )
        
        # Execute
        result = await service.structure_text(request, user_id)
        
        # Assertions
        assert isinstance(result, AIAnalysisResponse)
        assert result.success is True
        assert result.analysis_type == "text_structure"
        assert result.user_id == user_id
        assert result.data is not None
        assert isinstance(result.data, TextStructureSuggestion)
        assert result.execution_time_ms is not None
        
        # Verify AI service was called correctly
        mock_kernel_service.invoke_semantic_function.assert_called_once_with(
            skill_name="canvas",
            function_name="StructureText",
            input_text="",
            variables={
                "text": request.text,
                "canvas_context": json.dumps(request.canvas_context),
                "north_star_context": json.dumps(request.north_star_context)
            }
        )
    
    @pytest.mark.asyncio
    @patch('backend.services.canvas_ai_service.kernel_service')
    async def test_structure_text_with_minimal_request(self, mock_kernel_service, service, user_id, mock_ai_response):
        """Test text structuring with minimal request data."""
        mock_kernel_service.invoke_semantic_function = AsyncMock(
            return_value=json.dumps(mock_ai_response)
        )
        
        request = TextStructureRequest(text="Simple goal statement")
        
        result = await service.structure_text(request, user_id)
        
        assert result.success is True
        assert result.data is not None
        
        # Verify empty contexts are handled
        call_args = mock_kernel_service.invoke_semantic_function.call_args
        variables = call_args[1]['variables']
        assert variables['canvas_context'] == json.dumps({})
        assert variables['north_star_context'] == json.dumps({})
    
    @pytest.mark.asyncio
    @patch('backend.services.canvas_ai_service.kernel_service')
    async def test_structure_text_ai_error(self, mock_kernel_service, service, user_id):
        """Test text structuring when AI service fails."""
        mock_kernel_service.invoke_semantic_function = AsyncMock(
            side_effect=Exception("AI service unavailable")
        )
        
        request = TextStructureRequest(text="Test text")
        
        result = await service.structure_text(request, user_id)
        
        assert result.success is False
        assert "Failed to analyze text structure" in result.message
        assert result.data is None
        assert result.execution_time_ms is not None
    
    @pytest.mark.asyncio
    @patch('backend.services.canvas_ai_service.kernel_service')
    async def test_structure_text_invalid_json_response(self, mock_kernel_service, service, user_id):
        """Test handling of invalid JSON response from AI."""
        mock_kernel_service.invoke_semantic_function = AsyncMock(
            return_value="Invalid JSON response"
        )
        
        request = TextStructureRequest(text="Test text")
        
        result = await service.structure_text(request, user_id)
        
        assert result.success is False
        assert "Failed to analyze text structure" in result.message


class TestConnectionAnalysis:
    """Test connection analysis functionality."""
    
    @pytest.mark.asyncio
    @patch('backend.services.canvas_ai_service.kernel_service')
    async def test_analyze_connections_success(self, mock_kernel_service, service, user_id, sample_canvas_data):
        """Test successful connection analysis."""
        mock_response = {
            "analysis": {
                "total_nodes": 3,
                "existing_connections": 1,
                "connectivity_score": 0.33,
                "main_themes": ["strategic_planning"],
                "connection_gaps": ["Missing SWOT connections"]
            },
            "suggested_connections": [
                {
                    "source_node": {
                        "id": "node_1",
                        "title": "Strategic Goal",
                        "type": "basic"
                    },
                    "target_node": {
                        "id": "node_3",
                        "title": "Brand Strength",
                        "type": "swotS"
                    },
                    "relationship_type": "supporting",
                    "relationship_label": "leverages",
                    "confidence": 0.8,
                    "rationale": "Strong brand supports market share goals",
                    "strategic_impact": "Aligns strength with objective",
                    "priority": "high"
                }
            ],
            "connection_patterns": {
                "clusters": [],
                "orphaned_nodes": [],
                "hub_nodes": ["node_1"],
                "strategic_flows": []
            },
            "recommendations": {
                "high_priority": []
            },
            "strategic_insights": []
        }
        
        mock_kernel_service.invoke_semantic_function = AsyncMock(
            return_value=json.dumps(mock_response)
        )
        
        request = ConnectionAnalysisRequest(
            canvas_data=sample_canvas_data,
            selected_nodes=["node_1", "node_3"],
            north_star_context={"vision": "Market leadership"}
        )
        
        result = await service.analyze_connections(request, user_id)
        
        assert result.success is True
        assert result.analysis_type == "connection_analysis"
        assert result.data is not None
        assert isinstance(result.data, ConnectionSuggestionResponse)
        
        # Verify canvas data was passed correctly
        call_args = mock_kernel_service.invoke_semantic_function.call_args
        variables = call_args[1]['variables']
        canvas_data = json.loads(variables['canvas_data'])
        assert len(canvas_data['nodes']) == 3
        assert len(canvas_data['edges']) == 1
    
    @pytest.mark.asyncio
    @patch('backend.services.canvas_ai_service.kernel_service')
    async def test_analyze_connections_empty_canvas(self, mock_kernel_service, service, user_id):
        """Test connection analysis with empty canvas."""
        empty_canvas = CanvasData(nodes=[], edges=[])
        request = ConnectionAnalysisRequest(canvas_data=empty_canvas)
        
        # Should still call AI service even with empty canvas
        mock_kernel_service.invoke_semantic_function = AsyncMock(
            return_value=json.dumps({
                "analysis": {"total_nodes": 0, "existing_connections": 0, "connectivity_score": 0, "main_themes": [], "connection_gaps": []},
                "suggested_connections": [],
                "connection_patterns": {"clusters": [], "orphaned_nodes": [], "hub_nodes": [], "strategic_flows": []},
                "recommendations": {"high_priority": []},
                "strategic_insights": []
            })
        )
        
        result = await service.analyze_connections(request, user_id)
        
        assert result.success is True
        assert result.data is not None


class TestThemeAnalysis:
    """Test theme analysis functionality."""
    
    @pytest.mark.asyncio
    @patch('backend.services.canvas_ai_service.kernel_service')
    async def test_identify_themes_success(self, mock_kernel_service, service, user_id, sample_canvas_data):
        """Test successful theme identification."""
        mock_response = {
            "executive_summary": {
                "dominant_themes": ["growth", "market_strategy"],
                "strategic_focus": "Market expansion and growth",
                "thematic_balance": "Good balance across themes",
                "key_insight": "Strong focus on market-driven growth"
            },
            "content_themes": [
                {
                    "theme_name": "Market Growth",
                    "frequency": 2,
                    "nodes_containing": ["node_1", "node_2"],
                    "key_concepts": ["market", "growth", "share"],
                    "strategic_significance": "Core to business strategy",
                    "coverage_assessment": "comprehensive",
                    "related_frameworks": ["Porter's Five Forces"]
                }
            ],
            "strategic_themes": [],
            "pattern_analysis": {"connection_patterns": [], "content_patterns": [], "temporal_patterns": []},
            "thematic_insights": [],
            "thematic_gaps": [],
            "thematic_balance": {},
            "thematic_recommendations": {},
            "strategic_narrative": {"current_story": "Growth-focused strategy", "story_completeness": "Good", "missing_chapters": [], "narrative_coherence": "High"}
        }
        
        mock_kernel_service.invoke_semantic_function = AsyncMock(
            return_value=json.dumps(mock_response)
        )
        
        request = ThemeAnalysisRequest(
            canvas_data=sample_canvas_data,
            analysis_scope="comprehensive",
            north_star_context={"purpose": "Growth leadership"}
        )
        
        result = await service.identify_themes(request, user_id)
        
        assert result.success is True
        assert result.analysis_type == "theme_analysis"
        assert result.data is not None
        assert isinstance(result.data, ThemeAnalysisResponse)
        
        # Verify correct parameters were passed
        call_args = mock_kernel_service.invoke_semantic_function.call_args
        assert call_args[1]['skill_name'] == "canvas"
        assert call_args[1]['function_name'] == "IdentifyThemes"


class TestCanvasOptimization:
    """Test canvas optimization functionality."""
    
    @pytest.mark.asyncio
    @patch('backend.services.canvas_ai_service.kernel_service')
    async def test_optimize_canvas_success(self, mock_kernel_service, service, user_id, sample_canvas_data):
        """Test successful canvas optimization."""
        mock_response = {
            "executive_summary": {
                "overall_score": 7.2,
                "strengths": ["Clear goals", "Good SWOT coverage"],
                "main_gaps": ["Missing risk analysis", "Incomplete metrics"],
                "priority_recommendation": "Add comprehensive risk assessment"
            },
            "completeness_assessment": {
                "swot_completeness": {
                    "score": 25,
                    "strengths": 1,
                    "weaknesses": 0,
                    "opportunities": 0,
                    "threats": 0,
                    "missing_elements": ["weaknesses", "opportunities", "threats"]
                }
            },
            "structural_analysis": {},
            "content_quality": {},
            "strategic_alignment": {},
            "optimization_recommendations": {},
            "implementation_roadmap": {},
            "success_metrics": {}
        }
        
        mock_kernel_service.invoke_semantic_function = AsyncMock(
            return_value=json.dumps(mock_response)
        )
        
        request = CanvasOptimizationRequest(
            canvas_data=sample_canvas_data,
            current_objectives=["Growth", "Market leadership"],
            north_star_context={"purpose": "Excellence"}
        )
        
        result = await service.optimize_canvas(request, user_id)
        
        assert result.success is True
        assert result.analysis_type == "canvas_optimization"
        assert result.data is not None
        assert isinstance(result.data, CanvasOptimizationResponse)


class TestComprehensiveAnalysis:
    """Test comprehensive analysis functionality."""
    
    @pytest.mark.asyncio
    @patch('backend.services.canvas_ai_service.CanvasAIService.analyze_connections')
    @patch('backend.services.canvas_ai_service.CanvasAIService.identify_themes')
    @patch('backend.services.canvas_ai_service.CanvasAIService.optimize_canvas')
    async def test_comprehensive_analysis_all_enabled(self, mock_optimize, mock_themes, mock_connections, service, user_id, sample_canvas_data):
        """Test comprehensive analysis with all features enabled."""
        # Setup mocks
        mock_connections.return_value = AIAnalysisResponse(
            analysis_type="connection_analysis",
            user_id=user_id,
            success=True
        )
        mock_themes.return_value = AIAnalysisResponse(
            analysis_type="theme_analysis", 
            user_id=user_id,
            success=True
        )
        mock_optimize.return_value = AIAnalysisResponse(
            analysis_type="canvas_optimization",
            user_id=user_id,
            success=True
        )
        
        result = await service.comprehensive_analysis(
            canvas_data=sample_canvas_data,
            user_id=user_id,
            include_themes=True,
            include_connections=True,
            include_optimization=True,
            north_star_context={"purpose": "Excellence"}
        )
        
        assert len(result) == 3
        assert "connections" in result
        assert "themes" in result
        assert "optimization" in result
        
        # Verify all methods were called
        mock_connections.assert_called_once()
        mock_themes.assert_called_once()
        mock_optimize.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('backend.services.canvas_ai_service.CanvasAIService.analyze_connections')
    async def test_comprehensive_analysis_selective_enabled(self, mock_connections, service, user_id, sample_canvas_data):
        """Test comprehensive analysis with only connections enabled."""
        mock_connections.return_value = AIAnalysisResponse(
            analysis_type="connection_analysis",
            user_id=user_id,
            success=True
        )
        
        result = await service.comprehensive_analysis(
            canvas_data=sample_canvas_data,
            user_id=user_id,
            include_themes=False,
            include_connections=True,
            include_optimization=False
        )
        
        assert len(result) == 1
        assert "connections" in result
        assert "themes" not in result
        assert "optimization" not in result
        
        mock_connections.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('backend.services.canvas_ai_service.CanvasAIService.analyze_connections')
    async def test_comprehensive_analysis_with_exception(self, mock_connections, service, user_id, sample_canvas_data):
        """Test comprehensive analysis when one analysis fails."""
        # Mock one analysis to raise an exception
        mock_connections.side_effect = Exception("Connection analysis failed")
        
        result = await service.comprehensive_analysis(
            canvas_data=sample_canvas_data,
            user_id=user_id,
            include_themes=False,
            include_connections=True,
            include_optimization=False
        )
        
        assert len(result) == 1
        assert "connections" in result
        assert result["connections"].success is False
        assert "Connection analysis failed" in result["connections"].message


class TestHelperMethods:
    """Test helper methods in CanvasAIService."""
    
    def test_prepare_canvas_context(self, service, sample_canvas_data):
        """Test canvas context preparation."""
        context = service._prepare_canvas_context(sample_canvas_data)
        
        assert context["total_nodes"] == 3
        assert context["total_edges"] == 1
        assert NodeType.BASIC in context["node_types"]
        assert NodeType.SWOT_S in context["node_types"]
        assert context["has_content"] is True
        assert isinstance(context["connectivity"], float)
        assert context["connectivity"] == 1/3  # 1 edge / 3 nodes
    
    def test_prepare_canvas_context_empty(self, service):
        """Test canvas context preparation with empty canvas."""
        empty_canvas = CanvasData(nodes=[], edges=[])
        context = service._prepare_canvas_context(empty_canvas)
        
        assert context["total_nodes"] == 0
        assert context["total_edges"] == 0
        assert context["node_types"] == []
        assert context["has_content"] is False
        assert context["connectivity"] == 0  # 0 edges / max(0 nodes, 1)


class TestErrorHandling:
    """Test error handling scenarios."""
    
    @pytest.mark.asyncio
    @patch('backend.services.canvas_ai_service.kernel_service')
    async def test_json_parsing_error(self, mock_kernel_service, service, user_id):
        """Test handling of malformed JSON from AI service."""
        mock_kernel_service.invoke_semantic_function = AsyncMock(
            return_value="This is not valid JSON"
        )
        
        request = TextStructureRequest(text="Test text")
        result = await service.structure_text(request, user_id)
        
        assert result.success is False
        assert "Failed to analyze text structure" in result.message
    
    @pytest.mark.asyncio
    @patch('backend.services.canvas_ai_service.kernel_service')
    async def test_kernel_service_timeout(self, mock_kernel_service, service, user_id):
        """Test handling of kernel service timeout."""
        mock_kernel_service.invoke_semantic_function = AsyncMock(
            side_effect=asyncio.TimeoutError("AI service timeout")
        )
        
        request = TextStructureRequest(text="Test text")
        result = await service.structure_text(request, user_id)
        
        assert result.success is False
        assert "Failed to analyze text structure" in result.message


class TestPerformance:
    """Test performance-related functionality."""
    
    @pytest.mark.asyncio
    @patch('backend.services.canvas_ai_service.kernel_service')
    async def test_execution_time_tracking(self, mock_kernel_service, service, user_id):
        """Test that execution time is properly tracked."""
        # Add a small delay to simulate AI processing
        async def mock_ai_call(*args, **kwargs):
            await asyncio.sleep(0.01)  # 10ms delay
            return json.dumps({
                "analysis": {"content_type": "test", "key_concepts": [], "strategic_relevance": "test"},
                "suggestions": [],
                "connections": [],
                "recommendations": {}
            })
        
        mock_kernel_service.invoke_semantic_function = mock_ai_call
        
        request = TextStructureRequest(text="Test text")
        result = await service.structure_text(request, user_id)
        
        assert result.success is True
        assert result.execution_time_ms is not None
        assert result.execution_time_ms > 0
        # Should be at least 10ms but allow for some variance
        assert result.execution_time_ms >= 5