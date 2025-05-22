import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
import json

from backend.ai.kernel_service import KernelService, kernel_service


class TestConversationAISkills:
    """Test conversation AI skills functionality."""
    
    @pytest_asyncio.fixture
    async def service(self):
        """Create kernel service instance for testing."""
        service = KernelService()
        # Ensure conversation skills are loaded
        return service
    
    def test_conversation_skills_loaded(self, service):
        """Test that conversation skills are properly loaded."""
        assert 'conversation' in service._skills_cache
        conversation_skills = service._skills_cache['conversation']
        assert 'GenerateResponse' in conversation_skills
        assert 'SummarizeConversation' in conversation_skills
        
        # Verify skill content is loaded
        assert len(conversation_skills['GenerateResponse']) > 0
        assert len(conversation_skills['SummarizeConversation']) > 0
    
    @pytest.mark.asyncio
    async def test_generate_response_analysis_support(self, service):
        """Test conversation response generation for analysis support."""
        variables = {
            'conversation_history': 'user: I need help with strategic analysis\nassistant: I can help with that',
            'user_message': 'How should I approach SWOT analysis for my startup?',
            'conversation_type': 'analysis_support',
            'summary': 'Discussion about strategic frameworks'
        }
        
        response = await service.invoke_semantic_function(
            'conversation', 'GenerateResponse', '', variables
        )
        
        assert isinstance(response, str)
        assert len(response) > 0
        assert 'SWOT' in response
        assert 'analysis' in response.lower()
        assert 'strategic' in response.lower()
        # Should mention StratOS Analysis tools
        assert 'Analysis tools' in response or 'SWOT Analysis' in response
    
    @pytest.mark.asyncio
    async def test_generate_response_canvas_collaboration(self, service):
        """Test conversation response generation for canvas collaboration."""
        variables = {
            'conversation_history': 'user: Tell me about strategic canvases\nassistant: Strategic canvases are visual tools',
            'user_message': 'How do I connect elements on the Strategic Canvas?',
            'conversation_type': 'canvas_collaboration',
            'summary': 'Discussion about strategic visualization'
        }
        
        response = await service.invoke_semantic_function(
            'conversation', 'GenerateResponse', '', variables
        )
        
        assert isinstance(response, str)
        assert len(response) > 0
        assert 'canvas' in response.lower() or 'Canvas' in response
        assert 'strategic' in response.lower()
        assert 'connection' in response.lower() or 'connect' in response.lower()
        # Should mention Strategic Canvas features
        assert 'Strategic Canvas' in response or 'visual' in response.lower()
    
    @pytest.mark.asyncio
    async def test_generate_response_strategic_planning(self, service):
        """Test conversation response generation for strategic planning."""
        variables = {
            'conversation_history': 'user: I need help with planning\nassistant: Strategic planning is important',
            'user_message': 'What frameworks should I use for strategic planning?',
            'conversation_type': 'strategic_planning',
            'summary': 'Planning discussion'
        }
        
        response = await service.invoke_semantic_function(
            'conversation', 'GenerateResponse', '', variables
        )
        
        assert isinstance(response, str)
        assert len(response) > 0
        assert 'strategic planning' in response.lower() or 'planning' in response.lower()
        assert 'framework' in response.lower()
        # Should mention planning concepts
        assert any(keyword in response.lower() for keyword in ['north star', 'goal', 'initiative', 'metric'])
    
    @pytest.mark.asyncio
    async def test_generate_response_ceo_log_discussion(self, service):
        """Test conversation response generation for CEO log discussion."""
        variables = {
            'conversation_history': 'user: I want to document decisions\nassistant: Documentation is crucial',
            'user_message': 'How should I structure my leadership insights?',
            'conversation_type': 'ceo_log_discussion',
            'summary': 'Leadership documentation discussion'
        }
        
        response = await service.invoke_semantic_function(
            'conversation', 'GenerateResponse', '', variables
        )
        
        assert isinstance(response, str)
        assert len(response) > 0
        assert 'leadership' in response.lower() or 'decision' in response.lower()
        assert 'log' in response.lower() or 'CEO' in response
        # Should mention CEO's Log features
        assert "CEO's Log" in response or 'insight' in response.lower()
    
    @pytest.mark.asyncio
    async def test_generate_response_general(self, service):
        """Test conversation response generation for general conversations."""
        variables = {
            'conversation_history': 'user: Hello\nassistant: Hi there',
            'user_message': 'Can you help me with business strategy?',
            'conversation_type': 'general',
            'summary': 'General business discussion'
        }
        
        response = await service.invoke_semantic_function(
            'conversation', 'GenerateResponse', '', variables
        )
        
        assert isinstance(response, str)
        assert len(response) > 0
        assert 'strategic' in response.lower() or 'strategy' in response.lower()
        assert 'business' in response.lower()
        # Should mention general capabilities
        assert any(keyword in response.lower() for keyword in ['analysis', 'planning', 'decision', 'leadership'])
    
    @pytest.mark.asyncio
    async def test_generate_response_with_context(self, service):
        """Test that responses incorporate conversation history context."""
        variables = {
            'conversation_history': 'user: We discussed SWOT analysis earlier\nassistant: Yes, we covered strengths and weaknesses\nuser: Now I want to explore TOWS',
            'user_message': 'How does TOWS build on our SWOT discussion?',
            'conversation_type': 'analysis_support',
            'summary': 'SWOT and TOWS analysis discussion'
        }
        
        response = await service.invoke_semantic_function(
            'conversation', 'GenerateResponse', '', variables
        )
        
        assert isinstance(response, str)
        assert len(response) > 0
        assert 'TOWS' in response or 'tows' in response.lower()
        # Should reference the earlier discussion
        # The contextual follow-up method should detect previous analysis discussion
    
    @pytest.mark.asyncio
    async def test_generate_response_empty_history(self, service):
        """Test response generation with minimal conversation history."""
        variables = {
            'conversation_history': '',
            'user_message': 'What is strategic planning?',
            'conversation_type': 'general',
            'summary': ''
        }
        
        response = await service.invoke_semantic_function(
            'conversation', 'GenerateResponse', '', variables
        )
        
        assert isinstance(response, str)
        assert len(response) > 0
        assert 'strategic planning' in response.lower() or 'planning' in response.lower()
    
    @pytest.mark.asyncio
    async def test_summarize_conversation_strategic_planning(self, service):
        """Test conversation summarization for strategic planning."""
        variables = {
            'conversation_history': '''user: I need help with strategic planning for market expansion
assistant: Strategic planning is crucial for expansion success
user: What frameworks should I use?
assistant: Consider SWOT analysis and market assessment frameworks
user: How do I prioritize different markets?
assistant: Use criteria like market size, competition, and strategic fit''',
            'conversation_type': 'strategic_planning',
            'conversation_title': 'Market Expansion Strategy'
        }
        
        summary = await service.invoke_semantic_function(
            'conversation', 'SummarizeConversation', '', variables
        )
        
        assert isinstance(summary, str)
        assert len(summary) > 0
        assert '## Conversation Summary' in summary
        assert 'Strategic Planning' in summary
        assert 'Main Topics' in summary
        assert 'Key Insights' in summary
        assert 'Strategic Context' in summary
    
    @pytest.mark.asyncio
    async def test_summarize_conversation_analysis_focus(self, service):
        """Test conversation summarization with analysis focus."""
        variables = {
            'conversation_history': '''user: Help me with SWOT analysis
assistant: SWOT helps identify strengths, weaknesses, opportunities, threats
user: How do I analyze my strengths?
assistant: Look at your core competencies and competitive advantages
user: What about market opportunities?
assistant: Analyze market trends, customer needs, and gaps in competition''',
            'conversation_type': 'analysis_support',
            'conversation_title': 'SWOT Analysis Discussion'
        }
        
        summary = await service.invoke_semantic_function(
            'conversation', 'SummarizeConversation', '', variables
        )
        
        assert isinstance(summary, str)
        assert len(summary) > 0
        assert 'Strategic Analysis' in summary
        assert 'SWOT' in summary or 'swot' in summary.lower()
    
    @pytest.mark.asyncio
    async def test_summarize_conversation_canvas_focus(self, service):
        """Test conversation summarization with canvas focus."""
        variables = {
            'conversation_history': '''user: How do I use the Strategic Canvas?
assistant: The Strategic Canvas helps visualize strategic relationships
user: What types of elements can I add?
assistant: You can add SWOT elements, goals, data snippets, and more
user: How do I connect elements?
assistant: Draw connections to show relationships and dependencies''',
            'conversation_type': 'canvas_collaboration',
            'conversation_title': 'Strategic Canvas Tutorial'
        }
        
        summary = await service.invoke_semantic_function(
            'conversation', 'SummarizeConversation', '', variables
        )
        
        assert isinstance(summary, str)
        assert len(summary) > 0
        assert 'Strategic Canvas' in summary or 'canvas' in summary.lower()
    
    @pytest.mark.asyncio
    async def test_summarize_conversation_minimal_data(self, service):
        """Test conversation summarization with minimal conversation data."""
        variables = {
            'conversation_history': 'user: Hello\nassistant: Hi, how can I help?',
            'conversation_type': 'general',
            'conversation_title': 'Brief Chat'
        }
        
        summary = await service.invoke_semantic_function(
            'conversation', 'SummarizeConversation', '', variables
        )
        
        assert isinstance(summary, str)
        assert len(summary) > 0
        assert '## Conversation Summary' in summary
        assert 'General Strategic Discussion' in summary or 'general' in summary.lower()
    
    def test_contextual_follow_up_analysis_context(self, service):
        """Test contextual follow-up generation with analysis context."""
        result = service._get_contextual_follow_up(
            "user: We discussed SWOT analysis earlier\nassistant: Yes, strengths and weaknesses",
            "planning"
        )
        
        assert "analysis discussion" in result.lower()
    
    def test_contextual_follow_up_canvas_context(self, service):
        """Test contextual follow-up generation with canvas context."""
        result = service._get_contextual_follow_up(
            "user: I'm working on the strategic canvas\nassistant: Great, let's continue",
            "analysis"
        )
        
        assert "canvas work" in result.lower()
    
    def test_contextual_follow_up_planning_context(self, service):
        """Test contextual follow-up generation with planning context."""
        result = service._get_contextual_follow_up(
            "user: We covered strategic planning\nassistant: Yes, goal setting is important",
            "canvas"
        )
        
        assert "planning considerations" in result.lower()
    
    def test_contextual_follow_up_same_topic(self, service):
        """Test contextual follow-up when topic matches history."""
        result = service._get_contextual_follow_up(
            "user: We discussed analysis\nassistant: Yes, SWOT is useful",
            "analysis"
        )
        
        assert "our strategic conversation" in result.lower()
    
    def test_contextual_follow_up_empty_history(self, service):
        """Test contextual follow-up with empty history."""
        result = service._get_contextual_follow_up("", "analysis")
        assert result == ""
        
        result = service._get_contextual_follow_up("short", "analysis")
        assert result == ""
    
    @pytest.mark.asyncio
    async def test_skill_error_handling(self, service):
        """Test skill error handling with invalid variables."""
        # Test with missing required variables
        variables = {}  # Empty variables
        
        response = await service.invoke_semantic_function(
            'conversation', 'GenerateResponse', '', variables
        )
        
        # Should handle gracefully and return a reasonable response
        assert isinstance(response, str)
        assert len(response) > 0
    
    @pytest.mark.asyncio
    async def test_nonexistent_skill(self, service):
        """Test calling non-existent conversation skill."""
        variables = {'test': 'value'}
        
        response = await service.invoke_semantic_function(
            'conversation', 'NonExistentFunction', '', variables
        )
        
        # Should return error message
        assert isinstance(response, str)
        assert 'not available' in response.lower() or 'error' in response.lower()


class TestConversationSkillIntegration:
    """Test conversation skill integration with the service layer."""
    
    @pytest.mark.asyncio
    async def test_kernel_service_singleton(self):
        """Test that kernel_service singleton is accessible."""
        from backend.ai.kernel_service import kernel_service
        assert isinstance(kernel_service, KernelService)
        assert 'conversation' in kernel_service._skills_cache
    
    @pytest.mark.asyncio
    async def test_conversation_service_integration(self):
        """Test integration between conversation service and AI skills."""
        # This would typically be tested in the service tests, but we can verify
        # that the kernel service can be called with appropriate parameters
        
        variables = {
            'conversation_history': 'user: test\nassistant: response',
            'user_message': 'How can you help me?',
            'conversation_type': 'general',
            'summary': 'Test conversation'
        }
        
        # Verify the kernel service can handle conversation skill calls
        response = await kernel_service.invoke_semantic_function(
            'conversation', 'GenerateResponse', '', variables
        )
        
        assert isinstance(response, str)
        assert len(response) > 0
        assert 'strategic' in response.lower()


class TestAIResponseQuality:
    """Test the quality and appropriateness of AI responses."""
    
    @pytest.mark.asyncio
    async def test_response_mentions_stratos_features(self, service=kernel_service):
        """Test that responses appropriately mention StratOS features."""
        test_cases = [
            {
                'variables': {
                    'user_message': 'How do I do SWOT analysis?',
                    'conversation_type': 'analysis_support',
                    'conversation_history': '',
                    'summary': ''
                },
                'expected_mentions': ['SWOT Analysis', 'Analysis tools', 'TOWS']
            },
            {
                'variables': {
                    'user_message': 'Tell me about strategic visualization',
                    'conversation_type': 'canvas_collaboration',
                    'conversation_history': '',
                    'summary': ''
                },
                'expected_mentions': ['Strategic Canvas', 'visual', 'elements']
            },
            {
                'variables': {
                    'user_message': 'How do I document decisions?',
                    'conversation_type': 'ceo_log_discussion',
                    'conversation_history': '',
                    'summary': ''
                },
                'expected_mentions': ["CEO's Log", 'decision', 'insight']
            }
        ]
        
        for test_case in test_cases:
            response = await service.invoke_semantic_function(
                'conversation', 'GenerateResponse', '', test_case['variables']
            )
            
            # Check that response mentions relevant features
            response_lower = response.lower()
            mentions_found = []
            for mention in test_case['expected_mentions']:
                if mention.lower() in response_lower or mention in response:
                    mentions_found.append(mention)
            
            assert len(mentions_found) > 0, f"Response should mention at least one of {test_case['expected_mentions']} but mentions were: {mentions_found}"
    
    @pytest.mark.asyncio
    async def test_response_appropriate_length(self, service=kernel_service):
        """Test that responses are appropriate length (not too short or too long)."""
        variables = {
            'user_message': 'What is strategic planning?',
            'conversation_type': 'general',
            'conversation_history': '',
            'summary': ''
        }
        
        response = await service.invoke_semantic_function(
            'conversation', 'GenerateResponse', '', variables
        )
        
        # Response should be substantial but not excessive
        assert 100 <= len(response) <= 2000, f"Response length {len(response)} should be between 100-2000 characters"
        
        # Should contain multiple sentences
        sentence_count = response.count('.') + response.count('?') + response.count('!')
        assert sentence_count >= 2, "Response should contain multiple sentences"
    
    @pytest.mark.asyncio
    async def test_summary_structure(self, service=kernel_service):
        """Test that conversation summaries follow expected structure."""
        variables = {
            'conversation_history': '''user: I need strategic help
assistant: I can help with strategic planning
user: What about SWOT analysis?
assistant: SWOT is a great framework for analysis''',
            'conversation_type': 'analysis_support',
            'conversation_title': 'Strategic Help Session'
        }
        
        summary = await service.invoke_semantic_function(
            'conversation', 'SummarizeConversation', '', variables
        )
        
        # Check summary structure
        assert '## Conversation Summary' in summary
        assert '**Main Topics**:' in summary
        assert '**Key Insights**:' in summary
        assert '**Strategic Context**:' in summary
        
        # Should be concise but informative
        assert 50 <= len(summary) <= 1000, f"Summary length {len(summary)} should be between 50-1000 characters"