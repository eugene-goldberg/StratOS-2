"""
Test suite for guided SWOT/TOWS analysis functionality.
"""

import pytest
import json
from uuid import uuid4, UUID
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime
from typing import Dict, Any

from backend.models.analysis import (
    AnalysisSession,
    AnalysisSessionCreate,
    AnalysisSessionType,
    AnalysisSessionStatus,
    GuidanceRequest,
    GuidanceResponse,
    SessionStepState,
    SWOTCategory,
    SWOTItem,
    InsightSource
)
from backend.services.analysis_service import AnalysisService
from backend.ai.skills.analysis_skills.contextual_prompt_generation_skill import ContextualPromptGenerationSkill


class TestGuidedAnalysisSession:
    """Test suite for guided analysis session functionality"""
    
    @pytest.fixture
    def sample_user_id(self):
        return uuid4()
    
    @pytest.fixture
    def mock_analysis_service(self):
        service = AnalysisService()
        service.cosmos_db_available = False  # Use in-memory cache
        service.active_sessions = {}
        return service
    
    @pytest.fixture
    def sample_session_create(self):
        return AnalysisSessionCreate(
            session_type=AnalysisSessionType.GUIDED_SWOT,
            title="Market Expansion SWOT Analysis",
            description="Strategic analysis for expanding into European markets",
            topic="European Market Expansion",
            company_name="TechNova Inc"
        )
    
    @pytest.fixture
    def sample_strategic_context(self):
        return {
            "purpose": {"statement": "Empower businesses through innovative technology solutions"},
            "vision": {"statement": "Become the leading provider of business automation tools by 2030"},
            "values": [{"name": "Innovation"}, {"name": "Customer Focus"}, {"name": "Excellence"}],
            "strategic_goals": [{"title": "Achieve 50% market share in automation tools"}]
        }

    @pytest.mark.asyncio
    async def test_create_guided_swot_session(self, mock_analysis_service, sample_session_create, sample_user_id):
        """Test creating a new guided SWOT analysis session"""
        session = await mock_analysis_service.create_analysis_session(sample_session_create, sample_user_id)
        
        assert session.user_id == sample_user_id
        assert session.session_type == AnalysisSessionType.GUIDED_SWOT
        assert session.title == sample_session_create.title
        assert session.topic == sample_session_create.topic
        assert session.company_name == sample_session_create.company_name
        assert session.status == AnalysisSessionStatus.ACTIVE
        assert session.current_step == "swot_strength"
        assert session.estimated_completion_time == 30  # 30 minutes for SWOT
        
        # Check step states initialization
        expected_steps = ["swot_strength", "swot_weakness", "swot_opportunity", "swot_threat"]
        for step in expected_steps:
            assert step in session.step_states
            assert isinstance(session.step_states[step], SessionStepState)
            assert not session.step_states[step].is_completed
            assert session.step_states[step].items_count == 0

    @pytest.mark.asyncio
    async def test_create_guided_tows_session(self, mock_analysis_service, sample_user_id):
        """Test creating a guided TOWS analysis session"""
        session_create = AnalysisSessionCreate(
            session_type=AnalysisSessionType.GUIDED_TOWS,
            title="Strategic TOWS Analysis",
            topic="Digital Transformation",
            company_name="StratCorp"
        )
        
        session = await mock_analysis_service.create_analysis_session(session_create, sample_user_id)
        
        assert session.session_type == AnalysisSessionType.GUIDED_TOWS
        assert session.current_step == "tows_so"
        assert session.estimated_completion_time == 45  # 45 minutes for TOWS
        
        # Check TOWS step states
        expected_steps = ["tows_so", "tows_wo", "tows_st", "tows_wt"]
        for step in expected_steps:
            assert step in session.step_states

    @pytest.mark.asyncio
    async def test_get_analysis_session(self, mock_analysis_service, sample_session_create, sample_user_id):
        """Test retrieving an analysis session"""
        # Create session first
        created_session = await mock_analysis_service.create_analysis_session(sample_session_create, sample_user_id)
        
        # Retrieve session
        retrieved_session = await mock_analysis_service.get_analysis_session(created_session.id, sample_user_id)
        
        assert retrieved_session is not None
        assert retrieved_session.id == created_session.id
        assert retrieved_session.user_id == sample_user_id
        assert retrieved_session.title == sample_session_create.title

    @pytest.mark.asyncio
    async def test_get_nonexistent_session(self, mock_analysis_service, sample_user_id):
        """Test retrieving a non-existent session returns None"""
        nonexistent_id = uuid4()
        session = await mock_analysis_service.get_analysis_session(nonexistent_id, sample_user_id)
        assert session is None


class TestContextualPromptGenerationSkill:
    """Test suite for the contextual prompt generation skill"""
    
    @pytest.fixture
    def skill(self):
        return ContextualPromptGenerationSkill()
    
    @pytest.fixture
    def sample_strategic_context(self):
        return {
            "purpose": "Transform industries through innovative solutions",
            "vision": "Be the global leader in business automation by 2030",
            "values": ["Innovation", "Excellence", "Customer Success"],
            "strategic_goals": ["Expand to 3 new markets", "Achieve 25% market share"]
        }

    @pytest.mark.asyncio
    async def test_generate_swot_quadrant_guidance(self, skill):
        """Test generating guidance for SWOT quadrant"""
        mock_response = """
        1. What unique technological capabilities give your company a competitive advantage?
        2. How does your team's expertise compare to industry standards?
        3. What resources or assets are exclusive to your organization?
        4. Which processes or systems deliver superior performance?
        5. What do customers consistently praise about your offerings?
        """
        
        with patch('backend.ai.kernel_service.kernel_service') as mock_kernel:
            mock_kernel.generate_completion = AsyncMock(return_value=mock_response)
            
            result = await skill.generate_session_guidance(
                session_id="test-session",
                user_id="test-user",
                step_id="swot_strength",
                topic="Market Expansion",
                company_name="TechCorp",
                current_items='["Strong R&D team", "Patent portfolio"]',
                strategic_context='{"purpose": "Innovate for better business"}',
                subjective_data="CEO noted strong technical capabilities",
                objective_data="R&D spending increased 25% last year"
            )
            
            result_data = json.loads(result)
            
            assert "error" not in result_data
            assert result_data["step_id"] == "swot_strength"
            assert result_data["guidance_type"] == "swot_quadrant"
            assert result_data["primary_focus"] == "strength"
            assert len(result_data["guiding_questions"]) > 0
            assert "progress" in result_data
            assert "strategic_alignment" in result_data

    @pytest.mark.asyncio
    async def test_generate_tows_cell_guidance(self, skill):
        """Test generating guidance for TOWS cell"""
        mock_response = """
        1. How can your technological strengths help capitalize on market opportunities?
        2. What partnerships could leverage your capabilities for new market entry?
        3. Which product innovations could address emerging customer needs?
        4. How might your expertise create first-mover advantages?
        """
        
        with patch('backend.ai.kernel_service.kernel_service') as mock_kernel:
            mock_kernel.generate_completion = AsyncMock(return_value=mock_response)
            
            result = await skill.generate_session_guidance(
                session_id="test-session",
                user_id="test-user", 
                step_id="tows_so",
                topic="Market Expansion",
                company_name="TechCorp",
                current_items='[{"cell_type": "SO", "strategy": "Partner with local distributors"}]',
                strategic_context='{"purpose": "Innovate for better business"}',
                subjective_data="",
                objective_data=""
            )
            
            result_data = json.loads(result)
            
            assert "error" not in result_data
            assert result_data["step_id"] == "tows_so"
            assert result_data["guidance_type"] == "tows_cell"
            assert result_data["primary_focus"] == "SO"

    def test_parse_strategic_context(self, skill):
        """Test parsing strategic context from JSON"""
        context_json = json.dumps({
            "purpose": {"statement": "Transform business operations"},
            "vision": {"statement": "Lead the automation revolution"},
            "values": [{"name": "Innovation"}, {"name": "Excellence"}],
            "strategic_goals": [{"title": "Expand globally"}, {"title": "Double revenue"}]
        })
        
        parsed = skill._parse_strategic_context(context_json)
        
        assert parsed["purpose"] == "Transform business operations"
        assert parsed["vision"] == "Lead the automation revolution"
        assert parsed["values"] == ["Innovation", "Excellence"]
        assert parsed["strategic_goals"] == ["Expand globally", "Double revenue"]

    def test_parse_strategic_context_invalid_json(self, skill):
        """Test parsing invalid strategic context JSON"""
        parsed = skill._parse_strategic_context("invalid json")
        
        assert parsed["purpose"] == ""
        assert parsed["vision"] == ""
        assert parsed["values"] == []
        assert parsed["strategic_goals"] == []

    def test_determine_guidance_type(self, skill):
        """Test determining guidance type from step ID"""
        swot_type, swot_focus = skill._determine_guidance_type("swot_strength")
        assert swot_type == "swot_quadrant"
        assert swot_focus == "strength"
        
        tows_type, tows_focus = skill._determine_guidance_type("tows_so")
        assert tows_type == "tows_cell"
        assert tows_focus == "SO"
        
        general_type, general_focus = skill._determine_guidance_type("custom_step")
        assert general_type == "general"
        assert general_focus == "custom_step"

    def test_extract_questions_from_response(self, skill):
        """Test extracting questions from AI response"""
        ai_response = """
        1. What are your core technological advantages?
        2. How does your team compare to competitors?
        3. Which resources give you an edge?
        - What do customers value most?
        • How do you measure success?
        Not a question without question mark
        """
        
        questions = skill._extract_questions_from_response(ai_response)
        
        assert len(questions) == 5
        assert "What are your core technological advantages?" in questions
        assert "How does your team compare to competitors?" in questions
        assert "Which resources give you an edge?" in questions
        assert "What do customers value most?" in questions
        assert "How do you measure success?" in questions

    def test_generate_suggestions_swot(self, skill):
        """Test generating suggestions for SWOT analysis"""
        context = {
            "guidance_type": "swot_quadrant",
            "primary_focus": "strength",
            "topic": "Market Expansion"
        }
        
        suggestions = skill._generate_suggestions(context, ["item1", "item2"])
        
        assert len(suggestions) > 0
        assert any("strength" in suggestion.lower() for suggestion in suggestions)

    def test_generate_suggestions_tows(self, skill):
        """Test generating suggestions for TOWS analysis"""
        context = {
            "guidance_type": "tows_cell",
            "primary_focus": "SO"
        }
        
        suggestions = skill._generate_suggestions(context, ["strategy1"])
        
        assert len(suggestions) > 0
        assert any("combine" in suggestion.lower() for suggestion in suggestions)

    def test_format_strategic_context(self, skill):
        """Test formatting strategic context for prompts"""
        context = {
            "purpose": "Transform businesses",
            "vision": "Lead the market",
            "values": ["Innovation", "Excellence"],
            "strategic_goals": ["Expand globally", "Increase revenue"]
        }
        
        formatted = skill._format_strategic_context(context)
        
        assert "Purpose: Transform businesses" in formatted
        assert "Vision: Lead the market" in formatted
        assert "Values: Innovation, Excellence" in formatted
        assert "Strategic Goals: Expand globally; Increase revenue" in formatted

    def test_format_strategic_context_empty(self, skill):
        """Test formatting empty strategic context"""
        context = {"purpose": "", "vision": "", "values": [], "strategic_goals": []}
        
        formatted = skill._format_strategic_context(context)
        
        assert formatted == "No strategic foundation defined yet."


class TestSessionGuidanceIntegration:
    """Integration tests for session guidance functionality"""
    
    @pytest.fixture
    def mock_analysis_service(self):
        service = AnalysisService()
        service.cosmos_db_available = False
        service.active_sessions = {}
        return service

    @pytest.mark.asyncio
    async def test_get_session_guidance_integration(self, mock_analysis_service):
        """Test getting session guidance with mocked dependencies"""
        # Setup
        user_id = uuid4()
        session_create = AnalysisSessionCreate(
            session_type=AnalysisSessionType.GUIDED_SWOT,
            title="Test Analysis",
            topic="Business Growth",
            company_name="TestCorp"
        )
        
        # Create session
        session = await mock_analysis_service.create_analysis_session(session_create, user_id)
        
        # Mock dependencies
        mock_response = """
        1. What unique capabilities drive your competitive advantage?
        2. How do your resources compare to industry leaders?
        3. What internal processes deliver exceptional results?
        """
        
        with patch.object(mock_analysis_service, '_get_strategic_context', return_value={}), \
             patch.object(mock_analysis_service, '_get_relevant_subjective_data', return_value=""), \
             patch.object(mock_analysis_service, '_get_relevant_objective_data', return_value=""), \
             patch('backend.ai.kernel_service.kernel_service') as mock_kernel:
            
            mock_kernel.generate_completion = AsyncMock(return_value=mock_response)
            
            guidance_request = GuidanceRequest(
                session_id=session.id,
                step_id="swot_strength"
            )
            
            guidance_response = await mock_analysis_service.get_session_guidance(guidance_request, user_id)
            
            assert guidance_response is not None
            assert guidance_response.session_id == session.id
            assert guidance_response.step_id == "swot_strength"
            assert len(guidance_response.guiding_questions) > 0
            assert len(guidance_response.suggestions) > 0

    @pytest.mark.asyncio
    async def test_get_session_guidance_nonexistent_session(self, mock_analysis_service):
        """Test getting guidance for non-existent session raises error"""
        user_id = uuid4()
        nonexistent_session_id = uuid4()
        
        guidance_request = GuidanceRequest(
            session_id=nonexistent_session_id,
            step_id="swot_strength"
        )
        
        with pytest.raises(Exception):  # Should raise HTTPException
            await mock_analysis_service.get_session_guidance(guidance_request, user_id)


class TestSessionProgressTracking:
    """Test suite for session progress tracking"""
    
    @pytest.fixture
    def mock_service(self):
        service = AnalysisService()
        service.cosmos_db_available = False
        service.active_sessions = {}
        return service

    def test_initialize_swot_step_states(self, mock_service):
        """Test initialization of SWOT step states"""
        step_states = mock_service._initialize_step_states(AnalysisSessionType.GUIDED_SWOT)
        
        expected_steps = ["swot_strength", "swot_weakness", "swot_opportunity", "swot_threat"]
        
        assert len(step_states) == 4
        for step in expected_steps:
            assert step in step_states
            assert isinstance(step_states[step], SessionStepState)
            assert step_states[step].step_id == step
            assert not step_states[step].is_completed
            assert step_states[step].items_count == 0

    def test_initialize_tows_step_states(self, mock_service):
        """Test initialization of TOWS step states"""
        step_states = mock_service._initialize_step_states(AnalysisSessionType.GUIDED_TOWS)
        
        expected_steps = ["tows_so", "tows_wo", "tows_st", "tows_wt"]
        
        assert len(step_states) == 4
        for step in expected_steps:
            assert step in step_states

    def test_get_initial_step_swot(self, mock_service):
        """Test getting initial step for SWOT session"""
        initial_step = mock_service._get_initial_step(AnalysisSessionType.GUIDED_SWOT)
        assert initial_step == "swot_strength"

    def test_get_initial_step_tows(self, mock_service):
        """Test getting initial step for TOWS session"""
        initial_step = mock_service._get_initial_step(AnalysisSessionType.GUIDED_TOWS)
        assert initial_step == "tows_so"

    def test_estimate_session_time(self, mock_service):
        """Test session time estimation"""
        swot_time = mock_service._estimate_session_time(AnalysisSessionType.GUIDED_SWOT)
        assert swot_time == 30
        
        tows_time = mock_service._estimate_session_time(AnalysisSessionType.GUIDED_TOWS)
        assert tows_time == 45

    def test_get_current_items_for_swot_step(self, mock_service):
        """Test getting current items for SWOT step"""
        # Create mock session with SWOT items
        session = AnalysisSession(
            id=uuid4(),
            user_id=uuid4(),
            session_type=AnalysisSessionType.GUIDED_SWOT,
            title="Test",
            topic="Test",
            current_step="swot_strength",
            step_states={},
            swot_items=[
                SWOTItem(category=SWOTCategory.STRENGTH, content="Strong team", source=InsightSource.AI_GENERATED),
                SWOTItem(category=SWOTCategory.STRENGTH, content="Good tech", source=InsightSource.AI_GENERATED),
                SWOTItem(category=SWOTCategory.WEAKNESS, content="Limited budget", source=InsightSource.AI_GENERATED)
            ]
        )
        
        strength_items = mock_service._get_current_items_for_step(session, "swot_strength")
        weakness_items = mock_service._get_current_items_for_step(session, "swot_weakness")
        
        assert len(strength_items) == 2
        assert len(weakness_items) == 1
        assert all(item.category == SWOTCategory.STRENGTH for item in strength_items)
        assert all(item.category == SWOTCategory.WEAKNESS for item in weakness_items)

    def test_get_current_items_for_tows_step(self, mock_service):
        """Test getting current items for TOWS step"""
        session = AnalysisSession(
            id=uuid4(),
            user_id=uuid4(),
            session_type=AnalysisSessionType.GUIDED_TOWS,
            title="Test",
            topic="Test", 
            current_step="tows_so",
            step_states={},
            tows_strategies=[
                {"cell_type": "SO", "strategy": "Leverage strengths for opportunities"},
                {"cell_type": "SO", "strategy": "Use capabilities for growth"},
                {"cell_type": "WO", "strategy": "Address weaknesses through opportunities"}
            ]
        )
        
        so_items = mock_service._get_current_items_for_step(session, "tows_so")
        wo_items = mock_service._get_current_items_for_step(session, "tows_wo")
        
        assert len(so_items) == 2
        assert len(wo_items) == 1
        assert all(item["cell_type"] == "SO" for item in so_items)
        assert all(item["cell_type"] == "WO" for item in wo_items)