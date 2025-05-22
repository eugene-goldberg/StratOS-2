"""
Canvas AI Router - API endpoints for AI-powered canvas analysis and structuring.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from typing import List, Optional, Dict, Any
from uuid import UUID
import logging

from ..models.canvas_ai import (
    # Request models
    TextStructureRequest,
    ConnectionAnalysisRequest,
    ThemeAnalysisRequest, 
    CanvasOptimizationRequest,
    # Response models
    AIAnalysisResponse,
    CanvasData
)
from ..services.canvas_ai_service import canvas_ai_service
from ..dependencies import get_current_user_id

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/canvas-ai", tags=["canvas-ai"])


@router.post("/structure-text", response_model=AIAnalysisResponse)
async def structure_text(
    request: TextStructureRequest,
    current_user_id: UUID = Depends(get_current_user_id)
):
    """
    Analyze unstructured text and suggest structured canvas nodes.
    
    This endpoint uses AI to parse freehand text input and suggest how to
    structure it into strategic canvas nodes with appropriate types and content.
    """
    try:
        logger.info(f"Text structuring request from user {current_user_id}")
        
        if not request.text.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Text content cannot be empty"
            )
        
        result = await canvas_ai_service.structure_text(request, current_user_id)
        
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.message
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in text structuring endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to analyze text structure"
        )


@router.post("/analyze-connections", response_model=AIAnalysisResponse)
async def analyze_connections(
    request: ConnectionAnalysisRequest,
    current_user_id: UUID = Depends(get_current_user_id)
):
    """
    Analyze canvas nodes and suggest meaningful connections.
    
    This endpoint uses AI to identify potential strategic relationships between
    canvas nodes and suggest connections that would enhance strategic understanding.
    """
    try:
        logger.info(f"Connection analysis request from user {current_user_id}")
        
        if not request.canvas_data.nodes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Canvas must contain at least one node for connection analysis"
            )
        
        result = await canvas_ai_service.analyze_connections(request, current_user_id)
        
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.message
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in connection analysis endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to analyze connections"
        )


@router.post("/identify-themes", response_model=AIAnalysisResponse)
async def identify_themes(
    request: ThemeAnalysisRequest,
    current_user_id: UUID = Depends(get_current_user_id)
):
    """
    Identify themes and patterns across canvas elements.
    
    This endpoint uses AI to discover recurring themes, strategic patterns,
    and insights from the overall canvas content and structure.
    """
    try:
        logger.info(f"Theme analysis request from user {current_user_id}")
        
        if not request.canvas_data.nodes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Canvas must contain at least one node for theme analysis"
            )
        
        result = await canvas_ai_service.identify_themes(request, current_user_id)
        
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.message
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in theme analysis endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to analyze themes"
        )


@router.post("/optimize-canvas", response_model=AIAnalysisResponse)
async def optimize_canvas(
    request: CanvasOptimizationRequest,
    current_user_id: UUID = Depends(get_current_user_id)
):
    """
    Analyze canvas and provide optimization recommendations.
    
    This endpoint uses AI to evaluate the canvas against strategic frameworks
    and provide comprehensive recommendations for improvement and optimization.
    """
    try:
        logger.info(f"Canvas optimization request from user {current_user_id}")
        
        if not request.canvas_data.nodes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Canvas must contain at least one node for optimization analysis"
            )
        
        result = await canvas_ai_service.optimize_canvas(request, current_user_id)
        
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.message
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in canvas optimization endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to optimize canvas"
        )


@router.post("/comprehensive-analysis")
async def comprehensive_analysis(
    canvas_data: CanvasData,
    include_themes: bool = Query(True, description="Include theme analysis"),
    include_connections: bool = Query(True, description="Include connection analysis"),
    include_optimization: bool = Query(True, description="Include optimization analysis"),
    north_star_context: Optional[Dict[str, Any]] = None,
    current_user_id: UUID = Depends(get_current_user_id)
):
    """
    Perform comprehensive AI analysis of the canvas.
    
    This endpoint runs multiple AI analyses concurrently to provide a complete
    picture of the canvas including themes, connections, and optimization recommendations.
    """
    try:
        logger.info(f"Comprehensive analysis request from user {current_user_id}")
        
        if not canvas_data.nodes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Canvas must contain at least one node for analysis"
            )
        
        results = await canvas_ai_service.comprehensive_analysis(
            canvas_data=canvas_data,
            user_id=current_user_id,
            include_themes=include_themes,
            include_connections=include_connections,
            include_optimization=include_optimization,
            north_star_context=north_star_context
        )
        
        # Check if any analysis failed
        failed_analyses = [
            analysis_type for analysis_type, result in results.items()
            if not result.success
        ]
        
        if failed_analyses:
            logger.warning(f"Some analyses failed: {failed_analyses}")
        
        return {
            "analysis_results": results,
            "total_analyses": len(results),
            "successful_analyses": len([r for r in results.values() if r.success]),
            "failed_analyses": failed_analyses
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in comprehensive analysis endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to perform comprehensive analysis"
        )


@router.get("/analysis-status/{analysis_id}")
async def get_analysis_status(
    analysis_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id)
):
    """
    Get the status of a long-running analysis.
    
    This endpoint allows checking the status of analyses that might take
    longer to complete, especially comprehensive analyses.
    """
    # This would be implemented with a task queue system like Celery
    # For now, return a simple response
    return {
        "analysis_id": analysis_id,
        "status": "completed",
        "message": "Analysis completed successfully"
    }


@router.post("/batch-text-structure")
async def batch_text_structure(
    texts: List[str],
    canvas_context: Optional[Dict[str, Any]] = None,
    north_star_context: Optional[Dict[str, Any]] = None,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user_id: UUID = Depends(get_current_user_id)
):
    """
    Process multiple text inputs for structuring in batch.
    
    This endpoint allows batch processing of multiple text inputs,
    useful for processing multiple ideas or imported content at once.
    """
    try:
        logger.info(f"Batch text structuring request from user {current_user_id} for {len(texts)} texts")
        
        if not texts or len(texts) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one text input is required"
            )
        
        if len(texts) > 10:  # Limit batch size
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Batch size cannot exceed 10 texts"
            )
        
        # Process each text
        results = []
        for i, text in enumerate(texts):
            if text.strip():  # Only process non-empty texts
                request = TextStructureRequest(
                    text=text,
                    canvas_context=canvas_context,
                    north_star_context=north_star_context
                )
                
                result = await canvas_ai_service.structure_text(request, current_user_id)
                results.append({
                    "index": i,
                    "text_preview": text[:100] + "..." if len(text) > 100 else text,
                    "analysis": result
                })
        
        return {
            "batch_results": results,
            "total_processed": len(results),
            "successful": len([r for r in results if r["analysis"].success])
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in batch text structuring endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process batch text structuring"
        )


@router.get("/health")
async def health_check():
    """
    Health check endpoint for the Canvas AI service.
    """
    try:
        # Basic health check - could be expanded to check AI service availability
        return {
            "status": "healthy",
            "service": "canvas-ai",
            "timestamp": "2025-01-XX",  # Would use actual timestamp
            "available_analyses": [
                "text_structure",
                "connection_analysis", 
                "theme_analysis",
                "canvas_optimization",
                "comprehensive_analysis"
            ]
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Canvas AI service is not available"
        )