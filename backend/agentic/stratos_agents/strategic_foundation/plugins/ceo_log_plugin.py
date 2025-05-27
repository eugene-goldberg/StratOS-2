"""
CEO Log Plugin for StratOS
Adapted from semantic_kernel_multi_agent pattern using @kernel_function decorators
"""

import json
from typing import Optional, List, Dict, Any
from datetime import datetime
from semantic_kernel.functions import kernel_function
from semantic_kernel.kernel_pydantic import KernelBaseModel


class CEOLogPlugin(KernelBaseModel):
    """Plugin that provides CEO Log functionality using Semantic Kernel patterns."""
    
    def __init__(self):
        """Initialize the CEO Log plugin."""
        super().__init__()
        # In production, this would connect to Cosmos DB and other services
        # For now, we'll use in-memory storage for demonstration
        self.entries: List[Dict[str, Any]] = []
    
    @kernel_function(
        description="Generate tags for a CEO log entry",
        name="GenerateTags"
    )
    def generate_tags(self, entry: str) -> str:
        """
        Generate relevant tags for a CEO log entry.
        
        Args:
            entry (str): The CEO log entry text
            
        Returns:
            str: JSON string with generated tags
        """
        # In production, this would use the AI model to generate tags
        # For now, we'll simulate tag generation
        tags = []
        
        # Simple keyword-based tag generation (to be replaced with AI)
        keywords = {
            "strategy": ["strategic", "plan", "goal", "objective", "vision"],
            "risk": ["risk", "threat", "concern", "issue", "problem"],
            "opportunity": ["opportunity", "potential", "growth", "expand"],
            "team": ["team", "people", "staff", "employee", "culture"],
            "market": ["market", "customer", "client", "competitor", "industry"],
            "financial": ["revenue", "cost", "budget", "profit", "financial"],
            "innovation": ["innovation", "technology", "digital", "transform", "new"]
        }
        
        entry_lower = entry.lower()
        for tag, words in keywords.items():
            if any(word in entry_lower for word in words):
                tags.append(tag)
        
        # Add a timestamp tag
        tags.append(f"week_{datetime.now().isocalendar()[1]}")
        
        return json.dumps({
            "tags": tags,
            "count": len(tags),
            "generated_at": datetime.now().isoformat()
        }, indent=2)
    
    @kernel_function(
        description="Summarize a CEO log entry",
        name="SummarizeEntry"
    )
    def summarize_entry(self, entry: str, max_length: Optional[int] = 150) -> str:
        """
        Create a concise summary of a CEO log entry.
        
        Args:
            entry (str): The CEO log entry text
            max_length (int, optional): Maximum length of summary. Defaults to 150.
            
        Returns:
            str: Summarized version of the entry
        """
        # In production, this would use the AI model for summarization
        # For now, we'll do simple truncation with ellipsis
        if len(entry) <= max_length:
            return entry
        
        # Find a good break point
        truncated = entry[:max_length]
        last_period = truncated.rfind('.')
        last_space = truncated.rfind(' ')
        
        if last_period > max_length * 0.8:
            return truncated[:last_period + 1]
        elif last_space > max_length * 0.8:
            return truncated[:last_space] + "..."
        else:
            return truncated + "..."
    
    @kernel_function(
        description="Extract strategic insights from CEO log entries",
        name="ExtractInsights"
    )
    def extract_insights(self, entries: str, focus_area: Optional[str] = None) -> str:
        """
        Extract strategic insights from one or more CEO log entries.
        
        Args:
            entries (str): JSON string of CEO log entries or single entry text
            focus_area (str, optional): Specific area to focus on (e.g., "risks", "opportunities")
            
        Returns:
            str: JSON string with extracted insights
        """
        # Parse entries if JSON, otherwise treat as single entry
        try:
            entry_list = json.loads(entries) if entries.startswith('[') or entries.startswith('{') else [entries]
        except:
            entry_list = [entries]
        
        insights = {
            "total_entries_analyzed": len(entry_list),
            "focus_area": focus_area or "general",
            "insights": [],
            "themes": [],
            "recommendations": []
        }
        
        # In production, this would use AI to extract insights
        # For now, we'll provide template insights
        if focus_area == "risks":
            insights["insights"].append("Risk awareness is demonstrated across entries")
            insights["recommendations"].append("Develop formal risk mitigation strategies")
        elif focus_area == "opportunities":
            insights["insights"].append("Several growth opportunities identified")
            insights["recommendations"].append("Prioritize opportunities by strategic fit")
        else:
            insights["insights"].append("Strategic thinking evident throughout entries")
            insights["themes"].append("Leadership focus on long-term vision")
        
        insights["generated_at"] = datetime.now().isoformat()
        
        return json.dumps(insights, indent=2)
    
    @kernel_function(
        description="Save a CEO log entry with metadata",
        name="SaveEntry"
    )
    def save_entry(self, 
                   content: str, 
                   category: Optional[str] = "general",
                   is_voice: Optional[bool] = False) -> str:
        """
        Save a CEO log entry with metadata.
        
        Args:
            content (str): The entry content
            category (str): Category of the entry
            is_voice (bool): Whether this was a voice entry
            
        Returns:
            str: JSON string with entry ID and save status
        """
        entry = {
            "id": f"ceo_log_{datetime.now().timestamp()}",
            "content": content,
            "category": category,
            "is_voice": is_voice,
            "created_at": datetime.now().isoformat(),
            "tags": json.loads(self.generate_tags(content))["tags"],
            "summary": self.summarize_entry(content)
        }
        
        self.entries.append(entry)
        
        return json.dumps({
            "success": True,
            "entry_id": entry["id"],
            "message": "Entry saved successfully"
        }, indent=2)
    
    @kernel_function(
        description="Search CEO log entries",
        name="SearchEntries"
    )
    def search_entries(self, 
                      query: str,
                      category: Optional[str] = None,
                      limit: Optional[int] = 10) -> str:
        """
        Search through CEO log entries.
        
        Args:
            query (str): Search query
            category (str, optional): Filter by category
            limit (int, optional): Maximum results to return
            
        Returns:
            str: JSON string with search results
        """
        results = []
        query_lower = query.lower()
        
        for entry in self.entries:
            # Filter by category if specified
            if category and entry.get("category") != category:
                continue
            
            # Simple text search (to be replaced with semantic search)
            if (query_lower in entry["content"].lower() or 
                any(query_lower in tag for tag in entry.get("tags", []))):
                results.append({
                    "id": entry["id"],
                    "summary": entry["summary"],
                    "category": entry["category"],
                    "created_at": entry["created_at"],
                    "relevance_score": 0.8  # Simulated relevance
                })
                
                if len(results) >= limit:
                    break
        
        return json.dumps({
            "query": query,
            "count": len(results),
            "results": results
        }, indent=2)