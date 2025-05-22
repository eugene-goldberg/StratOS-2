import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from httpx import AsyncClient
from fastapi import status
import json
from uuid import uuid4, UUID
from datetime import datetime

from backend.main import app
from backend.models.canvas_ai import (
    TextStructureRequest, ConnectionAnalysisRequest,
    AIAnalysisResponse, NodeSuggestion, ConnectionSuggestion,
    NodeType, ConnectionType
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


class TestCanvasAIIntegration:
    """End-to-end integration tests for canvas AI functionality."""

    @pytest.mark.asyncio
    async def test_full_canvas_analysis_workflow(self, async_client, auth_headers):
        """Test complete workflow from text input to optimized canvas."""
        
        # Step 1: Structure initial text
        text_request = {
            "text": "We need to increase market share by improving product quality and expanding our sales team while reducing operational costs.",
            "canvas_context": {
                "existing_nodes": [],
                "canvas_type": "strategic_planning"
            },
            "preferences": {
                "max_suggestions": 10,
                "confidence_threshold": 0.6
            }
        }
        
        mock_text_response = AIAnalysisResponse(
            analysis_type="text_structure",
            suggestions=[
                NodeSuggestion(
                    suggested_node_type=NodeType.GOAL,
                    title="Increase Market Share",
                    content="Expand market presence and customer base",
                    rationale="Primary business objective",
                    confidence=0.95
                ),
                NodeSuggestion(
                    suggested_node_type=NodeType.INITIATIVE,
                    title="Improve Product Quality",
                    content="Enhance product features and reliability",
                    rationale="Key driver for market expansion",
                    confidence=0.88
                ),
                NodeSuggestion(
                    suggested_node_type=NodeType.INITIATIVE,
                    title="Expand Sales Team",
                    content="Hire additional sales representatives",
                    rationale="Increase sales capacity",
                    confidence=0.82
                )
            ],
            confidence=0.88,
            processing_time=1.5
        )
        
        with patch('backend.services.canvas_ai_service.CanvasAIService.structure_text',
                  return_value=mock_text_response):
            response = await async_client.post(
                "/api/canvas-ai/structure-text",
                json=text_request,
                headers=auth_headers
            )
            
            assert response.status_code == status.HTTP_200_OK
            text_data = response.json()
            assert len(text_data["suggestions"]) == 3
            
        # Step 2: Analyze connections between generated nodes
        connection_request = {
            "nodes": [
                {"id": "goal1", "type": "goal", "content": "Increase Market Share"},
                {"id": "init1", "type": "initiative", "content": "Improve Product Quality"},
                {"id": "init2", "type": "initiative", "content": "Expand Sales Team"}
            ],
            "canvas_context": {
                "existing_connections": [],
                "canvas_type": "strategic_planning"
            },
            "analysis_depth": "comprehensive"
        }
        
        mock_connection_response = AIAnalysisResponse(
            analysis_type="connection_analysis",
            suggestions=[
                ConnectionSuggestion(
                    from_node_id="init1",
                    to_node_id="goal1",
                    connection_type=ConnectionType.SUPPORTS,
                    rationale="Quality improvements drive market share growth",
                    confidence=0.92
                ),
                ConnectionSuggestion(
                    from_node_id="init2", 
                    to_node_id="goal1",
                    connection_type=ConnectionType.SUPPORTS,
                    rationale="More sales capacity increases market reach",
                    confidence=0.89
                )
            ],
            confidence=0.90,
            processing_time=2.1
        )
        
        with patch('backend.services.canvas_ai_service.CanvasAIService.analyze_connections',
                  return_value=mock_connection_response):
            response = await async_client.post(
                "/api/canvas-ai/analyze-connections",
                json=connection_request,
                headers=auth_headers
            )
            
            assert response.status_code == status.HTTP_200_OK
            connection_data = response.json()
            assert len(connection_data["suggestions"]) == 2
            
        # Step 3: Identify themes across the canvas
        theme_request = {
            "canvas_elements": {
                "nodes": connection_request["nodes"],
                "connections": [
                    {"from": "init1", "to": "goal1", "type": "supports"},
                    {"from": "init2", "to": "goal1", "type": "supports"}
                ]
            },
            "analysis_scope": "comprehensive"
        }
        
        with patch('backend.services.canvas_ai_service.CanvasAIService.identify_themes') as mock_themes:
            mock_themes.return_value = AIAnalysisResponse(
                analysis_type="theme_identification",
                suggestions=[],
                confidence=0.85,
                processing_time=1.8
            )
            
            response = await async_client.post(
                "/api/canvas-ai/identify-themes",
                json=theme_request,
                headers=auth_headers
            )
            
            assert response.status_code == status.HTTP_200_OK
            
        # Step 4: Optimize the complete canvas
        optimization_request = {
            "current_canvas": {
                "nodes": connection_request["nodes"],
                "connections": [
                    {"from": "init1", "to": "goal1", "type": "supports"},
                    {"from": "init2", "to": "goal1", "type": "supports"}
                ]
            },
            "optimization_goals": ["completeness", "strategic_alignment", "actionability"],
            "strategic_context": {
                "industry": "technology",
                "company_stage": "growth",
                "market_conditions": "competitive"
            }
        }
        
        with patch('backend.services.canvas_ai_service.CanvasAIService.optimize_canvas') as mock_optimize:
            mock_optimize.return_value = AIAnalysisResponse(
                analysis_type="canvas_optimization",
                suggestions=[],
                confidence=0.87,
                processing_time=3.2
            )
            
            response = await async_client.post(
                "/api/canvas-ai/optimize-canvas",
                json=optimization_request,
                headers=auth_headers
            )
            
            assert response.status_code == status.HTTP_200_OK

    @pytest.mark.asyncio
    async def test_batch_processing_workflow(self, async_client, auth_headers):
        """Test batch processing of multiple AI requests."""
        
        batch_request = {
            "requests": [
                {
                    "type": "text_structure",
                    "data": {
                        "text": "Improve customer satisfaction",
                        "canvas_context": {"existing_nodes": []},
                        "preferences": {"max_suggestions": 5}
                    }
                },
                {
                    "type": "text_structure",
                    "data": {
                        "text": "Reduce operational costs",
                        "canvas_context": {"existing_nodes": []},
                        "preferences": {"max_suggestions": 5}
                    }
                },
                {
                    "type": "connection_analysis",
                    "data": {
                        "nodes": [
                            {"id": "1", "type": "goal", "content": "Test goal"},
                            {"id": "2", "type": "initiative", "content": "Test initiative"}
                        ],
                        "canvas_context": {"existing_connections": []},
                        "analysis_depth": "standard"
                    }
                }
            ]
        }
        
        mock_batch_responses = [
            AIAnalysisResponse(
                analysis_type="text_structure",
                suggestions=[
                    NodeSuggestion(
                        suggested_node_type=NodeType.GOAL,
                        title="Customer Satisfaction Goal",
                        content="Improve customer experience metrics",
                        rationale="Direct response to input",
                        confidence=0.9
                    )
                ],
                confidence=0.9,
                processing_time=1.2
            ),
            AIAnalysisResponse(
                analysis_type="text_structure", 
                suggestions=[
                    NodeSuggestion(
                        suggested_node_type=NodeType.GOAL,
                        title="Cost Reduction Goal",
                        content="Decrease operational expenses",
                        rationale="Cost optimization focus",
                        confidence=0.85
                    )
                ],
                confidence=0.85,
                processing_time=1.1
            ),
            AIAnalysisResponse(
                analysis_type="connection_analysis",
                suggestions=[
                    ConnectionSuggestion(
                        from_node_id="2",
                        to_node_id="1",
                        connection_type=ConnectionType.SUPPORTS,
                        rationale="Initiative supports goal",
                        confidence=0.8
                    )
                ],
                confidence=0.8,
                processing_time=1.5
            )
        ]
        
        with patch('backend.services.canvas_ai_service.CanvasAIService.process_batch',
                  return_value=mock_batch_responses):
            response = await async_client.post(
                "/api/canvas-ai/batch-process",
                json=batch_request,
                headers=auth_headers
            )
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "results" in data
            assert len(data["results"]) == 3
            
            # Verify each result type
            assert data["results"][0]["analysis_type"] == "text_structure"
            assert data["results"][1]["analysis_type"] == "text_structure"
            assert data["results"][2]["analysis_type"] == "connection_analysis"

    @pytest.mark.asyncio
    async def test_comprehensive_analysis_integration(self, async_client, auth_headers):
        """Test comprehensive analysis endpoint integration."""
        
        comprehensive_request = {
            "text": "Launch new product line to capture emerging market opportunities while strengthening our competitive position",
            "canvas_context": {
                "existing_nodes": [
                    {"id": "existing1", "type": "challenge", "content": "Market competition"}
                ],
                "canvas_type": "strategic_planning"
            },
            "preferences": {
                "max_suggestions": 15,
                "confidence_threshold": 0.5,
                "include_connections": True,
                "include_themes": True,
                "include_optimization": True
            }
        }
        
        mock_comprehensive_response = AIAnalysisResponse(
            analysis_type="comprehensive_analysis",
            suggestions=[
                NodeSuggestion(
                    suggested_node_type=NodeType.INITIATIVE,
                    title="New Product Launch",
                    content="Develop and launch innovative product line",
                    rationale="Core initiative from input text",
                    confidence=0.95
                ),
                ConnectionSuggestion(
                    from_node_id="new_product",
                    to_node_id="existing1",
                    connection_type=ConnectionType.ADDRESSES,
                    rationale="New product addresses competitive challenges",
                    confidence=0.82
                )
            ],
            confidence=0.88,
            processing_time=5.7,
            metadata={
                "comprehensive": True,
                "included_analyses": ["structure", "connections", "themes", "optimization"],
                "total_suggestions": 8
            }
        )
        
        with patch('backend.services.canvas_ai_service.CanvasAIService.comprehensive_analysis',
                  return_value=mock_comprehensive_response):
            response = await async_client.post(
                "/api/canvas-ai/comprehensive-analysis",
                json=comprehensive_request,
                headers=auth_headers
            )
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["analysis_type"] == "comprehensive_analysis"
            assert data["metadata"]["comprehensive"] is True
            assert "included_analyses" in data["metadata"]
            assert data["processing_time"] > 5.0  # Comprehensive analysis takes longer

    @pytest.mark.asyncio
    async def test_error_recovery_and_resilience(self, async_client, auth_headers):
        """Test system resilience to various error conditions."""
        
        # Test AI service timeout
        with patch('backend.services.canvas_ai_service.CanvasAIService.structure_text',
                  side_effect=asyncio.TimeoutError("AI service timeout")):
            response = await async_client.post(
                "/api/canvas-ai/structure-text",
                json={
                    "text": "Test text",
                    "canvas_context": {"existing_nodes": []},
                    "preferences": {"max_suggestions": 5}
                },
                headers=auth_headers
            )
            
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            data = response.json()
            assert "error" in data
            
        # Test malformed AI response
        with patch('backend.services.canvas_ai_service.CanvasAIService.structure_text',
                  side_effect=ValueError("Invalid AI response format")):
            response = await async_client.post(
                "/api/canvas-ai/structure-text",
                json={
                    "text": "Test text",
                    "canvas_context": {"existing_nodes": []},
                    "preferences": {"max_suggestions": 5}
                },
                headers=auth_headers
            )
            
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            
        # Test service unavailable
        with patch('backend.services.canvas_ai_service.CanvasAIService.structure_text',
                  side_effect=ConnectionError("AI service unavailable")):
            response = await async_client.post(
                "/api/canvas-ai/structure-text",
                json={
                    "text": "Test text",
                    "canvas_context": {"existing_nodes": []},
                    "preferences": {"max_suggestions": 5}
                },
                headers=auth_headers
            )
            
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    @pytest.mark.asyncio
    async def test_performance_under_load(self, async_client, auth_headers):
        """Test system performance under concurrent load."""
        
        request_data = {
            "text": "Performance test request",
            "canvas_context": {"existing_nodes": []},
            "preferences": {"max_suggestions": 3}
        }
        
        mock_response = AIAnalysisResponse(
            analysis_type="text_structure",
            suggestions=[],
            confidence=0.8,
            processing_time=1.0
        )
        
        async def make_request():
            with patch('backend.services.canvas_ai_service.CanvasAIService.structure_text',
                      return_value=mock_response):
                return await async_client.post(
                    "/api/canvas-ai/structure-text",
                    json=request_data,
                    headers=auth_headers
                )
        
        # Make 10 concurrent requests
        start_time = datetime.now()
        tasks = [make_request() for _ in range(10)]
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = datetime.now()
        
        # Check that most requests succeeded
        successful_responses = [r for r in responses if not isinstance(r, Exception)]
        assert len(successful_responses) >= 8  # Allow for some failures under load
        
        # Check response times are reasonable
        total_time = (end_time - start_time).total_seconds()
        assert total_time < 30  # Should complete within 30 seconds
        
        for response in successful_responses:
            assert response.status_code == status.HTTP_200_OK

    @pytest.mark.asyncio
    async def test_canvas_state_persistence(self, async_client, auth_headers):
        """Test that canvas state is properly maintained across requests."""
        
        # This test would typically require actual database integration
        # For now, we test the API contract for state handling
        
        initial_nodes = [
            {"id": "node1", "type": "goal", "content": "Initial goal"},
            {"id": "node2", "type": "challenge", "content": "Initial challenge"}
        ]
        
        # Test that existing nodes are properly referenced in requests
        request_with_context = {
            "text": "Add new strategic initiative",
            "canvas_context": {
                "existing_nodes": initial_nodes,
                "canvas_type": "strategic_planning",
                "canvas_id": str(uuid4())
            },
            "preferences": {"max_suggestions": 5}
        }
        
        mock_response = AIAnalysisResponse(
            analysis_type="text_structure",
            suggestions=[
                NodeSuggestion(
                    suggested_node_type=NodeType.INITIATIVE,
                    title="New Initiative",
                    content="Strategic initiative that builds on existing context",
                    rationale="Complements existing goals and addresses challenges",
                    confidence=0.87
                )
            ],
            confidence=0.87,
            processing_time=1.3
        )
        
        with patch('backend.services.canvas_ai_service.CanvasAIService.structure_text',
                  return_value=mock_response) as mock_service:
            response = await async_client.post(
                "/api/canvas-ai/structure-text",
                json=request_with_context,
                headers=auth_headers
            )
            
            assert response.status_code == status.HTTP_200_OK
            
            # Verify that the service was called with the context
            mock_service.assert_called_once()
            call_args = mock_service.call_args[0][0]  # First argument (request)
            assert len(call_args.canvas_context["existing_nodes"]) == 2
            assert call_args.canvas_context["canvas_id"] is not None

    @pytest.mark.asyncio
    async def test_health_check_integration(self, async_client):
        """Test health check endpoint integration."""
        
        response = await async_client.get("/api/canvas-ai/health")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "healthy"
        assert "ai_service" in data
        assert "timestamp" in data
        assert "version" in data

    @pytest.mark.asyncio
    async def test_authentication_integration(self, async_client):
        """Test authentication integration across all endpoints."""
        
        endpoints_and_data = [
            ("/api/canvas-ai/structure-text", {
                "text": "Test", 
                "canvas_context": {"existing_nodes": []},
                "preferences": {"max_suggestions": 5}
            }),
            ("/api/canvas-ai/analyze-connections", {
                "nodes": [{"id": "1", "type": "goal", "content": "Test"}],
                "canvas_context": {"existing_connections": []},
                "analysis_depth": "standard"
            }),
            ("/api/canvas-ai/identify-themes", {
                "canvas_elements": {"nodes": [], "connections": []},
                "analysis_scope": "standard"
            }),
            ("/api/canvas-ai/optimize-canvas", {
                "current_canvas": {"nodes": [], "connections": []},
                "optimization_goals": ["completeness"]
            })
        ]
        
        for endpoint, data in endpoints_and_data:
            # Test without auth headers
            response = await async_client.post(endpoint, json=data)
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
            
            # Test with invalid auth headers  
            invalid_headers = {"Authorization": "Bearer invalid-token"}
            response = await async_client.post(endpoint, json=data, headers=invalid_headers)
            # Might be 401 or 403 depending on auth implementation
            assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]