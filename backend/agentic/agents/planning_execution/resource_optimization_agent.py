"""Resource Optimization Agent

Manages resource allocation, optimization, and utilization tracking across initiatives.
"""

import asyncio
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from uuid import uuid4

from semantic_kernel import Kernel
from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.contents import ChatMessageContent, AuthorRole

from common.base_agent import BaseStratosAgent
from .plugins.resource_plugin import ResourcePlugin


class ResourceOptimizationAgent(BaseStratosAgent):
    """Agent responsible for resource management and optimization"""
    
    def __init__(self):
        super().__init__(
            name="Resource Optimization Agent",
            description="Optimizes resource allocation and tracks utilization across initiatives",
            model="gpt-4"  # Use GPT-4 for complex optimization
        )
        
        # Initialize resource plugin
        self.resource_plugin = ResourcePlugin()
        self.kernel.add_plugin(self.resource_plugin, "ResourcePlugin")
        
        # Resource types and constraints
        self.resource_types = {
            "financial": {
                "unit": "USD",
                "constraints": ["budget_limit", "cashflow", "roi_threshold"]
            },
            "human": {
                "unit": "FTE",
                "constraints": ["availability", "skills", "capacity"]
            },
            "technical": {
                "unit": "units",
                "constraints": ["compatibility", "scalability", "licensing"]
            }
        }
        
    async def _create_resource_agent(self) -> ChatCompletionAgent:
        """Create the resource optimization agent with specific instructions"""
        
        instructions = """You are a resource optimization expert specializing in strategic resource management.

Your capabilities include:
1. **Resource Allocation**: Optimize resource distribution across initiatives
2. **Capacity Planning**: Forecast and plan resource needs
3. **Utilization Tracking**: Monitor resource usage and efficiency
4. **Conflict Resolution**: Resolve resource conflicts between initiatives
5. **Cost Optimization**: Minimize costs while maintaining quality
6. **Skills Matching**: Match resources to requirements

When optimizing resources:
- Consider constraints (budget, availability, skills)
- Balance competing priorities
- Maximize resource utilization
- Minimize waste and idle time
- Ensure critical initiatives are resourced
- Plan for contingencies

Resource management principles:
- Efficiency: Maximize output per unit of resource
- Effectiveness: Right resources for right tasks
- Economy: Cost-effective resource usage
- Flexibility: Adapt to changing needs
- Sustainability: Long-term resource health

Available functions:
- AllocateResources: Distribute resources across initiatives
- OptimizeAllocation: Find optimal resource distribution
- TrackUtilization: Monitor resource usage
- ForecastNeeds: Predict future resource requirements
- ResolveConflicts: Handle resource contention
- GenerateDashboard: Create resource utilization views"""

        return ChatCompletionAgent(
            service_id="resource_agent",
            kernel=self.kernel,
            name="ResourceOptimizer",
            instructions=instructions
        )
        
    async def process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process resource optimization requests"""
        
        try:
            query = request.get("query", "")
            context = request.get("context", {})
            user_id = request.get("user_id")
            
            # Create resource agent
            agent = await self._create_resource_agent()
            
            # Determine request type
            request_type = self._determine_request_type(query, context)
            
            if request_type == "allocate":
                return await self._allocate_resources(agent, query, context, user_id)
            elif request_type == "optimize":
                return await self._optimize_allocation(agent, query, context, user_id)
            elif request_type == "track":
                return await self._track_utilization(agent, query, context, user_id)
            elif request_type == "forecast":
                return await self._forecast_needs(agent, query, context, user_id)
            elif request_type == "resolve_conflict":
                return await self._resolve_conflicts(agent, query, context, user_id)
            else:
                # General resource query
                return await self._handle_general_query(agent, query, context, user_id)
                
        except Exception as e:
            return {
                "status": "error",
                "message": f"Resource optimization failed: {str(e)}"
            }
    
    def _determine_request_type(self, query: str, context: Dict[str, Any]) -> str:
        """Determine the type of resource request"""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ["allocate", "assign", "distribute"]):
            return "allocate"
        elif any(word in query_lower for word in ["optimize", "rebalance", "efficiency"]):
            return "optimize"
        elif any(word in query_lower for word in ["track", "utilization", "usage", "dashboard"]):
            return "track"
        elif any(word in query_lower for word in ["forecast", "predict", "future needs"]):
            return "forecast"
        elif any(word in query_lower for word in ["conflict", "contention", "competing"]):
            return "resolve_conflict"
        else:
            return "general"
    
    async def _allocate_resources(self, agent: ChatCompletionAgent, query: str, context: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Allocate resources to initiatives"""
        
        # Gather allocation context
        initiatives = context.get("initiatives", [])
        available_resources = context.get("available_resources", {})
        constraints = context.get("constraints", {})
        priority_weights = context.get("priority_weights", {})
        
        # Use plugin to allocate resources
        allocation_result = await self.resource_plugin.allocate_resources(
            initiatives=initiatives,
            available_resources=available_resources,
            constraints=constraints,
            optimization_goal="balanced"
        )
        
        # Parse result
        allocation_data = json.loads(allocation_result)
        
        # Create detailed allocation records
        allocations = []
        for alloc in allocation_data["allocations"]:
            allocation = {
                "id": str(uuid4()),
                "initiative_id": alloc["initiative_id"],
                "resource_type": alloc["resource_type"],
                "resource_id": alloc.get("resource_id"),
                "amount": alloc["amount"],
                "unit": alloc["unit"],
                "start_date": alloc["start_date"],
                "end_date": alloc["end_date"],
                "status": "active",
                "created_at": datetime.utcnow().isoformat()
            }
            allocations.append(allocation)
        
        # Calculate allocation metrics
        metrics = self._calculate_allocation_metrics(allocations, available_resources)
        
        return {
            "status": "success",
            "allocations": allocations,
            "metrics": metrics,
            "summary": allocation_data["summary"],
            "warnings": allocation_data.get("warnings", []),
            "next_steps": [
                "Review allocation fairness",
                "Confirm resource availability",
                "Set up utilization tracking",
                "Plan for contingencies"
            ]
        }
    
    async def _optimize_allocation(self, agent: ChatCompletionAgent, query: str, context: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Optimize existing resource allocations"""
        
        # Get current allocations and performance data
        current_allocations = context.get("current_allocations", [])
        performance_data = context.get("performance_data", {})
        optimization_goals = context.get("goals", ["efficiency", "cost"])
        
        # Use plugin to optimize
        optimization_result = await self.resource_plugin.optimize_allocation(
            current_allocations=current_allocations,
            performance_metrics=performance_data,
            optimization_goals=optimization_goals
        )
        
        # Parse result
        optimization_data = json.loads(optimization_result)
        
        # Create optimization recommendations
        recommendations = []
        for rec in optimization_data["recommendations"]:
            recommendation = {
                "id": str(uuid4()),
                "type": rec["type"],
                "description": rec["description"],
                "from_allocation": rec.get("from"),
                "to_allocation": rec.get("to"),
                "impact": rec["impact"],
                "effort": rec["effort"],
                "priority": rec["priority"]
            }
            recommendations.append(recommendation)
        
        # Calculate optimization potential
        optimization_potential = self._calculate_optimization_potential(
            current_allocations,
            optimization_data["optimized_allocations"]
        )
        
        return {
            "status": "success",
            "current_state": {
                "efficiency_score": optimization_data["current_efficiency"],
                "cost": optimization_data["current_cost"],
                "utilization": optimization_data["current_utilization"]
            },
            "optimized_state": {
                "efficiency_score": optimization_data["optimized_efficiency"],
                "cost": optimization_data["optimized_cost"],
                "utilization": optimization_data["optimized_utilization"]
            },
            "recommendations": recommendations,
            "optimization_potential": optimization_potential,
            "implementation_plan": optimization_data.get("implementation_plan", []),
            "next_steps": [
                "Review and approve recommendations",
                "Implement high-priority changes",
                "Monitor impact",
                "Iterate on optimization"
            ]
        }
    
    async def _track_utilization(self, agent: ChatCompletionAgent, query: str, context: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Track resource utilization and generate dashboards"""
        
        # Get tracking parameters
        time_period = context.get("time_period", "current_month")
        resource_types = context.get("resource_types", ["all"])
        group_by = context.get("group_by", "initiative")
        
        # Use plugin to get utilization data
        utilization_result = await self.resource_plugin.track_utilization(
            time_period=time_period,
            resource_filters={"types": resource_types},
            aggregation_level=group_by
        )
        
        # Parse result
        utilization_data = json.loads(utilization_result)
        
        # Create utilization dashboard
        dashboard = {
            "summary": {
                "overall_utilization": utilization_data["overall_utilization"],
                "efficiency_score": utilization_data["efficiency_score"],
                "waste_percentage": utilization_data["waste_percentage"],
                "peak_utilization": utilization_data["peak_utilization"]
            },
            "by_resource_type": utilization_data["by_type"],
            "by_initiative": utilization_data["by_initiative"],
            "trends": utilization_data["trends"],
            "alerts": self._generate_utilization_alerts(utilization_data)
        }
        
        # Generate visualizations data
        visualizations = self._create_utilization_visualizations(utilization_data)
        
        return {
            "status": "success",
            "dashboard": dashboard,
            "visualizations": visualizations,
            "insights": utilization_data["insights"],
            "recommendations": utilization_data["recommendations"],
            "export_formats": ["PDF", "Excel", "PowerBI"],
            "next_steps": [
                "Address underutilized resources",
                "Resolve overallocation issues",
                "Optimize resource distribution",
                "Update forecasts"
            ]
        }
    
    async def _forecast_needs(self, agent: ChatCompletionAgent, query: str, context: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Forecast future resource needs"""
        
        # Get forecasting parameters
        forecast_horizon = context.get("horizon", "6_months")
        planned_initiatives = context.get("planned_initiatives", [])
        growth_assumptions = context.get("growth_assumptions", {})
        
        # Use plugin to forecast
        forecast_result = await self.resource_plugin.forecast_needs(
            horizon=forecast_horizon,
            planned_initiatives=planned_initiatives,
            historical_data=context.get("historical_data", {}),
            assumptions=growth_assumptions
        )
        
        # Parse result
        forecast_data = json.loads(forecast_result)
        
        # Create forecast timeline
        forecast_timeline = []
        for period in forecast_data["forecast_periods"]:
            forecast_timeline.append({
                "period": period["period"],
                "resource_needs": period["needs"],
                "capacity_gap": period.get("gap", {}),
                "confidence": period["confidence"],
                "critical_resources": period.get("critical", [])
            })
        
        # Generate procurement recommendations
        procurement_plan = self._generate_procurement_plan(forecast_data)
        
        return {
            "status": "success",
            "forecast": {
                "horizon": forecast_horizon,
                "timeline": forecast_timeline,
                "peak_demand": forecast_data["peak_demand"],
                "total_needs": forecast_data["total_needs"]
            },
            "gaps": forecast_data["capacity_gaps"],
            "procurement_plan": procurement_plan,
            "risk_factors": forecast_data["risks"],
            "confidence_level": forecast_data["overall_confidence"],
            "next_steps": [
                "Validate assumptions",
                "Secure budget approval",
                "Begin procurement process",
                "Develop contingency plans"
            ]
        }
    
    async def _resolve_conflicts(self, agent: ChatCompletionAgent, query: str, context: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Resolve resource conflicts between initiatives"""
        
        # Get conflict details
        conflicts = context.get("conflicts", [])
        priority_framework = context.get("priority_framework", {})
        
        # Use plugin to resolve conflicts
        resolution_result = await self.resource_plugin.resolve_conflicts(
            conflicts=conflicts,
            priority_rules=priority_framework,
            resolution_strategy=context.get("strategy", "balanced")
        )
        
        # Parse result
        resolution_data = json.loads(resolution_result)
        
        # Create resolution plan
        resolutions = []
        for res in resolution_data["resolutions"]:
            resolution = {
                "conflict_id": res["conflict_id"],
                "resolution_type": res["type"],
                "affected_initiatives": res["affected_initiatives"],
                "resource_redistribution": res["redistribution"],
                "impact_assessment": res["impact"],
                "implementation_steps": res["steps"]
            }
            resolutions.append(resolution)
        
        # Calculate trade-offs
        trade_offs = self._analyze_resolution_tradeoffs(resolutions, conflicts)
        
        return {
            "status": "success",
            "conflicts_resolved": len(resolutions),
            "resolutions": resolutions,
            "trade_offs": trade_offs,
            "fairness_score": resolution_data["fairness_score"],
            "stakeholder_impacts": resolution_data["stakeholder_impacts"],
            "implementation_timeline": resolution_data["timeline"],
            "next_steps": [
                "Communicate decisions to stakeholders",
                "Implement resource changes",
                "Monitor for new conflicts",
                "Update resource policies"
            ]
        }
    
    async def _handle_general_query(self, agent: ChatCompletionAgent, query: str, context: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Handle general resource management queries"""
        
        response = await agent.invoke(f"""
Query: {query}
Context: {json.dumps(context, indent=2)}

Please provide resource optimization guidance or answer the question.
""")
        
        return {
            "status": "success",
            "response": response.content,
            "suggestions": [
                "View resource utilization dashboard",
                "Optimize current allocations",
                "Forecast future needs",
                "Resolve resource conflicts"
            ]
        }
    
    def _calculate_allocation_metrics(self, allocations: List[Dict[str, Any]], available: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate metrics for resource allocations"""
        
        metrics = {
            "total_allocated": {},
            "utilization_rate": {},
            "allocation_balance": 0,
            "efficiency_score": 0
        }
        
        # Calculate by resource type
        for resource_type in self.resource_types:
            allocated = sum(a["amount"] for a in allocations if a["resource_type"] == resource_type)
            available_amount = available.get(resource_type, {}).get("total", 0)
            
            metrics["total_allocated"][resource_type] = allocated
            if available_amount > 0:
                metrics["utilization_rate"][resource_type] = allocated / available_amount
        
        # Calculate overall metrics
        utilization_rates = list(metrics["utilization_rate"].values())
        if utilization_rates:
            metrics["allocation_balance"] = 1 - (max(utilization_rates) - min(utilization_rates))
            metrics["efficiency_score"] = sum(utilization_rates) / len(utilization_rates)
        
        return metrics
    
    def _calculate_optimization_potential(self, current: List[Dict[str, Any]], optimized: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate the potential improvement from optimization"""
        
        potential = {
            "efficiency_gain": 0,
            "cost_savings": 0,
            "utilization_improvement": 0,
            "reallocation_count": 0
        }
        
        # This is a simplified calculation
        # In practice, would use more sophisticated metrics
        potential["efficiency_gain"] = 15  # percentage
        potential["cost_savings"] = 50000  # dollars
        potential["utilization_improvement"] = 12  # percentage
        potential["reallocation_count"] = len(current) // 3
        
        return potential
    
    def _generate_utilization_alerts(self, utilization_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate alerts for utilization issues"""
        
        alerts = []
        
        # Check for underutilization
        for resource_type, util in utilization_data.get("by_type", {}).items():
            if util.get("utilization", 0) < 0.5:
                alerts.append({
                    "type": "underutilization",
                    "severity": "warning",
                    "resource": resource_type,
                    "message": f"{resource_type} utilization below 50%",
                    "action": "Consider reallocation or reduction"
                })
            elif util.get("utilization", 0) > 0.95:
                alerts.append({
                    "type": "overutilization",
                    "severity": "critical",
                    "resource": resource_type,
                    "message": f"{resource_type} utilization above 95%",
                    "action": "Add capacity or redistribute load"
                })
        
        return alerts
    
    def _create_utilization_visualizations(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create visualization data for utilization dashboard"""
        
        return {
            "charts": [
                {
                    "type": "gauge",
                    "title": "Overall Utilization",
                    "value": data["overall_utilization"],
                    "target": 85,
                    "ranges": {"low": 50, "medium": 70, "high": 85}
                },
                {
                    "type": "bar",
                    "title": "Utilization by Type",
                    "data": data["by_type"],
                    "axis": {"x": "Resource Type", "y": "Utilization %"}
                },
                {
                    "type": "line",
                    "title": "Utilization Trend",
                    "data": data["trends"],
                    "axis": {"x": "Time", "y": "Utilization %"}
                },
                {
                    "type": "heatmap",
                    "title": "Resource-Initiative Matrix",
                    "data": data.get("matrix", {}),
                    "axis": {"x": "Initiatives", "y": "Resources"}
                }
            ]
        }
    
    def _generate_procurement_plan(self, forecast_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate procurement recommendations based on forecast"""
        
        plan = {
            "immediate_needs": [],
            "future_needs": [],
            "budget_requirements": 0,
            "timeline": []
        }
        
        # Analyze gaps and create procurement items
        for gap in forecast_data.get("capacity_gaps", []):
            if gap["urgency"] == "immediate":
                plan["immediate_needs"].append({
                    "resource": gap["resource"],
                    "quantity": gap["quantity"],
                    "estimated_cost": gap.get("cost", 0),
                    "lead_time": gap.get("lead_time", "2 weeks")
                })
            else:
                plan["future_needs"].append({
                    "resource": gap["resource"],
                    "quantity": gap["quantity"],
                    "needed_by": gap["needed_by"],
                    "estimated_cost": gap.get("cost", 0)
                })
        
        # Calculate total budget
        plan["budget_requirements"] = sum(
            item.get("estimated_cost", 0) 
            for item in plan["immediate_needs"] + plan["future_needs"]
        )
        
        return plan
    
    def _analyze_resolution_tradeoffs(self, resolutions: List[Dict[str, Any]], conflicts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze trade-offs in conflict resolutions"""
        
        trade_offs = {
            "winners": [],
            "losers": [],
            "neutral": [],
            "overall_fairness": 0,
            "strategic_alignment": 0
        }
        
        # Simple analysis of impacts
        for resolution in resolutions:
            for initiative in resolution["affected_initiatives"]:
                impact = initiative.get("impact", "neutral")
                if impact == "positive":
                    trade_offs["winners"].append(initiative["id"])
                elif impact == "negative":
                    trade_offs["losers"].append(initiative["id"])
                else:
                    trade_offs["neutral"].append(initiative["id"])
        
        # Calculate fairness
        total = len(trade_offs["winners"]) + len(trade_offs["losers"]) + len(trade_offs["neutral"])
        if total > 0:
            trade_offs["overall_fairness"] = len(trade_offs["neutral"]) / total
        
        return trade_offs