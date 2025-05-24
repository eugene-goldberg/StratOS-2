import logging
import json
import re
from typing import Optional, Dict, Any, List
from uuid import UUID, uuid4
import semantic_kernel as sk
from semantic_kernel.functions import kernel_function

class VoiceCanvasCommandsSkill:
    """
    A Semantic Kernel skill for processing voice commands on the Strategic Canvas.
    Parses natural language commands and converts them to canvas operations.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Command patterns for different canvas operations
        self.command_patterns = {
            'add_node': [
                r"add (?:a )?(?:new )?node (?:titled|called|named) ['\"]?(.+?)['\"]?$",
                r"create (?:a )?(?:new )?node (?:titled|called|named) ['\"]?(.+?)['\"]?$",
                r"add ['\"]?(.+?)['\"]? (?:as a )?node",
                r"create ['\"]?(.+?)['\"]? (?:as a )?node"
            ],
            'connect_nodes': [
                r"connect (.+?) (?:to|with|and) (.+?)$",
                r"link (.+?) (?:to|with|and) (.+?)$",
                r"draw (?:a )?(?:line|connection|link) (?:from|between) (.+?) (?:to|and) (.+?)$"
            ],
            'delete_node': [
                r"delete (?:the )?node ['\"]?(.+?)['\"]?$",
                r"remove (?:the )?node ['\"]?(.+?)['\"]?$"
            ],
            'move_node': [
                r"move (?:the )?node ['\"]?(.+?)['\"]? to (?:the )?(.+)$",
                r"place (?:the )?node ['\"]?(.+?)['\"]? (?:at|on|to) (?:the )?(.+)$"
            ],
            'update_node': [
                r"rename (?:the )?node ['\"]?(.+?)['\"]? to ['\"]?(.+?)['\"]?$",
                r"change (?:the )?node ['\"]?(.+?)['\"]? to ['\"]?(.+?)['\"]?$"
            ],
            'group_nodes': [
                r"group (?:nodes )?(.+)$",
                r"cluster (?:nodes )?(.+)$"
            ],
            'analyze': [
                r"analyze (?:the )?(?:selected )?nodes?$",
                r"what (?:are )?(?:the )?connections? between (?:these )?nodes?$",
                r"suggest connections?$"
            ]
        }
        
        # Position descriptors
        self.position_map = {
            'top': {'x': 0, 'y': -200},
            'bottom': {'x': 0, 'y': 200},
            'left': {'x': -300, 'y': 0},
            'right': {'x': 300, 'y': 0},
            'center': {'x': 0, 'y': 0},
            'top left': {'x': -300, 'y': -200},
            'top right': {'x': 300, 'y': -200},
            'bottom left': {'x': -300, 'y': 200},
            'bottom right': {'x': 300, 'y': 200}
        }

    @kernel_function(
        description="Parses voice commands for canvas operations and returns structured action data",
        name="parse_canvas_voice_command"
    )
    async def parse_canvas_voice_command(self, command: str) -> str:
        """
        Parses natural language voice commands for canvas operations.
        
        :param command: The voice command to parse
        :return: JSON string containing the parsed action and parameters
        """
        self.logger.info(f"Parsing canvas voice command: {command}")
        
        # Clean and normalize the command
        command = command.lower().strip()
        command = re.sub(r'\s+', ' ', command)  # Normalize whitespace
        
        # Try to match command patterns
        for action_type, patterns in self.command_patterns.items():
            for pattern in patterns:
                match = re.match(pattern, command, re.IGNORECASE)
                if match:
                    return await self._handle_matched_command(action_type, match, command)
        
        # If no pattern matches, try to infer intent
        return await self._infer_command_intent(command)
    
    async def _handle_matched_command(self, action_type: str, match: re.Match, original_command: str) -> str:
        """Handle a matched command pattern"""
        
        if action_type == 'add_node':
            title = match.group(1).strip()
            return json.dumps({
                'action': 'add_node',
                'parameters': {
                    'title': title,
                    'type': 'concept',  # Default type
                    'position': self._get_smart_position()
                },
                'original_command': original_command
            })
        
        elif action_type == 'connect_nodes':
            source = match.group(1).strip()
            target = match.group(2).strip()
            return json.dumps({
                'action': 'connect_nodes',
                'parameters': {
                    'source_title': source,
                    'target_title': target,
                    'connection_type': 'relates_to'  # Default connection type
                },
                'original_command': original_command
            })
        
        elif action_type == 'delete_node':
            node_title = match.group(1).strip()
            return json.dumps({
                'action': 'delete_node',
                'parameters': {
                    'node_title': node_title
                },
                'original_command': original_command
            })
        
        elif action_type == 'move_node':
            node_title = match.group(1).strip()
            position_desc = match.group(2).strip()
            position = self.position_map.get(position_desc, {'x': 0, 'y': 0})
            return json.dumps({
                'action': 'move_node',
                'parameters': {
                    'node_title': node_title,
                    'position': position,
                    'position_description': position_desc
                },
                'original_command': original_command
            })
        
        elif action_type == 'update_node':
            old_title = match.group(1).strip()
            new_title = match.group(2).strip()
            return json.dumps({
                'action': 'update_node',
                'parameters': {
                    'old_title': old_title,
                    'new_title': new_title
                },
                'original_command': original_command
            })
        
        elif action_type == 'group_nodes':
            nodes_desc = match.group(1).strip()
            node_titles = [n.strip() for n in re.split(r',|and', nodes_desc)]
            return json.dumps({
                'action': 'group_nodes',
                'parameters': {
                    'node_titles': node_titles
                },
                'original_command': original_command
            })
        
        elif action_type == 'analyze':
            return json.dumps({
                'action': 'analyze_canvas',
                'parameters': {},
                'original_command': original_command
            })
        
        return json.dumps({
            'action': 'unknown',
            'original_command': original_command,
            'error': 'Command pattern matched but handler not implemented'
        })
    
    async def _infer_command_intent(self, command: str) -> str:
        """Try to infer the intent when no pattern matches"""
        
        # Simple keyword-based inference
        if any(word in command for word in ['add', 'create', 'new']):
            # Extract quoted text or last few words as title
            quoted = re.findall(r"['\"](.+?)['\"]", command)
            if quoted:
                title = quoted[0]
            else:
                words = command.split()
                title = ' '.join(words[-3:]) if len(words) > 3 else command
            
            return json.dumps({
                'action': 'add_node',
                'parameters': {
                    'title': title,
                    'type': 'concept'
                },
                'original_command': command,
                'inferred': True
            })
        
        elif any(word in command for word in ['connect', 'link', 'relate']):
            return json.dumps({
                'action': 'connect_nodes',
                'parameters': {
                    'requires_selection': True
                },
                'original_command': command,
                'inferred': True
            })
        
        elif any(word in command for word in ['delete', 'remove']):
            return json.dumps({
                'action': 'delete_node',
                'parameters': {
                    'requires_selection': True
                },
                'original_command': command,
                'inferred': True
            })
        
        elif any(word in command for word in ['analyze', 'suggest', 'help']):
            return json.dumps({
                'action': 'analyze_canvas',
                'parameters': {},
                'original_command': command,
                'inferred': True
            })
        
        # Default: couldn't understand the command
        return json.dumps({
            'action': 'unknown',
            'original_command': command,
            'suggestions': [
                'Add a node titled "Example"',
                'Connect Node A to Node B',
                'Delete node "Old Idea"',
                'Analyze selected nodes'
            ]
        })
    
    def _get_smart_position(self) -> Dict[str, int]:
        """Get a smart position for new nodes to avoid overlap"""
        # In a real implementation, this would check existing node positions
        # For now, return a slightly randomized position
        import random
        return {
            'x': random.randint(-100, 100),
            'y': random.randint(-100, 100)
        }

    @kernel_function(
        description="Processes a complex voice command that may contain multiple operations",
        name="process_compound_canvas_command"
    )
    async def process_compound_canvas_command(self, command: str) -> str:
        """
        Processes compound commands that contain multiple operations.
        E.g., "Create a node called Strategy and connect it to Goals"
        
        :param command: The compound voice command
        :return: JSON string containing multiple parsed actions
        """
        self.logger.info(f"Processing compound canvas command: {command}")
        
        # Split by common conjunctions
        command_parts = re.split(r'\s+and\s+then\s+|\s+then\s+|\s+and\s+', command, flags=re.IGNORECASE)
        
        actions = []
        for part in command_parts:
            part = part.strip()
            if part:
                result = await self.parse_canvas_voice_command(part)
                parsed = json.loads(result)
                if parsed.get('action') != 'unknown':
                    actions.append(parsed)
        
        return json.dumps({
            'compound_command': True,
            'actions': actions,
            'original_command': command
        })