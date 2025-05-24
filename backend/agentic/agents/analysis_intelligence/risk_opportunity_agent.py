"""Risk/Opportunity Detection Agent

Identifies, analyzes, and monitors risks and opportunities from various data sources.
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
from .plugins.risk_plugin import RiskPlugin


class RiskOpportunityAgent(BaseStratosAgent):
    """Agent responsible for risk and opportunity detection and analysis"""
    
    def __init__(self):
        super().__init__(
            name="Risk/Opportunity Detection Agent",
            description="Detects, analyzes, and monitors risks and opportunities",
            model="gpt-4"  # Use GPT-4 for complex risk analysis
        )
        
        # Initialize risk plugin
        self.risk_plugin = RiskPlugin()
        self.kernel.add_plugin(self.risk_plugin, "RiskPlugin")
        
        # Alert thresholds
        self.alert_thresholds = {
            "risk": {
                "high": 8,
                "medium": 5,
                "low": 3
            },
            "opportunity": {
                "high": 8,
                "medium": 5,
                "low": 3
            }
        }
        
    async def _create_risk_agent(self) -> ChatCompletionAgent:
        """Create the risk/opportunity analysis agent"""
        
        instructions = """You are a strategic risk and opportunity analyst specializing in business intelligence.

Your capabilities include:
1. **Risk Detection**: Identify potential risks from various data sources
2. **Opportunity Identification**: Spot emerging opportunities in markets and operations
3. **Impact Assessment**: Evaluate probability and potential impact
4. **Trend Analysis**: Detect patterns indicating future risks/opportunities
5. **Alert Generation**: Create actionable alerts for critical findings
6. **Mitigation Strategies**: Suggest risk mitigation and opportunity capture strategies

When analyzing risks:
- Consider internal and external factors
- Assess likelihood (1-10) and impact (1-10)
- Identify early warning indicators
- Suggest mitigation strategies
- Flag interconnected risks

When identifying opportunities:
- Look for market gaps and trends
- Assess feasibility and potential returns
- Consider resource requirements
- Identify time-sensitive opportunities
- Link to strategic objectives

Available functions:
- DetectRisks: Analyze data for potential risks
- IdentifyOpportunities: Find growth and improvement opportunities
- AssessImpact: Evaluate probability and impact scores
- GenerateAlerts: Create alerts for high-priority items
- SuggestMitigation: Provide risk mitigation strategies
- MonitorTrends: Track risk/opportunity indicators over time"""

        return ChatCompletionAgent(
            service_id="risk_opportunity_agent",
            kernel=self.kernel,
            name="RiskOpportunityAnalyst",
            instructions=instructions
        )
        
    async def process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process risk/opportunity detection requests"""
        
        try:
            query = request.get("query", "")
            context = request.get("context", {})
            user_id = request.get("user_id")
            
            # Create risk agent
            agent = await self._create_risk_agent()
            
            # Determine request type
            request_type = self._determine_request_type(query, context)
            
            if request_type == "detect_risks":
                return await self._detect_risks(agent, query, context, user_id)
            elif request_type == "find_opportunities":
                return await self._find_opportunities(agent, query, context, user_id)
            elif request_type == "assess_impact":
                return await self._assess_impact(agent, query, context, user_id)
            elif request_type == "generate_alerts":
                return await self._generate_alerts(agent, query, context, user_id)
            elif request_type == "monitor_trends":
                return await self._monitor_trends(agent, query, context, user_id)
            else:
                # General risk/opportunity query
                return await self._handle_general_query(agent, query, context, user_id)
                
        except Exception as e:
            return {
                "status": "error",
                "message": f"Risk/opportunity analysis failed: {str(e)}"
            }
    
    def _determine_request_type(self, query: str, context: Dict[str, Any]) -> str:
        """Determine the type of risk/opportunity request"""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ["detect risk", "identify risk", "find risk", "risk analysis"]):
            return "detect_risks"
        elif any(word in query_lower for word in ["opportunity", "find opportunity", "growth", "potential"]):
            return "find_opportunities"
        elif any(word in query_lower for word in ["assess", "impact", "probability", "score"]):
            return "assess_impact"
        elif any(word in query_lower for word in ["alert", "warning", "critical", "urgent"]):
            return "generate_alerts"
        elif any(word in query_lower for word in ["trend", "monitor", "track", "pattern"]):
            return "monitor_trends"
        else:
            return "general"
    
    async def _detect_risks(self, agent: ChatCompletionAgent, query: str, context: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Detect risks from various data sources"""
        
        # Gather data sources
        data_sources = context.get("data_sources", {})
        risk_category = context.get("category", "all")
        time_horizon = context.get("time_horizon", "short_term")
        
        # Use plugin to detect risks
        risks_result = await self.risk_plugin.detect_risks(
            data_sources=data_sources,
            risk_category=risk_category,
            time_horizon=time_horizon,
            user_id=user_id
        )
        
        # Parse results
        risks_data = json.loads(risks_result)
        
        # Categorize risks by severity
        high_risks = [r for r in risks_data["risks"] if r["impact_score"] >= self.alert_thresholds["risk"]["high"]]
        medium_risks = [r for r in risks_data["risks"] if self.alert_thresholds["risk"]["medium"] <= r["impact_score"] < self.alert_thresholds["risk"]["high"]]
        low_risks = [r for r in risks_data["risks"] if r["impact_score"] < self.alert_thresholds["risk"]["medium"]]
        
        # Generate alerts for high risks
        alerts = []
        for risk in high_risks:
            alert = await self._create_risk_alert(risk, user_id)
            alerts.append(alert)
        
        return {
            "status": "success",
            "analysis_type": "risk_detection",
            "data": {
                "risks": risks_data["risks"],
                "summary": {
                    "total": len(risks_data["risks"]),
                    "high": len(high_risks),
                    "medium": len(medium_risks),
                    "low": len(low_risks)
                },
                "alerts": alerts,
                "analysis_metadata": risks_data["metadata"]
            },
            "recommendations": self._generate_risk_recommendations(risks_data["risks"]),
            "next_steps": [
                "Create mitigation plans for high-priority risks",
                "Set up monitoring for risk indicators",
                "Link risks to strategic initiatives"
            ]
        }
    
    async def _find_opportunities(self, agent: ChatCompletionAgent, query: str, context: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Identify opportunities from data analysis"""
        
        # Gather context
        data_sources = context.get("data_sources", {})
        opportunity_type = context.get("type", "all")
        strategic_focus = context.get("strategic_focus", [])
        
        # Use plugin to identify opportunities
        opportunities_result = await self.risk_plugin.identify_opportunities(
            data_sources=data_sources,
            opportunity_type=opportunity_type,
            strategic_focus=strategic_focus
        )
        
        # Parse results
        opportunities_data = json.loads(opportunities_result)
        
        # Rank opportunities by potential
        ranked_opportunities = sorted(
            opportunities_data["opportunities"],
            key=lambda x: x["potential_score"] * x["feasibility_score"],
            reverse=True
        )
        
        return {
            "status": "success",
            "analysis_type": "opportunity_identification",
            "data": {
                "opportunities": ranked_opportunities,
                "summary": {
                    "total": len(ranked_opportunities),
                    "high_potential": len([o for o in ranked_opportunities if o["potential_score"] >= 8]),
                    "quick_wins": len([o for o in ranked_opportunities if o["time_to_value"] == "short"])
                },
                "analysis_metadata": opportunities_data["metadata"]
            },
            "recommendations": self._generate_opportunity_recommendations(ranked_opportunities[:5]),
            "next_steps": [
                "Evaluate resource requirements",
                "Create business cases for top opportunities",
                "Align with strategic objectives"
            ]
        }
    
    async def _assess_impact(self, agent: ChatCompletionAgent, query: str, context: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Assess impact and probability of risks/opportunities"""
        
        items = context.get("items", [])
        assessment_type = context.get("type", "risk")
        
        # Use plugin to assess impact
        assessment_result = await self.risk_plugin.assess_impact(
            items=items,
            assessment_type=assessment_type,
            criteria=context.get("criteria", {})
        )
        
        # Parse results
        assessment_data = json.loads(assessment_result)
        
        # Create risk/opportunity matrix
        matrix = self._create_impact_matrix(assessment_data["assessed_items"])
        
        return {
            "status": "success",
            "analysis_type": "impact_assessment",
            "data": {
                "assessed_items": assessment_data["assessed_items"],
                "matrix": matrix,
                "scoring_methodology": assessment_data["methodology"]
            },
            "insights": self._generate_impact_insights(assessment_data["assessed_items"]),
            "next_steps": [
                "Focus on high-impact, high-probability items",
                "Develop contingency plans",
                "Allocate resources based on priorities"
            ]
        }
    
    async def _generate_alerts(self, agent: ChatCompletionAgent, query: str, context: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Generate alerts for critical risks and time-sensitive opportunities"""
        
        # Get recent analysis results
        analysis_window = context.get("window", "24h")
        alert_types = context.get("types", ["risk", "opportunity"])
        
        # Use plugin to generate alerts
        alerts_result = await self.risk_plugin.generate_alerts(
            analysis_window=analysis_window,
            alert_types=alert_types,
            user_id=user_id,
            thresholds=self.alert_thresholds
        )
        
        # Parse results
        alerts_data = json.loads(alerts_result)
        
        # Prioritize alerts
        critical_alerts = [a for a in alerts_data["alerts"] if a["priority"] == "critical"]
        high_alerts = [a for a in alerts_data["alerts"] if a["priority"] == "high"]
        medium_alerts = [a for a in alerts_data["alerts"] if a["priority"] == "medium"]
        
        return {
            "status": "success",
            "analysis_type": "alert_generation",
            "data": {
                "alerts": alerts_data["alerts"],
                "summary": {
                    "total": len(alerts_data["alerts"]),
                    "critical": len(critical_alerts),
                    "high": len(high_alerts),
                    "medium": len(medium_alerts)
                }
            },
            "immediate_actions": self._generate_alert_actions(critical_alerts),
            "next_steps": [
                "Address critical alerts immediately",
                "Set up alert notifications",
                "Review and update alert thresholds"
            ]
        }
    
    async def _monitor_trends(self, agent: ChatCompletionAgent, query: str, context: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Monitor trends in risks and opportunities over time"""
        
        # Get monitoring parameters
        time_period = context.get("period", "30d")
        indicators = context.get("indicators", [])
        categories = context.get("categories", ["all"])
        
        # Use plugin to analyze trends
        trends_result = await self.risk_plugin.monitor_trends(
            time_period=time_period,
            indicators=indicators,
            categories=categories,
            user_id=user_id
        )
        
        # Parse results
        trends_data = json.loads(trends_result)
        
        # Identify significant changes
        emerging_risks = [t for t in trends_data["trends"] if t["type"] == "risk" and t["direction"] == "increasing"]
        emerging_opportunities = [t for t in trends_data["trends"] if t["type"] == "opportunity" and t["direction"] == "increasing"]
        
        return {
            "status": "success",
            "analysis_type": "trend_monitoring",
            "data": {
                "trends": trends_data["trends"],
                "indicators": trends_data["indicators"],
                "summary": {
                    "emerging_risks": len(emerging_risks),
                    "emerging_opportunities": len(emerging_opportunities),
                    "stable_items": len([t for t in trends_data["trends"] if t["direction"] == "stable"])
                }
            },
            "insights": trends_data["insights"],
            "next_steps": [
                "Investigate emerging trends",
                "Update risk registers",
                "Adjust strategic plans based on trends"
            ]
        }
    
    async def _handle_general_query(self, agent: ChatCompletionAgent, query: str, context: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Handle general risk/opportunity queries"""
        
        response = await agent.invoke(f"""
Query: {query}
Context: {json.dumps(context, indent=2)}

Please provide risk and opportunity analysis guidance or answer the question.
""")
        
        return {
            "status": "success",
            "response": response.content,
            "suggestions": [
                "Run comprehensive risk assessment",
                "Identify strategic opportunities",
                "Set up risk monitoring dashboard"
            ]
        }
    
    async def _create_risk_alert(self, risk: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Create an alert for a high-priority risk"""
        
        return {
            "id": str(uuid4()),
            "user_id": user_id,
            "type": "risk_alert",
            "priority": "high" if risk["impact_score"] >= 9 else "medium",
            "title": risk["title"],
            "description": risk["description"],
            "impact_score": risk["impact_score"],
            "probability_score": risk["probability_score"],
            "mitigation_required": True,
            "created_at": datetime.utcnow().isoformat(),
            "expires_at": None  # Set based on risk time horizon
        }
    
    def _generate_risk_recommendations(self, risks: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations based on detected risks"""
        
        recommendations = []
        
        # Focus on high-impact risks
        high_impact_risks = [r for r in risks if r.get("impact_score", 0) >= 7]
        if high_impact_risks:
            recommendations.append(f"Prioritize mitigation for {len(high_impact_risks)} high-impact risks")
        
        # Check for systemic risks
        categories = {}
        for risk in risks:
            cat = risk.get("category", "other")
            categories[cat] = categories.get(cat, 0) + 1
        
        for cat, count in categories.items():
            if count >= 3:
                recommendations.append(f"Address systemic issues in {cat} category ({count} risks)")
        
        # Time-sensitive risks
        urgent_risks = [r for r in risks if r.get("time_horizon") == "immediate"]
        if urgent_risks:
            recommendations.append(f"Take immediate action on {len(urgent_risks)} time-critical risks")
        
        return recommendations[:5]  # Top 5 recommendations
    
    def _generate_opportunity_recommendations(self, opportunities: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations for top opportunities"""
        
        recommendations = []
        
        for opp in opportunities[:3]:  # Top 3 opportunities
            if opp.get("time_to_value") == "short":
                recommendations.append(f"Quick win: {opp['title']} (potential score: {opp['potential_score']})")
            else:
                recommendations.append(f"Strategic opportunity: {opp['title']} (potential score: {opp['potential_score']})")
        
        return recommendations
    
    def _create_impact_matrix(self, items: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Create impact/probability matrix"""
        
        matrix = {
            "high_impact_high_prob": [],
            "high_impact_low_prob": [],
            "low_impact_high_prob": [],
            "low_impact_low_prob": []
        }
        
        for item in items:
            impact = item.get("impact_score", 5)
            probability = item.get("probability_score", 5)
            
            if impact >= 7 and probability >= 7:
                matrix["high_impact_high_prob"].append(item)
            elif impact >= 7 and probability < 7:
                matrix["high_impact_low_prob"].append(item)
            elif impact < 7 and probability >= 7:
                matrix["low_impact_high_prob"].append(item)
            else:
                matrix["low_impact_low_prob"].append(item)
        
        return matrix
    
    def _generate_impact_insights(self, items: List[Dict[str, Any]]) -> List[str]:
        """Generate insights from impact assessment"""
        
        insights = []
        
        # High impact/high probability items
        critical_items = [i for i in items if i.get("impact_score", 0) >= 7 and i.get("probability_score", 0) >= 7]
        if critical_items:
            insights.append(f"{len(critical_items)} items require immediate attention (high impact + high probability)")
        
        # Average scores
        if items:
            avg_impact = sum(i.get("impact_score", 0) for i in items) / len(items)
            avg_prob = sum(i.get("probability_score", 0) for i in items) / len(items)
            insights.append(f"Average impact score: {avg_impact:.1f}, Average probability: {avg_prob:.1f}")
        
        return insights
    
    def _generate_alert_actions(self, alerts: List[Dict[str, Any]]) -> List[str]:
        """Generate immediate actions for critical alerts"""
        
        actions = []
        
        for alert in alerts[:3]:  # Top 3 critical alerts
            if alert.get("type") == "risk_alert":
                actions.append(f"Mitigate risk: {alert['title']} (Priority: {alert['priority']})")
            elif alert.get("type") == "opportunity_alert":
                actions.append(f"Capture opportunity: {alert['title']} (Time-sensitive)")
        
        return actions