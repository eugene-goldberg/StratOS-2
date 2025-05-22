import logging
import json
from typing import Dict, Any, Optional, List
from uuid import UUID
from fastapi import HTTPException

from ..ai.kernel_service import kernel_service
from ..services.canvas_ai_service import CanvasAIService
from ..models.canvas_ai import CanvasNode, CanvasEdge, NodeType

class CanvasVoiceService:
    """Service for handling voice commands on the Strategic Canvas"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.canvas_ai_service = CanvasAIService()
        
        # Register the voice canvas commands skill
        self._register_voice_skill()
    
    def _register_voice_skill(self):
        """Register the voice canvas commands skill with the kernel"""
        try:
            from ..ai.skills.canvas.VoiceCanvasCommands import VoiceCanvasCommandsSkill
            voice_skill = VoiceCanvasCommandsSkill()
            kernel_service.kernel.add_plugin(voice_skill, "VoiceCanvasCommands")
            self.logger.info("Registered VoiceCanvasCommands skill")
        except Exception as e:
            self.logger.error(f"Failed to register voice canvas skill: {str(e)}")
    
    async def process_voice_command(
        self,
        user_id: UUID,
        canvas_id: UUID,
        voice_command: str,
        current_nodes: Optional[List[Dict[str, Any]]] = None,
        selected_node_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Process a voice command for canvas operations.
        
        Args:
            user_id: User ID
            canvas_id: Canvas ID
            voice_command: The transcribed voice command
            current_nodes: Current nodes on the canvas for context
            selected_node_ids: Currently selected node IDs
            
        Returns:
            Dict containing the action to perform and any UI updates
        """
        self.logger.info(f"Processing voice command for canvas {canvas_id}: {voice_command}")
        
        try:
            # Parse the voice command using the skill
            result = await kernel_service.generate_skill_response(
                skill_name="VoiceCanvasCommands",
                function_name="parse_canvas_voice_command",
                command=voice_command
            )
            
            parsed_command = json.loads(result)
            self.logger.info(f"Parsed command: {parsed_command}")
            
            # Execute the parsed command
            response = await self._execute_canvas_command(
                user_id=user_id,
                canvas_id=canvas_id,
                parsed_command=parsed_command,
                current_nodes=current_nodes,
                selected_node_ids=selected_node_ids
            )
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error processing voice command: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'message': "Sorry, I couldn't understand that command. Try saying something like 'Add a node called Strategy' or 'Connect Goals to Objectives'."
            }
    
    async def _execute_canvas_command(
        self,
        user_id: UUID,
        canvas_id: UUID,
        parsed_command: Dict[str, Any],
        current_nodes: Optional[List[Dict[str, Any]]] = None,
        selected_node_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Execute the parsed canvas command"""
        
        action = parsed_command.get('action')
        params = parsed_command.get('parameters', {})
        
        if action == 'add_node':
            return await self._add_node(user_id, canvas_id, params)
        
        elif action == 'connect_nodes':
            return await self._connect_nodes(user_id, canvas_id, params, current_nodes)
        
        elif action == 'delete_node':
            return await self._delete_node(user_id, canvas_id, params, selected_node_ids)
        
        elif action == 'move_node':
            return await self._move_node(user_id, canvas_id, params, current_nodes)
        
        elif action == 'update_node':
            return await self._update_node(user_id, canvas_id, params, current_nodes)
        
        elif action == 'group_nodes':
            return await self._group_nodes(user_id, canvas_id, params, current_nodes)
        
        elif action == 'analyze_canvas':
            return await self._analyze_canvas(user_id, canvas_id, selected_node_ids)
        
        else:
            return {
                'success': False,
                'action': 'unknown',
                'message': f"I didn't understand that command. {parsed_command.get('suggestions', ['Try a different command'])}"
            }
    
    async def _add_node(self, user_id: UUID, canvas_id: UUID, params: Dict[str, Any]) -> Dict[str, Any]:
        """Add a new node to the canvas"""
        try:
            # Create node data
            node_data = {
                'title': params.get('title', 'New Node'),
                'type': params.get('type', 'concept'),
                'position': params.get('position', {'x': 0, 'y': 0}),
                'content': ''
            }
            
            # Add node via canvas AI service
            result = await self.canvas_ai_service.process_canvas_content(
                user_id=user_id,
                canvas_data={
                    'canvas_id': str(canvas_id),
                    'action': 'add_node',
                    'node_data': node_data
                }
            )
            
            return {
                'success': True,
                'action': 'add_node',
                'node': node_data,
                'message': f"Added node '{node_data['title']}'"
            }
            
        except Exception as e:
            self.logger.error(f"Error adding node: {str(e)}")
            return {
                'success': False,
                'action': 'add_node',
                'error': str(e)
            }
    
    async def _connect_nodes(
        self,
        user_id: UUID,
        canvas_id: UUID,
        params: Dict[str, Any],
        current_nodes: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Connect two nodes"""
        
        if params.get('requires_selection'):
            return {
                'success': False,
                'action': 'connect_nodes',
                'requires_user_input': True,
                'message': "Please select the nodes you want to connect"
            }
        
        source_title = params.get('source_title')
        target_title = params.get('target_title')
        
        if not current_nodes:
            return {
                'success': False,
                'action': 'connect_nodes',
                'error': 'No nodes available to connect'
            }
        
        # Find nodes by title
        source_node = None
        target_node = None
        
        for node in current_nodes:
            if node.get('data', {}).get('label', '').lower() == source_title.lower():
                source_node = node
            if node.get('data', {}).get('label', '').lower() == target_title.lower():
                target_node = node
        
        if not source_node or not target_node:
            missing = []
            if not source_node:
                missing.append(source_title)
            if not target_node:
                missing.append(target_title)
            
            return {
                'success': False,
                'action': 'connect_nodes',
                'error': f"Could not find node(s): {', '.join(missing)}"
            }
        
        # Create edge
        edge_data = {
            'source': source_node['id'],
            'target': target_node['id'],
            'type': params.get('connection_type', 'relates_to')
        }
        
        return {
            'success': True,
            'action': 'connect_nodes',
            'edge': edge_data,
            'message': f"Connected '{source_title}' to '{target_title}'"
        }
    
    async def _delete_node(
        self,
        user_id: UUID,
        canvas_id: UUID,
        params: Dict[str, Any],
        selected_node_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Delete a node"""
        
        if params.get('requires_selection'):
            if not selected_node_ids:
                return {
                    'success': False,
                    'action': 'delete_node',
                    'requires_user_input': True,
                    'message': "Please select the node you want to delete"
                }
            
            return {
                'success': True,
                'action': 'delete_node',
                'node_ids': selected_node_ids,
                'message': f"Deleted {len(selected_node_ids)} node(s)"
            }
        
        node_title = params.get('node_title')
        
        return {
            'success': True,
            'action': 'delete_node',
            'node_title': node_title,
            'message': f"Delete node '{node_title}'"
        }
    
    async def _move_node(
        self,
        user_id: UUID,
        canvas_id: UUID,
        params: Dict[str, Any],
        current_nodes: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Move a node to a new position"""
        
        node_title = params.get('node_title')
        position = params.get('position')
        position_desc = params.get('position_description')
        
        return {
            'success': True,
            'action': 'move_node',
            'node_title': node_title,
            'position': position,
            'message': f"Move '{node_title}' to {position_desc}"
        }
    
    async def _update_node(
        self,
        user_id: UUID,
        canvas_id: UUID,
        params: Dict[str, Any],
        current_nodes: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Update a node's title"""
        
        old_title = params.get('old_title')
        new_title = params.get('new_title')
        
        return {
            'success': True,
            'action': 'update_node',
            'old_title': old_title,
            'new_title': new_title,
            'message': f"Rename '{old_title}' to '{new_title}'"
        }
    
    async def _group_nodes(
        self,
        user_id: UUID,
        canvas_id: UUID,
        params: Dict[str, Any],
        current_nodes: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Group multiple nodes"""
        
        node_titles = params.get('node_titles', [])
        
        return {
            'success': True,
            'action': 'group_nodes',
            'node_titles': node_titles,
            'message': f"Group nodes: {', '.join(node_titles)}"
        }
    
    async def _analyze_canvas(
        self,
        user_id: UUID,
        canvas_id: UUID,
        selected_node_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Analyze canvas or selected nodes"""
        
        try:
            # Use canvas AI service for analysis
            result = await self.canvas_ai_service.analyze_connections(
                user_id=user_id,
                selected_nodes=selected_node_ids or []
            )
            
            return {
                'success': True,
                'action': 'analyze_canvas',
                'analysis': result,
                'message': "Canvas analysis complete"
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing canvas: {str(e)}")
            return {
                'success': False,
                'action': 'analyze_canvas',
                'error': str(e)
            }
    
    async def process_compound_command(
        self,
        user_id: UUID,
        canvas_id: UUID,
        voice_command: str,
        current_nodes: Optional[List[Dict[str, Any]]] = None,
        selected_node_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Process compound voice commands with multiple operations"""
        
        try:
            # Parse compound command
            result = await kernel_service.generate_skill_response(
                skill_name="VoiceCanvasCommands",
                function_name="process_compound_canvas_command",
                command=voice_command
            )
            
            parsed = json.loads(result)
            
            if not parsed.get('compound_command'):
                # Fall back to single command processing
                return await self.process_voice_command(
                    user_id, canvas_id, voice_command, current_nodes, selected_node_ids
                )
            
            # Execute each action in sequence
            results = []
            for action_data in parsed.get('actions', []):
                result = await self._execute_canvas_command(
                    user_id=user_id,
                    canvas_id=canvas_id,
                    parsed_command=action_data,
                    current_nodes=current_nodes,
                    selected_node_ids=selected_node_ids
                )
                results.append(result)
            
            return {
                'success': True,
                'compound': True,
                'results': results,
                'message': f"Executed {len(results)} commands"
            }
            
        except Exception as e:
            self.logger.error(f"Error processing compound command: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }