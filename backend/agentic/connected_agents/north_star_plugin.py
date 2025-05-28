"""
North Star Plugin for StratOS
Manages organizational purpose, vision, values, and strategic goals
"""

import json
from typing import Optional, List, Dict, Any
from datetime import datetime
from semantic_kernel.functions import kernel_function
from semantic_kernel.kernel_pydantic import KernelBaseModel


class NorthStarPlugin(KernelBaseModel):
    """Plugin that manages strategic foundation elements."""
    
    def __init__(self):
        """Initialize the North Star plugin."""
        super().__init__()
        # In production, this would connect to Cosmos DB
        # For now, we'll use in-memory storage
        self.purpose = None
        self.vision = None
        self.values = []
        self.strategic_goals = {}  # id -> goal mapping
        self.goal_hierarchy = {}   # parent_id -> [child_ids] mapping
    
    @kernel_function(
        description="Get or set the organizational purpose",
        name="ManagePurpose"
    )
    def manage_purpose(self, action: str, content: Optional[str] = None) -> str:
        """
        Get or set the organizational purpose statement.
        
        Args:
            action (str): Either "get" or "set"
            content (str, optional): The purpose statement (required for "set")
            
        Returns:
            str: JSON string with purpose information
        """
        if action.lower() == "set" and content:
            self.purpose = {
                "statement": content,
                "updated_at": datetime.now().isoformat(),
                "version": 1 if not self.purpose else self.purpose.get("version", 0) + 1
            }
            return json.dumps({
                "success": True,
                "action": "set",
                "purpose": self.purpose
            }, indent=2)
        
        elif action.lower() == "get":
            if self.purpose:
                return json.dumps({
                    "success": True,
                    "action": "get",
                    "purpose": self.purpose
                }, indent=2)
            else:
                return json.dumps({
                    "success": False,
                    "action": "get",
                    "message": "No purpose statement defined yet"
                }, indent=2)
        
        return json.dumps({
            "success": False,
            "error": "Invalid action. Use 'get' or 'set'"
        }, indent=2)
    
    @kernel_function(
        description="Get or set the organizational vision",
        name="ManageVision"
    )
    def manage_vision(self, action: str, content: Optional[str] = None) -> str:
        """
        Get or set the organizational vision statement.
        
        Args:
            action (str): Either "get" or "set"
            content (str, optional): The vision statement (required for "set")
            
        Returns:
            str: JSON string with vision information
        """
        if action.lower() == "set" and content:
            self.vision = {
                "statement": content,
                "updated_at": datetime.now().isoformat(),
                "version": 1 if not self.vision else self.vision.get("version", 0) + 1
            }
            return json.dumps({
                "success": True,
                "action": "set",
                "vision": self.vision
            }, indent=2)
        
        elif action.lower() == "get":
            if self.vision:
                return json.dumps({
                    "success": True,
                    "action": "get",
                    "vision": self.vision
                }, indent=2)
            else:
                return json.dumps({
                    "success": False,
                    "action": "get",
                    "message": "No vision statement defined yet"
                }, indent=2)
        
        return json.dumps({
            "success": False,
            "error": "Invalid action. Use 'get' or 'set'"
        }, indent=2)
    
    @kernel_function(
        description="Manage organizational values",
        name="ManageValues"
    )
    def manage_values(self, 
                     action: str, 
                     value_name: Optional[str] = None,
                     value_description: Optional[str] = None) -> str:
        """
        Manage organizational values (add, remove, list).
        
        Args:
            action (str): One of "add", "remove", "list"
            value_name (str, optional): Name of the value
            value_description (str, optional): Description of the value
            
        Returns:
            str: JSON string with values information
        """
        if action.lower() == "add" and value_name:
            value = {
                "name": value_name,
                "description": value_description or "",
                "created_at": datetime.now().isoformat()
            }
            self.values.append(value)
            return json.dumps({
                "success": True,
                "action": "add",
                "value": value,
                "total_values": len(self.values)
            }, indent=2)
        
        elif action.lower() == "remove" and value_name:
            initial_count = len(self.values)
            self.values = [v for v in self.values if v["name"] != value_name]
            removed = initial_count > len(self.values)
            return json.dumps({
                "success": removed,
                "action": "remove",
                "message": f"Value '{value_name}' removed" if removed else f"Value '{value_name}' not found"
            }, indent=2)
        
        elif action.lower() == "list":
            return json.dumps({
                "success": True,
                "action": "list",
                "values": self.values,
                "count": len(self.values)
            }, indent=2)
        
        return json.dumps({
            "success": False,
            "error": "Invalid action. Use 'add', 'remove', or 'list'"
        }, indent=2)
    
    @kernel_function(
        description="Manage strategic goals with hierarchy",
        name="ManageStrategicGoals"
    )
    def manage_strategic_goals(self,
                              action: str,
                              goal_id: Optional[str] = None,
                              goal_name: Optional[str] = None,
                              goal_description: Optional[str] = None,
                              parent_id: Optional[str] = None,
                              target_date: Optional[str] = None) -> str:
        """
        Manage strategic goals with parent-child relationships.
        
        Args:
            action (str): One of "create", "update", "delete", "get", "list"
            goal_id (str, optional): Goal identifier
            goal_name (str, optional): Name of the goal
            goal_description (str, optional): Description of the goal
            parent_id (str, optional): Parent goal ID for hierarchy
            target_date (str, optional): Target completion date
            
        Returns:
            str: JSON string with goal information
        """
        if action.lower() == "create" and goal_name:
            goal_id = goal_id or f"goal_{datetime.now().timestamp()}"
            goal = {
                "id": goal_id,
                "name": goal_name,
                "description": goal_description or "",
                "parent_id": parent_id,
                "target_date": target_date,
                "created_at": datetime.now().isoformat(),
                "status": "active"
            }
            
            self.strategic_goals[goal_id] = goal
            
            # Update hierarchy
            if parent_id:
                if parent_id not in self.goal_hierarchy:
                    self.goal_hierarchy[parent_id] = []
                self.goal_hierarchy[parent_id].append(goal_id)
            
            return json.dumps({
                "success": True,
                "action": "create",
                "goal": goal
            }, indent=2)
        
        elif action.lower() == "get" and goal_id:
            goal = self.strategic_goals.get(goal_id)
            if goal:
                # Add children to response
                children = self.goal_hierarchy.get(goal_id, [])
                goal_with_children = goal.copy()
                goal_with_children["children"] = children
                
                return json.dumps({
                    "success": True,
                    "action": "get",
                    "goal": goal_with_children
                }, indent=2)
            else:
                return json.dumps({
                    "success": False,
                    "action": "get",
                    "message": f"Goal '{goal_id}' not found"
                }, indent=2)
        
        elif action.lower() == "list":
            # Build hierarchical view
            root_goals = [g for g in self.strategic_goals.values() if not g.get("parent_id")]
            
            def build_tree(goal):
                tree_goal = goal.copy()
                children_ids = self.goal_hierarchy.get(goal["id"], [])
                tree_goal["children"] = [build_tree(self.strategic_goals[child_id]) 
                                        for child_id in children_ids 
                                        if child_id in self.strategic_goals]
                return tree_goal
            
            hierarchical_goals = [build_tree(g) for g in root_goals]
            
            return json.dumps({
                "success": True,
                "action": "list",
                "goals": hierarchical_goals,
                "total_count": len(self.strategic_goals)
            }, indent=2)
        
        return json.dumps({
            "success": False,
            "error": "Invalid action or missing required parameters"
        }, indent=2)
    
    @kernel_function(
        description="Validate alignment between strategic elements",
        name="ValidateAlignment"
    )
    def validate_alignment(self, element_type: str, element_content: str) -> str:
        """
        Validate alignment of an element with the North Star.
        
        Args:
            element_type (str): Type of element (e.g., "goal", "initiative", "decision")
            element_content (str): Content to validate
            
        Returns:
            str: JSON string with alignment assessment
        """
        alignment_score = 0.0
        alignment_factors = []
        recommendations = []
        
        # Check if North Star elements exist
        if not self.purpose:
            recommendations.append("Define organizational purpose first")
        if not self.vision:
            recommendations.append("Define organizational vision first")
        if not self.values:
            recommendations.append("Define organizational values first")
        
        # Simulate alignment scoring (to be replaced with AI)
        if self.purpose and self.vision:
            alignment_score = 0.75  # Simulated score
            alignment_factors.append("Aligns with stated purpose")
            alignment_factors.append("Supports vision achievement")
        
        # Check value alignment
        if self.values:
            aligned_values = [v["name"] for v in self.values[:2]]  # Simulate finding aligned values
            if aligned_values:
                alignment_factors.append(f"Demonstrates values: {', '.join(aligned_values)}")
                alignment_score += 0.1
        
        # Provide recommendations based on alignment
        if alignment_score < 0.7:
            recommendations.append("Consider how this better supports the organizational purpose")
            recommendations.append("Ensure clear connection to strategic goals")
        
        return json.dumps({
            "element_type": element_type,
            "alignment_score": min(alignment_score, 1.0),
            "alignment_factors": alignment_factors,
            "recommendations": recommendations,
            "is_aligned": alignment_score >= 0.7
        }, indent=2)
    
    @kernel_function(
        description="Get complete North Star summary",
        name="GetNorthStarSummary"
    )
    def get_north_star_summary(self) -> str:
        """
        Get a complete summary of all North Star elements.
        
        Returns:
            str: JSON string with complete North Star information
        """
        summary = {
            "purpose": self.purpose["statement"] if self.purpose else None,
            "vision": self.vision["statement"] if self.vision else None,
            "values": [v["name"] for v in self.values],
            "strategic_goals_count": len(self.strategic_goals),
            "top_level_goals": [g["name"] for g in self.strategic_goals.values() 
                               if not g.get("parent_id")][:5],  # Top 5 root goals
            "last_updated": max([
                self.purpose.get("updated_at", "") if self.purpose else "",
                self.vision.get("updated_at", "") if self.vision else "",
                *[v.get("created_at", "") for v in self.values]
            ]) if any([self.purpose, self.vision, self.values]) else None
        }
        
        return json.dumps(summary, indent=2)