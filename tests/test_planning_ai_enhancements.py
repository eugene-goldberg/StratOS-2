"""
Tests for Planning AI Enhancements (A2)
Testing enhanced analyze_plan_alignment, generate_plan_variants, and generate_actions methods
"""

import pytest
import pytest_asyncio
import json
from uuid import uuid4, UUID
from datetime import datetime, date
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import HTTPException

from backend.services.planning_service import PlanningService
from backend.services.strategic_foundation_service import StrategicFoundationService
from backend.models.planning import (
    StrategicPlanCreate, StrategicPlan, PlanStatus,
    InitiativeCreate, Initiative, InitiativeType,
    ActionCreate, Action, ActionStatus
)
from backend.models.strategic_foundation import (
    NorthStar, Purpose, Vision, Value, StrategicGoal
)


@pytest_asyncio.fixture
async def planning_service_with_ai():
    """Setup planning service with mocked dependencies for AI testing"""
    service = PlanningService()
    # Force in-memory cache
    service.cosmos_db_available = False
    service.plans_cache = {}
    service.initiatives_cache = {}
    
    # Mock foundation_service dependency
    mock_foundation_service = AsyncMock(spec=StrategicFoundationService)
    service.foundation_service = mock_foundation_service
    
    return service


@pytest_asyncio.fixture
def mock_user_id():
    return uuid4()


@pytest_asyncio.fixture
def mock_north_star():
    """Mock North Star data for testing"""
    return NorthStar(
        id=uuid4(),
        user_id=uuid4(),
        purpose=Purpose(statement="Transform business operations through innovation"),
        vision=Vision(statement="Lead the automation revolution in our industry"),
        values=[
            Value(name="Innovation", description="Push boundaries"),
            Value(name="Excellence", description="Deliver quality")
        ],
        strategic_goals=[
            StrategicGoal(id=uuid4(), title="Expand globally", description="Enter 3 new markets"),
            StrategicGoal(id=uuid4(), title="Double revenue", description="Achieve 100% growth")
        ]
    )


@pytest_asyncio.fixture
def mock_strategic_plan():
    """Mock strategic plan for testing"""
    return StrategicPlan(
        id=uuid4(),
        user_id=uuid4(),
        title="Digital Transformation Plan",
        description="Modernize operations and technology",
        status=PlanStatus.ACTIVE,
        time_horizon="2 years",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )


@pytest_asyncio.fixture
def mock_initiative():
    """Mock initiative for testing"""
    return Initiative(
        id=uuid4(),
        plan_id=uuid4(),
        user_id=uuid4(),
        title="Implement AI-driven analytics",
        description="Deploy machine learning for business insights",
        initiative_type=InitiativeType.STRATEGIC,
        status=PlanStatus.ACTIVE,
        actions=[],
        resources=[],
        risks=[],
        created_at=datetime.now(),
        updated_at=datetime.now()
    )


class TestAnalyzePlanAlignment:
    """Test suite for enhanced analyze_plan_alignment method"""
    
    @pytest.mark.asyncio
    @patch('backend.services.planning_service.kernel_service', new_callable=AsyncMock)
    async def test_analyze_plan_alignment_comprehensive(
        self, mock_kernel, planning_service_with_ai, mock_user_id, 
        mock_north_star, mock_strategic_plan
    ):
        """Test comprehensive plan alignment analysis with enhanced prompt"""
        service = planning_service_with_ai
        
        # Setup mocks
        service.foundation_service.get_north_star = AsyncMock(return_value=mock_north_star)
        # Ensure plan user_id matches test user_id
        mock_strategic_plan.user_id = mock_user_id
        service.plans_cache[str(mock_strategic_plan.id)] = mock_strategic_plan
        
        # Mock initiatives
        initiatives = [
            Initiative(
                id=uuid4(), plan_id=mock_strategic_plan.id, user_id=mock_user_id,
                title="Cloud Migration", description="Move to cloud infrastructure",
                initiative_type=InitiativeType.STRATEGIC, status=PlanStatus.ACTIVE,
                linked_strategic_goal=mock_north_star.strategic_goals[0].id,
                actions=[], resources=[], risks=[],
                created_at=datetime.now(), updated_at=datetime.now()
            ),
            Initiative(
                id=uuid4(), plan_id=mock_strategic_plan.id, user_id=mock_user_id,
                title="Market Research", description="Analyze new market opportunities",
                initiative_type=InitiativeType.OPERATIONAL, status=PlanStatus.ACTIVE,
                actions=[], resources=[], risks=[],
                created_at=datetime.now(), updated_at=datetime.now()
            )
        ]
        
        for initiative in initiatives:
            service.initiatives_cache[str(initiative.id)] = initiative
        
        # Mock AI response with enhanced structure
        mock_ai_response = {
            "overall_assessment": "Good",
            "purpose_alignment": "Initiatives strongly support the transformation purpose with clear technology focus",
            "vision_coherence": "Cloud migration aligns with automation leadership vision",
            "goal_coverage": "Global expansion goal partially addressed through market research",
            "values_integration": "Innovation reflected in technology initiatives",
            "strategic_cohesion": "Initiatives work synergistically toward digital transformation",
            "key_strengths": ["Technology focus aligns with purpose", "Clear strategic goal linkage"],
            "critical_gaps": ["Limited people development initiatives", "No specific automation projects"],
            "recommendations": [
                "Add automation-specific initiatives to better support vision",
                "Include talent development to support transformation"
            ],
            "strategic_risks": ["Technology focus may neglect organizational change management"]
        }
        
        mock_kernel.generate_completion = AsyncMock(return_value=json.dumps(mock_ai_response))
        
        # Execute test
        result = await service.analyze_plan_alignment(mock_strategic_plan.id, mock_user_id)
        
        # Verify results
        assert result["plan_id"] == str(mock_strategic_plan.id)
        assert "quantitative_score" in result
        assert result["quantitative_score"] == 5.0  # 1 of 2 initiatives linked = 50% = 5.0
        
        ai_analysis = result["ai_analysis"]
        assert ai_analysis["overall_assessment"] == "Good"
        assert "purpose_alignment" in ai_analysis
        assert "vision_coherence" in ai_analysis
        assert "goal_coverage" in ai_analysis
        assert "values_integration" in ai_analysis
        assert "strategic_cohesion" in ai_analysis
        assert isinstance(ai_analysis["key_strengths"], list)
        assert isinstance(ai_analysis["critical_gaps"], list)
        assert isinstance(ai_analysis["recommendations"], list)
        assert isinstance(ai_analysis["strategic_risks"], list)
        
        # Verify prompt enhancement - check call was made with enhanced prompt
        mock_kernel.generate_completion.assert_called_once()
        call_args = mock_kernel.generate_completion.call_args[0]
        prompt = call_args[0]
        
        # Verify enhanced prompt structure
        assert "STRATEGIC FOUNDATION:" in prompt
        assert "ANALYSIS REQUIREMENTS:" in prompt
        assert "PURPOSE ALIGNMENT:" in prompt
        assert "VISION COHERENCE:" in prompt
        assert "STRATEGIC GOAL COVERAGE:" in prompt
        assert "VALUES INTEGRATION:" in prompt
        assert "OVERALL STRATEGIC COHESION:" in prompt
        assert mock_north_star.purpose.statement in prompt
        assert mock_north_star.vision.statement in prompt
    
    @pytest.mark.asyncio
    @patch('backend.services.planning_service.kernel_service', new_callable=AsyncMock)
    async def test_analyze_plan_alignment_no_north_star(
        self, mock_kernel, planning_service_with_ai, mock_user_id, mock_strategic_plan
    ):
        """Test plan alignment when no North Star is defined"""
        service = planning_service_with_ai
        
        # Setup mocks - no north star
        service.foundation_service.get_north_star = AsyncMock(return_value=None)
        mock_strategic_plan.user_id = mock_user_id
        service.plans_cache[str(mock_strategic_plan.id)] = mock_strategic_plan
        
        mock_ai_response = {
            "overall_assessment": "Poor",
            "purpose_alignment": "Cannot assess without defined purpose",
            "recommendations": ["Define organizational North Star first"]
        }
        
        mock_kernel.generate_completion = AsyncMock(return_value=json.dumps(mock_ai_response))
        
        result = await service.analyze_plan_alignment(mock_strategic_plan.id, mock_user_id)
        
        # Verify prompt includes "not defined" message
        call_args = mock_kernel.generate_completion.call_args[0]
        prompt = call_args[0]
        assert "User's North Star is not defined" in prompt
        
        assert result["ai_analysis"]["overall_assessment"] == "Poor"
    
    @pytest.mark.asyncio
    @patch('backend.services.planning_service.kernel_service', new_callable=AsyncMock)
    async def test_analyze_plan_alignment_error_handling(
        self, mock_kernel, planning_service_with_ai, mock_user_id, mock_strategic_plan
    ):
        """Test error handling in plan alignment analysis"""
        service = planning_service_with_ai
        
        service.foundation_service.get_north_star = AsyncMock(return_value=None)
        mock_strategic_plan.user_id = mock_user_id
        service.plans_cache[str(mock_strategic_plan.id)] = mock_strategic_plan
        
        # Mock AI error
        mock_kernel.generate_completion = AsyncMock(side_effect=Exception("AI service error"))
        
        result = await service.analyze_plan_alignment(mock_strategic_plan.id, mock_user_id)
        
        assert result["ai_analysis"]["overall_assessment"] == "Error"
        assert "AI service error" in result["ai_analysis"]["purpose_alignment"]


class TestGeneratePlanVariants:
    """Test suite for enhanced generate_plan_variants method"""
    
    @pytest.mark.asyncio
    @patch('backend.services.planning_service.kernel_service', new_callable=AsyncMock)
    async def test_generate_plan_variants_enhanced(
        self, mock_kernel, planning_service_with_ai, mock_user_id,
        mock_north_star, mock_strategic_plan
    ):
        """Test enhanced plan variant generation with strategic context"""
        service = planning_service_with_ai
        
        # Setup mocks
        service.foundation_service.get_north_star = AsyncMock(return_value=mock_north_star)
        service.plans_cache[str(mock_strategic_plan.id)] = mock_strategic_plan
        
        # Add base plan to user context
        mock_strategic_plan.user_id = mock_user_id
        
        # Mock initiatives for context
        initiative = Initiative(
            id=uuid4(), plan_id=mock_strategic_plan.id, user_id=mock_user_id,
            title="Digital Platform", description="Build customer platform",
            initiative_type=InitiativeType.STRATEGIC, status=PlanStatus.DRAFT,
            actions=[], resources=[], risks=[],
            created_at=datetime.now(), updated_at=datetime.now()
        )
        service.initiatives_cache[str(initiative.id)] = initiative
        
        # Mock enhanced AI response
        mock_variants_response = [
            {
                "title": "Aggressive Growth Variant",
                "description": "Focus on rapid market expansion through aggressive investment and risk-taking. Prioritize speed over optimization.",
                "strategic_rationale": "Best suited for high-growth markets with first-mover advantages available"
            },
            {
                "title": "Steady Optimization Variant", 
                "description": "Focus on operational excellence and gradual improvement. Emphasize efficiency and risk mitigation.",
                "strategic_rationale": "Ideal for mature markets where competitive advantage comes from operational excellence"
            }
        ]
        
        mock_kernel.generate_completion = AsyncMock(return_value=json.dumps(mock_variants_response))
        
        # Execute test with focus areas
        focus_areas = ["market expansion", "operational efficiency"]
        variants = await service.generate_plan_variants(
            mock_strategic_plan.id, mock_user_id, num_variants=2, focus_areas=focus_areas
        )
        
        # Verify results
        assert len(variants) == 2
        
        # Check first variant
        variant1 = variants[0]
        assert "Aggressive Growth Variant" in variant1.title
        assert "rapid market expansion" in variant1.description
        assert "Strategic Rationale:" in variant1.description
        assert "first-mover advantages" in variant1.description
        assert variant1.status == PlanStatus.DRAFT
        
        # Check second variant
        variant2 = variants[1]
        assert "Steady Optimization Variant" in variant2.title
        assert "operational excellence" in variant2.description
        assert "Strategic Rationale:" in variant2.description
        
        # Verify prompt enhancement
        call_args = mock_kernel.generate_completion.call_args[0]
        prompt = call_args[0]
        
        # Check enhanced prompt structure
        assert "strategically distinct plan variants" in prompt
        assert "STRATEGIC FOUNDATION:" in prompt
        assert "BASE PLAN ANALYSIS:" in prompt
        assert "VARIANT GENERATION FOCUS:" in prompt
        assert "REQUIREMENTS FOR EACH VARIANT:" in prompt
        assert "STRATEGIC DISTINCTION:" in prompt
        assert "PURPOSE ALIGNMENT:" in prompt
        assert "FEASIBILITY:" in prompt
        assert mock_north_star.purpose.statement in prompt
        assert ", ".join(focus_areas) in prompt
        assert initiative.title in prompt
    
    @pytest.mark.asyncio
    @patch('backend.services.planning_service.kernel_service', new_callable=AsyncMock)
    async def test_generate_plan_variants_no_focus_areas(
        self, mock_kernel, planning_service_with_ai, mock_user_id, mock_strategic_plan
    ):
        """Test plan variant generation without specific focus areas"""
        service = planning_service_with_ai
        
        service.foundation_service.get_north_star = AsyncMock(return_value=None)
        service.plans_cache[str(mock_strategic_plan.id)] = mock_strategic_plan
        mock_strategic_plan.user_id = mock_user_id
        
        mock_variants_response = [
            {
                "title": "Technology-First Variant",
                "description": "Emphasize technological innovation",
                "strategic_rationale": "Suitable for tech-driven industries"
            }
        ]
        
        mock_kernel.generate_completion = AsyncMock(return_value=json.dumps(mock_variants_response))
        
        variants = await service.generate_plan_variants(mock_strategic_plan.id, mock_user_id, num_variants=1)
        
        assert len(variants) == 1
        
        # Verify default focus is used
        call_args = mock_kernel.generate_completion.call_args[0]
        prompt = call_args[0]
        assert "diverse strategic approaches covering different execution philosophies" in prompt


class TestGenerateActions:
    """Test suite for enhanced generate_actions method"""
    
    @pytest.mark.asyncio
    @patch('backend.services.planning_service.kernel_service', new_callable=AsyncMock)
    async def test_generate_actions_smart_framework(
        self, mock_kernel, planning_service_with_ai, mock_user_id,
        mock_north_star, mock_strategic_plan, mock_initiative
    ):
        """Test SMART action generation with strategic context"""
        service = planning_service_with_ai
        
        # Setup mocks
        service.foundation_service.get_north_star = AsyncMock(return_value=mock_north_star)
        
        # Setup initiative with proper context
        mock_initiative.user_id = mock_user_id
        mock_initiative.plan_id = mock_strategic_plan.id
        mock_initiative.start_date = date.today()
        mock_initiative.end_date = date(2024, 12, 31)
        mock_initiative.owner = "AI Team Lead"
        mock_initiative.linked_strategic_goal = mock_north_star.strategic_goals[0].id
        
        service.initiatives_cache[str(mock_initiative.id)] = mock_initiative
        # Ensure plan user_id matches
        mock_strategic_plan.user_id = mock_user_id
        service.plans_cache[str(mock_strategic_plan.id)] = mock_strategic_plan
        
        # Mock enhanced AI response with SMART structure
        mock_actions_response = [
            {
                "title": "Define AI analytics requirements and success metrics",
                "description": "Create comprehensive requirements document specifying data sources, analytics capabilities, and KPIs. Success criteria: Approved requirements document with measurable metrics within 3 weeks.",
                "suggested_owner": "Data Science Manager",
                "estimated_timeline": "3 weeks",
                "priority": "High"
            },
            {
                "title": "Assemble cross-functional AI implementation team",
                "description": "Recruit data scientists, ML engineers, and business analysts. Success criteria: Full team of 5 members assembled and onboarded within 4 weeks.",
                "suggested_owner": "AI Team Lead",
                "estimated_timeline": "4 weeks", 
                "priority": "High"
            },
            {
                "title": "Establish development environment and data pipeline",
                "description": "Set up ML development tools, data access, and model deployment infrastructure. Success criteria: Development environment operational and first prototype deployed within 6 weeks.",
                "suggested_owner": "DevOps Engineer",
                "estimated_timeline": "6 weeks",
                "priority": "Medium"
            }
        ]
        
        mock_kernel.generate_completion = AsyncMock(return_value=json.dumps(mock_actions_response))
        
        # Execute test
        actions = await service.generate_actions(mock_initiative.id, mock_user_id)
        
        # Verify results
        assert len(actions) == 3
        
        # Check first action (requirements)
        action1 = actions[0]
        assert "requirements and success metrics" in action1.title
        assert "Success criteria:" in action1.description
        assert "Timeline: 3 weeks" in action1.description
        assert "Suggested Owner: Data Science Manager" in action1.description
        assert "Priority: High" in action1.description
        assert action1.owner == "Data Science Manager"
        assert action1.status == ActionStatus.NOT_STARTED
        
        # Check second action (team)
        action2 = actions[1]
        assert "cross-functional" in action2.title
        assert "Timeline: 4 weeks" in action2.description
        assert action2.owner == "AI Team Lead"
        
        # Check third action (infrastructure)
        action3 = actions[2]
        assert "development environment" in action3.title
        assert "Priority: Medium" in action3.description
        
        # Verify prompt enhancement
        call_args = mock_kernel.generate_completion.call_args[0]
        prompt = call_args[0]
        
        # Check SMART framework in prompt
        assert "SMART (Specific, Measurable, Achievable, Relevant, Time-bound)" in prompt
        assert "STRATEGIC CONTEXT:" in prompt
        assert "PLAN CONTEXT:" in prompt
        assert "INITIATIVE DETAILS:" in prompt
        assert "EXISTING ACTIONS:" in prompt
        assert "ACTION GENERATION REQUIREMENTS:" in prompt
        assert "1. SPECIFIC:" in prompt
        assert "2. MEASURABLE:" in prompt
        assert "3. ACHIEVABLE:" in prompt
        assert "4. RELEVANT:" in prompt
        assert "5. TIME-BOUND:" in prompt
        assert "6. NON-OVERLAPPING:" in prompt
        assert "7. SEQUENTIAL LOGIC:" in prompt
        
        # Check context inclusion
        assert mock_north_star.purpose.statement in prompt
        assert mock_strategic_plan.title in prompt
        assert mock_initiative.title in prompt
        assert mock_initiative.description in prompt
        assert mock_initiative.owner in prompt
    
    @pytest.mark.asyncio
    @patch('backend.services.planning_service.kernel_service', new_callable=AsyncMock)
    async def test_generate_actions_with_existing_actions(
        self, mock_kernel, planning_service_with_ai, mock_user_id, mock_initiative
    ):
        """Test action generation that considers existing actions"""
        service = planning_service_with_ai
        
        service.foundation_service.get_north_star = AsyncMock(return_value=None)
        
        # Add existing actions to initiative
        existing_action = Action(
            id=uuid4(),
            title="Initial research completed",
            description="Market research and feasibility study",
            status=ActionStatus.COMPLETED,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        mock_initiative.actions = [existing_action]
        mock_initiative.user_id = mock_user_id
        # Mock initiative doesn't need a plan for this test - set plan_id to None
        mock_initiative.plan_id = None
        
        service.initiatives_cache[str(mock_initiative.id)] = mock_initiative
        
        mock_actions_response = [
            {
                "title": "Design system architecture",
                "description": "Create technical design based on research findings",
                "suggested_owner": "System Architect",
                "estimated_timeline": "2 weeks",
                "priority": "High"
            }
        ]
        
        mock_kernel.generate_completion = AsyncMock(return_value=json.dumps(mock_actions_response))
        
        actions = await service.generate_actions(mock_initiative.id, mock_user_id)
        
        # Verify existing actions are included in prompt
        call_args = mock_kernel.generate_completion.call_args[0]
        prompt = call_args[0]
        assert "Initial research completed" in prompt
        assert "NON-OVERLAPPING" in prompt
        
        assert len(actions) == 1
        assert "architecture" in actions[0].title
    
    @pytest.mark.asyncio
    @patch('backend.services.planning_service.kernel_service', new_callable=AsyncMock)
    async def test_generate_actions_fallback(
        self, mock_kernel, planning_service_with_ai, mock_user_id, mock_initiative
    ):
        """Test fallback action generation when AI fails"""
        service = planning_service_with_ai
        
        service.foundation_service.get_north_star = AsyncMock(return_value=None)
        mock_initiative.user_id = mock_user_id
        # Mock initiative doesn't need a plan for this test - set plan_id to None
        mock_initiative.plan_id = None
        service.initiatives_cache[str(mock_initiative.id)] = mock_initiative
        
        # Mock AI failure
        mock_kernel.generate_completion = AsyncMock(side_effect=Exception("AI error"))
        
        actions = await service.generate_actions(mock_initiative.id, mock_user_id)
        
        # Verify fallback actions are SMART-structured
        assert len(actions) == 3
        assert "scope and requirements" in actions[0].title
        assert "Success criteria:" in actions[0].description
        assert "Timeline: 2 weeks" in actions[0].description
        assert actions[0].owner == "Project Manager"
        
        assert "team and allocate resources" in actions[1].title
        assert "Success criteria:" in actions[1].description
        
        assert "measurement framework" in actions[2].title
        assert "Success criteria:" in actions[2].description
    
    @pytest.mark.asyncio
    async def test_generate_actions_unauthorized_user(
        self, planning_service_with_ai, mock_initiative
    ):
        """Test action generation with unauthorized user"""
        service = planning_service_with_ai
        
        # Different user ID
        unauthorized_user_id = uuid4()
        mock_initiative.user_id = uuid4()  # Different from unauthorized_user_id
        service.initiatives_cache[str(mock_initiative.id)] = mock_initiative
        
        with pytest.raises(HTTPException) as exc_info:
            await service.generate_actions(mock_initiative.id, unauthorized_user_id)
        
        assert exc_info.value.status_code == 403
        assert "not authorized" in str(exc_info.value.detail)


# Integration test to ensure all enhancements work together
class TestPlanningAIIntegration:
    """Integration tests for all planning AI enhancements"""
    
    @pytest.mark.asyncio
    @patch('backend.services.planning_service.kernel_service', new_callable=AsyncMock)
    async def test_full_planning_ai_workflow(
        self, mock_kernel, planning_service_with_ai, mock_user_id, mock_north_star
    ):
        """Test complete workflow: create plan -> analyze -> generate variants -> generate actions"""
        service = planning_service_with_ai
        
        service.foundation_service.get_north_star = AsyncMock(return_value=mock_north_star)
        service.foundation_service.get_strategic_goal = AsyncMock(
            return_value=mock_north_star.strategic_goals[0]
        )
        
        # 1. Create strategic plan
        plan_data = StrategicPlanCreate(
            title="AI Integration Strategy",
            description="Integrate AI across business operations",
            time_horizon="18 months"
        )
        plan = await service.create_strategic_plan(mock_user_id, plan_data)
        
        # 2. Create initiative
        initiative_data = InitiativeCreate(
            title="Implement AI Analytics",
            description="Deploy ML models for business intelligence",
            initiative_type=InitiativeType.STRATEGIC,
            linked_strategic_goal=mock_north_star.strategic_goals[0].id
        )
        initiative = await service.create_initiative(plan.id, mock_user_id, initiative_data)
        
        # 3. Mock AI responses for each method
        mock_kernel.generate_completion = AsyncMock(side_effect=[
            # analyze_plan_alignment response
            json.dumps({
                "overall_assessment": "Good",
                "purpose_alignment": "Strong alignment with transformation purpose",
                "recommendations": ["Add more customer-facing AI initiatives"]
            }),
            # generate_plan_variants response  
            json.dumps([{
                "title": "Customer-First AI Strategy",
                "description": "Focus on customer experience improvements",
                "strategic_rationale": "Higher customer satisfaction ROI"
            }]),
            # generate_actions response
            json.dumps([{
                "title": "Setup ML development environment",
                "description": "Configure tools and infrastructure",
                "suggested_owner": "DevOps Engineer",
                "estimated_timeline": "2 weeks",
                "priority": "High"
            }])
        ])
        
        # 4. Test analyze_plan_alignment
        alignment_result = await service.analyze_plan_alignment(plan.id, mock_user_id)
        assert alignment_result["ai_analysis"]["overall_assessment"] == "Good"
        
        # 5. Test generate_plan_variants
        variants = await service.generate_plan_variants(plan.id, mock_user_id, num_variants=1)
        assert len(variants) == 1
        assert "Customer-First" in variants[0].title
        
        # 6. Test generate_actions
        actions = await service.generate_actions(initiative.id, mock_user_id)
        assert len(actions) == 1
        assert "ML development" in actions[0].title
        
        # Verify all methods were called with enhanced prompts
        assert mock_kernel.generate_completion.call_count == 3
        
        # Check that each call used enhanced prompts
        calls = mock_kernel.generate_completion.call_args_list
        
        # Alignment prompt should include comprehensive analysis requirements
        alignment_prompt = calls[0][0][0]
        assert "ANALYSIS REQUIREMENTS:" in alignment_prompt
        assert "PURPOSE ALIGNMENT:" in alignment_prompt
        
        # Variants prompt should include strategic distinction requirements
        variants_prompt = calls[1][0][0]
        assert "STRATEGIC DISTINCTION:" in variants_prompt
        assert "strategically distinct" in variants_prompt
        
        # Actions prompt should include SMART framework
        actions_prompt = calls[2][0][0]
        assert "SMART (Specific, Measurable, Achievable, Relevant, Time-bound)" in actions_prompt
        assert "ACTION GENERATION REQUIREMENTS:" in actions_prompt