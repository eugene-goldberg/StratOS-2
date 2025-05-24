"""
North Star Agent - Manages organizational strategic foundation elements.

Responsibilities:
- Purpose management
- Vision management
- Values management
- Strategic goals hierarchy
"""

from typing import Dict, Any, List, Optional
import json
from semantic_kernel import Kernel
from semantic_kernel.functions import KernelPlugin
from ...common.base_agent import BaseStratosAgent
from .plugins.north_star_plugin import NorthStarPlugin


class NorthStarAgent(BaseStratosAgent):
    """Agent for managing strategic foundation elements."""
    
    def __init__(self, kernel: Kernel):
        """Initialize North Star Agent.
        
        Args:
            kernel: Semantic Kernel instance
        """
        # Initialize the plugin using the pattern from semantic_kernel_multi_agent
        self.north_star_plugin_instance = NorthStarPlugin()
        
        # Create KernelPlugin from the plugin instance
        self.north_star_plugin = KernelPlugin.from_object(
            "NorthStarPlugin",
            self.north_star_plugin_instance,
            description="Strategic foundation management capabilities"
        )
        
        instructions = """
You are the North Star Agent responsible for managing the organization's strategic foundation.
Your responsibilities include:
- Maintaining the organizational purpose statement
- Managing the vision statement
- Curating organizational values
- Overseeing strategic goals with hierarchical relationships
- Validating alignment of initiatives with strategic elements

When managing strategic elements:
1. Ensure consistency across all elements
2. Maintain clear parent-child relationships for goals
3. Validate that all elements support each other
4. Provide guidance on strategic alignment
5. Track versions and changes over time

Always emphasize the importance of alignment between purpose, vision, values, and goals.
"""
        
        super().__init__(
            name="NorthStarAgent",
            instructions=instructions,
            kernel=kernel,
            description="Manages organizational purpose, vision, values, and strategic goals",
            plugins=[self.north_star_plugin]
        )
        
        # Add plugin to kernel for function calling
        self.kernel.plugins["NorthStarPlugin"] = self.north_star_plugin
    
    async def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process North Star related requests.
        
        Args:
            request: Request containing:
                - element: Type of element (purpose, vision, values, goals)
                - action: Action to perform
                - data: Action-specific data
                
        Returns:
            Response with processed results
        """
        element = request.get("element", "")
        action = request.get("action", "")
        data = request.get("data", {})
        
        try:
            if element == "purpose":
                return await self._manage_purpose(action, data)
            elif element == "vision":
                return await self._manage_vision(action, data)
            elif element == "values":
                return await self._manage_values(action, data)
            elif element == "goals":
                return await self._manage_goals(action, data)
            elif element == "alignment":
                return await self._validate_alignment(data)
            elif element == "summary":
                return await self._get_summary()
            else:
                return {
                    "error": f"Unknown element: {element}",
                    "supported_elements": [
                        "purpose", "vision", "values", "goals", 
                        "alignment", "summary"
                    ]
                }
        except Exception as e:
            return {
                "error": f"Error processing request: {str(e)}",
                "element": element,
                "action": action
            }
    
    async def _manage_purpose(self, action: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Manage organizational purpose."""
        content = data.get("content")
        
        purpose_json = self.north_star_plugin_instance.manage_purpose(
            action=action,
            content=content
        )
        
        return json.loads(purpose_json)
    
    async def _manage_vision(self, action: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Manage organizational vision."""
        content = data.get("content")
        
        vision_json = self.north_star_plugin_instance.manage_vision(
            action=action,
            content=content
        )
        
        return json.loads(vision_json)
    
    async def _manage_values(self, action: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Manage organizational values."""
        value_name = data.get("name")
        value_description = data.get("description")
        
        values_json = self.north_star_plugin_instance.manage_values(
            action=action,
            value_name=value_name,
            value_description=value_description
        )
        
        return json.loads(values_json)
    
    async def _manage_goals(self, action: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Manage strategic goals."""
        goal_id = data.get("id")
        goal_name = data.get("name")
        goal_description = data.get("description")
        parent_id = data.get("parent_id")
        target_date = data.get("target_date")
        
        goals_json = self.north_star_plugin_instance.manage_strategic_goals(
            action=action,
            goal_id=goal_id,
            goal_name=goal_name,
            goal_description=goal_description,
            parent_id=parent_id,
            target_date=target_date
        )
        
        return json.loads(goals_json)
    
    async def _validate_alignment(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate alignment with North Star elements."""
        element_type = data.get("element_type", "")
        element_content = data.get("content", "")
        
        alignment_json = self.north_star_plugin_instance.validate_alignment(
            element_type=element_type,
            element_content=element_content
        )
        
        return json.loads(alignment_json)
    
    async def _get_summary(self) -> Dict[str, Any]:
        """Get complete North Star summary."""
        summary_json = self.north_star_plugin_instance.get_north_star_summary()
        
        result = json.loads(summary_json)
        result["status"] = "success"
        
        return result