"""
CEO Log Plugin for Connected Agents
Provides CEO log entry management capabilities including tagging, summarization, and insights
"""

import json
from typing import Annotated, Optional, List, Dict, Any
from datetime import datetime
from semantic_kernel.functions import kernel_function
from semantic_kernel.kernel_pydantic import KernelBaseModel


class CEOLogPlugin(KernelBaseModel):
    """Plugin that provides CEO Log functionality for connected agents."""
    
    def __init__(self):
        """Initialize the CEO Log plugin."""
        super().__init__()
        # In-memory storage for demonstration (would use Cosmos DB in production)
        self.entries: List[Dict[str, Any]] = []
        
        # Predefined categories for CEO log entries
        self.categories = [
            "strategic_planning",
            "team_leadership", 
            "market_analysis",
            "risk_assessment",
            "innovation",
            "operations",
            "financial",
            "customer_insights",
            "general"
        ]
    
    @kernel_function(
        name="GenerateTags",
        description="Generate relevant tags for a CEO log entry based on content analysis"
    )
    def generate_tags(
        self, 
        entry: Annotated[str, "The CEO log entry text to analyze for tag generation"]
    ) -> Annotated[str, "Generated tags with metadata"]:
        """
        Generate relevant tags for a CEO log entry.
        Analyzes content for strategic themes, risks, opportunities, and key areas.
        """
        tags = []
        entry_lower = entry.lower()
        
        # Strategic keyword mapping for tag generation
        tag_mappings = {
            "strategy": ["strategic", "plan", "goal", "objective", "vision", "roadmap", "initiative"],
            "risk": ["risk", "threat", "concern", "issue", "problem", "challenge", "vulnerability"],
            "opportunity": ["opportunity", "potential", "growth", "expand", "possibility", "prospect"],
            "team": ["team", "people", "staff", "employee", "culture", "talent", "leadership"],
            "market": ["market", "customer", "client", "competitor", "industry", "segment", "trend"],
            "financial": ["revenue", "cost", "budget", "profit", "financial", "expense", "investment"],
            "innovation": ["innovation", "technology", "digital", "transform", "new", "ai", "automation"],
            "decision": ["decide", "decision", "choice", "select", "approve", "reject", "prioritize"],
            "action": ["action", "todo", "task", "implement", "execute", "deliver", "complete"],
            "urgent": ["urgent", "immediate", "asap", "critical", "priority", "important"]
        }
        
        # Check for keywords and add relevant tags
        for tag, keywords in tag_mappings.items():
            if any(keyword in entry_lower for keyword in keywords):
                tags.append(tag)
        
        # Add temporal tags
        now = datetime.now()
        tags.append(f"week_{now.isocalendar()[1]}")
        tags.append(f"month_{now.strftime('%B').lower()}")
        tags.append(f"q{(now.month-1)//3 + 1}_{now.year}")
        
        # Analyze sentiment/tone
        positive_words = ["success", "achieve", "excellent", "great", "positive", "win", "breakthrough"]
        negative_words = ["concern", "worry", "issue", "problem", "fail", "loss", "difficult"]
        
        positive_count = sum(1 for word in positive_words if word in entry_lower)
        negative_count = sum(1 for word in negative_words if word in entry_lower)
        
        if positive_count > negative_count:
            tags.append("positive_sentiment")
        elif negative_count > positive_count:
            tags.append("concern_raised")
        
        # Ensure we don't have duplicates
        tags = list(set(tags))
        
        result = {
            "tags": tags,
            "count": len(tags),
            "generated_at": datetime.now().isoformat(),
            "analysis": {
                "has_action_items": "action" in tags,
                "is_urgent": "urgent" in tags,
                "involves_risk": "risk" in tags,
                "strategic_relevance": "strategy" in tags
            }
        }
        
        return json.dumps(result, indent=2)
    
    @kernel_function(
        name="SummarizeEntry",
        description="Create a concise summary of a CEO log entry preserving key insights"
    )
    def summarize_entry(
        self, 
        entry: Annotated[str, "The CEO log entry text to summarize"],
        max_words: Annotated[int, "Maximum number of words for the summary"] = 50
    ) -> Annotated[str, "Concise summary of the entry"]:
        """
        Create a concise summary of a CEO log entry.
        Focuses on main points, decisions, and action items.
        """
        # In production, this would use AI summarization
        # For now, we'll create a structured summary
        
        sentences = entry.split('. ')
        
        # Extract key elements
        key_elements = {
            "main_topic": "",
            "key_points": [],
            "actions": [],
            "decisions": []
        }
        
        # Simple extraction logic (to be enhanced with AI)
        for sentence in sentences:
            sentence_lower = sentence.lower()
            
            # First sentence often contains main topic
            if not key_elements["main_topic"] and len(sentence) > 10:
                key_elements["main_topic"] = sentence.strip()
            
            # Look for action items
            if any(word in sentence_lower for word in ["will", "need to", "must", "should", "action"]):
                key_elements["actions"].append(sentence.strip())
            
            # Look for decisions
            if any(word in sentence_lower for word in ["decided", "decision", "agreed", "approved"]):
                key_elements["decisions"].append(sentence.strip())
        
        # Build summary
        summary_parts = []
        
        if key_elements["main_topic"]:
            # Truncate main topic if too long
            main_topic = key_elements["main_topic"]
            if len(main_topic.split()) > max_words // 2:
                words = main_topic.split()[:max_words // 2]
                main_topic = ' '.join(words) + "..."
            summary_parts.append(main_topic)
        
        if key_elements["decisions"]:
            summary_parts.append(f"Decision: {key_elements['decisions'][0][:50]}...")
        
        if key_elements["actions"]:
            summary_parts.append(f"Action: {key_elements['actions'][0][:50]}...")
        
        # Join and ensure we stay within word limit
        summary = " | ".join(summary_parts)
        words = summary.split()
        if len(words) > max_words:
            summary = ' '.join(words[:max_words]) + "..."
        
        return summary
    
    @kernel_function(
        name="ExtractInsights",
        description="Extract strategic insights from CEO log entries"
    )
    def extract_insights(
        self,
        entries: Annotated[str, "One or more CEO log entries to analyze (text or JSON array)"],
        focus_area: Annotated[Optional[str], "Specific area to focus on: risks, opportunities, team, market, or general"] = "general"
    ) -> Annotated[str, "Extracted strategic insights with themes and recommendations"]:
        """
        Extract strategic insights from one or more CEO log entries.
        Identifies patterns, themes, and provides recommendations.
        """
        # Parse entries
        if entries.startswith('['):
            try:
                entry_list = json.loads(entries)
            except:
                entry_list = [entries]
        else:
            entry_list = [entries]
        
        # Combine all entries for analysis
        combined_text = ' '.join(entry_list).lower()
        
        insights = {
            "total_entries_analyzed": len(entry_list),
            "focus_area": focus_area,
            "insights": [],
            "themes": [],
            "recommendations": [],
            "metrics": {}
        }
        
        # Focus area specific analysis
        if focus_area == "risks":
            risk_indicators = ["risk", "threat", "concern", "issue", "problem", "challenge"]
            risk_count = sum(1 for indicator in risk_indicators if indicator in combined_text)
            
            if risk_count > 0:
                insights["insights"].append(f"Identified {risk_count} risk-related mentions across entries")
                insights["themes"].append("Risk awareness")
                insights["recommendations"].append("Develop comprehensive risk mitigation framework")
                insights["recommendations"].append("Schedule risk assessment review with leadership team")
            
            insights["metrics"]["risk_mentions"] = risk_count
            
        elif focus_area == "opportunities":
            opp_indicators = ["opportunity", "potential", "growth", "expand", "new market", "innovation"]
            opp_count = sum(1 for indicator in opp_indicators if indicator in combined_text)
            
            if opp_count > 0:
                insights["insights"].append(f"Found {opp_count} opportunity-related discussions")
                insights["themes"].append("Growth mindset")
                insights["recommendations"].append("Create opportunity evaluation matrix")
                insights["recommendations"].append("Allocate resources for high-potential initiatives")
            
            insights["metrics"]["opportunity_mentions"] = opp_count
            
        elif focus_area == "team":
            team_indicators = ["team", "people", "staff", "culture", "talent", "leadership"]
            team_count = sum(1 for indicator in team_indicators if indicator in combined_text)
            
            if team_count > 0:
                insights["insights"].append(f"Team and culture mentioned {team_count} times")
                insights["themes"].append("People focus")
                insights["recommendations"].append("Conduct team health assessment")
                insights["recommendations"].append("Implement leadership development program")
            
            insights["metrics"]["team_mentions"] = team_count
            
        elif focus_area == "market":
            market_indicators = ["market", "customer", "competitor", "industry", "trend"]
            market_count = sum(1 for indicator in market_indicators if indicator in combined_text)
            
            if market_count > 0:
                insights["insights"].append(f"Market dynamics discussed {market_count} times")
                insights["themes"].append("Market awareness")
                insights["recommendations"].append("Commission market analysis report")
                insights["recommendations"].append("Review competitive positioning")
            
            insights["metrics"]["market_mentions"] = market_count
            
        else:  # general analysis
            # Identify common themes
            theme_counts = {
                "Strategic planning": combined_text.count("strateg"),
                "Decision making": combined_text.count("decid") + combined_text.count("decision"),
                "Innovation": combined_text.count("innovat") + combined_text.count("new"),
                "Financial": combined_text.count("financ") + combined_text.count("revenue"),
            }
            
            top_themes = sorted(theme_counts.items(), key=lambda x: x[1], reverse=True)[:3]
            for theme, count in top_themes:
                if count > 0:
                    insights["themes"].append(theme)
            
            insights["insights"].append("CEO focus spans multiple strategic areas")
            insights["recommendations"].append("Maintain balanced attention across all business dimensions")
            insights["metrics"] = theme_counts
        
        # Add general insights
        total_words = len(combined_text.split())
        insights["insights"].append(f"Analyzed {total_words} words across {len(entry_list)} entries")
        
        # Check for urgency
        if any(word in combined_text for word in ["urgent", "immediate", "asap", "critical"]):
            insights["insights"].append("Urgent items detected requiring immediate attention")
            insights["recommendations"].insert(0, "Address urgent items in next leadership meeting")
        
        insights["generated_at"] = datetime.now().isoformat()
        
        return json.dumps(insights, indent=2)
    
    @kernel_function(
        name="SaveEntry",
        description="Save a CEO log entry with metadata and automatic tagging"
    )
    def save_entry(
        self,
        content: Annotated[str, "The CEO log entry content to save"],
        category: Annotated[str, "Category: strategic_planning, team_leadership, market_analysis, risk_assessment, innovation, operations, financial, customer_insights, or general"] = "general",
        is_voice: Annotated[bool, "Whether this entry was transcribed from voice"] = False
    ) -> Annotated[str, "Confirmation of saved entry with ID and metadata"]:
        """
        Save a CEO log entry with automatic tagging and summarization.
        Returns entry ID and processed metadata.
        """
        # Validate category
        if category not in self.categories:
            category = "general"
        
        # Generate unique ID
        entry_id = f"ceo_log_{int(datetime.now().timestamp() * 1000)}"
        
        # Generate tags
        tags_result = json.loads(self.generate_tags(content))
        
        # Generate summary
        summary = self.summarize_entry(content, max_words=30)
        
        # Create entry object
        entry = {
            "id": entry_id,
            "content": content,
            "category": category,
            "is_voice": is_voice,
            "created_at": datetime.now().isoformat(),
            "tags": tags_result["tags"],
            "summary": summary,
            "metadata": {
                "word_count": len(content.split()),
                "has_action_items": tags_result["analysis"]["has_action_items"],
                "is_urgent": tags_result["analysis"]["is_urgent"],
                "involves_risk": tags_result["analysis"]["involves_risk"]
            }
        }
        
        # Store entry
        self.entries.append(entry)
        
        result = {
            "success": True,
            "entry_id": entry_id,
            "message": f"CEO log entry saved successfully in category: {category}",
            "summary": summary,
            "tags": tags_result["tags"][:5],  # Return top 5 tags
            "metadata": entry["metadata"]
        }
        
        return json.dumps(result, indent=2)
    
    @kernel_function(
        name="SearchEntries",
        description="Search CEO log entries by keyword, category, or tags"
    )
    def search_entries(
        self,
        query: Annotated[str, "Search query - can be keywords, tags, or phrases"],
        category: Annotated[Optional[str], "Filter by specific category"] = None,
        limit: Annotated[int, "Maximum number of results to return"] = 5
    ) -> Annotated[str, "Search results with relevance scores"]:
        """
        Search through CEO log entries using keywords, tags, or categories.
        Returns matched entries with relevance scores.
        """
        results = []
        query_lower = query.lower()
        query_words = set(query_lower.split())
        
        for entry in self.entries:
            # Skip if category filter doesn't match
            if category and entry.get("category") != category:
                continue
            
            relevance_score = 0.0
            
            # Check content match
            content_lower = entry["content"].lower()
            content_words = set(content_lower.split())
            
            # Word overlap score
            word_overlap = len(query_words.intersection(content_words))
            if word_overlap > 0:
                relevance_score += word_overlap * 0.3
            
            # Exact phrase match
            if query_lower in content_lower:
                relevance_score += 0.5
            
            # Tag match
            matching_tags = [tag for tag in entry.get("tags", []) if tag in query_lower or query_lower in tag]
            relevance_score += len(matching_tags) * 0.4
            
            # Category match
            if category and entry.get("category") == category:
                relevance_score += 0.2
            
            # Summary match
            if query_lower in entry.get("summary", "").lower():
                relevance_score += 0.3
            
            if relevance_score > 0:
                results.append({
                    "id": entry["id"],
                    "summary": entry["summary"],
                    "category": entry["category"],
                    "tags": entry.get("tags", [])[:3],  # Top 3 tags
                    "created_at": entry["created_at"],
                    "relevance_score": round(relevance_score, 2),
                    "is_voice": entry.get("is_voice", False),
                    "has_action_items": entry.get("metadata", {}).get("has_action_items", False)
                })
        
        # Sort by relevance score
        results.sort(key=lambda x: x["relevance_score"], reverse=True)
        results = results[:limit]
        
        search_summary = {
            "query": query,
            "category_filter": category,
            "total_results": len(results),
            "results": results,
            "search_completed_at": datetime.now().isoformat()
        }
        
        return json.dumps(search_summary, indent=2)