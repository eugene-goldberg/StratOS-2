"""
Canvas AI Service - Service layer for AI-powered canvas structuring and analysis.
Provides intelligent analysis and suggestions for strategic canvas elements.
"""

import asyncio
import json
import logging
import time
from typing import Dict, List, Optional, Any, Union
from uuid import UUID

from ..ai.kernel_service import kernel_service
from ..models.canvas_ai import (
    # Request models
    TextStructureRequest,
    ConnectionAnalysisRequest, 
    ThemeAnalysisRequest,
    CanvasOptimizationRequest,
    # Response models
    TextStructureSuggestion,
    ConnectionSuggestionResponse,
    ThemeAnalysisResponse,
    CanvasOptimizationResponse,
    AIAnalysisResponse,
    # Data models
    CanvasData,
    CanvasNode,
    NodeSuggestion,
    NodeConnectionSuggestion
)

logger = logging.getLogger(__name__)


class CanvasAIService:
    """Service for AI-powered canvas analysis and structuring."""
    
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
                "canvas_context": json.dumps(request.canvas_context or {}),
                "north_star_context": json.dumps(request.north_star_context or {})
            }
            
            # Invoke the text structuring AI skill
            ai_response = await kernel_service.invoke_semantic_function(
                skill_name="canvas",
                function_name="StructureText",
                input_text="",
                variables=variables
            )
            
            # Parse the AI response
            if isinstance(ai_response, str):
                # Extract JSON from AI response if it's wrapped in text
                json_start = ai_response.find('{')
                json_end = ai_response.rfind('}') + 1
                if json_start != -1 and json_end > json_start:
                    ai_response = ai_response[json_start:json_end]
                
                response_data = json.loads(ai_response)
            else:
                response_data = ai_response
            
            # Convert to structured response
            suggestions_data = TextStructureSuggestion(**response_data)
            
            execution_time = int((time.time() - start_time) * 1000)
            
            return AIAnalysisResponse(
                analysis_type="text_structure",
                user_id=user_id,
                data=suggestions_data,
                execution_time_ms=execution_time
            )
            
        except Exception as e:
            self.logger.error(f"Error in text structuring analysis: {e}")
            execution_time = int((time.time() - start_time) * 1000)
            
            return AIAnalysisResponse(
                analysis_type="text_structure",
                user_id=user_id,
                success=False,
                message=f"Failed to analyze text structure: {str(e)}",
                execution_time_ms=execution_time
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
            
            # Prepare canvas data for AI analysis
            canvas_json = request.canvas_data.model_dump()
            
            # Prepare variables for the AI skill
            variables = {
                "canvas_data": json.dumps(canvas_json),
                "selected_nodes": json.dumps(request.selected_nodes or []),
                "north_star_context": json.dumps(request.north_star_context or {})
            }
            
            # Invoke the connection analysis AI skill
            ai_response = await kernel_service.invoke_semantic_function(
                skill_name="canvas",
                function_name="AnalyzeConnections", 
                input_text="",
                variables=variables
            )
            
            # Parse the AI response
            if isinstance(ai_response, str):
                json_start = ai_response.find('{')
                json_end = ai_response.rfind('}') + 1
                if json_start != -1 and json_end > json_start:
                    ai_response = ai_response[json_start:json_end]
                
                response_data = json.loads(ai_response)
            else:
                response_data = ai_response
            
            # Convert to structured response
            connections_data = ConnectionSuggestionResponse(**response_data)
            
            execution_time = int((time.time() - start_time) * 1000)
            
            return AIAnalysisResponse(
                analysis_type="connection_analysis",
                user_id=user_id,
                canvas_id=request.canvas_data.metadata.get("canvas_id"),
                data=connections_data,
                execution_time_ms=execution_time
            )
            
        except Exception as e:
            self.logger.error(f"Error in connection analysis: {e}")
            execution_time = int((time.time() - start_time) * 1000)
            
            return AIAnalysisResponse(
                analysis_type="connection_analysis",
                user_id=user_id,
                success=False,
                message=f"Failed to analyze connections: {str(e)}",
                execution_time_ms=execution_time
            )
    
    async def identify_themes(
        self,
        request: ThemeAnalysisRequest,
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
            
            # Prepare canvas data for AI analysis
            canvas_json = request.canvas_data.model_dump()
            
            # Prepare variables for the AI skill
            variables = {
                "canvas_data": json.dumps(canvas_json),
                "analysis_scope": request.analysis_scope or "comprehensive",
                "north_star_context": json.dumps(request.north_star_context or {})
            }
            
            # Invoke the theme identification AI skill
            ai_response = await kernel_service.invoke_semantic_function(
                skill_name="canvas",
                function_name="IdentifyThemes",
                input_text="",
                variables=variables
            )
            
            # Parse the AI response
            if isinstance(ai_response, str):
                json_start = ai_response.find('{')
                json_end = ai_response.rfind('}') + 1
                if json_start != -1 and json_end > json_start:
                    ai_response = ai_response[json_start:json_end]
                
                response_data = json.loads(ai_response)
            else:
                response_data = ai_response
            
            # Convert to structured response
            themes_data = ThemeAnalysisResponse(**response_data)
            
            execution_time = int((time.time() - start_time) * 1000)
            
            return AIAnalysisResponse(
                analysis_type="theme_analysis",
                user_id=user_id,
                canvas_id=request.canvas_data.metadata.get("canvas_id"),
                data=themes_data,
                execution_time_ms=execution_time
            )
            
        except Exception as e:
            self.logger.error(f"Error in theme analysis: {e}")
            execution_time = int((time.time() - start_time) * 1000)
            
            return AIAnalysisResponse(
                analysis_type="theme_analysis",
                user_id=user_id,
                success=False,
                message=f"Failed to analyze themes: {str(e)}",
                execution_time_ms=execution_time
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
            
            # Prepare canvas data for AI analysis
            canvas_json = request.canvas_data.model_dump()
            
            # Prepare variables for the AI skill
            variables = {
                "canvas_data": json.dumps(canvas_json),
                "current_objectives": json.dumps(request.current_objectives or []),
                "north_star_context": json.dumps(request.north_star_context or {})
            }
            
            # Invoke the canvas optimization AI skill
            ai_response = await kernel_service.invoke_semantic_function(
                skill_name="canvas",
                function_name="OptimizeCanvas",
                input_text="",
                variables=variables
            )
            
            # Parse the AI response
            if isinstance(ai_response, str):
                json_start = ai_response.find('{')
                json_end = ai_response.rfind('}') + 1
                if json_start != -1 and json_end > json_start:
                    ai_response = ai_response[json_start:json_end]
                
                response_data = json.loads(ai_response)
            else:
                response_data = ai_response
            
            # Convert to structured response
            optimization_data = CanvasOptimizationResponse(**response_data)
            
            execution_time = int((time.time() - start_time) * 1000)
            
            return AIAnalysisResponse(
                analysis_type="canvas_optimization",
                user_id=user_id,
                canvas_id=request.canvas_data.metadata.get("canvas_id"),
                data=optimization_data,
                execution_time_ms=execution_time
            )
            
        except Exception as e:
            self.logger.error(f"Error in canvas optimization: {e}")
            execution_time = int((time.time() - start_time) * 1000)
            
            return AIAnalysisResponse(
                analysis_type="canvas_optimization",
                user_id=user_id,
                success=False,
                message=f"Failed to optimize canvas: {str(e)}",
                execution_time_ms=execution_time
            )
    
    async def comprehensive_analysis(
        self,
        canvas_data: CanvasData,
        user_id: UUID,
        include_themes: bool = True,
        include_connections: bool = True,
        include_optimization: bool = True,
        north_star_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, AIAnalysisResponse]:
        """
        Perform comprehensive analysis including multiple AI algorithms.
        
        Args:
            canvas_data: Canvas data to analyze
            user_id: ID of the user making the request
            include_themes: Whether to include theme analysis
            include_connections: Whether to include connection analysis
            include_optimization: Whether to include optimization analysis
            north_star_context: User's strategic context
            
        Returns:
            Dictionary of analysis results by analysis type
        """
        start_time = time.time()
        
        try:
            self.logger.info(f"Starting comprehensive canvas analysis for user {user_id}")
            
            # Prepare analysis tasks
            tasks = []
            analysis_types = []
            
            if include_connections:
                connection_request = ConnectionAnalysisRequest(
                    canvas_data=canvas_data,
                    north_star_context=north_star_context
                )
                tasks.append(self.analyze_connections(connection_request, user_id))
                analysis_types.append("connections")
            
            if include_themes:
                theme_request = ThemeAnalysisRequest(
                    canvas_data=canvas_data,
                    north_star_context=north_star_context
                )
                tasks.append(self.identify_themes(theme_request, user_id))
                analysis_types.append("themes")
            
            if include_optimization:
                optimization_request = CanvasOptimizationRequest(
                    canvas_data=canvas_data,
                    north_star_context=north_star_context
                )
                tasks.append(self.optimize_canvas(optimization_request, user_id))
                analysis_types.append("optimization")
            
            # Execute all analyses concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Combine results
            analysis_results = {}
            for i, result in enumerate(results):
                analysis_type = analysis_types[i]
                if isinstance(result, Exception):
                    self.logger.error(f"Error in {analysis_type} analysis: {result}")
                    analysis_results[analysis_type] = AIAnalysisResponse(
                        analysis_type=analysis_type,
                        user_id=user_id,
                        success=False,
                        message=f"Failed to complete {analysis_type} analysis: {str(result)}"
                    )
                else:
                    analysis_results[analysis_type] = result
            
            execution_time = int((time.time() - start_time) * 1000)
            self.logger.info(f"Comprehensive analysis completed in {execution_time}ms")
            
            return analysis_results
            
        except Exception as e:
            self.logger.error(f"Error in comprehensive analysis: {e}")
            return {
                "error": AIAnalysisResponse(
                    analysis_type="comprehensive",
                    user_id=user_id,
                    success=False,
                    message=f"Failed to complete comprehensive analysis: {str(e)}"
                )
            }
    
    def _prepare_canvas_context(self, canvas_data: CanvasData) -> Dict[str, Any]:
        """
        Prepare canvas context for AI analysis.
        
        Args:
            canvas_data: Canvas data to prepare
            
        Returns:
            Prepared context dictionary
        """
        return {
            "total_nodes": len(canvas_data.nodes),
            "total_edges": len(canvas_data.edges),
            "node_types": list(set(node.type for node in canvas_data.nodes)),
            "has_content": any(node.content.strip() for node in canvas_data.nodes),
            "connectivity": len(canvas_data.edges) / max(len(canvas_data.nodes), 1)
        }


# Create service instance
canvas_ai_service = CanvasAIService()