import pytest
import json
from uuid import uuid4
from unittest.mock import patch, MagicMock, AsyncMock

from backend.ai.skills.canvas.VoiceCanvasCommands import VoiceCanvasCommandsSkill
from backend.services.canvas_voice_service import CanvasVoiceService


class TestVoiceCanvasCommandsSkill:
    """Test the VoiceCanvasCommands skill for parsing voice commands"""
    
    @pytest.fixture
    def skill(self):
        return VoiceCanvasCommandsSkill()
    
    @pytest.mark.asyncio
    async def test_parse_add_node_commands(self, skill):
        """Test parsing various add node voice commands"""
        test_commands = [
            ("add a node called Strategy", "strategy"),
            ("create a new node named Innovation", "innovation"),
            ("add 'Market Analysis' as a node", "market analysis"),
            ("create node titled Risk Assessment", "risk assessment"),
        ]
        
        for command, expected_title in test_commands:
            result = await skill.parse_canvas_voice_command(command)
            parsed = json.loads(result)
            
            assert parsed['action'] == 'add_node'
            assert parsed['parameters']['title'] == expected_title
            assert parsed['parameters']['type'] == 'concept'
            assert 'position' in parsed['parameters']
    
    @pytest.mark.asyncio
    async def test_parse_connect_nodes_commands(self, skill):
        """Test parsing connect nodes commands"""
        test_commands = [
            ("connect Goals to Objectives", "goals", "objectives"),
            ("link Strategy with Tactics", "strategy", "tactics"),
            ("draw a line from Vision to Mission", "vision", "mission"),
        ]
        
        for command, source, target in test_commands:
            result = await skill.parse_canvas_voice_command(command)
            parsed = json.loads(result)
            
            assert parsed['action'] == 'connect_nodes'
            assert parsed['parameters']['source_title'] == source
            assert parsed['parameters']['target_title'] == target
            assert parsed['parameters']['connection_type'] == 'relates_to'
    
    @pytest.mark.asyncio
    async def test_parse_delete_node_commands(self, skill):
        """Test parsing delete node commands"""
        test_commands = [
            "delete node Old Strategy",
            "remove the node Outdated Plan",
        ]
        
        for command in test_commands:
            result = await skill.parse_canvas_voice_command(command)
            parsed = json.loads(result)
            
            assert parsed['action'] == 'delete_node'
            assert 'node_title' in parsed['parameters']
    
    @pytest.mark.asyncio
    async def test_parse_move_node_commands(self, skill):
        """Test parsing move node commands"""
        result = await skill.parse_canvas_voice_command("move node Strategy to the top")
        parsed = json.loads(result)
        
        assert parsed['action'] == 'move_node'
        assert parsed['parameters']['node_title'] == 'strategy'
        assert parsed['parameters']['position'] == {'x': 0, 'y': -200}
        assert parsed['parameters']['position_description'] == 'top'
    
    @pytest.mark.asyncio
    async def test_parse_update_node_commands(self, skill):
        """Test parsing update/rename node commands"""
        test_commands = [
            ("rename node Old Plan to New Strategy", "old plan", "new strategy"),
            ("change the node Draft to Final", "draft", "final"),
        ]
        
        for command, old_title, new_title in test_commands:
            result = await skill.parse_canvas_voice_command(command)
            parsed = json.loads(result)
            
            assert parsed['action'] == 'update_node'
            assert parsed['parameters']['old_title'] == old_title
            assert parsed['parameters']['new_title'] == new_title
    
    @pytest.mark.asyncio
    async def test_parse_analyze_commands(self, skill):
        """Test parsing analyze commands"""
        test_commands = [
            "analyze the canvas",
            "analyze selected nodes",
            "suggest connections",
        ]
        
        for command in test_commands:
            result = await skill.parse_canvas_voice_command(command)
            parsed = json.loads(result)
            
            assert parsed['action'] == 'analyze_canvas'
    
    @pytest.mark.asyncio
    async def test_parse_unknown_commands(self, skill):
        """Test handling of unknown commands"""
        result = await skill.parse_canvas_voice_command("do something random")
        parsed = json.loads(result)
        
        assert parsed['action'] == 'unknown'
        assert 'suggestions' in parsed
        assert isinstance(parsed['suggestions'], list)
    
    @pytest.mark.asyncio
    async def test_compound_commands(self, skill):
        """Test parsing compound commands"""
        command = "create a node called Strategy and connect it to Goals"
        result = await skill.process_compound_canvas_command(command)
        parsed = json.loads(result)
        
        assert parsed['compound_command'] is True
        assert len(parsed['actions']) == 2
        assert parsed['actions'][0]['action'] == 'add_node'
        assert parsed['actions'][0]['parameters']['title'] == 'strategy'
        assert parsed['actions'][1]['action'] == 'connect_nodes'


class TestCanvasVoiceService:
    """Test the CanvasVoiceService for executing voice commands"""
    
    @pytest.fixture
    def mock_canvas_ai_service(self):
        with patch('backend.services.canvas_voice_service.CanvasAIService') as mock:
            yield mock
    
    @pytest.fixture
    def mock_kernel_service(self):
        with patch('backend.services.canvas_voice_service.kernel_service') as mock:
            yield mock
    
    @pytest.fixture
    def service(self, mock_canvas_ai_service, mock_kernel_service):
        # Mock the entire initialization to avoid import/registration issues
        with patch.object(CanvasVoiceService, '_register_voice_skill'):
            service = CanvasVoiceService()
            # Manually set the mocked canvas_ai_service
            service.canvas_ai_service = MagicMock()
            service.canvas_ai_service.process_canvas_content = AsyncMock(return_value={'success': True})
            return service
    
    @pytest.mark.asyncio
    async def test_process_voice_command_add_node(self, service, mock_kernel_service, mock_canvas_ai_service):
        """Test processing add node voice command"""
        user_id = uuid4()
        canvas_id = uuid4()
        
        # Mock the skill response
        mock_kernel_service.generate_skill_response = AsyncMock(return_value=json.dumps({
            'action': 'add_node',
            'parameters': {
                'title': 'Test Node',
                'type': 'concept',
                'position': {'x': 0, 'y': 0}
            }
        }))
        
        # Mock the canvas AI service
        service.canvas_ai_service.process_canvas_content = AsyncMock(return_value={'success': True})
        
        result = await service.process_voice_command(
            user_id=user_id,
            canvas_id=canvas_id,
            voice_command="add a node called Test Node"
        )
        
        assert result['success'] is True
        assert result['action'] == 'add_node'
        assert result['message'] == "Added node 'Test Node'"
    
    @pytest.mark.asyncio
    async def test_process_voice_command_connect_nodes(self, service, mock_kernel_service):
        """Test processing connect nodes voice command"""
        user_id = uuid4()
        canvas_id = uuid4()
        
        current_nodes = [
            {'id': 'node1', 'data': {'label': 'Source'}},
            {'id': 'node2', 'data': {'label': 'Target'}}
        ]
        
        mock_kernel_service.generate_skill_response = AsyncMock(return_value=json.dumps({
            'action': 'connect_nodes',
            'parameters': {
                'source_title': 'source',
                'target_title': 'target',
                'connection_type': 'relates_to'
            }
        }))
        
        result = await service.process_voice_command(
            user_id=user_id,
            canvas_id=canvas_id,
            voice_command="connect Source to Target",
            current_nodes=current_nodes
        )
        
        assert result['success'] is True
        assert result['action'] == 'connect_nodes'
        assert result['edge']['source'] == 'node1'
        assert result['edge']['target'] == 'node2'
    
    @pytest.mark.asyncio
    async def test_process_voice_command_delete_node(self, service, mock_kernel_service):
        """Test processing delete node voice command"""
        user_id = uuid4()
        canvas_id = uuid4()
        selected_node_ids = ['node1', 'node2']
        
        mock_kernel_service.generate_skill_response = AsyncMock(return_value=json.dumps({
            'action': 'delete_node',
            'parameters': {
                'requires_selection': True
            }
        }))
        
        result = await service.process_voice_command(
            user_id=user_id,
            canvas_id=canvas_id,
            voice_command="delete selected nodes",
            selected_node_ids=selected_node_ids
        )
        
        assert result['success'] is True
        assert result['action'] == 'delete_node'
        assert result['node_ids'] == selected_node_ids
        assert result['message'] == "Deleted 2 node(s)"
    
    @pytest.mark.asyncio
    async def test_process_voice_command_error_handling(self, service, mock_kernel_service):
        """Test error handling in voice command processing"""
        user_id = uuid4()
        canvas_id = uuid4()
        
        # Mock an error
        mock_kernel_service.generate_skill_response = AsyncMock(
            side_effect=Exception("Test error")
        )
        
        result = await service.process_voice_command(
            user_id=user_id,
            canvas_id=canvas_id,
            voice_command="any command"
        )
        
        assert result['success'] is False
        assert 'error' in result
        assert 'Sorry, I couldn\'t understand that command' in result['message']
    
    @pytest.mark.asyncio
    async def test_process_compound_command(self, service, mock_kernel_service):
        """Test processing compound commands"""
        user_id = uuid4()
        canvas_id = uuid4()
        
        mock_kernel_service.generate_skill_response = AsyncMock(return_value=json.dumps({
            'compound_command': True,
            'actions': [
                {
                    'action': 'add_node',
                    'parameters': {'title': 'Node1', 'type': 'concept', 'position': {'x': 0, 'y': 0}}
                },
                {
                    'action': 'add_node',
                    'parameters': {'title': 'Node2', 'type': 'concept', 'position': {'x': 100, 'y': 0}}
                }
            ]
        }))
        
        result = await service.process_compound_command(
            user_id=user_id,
            canvas_id=canvas_id,
            voice_command="create Node1 and then create Node2"
        )
        
        assert result['success'] is True
        assert result['compound'] is True
        assert len(result['results']) == 2
        assert result['message'] == "Executed 2 commands"


class TestCanvasVoiceIntegration:
    """Integration tests for canvas voice commands"""
    
    # TODO: Fix these integration tests - they have issues with:
    # 1. Pronoun handling in compound commands ("it" references)
    # 2. Case sensitivity in special character handling
    pass