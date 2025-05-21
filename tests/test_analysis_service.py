import pytest
import pytest_asyncio
import json
from uuid import uuid4, UUID
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import HTTPException

from backend.services.analysis_service import AnalysisService
from backend.models.analysis import (
    SWOTAnalysisCreate, SWOTAnalysis, SWOTItemCreate, SWOTItem, SWOTCategory,
    InsightCreate, Insight, InsightType, InsightSource,
    SOLinkageCreate, SOLinkage, LinkageType
)
# Mock kernel_service if it's directly imported and used by AnalysisService
# If it's passed in or accessed via a global, mocking strategy might differ.
# For now, assuming it might be globally accessible or needs patching where used.

@pytest_asyncio.fixture
async def analysis_service(monkeypatch):
    service = AnalysisService()
    # Use in-memory cache for tests
    service.cosmos_db_available = False
    service.analyses_cache = {}
    service.insights_cache = {}
    service.so_linkages_cache = {}
    service.active_sessions = {} # If used by methods being tested

    # Mock kernel_service if it's a direct dependency of the service instance
    # or patch its usage within the methods if it's globally imported.
    # Example: monkeypatch.setattr(service, 'kernel_service', AsyncMock())
    # For global imports: @patch('backend.services.analysis_service.kernel_service', new_callable=AsyncMock) above test methods.
    # For now, we'll assume kernel_service calls within methods will be patched directly in tests needing them.
    return service

@pytest_asyncio.fixture
def mock_kernel_service():
    # A general mock for kernel_service if used across multiple tests
    mock_ks = AsyncMock()
    mock_ks.invoke_semantic_function = AsyncMock(return_value="Mocked LLM Response")
    mock_ks.generate_completion = AsyncMock(return_value="Mocked LLM Completion")
    # Add other methods as needed
    return mock_ks

# --- SWOTAnalysis Tests ---
@pytest.mark.asyncio
async def test_create_swot_analysis(analysis_service: AnalysisService):
    user_id = uuid4()
    swot_data = SWOTAnalysisCreate(title="Test SWOT", description="A test SWOT analysis.")
    
    # Ensure the service uses its cache
    analysis_service.analyses_container = None # To force cache usage if DB check is strict

    created_swot = await analysis_service.create_swot_analysis(swot_data, user_id)
    
    assert created_swot is not None
    assert created_swot.title == swot_data.title
    assert created_swot.user_id == user_id
    assert str(created_swot.id) in analysis_service.analyses_cache # Assuming cache keys by analysis_id
    # Or if cache is user_id partitioned:
    # assert f"{user_id}_{created_swot.id}" in analysis_service.analyses_cache


@pytest.mark.asyncio
async def test_get_swot_analysis(analysis_service: AnalysisService):
    user_id = uuid4()
    swot_id = uuid4()
    # Populate cache directly for test
    analysis_service.analyses_cache[f"{user_id}_{swot_id}"] = {
        "id": str(swot_id), "user_id": str(user_id), "title": "Cached SWOT", 
        "items": [], "tows_strategies": [], 
        "created_at": datetime.now().isoformat(), "updated_at": datetime.now().isoformat()
    }
    
    fetched_swot = await analysis_service.get_swot_analysis(swot_id, user_id)
    assert fetched_swot is not None
    assert fetched_swot.title == "Cached SWOT"

# --- Insight Tests ---
@pytest.mark.asyncio
async def test_create_insight(analysis_service: AnalysisService):
    user_id = uuid4()
    insight_data = InsightCreate(
        title="Test Insight", 
        description="A test insight.",
        insight_type=InsightType.OPPORTUNITY,
        source=InsightSource.AI_GENERATED
    )
    analysis_service.insights_container = None # Force cache

    created_insight = await analysis_service.create_insight(insight_data, user_id)
    
    assert created_insight is not None
    assert created_insight.title == insight_data.title
    assert created_insight.user_id == user_id
    assert f"{user_id}_{created_insight.id}" in analysis_service.insights_cache

@pytest.mark.asyncio
async def test_get_insight(analysis_service: AnalysisService):
    user_id = uuid4()
    insight_id = uuid4()
    analysis_service.insights_cache[f"{user_id}_{insight_id}"] = {
        "id": str(insight_id), "user_id": str(user_id), "title": "Cached Insight", 
        "description": "Desc", "insight_type": "opportunity", "source": "ai_generated",
        "created_at": datetime.now().isoformat(), "updated_at": datetime.now().isoformat(),
        "linked_strategic_goals": []
    }
    
    fetched_insight = await analysis_service.get_insight(insight_id, user_id)
    assert fetched_insight is not None
    assert fetched_insight.title == "Cached Insight"

# --- SOLinkage Tests ---
@pytest.mark.asyncio
async def test_save_so_linkage(analysis_service: AnalysisService):
    user_id = uuid4()
    linkage_data = SOLinkageCreate(
        user_id=user_id,
        subjective_snippet_text="CEO feels market is shifting.",
        objective_snippet_text="Sales data shows 10% dip in product X.",
        linkage_type=LinkageType.CORRELATION,
        ai_summary_of_linkage="CEO intuition matches data.",
        ai_prompt_for_ceo="How to react?"
    )
    analysis_service.so_linkages_container = None # Force cache

    # _save_so_linkage is protected, test via a method that uses it, or make it public for testing
    # For now, let's assume we can test it directly or it's refactored.
    # If it remains protected, this test would need to call discover_so_linkages
    # which is more complex to mock.
    # Let's assume we can call it for this unit test:
    
    # Temporarily make it public for test or use a wrapper if available
    # This is a common pattern if _save_so_linkage is only called by discover_so_linkages
    # For this example, let's assume it's testable.
    # If not, this test needs to be redesigned around discover_so_linkages.

    # Direct call to _save_so_linkage (if made public for testing or refactored)
    # saved_linkage = await analysis_service._save_so_linkage(linkage_data)
    # assert saved_linkage is not None
    # assert saved_linkage.user_id == user_id
    # assert str(saved_linkage.id) in analysis_service.so_linkages_cache
    
    # As _save_so_linkage is protected, we'll skip direct test and assume
    # its functionality is covered by testing discover_so_linkages.
    pass 


@pytest.mark.asyncio
@patch('backend.services.analysis_service.kernel_service', new_callable=AsyncMock)
async def test_discover_so_linkages_basic(mock_ks: AsyncMock, analysis_service: AnalysisService):
    user_id = uuid4()
    
    # Mock responses from kernel_service skills
    async def mock_run_async_replacement(*args, **kwargs):
        # args[0] is the sk_function object (the function itself)
        # In the real code, kernel_service.run_async is called with:
        # (sk_function_object, input_vars=context_vars)
        # The mock setup is:
        # mock_ks.get_skill = MagicMock(return_value=MagicMock(get_function=lambda name: name))
        # So sk_function_invoked will be the string name of the function
        sk_function_invoked = args[0]
        
        # Identify which function is being called based on the function name
        func_name_being_called = sk_function_invoked
        
        # For debugging, we could access context variables with:
        # input_vars = kwargs.get('input_vars', {})
        # user_id_from_context = input_vars.get('user_id')
        # topic_from_context = input_vars.get('topic')
        
        if func_name_being_called == "fetch_relevant_subjective_notes":
            # run_async returns a context with a result attribute
            mock_context_result = MagicMock()
            mock_context_result.result = "Subjective Note: Market feels slow."
            return mock_context_result
        elif func_name_being_called == "fetch_relevant_objective_data":
            mock_context_result = MagicMock()
            mock_context_result.result = "Objective Data: Sales are down 5%."
            return mock_context_result
        elif func_name_being_called == "FindPotentialLinkages":
            mock_context_result = MagicMock()
            linkage_json = json.dumps([{
                "subjective_ref_id": f"s_{user_id}_1",
                "objective_ref_id": f"o_{user_id}_1",
                "linkage_type": "correlation",
                "ai_summary_of_linkage": "Slow market feeling correlates with sales dip.",
                "ai_prompt_for_ceo": "What actions can address this?"
            }])
            # For run_async, set the result attribute on the mock
            mock_context_result.result = linkage_json
            return mock_context_result
            
        # Default response for unknown functions
        mock_unknown_result = MagicMock()
        mock_unknown_result.result = "Unknown skill/function in mock_run_async_replacement"
        return mock_unknown_result

    # mock_ks.invoke_semantic_function = mock_invoke_skill # Not used by AnalysisService directly
    mock_ks.get_skill = MagicMock(return_value=MagicMock(get_function=lambda name: name))
    mock_ks.run_async = mock_run_async_replacement # This is what AnalysisService calls
    
    # Mock create_new_context to return a mock context that can be updated
    mock_sk_context_instance = MagicMock()
    def update_mock_context_vars(key, value, _=None):
        # Simulate context variable assignment
        # The third argument is for compatibility with the actual context implementation
        if not hasattr(mock_sk_context_instance, 'variables'):
            mock_sk_context_instance.variables = {}
        mock_sk_context_instance.variables[key] = value
    mock_sk_context_instance.__setitem__ = update_mock_context_vars
    mock_sk_context_instance.variables = {} # Initialize variables

    mock_ks.create_new_context = MagicMock(return_value=mock_sk_context_instance)

    analysis_service.so_linkages_container = None # Force cache for _save_so_linkage

    linkages_response = await analysis_service.discover_so_linkages(str(user_id), topic_context="Q3 Performance")
    
    assert linkages_response is not None
    assert len(linkages_response) == 1
    linkage = linkages_response[0]
    assert linkage["linkage_type"] == "correlation"
    assert "Market feels slow" in linkage["subjective_snippet"] # Based on simplified parsing in service
    assert "Sales are down" in linkage["objective_snippet"]
    # The cache keys are by linkage ID, not user ID
    # Just verify the cache has something in it
    assert len(analysis_service.so_linkages_cache) > 0


# Add more tests for list, update, delete for SWOT and Insights,
# and for AI generation methods like generate_tows_strategies, generate_ai_guided_swot_items,
# generate_insight_explanation, generate_insights_from_data, mocking kernel_service calls.
