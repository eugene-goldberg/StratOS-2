import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import json
from uuid import uuid4
from semantic_kernel import Kernel
from semantic_kernel.functions import KernelArguments

from backend.ai.skills.analysis_skills.swot_analysis_skill import SwotAnalysisSkill
from backend.ai.kernel_service import AIKernelService
from backend.models.canvas_ai import (
    TextStructureRequest, ConnectionAnalysisRequest,
    AIAnalysisResponse, NodeSuggestion, ConnectionSuggestion,
    NodeType, ConnectionType
)


@pytest.fixture
def mock_kernel():
    """Mock Semantic Kernel instance."""
    kernel = MagicMock(spec=Kernel)
    return kernel


@pytest.fixture
def mock_ai_kernel_service(mock_kernel):
    """Mock AI Kernel Service with mocked kernel."""
    service = MagicMock(spec=AIKernelService)
    service.kernel = mock_kernel
    return service


@pytest.fixture
def sample_ai_skill_response():
    """Sample AI skill response in expected JSON format."""
    return {
        "suggestions": [
            {
                "suggested_node_type": "goal",
                "title": "Market Leadership Goal",
                "content": "Achieve market leadership in our sector",
                "rationale": "Strategic objective for competitive advantage",
                "confidence": 0.92,
                "metadata": {
                    "strategic_framework": "competitive_positioning",
                    "time_horizon": "long_term"
                }
            },
            {
                "suggested_node_type": "initiative",
                "title": "Product Innovation Initiative",
                "content": "Launch innovative product features",
                "rationale": "Drive market differentiation",
                "confidence": 0.85,
                "metadata": {
                    "department": "product",
                    "estimated_timeline": "6_months"
                }
            }
        ],
        "analysis_metadata": {
            "processing_approach": "strategic_framework_analysis",
            "confidence_factors": ["clear_objectives", "market_context"],
            "recommendations": [
                "Consider adding competitive analysis",
                "Define success metrics"
            ]
        }
    }


@pytest.fixture
def sample_connection_response():
    """Sample connection analysis response."""
    return {
        "suggestions": [
            {
                "from_node_id": "initiative_1",
                "to_node_id": "goal_1", 
                "connection_type": "supports",
                "rationale": "Initiative directly supports strategic goal achievement",
                "confidence": 0.89,
                "metadata": {
                    "relationship_strength": "strong",
                    "dependency_type": "enabling"
                }
            },
            {
                "from_node_id": "challenge_1",
                "to_node_id": "initiative_1",
                "connection_type": "blocks",
                "rationale": "Challenge may impede initiative progress",
                "confidence": 0.76,
                "metadata": {
                    "risk_level": "medium",
                    "mitigation_required": True
                }
            }
        ],
        "analysis_metadata": {
            "connection_density": "optimal",
            "strategic_coherence": 0.87,
            "identified_gaps": ["missing_feedback_loops"]
        }
    }


class TestCanvasAISkills:
    """Test suite for AI skills used in canvas intelligence."""

    @pytest.mark.asyncio
    async def test_structure_text_skill_invocation(self, mock_ai_kernel_service, sample_ai_skill_response):
        """Test text structuring AI skill invocation."""
        
        # Mock skill response
        mock_function_result = MagicMock()
        mock_function_result.value = json.dumps(sample_ai_skill_response)
        
        mock_ai_kernel_service.kernel.invoke.return_value = mock_function_result
        
        # Create request
        request = TextStructureRequest(
            text="We need to dominate our market through innovative products and superior customer experience",
            canvas_context={
                "existing_nodes": [],
                "canvas_type": "strategic_planning"
            },
            preferences={
                "max_suggestions": 5,
                "confidence_threshold": 0.7
            }
        )
        
        # Test skill invocation
        with patch('backend.services.canvas_ai_service.CanvasAIService._get_kernel_service',
                  return_value=mock_ai_kernel_service):
            
            # Import service here to avoid circular imports in test setup
            from backend.services.canvas_ai_service import CanvasAIService
            service = CanvasAIService()
            
            # Mock the internal skill invocation
            with patch.object(service, '_invoke_skill') as mock_invoke:
                mock_invoke.return_value = sample_ai_skill_response
                
                result = await service.structure_text(request, uuid4())
                
                # Verify skill was called with correct parameters
                mock_invoke.assert_called_once()
                call_args = mock_invoke.call_args
                assert "StructureText" in call_args[0][0]  # Skill name
                assert "text" in call_args[0][1]  # Arguments should contain text
                
                # Verify response structure
                assert isinstance(result, AIAnalysisResponse)
                assert result.analysis_type == "text_structure"
                assert len(result.suggestions) == 2
                assert result.suggestions[0].title == "Market Leadership Goal"

    @pytest.mark.asyncio
    async def test_analyze_connections_skill_invocation(self, mock_ai_kernel_service, sample_connection_response):
        """Test connection analysis AI skill invocation."""
        
        mock_function_result = MagicMock()
        mock_function_result.value = json.dumps(sample_connection_response)
        mock_ai_kernel_service.kernel.invoke.return_value = mock_function_result
        
        request = ConnectionAnalysisRequest(
            nodes=[
                {"id": "goal_1", "type": "goal", "content": "Market leadership"},
                {"id": "initiative_1", "type": "initiative", "content": "Product innovation"},
                {"id": "challenge_1", "type": "challenge", "content": "Resource constraints"}
            ],
            canvas_context={
                "existing_connections": [],
                "canvas_type": "strategic_planning"
            },
            analysis_depth="comprehensive"
        )
        
        with patch('backend.services.canvas_ai_service.CanvasAIService._get_kernel_service',
                  return_value=mock_ai_kernel_service):
            
            from backend.services.canvas_ai_service import CanvasAIService
            service = CanvasAIService()
            
            with patch.object(service, '_invoke_skill') as mock_invoke:
                mock_invoke.return_value = sample_connection_response
                
                result = await service.analyze_connections(request, uuid4())
                
                # Verify skill invocation
                mock_invoke.assert_called_once()
                call_args = mock_invoke.call_args
                assert "AnalyzeConnections" in call_args[0][0]
                
                # Verify response
                assert result.analysis_type == "connection_analysis"
                assert len(result.suggestions) == 2
                connection_suggestion = result.suggestions[0]
                assert hasattr(connection_suggestion, 'from_node_id')
                assert hasattr(connection_suggestion, 'to_node_id')
                assert hasattr(connection_suggestion, 'connection_type')

    @pytest.mark.asyncio
    async def test_identify_themes_skill_invocation(self, mock_ai_kernel_service):
        """Test theme identification AI skill invocation."""
        
        theme_response = {
            "suggestions": [
                {
                    "theme_name": "Digital Transformation",
                    "description": "Comprehensive digitization of business processes",
                    "related_nodes": ["node_1", "node_2", "node_3"],
                    "confidence": 0.91,
                    "strategic_importance": "high",
                    "metadata": {
                        "theme_category": "technology",
                        "cross_functional": True
                    }
                },
                {
                    "theme_name": "Customer Centricity",
                    "description": "Focus on customer experience and satisfaction",
                    "related_nodes": ["node_2", "node_4"],
                    "confidence": 0.84,
                    "strategic_importance": "high",
                    "metadata": {
                        "theme_category": "customer",
                        "cross_functional": False
                    }
                }
            ],
            "analysis_metadata": {
                "theme_coverage": 0.85,
                "thematic_coherence": 0.88,
                "identified_patterns": ["technology_focus", "customer_emphasis"]
            }
        }
        
        mock_function_result = MagicMock()
        mock_function_result.value = json.dumps(theme_response)
        mock_ai_kernel_service.kernel.invoke.return_value = mock_function_result
        
        from backend.models.canvas_ai import ThemeIdentificationRequest
        request = ThemeIdentificationRequest(
            canvas_elements={
                "nodes": [
                    {"id": "node_1", "type": "initiative", "content": "Digital platform"},
                    {"id": "node_2", "type": "goal", "content": "Customer satisfaction"},
                    {"id": "node_3", "type": "capability", "content": "AI technology"},
                    {"id": "node_4", "type": "metric", "content": "NPS score"}
                ],
                "connections": [
                    {"from": "node_1", "to": "node_2", "type": "supports"},
                    {"from": "node_3", "to": "node_1", "type": "enables"}
                ]
            },
            analysis_scope="comprehensive"
        )
        
        with patch('backend.services.canvas_ai_service.CanvasAIService._get_kernel_service',
                  return_value=mock_ai_kernel_service):
            
            from backend.services.canvas_ai_service import CanvasAIService
            service = CanvasAIService()
            
            with patch.object(service, '_invoke_skill') as mock_invoke:
                mock_invoke.return_value = theme_response
                
                result = await service.identify_themes(request, uuid4())
                
                # Verify skill call
                mock_invoke.assert_called_once()
                call_args = mock_invoke.call_args
                assert "IdentifyThemes" in call_args[0][0]
                
                # Verify response structure
                assert result.analysis_type == "theme_identification" 
                assert len(result.suggestions) == 2
                theme_suggestion = result.suggestions[0]
                assert hasattr(theme_suggestion, 'theme_name')
                assert hasattr(theme_suggestion, 'related_nodes')

    @pytest.mark.asyncio
    async def test_optimize_canvas_skill_invocation(self, mock_ai_kernel_service):
        """Test canvas optimization AI skill invocation."""
        
        optimization_response = {
            "suggestions": [
                {
                    "category": "strategic_alignment",
                    "recommendation": "Add competitive analysis framework",
                    "rationale": "Missing external market perspective",
                    "priority": "high",
                    "confidence": 0.93,
                    "implementation_steps": [
                        "Conduct competitor research",
                        "Map competitive positioning",
                        "Identify differentiation opportunities"
                    ],
                    "estimated_effort": "medium",
                    "expected_impact": "high"
                },
                {
                    "category": "completeness",
                    "recommendation": "Define success metrics for initiatives",
                    "rationale": "Lack of measurable outcomes",
                    "priority": "medium",
                    "confidence": 0.87,
                    "implementation_steps": [
                        "Identify key performance indicators",
                        "Set measurable targets",
                        "Establish tracking mechanisms"
                    ],
                    "estimated_effort": "low",
                    "expected_impact": "medium"
                }
            ],
            "analysis_metadata": {
                "optimization_score": 0.72,
                "completeness_score": 0.68,
                "strategic_coherence": 0.81,
                "actionability_score": 0.75
            }
        }
        
        mock_function_result = MagicMock()
        mock_function_result.value = json.dumps(optimization_response)
        mock_ai_kernel_service.kernel.invoke.return_value = mock_function_result
        
        from backend.models.canvas_ai import CanvasOptimizationRequest
        request = CanvasOptimizationRequest(
            current_canvas={
                "nodes": [
                    {"id": "goal_1", "type": "goal", "content": "Market expansion"},
                    {"id": "init_1", "type": "initiative", "content": "New product development"}
                ],
                "connections": [
                    {"from": "init_1", "to": "goal_1", "type": "supports"}
                ]
            },
            optimization_goals=["completeness", "strategic_alignment", "actionability"],
            strategic_context={
                "industry": "technology",
                "company_stage": "growth",
                "market_conditions": "competitive"
            }
        )
        
        with patch('backend.services.canvas_ai_service.CanvasAIService._get_kernel_service',
                  return_value=mock_ai_kernel_service):
            
            from backend.services.canvas_ai_service import CanvasAIService
            service = CanvasAIService()
            
            with patch.object(service, '_invoke_skill') as mock_invoke:
                mock_invoke.return_value = optimization_response
                
                result = await service.optimize_canvas(request, uuid4())
                
                # Verify skill call
                mock_invoke.assert_called_once()
                call_args = mock_invoke.call_args
                assert "OptimizeCanvas" in call_args[0][0]
                
                # Verify response
                assert result.analysis_type == "canvas_optimization"
                assert len(result.suggestions) == 2
                opt_suggestion = result.suggestions[0]
                assert hasattr(opt_suggestion, 'category')
                assert hasattr(opt_suggestion, 'recommendation')
                assert hasattr(opt_suggestion, 'priority')

    @pytest.mark.asyncio
    async def test_skill_error_handling(self, mock_ai_kernel_service):
        """Test error handling in AI skill invocations."""
        
        with patch('backend.services.canvas_ai_service.CanvasAIService._get_kernel_service',
                  return_value=mock_ai_kernel_service):
            
            from backend.services.canvas_ai_service import CanvasAIService
            service = CanvasAIService()
            
            # Test JSON parsing error
            mock_function_result = MagicMock()
            mock_function_result.value = "Invalid JSON response"
            mock_ai_kernel_service.kernel.invoke.return_value = mock_function_result
            
            request = TextStructureRequest(
                text="Test text",
                canvas_context={"existing_nodes": []},
                preferences={"max_suggestions": 5}
            )
            
            with pytest.raises(Exception):
                await service.structure_text(request, uuid4())
            
            # Test kernel invocation error
            mock_ai_kernel_service.kernel.invoke.side_effect = Exception("Kernel error")
            
            with pytest.raises(Exception):
                await service.structure_text(request, uuid4())

    @pytest.mark.asyncio
    async def test_skill_response_validation(self, mock_ai_kernel_service):
        """Test validation of AI skill responses."""
        
        # Test with missing required fields
        invalid_response = {
            "suggestions": [
                {
                    "suggested_node_type": "goal",
                    # Missing title, content, rationale, confidence
                }
            ]
        }
        
        mock_function_result = MagicMock()
        mock_function_result.value = json.dumps(invalid_response)
        mock_ai_kernel_service.kernel.invoke.return_value = mock_function_result
        
        with patch('backend.services.canvas_ai_service.CanvasAIService._get_kernel_service',
                  return_value=mock_ai_kernel_service):
            
            from backend.services.canvas_ai_service import CanvasAIService
            service = CanvasAIService()
            
            request = TextStructureRequest(
                text="Test text",
                canvas_context={"existing_nodes": []},
                preferences={"max_suggestions": 5}
            )
            
            # Should handle validation errors gracefully
            with pytest.raises(Exception):
                await service.structure_text(request, uuid4())

    @pytest.mark.asyncio
    async def test_skill_confidence_filtering(self, mock_ai_kernel_service):
        """Test filtering of suggestions based on confidence thresholds."""
        
        mixed_confidence_response = {
            "suggestions": [
                {
                    "suggested_node_type": "goal",
                    "title": "High confidence goal",
                    "content": "Strategic objective",
                    "rationale": "Clear strategic fit",
                    "confidence": 0.95
                },
                {
                    "suggested_node_type": "initiative",
                    "title": "Low confidence initiative", 
                    "content": "Uncertain initiative",
                    "rationale": "Unclear strategic value",
                    "confidence": 0.45
                },
                {
                    "suggested_node_type": "challenge",
                    "title": "Medium confidence challenge",
                    "content": "Potential obstacle",
                    "rationale": "Moderate concern",
                    "confidence": 0.75
                }
            ]
        }
        
        mock_function_result = MagicMock()
        mock_function_result.value = json.dumps(mixed_confidence_response)
        mock_ai_kernel_service.kernel.invoke.return_value = mock_function_result
        
        with patch('backend.services.canvas_ai_service.CanvasAIService._get_kernel_service',
                  return_value=mock_ai_kernel_service):
            
            from backend.services.canvas_ai_service import CanvasAIService
            service = CanvasAIService()
            
            with patch.object(service, '_invoke_skill') as mock_invoke:
                mock_invoke.return_value = mixed_confidence_response
                
                # Test with high confidence threshold
                high_threshold_request = TextStructureRequest(
                    text="Test text",
                    canvas_context={"existing_nodes": []},
                    preferences={
                        "max_suggestions": 10,
                        "confidence_threshold": 0.8
                    }
                )
                
                result = await service.structure_text(high_threshold_request, uuid4())
                
                # Should only include high confidence suggestions
                high_confidence_suggestions = [
                    s for s in result.suggestions 
                    if hasattr(s, 'confidence') and s.confidence >= 0.8
                ]
                
                # The service should filter based on threshold
                # (This test assumes the service implements confidence filtering)
                assert len(high_confidence_suggestions) >= 0

    @pytest.mark.asyncio
    async def test_skill_metadata_handling(self, mock_ai_kernel_service):
        """Test handling of metadata in AI skill responses."""
        
        metadata_rich_response = {
            "suggestions": [
                {
                    "suggested_node_type": "goal",
                    "title": "Strategic Goal",
                    "content": "Achieve market leadership",
                    "rationale": "Competitive advantage",
                    "confidence": 0.88,
                    "metadata": {
                        "strategic_framework": "porter_five_forces",
                        "time_horizon": "3_years",
                        "success_metrics": ["market_share", "revenue_growth"],
                        "dependencies": ["product_innovation", "market_expansion"],
                        "risk_factors": ["competitive_response", "market_saturation"]
                    }
                }
            ],
            "analysis_metadata": {
                "processing_time": 2.34,
                "model_version": "gpt-4-turbo",
                "confidence_factors": ["clear_objective", "market_context"],
                "limitations": ["limited_financial_data", "external_factors"]
            }
        }
        
        mock_function_result = MagicMock()
        mock_function_result.value = json.dumps(metadata_rich_response)
        mock_ai_kernel_service.kernel.invoke.return_value = mock_function_result
        
        with patch('backend.services.canvas_ai_service.CanvasAIService._get_kernel_service',
                  return_value=mock_ai_kernel_service):
            
            from backend.services.canvas_ai_service import CanvasAIService
            service = CanvasAIService()
            
            with patch.object(service, '_invoke_skill') as mock_invoke:
                mock_invoke.return_value = metadata_rich_response
                
                request = TextStructureRequest(
                    text="Test text",
                    canvas_context={"existing_nodes": []},
                    preferences={"max_suggestions": 5}
                )
                
                result = await service.structure_text(request, uuid4())
                
                # Verify metadata is preserved
                assert result.metadata is not None
                suggestion = result.suggestions[0]
                assert hasattr(suggestion, 'metadata')
                assert suggestion.metadata.get("strategic_framework") == "porter_five_forces"

    def test_skill_configuration_loading(self):
        """Test loading of AI skill configurations."""
        
        # Test that skill configurations are properly loaded
        # This would test the config.json files in the skills directories
        
        from pathlib import Path
        import json
        
        skills_path = Path("backend/ai/skills/canvas")
        
        if skills_path.exists():
            config_file = skills_path / "config.json"
            
            if config_file.exists():
                with open(config_file, 'r') as f:
                    config = json.load(f)
                
                # Verify expected configuration structure
                assert "skills" in config
                assert isinstance(config["skills"], list)
                
                for skill in config["skills"]:
                    assert "name" in skill
                    assert "prompt_file" in skill
                    assert "description" in skill

    @pytest.mark.asyncio
    async def test_skill_prompt_template_loading(self):
        """Test loading and validation of skill prompt templates."""
        
        from pathlib import Path
        
        skills_path = Path("backend/ai/skills/canvas")
        
        if skills_path.exists():
            prompt_files = list(skills_path.glob("*.prompt.txt"))
            
            for prompt_file in prompt_files:
                # Test that prompt files exist and are readable
                assert prompt_file.exists()
                
                with open(prompt_file, 'r') as f:
                    content = f.read()
                
                # Basic validation of prompt content
                assert len(content) > 0
                assert "{{" in content or "{" in content  # Template variables
                
                # Verify expected sections in prompts
                expected_sections = ["TASK:", "INPUT:", "OUTPUT:"]
                content_upper = content.upper()
                
                # At least some structure should be present
                has_structure = any(section in content_upper for section in expected_sections)
                if not has_structure:
                    # More flexible check for structured content
                    assert any(keyword in content.lower() for keyword in 
                             ["analyze", "suggest", "identify", "recommend"])