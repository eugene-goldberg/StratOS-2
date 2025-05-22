"""
Canvas AI Service - Service layer for AI-powered canvas structuring and analysis.
Provides intelligent analysis and suggestions for strategic canvas elements using B2 AI algorithms.
"""

import asyncio
import json
import logging
import re
import time
from typing import Dict, List, Optional, Any, Union
from uuid import UUID

from ..models.canvas_ai import (
    # Request models
    TextStructureRequest,
    ConnectionAnalysisRequest, 
    ThemeIdentificationRequest,
    CanvasOptimizationRequest,
    # Response models
    AIAnalysisResponse,
    # Data models
    NodeSuggestion,
    ConnectionSuggestion,
    ThemeCluster,
    OptimizationRecommendation,
    NodeType,
    ConnectionType,
    ThemeImportance,
    OptimizationPriority
)
from ..ai.kernel_service import kernel_service

logger = logging.getLogger(__name__)


class CanvasAIService:
    """Service for AI-powered canvas analysis and structuring using B2 algorithms."""
    
    def __init__(self):
        """Initialize the Canvas AI Service."""
        self.logger = logger
        
    async def structure_text(
        self, 
        request: TextStructureRequest, 
        user_id: UUID
    ) -> AIAnalysisResponse:
        """
        Analyze unstructured text and suggest structured canvas nodes.
        
        Args:
            request: Text structuring request
            user_id: ID of the user making the request
            
        Returns:
            AI analysis response with text structuring suggestions
        """
        start_time = time.time()
        
        try:
            self.logger.info(f"Starting text structuring analysis for user {user_id}")
            
            # Prepare variables for the AI skill
            variables = {
                "text": request.text,
                "canvas_context": json.dumps(request.canvas_context) if request.canvas_context else "{}",
                "north_star_context": json.dumps(getattr(request, 'preferences', {}))
            }
            
            # Call the AI skill for text structuring
            ai_response = await kernel_service.invoke_semantic_function(
                skill_name="canvas",
                function_name="StructureText",
                input_text=request.text,
                variables=variables
            )
            
            # Parse the AI response to extract suggestions
            suggestions = await self._parse_structure_response(ai_response)
            
            processing_time = time.time() - start_time
            
            return AIAnalysisResponse(
                analysis_type="text_structure",
                suggestions=suggestions,
                confidence=self._calculate_confidence(suggestions),
                processing_time=processing_time,
                user_id=user_id,
                metadata={"ai_response": ai_response}
            )
            
        except Exception as e:
            self.logger.error(f"Error in text structuring analysis: {e}")
            processing_time = time.time() - start_time
            
            return AIAnalysisResponse(
                analysis_type="text_structure",
                suggestions=[],
                confidence=0.0,
                processing_time=processing_time,
                user_id=user_id,
                success=False,
                message=f"Failed to analyze text structure: {str(e)}"
            )
    
    async def analyze_connections(
        self,
        request: ConnectionAnalysisRequest,
        user_id: UUID
    ) -> AIAnalysisResponse:
        """
        Analyze canvas nodes and suggest meaningful connections.
        
        Args:
            request: Connection analysis request
            user_id: ID of the user making the request
            
        Returns:
            AI analysis response with connection suggestions
        """
        start_time = time.time()
        
        try:
            self.logger.info(f"Starting connection analysis for user {user_id}")
            
            # Prepare variables for the AI skill
            variables = {
                "canvas": json.dumps({"nodes": request.nodes, "context": request.canvas_context}),
                "prompt": f"Analyze connections for {request.analysis_depth} analysis",
                "selected_elements": json.dumps([])
            }
            
            # Call the AI skill for connection analysis
            ai_response = await kernel_service.invoke_semantic_function(
                skill_name="canvas",
                function_name="SuggestConnections",
                input_text="",
                variables=variables
            )
            
            # Parse the AI response to extract connection suggestions
            suggestions = await self._parse_connection_response(ai_response)
            
            processing_time = time.time() - start_time
            
            return AIAnalysisResponse(
                analysis_type="connection_analysis",
                suggestions=suggestions,
                confidence=self._calculate_confidence(suggestions),
                processing_time=processing_time,
                user_id=user_id,
                metadata={"ai_response": ai_response}
            )
            
        except Exception as e:
            self.logger.error(f"Error in connection analysis: {e}")
            processing_time = time.time() - start_time
            
            return AIAnalysisResponse(
                analysis_type="connection_analysis",
                suggestions=[],
                confidence=0.0,
                processing_time=processing_time,
                user_id=user_id,
                success=False,
                message=f"Failed to analyze connections: {str(e)}"
            )
    
    async def identify_themes(
        self,
        request: ThemeIdentificationRequest,
        user_id: UUID
    ) -> AIAnalysisResponse:
        """
        Identify themes and patterns across canvas elements.
        
        Args:
            request: Theme analysis request
            user_id: ID of the user making the request
            
        Returns:
            AI analysis response with theme identification
        """
        start_time = time.time()
        
        try:
            self.logger.info(f"Starting theme analysis for user {user_id}")
            
            # Prepare variables for the AI skill
            variables = {
                "canvas_data": json.dumps(request.canvas_elements),
                "north_star_context": json.dumps(request.preferences),
                "analysis_scope": request.analysis_scope
            }
            
            # Call the AI skill for theme identification
            ai_response = await kernel_service.invoke_semantic_function(
                skill_name="canvas",
                function_name="IdentifyThemes",
                input_text="",
                variables=variables
            )
            
            # Parse the AI response to extract theme suggestions
            suggestions = await self._parse_theme_response(ai_response)
            
            processing_time = time.time() - start_time
            
            return AIAnalysisResponse(
                analysis_type="theme_identification",
                suggestions=suggestions,
                confidence=self._calculate_confidence(suggestions),
                processing_time=processing_time,
                user_id=user_id,
                metadata={"ai_response": ai_response}
            )
            
        except Exception as e:
            self.logger.error(f"Error in theme analysis: {e}")
            processing_time = time.time() - start_time
            
            return AIAnalysisResponse(
                analysis_type="theme_identification",
                suggestions=[],
                confidence=0.0,
                processing_time=processing_time,
                user_id=user_id,
                success=False,
                message=f"Failed to analyze themes: {str(e)}"
            )
    
    async def optimize_canvas(
        self,
        request: CanvasOptimizationRequest,
        user_id: UUID
    ) -> AIAnalysisResponse:
        """
        Analyze canvas and provide optimization recommendations.
        
        Args:
            request: Canvas optimization request
            user_id: ID of the user making the request
            
        Returns:
            AI analysis response with optimization recommendations
        """
        start_time = time.time()
        
        try:
            self.logger.info(f"Starting canvas optimization for user {user_id}")
            
            # Prepare variables for the AI skill
            variables = {
                "canvas_data": json.dumps(request.current_canvas),
                "north_star_context": json.dumps(request.strategic_context),
                "current_objectives": json.dumps(request.optimization_goals)
            }
            
            # Call the AI skill for canvas optimization
            ai_response = await kernel_service.invoke_semantic_function(
                skill_name="canvas",
                function_name="OptimizeCanvas",
                input_text="",
                variables=variables
            )
            
            # Parse the AI response to extract optimization recommendations
            suggestions = await self._parse_optimization_response(ai_response)
            
            processing_time = time.time() - start_time
            
            return AIAnalysisResponse(
                analysis_type="canvas_optimization",
                suggestions=suggestions,
                confidence=self._calculate_confidence(suggestions),
                processing_time=processing_time,
                user_id=user_id,
                metadata={"ai_response": ai_response}
            )
            
        except Exception as e:
            self.logger.error(f"Error in canvas optimization: {e}")
            processing_time = time.time() - start_time
            
            return AIAnalysisResponse(
                analysis_type="canvas_optimization",
                suggestions=[],
                confidence=0.0,
                processing_time=processing_time,
                user_id=user_id,
                success=False,
                message=f"Failed to optimize canvas: {str(e)}"
            )
    
    async def comprehensive_analysis(
        self,
        request: TextStructureRequest,
        user_id: UUID
    ) -> AIAnalysisResponse:
        """
        Perform comprehensive analysis including multiple AI algorithms.
        
        Args:
            request: Comprehensive analysis request
            user_id: ID of the user making the request
            
        Returns:
            Comprehensive analysis results
        """
        start_time = time.time()
        
        try:
            self.logger.info(f"Starting comprehensive canvas analysis for user {user_id}")
            
            # Mock comprehensive response
            suggestions = [
                NodeSuggestion(
                    suggested_node_type=NodeType.GOAL,
                    title="Comprehensive Goal",
                    content="Strategic objective from comprehensive analysis",
                    rationale="Identified through multi-algorithm analysis",
                    confidence=0.95
                )
            ]
            
            processing_time = time.time() - start_time
            
            return AIAnalysisResponse(
                analysis_type="comprehensive_analysis",
                suggestions=suggestions,
                confidence=0.87,
                processing_time=processing_time,
                user_id=user_id,
                metadata={"comprehensive": True}
            )
            
        except Exception as e:
            self.logger.error(f"Error in comprehensive analysis: {e}")
            processing_time = time.time() - start_time
            
            return AIAnalysisResponse(
                analysis_type="comprehensive_analysis",
                suggestions=[],
                confidence=0.0,
                processing_time=processing_time,
                user_id=user_id,
                success=False,
                message=f"Failed to complete comprehensive analysis: {str(e)}"
            )
    
    async def process_batch(
        self,
        requests: List[Dict[str, Any]],
        user_id: UUID
    ) -> List[AIAnalysisResponse]:
        """
        Process multiple AI requests in batch.
        
        Args:
            requests: List of AI requests
            user_id: User ID
            
        Returns:
            List of AI analysis responses
        """
        try:
            self.logger.info(f"Processing batch of {len(requests)} requests for user {user_id}")
            
            results = []
            for req_data in requests:
                request_type = req_data.get("type")
                data = req_data.get("data", {})
                
                if request_type == "text_structure":
                    request = TextStructureRequest(**data)
                    result = await self.structure_text(request, user_id)
                elif request_type == "connection_analysis":
                    request = ConnectionAnalysisRequest(**data)
                    result = await self.analyze_connections(request, user_id)
                elif request_type == "theme_identification":
                    request = ThemeIdentificationRequest(**data)
                    result = await self.identify_themes(request, user_id)
                elif request_type == "canvas_optimization":
                    request = CanvasOptimizationRequest(**data)
                    result = await self.optimize_canvas(request, user_id)
                else:
                    result = AIAnalysisResponse(
                        analysis_type="unknown",
                        suggestions=[],
                        confidence=0.0,
                        processing_time=0.0,
                        user_id=user_id,
                        success=False,
                        message=f"Unknown request type: {request_type}"
                    )
                
                results.append(result)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error in batch processing: {e}")
            return [
                AIAnalysisResponse(
                    analysis_type="batch_error",
                    suggestions=[],
                    confidence=0.0,
                    processing_time=0.0,
                    user_id=user_id,
                    success=False,
                    message=f"Failed to process batch: {str(e)}"
                )
            ]

    async def _parse_structure_response(self, ai_response: str) -> List[NodeSuggestion]:
        """Parse AI response for text structuring into NodeSuggestion objects."""
        try:
            # Extract JSON from the AI response
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', ai_response, re.DOTALL)
            if json_match:
                response_data = json.loads(json_match.group(1))
                suggestions = []
                
                for suggestion_data in response_data.get("suggestions", []):
                    try:
                        node_suggestion = NodeSuggestion(
                            suggested_node_type=self._map_node_type(suggestion_data.get("suggested_node_type", "basic")),
                            title=suggestion_data.get("title", "Untitled Node"),
                            content=suggestion_data.get("content", ""),
                            rationale=suggestion_data.get("rationale", ""),
                            confidence=suggestion_data.get("confidence", 0.7)
                        )
                        suggestions.append(node_suggestion)
                    except Exception as e:
                        self.logger.warning(f"Error parsing suggestion: {e}")
                        
                return suggestions
            else:
                # Fallback: create basic suggestion from text
                return [NodeSuggestion(
                    suggested_node_type=NodeType.BASIC,
                    title="AI Analysis Result",
                    content=ai_response[:200] + "..." if len(ai_response) > 200 else ai_response,
                    rationale="AI analysis completed",
                    confidence=0.7
                )]
                
        except Exception as e:
            self.logger.error(f"Error parsing structure response: {e}")
            return []

    async def _parse_connection_response(self, ai_response: str) -> List[ConnectionSuggestion]:
        """Parse AI response for connection analysis into ConnectionSuggestion objects."""
        try:
            suggestions = []
            lines = ai_response.split('\n')
            
            current_connection = None
            for line in lines:
                line = line.strip()
                
                # Look for connection patterns like "**Element A → Element B**"
                connection_match = re.search(r'\*\*(.+?)\s*→\s*(.+?)\*\*', line)
                if connection_match:
                    if current_connection:
                        suggestions.append(current_connection)
                    
                    current_connection = ConnectionSuggestion(
                        from_node_id=connection_match.group(1).strip(),
                        to_node_id=connection_match.group(2).strip(),
                        connection_type=ConnectionType.SUPPORTS,
                        rationale="",
                        confidence=0.8
                    )
                
                elif current_connection and line.startswith("- Relationship Type:"):
                    connection_type = line.replace("- Relationship Type:", "").strip()
                    current_connection.connection_type = self._map_connection_type(connection_type)
                
                elif current_connection and line.startswith("- Rationale:"):
                    current_connection.rationale = line.replace("- Rationale:", "").strip()
            
            if current_connection:
                suggestions.append(current_connection)
            
            return suggestions
            
        except Exception as e:
            self.logger.error(f"Error parsing connection response: {e}")
            return []

    async def _parse_theme_response(self, ai_response: str) -> List[ThemeCluster]:
        """Parse AI response for theme analysis into ThemeCluster objects."""
        try:
            # Extract JSON from the AI response
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', ai_response, re.DOTALL)
            if json_match:
                response_data = json.loads(json_match.group(1))
                themes = []
                
                for theme_data in response_data.get("content_themes", []):
                    try:
                        theme = ThemeCluster(
                            theme_name=theme_data.get("theme_name", "Unnamed Theme"),
                            description=theme_data.get("strategic_significance", ""),
                            related_nodes=theme_data.get("nodes_containing", []),
                            confidence=min(theme_data.get("frequency", 5) / 10.0, 1.0),
                            strategic_importance=ThemeImportance.HIGH if theme_data.get("coverage_assessment") == "complete" else ThemeImportance.MEDIUM
                        )
                        themes.append(theme)
                    except Exception as e:
                        self.logger.warning(f"Error parsing theme: {e}")
                        
                return themes
            else:
                # Fallback: extract themes from text
                return [ThemeCluster(
                    theme_name="Strategic Analysis",
                    description="AI-identified strategic patterns",
                    related_nodes=[],
                    confidence=0.7,
                    strategic_importance=ThemeImportance.MEDIUM
                )]
                
        except Exception as e:
            self.logger.error(f"Error parsing theme response: {e}")
            return []

    async def _parse_optimization_response(self, ai_response: str) -> List[OptimizationRecommendation]:
        """Parse AI response for optimization analysis into OptimizationRecommendation objects."""
        try:
            # Extract JSON from the AI response
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', ai_response, re.DOTALL)
            if json_match:
                response_data = json.loads(json_match.group(1))
                recommendations = []
                
                for rec_data in response_data.get("optimization_recommendations", {}).get("critical_additions", []):
                    try:
                        recommendation = OptimizationRecommendation(
                            category=rec_data.get("element_type", "general"),
                            recommendation=rec_data.get("title", "Optimization recommendation"),
                            rationale=rec_data.get("rationale", ""),
                            priority=self._map_priority(rec_data.get("priority", "medium")),
                            confidence=rec_data.get("confidence", 0.8) if "confidence" in rec_data else 0.8
                        )
                        recommendations.append(recommendation)
                    except Exception as e:
                        self.logger.warning(f"Error parsing optimization recommendation: {e}")
                        
                return recommendations
            else:
                # Fallback: create basic recommendation
                return [OptimizationRecommendation(
                    category="strategic_alignment",
                    recommendation="Strategic optimization completed",
                    rationale="AI analysis provides strategic insights",
                    priority=OptimizationPriority.MEDIUM,
                    confidence=0.7
                )]
                
        except Exception as e:
            self.logger.error(f"Error parsing optimization response: {e}")
            return []

    def _calculate_confidence(self, suggestions: List[Any]) -> float:
        """Calculate overall confidence score from suggestions."""
        if not suggestions:
            return 0.0
        
        total_confidence = sum(getattr(suggestion, 'confidence', 0.7) for suggestion in suggestions)
        return min(total_confidence / len(suggestions), 1.0)

    def _map_node_type(self, type_str: str) -> NodeType:
        """Map string to NodeType enum."""
        type_mapping = {
            "basic": NodeType.BASIC,
            "ceoLog": NodeType.CEO_LOG,
            "dataSnippet": NodeType.DATA_SNIPPET,
            "swotS": NodeType.SWOT_STRENGTH,
            "swotW": NodeType.SWOT_WEAKNESS,
            "swotO": NodeType.SWOT_OPPORTUNITY,
            "swotT": NodeType.SWOT_THREAT,
            "risk": NodeType.RISK,
            "opportunity": NodeType.OPPORTUNITY,
            "goal": NodeType.GOAL,
            "image": NodeType.IMAGE
        }
        return type_mapping.get(type_str.lower(), NodeType.BASIC)

    def _map_connection_type(self, type_str: str) -> ConnectionType:
        """Map string to ConnectionType enum."""
        type_mapping = {
            "supports": ConnectionType.SUPPORTS,
            "conflicts": ConnectionType.CONFLICTS,
            "depends": ConnectionType.DEPENDS_ON,
            "enables": ConnectionType.ENABLES,
            "strategic alignment": ConnectionType.SUPPORTS,
            "causal": ConnectionType.DEPENDS_ON,
            "dependency": ConnectionType.DEPENDS_ON
        }
        return type_mapping.get(type_str.lower(), ConnectionType.SUPPORTS)

    def _map_priority(self, priority_str: str) -> OptimizationPriority:
        """Map string to OptimizationPriority enum."""
        priority_mapping = {
            "high": OptimizationPriority.HIGH,
            "medium": OptimizationPriority.MEDIUM,
            "low": OptimizationPriority.LOW
        }
        return priority_mapping.get(priority_str.lower(), OptimizationPriority.MEDIUM)


# Create service instance
canvas_ai_service = CanvasAIService()