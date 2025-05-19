from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional, Dict, Any
from uuid import UUID
from ..models.analysis import (
    SWOTAnalysis,
    SWOTAnalysisCreate,
    SWOTItem,
    SWOTItemCreate,
    Insight,
    InsightCreate,
    InsightType,
    InsightSource,
    SWOTCategory,
    SOLinkage,
    SOLinkageResponse,
    LinkageType
)
from ..services.analysis_service import AnalysisService
from ..ai.kernel_service import kernel_service

router = APIRouter()
analysis_service = AnalysisService()

# SWOT Analysis Endpoints

@router.post("/swot", response_model=SWOTAnalysis, status_code=status.HTTP_201_CREATED)
async def create_swot_analysis(analysis_data: SWOTAnalysisCreate):
    """
    Create a new SWOT analysis
    """
    return await analysis_service.create_swot_analysis(analysis_data)

@router.get("/swot/{analysis_id}", response_model=SWOTAnalysis)
async def get_swot_analysis(analysis_id: UUID):
    """
    Get a SWOT analysis by ID
    """
    analysis = await analysis_service.get_swot_analysis(analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="SWOT analysis not found")
    return analysis

@router.get("/swot", response_model=List[SWOTAnalysis])
async def list_swot_analyses(limit: int = 10, offset: int = 0):
    """
    List SWOT analyses
    """
    return await analysis_service.list_swot_analyses(limit, offset)

@router.post("/swot/{analysis_id}/items", response_model=SWOTItem, status_code=status.HTTP_201_CREATED)
async def add_swot_item(analysis_id: UUID, item_data: SWOTItemCreate):
    """
    Add an item to a SWOT analysis
    """
    return await analysis_service.add_swot_item(analysis_id, item_data)

@router.put("/swot/{analysis_id}/items/{item_id}", response_model=SWOTItem)
async def update_swot_item(analysis_id: UUID, item_id: UUID, item_data: dict):
    """
    Update a SWOT item
    """
    updated = await analysis_service.update_swot_item(analysis_id, item_id, item_data)
    if not updated:
        raise HTTPException(status_code=404, detail="SWOT item not found")
    return updated

@router.delete("/swot/{analysis_id}/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_swot_item(analysis_id: UUID, item_id: UUID):
    """
    Delete a SWOT item
    """
    deleted = await analysis_service.delete_swot_item(analysis_id, item_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="SWOT item not found")
    return {"status": "success"}

@router.post("/swot/{analysis_id}/generate-tows", response_model=Dict[str, Any])
async def generate_tows_strategies(analysis_id: UUID):
    """
    Generate TOWS strategies from a SWOT analysis
    """
    analysis = await analysis_service.get_swot_analysis(analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="SWOT analysis not found")
    
    tows_strategies = await analysis_service.generate_tows_strategies(analysis_id)
    return {"tows_strategies": tows_strategies}

@router.post("/swot/ai-guided", response_model=SWOTAnalysis, status_code=status.HTTP_201_CREATED)
async def create_ai_guided_swot(title: str, description: Optional[str] = None):
    """
    Create a SWOT analysis with AI guidance
    """
    # Create empty SWOT analysis
    analysis_data = SWOTAnalysisCreate(title=title, description=description)
    analysis = await analysis_service.create_swot_analysis(analysis_data)
    
    # Generate AI-guided SWOT items
    await analysis_service.generate_ai_guided_swot_items(analysis.id)
    
    # Get the updated analysis
    updated_analysis = await analysis_service.get_swot_analysis(analysis.id)
    return updated_analysis

# Insights Endpoints

@router.post("/insights", response_model=Insight, status_code=status.HTTP_201_CREATED)
async def create_insight(insight_data: InsightCreate):
    """
    Create a new insight
    """
    return await analysis_service.create_insight(insight_data)

@router.get("/insights/{insight_id}", response_model=Insight)
async def get_insight(insight_id: UUID):
    """
    Get an insight by ID
    """
    insight = await analysis_service.get_insight(insight_id)
    if not insight:
        raise HTTPException(status_code=404, detail="Insight not found")
    return insight

@router.get("/insights", response_model=List[Insight])
async def list_insights(
    limit: int = 20,
    offset: int = 0,
    insight_type: Optional[InsightType] = None,
    source: Optional[InsightSource] = None,
    goal_id: Optional[UUID] = None
):
    """
    List insights with optional filtering
    """
    return await analysis_service.list_insights(limit, offset, insight_type, source, goal_id)

@router.put("/insights/{insight_id}", response_model=Insight)
async def update_insight(insight_id: UUID, insight_data: dict):
    """
    Update an insight
    """
    updated = await analysis_service.update_insight(insight_id, insight_data)
    if not updated:
        raise HTTPException(status_code=404, detail="Insight not found")
    return updated

@router.delete("/insights/{insight_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_insight(insight_id: UUID):
    """
    Delete an insight
    """
    deleted = await analysis_service.delete_insight(insight_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Insight not found")
    return {"status": "success"}

@router.post("/insights/{insight_id}/explain", response_model=Dict[str, str])
async def get_insight_explanation(insight_id: UUID):
    """
    Get an AI-generated explanation for an insight
    """
    insight = await analysis_service.get_insight(insight_id)
    if not insight:
        raise HTTPException(status_code=404, detail="Insight not found")
    
    explanation = await analysis_service.generate_insight_explanation(insight_id)
    return {"explanation": explanation}

@router.post("/insights/generate-from-data", response_model=List[Insight], status_code=status.HTTP_201_CREATED)
async def generate_insights_from_data(
    data_sources: Dict[str, List[UUID]],
    insight_types: Optional[List[InsightType]] = None,
    max_insights: Optional[int] = 5
):
    """
    Generate insights from selected data sources
    """
    # Data sources format: {"subjective": [uuid1, uuid2], "objective": [uuid3, uuid4]}
    insights = await analysis_service.generate_insights_from_data(data_sources, insight_types, max_insights)
    return insights

# S+O Linkage Endpoints

@router.post("/so-linkage/discover", response_model=List[Dict[str, Any]])
async def discover_so_linkages(
    user_id: UUID,
    topic_context: Optional[str] = None,
    subjective_entry_ids: Optional[List[str]] = None,
    objective_dataset_ids: Optional[List[str]] = None,
    date_range_start: Optional[str] = None,
    date_range_end: Optional[str] = None,
    max_linkages_to_find: int = 5
):
    """
    Discover potential linkages between subjective insights and objective data
    """
    linkages = await analysis_service.discover_so_linkages(
        str(user_id),
        topic_context,
        subjective_entry_ids,
        objective_dataset_ids,
        date_range_start,
        date_range_end,
        max_linkages_to_find
    )
    return linkages

@router.get("/so-linkage", response_model=List[SOLinkageResponse])
async def list_so_linkages(
    user_id: UUID,
    topic_context_filter: Optional[str] = None,
    date_range_start: Optional[str] = None,
    date_range_end: Optional[str] = None,
    limit: int = 20,
    offset: int = 0
):
    """
    List S+O linkages with optional filtering
    """
    linkages = await analysis_service.list_so_linkages(
        user_id,
        topic_context_filter,
        date_range_start,
        date_range_end,
        limit,
        offset
    )
    return linkages

@router.get("/so-linkage/{linkage_id}", response_model=SOLinkageResponse)
async def get_so_linkage(linkage_id: UUID):
    """
    Get an S+O linkage by ID
    """
    linkage = await analysis_service.get_so_linkage(linkage_id)
    if not linkage:
        raise HTTPException(status_code=404, detail="S+O linkage not found")
    return linkage

@router.delete("/so-linkage/{linkage_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_so_linkage(linkage_id: UUID):
    """
    Delete an S+O linkage
    """
    deleted = await analysis_service.delete_so_linkage(linkage_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="S+O linkage not found")
    return {"status": "success"}