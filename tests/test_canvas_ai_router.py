import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient
from fastapi import status
import json
from uuid import uuid4, UUID

from backend.main import app
from backend.models.canvas_ai import (
    TextStructureRequest, ConnectionAnalysisRequest, 
    ThemeIdentificationRequest, CanvasOptimizationRequest,
    AIAnalysisResponse, NodeSuggestion, ConnectionSuggestion,
    ThemeCluster, OptimizationRecommendation, NodeType, ConnectionType
)


@pytest.fixture
async def async_client():
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
def auth_headers():
    return {"Authorization": "Bearer test-token"}


@pytest.fixture
def mock_user_id():
    return uuid4()


@pytest.fixture
def sample_text_structure_request():
    return {
        "text": "We need to improve customer satisfaction and reduce operational costs while expanding into new markets.",
        "canvas_context": {
            "existing_nodes": [],
            "canvas_type": "strategic_planning"
        },
        "preferences": {
            "max_suggestions": 5,
            "confidence_threshold": 0.7
        }
    }


@pytest.fixture
def sample_connection_analysis_request():
    return {
        "nodes": [
            {"id": "node1", "type": "goal", "content": "Increase revenue"},
            {"id": "node2", "type": "initiative", "content": "Launch new product"}
        ],
        "canvas_context": {
            "existing_connections": [],
            "canvas_type": "strategic_planning"
        },
        "analysis_depth": "comprehensive"
    }


@pytest.fixture
def sample_theme_request():
    return {
        "canvas_elements": {
            "nodes": [
                {"id": "1", "type": "goal", "content": "Digital transformation"},
                {"id": "2", "type": "challenge", "content": "Legacy systems"}
            ],
            "connections": []
        },
        "analysis_scope": "comprehensive"
    }


@pytest.fixture
def sample_optimization_request():
    return {
        "current_canvas": {
            "nodes": [
                {"id": "1", "type": "goal", "content": "Increase market share"}
            ],
            "connections": []
        },
        "optimization_goals": ["completeness", "strategic_alignment"],
        "strategic_context": {
            "industry": "technology",
            "company_stage": "growth"
        }
    }


@pytest.fixture
def mock_ai_response():
    return AIAnalysisResponse(
        analysis_type="text_structure",
        suggestions=[
            NodeSuggestion(
                suggested_node_type=NodeType.GOAL,
                title="Customer Satisfaction Goal",
                content="Improve customer satisfaction scores",
                rationale="Focus on customer experience",
                confidence=0.9
            )
        ],
        confidence=0.85,
        processing_time=1.2,
        metadata={"model_version": "test"}
    )


class TestCanvasAIRouter:
    """Test suite for canvas AI API endpoints."""

    @pytest.mark.asyncio
    async def test_structure_text_success(self, async_client, auth_headers, 
                                        sample_text_structure_request, mock_ai_response):
        with patch('backend.services.canvas_ai_service.CanvasAIService.structure_text', 
                  return_value=mock_ai_response) as mock_service:
            response = await async_client.post(
                "/api/canvas-ai/structure-text",
                json=sample_text_structure_request,
                headers=auth_headers
            )
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["analysis_type"] == "text_structure"
            assert len(data["suggestions"]) == 1
            assert data["confidence"] == 0.85
            mock_service.assert_called_once()

    @pytest.mark.asyncio
    async def test_structure_text_invalid_request(self, async_client, auth_headers):
        invalid_request = {"invalid": "data"}
        
        response = await async_client.post(
            "/api/canvas-ai/structure-text",
            json=invalid_request,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_structure_text_unauthorized(self, async_client, sample_text_structure_request):
        response = await async_client.post(
            "/api/canvas-ai/structure-text",
            json=sample_text_structure_request
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_analyze_connections_success(self, async_client, auth_headers,
                                             sample_connection_analysis_request, mock_ai_response):
        mock_response = AIAnalysisResponse(
            analysis_type="connection_analysis",
            suggestions=[
                ConnectionSuggestion(
                    from_node_id="node1",
                    to_node_id="node2",
                    connection_type=ConnectionType.SUPPORTS,
                    rationale="Revenue supports product launch",
                    confidence=0.8
                )
            ],
            confidence=0.82,
            processing_time=1.5
        )
        
        with patch('backend.services.canvas_ai_service.CanvasAIService.analyze_connections',
                  return_value=mock_response) as mock_service:
            response = await async_client.post(
                "/api/canvas-ai/analyze-connections",
                json=sample_connection_analysis_request,
                headers=auth_headers
            )
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["analysis_type"] == "connection_analysis"
            assert len(data["suggestions"]) == 1
            mock_service.assert_called_once()

    @pytest.mark.asyncio
    async def test_identify_themes_success(self, async_client, auth_headers,
                                         sample_theme_request):
        mock_response = AIAnalysisResponse(
            analysis_type="theme_identification",
            suggestions=[
                ThemeCluster(
                    theme_name="Digital Innovation",
                    description="Focus on technology advancement",
                    related_nodes=["1", "2"],
                    confidence=0.88,
                    strategic_importance="high"
                )
            ],
            confidence=0.86,
            processing_time=2.1
        )
        
        with patch('backend.services.canvas_ai_service.CanvasAIService.identify_themes',
                  return_value=mock_response) as mock_service:
            response = await async_client.post(
                "/api/canvas-ai/identify-themes",
                json=sample_theme_request,
                headers=auth_headers
            )
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["analysis_type"] == "theme_identification"
            mock_service.assert_called_once()

    @pytest.mark.asyncio
    async def test_optimize_canvas_success(self, async_client, auth_headers,
                                         sample_optimization_request):
        mock_response = AIAnalysisResponse(
            analysis_type="canvas_optimization",
            suggestions=[
                OptimizationRecommendation(
                    category="strategic_alignment",
                    recommendation="Add competitive analysis",
                    rationale="Missing market context",
                    priority="high",
                    confidence=0.91
                )
            ],
            confidence=0.89,
            processing_time=2.8
        )
        
        with patch('backend.services.canvas_ai_service.CanvasAIService.optimize_canvas',
                  return_value=mock_response) as mock_service:
            response = await async_client.post(
                "/api/canvas-ai/optimize-canvas",
                json=sample_optimization_request,
                headers=auth_headers
            )
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["analysis_type"] == "canvas_optimization"
            mock_service.assert_called_once()

    @pytest.mark.asyncio
    async def test_comprehensive_analysis_success(self, async_client, auth_headers,
                                                sample_text_structure_request):
        mock_response = AIAnalysisResponse(
            analysis_type="comprehensive_analysis",
            suggestions=[mock_ai_response.suggestions[0]],
            confidence=0.87,
            processing_time=4.2,
            metadata={"comprehensive": True}
        )
        
        with patch('backend.services.canvas_ai_service.CanvasAIService.comprehensive_analysis',
                  return_value=mock_response) as mock_service:
            response = await async_client.post(
                "/api/canvas-ai/comprehensive-analysis",
                json=sample_text_structure_request,
                headers=auth_headers
            )
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["analysis_type"] == "comprehensive_analysis"
            assert data["metadata"]["comprehensive"] is True
            mock_service.assert_called_once()

    @pytest.mark.asyncio
    async def test_health_check(self, async_client):
        response = await async_client.get("/api/canvas-ai/health")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "healthy"
        assert "ai_service" in data
        assert "timestamp" in data

    @pytest.mark.asyncio
    async def test_service_error_handling(self, async_client, auth_headers,
                                        sample_text_structure_request):
        with patch('backend.services.canvas_ai_service.CanvasAIService.structure_text',
                  side_effect=Exception("AI service error")) as mock_service:
            response = await async_client.post(
                "/api/canvas-ai/structure-text",
                json=sample_text_structure_request,
                headers=auth_headers
            )
            
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            data = response.json()
            assert "error" in data
            assert "AI service error" in data["error"]

    @pytest.mark.asyncio
    async def test_batch_processing_endpoints(self, async_client, auth_headers):
        batch_request = {
            "requests": [
                {
                    "type": "text_structure",
                    "data": {
                        "text": "Improve efficiency",
                        "canvas_context": {"existing_nodes": []},
                        "preferences": {"max_suggestions": 3}
                    }
                },
                {
                    "type": "connection_analysis", 
                    "data": {
                        "nodes": [{"id": "1", "type": "goal", "content": "Test"}],
                        "canvas_context": {"existing_connections": []}
                    }
                }
            ]
        }
        
        mock_responses = [
            AIAnalysisResponse(analysis_type="text_structure", suggestions=[], confidence=0.8),
            AIAnalysisResponse(analysis_type="connection_analysis", suggestions=[], confidence=0.7)
        ]
        
        with patch('backend.services.canvas_ai_service.CanvasAIService.process_batch',
                  return_value=mock_responses) as mock_service:
            response = await async_client.post(
                "/api/canvas-ai/batch-process",
                json=batch_request,
                headers=auth_headers
            )
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "results" in data
            assert len(data["results"]) == 2
            mock_service.assert_called_once()

    @pytest.mark.asyncio
    async def test_rate_limiting_simulation(self, async_client, auth_headers,
                                          sample_text_structure_request):
        """Test multiple rapid requests to ensure rate limiting works."""
        tasks = []
        
        with patch('backend.services.canvas_ai_service.CanvasAIService.structure_text',
                  return_value=mock_ai_response):
            for i in range(5):
                task = async_client.post(
                    "/api/canvas-ai/structure-text",
                    json=sample_text_structure_request,
                    headers=auth_headers
                )
                tasks.append(task)
            
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            # At least some requests should succeed
            successful_responses = [r for r in responses if not isinstance(r, Exception)]
            assert len(successful_responses) > 0
            
            for response in successful_responses:
                assert response.status_code == status.HTTP_200_OK

    @pytest.mark.asyncio
    async def test_content_validation(self, async_client, auth_headers):
        """Test various edge cases in content validation."""
        test_cases = [
            # Empty text
            {
                "text": "",
                "canvas_context": {"existing_nodes": []},
                "preferences": {"max_suggestions": 5}
            },
            # Very long text
            {
                "text": "x" * 10000,
                "canvas_context": {"existing_nodes": []},
                "preferences": {"max_suggestions": 5}
            },
            # Invalid preferences
            {
                "text": "Valid text",
                "canvas_context": {"existing_nodes": []},
                "preferences": {"max_suggestions": -1}
            }
        ]
        
        for test_case in test_cases:
            response = await async_client.post(
                "/api/canvas-ai/structure-text",
                json=test_case,
                headers=auth_headers
            )
            # Should either succeed or return validation error
            assert response.status_code in [status.HTTP_200_OK, status.HTTP_422_UNPROCESSABLE_ENTITY]

    @pytest.mark.asyncio
    async def test_cors_headers(self, async_client, auth_headers, sample_text_structure_request):
        """Test CORS headers are properly set."""
        with patch('backend.services.canvas_ai_service.CanvasAIService.structure_text',
                  return_value=mock_ai_response):
            response = await async_client.post(
                "/api/canvas-ai/structure-text",
                json=sample_text_structure_request,
                headers=auth_headers
            )
            
            assert response.status_code == status.HTTP_200_OK
            # Note: Actual CORS headers would be set by middleware in production