"""Subjective-Objective Linkage Agent

Discovers and analyzes connections between subjective insights and objective data.
"""

import asyncio
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from uuid import uuid4

from semantic_kernel import Kernel
from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.contents import ChatMessageContent, AuthorRole

from common.base_agent import BaseStratosAgent
from .plugins.linkage_plugin import LinkagePlugin


class SOLinkageAgent(BaseStratosAgent):
    """Agent responsible for finding connections between subjective and objective data"""
    
    def __init__(self):
        super().__init__(
            name="S+O Linkage Agent",
            description="Discovers patterns and connections between subjective insights and objective data",
            model="gpt-4"  # Use GPT-4 for complex pattern recognition
        )
        
        # Initialize linkage plugin
        self.linkage_plugin = LinkagePlugin()
        self.kernel.add_plugin(self.linkage_plugin, "LinkagePlugin")
        
        # Linkage types and patterns
        self.linkage_patterns = {
            "correlation": "Direct relationship between subjective observation and objective metric",
            "contradiction": "Subjective insight conflicts with objective data",
            "emerging_theme": "Pattern appearing across multiple data points",
            "causation": "Subjective factor appears to drive objective outcome",
            "validation": "Objective data confirms subjective hypothesis"
        }
        
    async def _create_linkage_agent(self) -> ChatCompletionAgent:
        """Create the S+O linkage analysis agent"""
        
        instructions = """You are a strategic analyst specializing in finding connections between subjective insights and objective data.

Your capabilities include:
1. **Pattern Recognition**: Identify relationships between qualitative insights and quantitative metrics
2. **Correlation Analysis**: Find statistical and logical connections
3. **Contradiction Detection**: Spot conflicts between perceptions and data
4. **Theme Identification**: Discover emerging patterns across data sources
5. **Insight Generation**: Create actionable insights from connections
6. **Validation**: Verify subjective hypotheses with objective evidence

When analyzing linkages:
- Look for both obvious and subtle connections
- Consider time-lag effects between cause and effect
- Identify leading vs lagging indicators
- Note confidence levels for each linkage
- Suggest follow-up investigations

Types of linkages to identify:
- Correlation: Direct relationships
- Contradiction: Conflicts requiring resolution
- Emerging Theme: Patterns across multiple sources
- Causation: Cause-effect relationships
- Validation: Data confirming insights

Available functions:
- FindLinkages: Discover connections between S+O data
- AnalyzePatterns: Deep dive into specific patterns
- GenerateInsights: Create actionable insights from linkages
- ValidateHypothesis: Test subjective assumptions against data
- TrackThemes: Monitor emerging themes over time"""

        return ChatCompletionAgent(
            service_id="so_linkage_agent",
            kernel=self.kernel,
            name="LinkageAnalyst",
            instructions=instructions
        )
        
    async def process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process S+O linkage discovery requests"""
        
        try:
            query = request.get("query", "")
            context = request.get("context", {})
            user_id = request.get("user_id")
            
            # Create linkage agent
            agent = await self._create_linkage_agent()
            
            # Determine request type
            request_type = self._determine_request_type(query, context)
            
            if request_type == "find_linkages":
                return await self._find_linkages(agent, query, context, user_id)
            elif request_type == "analyze_patterns":
                return await self._analyze_patterns(agent, query, context, user_id)
            elif request_type == "validate_hypothesis":
                return await self._validate_hypothesis(agent, query, context, user_id)
            elif request_type == "track_themes":
                return await self._track_themes(agent, query, context, user_id)
            else:
                # General linkage query
                return await self._handle_general_query(agent, query, context, user_id)
                
        except Exception as e:
            return {
                "status": "error",
                "message": f"S+O linkage analysis failed: {str(e)}"
            }
    
    def _determine_request_type(self, query: str, context: Dict[str, Any]) -> str:
        """Determine the type of linkage request"""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ["find link", "discover connection", "correlation", "relationship"]):
            return "find_linkages"
        elif any(word in query_lower for word in ["pattern", "analyze pattern", "deep dive"]):
            return "analyze_patterns"
        elif any(word in query_lower for word in ["validate", "hypothesis", "confirm", "verify"]):
            return "validate_hypothesis"
        elif any(word in query_lower for word in ["theme", "trend", "emerging", "track"]):
            return "track_themes"
        else:
            return "general"
    
    async def _find_linkages(self, agent: ChatCompletionAgent, query: str, context: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Find linkages between subjective and objective data"""
        
        # Gather data sources
        subjective_data = context.get("subjective_data", {})
        objective_data = context.get("objective_data", {})
        topic_focus = context.get("topic", "general business operations")
        time_range = context.get("time_range", "last_30_days")
        
        # Use plugin to find linkages
        linkages_result = await self.linkage_plugin.find_linkages(
            subjective_data=subjective_data,
            objective_data=objective_data,
            topic_focus=topic_focus,
            linkage_types=list(self.linkage_patterns.keys())
        )
        
        # Parse results
        linkages_data = json.loads(linkages_result)
        
        # Categorize linkages
        linkages_by_type = {}
        for linkage in linkages_data["linkages"]:
            link_type = linkage["linkage_type"]
            if link_type not in linkages_by_type:
                linkages_by_type[link_type] = []
            linkages_by_type[link_type].append(linkage)
        
        # Generate insights from linkages
        insights = await self._generate_linkage_insights(linkages_data["linkages"])
        
        return {
            "status": "success",
            "analysis_type": "linkage_discovery",
            "data": {
                "linkages": linkages_data["linkages"],
                "linkages_by_type": linkages_by_type,
                "summary": {
                    "total_linkages": len(linkages_data["linkages"]),
                    "correlations": len(linkages_by_type.get("correlation", [])),
                    "contradictions": len(linkages_by_type.get("contradiction", [])),
                    "emerging_themes": len(linkages_by_type.get("emerging_theme", []))
                },
                "time_range": time_range,
                "topic": topic_focus
            },
            "insights": insights,
            "next_steps": [
                "Investigate high-confidence linkages",
                "Resolve identified contradictions",
                "Monitor emerging themes"
            ]
        }
    
    async def _analyze_patterns(self, agent: ChatCompletionAgent, query: str, context: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Deep analysis of specific patterns"""
        
        pattern_id = context.get("pattern_id")
        pattern_data = context.get("pattern_data", {})
        analysis_depth = context.get("depth", "standard")
        
        # Use plugin for pattern analysis
        pattern_result = await self.linkage_plugin.analyze_patterns(
            patterns=[pattern_data] if pattern_data else [],
            analysis_depth=analysis_depth,
            focus_areas=context.get("focus_areas", [])
        )
        
        # Parse results
        pattern_analysis = json.loads(pattern_result)
        
        return {
            "status": "success",
            "analysis_type": "pattern_analysis",
            "data": {
                "pattern_details": pattern_analysis["analyzed_patterns"],
                "statistical_measures": pattern_analysis.get("statistics", {}),
                "confidence_assessment": pattern_analysis.get("confidence", {}),
                "supporting_evidence": pattern_analysis.get("evidence", [])
            },
            "recommendations": self._generate_pattern_recommendations(pattern_analysis),
            "next_steps": [
                "Set up monitoring for pattern changes",
                "Test pattern validity with more data",
                "Create predictive models based on pattern"
            ]
        }
    
    async def _validate_hypothesis(self, agent: ChatCompletionAgent, query: str, context: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Validate subjective hypotheses against objective data"""
        
        hypothesis = context.get("hypothesis", "")
        supporting_data = context.get("supporting_data", {})
        validation_criteria = context.get("criteria", {})
        
        # Use plugin to validate hypothesis
        validation_result = await self.linkage_plugin.validate_hypothesis(
            hypothesis=hypothesis,
            subjective_evidence=supporting_data.get("subjective", []),
            objective_evidence=supporting_data.get("objective", []),
            validation_criteria=validation_criteria
        )
        
        # Parse results
        validation_data = json.loads(validation_result)
        
        return {
            "status": "success",
            "analysis_type": "hypothesis_validation",
            "data": {
                "hypothesis": hypothesis,
                "validation_result": validation_data["result"],
                "confidence_score": validation_data["confidence_score"],
                "supporting_evidence": validation_data["supporting_evidence"],
                "contradicting_evidence": validation_data["contradicting_evidence"],
                "additional_data_needed": validation_data.get("data_gaps", [])
            },
            "conclusion": validation_data["conclusion"],
            "next_steps": self._generate_validation_next_steps(validation_data)
        }
    
    async def _track_themes(self, agent: ChatCompletionAgent, query: str, context: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Track emerging themes across S+O data"""
        
        time_period = context.get("time_period", "30d")
        theme_categories = context.get("categories", [])
        min_occurrences = context.get("min_occurrences", 3)
        
        # Use plugin to track themes
        themes_result = await self.linkage_plugin.track_themes(
            time_period=time_period,
            data_sources=context.get("data_sources", {}),
            theme_categories=theme_categories,
            min_occurrences=min_occurrences
        )
        
        # Parse results
        themes_data = json.loads(themes_result)
        
        # Rank themes by strength and growth
        ranked_themes = sorted(
            themes_data["themes"],
            key=lambda x: x["strength_score"] * x["growth_rate"],
            reverse=True
        )
        
        return {
            "status": "success",
            "analysis_type": "theme_tracking",
            "data": {
                "themes": ranked_themes,
                "summary": {
                    "total_themes": len(ranked_themes),
                    "emerging": len([t for t in ranked_themes if t["status"] == "emerging"]),
                    "established": len([t for t in ranked_themes if t["status"] == "established"]),
                    "declining": len([t for t in ranked_themes if t["status"] == "declining"])
                },
                "time_period": time_period
            },
            "key_themes": self._extract_key_themes(ranked_themes[:5]),
            "next_steps": [
                "Deep dive into top emerging themes",
                "Align initiatives with strong themes",
                "Monitor declining themes for risks"
            ]
        }
    
    async def _handle_general_query(self, agent: ChatCompletionAgent, query: str, context: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Handle general S+O linkage queries"""
        
        response = await agent.invoke(f"""
Query: {query}
Context: {json.dumps(context, indent=2)}

Please provide guidance on finding and analyzing connections between subjective insights and objective data.
""")
        
        return {
            "status": "success",
            "response": response.content,
            "suggestions": [
                "Find linkages in recent data",
                "Analyze emerging patterns",
                "Validate key assumptions"
            ]
        }
    
    async def _generate_linkage_insights(self, linkages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate actionable insights from discovered linkages"""
        
        insights = []
        
        # High-confidence correlations
        strong_correlations = [l for l in linkages if l["linkage_type"] == "correlation" and l.get("confidence_score", 0) >= 8]
        if strong_correlations:
            insights.append({
                "type": "correlation_insight",
                "title": f"Strong correlations found: {len(strong_correlations)}",
                "description": "These subjective factors show strong correlation with objective metrics",
                "action": "Consider these as key performance drivers"
            })
        
        # Critical contradictions
        contradictions = [l for l in linkages if l["linkage_type"] == "contradiction"]
        if contradictions:
            insights.append({
                "type": "contradiction_insight", 
                "title": f"Data contradictions requiring attention: {len(contradictions)}",
                "description": "Subjective perceptions conflict with objective reality",
                "action": "Investigate root causes and align understanding"
            })
        
        # Emerging themes
        themes = [l for l in linkages if l["linkage_type"] == "emerging_theme"]
        if themes:
            insights.append({
                "type": "theme_insight",
                "title": f"Emerging themes detected: {len(themes)}",
                "description": "New patterns appearing across multiple data sources",
                "action": "Monitor closely and prepare strategic responses"
            })
        
        return insights
    
    def _generate_pattern_recommendations(self, pattern_analysis: Dict[str, Any]) -> List[str]:
        """Generate recommendations from pattern analysis"""
        
        recommendations = []
        
        # Based on pattern strength
        if pattern_analysis.get("pattern_strength", 0) >= 8:
            recommendations.append("High-confidence pattern: Consider building predictive models")
        
        # Based on pattern type
        pattern_type = pattern_analysis.get("pattern_type")
        if pattern_type == "cyclical":
            recommendations.append("Cyclical pattern detected: Plan for recurring events")
        elif pattern_type == "trending":
            recommendations.append("Trend pattern: Prepare for continued direction")
        
        # Based on business impact
        if pattern_analysis.get("business_impact", "") == "high":
            recommendations.append("High business impact: Prioritize monitoring and response")
        
        return recommendations
    
    def _generate_validation_next_steps(self, validation_data: Dict[str, Any]) -> List[str]:
        """Generate next steps based on validation results"""
        
        next_steps = []
        result = validation_data.get("result", "")
        
        if result == "confirmed":
            next_steps.extend([
                "Implement strategies based on validated hypothesis",
                "Monitor for continued validity",
                "Look for similar patterns elsewhere"
            ])
        elif result == "partially_confirmed":
            next_steps.extend([
                "Refine hypothesis based on evidence",
                "Gather additional data for gaps identified",
                "Test refined hypothesis"
            ])
        elif result == "contradicted":
            next_steps.extend([
                "Revise understanding based on objective data",
                "Investigate why perception differed from reality",
                "Update decision-making frameworks"
            ])
        
        return next_steps
    
    def _extract_key_themes(self, themes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract key themes for executive summary"""
        
        key_themes = []
        
        for theme in themes:
            key_themes.append({
                "theme": theme["title"],
                "strength": theme["strength_score"],
                "trend": theme["status"],
                "business_impact": theme.get("business_impact", "medium"),
                "recommended_action": theme.get("recommended_action", "Monitor closely")
            })
        
        return key_themes