"""CEO Log Agent - Handles CEO log entries and related operations.

Responsibilities:
- Voice transcription
- Tag generation
- Entry summarization
- Insight extraction

Adopted from semantic_kernel_multi_agent pattern using plugin architecture.
"""

from typing import Dict, Any, List, Optional
from uuid import UUID
import json
from semantic_kernel import Kernel
from semantic_kernel.functions import KernelPlugin
from ...common.base_agent import BaseStratosAgent
from .plugins.ceo_log_plugin import CEOLogPlugin


class CEOLogAgent(BaseStratosAgent):
    """Agent for handling CEO log operations."""
    
    def __init__(self, kernel: Kernel):
        """Initialize CEO Log Agent.
        
        Args:
            kernel: Semantic Kernel instance
        """
        # Initialize the plugin using the pattern from semantic_kernel_multi_agent
        self.ceo_log_plugin_instance = CEOLogPlugin()
        
        # Create KernelPlugin from the plugin instance
        self.ceo_log_plugin = KernelPlugin.from_object(
            "CEOLogPlugin",
            self.ceo_log_plugin_instance,
            description="CEO Log management capabilities"
        )
        
        instructions = """
You are the CEO Log Agent responsible for processing executive log entries.
Your capabilities include:
- Processing voice transcriptions
- Generating relevant tags for entries
- Creating concise summaries
- Extracting strategic insights
- Maintaining context across entries

When processing entries, focus on:
1. Strategic implications
2. Action items
3. Key decisions
4. Emerging patterns
5. Links to organizational goals

Always maintain confidentiality and highlight critical insights.
"""
        
        super().__init__(
            name="CEOLogAgent",
            instructions=instructions,
            kernel=kernel,
            description="Handles CEO log entries, voice transcription, and insights",
            plugins=[self.ceo_log_plugin]
        )
        
        # Add plugin to kernel for function calling
        self.kernel.plugins["CEOLogPlugin"] = self.ceo_log_plugin
    
    async def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process CEO log related requests.
        
        Args:
            request: Request containing:
                - action: Type of action (create_entry, transcribe, generate_tags, etc.)
                - data: Action-specific data
                
        Returns:
            Response with processed results
        """
        action = request.get("action", "unknown")
        data = request.get("data", {})
        
        try:
            if action == "create_entry":
                return await self._create_entry(data)
            elif action == "transcribe_voice":
                return await self._transcribe_voice(data)
            elif action == "generate_tags":
                return await self._generate_tags(data)
            elif action == "summarize":
                return await self._summarize_entry(data)
            elif action == "extract_insights":
                return await self._extract_insights(data)
            else:
                return {
                    "error": f"Unknown action: {action}",
                    "supported_actions": [
                        "create_entry",
                        "transcribe_voice", 
                        "generate_tags",
                        "summarize",
                        "extract_insights"
                    ]
                }
        except Exception as e:
            return {
                "error": f"Error processing request: {str(e)}",
                "action": action
            }
    
    async def _create_entry(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new CEO log entry."""
        entry_text = data.get("text", "")
        category = data.get("category", "general")
        is_voice = data.get("is_voice", False)
        
        # Save the entry using the plugin
        save_json = self.ceo_log_plugin_instance.save_entry(
            content=entry_text,
            category=category,
            is_voice=is_voice
        )
        save_result = json.loads(save_json)
        
        # Generate tags
        tags = await self._generate_tags({"text": entry_text})
        
        # Generate summary
        summary = await self._summarize_entry({"text": entry_text})
        
        return {
            "status": "success",
            "entry_id": save_result.get("entry_id"),
            "entry": {
                "text": entry_text,
                "category": category,
                "is_voice": is_voice,
                "tags": tags["tags"],
                "summary": summary["summary"]
            }
        }
    
    async def _transcribe_voice(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Transcribe voice to text."""
        # This would integrate with Azure Speech Services
        audio_data = data.get("audio")
        
        return {
            "status": "success",
            "transcription": "Transcribed text placeholder",
            "confidence": 0.95
        }
    
    async def _generate_tags(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate tags for entry."""
        text = data.get("text", "")
        
        # Use the plugin function directly
        tags_json = self.ceo_log_plugin_instance.generate_tags(text)
        tags_result = json.loads(tags_json)
        
        return {
            "status": "success",
            "tags": tags_result.get("tags", [])
        }
    
    async def _summarize_entry(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Summarize log entry."""
        text = data.get("text", "")
        max_length = data.get("max_length", 150)
        
        # Use the plugin function directly
        summary = self.ceo_log_plugin_instance.summarize_entry(text, max_length)
        
        return {
            "status": "success",
            "summary": summary
        }
    
    async def _extract_insights(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract insights from entries."""
        entries = data.get("entries", [])
        focus_area = data.get("focus_area")
        
        # Use the plugin function directly
        insights_json = self.ceo_log_plugin_instance.extract_insights(
            json.dumps(entries) if isinstance(entries, list) else entries,
            focus_area
        )
        insights_result = json.loads(insights_json)
        
        return {
            "status": "success",
            "insights": insights_result.get("insights", []),
            "themes": insights_result.get("themes", []),
            "recommendations": insights_result.get("recommendations", [])
        }