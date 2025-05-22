"""
Test data fixtures for Canvas AI functionality.
Provides comprehensive test data for all AI structuring components.
"""

import pytest
from uuid import uuid4
from datetime import datetime
from typing import Dict, Any, List

from backend.models.canvas_ai import (
    TextStructureRequest, ConnectionAnalysisRequest,
    ThemeIdentificationRequest, CanvasOptimizationRequest,
    AIAnalysisResponse, NodeSuggestion, ConnectionSuggestion,
    ThemeCluster, OptimizationRecommendation,
    NodeType, ConnectionType, ThemeImportance, OptimizationPriority
)


class CanvasAITestData:
    """Centralized test data for Canvas AI testing."""
    
    @staticmethod
    def sample_text_inputs() -> List[str]:
        """Sample text inputs for structure analysis."""
        return [
            "We need to increase market share by improving product quality and expanding our sales team while reducing operational costs.",
            "Launch innovative AI-powered features to differentiate from competitors and capture emerging market opportunities.",
            "Address customer satisfaction issues through better support processes and streamlined user experience design.",
            "Develop strategic partnerships with key industry players to accelerate growth and market penetration.",
            "Transform our digital infrastructure to support scalable operations and enhanced data analytics capabilities.",
            "Implement sustainable business practices to meet environmental regulations and customer expectations.",
            "Expand internationally into European and Asian markets while maintaining operational excellence.",
            "Build competitive advantages through advanced technology adoption and workforce development programs.",
            "Optimize supply chain efficiency and reduce costs through automation and vendor consolidation.",
            "Create new revenue streams through subscription services and premium product offerings."
        ]
    
    @staticmethod
    def sample_canvas_nodes() -> List[Dict[str, Any]]:
        """Sample canvas nodes for testing."""
        return [
            {
                "id": "goal_1",
                "type": "goal", 
                "content": "Achieve 25% market share by 2025",
                "metadata": {"priority": "high", "timeline": "2_years"}
            },
            {
                "id": "goal_2",
                "type": "goal",
                "content": "Improve customer satisfaction score to 95%",
                "metadata": {"priority": "high", "timeline": "1_year"}
            },
            {
                "id": "initiative_1",
                "type": "initiative",
                "content": "Launch AI-powered product recommendation engine",
                "metadata": {"department": "product", "budget": "500k"}
            },
            {
                "id": "initiative_2",
                "type": "initiative", 
                "content": "Implement comprehensive customer success program",
                "metadata": {"department": "customer_success", "budget": "300k"}
            },
            {
                "id": "challenge_1",
                "type": "challenge",
                "content": "Legacy system integration complexity",
                "metadata": {"severity": "high", "impact": "technical"}
            },
            {
                "id": "challenge_2",
                "type": "challenge",
                "content": "Intense competitive pressure in core markets",
                "metadata": {"severity": "medium", "impact": "market"}
            },
            {
                "id": "capability_1",
                "type": "capability",
                "content": "Advanced data analytics and machine learning expertise",
                "metadata": {"maturity": "high", "strategic_value": "high"}
            },
            {
                "id": "capability_2",
                "type": "capability",
                "content": "Strong customer relationship management processes",
                "metadata": {"maturity": "medium", "strategic_value": "medium"}
            },
            {
                "id": "metric_1",
                "type": "metric",
                "content": "Monthly recurring revenue growth rate",
                "metadata": {"frequency": "monthly", "target": "15%"}
            },
            {
                "id": "metric_2",
                "type": "metric",
                "content": "Customer Net Promoter Score (NPS)",
                "metadata": {"frequency": "quarterly", "target": "70+"}
            }
        ]
    
    @staticmethod
    def sample_canvas_connections() -> List[Dict[str, Any]]:
        """Sample canvas connections for testing."""
        return [
            {
                "from": "initiative_1",
                "to": "goal_1",
                "type": "supports",
                "strength": 0.9
            },
            {
                "from": "initiative_2", 
                "to": "goal_2",
                "type": "supports",
                "strength": 0.85
            },
            {
                "from": "challenge_1",
                "to": "initiative_1",
                "type": "blocks",
                "strength": 0.7
            },
            {
                "from": "capability_1",
                "to": "initiative_1",
                "type": "enables",
                "strength": 0.95
            },
            {
                "from": "capability_2",
                "to": "initiative_2",
                "type": "enables",
                "strength": 0.8
            },
            {
                "from": "metric_1",
                "to": "goal_1",
                "type": "measures",
                "strength": 0.9
            },
            {
                "from": "metric_2",
                "to": "goal_2",
                "type": "measures",
                "strength": 0.95
            }
        ]
    
    @staticmethod
    def sample_ai_responses() -> Dict[str, Dict[str, Any]]:
        """Sample AI skill responses for different analysis types."""
        return {
            "text_structure": {
                "suggestions": [
                    {
                        "suggested_node_type": "goal",
                        "title": "Market Leadership Goal",
                        "content": "Achieve market leadership in our industry segment",
                        "rationale": "Strategic objective aligned with business vision",
                        "confidence": 0.92,
                        "metadata": {
                            "strategic_framework": "competitive_positioning",
                            "time_horizon": "long_term",
                            "success_criteria": ["market_share", "brand_recognition"]
                        }
                    },
                    {
                        "suggested_node_type": "initiative",
                        "title": "Product Innovation Initiative",
                        "content": "Develop next-generation product features",
                        "rationale": "Innovation drives competitive advantage",
                        "confidence": 0.88,
                        "metadata": {
                            "department": "product",
                            "estimated_timeline": "9_months",
                            "resource_requirements": ["engineering", "design"]
                        }
                    },
                    {
                        "suggested_node_type": "challenge",
                        "title": "Resource Allocation Challenge",
                        "content": "Limited budget for simultaneous initiatives",
                        "rationale": "Financial constraints require prioritization",
                        "confidence": 0.85,
                        "metadata": {
                            "impact_area": "execution",
                            "mitigation_options": ["phased_approach", "external_funding"]
                        }
                    }
                ],
                "analysis_metadata": {
                    "processing_approach": "strategic_decomposition",
                    "confidence_factors": ["clear_objectives", "strategic_context"],
                    "identified_themes": ["growth", "innovation", "competitiveness"]
                }
            },
            "connection_analysis": {
                "suggestions": [
                    {
                        "from_node_id": "initiative_1",
                        "to_node_id": "goal_1",
                        "connection_type": "supports",
                        "rationale": "Product innovation directly supports market leadership goals",
                        "confidence": 0.91,
                        "metadata": {
                            "relationship_strength": "strong",
                            "dependency_type": "enabling",
                            "risk_factors": ["execution_complexity"]
                        }
                    },
                    {
                        "from_node_id": "challenge_1",
                        "to_node_id": "initiative_1",
                        "connection_type": "blocks",
                        "rationale": "Resource constraints may impede innovation efforts",
                        "confidence": 0.83,
                        "metadata": {
                            "relationship_strength": "medium",
                            "dependency_type": "constraining",
                            "mitigation_strategies": ["budget_reallocation", "phased_execution"]
                        }
                    }
                ],
                "analysis_metadata": {
                    "connection_density": "optimal",
                    "strategic_coherence": 0.87,
                    "identified_patterns": ["goal_initiative_alignment", "resource_constraints"]
                }
            },
            "theme_identification": {
                "suggestions": [
                    {
                        "theme_name": "Digital Transformation",
                        "description": "Comprehensive digitization and technology adoption",
                        "related_nodes": ["initiative_1", "capability_1", "challenge_1"],
                        "confidence": 0.89,
                        "strategic_importance": "high",
                        "metadata": {
                            "theme_category": "technology",
                            "cross_functional_impact": True,
                            "transformation_scope": "enterprise_wide"
                        }
                    },
                    {
                        "theme_name": "Customer Experience Excellence",
                        "description": "Focus on superior customer satisfaction and engagement",
                        "related_nodes": ["goal_2", "initiative_2", "metric_2"],
                        "confidence": 0.86,
                        "strategic_importance": "high",
                        "metadata": {
                            "theme_category": "customer",
                            "cross_functional_impact": True,
                            "transformation_scope": "customer_facing"
                        }
                    }
                ],
                "analysis_metadata": {
                    "theme_coverage": 0.85,
                    "thematic_coherence": 0.88,
                    "identified_gaps": ["operational_efficiency", "financial_optimization"]
                }
            },
            "canvas_optimization": {
                "suggestions": [
                    {
                        "category": "strategic_alignment",
                        "recommendation": "Add competitive analysis framework",
                        "rationale": "Missing external market perspective in current canvas",
                        "priority": "high",
                        "confidence": 0.93,
                        "implementation_steps": [
                            "Conduct comprehensive competitor analysis",
                            "Map competitive positioning for each initiative",
                            "Identify unique value propositions and differentiators"
                        ],
                        "estimated_effort": "medium",
                        "expected_impact": "high",
                        "metadata": {
                            "framework_type": "porter_five_forces",
                            "analysis_scope": "market_environment"
                        }
                    },
                    {
                        "category": "completeness",
                        "recommendation": "Define measurable success metrics for all initiatives",
                        "rationale": "Lack of quantifiable outcomes limits progress tracking",
                        "priority": "medium",
                        "confidence": 0.87,
                        "implementation_steps": [
                            "Identify key performance indicators for each initiative",
                            "Set specific, measurable targets with timelines",
                            "Establish regular monitoring and reporting processes"
                        ],
                        "estimated_effort": "low",
                        "expected_impact": "medium",
                        "metadata": {
                            "measurement_framework": "okr",
                            "tracking_frequency": "monthly"
                        }
                    }
                ],
                "analysis_metadata": {
                    "optimization_score": 0.72,
                    "completeness_score": 0.68,
                    "strategic_coherence": 0.81,
                    "actionability_score": 0.75
                }
            }
        }


@pytest.fixture
def canvas_ai_test_data():
    """Fixture providing access to Canvas AI test data."""
    return CanvasAITestData()


@pytest.fixture
def sample_text_structure_requests(canvas_ai_test_data):
    """Fixture providing sample text structure requests."""
    text_inputs = canvas_ai_test_data.sample_text_inputs()
    
    return [
        TextStructureRequest(
            text=text,
            canvas_context={
                "existing_nodes": canvas_ai_test_data.sample_canvas_nodes()[:3],
                "canvas_type": "strategic_planning"
            },
            preferences={
                "max_suggestions": 5,
                "confidence_threshold": 0.7
            }
        )
        for text in text_inputs[:3]
    ]


@pytest.fixture
def sample_connection_analysis_requests(canvas_ai_test_data):
    """Fixture providing sample connection analysis requests."""
    nodes = canvas_ai_test_data.sample_canvas_nodes()
    
    return [
        ConnectionAnalysisRequest(
            nodes=nodes[:4],
            canvas_context={
                "existing_connections": canvas_ai_test_data.sample_canvas_connections()[:2],
                "canvas_type": "strategic_planning"
            },
            analysis_depth="comprehensive"
        ),
        ConnectionAnalysisRequest(
            nodes=nodes[2:6],
            canvas_context={
                "existing_connections": [],
                "canvas_type": "operational_planning"
            },
            analysis_depth="standard"
        )
    ]


@pytest.fixture
def sample_theme_identification_requests(canvas_ai_test_data):
    """Fixture providing sample theme identification requests."""
    nodes = canvas_ai_test_data.sample_canvas_nodes()
    connections = canvas_ai_test_data.sample_canvas_connections()
    
    return [
        ThemeIdentificationRequest(
            canvas_elements={
                "nodes": nodes[:6],
                "connections": connections[:4]
            },
            analysis_scope="comprehensive"
        ),
        ThemeIdentificationRequest(
            canvas_elements={
                "nodes": nodes[3:8],
                "connections": connections[2:6]
            },
            analysis_scope="focused"
        )
    ]


@pytest.fixture
def sample_canvas_optimization_requests(canvas_ai_test_data):
    """Fixture providing sample canvas optimization requests."""
    nodes = canvas_ai_test_data.sample_canvas_nodes()
    connections = canvas_ai_test_data.sample_canvas_connections()
    
    return [
        CanvasOptimizationRequest(
            current_canvas={
                "nodes": nodes[:5],
                "connections": connections[:3]
            },
            optimization_goals=["completeness", "strategic_alignment", "actionability"],
            strategic_context={
                "industry": "technology",
                "company_stage": "growth",
                "market_conditions": "competitive",
                "organization_size": "mid_market"
            }
        ),
        CanvasOptimizationRequest(
            current_canvas={
                "nodes": nodes[2:7],
                "connections": connections[1:5]
            },
            optimization_goals=["coherence", "feasibility"],
            strategic_context={
                "industry": "healthcare",
                "company_stage": "mature",
                "market_conditions": "regulated",
                "organization_size": "enterprise"
            }
        )
    ]


@pytest.fixture
def sample_ai_analysis_responses(canvas_ai_test_data):
    """Fixture providing sample AI analysis responses."""
    responses_data = canvas_ai_test_data.sample_ai_responses()
    
    return {
        "text_structure": AIAnalysisResponse(
            analysis_type="text_structure",
            suggestions=[
                NodeSuggestion(**suggestion) 
                for suggestion in responses_data["text_structure"]["suggestions"]
            ],
            confidence=0.88,
            processing_time=1.5,
            metadata=responses_data["text_structure"]["analysis_metadata"]
        ),
        "connection_analysis": AIAnalysisResponse(
            analysis_type="connection_analysis",
            suggestions=[
                ConnectionSuggestion(**suggestion)
                for suggestion in responses_data["connection_analysis"]["suggestions"]
            ],
            confidence=0.87,
            processing_time=2.1,
            metadata=responses_data["connection_analysis"]["analysis_metadata"]
        ),
        "theme_identification": AIAnalysisResponse(
            analysis_type="theme_identification",
            suggestions=[
                ThemeCluster(**suggestion)
                for suggestion in responses_data["theme_identification"]["suggestions"]
            ],
            confidence=0.87,
            processing_time=1.8,
            metadata=responses_data["theme_identification"]["analysis_metadata"]
        ),
        "canvas_optimization": AIAnalysisResponse(
            analysis_type="canvas_optimization",
            suggestions=[
                OptimizationRecommendation(**suggestion)
                for suggestion in responses_data["canvas_optimization"]["suggestions"]
            ],
            confidence=0.90,
            processing_time=3.2,
            metadata=responses_data["canvas_optimization"]["analysis_metadata"]
        )
    }


@pytest.fixture
def mock_user_ids():
    """Fixture providing sample user IDs for testing."""
    return [uuid4() for _ in range(5)]


@pytest.fixture
def sample_canvas_contexts():
    """Fixture providing various canvas contexts for testing."""
    return [
        {
            "existing_nodes": [],
            "canvas_type": "strategic_planning",
            "canvas_id": str(uuid4()),
            "user_preferences": {
                "analysis_style": "comprehensive",
                "industry_focus": "technology"
            }
        },
        {
            "existing_nodes": CanvasAITestData.sample_canvas_nodes()[:3],
            "canvas_type": "operational_planning",
            "canvas_id": str(uuid4()),
            "user_preferences": {
                "analysis_style": "focused",
                "industry_focus": "healthcare"
            }
        },
        {
            "existing_nodes": CanvasAITestData.sample_canvas_nodes()[:5],
            "canvas_type": "innovation_planning",
            "canvas_id": str(uuid4()),
            "user_preferences": {
                "analysis_style": "creative",
                "industry_focus": "fintech"
            }
        }
    ]


@pytest.fixture
def sample_strategic_contexts():
    """Fixture providing various strategic contexts for testing."""
    return [
        {
            "industry": "technology",
            "company_stage": "startup",
            "market_conditions": "emerging",
            "organization_size": "small",
            "geographical_scope": "local",
            "competitive_intensity": "high"
        },
        {
            "industry": "healthcare",
            "company_stage": "growth",
            "market_conditions": "regulated",
            "organization_size": "mid_market",
            "geographical_scope": "national",
            "competitive_intensity": "medium"
        },
        {
            "industry": "financial_services",
            "company_stage": "mature",
            "market_conditions": "consolidated",
            "organization_size": "enterprise",
            "geographical_scope": "global",
            "competitive_intensity": "low"
        }
    ]


@pytest.fixture
def performance_test_data():
    """Fixture providing data for performance testing."""
    return {
        "large_text_input": " ".join([
            "Strategic initiative" for _ in range(1000)
        ]) + " focused on comprehensive market expansion and operational excellence.",
        "many_nodes": [
            {
                "id": f"node_{i}",
                "type": "goal" if i % 3 == 0 else "initiative" if i % 3 == 1 else "challenge",
                "content": f"Test node content {i}"
            }
            for i in range(100)
        ],
        "many_connections": [
            {
                "from": f"node_{i}",
                "to": f"node_{i+1}",
                "type": "supports"
            }
            for i in range(99)
        ]
    }


@pytest.fixture
def edge_case_test_data():
    """Fixture providing edge case test data."""
    return {
        "empty_text": "",
        "very_long_text": "Strategic planning " * 5000,
        "special_characters_text": "Strategic planning with émojis 🚀 and spéçial charactërs!",
        "minimal_node": {
            "id": "minimal",
            "type": "goal",
            "content": "X"
        },
        "maximal_node": {
            "id": "maximal",
            "type": "initiative", 
            "content": "Very detailed initiative description " * 100,
            "metadata": {
                "key_" + str(i): f"value_{i}" for i in range(50)
            }
        },
        "invalid_node_types": ["invalid_type", "", None, 123],
        "invalid_connection_types": ["invalid_connection", "", None, 456]
    }


# Export all fixtures for easy importing
__all__ = [
    'canvas_ai_test_data',
    'sample_text_structure_requests',
    'sample_connection_analysis_requests', 
    'sample_theme_identification_requests',
    'sample_canvas_optimization_requests',
    'sample_ai_analysis_responses',
    'mock_user_ids',
    'sample_canvas_contexts',
    'sample_strategic_contexts',
    'performance_test_data',
    'edge_case_test_data'
]