"""
Tests for Strategic Canvas Backend Robustness (D1)
Testing error handling, edge cases, data validation, and service reliability
"""

import pytest
import pytest_asyncio
from uuid import uuid4, UUID
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException

from backend.services.subjective_input_service import SubjectiveInputService
from backend.models.subjective_input import (
    StrategicCanvas, StrategicCanvasCreate, 
    CanvasElement, CanvasElementCreate
)


@pytest_asyncio.fixture
async def canvas_service():
    """Setup canvas service with mocked dependencies"""
    service = SubjectiveInputService()
    # Force in-memory cache for testing
    service.cosmos_db_available = False
    service.canvases_cache = {}
    service.log_entries_cache = {}
    return service


@pytest_asyncio.fixture
def mock_user_id():
    return uuid4()


@pytest_asyncio.fixture 
def sample_canvas_data():
    return StrategicCanvasCreate(
        title="Test Strategic Canvas",
        description="A comprehensive test canvas for validation"
    )


@pytest_asyncio.fixture
def sample_element_data():
    return CanvasElementCreate(
        element_type="strategy_block",
        content={
            "title": "Market Expansion",
            "description": "Enter 3 new geographic markets",
            "priority": "high"
        },
        position={"x": 250.5, "y": 150.0},
        style={"color": "#3498db", "width": 200, "height": 100},
        connections=[]
    )


class TestStrategicCanvasRobustness:
    """Test suite for Strategic Canvas robustness and error handling"""
    
    @pytest.mark.asyncio
    async def test_create_canvas_with_empty_title(self, canvas_service, mock_user_id):
        """Test canvas creation with invalid data"""
        invalid_data = StrategicCanvasCreate(title="", description="Valid description")
        
        # Should succeed - empty title is technically valid in Pydantic
        canvas = await canvas_service.create_canvas(invalid_data, mock_user_id)
        assert canvas.title == ""
        assert canvas.user_id == mock_user_id
    
    @pytest.mark.asyncio
    async def test_create_canvas_with_very_long_title(self, canvas_service, mock_user_id):
        """Test canvas creation with extremely long title"""
        long_title = "A" * 10000  # Very long title
        canvas_data = StrategicCanvasCreate(title=long_title, description="Test")
        
        canvas = await canvas_service.create_canvas(canvas_data, mock_user_id)
        assert canvas.title == long_title
        assert len(canvas.title) == 10000
    
    @pytest.mark.asyncio
    async def test_get_canvas_nonexistent(self, canvas_service, mock_user_id):
        """Test getting a canvas that doesn't exist"""
        nonexistent_id = uuid4()
        
        result = await canvas_service.get_canvas(nonexistent_id, mock_user_id)
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_canvas_wrong_user(self, canvas_service, mock_user_id):
        """Test user isolation - user cannot access another user's canvas"""
        other_user_id = uuid4()
        
        # Create canvas for one user
        canvas_data = StrategicCanvasCreate(title="User A Canvas")
        canvas = await canvas_service.create_canvas(canvas_data, mock_user_id)
        
        # Try to access as different user
        result = await canvas_service.get_canvas(canvas.id, other_user_id)
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_canvas_without_user_id(self, canvas_service, mock_user_id):
        """Test getting canvas without providing user_id"""
        canvas_data = StrategicCanvasCreate(title="Test Canvas")
        canvas = await canvas_service.create_canvas(canvas_data, mock_user_id)
        
        # Should still find it in cache-based fallback
        result = await canvas_service.get_canvas(canvas.id, None)
        assert result is not None
        assert result.id == canvas.id
    
    @pytest.mark.asyncio
    async def test_list_canvases_empty(self, canvas_service, mock_user_id):
        """Test listing canvases when none exist"""
        canvases = await canvas_service.list_canvases(mock_user_id, limit=10, offset=0)
        assert canvases == []
    
    @pytest.mark.asyncio
    async def test_list_canvases_pagination(self, canvas_service, mock_user_id):
        """Test canvas listing with pagination"""
        # Create multiple canvases
        for i in range(5):
            canvas_data = StrategicCanvasCreate(title=f"Canvas {i}")
            await canvas_service.create_canvas(canvas_data, mock_user_id)
        
        # Test pagination
        page1 = await canvas_service.list_canvases(mock_user_id, limit=2, offset=0)
        page2 = await canvas_service.list_canvases(mock_user_id, limit=2, offset=2)
        page3 = await canvas_service.list_canvases(mock_user_id, limit=2, offset=4)
        
        assert len(page1) == 2
        assert len(page2) == 2  
        assert len(page3) == 1
        
        # Ensure no duplicates between pages
        all_ids = [c.id for c in page1 + page2 + page3]
        assert len(set(all_ids)) == 5


class TestCanvasElementRobustness:
    """Test suite for Canvas Element robustness and validation"""
    
    @pytest.mark.asyncio
    async def test_add_element_to_nonexistent_canvas(self, canvas_service, mock_user_id, sample_element_data):
        """Test adding element to canvas that doesn't exist"""
        nonexistent_canvas_id = uuid4()
        
        with pytest.raises(HTTPException) as exc_info:
            await canvas_service.add_canvas_element(nonexistent_canvas_id, mock_user_id, sample_element_data)
        
        assert exc_info.value.status_code == 404
        assert "not found" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_add_element_with_malformed_content(self, canvas_service, mock_user_id, sample_canvas_data):
        """Test adding element with various content structures"""
        canvas = await canvas_service.create_canvas(sample_canvas_data, mock_user_id)
        
        # Test with None content (should work - Dict[str, Any] allows this)
        element_data = CanvasElementCreate(
            element_type="test",
            content={},  # Empty content
            position={"x": 0, "y": 0}
        )
        
        element = await canvas_service.add_canvas_element(canvas.id, mock_user_id, element_data)
        assert element.content == {}
    
    @pytest.mark.asyncio
    async def test_add_element_with_negative_positions(self, canvas_service, mock_user_id, sample_canvas_data):
        """Test adding element with negative position coordinates"""
        canvas = await canvas_service.create_canvas(sample_canvas_data, mock_user_id)
        
        element_data = CanvasElementCreate(
            element_type="test",
            content={"text": "Test"},
            position={"x": -100, "y": -200}  # Negative coordinates
        )
        
        element = await canvas_service.add_canvas_element(canvas.id, mock_user_id, element_data)
        assert element.position["x"] == -100
        assert element.position["y"] == -200
    
    @pytest.mark.asyncio
    async def test_add_element_with_extreme_positions(self, canvas_service, mock_user_id, sample_canvas_data):
        """Test adding element with very large position coordinates"""
        canvas = await canvas_service.create_canvas(sample_canvas_data, mock_user_id)
        
        element_data = CanvasElementCreate(
            element_type="test",
            content={"text": "Test"},
            position={"x": 999999.99, "y": -999999.99}  # Extreme coordinates
        )
        
        element = await canvas_service.add_canvas_element(canvas.id, mock_user_id, element_data)
        assert element.position["x"] == 999999.99
        assert element.position["y"] == -999999.99
    
    @pytest.mark.asyncio
    async def test_add_element_with_invalid_connections(self, canvas_service, mock_user_id, sample_canvas_data):
        """Test adding element with invalid connection UUIDs"""
        canvas = await canvas_service.create_canvas(sample_canvas_data, mock_user_id)
        
        # Test with invalid UUID strings
        with pytest.raises(ValueError):
            element_data = CanvasElementCreate(
                element_type="test",
                content={"text": "Test"},
                position={"x": 0, "y": 0},
                connections=["not-a-uuid", "also-invalid"]
            )
            await canvas_service.add_canvas_element(canvas.id, mock_user_id, element_data)
    
    @pytest.mark.asyncio 
    async def test_update_nonexistent_element(self, canvas_service, mock_user_id, sample_canvas_data):
        """Test updating element that doesn't exist"""
        canvas = await canvas_service.create_canvas(sample_canvas_data, mock_user_id)
        nonexistent_element_id = uuid4()
        
        result = await canvas_service.update_canvas_element(
            canvas.id, mock_user_id, nonexistent_element_id, {"content": {"new": "data"}}
        )
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_update_element_partial_data(self, canvas_service, mock_user_id, sample_canvas_data, sample_element_data):
        """Test updating element with partial data"""
        canvas = await canvas_service.create_canvas(sample_canvas_data, mock_user_id)
        element = await canvas_service.add_canvas_element(canvas.id, mock_user_id, sample_element_data)
        
        # Update only position
        update_data = {"position": {"x": 500, "y": 600}}
        updated_element = await canvas_service.update_canvas_element(
            canvas.id, mock_user_id, element.id, update_data
        )
        
        assert updated_element.position["x"] == 500
        assert updated_element.position["y"] == 600
        # Original content should remain unchanged
        assert updated_element.content == sample_element_data.content
    
    @pytest.mark.asyncio
    async def test_delete_nonexistent_element(self, canvas_service, mock_user_id, sample_canvas_data):
        """Test deleting element that doesn't exist"""
        canvas = await canvas_service.create_canvas(sample_canvas_data, mock_user_id)
        nonexistent_element_id = uuid4()
        
        result = await canvas_service.delete_canvas_element(canvas.id, mock_user_id, nonexistent_element_id)
        assert result is False
    
    @pytest.mark.asyncio
    async def test_delete_element_with_connections(self, canvas_service, mock_user_id, sample_canvas_data):
        """Test deleting element that other elements connect to"""
        canvas = await canvas_service.create_canvas(sample_canvas_data, mock_user_id)
        
        # Create first element
        element1_data = CanvasElementCreate(
            element_type="node1",
            content={"text": "Element 1"},
            position={"x": 100, "y": 100}
        )
        element1 = await canvas_service.add_canvas_element(canvas.id, mock_user_id, element1_data)
        
        # Create second element that connects to first
        element2_data = CanvasElementCreate(
            element_type="node2", 
            content={"text": "Element 2"},
            position={"x": 200, "y": 200},
            connections=[str(element1.id)]
        )
        element2 = await canvas_service.add_canvas_element(canvas.id, mock_user_id, element2_data)
        
        # Delete first element
        deleted = await canvas_service.delete_canvas_element(canvas.id, mock_user_id, element1.id)
        assert deleted is True
        
        # Check that connection was removed from element2
        updated_canvas = await canvas_service.get_canvas(canvas.id, mock_user_id)
        remaining_element = updated_canvas.elements[0]  # Should only be element2 left
        assert element1.id not in remaining_element.connections


class TestCanvasDataIntegrity:
    """Test suite for data integrity and consistency"""
    
    @pytest.mark.asyncio
    async def test_canvas_user_isolation(self, canvas_service):
        """Test that users cannot access each other's canvases"""
        user1_id = uuid4()
        user2_id = uuid4()
        
        # Create canvas for user1
        canvas1_data = StrategicCanvasCreate(title="User 1 Canvas")
        canvas1 = await canvas_service.create_canvas(canvas1_data, user1_id)
        
        # Create canvas for user2  
        canvas2_data = StrategicCanvasCreate(title="User 2 Canvas")
        canvas2 = await canvas_service.create_canvas(canvas2_data, user2_id)
        
        # User1 should only see their canvas
        user1_canvases = await canvas_service.list_canvases(user1_id)
        assert len(user1_canvases) == 1
        assert user1_canvases[0].id == canvas1.id
        
        # User2 should only see their canvas
        user2_canvases = await canvas_service.list_canvases(user2_id)
        assert len(user2_canvases) == 1
        assert user2_canvases[0].id == canvas2.id
        
        # Users cannot access each other's canvases
        assert await canvas_service.get_canvas(canvas1.id, user2_id) is None
        assert await canvas_service.get_canvas(canvas2.id, user1_id) is None
    
    @pytest.mark.asyncio
    async def test_element_connections_integrity(self, canvas_service, mock_user_id, sample_canvas_data):
        """Test that element connections maintain referential integrity"""
        canvas = await canvas_service.create_canvas(sample_canvas_data, mock_user_id)
        
        # Create multiple connected elements
        elements = []
        for i in range(3):
            element_data = CanvasElementCreate(
                element_type=f"node_{i}",
                content={"text": f"Element {i}"},
                position={"x": i * 100, "y": i * 100},
                connections=[str(elements[j].id) for j in range(len(elements))] if elements else []
            )
            element = await canvas_service.add_canvas_element(canvas.id, mock_user_id, element_data)
            elements.append(element)
        
        # Verify all connections exist
        updated_canvas = await canvas_service.get_canvas(canvas.id, mock_user_id)
        
        # Element 0 should have no connections
        assert len(updated_canvas.elements[0].connections) == 0
        
        # Element 1 should connect to element 0
        assert len(updated_canvas.elements[1].connections) == 1
        assert updated_canvas.elements[0].id in updated_canvas.elements[1].connections
        
        # Element 2 should connect to elements 0 and 1
        assert len(updated_canvas.elements[2].connections) == 2
    
    @pytest.mark.asyncio
    async def test_timestamp_consistency(self, canvas_service, mock_user_id, sample_canvas_data, sample_element_data):
        """Test that timestamps are properly maintained"""
        # Create canvas
        canvas = await canvas_service.create_canvas(sample_canvas_data, mock_user_id)
        initial_canvas_time = canvas.updated_at
        
        # Add element - should update canvas timestamp
        element = await canvas_service.add_canvas_element(canvas.id, mock_user_id, sample_element_data)
        
        updated_canvas = await canvas_service.get_canvas(canvas.id, mock_user_id)
        assert updated_canvas.updated_at > initial_canvas_time
        
        # Update element - should update both element and canvas timestamps
        previous_canvas_time = updated_canvas.updated_at
        previous_element_time = element.updated_at
        
        await canvas_service.update_canvas_element(
            canvas.id, mock_user_id, element.id, {"content": {"updated": "data"}}
        )
        
        final_canvas = await canvas_service.get_canvas(canvas.id, mock_user_id)
        updated_element = final_canvas.elements[0]
        
        assert final_canvas.updated_at > previous_canvas_time
        assert updated_element.updated_at > previous_element_time


class TestCanvasErrorHandling:
    """Test suite for error handling and edge cases"""
    
    @pytest.mark.asyncio
    async def test_operations_on_nonexistent_canvas(self, canvas_service, mock_user_id, sample_element_data):
        """Test all operations on canvas that doesn't exist"""
        nonexistent_id = uuid4()
        element_id = uuid4()
        
        # All operations should handle missing canvas gracefully
        with pytest.raises(HTTPException):
            await canvas_service.add_canvas_element(nonexistent_id, mock_user_id, sample_element_data)
        
        result = await canvas_service.update_canvas_element(
            nonexistent_id, mock_user_id, element_id, {"content": {"test": "data"}}
        )
        assert result is None
        
        result = await canvas_service.delete_canvas_element(nonexistent_id, mock_user_id, element_id)
        assert result is False
    
    @pytest.mark.asyncio
    async def test_concurrent_element_operations(self, canvas_service, mock_user_id, sample_canvas_data):
        """Test handling of concurrent operations on same canvas"""
        canvas = await canvas_service.create_canvas(sample_canvas_data, mock_user_id)
        
        # Simulate adding multiple elements concurrently
        element_tasks = []
        for i in range(5):
            element_data = CanvasElementCreate(
                element_type=f"concurrent_{i}",
                content={"index": i},
                position={"x": i * 50, "y": i * 50}
            )
            element_tasks.append(canvas_service.add_canvas_element(canvas.id, mock_user_id, element_data))
        
        # All elements should be added successfully
        elements = await asyncio.gather(*element_tasks)
        assert len(elements) == 5
        
        # Verify all elements are in the canvas
        updated_canvas = await canvas_service.get_canvas(canvas.id, mock_user_id)
        assert len(updated_canvas.elements) == 5
    
    @pytest.mark.asyncio
    async def test_malformed_element_position_data(self, canvas_service, mock_user_id, sample_canvas_data):
        """Test handling of malformed position data"""
        canvas = await canvas_service.create_canvas(sample_canvas_data, mock_user_id)
        
        # Test with missing coordinate
        element_data = CanvasElementCreate(
            element_type="test",
            content={"text": "Test"},
            position={"x": 100}  # Missing y coordinate
        )
        
        # Should succeed - position is just Dict[str, float]
        element = await canvas_service.add_canvas_element(canvas.id, mock_user_id, element_data)
        assert element.position["x"] == 100
        assert "y" not in element.position
    
    @pytest.mark.asyncio
    async def test_large_canvas_performance(self, canvas_service, mock_user_id, sample_canvas_data):
        """Test performance with large number of elements"""
        canvas = await canvas_service.create_canvas(sample_canvas_data, mock_user_id)
        
        # Add many elements to test performance
        num_elements = 100
        for i in range(num_elements):
            element_data = CanvasElementCreate(
                element_type="bulk_element",
                content={"index": i, "data": f"Element {i} content"},
                position={"x": i % 10 * 100, "y": i // 10 * 100}
            )
            await canvas_service.add_canvas_element(canvas.id, mock_user_id, element_data)
        
        # Verify all elements were added
        updated_canvas = await canvas_service.get_canvas(canvas.id, mock_user_id)
        assert len(updated_canvas.elements) == num_elements
        
        # Test that we can still perform operations efficiently
        first_element = updated_canvas.elements[0]
        result = await canvas_service.update_canvas_element(
            canvas.id, mock_user_id, first_element.id, {"content": {"updated": True}}
        )
        assert result is not None


# Import asyncio for concurrent operations test
import asyncio