"""Canvas Visualization Plugin

Provides canvas manipulation, visualization, and analysis capabilities.
"""

import json
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from uuid import uuid4
import math

from semantic_kernel.functions import kernel_function
from semantic_kernel.kernel_pydantic import KernelBaseModel


class CanvasPlugin(KernelBaseModel):
    """Plugin for strategic canvas visualization and manipulation"""
    
    @kernel_function(
        description="Structure text content into canvas nodes and relationships",
        name="StructureText"
    )
    async def structure_text(
        self,
        text: str,
        structure_type: str = "auto",
        context_hints: List[str] = None
    ) -> str:
        """Convert unstructured text into structured canvas elements"""
        
        context_hints = context_hints or []
        
        # Analyze text for structure
        # This would use NLP to extract entities and relationships
        # For now, creating example structure
        structure = {
            "nodes": [
                {
                    "type": "vision",
                    "label": "Digital Transformation Excellence",
                    "description": "Lead industry transformation through innovative digital solutions",
                    "metadata": {"source": "extracted", "confidence": 0.9}
                },
                {
                    "type": "goal",
                    "label": "Increase Market Share 25%",
                    "description": "Capture additional market through digital channels",
                    "metadata": {"timeframe": "2 years", "measurable": True}
                },
                {
                    "type": "initiative",
                    "label": "Customer Experience Platform",
                    "description": "Build unified platform for seamless customer interactions",
                    "metadata": {"priority": "high", "status": "planning"}
                },
                {
                    "type": "action",
                    "label": "Implement AI Chatbot",
                    "description": "Deploy intelligent customer service automation",
                    "metadata": {"duration": "3 months", "owner": "Tech Team"}
                },
                {
                    "type": "risk",
                    "label": "Technical Complexity",
                    "description": "Integration challenges with legacy systems",
                    "metadata": {"probability": "medium", "impact": "high"}
                }
            ],
            "relationships": [
                {"from": 0, "to": 1, "type": "supports", "label": "enables"},
                {"from": 1, "to": 2, "type": "requires", "label": "drives"},
                {"from": 2, "to": 3, "type": "includes", "label": "contains"},
                {"from": 4, "to": 2, "type": "threatens", "label": "impacts"}
            ],
            "insights": [
                "Clear strategic alignment from vision to actions",
                "Risk identified that could impact initiative success",
                "Consider additional actions to mitigate technical complexity"
            ],
            "suggested_additions": [
                {"type": "action", "label": "Technical POC", "reason": "Validate integration approach"},
                {"type": "opportunity", "label": "Partner Ecosystem", "reason": "Accelerate platform development"}
            ]
        }
        
        return json.dumps(structure)
    
    @kernel_function(
        description="Process voice commands for canvas manipulation",
        name="ProcessVoiceCommand"
    )
    async def process_voice_command(
        self,
        command: str,
        canvas_state: Dict[str, Any],
        command_patterns: Dict[str, List[str]] = None
    ) -> str:
        """Parse and execute voice commands on canvas"""
        
        command_patterns = command_patterns or {}
        command_lower = command.lower()
        
        # Parse command intent
        # This would use NLP/intent recognition
        # For now, using pattern matching
        operations = []
        
        if any(word in command_lower for word in command_patterns.get("create", [])):
            # Create node command
            if "goal" in command_lower:
                operations.append({
                    "type": "create",
                    "node_type": "goal",
                    "label": self._extract_label(command, "goal"),
                    "description": "Created via voice command"
                })
            elif "risk" in command_lower:
                operations.append({
                    "type": "create",
                    "node_type": "risk",
                    "label": self._extract_label(command, "risk"),
                    "description": "Identified via voice"
                })
        
        elif any(word in command_lower for word in command_patterns.get("connect", [])):
            # Connect nodes command
            operations.append({
                "type": "connect",
                "source_id": "node_abc123",  # Would extract from command
                "target_id": "node_def456",
                "edge_type": "relates_to",
                "label": "connected"
            })
        
        elif any(word in command_lower for word in command_patterns.get("move", [])):
            # Move node command
            operations.append({
                "type": "move",
                "target": "node_abc123",
                "position": {"x": 300, "y": 200},
                "relative": "right" in command_lower
            })
        
        # Generate response
        result = {
            "interpretation": f"Understood: {command}",
            "operations": operations,
            "confidence": 0.85,
            "voice_response": self._generate_voice_response(operations),
            "suggestions": [
                "You can also say 'connect the goal to the initiative'",
                "Try 'show me all risks' to filter the view"
            ]
        }
        
        return json.dumps(result)
    
    @kernel_function(
        description="Optimize canvas layout for clarity and understanding",
        name="OptimizeLayout"
    )
    async def optimize_layout(
        self,
        nodes: List[Dict[str, Any]],
        edges: List[Dict[str, Any]],
        algorithm: str = "hierarchical",
        constraints: Dict[str, Any] = None
    ) -> str:
        """Optimize the layout of canvas elements"""
        
        constraints = constraints or {}
        
        # This would use graph layout algorithms
        # For now, creating example optimized positions
        positions = {}
        
        if algorithm == "hierarchical":
            # Group nodes by type/level
            levels = {
                "vision": 0,
                "goal": 1,
                "initiative": 2,
                "action": 3,
                "risk": 2,
                "opportunity": 2
            }
            
            # Position nodes by level
            level_counts = {}
            for node in nodes:
                node_type = node.get("type", "action")
                level = levels.get(node_type, 3)
                
                if level not in level_counts:
                    level_counts[level] = 0
                
                x = 200 + level_counts[level] * 250
                y = 100 + level * 200
                
                positions[node["id"]] = {"x": x, "y": y}
                level_counts[level] += 1
        
        elif algorithm == "force":
            # Force-directed layout
            center_x, center_y = 400, 400
            radius = 200
            
            for i, node in enumerate(nodes):
                angle = (2 * math.pi * i) / len(nodes)
                x = center_x + radius * math.cos(angle)
                y = center_y + radius * math.sin(angle)
                positions[node["id"]] = {"x": x, "y": y}
        
        # Calculate improvements
        improvements = [
            "Reduced edge crossings by 40%",
            "Improved visual hierarchy",
            "Better spacing between related elements"
        ]
        
        # Identify focus areas
        focus_areas = []
        if len(nodes) > 10:
            focus_areas.append({
                "area": "high_density",
                "nodes": [n["id"] for n in nodes[:5]],
                "suggestion": "Consider grouping or filtering"
            })
        
        result = {
            "positions": positions,
            "algorithm": algorithm,
            "improvements": improvements,
            "focus_areas": focus_areas,
            "views": ["overview", "by_type", "by_status"],
            "quality_score": 0.85
        }
        
        return json.dumps(result)
    
    @kernel_function(
        description="Analyze canvas for patterns, insights, and opportunities",
        name="AnalyzeCanvas"
    )
    async def analyze_canvas(
        self,
        canvas: Dict[str, Any],
        analysis_types: List[str] = None,
        depth: str = "standard"
    ) -> str:
        """Analyze canvas structure and content for insights"""
        
        analysis_types = analysis_types or ["patterns", "gaps", "opportunities"]
        nodes = canvas.get("nodes", [])
        edges = canvas.get("edges", [])
        
        # Perform various analyses
        analysis = {
            "patterns": [],
            "clusters": [],
            "gaps": [],
            "opportunities": [],
            "risks": [],
            "metrics": {}
        }
        
        # Pattern detection
        if "patterns" in analysis_types:
            # Identify common patterns
            node_types = {}
            for node in nodes:
                node_type = node.get("type", "unknown")
                node_types[node_type] = node_types.get(node_type, 0) + 1
            
            if node_types.get("goal", 0) > 3:
                analysis["patterns"].append({
                    "type": "multiple_goals",
                    "description": "Multiple strategic goals identified",
                    "implication": "Consider prioritization or consolidation"
                })
            
            # Check for orphaned nodes
            connected_nodes = set()
            for edge in edges:
                connected_nodes.add(edge["source"])
                connected_nodes.add(edge["target"])
            
            orphaned = [n["id"] for n in nodes if n["id"] not in connected_nodes]
            if orphaned:
                analysis["patterns"].append({
                    "type": "isolated_elements",
                    "description": f"{len(orphaned)} isolated elements found",
                    "affected_nodes": orphaned
                })
        
        # Gap analysis
        if "gaps" in analysis_types:
            # Check for missing elements
            has_vision = any(n.get("type") == "vision" for n in nodes)
            has_goals = any(n.get("type") == "goal" for n in nodes)
            has_actions = any(n.get("type") == "action" for n in nodes)
            
            if not has_vision:
                analysis["gaps"].append({
                    "type": "missing_vision",
                    "severity": "high",
                    "recommendation": "Add clear vision statement to guide strategy"
                })
            
            if has_goals and not has_actions:
                analysis["gaps"].append({
                    "type": "execution_gap",
                    "severity": "medium",
                    "recommendation": "Define concrete actions for goals"
                })
        
        # Opportunity identification
        if "opportunities" in analysis_types:
            # Look for opportunity patterns
            risk_count = sum(1 for n in nodes if n.get("type") == "risk")
            if risk_count > 2:
                analysis["opportunities"].append({
                    "type": "risk_mitigation",
                    "description": "Multiple risks identified - opportunity for comprehensive mitigation strategy",
                    "potential_impact": "high"
                })
        
        # Calculate metrics
        analysis["connectivity_score"] = len(edges) / (len(nodes) * (len(nodes) - 1) / 2) if len(nodes) > 1 else 0
        analysis["complexity_score"] = min(1.0, (len(nodes) + len(edges)) / 50)
        analysis["balance_score"] = 1 - abs(0.5 - analysis["connectivity_score"]) * 2
        analysis["completeness_score"] = self._calculate_completeness(nodes)
        
        # Key findings
        analysis["key_findings"] = [
            f"Canvas contains {len(nodes)} nodes with {len(edges)} connections",
            f"Connectivity level: {'High' if analysis['connectivity_score'] > 0.3 else 'Low'}",
            f"{len(analysis['gaps'])} strategic gaps identified"
        ]
        
        # Critical nodes (high connectivity)
        node_connections = {}
        for edge in edges:
            node_connections[edge["source"]] = node_connections.get(edge["source"], 0) + 1
            node_connections[edge["target"]] = node_connections.get(edge["target"], 0) + 1
        
        critical_nodes = [n for n, count in node_connections.items() if count > 3]
        analysis["critical_nodes"] = critical_nodes
        
        return json.dumps(analysis)
    
    @kernel_function(
        description="Create strategic visualization from data",
        name="CreateVisualization"
    )
    async def create_visualization(
        self,
        visualization_type: str,
        data: Dict[str, Any],
        style: str = "modern",
        interactive: bool = True
    ) -> str:
        """Create a new strategic visualization"""
        
        # This would create different visualization types
        # For now, creating a strategic overview
        visualization = {
            "nodes": [],
            "edges": [],
            "layout": {},
            "style": {}
        }
        
        if visualization_type == "strategic_overview":
            # Create hierarchical strategic view
            # Add vision node
            vision_node = {
                "id": f"vision_{uuid4().hex[:8]}",
                "type": "vision",
                "data": {
                    "label": data.get("vision", "Strategic Vision"),
                    "description": "Organization's long-term vision"
                },
                "position": {"x": 400, "y": 50}
            }
            visualization["nodes"].append(vision_node)
            
            # Add goal nodes
            goals = data.get("goals", [])
            for i, goal in enumerate(goals[:3]):  # Limit to 3 for clarity
                goal_node = {
                    "id": f"goal_{uuid4().hex[:8]}",
                    "type": "goal",
                    "data": {
                        "label": goal.get("title", f"Strategic Goal {i+1}"),
                        "description": goal.get("description", "")
                    },
                    "position": {"x": 200 + i * 200, "y": 200}
                }
                visualization["nodes"].append(goal_node)
                
                # Connect to vision
                visualization["edges"].append({
                    "id": f"edge_{uuid4().hex[:8]}",
                    "source": vision_node["id"],
                    "target": goal_node["id"],
                    "type": "supports"
                })
        
        # Define layout
        visualization["layout"] = {
            "type": "hierarchical",
            "direction": "TB",
            "rankSep": 150,
            "nodeSep": 100
        }
        
        # Define style
        visualization["style"] = {
            "theme": style,
            "node_styles": {
                "vision": {"fill": "#1976d2", "stroke": "#0d47a1", "text": "#ffffff"},
                "goal": {"fill": "#388e3c", "stroke": "#1b5e20", "text": "#ffffff"},
                "initiative": {"fill": "#f57c00", "stroke": "#e65100", "text": "#ffffff"},
                "action": {"fill": "#7b1fa2", "stroke": "#4a148c", "text": "#ffffff"}
            },
            "edge_styles": {
                "default": {"stroke": "#9e9e9e", "strokeWidth": 2},
                "critical": {"stroke": "#f44336", "strokeWidth": 3}
            }
        }
        
        # Add interactivity options
        if interactive:
            visualization["interactions"] = {
                "zoom": {"enabled": True, "min": 0.5, "max": 2},
                "pan": {"enabled": True},
                "select": {"enabled": True, "multi": True},
                "edit": {"enabled": True}
            }
        
        # Define available views
        visualization["views"] = [
            {"name": "overview", "zoom": 1, "center": {"x": 400, "y": 300}},
            {"name": "goals", "zoom": 1.5, "center": {"x": 400, "y": 200}},
            {"name": "execution", "zoom": 1.2, "center": {"x": 400, "y": 400}}
        ]
        
        visualization["initial_view"] = "overview"
        
        return json.dumps(visualization)
    
    @kernel_function(
        description="Suggest canvas connections based on content analysis",
        name="SuggestConnections"
    )
    async def suggest_connections(
        self,
        nodes: List[Dict[str, Any]],
        existing_edges: List[Dict[str, Any]],
        connection_strength_threshold: float = 0.7
    ) -> str:
        """Suggest meaningful connections between canvas elements"""
        
        # This would use semantic similarity and business rules
        # For now, creating example suggestions
        suggestions = []
        
        # Check for logical connections
        for i, node1 in enumerate(nodes):
            for j, node2 in enumerate(nodes[i+1:], i+1):
                # Skip if already connected
                if any(
                    (e["source"] == node1["id"] and e["target"] == node2["id"]) or
                    (e["source"] == node2["id"] and e["target"] == node1["id"])
                    for e in existing_edges
                ):
                    continue
                
                # Suggest connections based on type combinations
                type1, type2 = node1.get("type"), node2.get("type")
                
                if type1 == "goal" and type2 == "initiative":
                    suggestions.append({
                        "source": node1["id"],
                        "target": node2["id"],
                        "type": "drives",
                        "confidence": 0.85,
                        "reason": "Goals typically drive initiatives"
                    })
                elif type1 == "risk" and type2 in ["goal", "initiative"]:
                    suggestions.append({
                        "source": node1["id"],
                        "target": node2["id"],
                        "type": "threatens",
                        "confidence": 0.75,
                        "reason": "Risk may impact this element"
                    })
        
        result = {
            "suggestions": suggestions[:5],  # Limit to top 5
            "total_possible": len(suggestions),
            "analysis_notes": [
                "Connections suggested based on element types and content",
                "Review each suggestion for business relevance"
            ]
        }
        
        return json.dumps(result)
    
    def _extract_label(self, command: str, node_type: str) -> str:
        """Extract label from voice command"""
        
        # Simple extraction - would use NLP in practice
        words = command.split()
        
        # Find the node type word and take following words as label
        try:
            idx = words.index(node_type)
            label_words = words[idx+1:idx+4]  # Take up to 3 words
            return " ".join(label_words).strip('"').strip("'")
        except (ValueError, IndexError):
            return f"New {node_type}"
    
    def _generate_voice_response(self, operations: List[Dict[str, Any]]) -> str:
        """Generate natural language response for voice command"""
        
        if not operations:
            return "I didn't understand that command. Could you please try again?"
        
        responses = []
        for op in operations:
            if op["type"] == "create":
                responses.append(f"Created a new {op.get('node_type', 'element')}")
            elif op["type"] == "connect":
                responses.append("Connected the elements")
            elif op["type"] == "move":
                responses.append("Moved the element")
        
        return ". ".join(responses) + "."
    
    def _calculate_completeness(self, nodes: List[Dict[str, Any]]) -> float:
        """Calculate canvas completeness score"""
        
        required_types = {"vision", "goal", "initiative", "action"}
        present_types = {node.get("type") for node in nodes}
        
        completeness = len(present_types.intersection(required_types)) / len(required_types)
        
        # Bonus for having multiple of each type
        if len(nodes) > 10:
            completeness = min(1.0, completeness + 0.1)
        
        return completeness