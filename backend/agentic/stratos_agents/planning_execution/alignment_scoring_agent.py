"""Alignment Scoring Agent

Evaluates strategic alignment between initiatives, goals, and North Star elements.
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
from .plugins.alignment_plugin import AlignmentPlugin


class AlignmentScoringAgent(BaseStratosAgent):
    """Agent responsible for scoring and validating strategic alignment"""
    
    def __init__(self):
        super().__init__(
            name="Alignment Scoring Agent",
            description="Evaluates strategic alignment and validates plans against North Star",
            model="gpt-4"  # Use GPT-4 for nuanced alignment analysis
        )
        
        # Initialize alignment plugin
        self.alignment_plugin = AlignmentPlugin()
        self.kernel.add_plugin(self.alignment_plugin, "AlignmentPlugin")
        
        # Alignment dimensions
        self.alignment_dimensions = {
            "strategic": {
                "weight": 0.3,
                "factors": ["vision_alignment", "goal_support", "value_consistency"]
            },
            "operational": {
                "weight": 0.25,
                "factors": ["resource_efficiency", "capability_match", "timeline_feasibility"]
            },
            "market": {
                "weight": 0.25,
                "factors": ["customer_value", "competitive_advantage", "market_timing"]
            },
            "financial": {
                "weight": 0.2,
                "factors": ["roi_potential", "budget_alignment", "risk_return_profile"]
            }
        }
        
    async def _create_alignment_agent(self) -> ChatCompletionAgent:
        """Create the alignment scoring agent with specific instructions"""
        
        instructions = """You are a strategic alignment expert specializing in evaluating organizational coherence.

Your capabilities include:
1. **Alignment Scoring**: Evaluate how well initiatives align with strategic objectives
2. **Gap Analysis**: Identify misalignments and strategic gaps
3. **Impact Assessment**: Measure potential impact on organizational goals
4. **Recommendation Generation**: Suggest improvements for better alignment
5. **Portfolio Optimization**: Balance initiative portfolio for maximum strategic value
6. **Risk Evaluation**: Assess alignment-related risks

When scoring alignment:
- Consider multiple dimensions (strategic, operational, market, financial)
- Use quantitative and qualitative factors
- Provide actionable feedback
- Highlight both strengths and gaps
- Consider interdependencies
- Think long-term sustainability

Scoring methodology:
- 0-100 scale for overall alignment
- Multi-dimensional assessment
- Evidence-based scoring
- Clear rationale for scores
- Improvement pathways

Available functions:
- ScoreAlignment: Calculate alignment scores
- AnalyzeGaps: Identify alignment gaps
- CompareAlternatives: Compare alignment of options
- OptimizePortfolio: Optimize initiative mix
- ValidatePlan: Validate against North Star
- GenerateHeatmap: Create alignment visualization"""

        return ChatCompletionAgent(
            service_id="alignment_agent",
            kernel=self.kernel,
            name="AlignmentExpert",
            instructions=instructions
        )
        
    async def process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process alignment scoring requests"""
        
        try:
            query = request.get("query", "")
            context = request.get("context", {})
            user_id = request.get("user_id")
            
            # Create alignment agent
            agent = await self._create_alignment_agent()
            
            # Determine request type
            request_type = self._determine_request_type(query, context)
            
            if request_type == "score_alignment":
                return await self._score_alignment(agent, query, context, user_id)
            elif request_type == "analyze_gaps":
                return await self._analyze_gaps(agent, query, context, user_id)
            elif request_type == "compare_alternatives":
                return await self._compare_alternatives(agent, query, context, user_id)
            elif request_type == "optimize_portfolio":
                return await self._optimize_portfolio(agent, query, context, user_id)
            elif request_type == "validate_plan":
                return await self._validate_plan(agent, query, context, user_id)
            else:
                # General alignment query
                return await self._handle_general_query(agent, query, context, user_id)
                
        except Exception as e:
            return {
                "status": "error",
                "message": f"Alignment scoring failed: {str(e)}"
            }
    
    def _determine_request_type(self, query: str, context: Dict[str, Any]) -> str:
        """Determine the type of alignment request"""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ["score", "evaluate", "assess alignment"]):
            return "score_alignment"
        elif any(word in query_lower for word in ["gap", "missing", "misalignment"]):
            return "analyze_gaps"
        elif any(word in query_lower for word in ["compare", "alternatives", "options"]):
            return "compare_alternatives"
        elif any(word in query_lower for word in ["optimize", "portfolio", "balance"]):
            return "optimize_portfolio"
        elif any(word in query_lower for word in ["validate", "check", "verify"]):
            return "validate_plan"
        else:
            return "general"
    
    async def _score_alignment(self, agent: ChatCompletionAgent, query: str, context: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Score alignment of initiatives with strategic objectives"""
        
        # Gather scoring inputs
        initiative = context.get("initiative", {})
        north_star = context.get("north_star", {})
        strategic_goals = context.get("strategic_goals", [])
        scoring_depth = context.get("depth", "comprehensive")
        
        # Use plugin to score alignment
        alignment_result = await self.alignment_plugin.score_alignment(
            initiative=initiative,
            north_star=north_star,
            strategic_goals=strategic_goals,
            dimensions=list(self.alignment_dimensions.keys())
        )
        
        # Parse result
        alignment_data = json.loads(alignment_result)
        
        # Create detailed scoring report
        scoring_report = {
            "initiative_id": initiative.get("id"),
            "initiative_title": initiative.get("title"),
            "overall_score": alignment_data["overall_score"],
            "confidence_level": alignment_data["confidence"],
            "dimension_scores": alignment_data["dimension_scores"],
            "strengths": alignment_data["strengths"],
            "gaps": alignment_data["gaps"],
            "evidence": alignment_data["evidence"],
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Generate recommendations
        recommendations = self._generate_alignment_recommendations(alignment_data)
        
        # Create visual representation
        visualization = self._create_alignment_visualization(alignment_data)
        
        return {
            "status": "success",
            "scoring_report": scoring_report,
            "recommendations": recommendations,
            "visualization": visualization,
            "interpretation": self._interpret_score(alignment_data["overall_score"]),
            "next_steps": [
                "Address identified gaps",
                "Strengthen weak dimensions",
                "Compare with alternative approaches",
                "Track alignment over time"
            ]
        }
    
    async def _analyze_gaps(self, agent: ChatCompletionAgent, query: str, context: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Analyze alignment gaps and misalignments"""
        
        # Get analysis scope
        initiatives = context.get("initiatives", [])
        north_star = context.get("north_star", {})
        focus_areas = context.get("focus_areas", [])
        
        # Use plugin to analyze gaps
        gap_result = await self.alignment_plugin.analyze_gaps(
            initiatives=initiatives,
            north_star=north_star,
            gap_threshold=0.7,
            focus_areas=focus_areas
        )
        
        # Parse result
        gap_data = json.loads(gap_result)
        
        # Structure gap analysis
        gap_analysis = {
            "critical_gaps": [],
            "moderate_gaps": [],
            "minor_gaps": [],
            "coverage_analysis": {}
        }
        
        # Categorize gaps by severity
        for gap in gap_data["gaps"]:
            severity = gap["severity"]
            gap_detail = {
                "type": gap["type"],
                "description": gap["description"],
                "affected_elements": gap["affected_elements"],
                "impact": gap["impact"],
                "root_cause": gap.get("root_cause", ""),
                "remediation": gap["remediation"]
            }
            
            if severity == "critical":
                gap_analysis["critical_gaps"].append(gap_detail)
            elif severity == "moderate":
                gap_analysis["moderate_gaps"].append(gap_detail)
            else:
                gap_analysis["minor_gaps"].append(gap_detail)
        
        # Coverage analysis
        gap_analysis["coverage_analysis"] = gap_data["coverage_analysis"]
        
        # Generate action plan
        action_plan = self._create_gap_remediation_plan(gap_analysis)
        
        return {
            "status": "success",
            "gap_analysis": gap_analysis,
            "summary": {
                "total_gaps": len(gap_data["gaps"]),
                "critical": len(gap_analysis["critical_gaps"]),
                "coverage_score": gap_data["overall_coverage"]
            },
            "action_plan": action_plan,
            "priority_actions": gap_data.get("priority_actions", []),
            "timeline": gap_data.get("remediation_timeline", ""),
            "next_steps": [
                "Prioritize critical gap remediation",
                "Allocate resources to gap closure",
                "Set up gap monitoring",
                "Review progress regularly"
            ]
        }
    
    async def _compare_alternatives(self, agent: ChatCompletionAgent, query: str, context: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Compare alignment of alternative approaches"""
        
        # Get alternatives to compare
        alternatives = context.get("alternatives", [])
        comparison_criteria = context.get("criteria", list(self.alignment_dimensions.keys()))
        north_star = context.get("north_star", {})
        
        # Use plugin to compare
        comparison_result = await self.alignment_plugin.compare_alternatives(
            alternatives=alternatives,
            north_star=north_star,
            criteria=comparison_criteria,
            include_tradeoffs=True
        )
        
        # Parse result
        comparison_data = json.loads(comparison_result)
        
        # Create comparison matrix
        comparison_matrix = {
            "alternatives": [],
            "criteria": comparison_criteria,
            "scores": {},
            "rankings": {}
        }
        
        # Structure comparison data
        for alt_comparison in comparison_data["comparisons"]:
            alternative = {
                "id": alt_comparison["id"],
                "name": alt_comparison["name"],
                "overall_score": alt_comparison["overall_score"],
                "dimension_scores": alt_comparison["dimension_scores"],
                "pros": alt_comparison["pros"],
                "cons": alt_comparison["cons"],
                "unique_value": alt_comparison.get("unique_value", "")
            }
            comparison_matrix["alternatives"].append(alternative)
        
        # Generate rankings
        comparison_matrix["rankings"] = comparison_data["rankings"]
        
        # Trade-off analysis
        tradeoff_analysis = self._analyze_tradeoffs(comparison_data)
        
        # Recommendation
        recommendation = comparison_data.get("recommendation", {})
        
        return {
            "status": "success",
            "comparison_matrix": comparison_matrix,
            "tradeoff_analysis": tradeoff_analysis,
            "recommendation": recommendation,
            "sensitivity_analysis": comparison_data.get("sensitivity", {}),
            "decision_factors": comparison_data.get("key_differentiators", []),
            "visualization": self._create_comparison_charts(comparison_matrix),
            "next_steps": [
                "Review trade-offs with stakeholders",
                "Conduct sensitivity testing",
                "Validate assumptions",
                "Make selection decision"
            ]
        }
    
    async def _optimize_portfolio(self, agent: ChatCompletionAgent, query: str, context: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Optimize portfolio of initiatives for maximum alignment"""
        
        # Get portfolio data
        initiatives = context.get("initiatives", [])
        constraints = context.get("constraints", {})
        optimization_goals = context.get("goals", ["strategic_value", "resource_efficiency"])
        north_star = context.get("north_star", {})
        
        # Use plugin to optimize
        optimization_result = await self.alignment_plugin.optimize_portfolio(
            initiatives=initiatives,
            north_star=north_star,
            constraints=constraints,
            optimization_goals=optimization_goals
        )
        
        # Parse result
        optimization_data = json.loads(optimization_result)
        
        # Create optimized portfolio
        optimized_portfolio = {
            "selected_initiatives": optimization_data["selected"],
            "deferred_initiatives": optimization_data["deferred"],
            "cancelled_initiatives": optimization_data["cancelled"],
            "total_alignment_score": optimization_data["portfolio_score"],
            "resource_utilization": optimization_data["resource_utilization"],
            "risk_profile": optimization_data["risk_profile"]
        }
        
        # Generate portfolio insights
        insights = self._generate_portfolio_insights(optimization_data)
        
        # Create roadmap
        roadmap = self._create_portfolio_roadmap(optimization_data)
        
        return {
            "status": "success",
            "optimized_portfolio": optimized_portfolio,
            "optimization_metrics": {
                "before": optimization_data["baseline_metrics"],
                "after": optimization_data["optimized_metrics"],
                "improvement": optimization_data["improvement_percentage"]
            },
            "insights": insights,
            "roadmap": roadmap,
            "risks": optimization_data.get("portfolio_risks", []),
            "alternatives": optimization_data.get("alternative_portfolios", []),
            "next_steps": [
                "Review portfolio with leadership",
                "Secure resource commitments",
                "Establish portfolio governance",
                "Begin implementation"
            ]
        }
    
    async def _validate_plan(self, agent: ChatCompletionAgent, query: str, context: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Validate strategic plan against North Star"""
        
        # Get validation inputs
        strategic_plan = context.get("plan", {})
        north_star = context.get("north_star", {})
        validation_criteria = context.get("criteria", ["completeness", "consistency", "feasibility"])
        
        # Use plugin to validate
        validation_result = await self.alignment_plugin.validate_plan(
            plan=strategic_plan,
            north_star=north_star,
            validation_criteria=validation_criteria,
            strict_mode=context.get("strict", False)
        )
        
        # Parse result
        validation_data = json.loads(validation_result)
        
        # Create validation report
        validation_report = {
            "plan_id": strategic_plan.get("id"),
            "validation_status": validation_data["status"],
            "overall_validity": validation_data["validity_score"],
            "criteria_results": validation_data["criteria_results"],
            "issues_found": validation_data["issues"],
            "warnings": validation_data["warnings"],
            "strengths": validation_data["strengths"]
        }
        
        # Generate corrective actions
        corrective_actions = []
        for issue in validation_data["issues"]:
            if issue["severity"] in ["critical", "high"]:
                corrective_actions.append({
                    "issue": issue["description"],
                    "action": issue["remediation"],
                    "priority": issue["severity"],
                    "effort": issue.get("effort", "medium")
                })
        
        return {
            "status": "success",
            "validation_report": validation_report,
            "corrective_actions": corrective_actions,
            "readiness_assessment": {
                "ready_for_execution": validation_data["validity_score"] >= 80,
                "confidence_level": validation_data["confidence"],
                "risk_areas": validation_data.get("risk_areas", [])
            },
            "recommendations": validation_data["recommendations"],
            "certification": self._generate_validation_certificate(validation_data) if validation_data["validity_score"] >= 80 else None,
            "next_steps": [
                "Address critical issues",
                "Re-validate after corrections",
                "Get stakeholder approval",
                "Proceed with execution"
            ]
        }
    
    async def _handle_general_query(self, agent: ChatCompletionAgent, query: str, context: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Handle general alignment queries"""
        
        response = await agent.invoke(f"""
Query: {query}
Context: {json.dumps(context, indent=2)}

Please provide strategic alignment guidance or answer the question.
""")
        
        return {
            "status": "success",
            "response": response.content,
            "suggestions": [
                "Score initiative alignment",
                "Analyze strategic gaps",
                "Compare alternatives",
                "Optimize initiative portfolio"
            ]
        }
    
    def _generate_alignment_recommendations(self, alignment_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate recommendations to improve alignment"""
        
        recommendations = []
        
        # Check dimension scores
        for dimension, score in alignment_data["dimension_scores"].items():
            if score < 70:
                recommendations.append({
                    "dimension": dimension,
                    "current_score": score,
                    "recommendation": f"Strengthen {dimension} alignment",
                    "actions": self._get_dimension_improvement_actions(dimension, alignment_data),
                    "impact": "high" if score < 50 else "medium",
                    "effort": "medium"
                })
        
        # Address specific gaps
        for gap in alignment_data.get("gaps", []):
            recommendations.append({
                "gap": gap["description"],
                "recommendation": gap["remediation"],
                "impact": gap.get("impact", "medium"),
                "effort": gap.get("effort", "medium")
            })
        
        return sorted(recommendations, key=lambda x: x.get("impact", "") == "high", reverse=True)
    
    def _create_alignment_visualization(self, alignment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create visual representation of alignment scores"""
        
        return {
            "type": "radar_chart",
            "data": {
                "dimensions": list(alignment_data["dimension_scores"].keys()),
                "scores": list(alignment_data["dimension_scores"].values()),
                "benchmark": [80] * len(alignment_data["dimension_scores"])  # Target scores
            },
            "styling": {
                "colors": {
                    "actual": "#2196f3",
                    "benchmark": "#4caf50"
                },
                "fill_opacity": 0.3
            },
            "annotations": [
                {
                    "dimension": dim,
                    "score": score,
                    "label": f"{dim}: {score}%"
                }
                for dim, score in alignment_data["dimension_scores"].items()
            ]
        }
    
    def _interpret_score(self, score: float) -> Dict[str, str]:
        """Interpret alignment score meaning"""
        
        if score >= 90:
            return {
                "level": "Excellent",
                "interpretation": "Initiative is strongly aligned with strategic objectives",
                "action": "Proceed with confidence"
            }
        elif score >= 75:
            return {
                "level": "Good",
                "interpretation": "Initiative shows good alignment with minor gaps",
                "action": "Address gaps and proceed"
            }
        elif score >= 60:
            return {
                "level": "Moderate",
                "interpretation": "Initiative has moderate alignment with significant gaps",
                "action": "Strengthen alignment before proceeding"
            }
        else:
            return {
                "level": "Poor",
                "interpretation": "Initiative shows weak alignment with strategic objectives",
                "action": "Reconsider or significantly revise"
            }
    
    def _create_gap_remediation_plan(self, gap_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create action plan to address gaps"""
        
        action_plan = []
        
        # Priority 1: Critical gaps
        for gap in gap_analysis["critical_gaps"]:
            action_plan.append({
                "priority": 1,
                "gap": gap["description"],
                "actions": gap["remediation"],
                "timeline": "Immediate",
                "owner": "Leadership Team",
                "success_criteria": f"Close gap: {gap['type']}"
            })
        
        # Priority 2: Moderate gaps
        for gap in gap_analysis["moderate_gaps"]:
            action_plan.append({
                "priority": 2,
                "gap": gap["description"],
                "actions": gap["remediation"],
                "timeline": "30 days",
                "owner": "Project Team",
                "success_criteria": f"Improve: {gap['type']}"
            })
        
        return action_plan
    
    def _analyze_tradeoffs(self, comparison_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze trade-offs between alternatives"""
        
        tradeoffs = {
            "key_tradeoffs": [],
            "decision_dimensions": {},
            "risk_return_analysis": {}
        }
        
        # Identify key trade-offs
        comparisons = comparison_data.get("comparisons", [])
        if len(comparisons) >= 2:
            # Compare top alternatives
            alt1, alt2 = comparisons[0], comparisons[1]
            
            for dimension in alt1["dimension_scores"]:
                score_diff = alt1["dimension_scores"][dimension] - alt2["dimension_scores"][dimension]
                if abs(score_diff) > 10:
                    tradeoffs["key_tradeoffs"].append({
                        "dimension": dimension,
                        "alternative_1": {
                            "name": alt1["name"],
                            "score": alt1["dimension_scores"][dimension]
                        },
                        "alternative_2": {
                            "name": alt2["name"],
                            "score": alt2["dimension_scores"][dimension]
                        },
                        "implication": f"{alt1['name']} is {'stronger' if score_diff > 0 else 'weaker'} in {dimension}"
                    })
        
        return tradeoffs
    
    def _create_comparison_charts(self, comparison_matrix: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create visualization charts for comparison"""
        
        charts = []
        
        # Overall scores bar chart
        charts.append({
            "type": "bar",
            "title": "Overall Alignment Scores",
            "data": {
                "labels": [alt["name"] for alt in comparison_matrix["alternatives"]],
                "values": [alt["overall_score"] for alt in comparison_matrix["alternatives"]]
            }
        })
        
        # Dimension comparison radar chart
        if comparison_matrix["alternatives"]:
            charts.append({
                "type": "radar",
                "title": "Multi-Dimensional Comparison",
                "data": {
                    "dimensions": comparison_matrix["criteria"],
                    "datasets": [
                        {
                            "label": alt["name"],
                            "values": [alt["dimension_scores"].get(dim, 0) for dim in comparison_matrix["criteria"]]
                        }
                        for alt in comparison_matrix["alternatives"]
                    ]
                }
            })
        
        return charts
    
    def _get_dimension_improvement_actions(self, dimension: str, alignment_data: Dict[str, Any]) -> List[str]:
        """Get specific actions to improve dimension alignment"""
        
        actions_map = {
            "strategic": [
                "Clarify connection to vision",
                "Strengthen goal linkages",
                "Ensure value consistency"
            ],
            "operational": [
                "Optimize resource allocation",
                "Improve capability matching",
                "Adjust timeline for feasibility"
            ],
            "market": [
                "Enhance customer value proposition",
                "Strengthen competitive positioning",
                "Improve market timing"
            ],
            "financial": [
                "Improve ROI projections",
                "Align with budget constraints",
                "Balance risk-return profile"
            ]
        }
        
        return actions_map.get(dimension, ["Review and strengthen alignment"])
    
    def _generate_portfolio_insights(self, optimization_data: Dict[str, Any]) -> List[str]:
        """Generate insights from portfolio optimization"""
        
        insights = []
        
        # Selection insights
        selected_count = len(optimization_data["selected"])
        total_count = selected_count + len(optimization_data["deferred"]) + len(optimization_data["cancelled"])
        
        insights.append(f"Optimized portfolio includes {selected_count} of {total_count} initiatives")
        
        # Improvement insights
        improvement = optimization_data.get("improvement_percentage", 0)
        if improvement > 0:
            insights.append(f"Portfolio optimization improved alignment by {improvement}%")
        
        # Resource insights
        utilization = optimization_data.get("resource_utilization", {})
        if utilization:
            insights.append(f"Resource utilization optimized to {utilization.get('percentage', 0)}%")
        
        # Risk insights
        risk_profile = optimization_data.get("risk_profile", "")
        if risk_profile:
            insights.append(f"Portfolio risk profile: {risk_profile}")
        
        return insights
    
    def _create_portfolio_roadmap(self, optimization_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create implementation roadmap for optimized portfolio"""
        
        return {
            "phases": [
                {
                    "phase": "Quarter 1",
                    "initiatives": optimization_data["selected"][:3],
                    "focus": "Quick wins and foundation",
                    "resources": "30% allocation"
                },
                {
                    "phase": "Quarter 2-3",
                    "initiatives": optimization_data["selected"][3:6],
                    "focus": "Core implementation",
                    "resources": "50% allocation"
                },
                {
                    "phase": "Quarter 4+",
                    "initiatives": optimization_data["selected"][6:],
                    "focus": "Scale and optimize",
                    "resources": "20% allocation"
                }
            ],
            "milestones": [
                {"quarter": "Q1", "milestone": "Foundation complete"},
                {"quarter": "Q2", "milestone": "Core capabilities live"},
                {"quarter": "Q3", "milestone": "Integration complete"},
                {"quarter": "Q4", "milestone": "Full deployment"}
            ],
            "dependencies": optimization_data.get("dependencies", [])
        }
    
    def _generate_validation_certificate(self, validation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate validation certificate for approved plans"""
        
        return {
            "certificate_id": str(uuid4()),
            "validation_date": datetime.utcnow().isoformat(),
            "validity_score": validation_data["validity_score"],
            "status": "VALIDATED",
            "expires": (datetime.utcnow() + timedelta(days=90)).isoformat(),
            "criteria_passed": [
                criteria for criteria, result in validation_data["criteria_results"].items()
                if result["passed"]
            ],
            "validator": "Strategic Alignment System"
        }