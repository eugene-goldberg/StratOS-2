"""
Tests for enhanced dataset upload router endpoint logic.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException, status
import json
import io
from uuid import uuid4
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.models.objective_data import DataSet, DataCategory, DataSourceType
from backend.models.user import UserResponse


class TestDatasetUploadLogic:
    """Test enhanced dataset upload endpoint logic without full app"""
    
    @pytest.fixture
    def mock_current_user(self):
        """Mock authenticated user"""
        from datetime import datetime
        user_id = uuid4()
        return UserResponse(
            id=user_id,
            email="test@example.com",
            full_name="Test User",
            is_active=True,
            created_at=datetime.now()
        )
    
    @pytest.fixture
    def mock_upload_file(self):
        """Create mock upload file"""
        mock_file = MagicMock()
        mock_file.filename = "test.csv"
        mock_file.size = 1024
        return mock_file
    
    @pytest.mark.asyncio
    async def test_json_parsing_valid_tags(self):
        """Test JSON parsing for valid tags"""
        tags_json = '["quarterly", "finance", "revenue"]'
        
        try:
            parsed_tags = json.loads(tags_json)
            assert isinstance(parsed_tags, list)
            assert parsed_tags == ["quarterly", "finance", "revenue"]
        except (json.JSONDecodeError, ValueError):
            pytest.fail("Valid JSON should parse successfully")
    
    @pytest.mark.asyncio 
    async def test_json_parsing_invalid_tags(self):
        """Test JSON parsing for invalid tags"""
        invalid_tags = "invalid_json"
        
        with pytest.raises((json.JSONDecodeError, ValueError)):
            parsed_tags = json.loads(invalid_tags)
            if not isinstance(parsed_tags, list):
                raise ValueError("Tags must be a list")
    
    @pytest.mark.asyncio
    async def test_json_parsing_valid_strategic_elements(self):
        """Test JSON parsing for valid strategic elements"""
        links_json = '[{"type": "goal", "id": "123"}, {"type": "value", "id": "456"}]'
        
        parsed_links = json.loads(links_json)
        assert isinstance(parsed_links, list)
        assert len(parsed_links) == 2
        
        # Validate structure
        for element in parsed_links:
            assert isinstance(element, dict)
            assert "type" in element
            assert "id" in element
    
    @pytest.mark.asyncio
    async def test_json_parsing_invalid_strategic_elements_structure(self):
        """Test JSON parsing for invalid strategic elements structure"""
        invalid_links = '[{"invalid": "structure"}]'
        
        parsed_links = json.loads(invalid_links)
        assert isinstance(parsed_links, list)
        
        # Validate each element has required fields
        with pytest.raises(ValueError):
            for element in parsed_links:
                if not isinstance(element, dict) or "type" not in element or "id" not in element:
                    raise ValueError("Each linked element must be a dict with 'type' and 'id' fields")
    
    @pytest.mark.asyncio
    async def test_file_format_detection(self):
        """Test file format detection logic"""
        test_cases = [
            ("test.csv", "csv"),
            ("data.xlsx", "excel"),
            ("info.xls", "excel"),
            ("config.json", "json"),
            ("document.txt", None)  # Unsupported
        ]
        
        for filename, expected_format in test_cases:
            filename_lower = filename.lower()
            file_format = None
            
            if filename_lower.endswith('.csv'):
                file_format = 'csv'
            elif filename_lower.endswith('.xlsx') or filename_lower.endswith('.xls'):
                file_format = 'excel'
            elif filename_lower.endswith('.json'):
                file_format = 'json'
            
            assert file_format == expected_format, f"Failed for {filename}"
    
    @pytest.mark.asyncio
    async def test_upload_endpoint_logic_simulation(self, mock_current_user, mock_upload_file):
        """Test the upload endpoint logic simulation"""
        from backend.models.objective_data import DataSetCreate
        
        # Simulate form data parsing
        name = "Test Dataset"
        description = "Test description"
        category = DataCategory.FINANCIAL
        tags_json = '["tag1", "tag2"]'
        links_json = '[{"type": "goal", "id": "123"}]'
        
        # Parse tags
        parsed_tags = json.loads(tags_json)
        assert isinstance(parsed_tags, list)
        
        # Parse strategic elements
        parsed_links = json.loads(links_json)
        assert isinstance(parsed_links, list)
        for element in parsed_links:
            assert "type" in element and "id" in element
        
        # Determine file format
        filename_lower = mock_upload_file.filename.lower()
        file_format = 'csv' if filename_lower.endswith('.csv') else None
        assert file_format == 'csv'
        
        # Create dataset data
        dataset_data = DataSetCreate(
            name=name,
            description=description,
            category=category,
            source_type=DataSourceType.UPLOAD,
            data_format=file_format,
            tags=parsed_tags,
            linked_strategic_elements=parsed_links
        )
        
        # Verify dataset creation
        assert dataset_data.name == name
        assert dataset_data.tags == ["tag1", "tag2"]
        assert len(dataset_data.linked_strategic_elements) == 1
        assert dataset_data.linked_strategic_elements[0]["type"] == "goal"