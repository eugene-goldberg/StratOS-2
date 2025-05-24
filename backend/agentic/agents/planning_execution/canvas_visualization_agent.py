"""Canvas Visualization Agent

Manages strategic canvas operations, visualization, and voice-enabled interactions.
"""

import asyncio
import json
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from uuid import uuid4

from semantic_kernel import Kernel
from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.contents import ChatMessageContent, AuthorRole

from common.base_agent import BaseStratosAgent
from .plugins.canvas_plugin import CanvasPlugin


class CanvasVisualizationAgent(BaseStratosAgent):
    """Agent responsible for strategic canvas visualization and interaction"""
    
    def __init__(self):
        super().__init__(
            name="Canvas Visualization Agent",
            description="Manages strategic canvas visualization, layout, and voice interactions",
            model="gpt-4o"  # Use GPT-4o for multimodal capabilities (future voice)
        )
        
        # Initialize canvas plugin
        self.canvas_plugin = CanvasPlugin()
        self.kernel.add_plugin(self.canvas_plugin, "CanvasPlugin")
        
        # Node types and relationships
        self.node_types = {
            "vision": {"color": "#1976d2", "shape": "rectangle", "category": "strategic"},
            "goal": {"color": "#388e3c", "shape": "rectangle", "category": "strategic"},
            "initiative": {"color": "#f57c00", "shape": "rectangle", "category": "execution"},
            "action": {"color": "#7b1fa2", "shape": "ellipse", "category": "execution"},
            "risk": {"color": "#d32f2f", "shape": "diamond", "category": "analysis"},
            "opportunity": {"color": "#0288d1", "shape": "diamond", "category": "analysis"},
            "insight": {"color": "#616161", "shape": "ellipse", "category": "intelligence"}
        }
        
        # Voice command patterns
        self.voice_commands = {
            "create": ["add", "create", "new", "make"],
            "connect": ["connect", "link", "relate", "associate"],
            "move": ["move", "relocate", "position", "place"],
            "delete": ["delete", "remove", "clear", "erase"],
            "show": ["show", "display", "highlight", "focus"],
            "analyze": ["analyze", "examine", "investigate", "explore"]
        }
        
    async def _create_canvas_agent(self) -> ChatCompletionAgent:
        """Create the canvas visualization agent with specific instructions"""
        
        instructions = """You are a strategic canvas visualization expert specializing in visual thinking and diagramming.

Your capabilities include:
1. **Canvas Management**: Create and manage strategic canvas diagrams
2. **Node Operations**: Add, update, position, and style nodes
3. **Relationship Mapping**: Create meaningful connections between elements
4. **Layout Optimization**: Arrange elements for clarity and insight
5. **Voice Interaction**: Process natural language commands for canvas manipulation
6. **Visual Analysis**: Identify patterns and insights in visual structures

When working with canvas:
- Maintain visual clarity and hierarchy
- Use consistent styling and positioning
- Create meaningful relationships
- Optimize for understanding
- Support multiple view perspectives
- Enable collaborative editing

Canvas elements:
- Nodes: Vision, Goals, Initiatives, Actions, Risks, Opportunities, Insights
- Edges: Dependencies, relationships, flows, impacts
- Clusters: Grouped related elements
- Layers: Strategic, tactical, operational views

Voice command processing:
- Parse natural language into canvas operations
- Provide clear feedback on actions
- Support compound commands
- Handle ambiguity gracefully

Available functions:
- StructureText: Convert text into canvas nodes
- CreateNode: Add new elements to canvas
- ConnectNodes: Establish relationships
- OptimizeLayout: Arrange for clarity
- AnalyzeCanvas: Find patterns and insights
- ProcessVoiceCommand: Handle voice input"""

        return ChatCompletionAgent(
            service_id="canvas_agent",
            kernel=self.kernel,
            name="CanvasExpert",
            instructions=instructions
        )
        
    async def process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process canvas visualization requests"""
        
        try:
            query = request.get("query", "")
            context = request.get("context", {})
            user_id = request.get("user_id")
            
            # Create canvas agent
            agent = await self._create_canvas_agent()
            
            # Determine request type
            request_type = self._determine_request_type(query, context)
            
            if request_type == "structure_text":
                return await self._structure_text(agent, query, context, user_id)
            elif request_type == "voice_command":
                return await self._process_voice_command(agent, query, context, user_id)
            elif request_type == "optimize_layout":
                return await self._optimize_layout(agent, query, context, user_id)
            elif request_type == "analyze_canvas":
                return await self._analyze_canvas(agent, query, context, user_id)
            elif request_type == "create_visualization":
                return await self._create_visualization(agent, query, context, user_id)
            else:
                # General canvas query
                return await self._handle_general_query(agent, query, context, user_id)
                
        except Exception as e:
            return {
                "status": "error",
                "message": f"Canvas visualization failed: {str(e)}"
            }
    
    def _determine_request_type(self, query: str, context: Dict[str, Any]) -> str:
        """Determine the type of canvas request"""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ["structure", "convert", "text to canvas"]):
            return "structure_text"
        elif context.get("is_voice_command", False) or any(cmd in query_lower for cmds in self.voice_commands.values() for cmd in cmds):
            return "voice_command"
        elif any(word in query_lower for word in ["optimize", "arrange", "layout", "organize"]):
            return "optimize_layout"
        elif any(word in query_lower for word in ["analyze", "patterns", "insights", "examine"]):
            return "analyze_canvas"
        elif any(word in query_lower for word in ["visualize", "create canvas", "diagram"]):
            return "create_visualization"
        else:
            return "general"
    
    async def _structure_text(self, agent: ChatCompletionAgent, query: str, context: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Structure text into canvas nodes"""
        
        # Get text to structure
        text_content = context.get("text", query)
        structure_type = context.get("structure_type", "auto")
        
        # Use plugin to structure text
        structure_result = await self.canvas_plugin.structure_text(
            text=text_content,
            structure_type=structure_type,
            context_hints=context.get("hints", [])
        )
        
        # Parse result
        structure_data = json.loads(structure_result)
        
        # Create canvas nodes
        nodes = []
        for idx, node_data in enumerate(structure_data["nodes"]):
            node = {
                "id": f"node_{uuid4().hex[:8]}",
                "type": node_data["type"],
                "data": {
                    "label": node_data["label"],
                    "description": node_data.get("description", ""),
                    "metadata": node_data.get("metadata", {})
                },
                "position": self._calculate_position(idx, len(structure_data["nodes"])),
                "style": self.node_types.get(node_data["type"], {})
            }
            nodes.append(node)
        
        # Create edges
        edges = []
        for edge_data in structure_data.get("relationships", []):
            edge = {
                "id": f"edge_{uuid4().hex[:8]}",
                "source": nodes[edge_data["from"]]["id"],
                "target": nodes[edge_data["to"]]["id"],
                "type": edge_data.get("type", "default"),
                "label": edge_data.get("label", "")
            }
            edges.append(edge)
        
        # Generate layout
        layout = self._generate_layout(nodes, edges)
        
        return {
            "status": "success",
            "canvas": {
                "nodes": nodes,
                "edges": edges,
                "layout": layout,
                "metadata": {
                    "created_at": datetime.utcnow().isoformat(),
                    "source": "text_structure",
                    "node_count": len(nodes),
                    "edge_count": len(edges)
                }
            },
            "insights": structure_data.get("insights", []),
            "suggestions": [
                "Add more details to nodes",
                "Create additional connections",
                "Group related nodes",
                "Apply different layouts"
            ]
        }
    
    async def _process_voice_command(self, agent: ChatCompletionAgent, query: str, context: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Process voice commands for canvas manipulation"""
        
        # Get current canvas state
        current_canvas = context.get("canvas", {})
        voice_transcript = context.get("voice_transcript", query)
        
        # Use plugin to process voice command
        command_result = await self.canvas_plugin.process_voice_command(
            command=voice_transcript,
            canvas_state=current_canvas,
            command_patterns=self.voice_commands
        )
        
        # Parse result
        command_data = json.loads(command_result)
        
        # Execute canvas operations
        canvas_updates = {
            "operations": [],
            "affected_elements": []
        }
        
        for operation in command_data["operations"]:
            if operation["type"] == "create":
                new_node = self._create_node_from_voice(operation)
                canvas_updates["operations"].append({
                    "type": "add_node",
                    "node": new_node
                })
                canvas_updates["affected_elements"].append(new_node["id"])
                
            elif operation["type"] == "connect":
                new_edge = self._create_edge_from_voice(operation, current_canvas)
                canvas_updates["operations"].append({
                    "type": "add_edge",
                    "edge": new_edge
                })
                canvas_updates["affected_elements"].extend([new_edge["source"], new_edge["target"]])
                
            elif operation["type"] == "move":
                move_op = self._create_move_operation(operation, current_canvas)
                canvas_updates["operations"].append(move_op)
                canvas_updates["affected_elements"].append(operation["target"])
                
            elif operation["type"] == "delete":
                delete_op = self._create_delete_operation(operation, current_canvas)
                canvas_updates["operations"].append(delete_op)
                canvas_updates["affected_elements"].append(operation["target"])
        
        # Generate feedback
        feedback = self._generate_voice_feedback(command_data)
        
        return {
            "status": "success",
            "command_interpretation": command_data["interpretation"],
            "canvas_updates": canvas_updates,
            "feedback": feedback,
            "voice_response": command_data.get("voice_response", "Command executed successfully"),
            "suggestions": command_data.get("suggestions", []),
            "confidence": command_data.get("confidence", 0.95)
        }
    
    async def _optimize_layout(self, agent: ChatCompletionAgent, query: str, context: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Optimize canvas layout for clarity"""
        
        # Get current canvas
        canvas = context.get("canvas", {})
        layout_algorithm = context.get("algorithm", "hierarchical")
        optimization_goals = context.get("goals", ["clarity", "flow"])
        
        # Use plugin to optimize layout
        layout_result = await self.canvas_plugin.optimize_layout(
            nodes=canvas.get("nodes", []),
            edges=canvas.get("edges", []),
            algorithm=layout_algorithm,
            constraints=context.get("constraints", {})
        )
        
        # Parse result
        layout_data = json.loads(layout_result)
        
        # Apply new positions
        optimized_nodes = []
        for node in canvas.get("nodes", []):
            new_position = layout_data["positions"].get(node["id"])
            if new_position:
                node_copy = node.copy()
                node_copy["position"] = new_position
                optimized_nodes.append(node_copy)
            else:
                optimized_nodes.append(node)
        
        # Calculate layout metrics
        metrics = self._calculate_layout_metrics(optimized_nodes, canvas.get("edges", []))
        
        return {
            "status": "success",
            "optimized_canvas": {
                "nodes": optimized_nodes,
                "edges": canvas.get("edges", []),
                "layout_algorithm": layout_algorithm,
                "metrics": metrics
            },
            "improvements": layout_data.get("improvements", []),
            "visualization_hints": {
                "focus_areas": layout_data.get("focus_areas", []),
                "suggested_views": layout_data.get("views", ["overview", "detail"]),
                "interaction_points": layout_data.get("interaction_points", [])
            },
            "next_steps": [
                "Apply semantic grouping",
                "Add visual annotations",
                "Create alternative views",
                "Export for presentation"
            ]
        }
    
    async def _analyze_canvas(self, agent: ChatCompletionAgent, query: str, context: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Analyze canvas for patterns and insights"""
        
        # Get canvas to analyze
        canvas = context.get("canvas", {})
        analysis_focus = context.get("focus", ["patterns", "gaps", "opportunities"])
        
        # Use plugin to analyze canvas
        analysis_result = await self.canvas_plugin.analyze_canvas(
            canvas=canvas,
            analysis_types=analysis_focus,
            depth="comprehensive"
        )
        
        # Parse result
        analysis_data = json.loads(analysis_result)
        
        # Structure insights
        insights = {
            "patterns": analysis_data.get("patterns", []),
            "clusters": analysis_data.get("clusters", []),
            "gaps": analysis_data.get("gaps", []),
            "opportunities": analysis_data.get("opportunities", []),
            "risks": analysis_data.get("risks", [])
        }
        
        # Generate recommendations
        recommendations = self._generate_canvas_recommendations(analysis_data)
        
        # Create visual highlights
        visual_highlights = self._create_visual_highlights(analysis_data, canvas)
        
        return {
            "status": "success",
            "analysis": insights,
            "metrics": {
                "connectivity": analysis_data.get("connectivity_score", 0),
                "complexity": analysis_data.get("complexity_score", 0),
                "balance": analysis_data.get("balance_score", 0),
                "completeness": analysis_data.get("completeness_score", 0)
            },
            "recommendations": recommendations,
            "visual_highlights": visual_highlights,
            "key_findings": analysis_data.get("key_findings", []),
            "export_options": ["PDF Report", "Interactive Dashboard", "Presentation"]
        }
    
    async def _create_visualization(self, agent: ChatCompletionAgent, query: str, context: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Create a new strategic visualization"""
        
        # Get visualization parameters
        viz_type = context.get("type", "strategic_overview")
        data_sources = context.get("data_sources", {})
        style_preferences = context.get("style", "modern")
        
        # Use plugin to create visualization
        viz_result = await self.canvas_plugin.create_visualization(
            visualization_type=viz_type,
            data=data_sources,
            style=style_preferences,
            interactive=True
        )
        
        # Parse result
        viz_data = json.loads(viz_result)
        
        # Build complete canvas
        canvas = {
            "id": str(uuid4()),
            "type": viz_type,
            "nodes": viz_data["nodes"],
            "edges": viz_data["edges"],
            "layout": viz_data["layout"],
            "style": viz_data["style"],
            "metadata": {
                "created_at": datetime.utcnow().isoformat(),
                "created_by": user_id,
                "version": "1.0",
                "interactive": True
            }
        }
        
        # Add interaction handlers
        interactions = self._define_canvas_interactions(canvas)
        
        return {
            "status": "success",
            "canvas": canvas,
            "interactions": interactions,
            "initial_view": viz_data.get("initial_view", "overview"),
            "available_views": viz_data.get("views", ["overview", "detail", "flow"]),
            "customization_options": {
                "themes": ["light", "dark", "high-contrast"],
                "layouts": ["hierarchical", "force", "circular", "grid"],
                "filters": ["by_type", "by_status", "by_priority"]
            },
            "sharing_options": ["Export PNG", "Share Link", "Embed Code"]
        }
    
    async def _handle_general_query(self, agent: ChatCompletionAgent, query: str, context: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Handle general canvas queries"""
        
        response = await agent.invoke(f"""
Query: {query}
Context: {json.dumps(context, indent=2)}

Please provide strategic canvas visualization guidance or answer the question.
""")
        
        return {
            "status": "success",
            "response": response.content,
            "suggestions": [
                "Create new canvas visualization",
                "Optimize existing layout",
                "Analyze canvas patterns",
                "Try voice commands"
            ]
        }
    
    def _calculate_position(self, index: int, total: int) -> Dict[str, float]:
        """Calculate node position based on index"""
        
        # Simple grid layout
        cols = max(3, int(total ** 0.5))
        row = index // cols
        col = index % cols
        
        return {
            "x": col * 200 + 100,
            "y": row * 150 + 100
        }
    
    def _generate_layout(self, nodes: List[Dict[str, Any]], edges: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate layout configuration"""
        
        return {
            "algorithm": "hierarchical",
            "direction": "TB",  # Top to Bottom
            "spacing": {
                "nodeSpacing": 150,
                "levelSpacing": 200
            },
            "alignment": "center"
        }
    
    def _create_node_from_voice(self, operation: Dict[str, Any]) -> Dict[str, Any]:
        """Create a node from voice command operation"""
        
        node_type = operation.get("node_type", "insight")
        
        return {
            "id": f"node_{uuid4().hex[:8]}",
            "type": node_type,
            "data": {
                "label": operation.get("label", "New Node"),
                "description": operation.get("description", ""),
                "created_via": "voice"
            },
            "position": {"x": 100, "y": 100},  # Default position
            "style": self.node_types.get(node_type, {})
        }
    
    def _create_edge_from_voice(self, operation: Dict[str, Any], canvas: Dict[str, Any]) -> Dict[str, Any]:
        """Create an edge from voice command operation"""
        
        return {
            "id": f"edge_{uuid4().hex[:8]}",
            "source": operation.get("source_id"),
            "target": operation.get("target_id"),
            "type": operation.get("edge_type", "default"),
            "label": operation.get("label", ""),
            "created_via": "voice"
        }
    
    def _create_move_operation(self, operation: Dict[str, Any], canvas: Dict[str, Any]) -> Dict[str, Any]:
        """Create a move operation from voice command"""
        
        return {
            "type": "move_node",
            "node_id": operation.get("target"),
            "new_position": operation.get("position", {"x": 200, "y": 200}),
            "relative": operation.get("relative", False)
        }
    
    def _create_delete_operation(self, operation: Dict[str, Any], canvas: Dict[str, Any]) -> Dict[str, Any]:
        """Create a delete operation from voice command"""
        
        return {
            "type": "delete_element",
            "element_id": operation.get("target"),
            "element_type": operation.get("target_type", "node")
        }
    
    def _generate_voice_feedback(self, command_data: Dict[str, Any]) -> str:
        """Generate user-friendly feedback for voice commands"""
        
        operations = command_data.get("operations", [])
        if not operations:
            return "I couldn't understand that command. Could you please rephrase?"
        
        feedback_parts = []
        for op in operations:
            if op["type"] == "create":
                feedback_parts.append(f"Created {op.get('node_type', 'node')} '{op.get('label', 'new node')}'")
            elif op["type"] == "connect":
                feedback_parts.append(f"Connected nodes")
            elif op["type"] == "move":
                feedback_parts.append(f"Moved {op.get('target', 'element')}")
            elif op["type"] == "delete":
                feedback_parts.append(f"Deleted {op.get('target', 'element')}")
        
        return " and ".join(feedback_parts)
    
    def _calculate_layout_metrics(self, nodes: List[Dict[str, Any]], edges: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate metrics for layout quality"""
        
        return {
            "edge_crossings": 0,  # Would calculate actual crossings
            "node_overlaps": 0,   # Would check for overlaps
            "aspect_ratio": 1.5,  # Width/height ratio
            "density": len(edges) / (len(nodes) * (len(nodes) - 1) / 2) if len(nodes) > 1 else 0,
            "symmetry_score": 0.8  # Would calculate actual symmetry
        }
    
    def _generate_canvas_recommendations(self, analysis_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate recommendations based on canvas analysis"""
        
        recommendations = []
        
        # Check for isolated nodes
        if analysis_data.get("isolated_nodes", []):
            recommendations.append({
                "type": "connectivity",
                "priority": "high",
                "description": "Connect isolated elements to main structure",
                "affected_nodes": analysis_data["isolated_nodes"]
            })
        
        # Check for complexity
        if analysis_data.get("complexity_score", 0) > 0.8:
            recommendations.append({
                "type": "simplification",
                "priority": "medium",
                "description": "Consider breaking down complex areas into sub-canvases",
                "suggestion": "Use hierarchical grouping"
            })
        
        # Check for gaps
        if analysis_data.get("gaps", []):
            recommendations.append({
                "type": "completion",
                "priority": "medium",
                "description": "Address identified gaps in canvas",
                "gaps": analysis_data["gaps"]
            })
        
        return recommendations
    
    def _create_visual_highlights(self, analysis_data: Dict[str, Any], canvas: Dict[str, Any]) -> Dict[str, Any]:
        """Create visual highlights for analysis results"""
        
        return {
            "node_highlights": [
                {
                    "node_id": node_id,
                    "style": {"borderColor": "#ff5722", "borderWidth": 3},
                    "reason": "Critical path"
                }
                for node_id in analysis_data.get("critical_nodes", [])
            ],
            "edge_highlights": [
                {
                    "edge_id": edge_id,
                    "style": {"strokeWidth": 3, "strokeColor": "#2196f3"},
                    "reason": "Strong dependency"
                }
                for edge_id in analysis_data.get("critical_edges", [])
            ],
            "regions": [
                {
                    "nodes": cluster,
                    "style": {"backgroundColor": "rgba(33, 150, 243, 0.1)"},
                    "label": f"Cluster {idx + 1}"
                }
                for idx, cluster in enumerate(analysis_data.get("clusters", []))
            ]
        }
    
    def _define_canvas_interactions(self, canvas: Dict[str, Any]) -> Dict[str, Any]:
        """Define interaction handlers for canvas"""
        
        return {
            "node_click": {
                "action": "show_details",
                "enable_edit": True
            },
            "edge_click": {
                "action": "show_relationship",
                "enable_edit": True
            },
            "canvas_click": {
                "action": "create_node",
                "enable_context_menu": True
            },
            "node_drag": {
                "enabled": True,
                "snap_to_grid": True
            },
            "zoom": {
                "enabled": True,
                "min": 0.5,
                "max": 2.0
            },
            "pan": {
                "enabled": True
            }
        }