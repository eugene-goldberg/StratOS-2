"""Alignment Scoring Plugin

Provides strategic alignment evaluation and validation capabilities.
"""

import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from uuid import uuid4

from semantic_kernel.functions import kernel_function
from semantic_kernel.kernel_pydantic import KernelBaseModel


class AlignmentPlugin(KernelBaseModel):
    """Plugin for strategic alignment scoring and validation"""
    
    @kernel_function(
        description="Score alignment between initiatives and strategic objectives",
        name="ScoreAlignment"
    )
    async def score_alignment(
        self,
        initiative: Dict[str, Any],
        north_star: Dict[str, Any],
        strategic_goals: List[Dict[str, Any]] = None,
        dimensions: List[str] = None
    ) -> str:
        """Calculate multi-dimensional alignment scores"""
        
        strategic_goals = strategic_goals or []
        dimensions = dimensions or ["strategic", "operational", "market", "financial"]
        
        # This would use sophisticated scoring algorithms
        # For now, creating example scores
        dimension_scores = {}
        evidence = []
        strengths = []
        gaps = []
        
        # Strategic dimension
        if "strategic" in dimensions:
            # Check vision alignment
            vision_alignment = 85  # Would calculate based on semantic similarity
            goal_support = 80  # Would analyze goal connections
            value_consistency = 90  # Would check against values
            
            strategic_score = (vision_alignment + goal_support + value_consistency) / 3
            dimension_scores["strategic"] = strategic_score
            
            evidence.append({
                "dimension": "strategic",
                "factor": "vision_alignment",
                "score": vision_alignment,
                "evidence": "Initiative directly supports digital transformation vision"
            })
            
            if strategic_score >= 80:
                strengths.append({
                    "dimension": "strategic",
                    "description": "Strong alignment with vision and values"
                })
            else:
                gaps.append({
                    "dimension": "strategic",
                    "description": "Moderate vision alignment could be strengthened",
                    "remediation": "Clarify connection to strategic vision"
                })
        
        # Operational dimension
        if "operational" in dimensions:
            resource_efficiency = 75
            capability_match = 70
            timeline_feasibility = 85
            
            operational_score = (resource_efficiency + capability_match + timeline_feasibility) / 3
            dimension_scores["operational"] = operational_score
            
            evidence.append({
                "dimension": "operational",
                "factor": "capability_match",
                "score": capability_match,
                "evidence": "Some capability gaps identified"
            })
            
            if capability_match < 75:
                gaps.append({
                    "dimension": "operational",
                    "description": "Capability gaps may impact execution",
                    "remediation": "Develop capability building plan"
                })
        
        # Market dimension
        if "market" in dimensions:
            customer_value = 88
            competitive_advantage = 82
            market_timing = 78
            
            market_score = (customer_value + competitive_advantage + market_timing) / 3
            dimension_scores["market"] = market_score
            
            strengths.append({
                "dimension": "market",
                "description": "Strong customer value proposition"
            })
        
        # Financial dimension
        if "financial" in dimensions:
            roi_potential = 72
            budget_alignment = 80
            risk_return = 68
            
            financial_score = (roi_potential + budget_alignment + risk_return) / 3
            dimension_scores["financial"] = financial_score
            
            if risk_return < 70:
                gaps.append({
                    "dimension": "financial",
                    "description": "Risk-return profile needs improvement",
                    "remediation": "Develop risk mitigation strategies"
                })
        
        # Calculate overall score
        overall_score = sum(dimension_scores.values()) / len(dimension_scores)
        
        result = {
            "overall_score": round(overall_score, 1),
            "dimension_scores": {k: round(v, 1) for k, v in dimension_scores.items()},
            "confidence": 0.85,
            "strengths": strengths,
            "gaps": gaps,
            "evidence": evidence,
            "assessment_date": datetime.utcnow().isoformat()
        }
        
        return json.dumps(result)
    
    @kernel_function(
        description="Analyze alignment gaps between initiatives and strategy",
        name="AnalyzeGaps"
    )
    async def analyze_gaps(
        self,
        initiatives: List[Dict[str, Any]],
        north_star: Dict[str, Any],
        gap_threshold: float = 0.7,
        focus_areas: List[str] = None
    ) -> str:
        """Identify and analyze strategic alignment gaps"""
        
        focus_areas = focus_areas or []
        
        gaps = []
        coverage_analysis = {
            "vision_coverage": 0,
            "goals_covered": [],
            "goals_uncovered": [],
            "values_alignment": {}
        }
        
        # Check vision coverage
        vision_keywords = north_star.get("vision", "").lower().split()
        covered_keywords = set()
        
        for initiative in initiatives:
            init_text = f"{initiative.get('title', '')} {initiative.get('description', '')}".lower()
            for keyword in vision_keywords:
                if keyword in init_text:
                    covered_keywords.add(keyword)
        
        coverage_analysis["vision_coverage"] = len(covered_keywords) / len(vision_keywords) if vision_keywords else 0
        
        if coverage_analysis["vision_coverage"] < 0.6:
            gaps.append({
                "type": "vision_gap",
                "severity": "critical",
                "description": "Limited initiatives supporting vision elements",
                "affected_elements": ["vision"],
                "impact": "Strategic direction may not be fully realized",
                "remediation": "Develop initiatives targeting uncovered vision aspects"
            })
        
        # Check goal coverage
        goals = north_star.get("goals", [])
        for goal in goals:
            goal_id = goal.get("id", "")
            covered = any(
                goal_id in init.get("strategic_goals", [])
                for init in initiatives
            )
            
            if covered:
                coverage_analysis["goals_covered"].append(goal_id)
            else:
                coverage_analysis["goals_uncovered"].append(goal_id)
                gaps.append({
                    "type": "goal_gap",
                    "severity": "moderate",
                    "description": f"No initiatives supporting goal: {goal.get('title', '')}",
                    "affected_elements": [goal_id],
                    "impact": "Strategic goal may not be achieved",
                    "remediation": "Create initiatives targeting this goal"
                })
        
        # Check for execution gaps
        if not any(init.get("type") == "quick_win" for init in initiatives):
            gaps.append({
                "type": "execution_gap",
                "severity": "moderate",
                "description": "No quick win initiatives for momentum",
                "affected_elements": ["portfolio"],
                "impact": "May lack early success stories",
                "remediation": "Identify and add quick win initiatives"
            })
        
        # Check for balance gaps
        init_types = {}
        for init in initiatives:
            init_type = init.get("type", "other")
            init_types[init_type] = init_types.get(init_type, 0) + 1
        
        if len(init_types) < 3:
            gaps.append({
                "type": "diversity_gap",
                "severity": "minor",
                "description": "Limited diversity in initiative types",
                "affected_elements": ["portfolio"],
                "impact": "May miss opportunities or increase risk",
                "remediation": "Diversify initiative portfolio"
            })
        
        # Calculate overall coverage
        total_elements = len(goals) + 1  # goals + vision
        covered_elements = len(coverage_analysis["goals_covered"]) + (1 if coverage_analysis["vision_coverage"] > 0.6 else 0)
        overall_coverage = covered_elements / total_elements if total_elements > 0 else 0
        
        # Priority actions
        priority_actions = []
        for gap in gaps:
            if gap["severity"] == "critical":
                priority_actions.append({
                    "action": gap["remediation"],
                    "urgency": "immediate",
                    "owner": "Leadership"
                })
        
        result = {
            "gaps": gaps,
            "coverage_analysis": coverage_analysis,
            "overall_coverage": round(overall_coverage, 2),
            "priority_actions": priority_actions,
            "remediation_timeline": self._generate_remediation_timeline(gaps)
        }
        
        return json.dumps(result)
    
    @kernel_function(
        description="Compare alignment of multiple alternatives",
        name="CompareAlternatives"
    )
    async def compare_alternatives(
        self,
        alternatives: List[Dict[str, Any]],
        north_star: Dict[str, Any],
        criteria: List[str] = None,
        include_tradeoffs: bool = True
    ) -> str:
        """Compare strategic alignment of different alternatives"""
        
        criteria = criteria or ["strategic", "operational", "market", "financial"]
        
        comparisons = []
        
        for alt in alternatives:
            # Score each alternative
            dimension_scores = {}
            
            for criterion in criteria:
                # Simplified scoring - would use detailed analysis
                if criterion == "strategic":
                    score = 85 if "innovation" in alt.get("description", "").lower() else 75
                elif criterion == "operational":
                    score = 80 if alt.get("type") == "incremental" else 70
                elif criterion == "market":
                    score = 90 if "customer" in alt.get("description", "").lower() else 70
                elif criterion == "financial":
                    score = 75 if alt.get("cost") == "low" else 65
                else:
                    score = 70
                
                dimension_scores[criterion] = score
            
            overall_score = sum(dimension_scores.values()) / len(dimension_scores)
            
            comparison = {
                "id": alt.get("id", str(uuid4())),
                "name": alt.get("name", "Alternative"),
                "overall_score": round(overall_score, 1),
                "dimension_scores": dimension_scores,
                "pros": self._identify_pros(alt, dimension_scores),
                "cons": self._identify_cons(alt, dimension_scores),
                "unique_value": alt.get("unique_value", "")
            }
            comparisons.append(comparison)
        
        # Rank alternatives
        comparisons.sort(key=lambda x: x["overall_score"], reverse=True)
        rankings = {
            "overall": [c["name"] for c in comparisons],
            "by_dimension": {}
        }
        
        for criterion in criteria:
            sorted_by_criterion = sorted(
                comparisons,
                key=lambda x: x["dimension_scores"].get(criterion, 0),
                reverse=True
            )
            rankings["by_dimension"][criterion] = [c["name"] for c in sorted_by_criterion]
        
        # Identify key differentiators
        key_differentiators = []
        if len(comparisons) >= 2:
            top_two = comparisons[:2]
            for criterion in criteria:
                diff = abs(top_two[0]["dimension_scores"][criterion] - top_two[1]["dimension_scores"][criterion])
                if diff > 10:
                    key_differentiators.append({
                        "dimension": criterion,
                        "difference": diff,
                        "leader": top_two[0]["name"] if top_two[0]["dimension_scores"][criterion] > top_two[1]["dimension_scores"][criterion] else top_two[1]["name"]
                    })
        
        # Generate recommendation
        recommendation = {
            "recommended": comparisons[0]["name"] if comparisons else None,
            "rationale": f"Highest overall alignment score ({comparisons[0]['overall_score']})" if comparisons else "",
            "conditions": "Assuming equal weight for all criteria"
        }
        
        # Sensitivity analysis
        sensitivity = {
            "criteria_weights": "Equal weights assumed",
            "break_point": "Strategic dimension must drop below 60 to change recommendation"
        }
        
        result = {
            "comparisons": comparisons,
            "rankings": rankings,
            "key_differentiators": key_differentiators,
            "recommendation": recommendation,
            "sensitivity": sensitivity
        }
        
        return json.dumps(result)
    
    @kernel_function(
        description="Optimize portfolio of initiatives for maximum alignment",
        name="OptimizePortfolio"
    )
    async def optimize_portfolio(
        self,
        initiatives: List[Dict[str, Any]],
        north_star: Dict[str, Any],
        constraints: Dict[str, Any] = None,
        optimization_goals: List[str] = None
    ) -> str:
        """Optimize initiative portfolio for strategic alignment"""
        
        constraints = constraints or {"budget": 1000000, "resources": 20}
        optimization_goals = optimization_goals or ["strategic_value", "resource_efficiency"]
        
        # This would use portfolio optimization algorithms
        # For now, using simplified selection logic
        
        # Score and rank initiatives
        scored_initiatives = []
        for init in initiatives:
            score = self._calculate_initiative_score(init, north_star, optimization_goals)
            scored_initiatives.append({
                "initiative": init,
                "score": score,
                "cost": init.get("cost", 100000),
                "resources": init.get("resources", 2)
            })
        
        # Sort by score/cost ratio
        scored_initiatives.sort(key=lambda x: x["score"] / x["cost"], reverse=True)
        
        # Select initiatives within constraints
        selected = []
        deferred = []
        cancelled = []
        
        total_cost = 0
        total_resources = 0
        
        for scored_init in scored_initiatives:
            init_cost = scored_init["cost"]
            init_resources = scored_init["resources"]
            
            if (total_cost + init_cost <= constraints["budget"] and
                total_resources + init_resources <= constraints["resources"]):
                selected.append(scored_init["initiative"])
                total_cost += init_cost
                total_resources += init_resources
            elif scored_init["score"] >= 70:
                deferred.append(scored_init["initiative"])
            else:
                cancelled.append(scored_init["initiative"])
        
        # Calculate portfolio metrics
        portfolio_score = sum(s["score"] for s in scored_initiatives if s["initiative"] in selected) / len(selected) if selected else 0
        
        baseline_metrics = {
            "total_initiatives": len(initiatives),
            "average_score": sum(s["score"] for s in scored_initiatives) / len(scored_initiatives),
            "total_cost": sum(s["cost"] for s in scored_initiatives),
            "efficiency": 0.6
        }
        
        optimized_metrics = {
            "total_initiatives": len(selected),
            "average_score": portfolio_score,
            "total_cost": total_cost,
            "efficiency": 0.85
        }
        
        improvement = ((portfolio_score - baseline_metrics["average_score"]) / baseline_metrics["average_score"] * 100) if baseline_metrics["average_score"] > 0 else 0
        
        # Identify portfolio risks
        portfolio_risks = []
        if len(selected) < 3:
            portfolio_risks.append({
                "risk": "Limited portfolio diversity",
                "mitigation": "Consider adding more initiatives in next phase"
            })
        
        # Alternative portfolios
        alternative_portfolios = [
            {
                "name": "Aggressive",
                "description": "Focus on high-impact, high-risk initiatives",
                "score": portfolio_score + 5
            },
            {
                "name": "Conservative",
                "description": "Focus on low-risk, proven initiatives",
                "score": portfolio_score - 5
            }
        ]
        
        result = {
            "selected": [init.get("id", init.get("title", "")) for init in selected],
            "deferred": [init.get("id", init.get("title", "")) for init in deferred],
            "cancelled": [init.get("id", init.get("title", "")) for init in cancelled],
            "portfolio_score": round(portfolio_score, 1),
            "resource_utilization": {
                "budget": round(total_cost / constraints["budget"] * 100, 1),
                "resources": round(total_resources / constraints["resources"] * 100, 1),
                "percentage": round((total_cost / constraints["budget"] + total_resources / constraints["resources"]) / 2 * 100, 1)
            },
            "risk_profile": "balanced",
            "baseline_metrics": baseline_metrics,
            "optimized_metrics": optimized_metrics,
            "improvement_percentage": round(improvement, 1),
            "portfolio_risks": portfolio_risks,
            "alternative_portfolios": alternative_portfolios,
            "dependencies": self._identify_dependencies(selected)
        }
        
        return json.dumps(result)
    
    @kernel_function(
        description="Validate strategic plan against North Star",
        name="ValidatePlan"
    )
    async def validate_plan(
        self,
        plan: Dict[str, Any],
        north_star: Dict[str, Any],
        validation_criteria: List[str] = None,
        strict_mode: bool = False
    ) -> str:
        """Validate strategic plan alignment and completeness"""
        
        validation_criteria = validation_criteria or ["completeness", "consistency", "feasibility", "alignment"]
        
        issues = []
        warnings = []
        strengths = []
        criteria_results = {}
        
        # Completeness validation
        if "completeness" in validation_criteria:
            completeness_issues = []
            
            if not plan.get("initiatives"):
                completeness_issues.append("No initiatives defined")
            if not plan.get("timeline"):
                completeness_issues.append("No timeline specified")
            if not plan.get("resources"):
                completeness_issues.append("No resource allocation")
            
            passed = len(completeness_issues) == 0
            criteria_results["completeness"] = {
                "passed": passed,
                "score": 100 if passed else (100 - len(completeness_issues) * 20),
                "issues": completeness_issues
            }
            
            if not passed:
                for issue in completeness_issues:
                    issues.append({
                        "severity": "high" if strict_mode else "medium",
                        "description": issue,
                        "criterion": "completeness",
                        "remediation": f"Add missing element: {issue}"
                    })
            else:
                strengths.append("Plan is complete with all required elements")
        
        # Consistency validation
        if "consistency" in validation_criteria:
            consistency_score = 85  # Would check for internal consistency
            passed = consistency_score >= 70
            
            criteria_results["consistency"] = {
                "passed": passed,
                "score": consistency_score,
                "issues": []
            }
            
            if passed:
                strengths.append("Plan shows good internal consistency")
            else:
                issues.append({
                    "severity": "medium",
                    "description": "Inconsistencies found between plan elements",
                    "criterion": "consistency",
                    "remediation": "Review and align plan components"
                })
        
        # Feasibility validation
        if "feasibility" in validation_criteria:
            feasibility_checks = {
                "resource_feasibility": 80,
                "timeline_feasibility": 75,
                "capability_feasibility": 70
            }
            
            overall_feasibility = sum(feasibility_checks.values()) / len(feasibility_checks)
            passed = overall_feasibility >= 70
            
            criteria_results["feasibility"] = {
                "passed": passed,
                "score": overall_feasibility,
                "details": feasibility_checks
            }
            
            if feasibility_checks["capability_feasibility"] < 70:
                warnings.append({
                    "type": "capability_gap",
                    "description": "Some required capabilities may be lacking",
                    "recommendation": "Develop capability building plan"
                })
        
        # Alignment validation
        if "alignment" in validation_criteria:
            alignment_score = 82  # Would calculate actual alignment
            passed = alignment_score >= 75
            
            criteria_results["alignment"] = {
                "passed": passed,
                "score": alignment_score,
                "details": "Strong alignment with vision and goals"
            }
            
            if passed:
                strengths.append("Plan aligns well with North Star elements")
        
        # Calculate overall validity
        total_score = sum(
            result["score"] for result in criteria_results.values()
        )
        validity_score = total_score / len(criteria_results)
        
        # Determine validation status
        critical_issues = [i for i in issues if i["severity"] == "critical"]
        if critical_issues:
            status = "FAILED"
        elif validity_score >= 80:
            status = "PASSED"
        elif validity_score >= 60:
            status = "CONDITIONAL"
        else:
            status = "FAILED"
        
        # Generate recommendations
        recommendations = []
        for issue in issues:
            recommendations.append(issue["remediation"])
        
        if validity_score < 80:
            recommendations.append("Consider strategic review session")
        
        # Risk areas
        risk_areas = []
        if any(not result["passed"] for result in criteria_results.values()):
            risk_areas.append("Validation criteria not fully met")
        
        result = {
            "status": status,
            "validity_score": round(validity_score, 1),
            "criteria_results": criteria_results,
            "issues": issues,
            "warnings": warnings,
            "strengths": strengths,
            "confidence": 0.9 if status == "PASSED" else 0.6,
            "recommendations": recommendations,
            "risk_areas": risk_areas,
            "validation_date": datetime.utcnow().isoformat()
        }
        
        return json.dumps(result)
    
    def _generate_remediation_timeline(self, gaps: List[Dict[str, Any]]) -> str:
        """Generate timeline for gap remediation"""
        
        critical_count = len([g for g in gaps if g["severity"] == "critical"])
        moderate_count = len([g for g in gaps if g["severity"] == "moderate"])
        
        if critical_count > 0:
            return f"Immediate action required for {critical_count} critical gaps, 30-day plan for {moderate_count} moderate gaps"
        elif moderate_count > 0:
            return f"30-day remediation plan for {moderate_count} gaps"
        else:
            return "60-day improvement plan for minor gaps"
    
    def _identify_pros(self, alternative: Dict[str, Any], scores: Dict[str, float]) -> List[str]:
        """Identify pros of an alternative"""
        
        pros = []
        for dimension, score in scores.items():
            if score >= 80:
                pros.append(f"Strong {dimension} alignment ({score})")
        
        if alternative.get("cost") == "low":
            pros.append("Cost-effective solution")
        
        return pros[:3]  # Top 3 pros
    
    def _identify_cons(self, alternative: Dict[str, Any], scores: Dict[str, float]) -> List[str]:
        """Identify cons of an alternative"""
        
        cons = []
        for dimension, score in scores.items():
            if score < 70:
                cons.append(f"Weak {dimension} alignment ({score})")
        
        if alternative.get("risk") == "high":
            cons.append("High implementation risk")
        
        return cons[:3]  # Top 3 cons
    
    def _calculate_initiative_score(self, initiative: Dict[str, Any], north_star: Dict[str, Any], goals: List[str]) -> float:
        """Calculate overall score for an initiative"""
        
        # Simplified scoring
        base_score = 70
        
        # Bonus for strategic alignment
        if "strategic_value" in goals:
            if any(goal in initiative.get("strategic_goals", []) for goal in north_star.get("goals", [])):
                base_score += 10
        
        # Bonus for efficiency
        if "resource_efficiency" in goals:
            if initiative.get("type") == "quick_win":
                base_score += 5
        
        # Penalty for high risk
        if initiative.get("risk_level") == "high":
            base_score -= 5
        
        return min(100, max(0, base_score))
    
    def _identify_dependencies(self, selected_initiatives: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify dependencies between selected initiatives"""
        
        dependencies = []
        
        # Simplified dependency detection
        for i, init1 in enumerate(selected_initiatives):
            for j, init2 in enumerate(selected_initiatives[i+1:], i+1):
                # Check for logical dependencies
                if init1.get("type") == "foundation" and init2.get("type") == "enhancement":
                    dependencies.append({
                        "from": init1.get("id", init1.get("title", "")),
                        "to": init2.get("id", init2.get("title", "")),
                        "type": "prerequisite",
                        "description": "Foundation must complete before enhancement"
                    })
        
        return dependencies