"""
Test the AnalysisService.discover_so_linkages method with the updated mock
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import json
from uuid import uuid4
import sys
import os

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import the test module
from backend.services.analysis_service import AnalysisService

async def run_test():
    # Create analysis service
    service = AnalysisService()
    service.cosmos_db_available = False
    service.analyses_cache = {}
    service.insights_cache = {}
    service.so_linkages_cache = {}
    service.active_sessions = {}
    
    user_id = uuid4()
    
    # Create the patch
    with patch('backend.services.analysis_service.kernel_service', new_callable=AsyncMock) as mock_ks:
        # Mock responses from kernel_service skills
        async def mock_run_async_replacement(*args, **kwargs):
            # args[0] is the sk_function object (the function itself)
            # In the real code, kernel_service.run_async is called with:
            # (sk_function_object, input_vars=context_vars)
            sk_function_invoked = args[0]
            
            # Identify which function is being called based on the function name
            func_name_being_called = sk_function_invoked
            
            print(f"Mock called with function: {func_name_being_called}, kwargs: {kwargs}")
            
            if func_name_being_called == "fetch_relevant_subjective_notes":
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
                mock_context_result.result = linkage_json
                return mock_context_result
                
            # Default response for unknown functions
            mock_unknown_result = MagicMock()
            mock_unknown_result.result = "Unknown skill/function in mock_run_async_replacement"
            return mock_unknown_result

        # Set up the mock
        mock_ks.get_skill = MagicMock(return_value=MagicMock(get_function=lambda name: name))
        mock_ks.run_async = mock_run_async_replacement
        
        # Mock create_new_context to return a mock context that can be updated
        mock_sk_context_instance = MagicMock()
        def update_mock_context_vars(key, value, _=None):
            if not hasattr(mock_sk_context_instance, 'variables'):
                mock_sk_context_instance.variables = {}
            mock_sk_context_instance.variables[key] = value
        mock_sk_context_instance.__setitem__ = update_mock_context_vars
        mock_sk_context_instance.variables = {}
        
        mock_ks.create_new_context = MagicMock(return_value=mock_sk_context_instance)
        
        # Call the method being tested
        linkages_response = await service.discover_so_linkages(str(user_id), topic_context="Q3 Performance")
        
        # Assertions
        print("Linkages response:", linkages_response)
        assert linkages_response is not None
        assert len(linkages_response) == 1
        linkage = linkages_response[0]
        assert linkage["linkage_type"] == "correlation"
        assert "Market feels slow" in linkage["subjective_snippet"]
        assert "Sales are down" in linkage["objective_snippet"]
        assert len(service.so_linkages_cache) > 0
        
        print("Test passed!")

if __name__ == "__main__":
    # Run the test
    asyncio.run(run_test())