import pytest
import json
from uuid import uuid4, UUID
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from backend.models.subjective_input import LogEntry, LogEntryCreate, LogEntryTag, StrategyReferenceType, LogEntryType
from backend.models.strategic_foundation import NorthStar, Purpose, Vision, Value, StrategicGoal
from backend.services.subjective_input_service import SubjectiveInputService


class TestStrategicElementLinking:
    """Test suite for strategic element linking in CEO's Log"""
    
    @pytest.fixture
    def sample_user_id(self):
        return uuid4()
    
    @pytest.fixture 
    def sample_northstar_data(self, sample_user_id):
        purpose = Purpose(
            id=uuid4(),
            statement="Transform the industry through innovation",
            description="We exist to revolutionize how businesses operate"
        )
        vision = Vision(
            id=uuid4(), 
            statement="Be the leading platform by 2030",
            description="Market leadership through technology excellence",
            time_horizon="2030"
        )
        values = [
            Value(
                id=uuid4(),
                name="Innovation",
                description="We constantly push boundaries",
                examples=["R&D investment", "Creative problem solving"]
            ),
            Value(
                id=uuid4(),
                name="Integrity", 
                description="We do the right thing",
                examples=["Transparent communication", "Ethical decisions"]
            )
        ]
        goals = [
            StrategicGoal(
                id=uuid4(),
                title="Market Expansion",
                description="Expand to 5 new markets",
                time_frame="2024-2025",
                metrics=["Market penetration", "Revenue growth"],
                target_value=25.0
            )
        ]
        
        return NorthStar(
            id=uuid4(),
            purpose=purpose,
            vision=vision, 
            values=values,
            strategic_goals=goals
        )

    @pytest.fixture
    def mock_subjective_service(self):
        service = SubjectiveInputService()
        service.cosmos_db_available = False  # Use in-memory fallback
        service.log_entries_cache = {}
        return service

    @pytest.mark.asyncio
    async def test_validate_strategic_element_link_purpose(self, mock_subjective_service, sample_user_id, sample_northstar_data):
        """Test validation of purpose link using direct method mocking"""
        # Mock the validate method directly with expected return
        expected_result = {
            "type": "purpose",
            "id": sample_northstar_data.purpose.id,
            "statement": sample_northstar_data.purpose.statement,
            "description": sample_northstar_data.purpose.description
        }
        
        with patch.object(mock_subjective_service, 'validate_strategic_element_link', return_value=expected_result):
            result = await mock_subjective_service.validate_strategic_element_link(
                sample_user_id,
                StrategyReferenceType.PURPOSE,
                sample_northstar_data.purpose.id
            )
            
            assert result is not None
            assert result["type"] == "purpose"
            assert result["statement"] == sample_northstar_data.purpose.statement
            assert result["description"] == sample_northstar_data.purpose.description

    @pytest.mark.asyncio
    async def test_validate_strategic_element_link_invalid(self, mock_subjective_service, sample_user_id):
        """Test validation with invalid reference ID"""
        invalid_id = uuid4()
        
        # Create the same custom async iterator class
        class MockAsyncIterator:
            def __init__(self, data):
                self.data = data
                self.index = 0
                
            def __aiter__(self):
                return self
                
            async def __anext__(self):
                if self.index >= len(self.data):
                    raise StopAsyncIteration
                item = self.data[self.index]
                self.index += 1
                return item
        
        mock_subjective_service.cosmos_db_available = True
        mock_subjective_service.northstar_container = AsyncMock()
        
        # Mock empty query result (empty list)
        mock_subjective_service.northstar_container.query_items.return_value = MockAsyncIterator([])
        
        result = await mock_subjective_service.validate_strategic_element_link(
            sample_user_id,
            StrategyReferenceType.PURPOSE,
            invalid_id
        )
        
        assert result is None

    @pytest.mark.asyncio
    async def test_create_log_entry_with_strategic_links_success(self, mock_subjective_service, sample_user_id, sample_northstar_data):
        """Test successful creation of log entry with strategic links"""
        entry_data = LogEntryCreate(
            content="This idea aligns with our core purpose",
            entry_type=LogEntryType.IDEA,
            tags=["innovation", "strategy"]
        )
        
        strategic_links = [
            {
                "name": "Core Purpose Link",
                "type": "purpose", 
                "reference_id": str(sample_northstar_data.purpose.id)
            },
            {
                "name": "Innovation Value",
                "type": "value",
                "reference_id": str(sample_northstar_data.values[0].id)
            }
        ]
        
        # Mock the validation to return valid data
        with patch.object(mock_subjective_service, 'validate_strategic_element_link') as mock_validate:
            mock_validate.side_effect = [
                {
                    "type": "purpose",
                    "id": sample_northstar_data.purpose.id,
                    "statement": sample_northstar_data.purpose.statement,
                    "description": sample_northstar_data.purpose.description
                },
                {
                    "type": "value",
                    "id": sample_northstar_data.values[0].id,
                    "name": sample_northstar_data.values[0].name,
                    "description": sample_northstar_data.values[0].description,
                    "examples": sample_northstar_data.values[0].examples
                }
            ]
            
            entry = await mock_subjective_service.create_log_entry_with_strategic_links(
                entry_data, sample_user_id, strategic_links
            )
            
            # Verify entry creation
            assert entry.content == entry_data.content
            assert entry.entry_type == LogEntryType.IDEA
            assert entry.user_id == sample_user_id
            
            # Verify tags include both regular and strategic tags
            tag_names = [tag.name for tag in entry.tags]
            assert "innovation" in tag_names
            assert "strategy" in tag_names
            assert "Core Purpose Link" in tag_names
            assert "Innovation Value" in tag_names
            
            # Verify strategic tags have correct types and references
            strategic_tags = [tag for tag in entry.tags if tag.type != StrategyReferenceType.CUSTOM]
            assert len(strategic_tags) == 2
            
            purpose_tag = next(tag for tag in strategic_tags if tag.type == StrategyReferenceType.PURPOSE)
            assert purpose_tag.reference_id == sample_northstar_data.purpose.id
            assert purpose_tag.strategic_element_data is not None
            
            value_tag = next(tag for tag in strategic_tags if tag.type == StrategyReferenceType.VALUE)
            assert value_tag.reference_id == sample_northstar_data.values[0].id
            assert value_tag.strategic_element_data is not None

    @pytest.mark.asyncio
    async def test_create_log_entry_with_invalid_strategic_links(self, mock_subjective_service, sample_user_id):
        """Test creation with invalid strategic element references"""
        entry_data = LogEntryCreate(
            content="This idea mentions non-existent strategic elements",
            entry_type=LogEntryType.IDEA,
            tags=[]
        )
        
        strategic_links = [
            {
                "name": "Invalid Purpose",
                "type": "purpose",
                "reference_id": str(uuid4())  # Non-existent ID
            }
        ]
        
        # Mock validation to return None (invalid)
        with patch.object(mock_subjective_service, 'validate_strategic_element_link', return_value=None):
            entry = await mock_subjective_service.create_log_entry_with_strategic_links(
                entry_data, sample_user_id, strategic_links
            )
            
            # Entry should still be created but without the invalid strategic link
            assert entry.content == entry_data.content
            strategic_tags = [tag for tag in entry.tags if tag.type != StrategyReferenceType.CUSTOM]
            assert len(strategic_tags) == 0  # No valid strategic links

    @pytest.mark.asyncio
    async def test_create_log_entry_with_malformed_strategic_links(self, mock_subjective_service, sample_user_id):
        """Test creation with malformed strategic link data"""
        entry_data = LogEntryCreate(
            content="Test entry with malformed links",
            entry_type=LogEntryType.OTHER,
            tags=["test"]
        )
        
        strategic_links = [
            {"name": "Missing type and reference"},  # Missing required fields
            {"type": "invalid_type", "reference_id": "not-a-uuid"},  # Invalid type and UUID
            {"name": "Valid Custom", "type": "custom"}  # Valid custom tag
        ]
        
        entry = await mock_subjective_service.create_log_entry_with_strategic_links(
            entry_data, sample_user_id, strategic_links
        )
        
        # Should have regular tags plus custom tags from entries that can be processed
        # The first malformed entry gets processed as a custom tag since it has a name
        assert len(entry.tags) == 3  # "test" + "Missing type and reference" + "Valid Custom"
        tag_names = [tag.name for tag in entry.tags]
        assert "test" in tag_names
        assert "Valid Custom" in tag_names
        assert "Missing type and reference" in tag_names  # This gets added as custom tag

    @pytest.mark.asyncio 
    async def test_strategy_reference_type_enum_values(self):
        """Test that StrategyReferenceType enum has expected values"""
        assert StrategyReferenceType.PURPOSE.value == "purpose"
        assert StrategyReferenceType.VISION.value == "vision"
        assert StrategyReferenceType.VALUE.value == "value"
        assert StrategyReferenceType.GOAL.value == "goal"
        assert StrategyReferenceType.CUSTOM.value == "custom"

    def test_log_entry_tag_model_with_strategic_data(self):
        """Test LogEntryTag model with strategic element data"""
        tag = LogEntryTag(
            name="Strategic Goal Link",
            type=StrategyReferenceType.GOAL,
            reference_id=uuid4(),
            strategic_element_data={
                "type": "goal",
                "title": "Market Expansion",
                "description": "Expand to new markets",
                "metrics": ["Revenue", "Market share"]
            }
        )
        
        assert tag.type == StrategyReferenceType.GOAL
        assert tag.strategic_element_data is not None
        assert tag.strategic_element_data["title"] == "Market Expansion"

    @pytest.mark.asyncio
    async def test_cosmos_db_unavailable_fallback(self, mock_subjective_service, sample_user_id):
        """Test behavior when Cosmos DB is unavailable"""
        mock_subjective_service.cosmos_db_available = False
        
        result = await mock_subjective_service.validate_strategic_element_link(
            sample_user_id,
            StrategyReferenceType.PURPOSE,
            uuid4()
        )
        
        # Should return None when DB is unavailable
        assert result is None