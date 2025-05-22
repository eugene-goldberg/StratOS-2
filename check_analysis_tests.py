#!/usr/bin/env python3
"""
Script to check test_analysis_service.py
"""
import sys
import os
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from uuid import UUID, uuid4

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import conftest_helper to set up mocks
import tests.conftest_helper

# Mock essential analysis models
class SWOTAnalysis:
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', uuid4())
        self.user_id = kwargs.get('user_id', uuid4())
        self.title = kwargs.get('title', 'Test SWOT')
        self.created_at = kwargs.get('created_at', datetime.now())
        self.updated_at = kwargs.get('updated_at', datetime.now())
        self.items = kwargs.get('items', [])
    
    def model_dump(self, **kwargs):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'items': self.items
        }

class SWOTAnalysisCreate:
    def __init__(self, **kwargs):
        self.title = kwargs.get('title', 'New SWOT Analysis')

class SWOTItem:
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', uuid4())
        self.category = kwargs.get('category', 'strength')
        self.content = kwargs.get('content', 'Test content')
        self.source = kwargs.get('source', 'user')
        self.source_references = kwargs.get('source_references', [])
        self.impact_score = kwargs.get('impact_score', 3)
        self.certainty_score = kwargs.get('certainty_score', 3)
    
    def model_dump(self, **kwargs):
        return {
            'id': self.id,
            'category': self.category,
            'content': self.content,
            'source': self.source,
            'source_references': self.source_references,
            'impact_score': self.impact_score,
            'certainty_score': self.certainty_score
        }

class SWOTItemCreate:
    def __init__(self, **kwargs):
        self.category = kwargs.get('category', 'strength')
        self.content = kwargs.get('content', 'New item')
        self.source = kwargs.get('source', 'user')
        self.impact_score = kwargs.get('impact_score', 3)
        self.certainty_score = kwargs.get('certainty_score', 3)

class Insight:
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', uuid4())
        self.user_id = kwargs.get('user_id', uuid4())
        self.title = kwargs.get('title', 'Test Insight')
        self.content = kwargs.get('content', 'Insight content')
        self.insight_type = kwargs.get('insight_type', 'key_observation')
        self.source = kwargs.get('source', 'user')
        self.related_swot_items = kwargs.get('related_swot_items', [])
        self.created_at = kwargs.get('created_at', datetime.now())
        self.updated_at = kwargs.get('updated_at', datetime.now())
    
    def model_dump(self, **kwargs):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'content': self.content,
            'insight_type': self.insight_type,
            'source': self.source,
            'related_swot_items': self.related_swot_items,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

class InsightCreate:
    def __init__(self, **kwargs):
        self.title = kwargs.get('title', 'New Insight')
        self.content = kwargs.get('content', 'Insight content')
        self.insight_type = kwargs.get('insight_type', 'key_observation')
        self.source = kwargs.get('source', 'user')
        self.related_swot_items = kwargs.get('related_swot_items', [])

class SOLinkage:
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', uuid4())
        self.user_id = kwargs.get('user_id', uuid4())
        self.title = kwargs.get('title', 'Test Linkage')
        self.description = kwargs.get('description', 'Linkage description')
        self.linkage_type = kwargs.get('linkage_type', 'opportunity_risk')
        self.item1_id = kwargs.get('item1_id', uuid4())
        self.item2_id = kwargs.get('item2_id', uuid4())
        self.created_at = kwargs.get('created_at', datetime.now())
        self.updated_at = kwargs.get('updated_at', datetime.now())
    
    def model_dump(self, **kwargs):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'description': self.description,
            'linkage_type': self.linkage_type,
            'item1_id': self.item1_id,
            'item2_id': self.item2_id,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

class SOLinkageCreate:
    def __init__(self, **kwargs):
        self.title = kwargs.get('title', 'New Linkage')
        self.description = kwargs.get('description', 'Linkage description')
        self.linkage_type = kwargs.get('linkage_type', 'opportunity_risk')
        self.item1_id = kwargs.get('item1_id', uuid4())
        self.item2_id = kwargs.get('item2_id', uuid4())

# Set up mock models
sys.modules['backend.models.analysis'] = MagicMock()
sys.modules['backend.models.analysis'].SWOTAnalysisCreate = SWOTAnalysisCreate
sys.modules['backend.models.analysis'].SWOTAnalysis = SWOTAnalysis
sys.modules['backend.models.analysis'].SWOTItemCreate = SWOTItemCreate
sys.modules['backend.models.analysis'].SWOTItem = SWOTItem
sys.modules['backend.models.analysis'].SWOTCategory = MagicMock()
sys.modules['backend.models.analysis'].InsightCreate = InsightCreate
sys.modules['backend.models.analysis'].Insight = Insight
sys.modules['backend.models.analysis'].InsightType = MagicMock()
sys.modules['backend.models.analysis'].InsightSource = MagicMock()
sys.modules['backend.models.analysis'].SOLinkageCreate = SOLinkageCreate
sys.modules['backend.models.analysis'].SOLinkage = SOLinkage
sys.modules['backend.models.analysis'].LinkageType = MagicMock()

# Create mock AnalysisService
class MockAnalysisService:
    def __init__(self):
        self.analyses_cache = {}
        self.insights_cache = {}
        self.so_linkages_cache = {}
        self.cosmos_db_available = False
        
    async def create_swot_analysis(self, analysis_data, user_id):
        analysis = SWOTAnalysis(
            user_id=user_id,
            title=analysis_data.title,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        self.analyses_cache[f"{user_id}_{analysis.id}"] = analysis
        return analysis
    
    async def get_swot_analysis(self, analysis_id, user_id):
        return self.analyses_cache.get(f"{user_id}_{analysis_id}")
    
    async def add_swot_item(self, analysis_id, user_id, item_data):
        analysis = await self.get_swot_analysis(analysis_id, user_id)
        if not analysis:
            return None
        
        item = SWOTItem(
            category=item_data.category,
            content=item_data.content,
            source=item_data.source,
            impact_score=item_data.impact_score,
            certainty_score=item_data.certainty_score
        )
        
        if not hasattr(analysis, 'items'):
            analysis.items = []
        
        analysis.items.append(item)
        analysis.updated_at = datetime.now()
        return item
    
    async def create_insight(self, insight_data, user_id):
        insight = Insight(
            user_id=user_id,
            title=insight_data.title,
            content=insight_data.content,
            insight_type=insight_data.insight_type,
            source=insight_data.source,
            related_swot_items=insight_data.related_swot_items,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        self.insights_cache[f"{user_id}_{insight.id}"] = insight
        return insight
    
    async def get_insight(self, insight_id, user_id):
        return self.insights_cache.get(f"{user_id}_{insight_id}")
    
    async def save_so_linkage(self, linkage_data, user_id):
        linkage = SOLinkage(
            user_id=user_id,
            title=linkage_data.title,
            description=linkage_data.description,
            linkage_type=linkage_data.linkage_type,
            item1_id=linkage_data.item1_id,
            item2_id=linkage_data.item2_id,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        self.so_linkages_cache[f"{user_id}_{linkage.id}"] = linkage
        return linkage
    
    async def discover_so_linkages(self, user_id, analysis_id=None):
        # Simulate AI-generated linkages
        return [
            SOLinkage(
                user_id=user_id,
                title="AI-Generated Linkage",
                description="This linkage was found by AI",
                linkage_type="opportunity_risk"
            )
        ]

# Mock AnalysisService in the backend module
sys.modules['backend.services.analysis_service'] = MagicMock()
sys.modules['backend.services.analysis_service'].AnalysisService = MockAnalysisService

# Try to inspect the test file
def check_analysis_tests():
    try:
        # Import the test module
        from tests import test_analysis_service
        
        # Find all test functions
        test_functions = []
        for name in dir(test_analysis_service):
            if name.startswith('test_'):
                test_functions.append(name)
        
        print(f"Found {len(test_functions)} test functions in test_analysis_service.py")
        print(f"Test functions: {', '.join(test_functions)}")
        
        print("\nCheck complete - all AnalysisService tests could be parsed!")
        
    except Exception as e:
        print(f"Error importing test_analysis_service.py: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_analysis_tests()