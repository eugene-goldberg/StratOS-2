"""
AI skill for detecting risks and opportunities from various data sources
"""
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from uuid import UUID

from semantic_kernel.skill_definition import sk_function, sk_function_context_parameter
from semantic_kernel.orchestration.sk_context import SKContext

from ....models.alerts import (
    AlertType, AlertSeverity, RiskCategory, OpportunityCategory,
    RiskOpportunityDetectionConfig
)
from ....models.subjective_input import SubjectiveEntry
from ....models.objective_data import DataEntry
from ....models.analysis import Insight, InsightType, SWOTItem

logger = logging.getLogger(__name__)

class RiskOpportunityDetectionSkill:
    """Skill for detecting risks and opportunities using AI analysis"""
    
    @sk_function(
        description="Analyze recent data to detect potential risks",
        name="detect_risks"
    )
    @sk_function_context_parameter(
        name="data",
        description="JSON string containing recent subjective entries, objective data, and insights"
    )
    @sk_function_context_parameter(
        name="config",
        description="JSON string containing detection configuration"
    )
    async def detect_risks(self, context: SKContext) -> str:
        """
        Detect potential risks from recent data
        
        Returns JSON string with detected risks
        """
        try:
            data = json.loads(context.get("data", "{}"))
            config = json.loads(context.get("config", "{}"))
            
            # Prepare data for AI analysis
            analysis_prompt = self._prepare_risk_analysis_prompt(data, config)
            
            # Use the kernel to analyze risks
            kernel = context.kernel
            result = await kernel.run_async(
                kernel.skills.get_function("AnalysisSkills", "AnalyzeRisks"),
                input_str=analysis_prompt
            )
            
            # Parse and structure the results
            risks = self._parse_risk_results(result.result, data)
            
            return json.dumps(risks)
            
        except Exception as e:
            logger.error(f"Error detecting risks: {str(e)}")
            return json.dumps({"error": str(e), "risks": []})
    
    @sk_function(
        description="Analyze recent data to detect potential opportunities",
        name="detect_opportunities"
    )
    @sk_function_context_parameter(
        name="data",
        description="JSON string containing recent subjective entries, objective data, and insights"
    )
    @sk_function_context_parameter(
        name="config",
        description="JSON string containing detection configuration"
    )
    async def detect_opportunities(self, context: SKContext) -> str:
        """
        Detect potential opportunities from recent data
        
        Returns JSON string with detected opportunities
        """
        try:
            data = json.loads(context.get("data", "{}"))
            config = json.loads(context.get("config", "{}"))
            
            # Prepare data for AI analysis
            analysis_prompt = self._prepare_opportunity_analysis_prompt(data, config)
            
            # Use the kernel to analyze opportunities
            kernel = context.kernel
            result = await kernel.run_async(
                kernel.skills.get_function("AnalysisSkills", "AnalyzeOpportunities"),
                input_str=analysis_prompt
            )
            
            # Parse and structure the results
            opportunities = self._parse_opportunity_results(result.result, data)
            
            return json.dumps(opportunities)
            
        except Exception as e:
            logger.error(f"Error detecting opportunities: {str(e)}")
            return json.dumps({"error": str(e), "opportunities": []})
    
    @sk_function(
        description="Calculate risk scores based on impact and likelihood",
        name="calculate_risk_scores"
    )
    @sk_function_context_parameter(
        name="risks",
        description="JSON string containing detected risks"
    )
    async def calculate_risk_scores(self, context: SKContext) -> str:
        """
        Calculate risk scores for detected risks
        
        Returns JSON string with scored risks
        """
        try:
            risks = json.loads(context.get("risks", "[]"))
            
            scored_risks = []
            for risk in risks:
                # Calculate risk score
                impact = risk.get("impact_score", 50)
                likelihood = risk.get("likelihood_score", 50)
                risk_score = (impact * likelihood) / 100
                
                # Determine severity based on risk score
                if risk_score >= 75:
                    severity = AlertSeverity.CRITICAL
                elif risk_score >= 50:
                    severity = AlertSeverity.HIGH
                elif risk_score >= 25:
                    severity = AlertSeverity.MEDIUM
                else:
                    severity = AlertSeverity.LOW
                
                risk["risk_score"] = risk_score
                risk["severity"] = severity
                scored_risks.append(risk)
            
            return json.dumps(scored_risks)
            
        except Exception as e:
            logger.error(f"Error calculating risk scores: {str(e)}")
            return json.dumps({"error": str(e), "risks": []})
    
    def _prepare_risk_analysis_prompt(self, data: Dict[str, Any], config: Dict[str, Any]) -> str:
        """Prepare prompt for risk analysis"""
        prompt = f"""Analyze the following business data to identify potential risks:

Recent Subjective Entries:
{self._format_subjective_entries(data.get("subjective_entries", []))}

Recent Objective Data:
{self._format_objective_data(data.get("objective_data", []))}

Recent Insights:
{self._format_insights(data.get("insights", []))}

SWOT Analysis:
{self._format_swot_items(data.get("swot_items", []))}

Please identify potential risks considering:
1. Financial risks (budget overruns, revenue shortfalls, cost increases)
2. Operational risks (process failures, resource constraints, delays)
3. Strategic risks (market changes, competitive threats, strategic misalignment)
4. Compliance risks (regulatory changes, policy violations)
5. Reputational risks (brand damage, customer dissatisfaction)
6. Technology risks (system failures, cybersecurity threats, obsolescence)
7. Human resource risks (talent loss, skill gaps, morale issues)

For each risk, provide:
- Title: Brief descriptive title
- Description: Detailed explanation
- Category: One of the risk categories above
- Impact Score: 0-100 (how severe if it occurs)
- Likelihood Score: 0-100 (probability of occurrence)
- Indicators: What data points suggest this risk
- Recommendations: Suggested mitigation actions

Focus on risks with confidence above {config.get('min_confidence_score', 70)}%."""
        
        return prompt
    
    def _prepare_opportunity_analysis_prompt(self, data: Dict[str, Any], config: Dict[str, Any]) -> str:
        """Prepare prompt for opportunity analysis"""
        prompt = f"""Analyze the following business data to identify potential opportunities:

Recent Subjective Entries:
{self._format_subjective_entries(data.get("subjective_entries", []))}

Recent Objective Data:
{self._format_objective_data(data.get("objective_data", []))}

Recent Insights:
{self._format_insights(data.get("insights", []))}

SWOT Analysis:
{self._format_swot_items(data.get("swot_items", []))}

Please identify potential opportunities considering:
1. Market expansion (new markets, segments, geographies)
2. Cost reduction (efficiency improvements, automation, optimization)
3. Revenue growth (new products, pricing, upselling)
4. Innovation (new technologies, processes, business models)
5. Partnerships (strategic alliances, acquisitions, collaborations)
6. Competitive advantages (unique capabilities, market positioning)

For each opportunity, provide:
- Title: Brief descriptive title
- Description: Detailed explanation
- Category: One of the opportunity categories above
- Impact Score: 0-100 (potential positive impact)
- Likelihood Score: 0-100 (probability of success)
- Indicators: What data points suggest this opportunity
- Recommendations: Suggested actions to capture

Focus on opportunities with confidence above {config.get('min_confidence_score', 70)}%."""
        
        return prompt
    
    def _format_subjective_entries(self, entries: List[Dict[str, Any]]) -> str:
        """Format subjective entries for the prompt"""
        if not entries:
            return "No recent subjective entries."
        
        formatted = []
        for entry in entries[:10]:  # Limit to recent 10
            formatted.append(f"- {entry.get('entry_date', 'Unknown date')}: {entry.get('content', '')}")
        
        return "\n".join(formatted)
    
    def _format_objective_data(self, data: List[Dict[str, Any]]) -> str:
        """Format objective data for the prompt"""
        if not data:
            return "No recent objective data."
        
        formatted = []
        for item in data[:10]:  # Limit to recent 10
            formatted.append(
                f"- {item.get('name', 'Unknown')}: {item.get('value', '')} "
                f"({item.get('data_type', 'Unknown type')})"
            )
        
        return "\n".join(formatted)
    
    def _format_insights(self, insights: List[Dict[str, Any]]) -> str:
        """Format insights for the prompt"""
        if not insights:
            return "No recent insights."
        
        formatted = []
        for insight in insights[:10]:  # Limit to recent 10
            formatted.append(
                f"- [{insight.get('insight_type', 'Unknown')}] {insight.get('title', '')}: "
                f"{insight.get('content', '')}"
            )
        
        return "\n".join(formatted)
    
    def _format_swot_items(self, items: List[Dict[str, Any]]) -> str:
        """Format SWOT items for the prompt"""
        if not items:
            return "No SWOT analysis available."
        
        by_category = {"strengths": [], "weaknesses": [], "opportunities": [], "threats": []}
        
        for item in items:
            category = item.get('category', '').lower()
            if category in by_category:
                by_category[category].append(f"- {item.get('content', '')}")
        
        formatted = []
        for category, items in by_category.items():
            if items:
                formatted.append(f"{category.title()}:\n" + "\n".join(items))
        
        return "\n\n".join(formatted)
    
    def _parse_risk_results(self, ai_result: str, original_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse AI results into structured risk data"""
        # This is a simplified parser - in production, you'd want more robust parsing
        risks = []
        
        try:
            # Attempt to parse as JSON first
            parsed = json.loads(ai_result)
            if isinstance(parsed, list):
                risks = parsed
            elif isinstance(parsed, dict) and "risks" in parsed:
                risks = parsed["risks"]
        except:
            # Fall back to text parsing if not JSON
            # This would need more sophisticated parsing logic
            pass
        
        return risks
    
    def _parse_opportunity_results(self, ai_result: str, original_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse AI results into structured opportunity data"""
        # This is a simplified parser - in production, you'd want more robust parsing
        opportunities = []
        
        try:
            # Attempt to parse as JSON first
            parsed = json.loads(ai_result)
            if isinstance(parsed, list):
                opportunities = parsed
            elif isinstance(parsed, dict) and "opportunities" in parsed:
                opportunities = parsed["opportunities"]
        except:
            # Fall back to text parsing if not JSON
            # This would need more sophisticated parsing logic
            pass
        
        return opportunities