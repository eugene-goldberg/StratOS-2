"""Initiative Generation Agent

Creates strategic initiatives aligned with organizational goals and North Star.
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
from .plugins.initiative_plugin import InitiativePlugin


class InitiativeGenerationAgent(BaseStratosAgent):
    """Agent responsible for generating and managing strategic initiatives"""
    
    def __init__(self):
        super().__init__(
            name="Initiative Generation Agent",
            description="Creates strategic initiatives and action plans aligned with organizational goals",
            model="gpt-4"  # Use GPT-4 for complex strategic planning
        )
        
        # Initialize initiative plugin
        self.initiative_plugin = InitiativePlugin()
        self.kernel.add_plugin(self.initiative_plugin, "InitiativePlugin")
        
        # Initiative types and templates
        self.initiative_types = {
            "strategic": "Long-term transformational initiatives",
            "tactical": "Medium-term operational improvements",
            "quick_win": "Short-term high-impact projects",
            "innovation": "Experimental or R&D initiatives",
            "compliance": "Regulatory or compliance-driven projects"
        }
        
    async def _create_initiative_agent(self) -> ChatCompletionAgent:
        """Create the initiative generation agent with specific instructions"""
        
        instructions = """You are a strategic planning expert specializing in initiative creation and management.

Your capabilities include:
1. **Initiative Generation**: Create strategic initiatives aligned with organizational goals
2. **Action Planning**: Break down initiatives into actionable steps
3. **Goal Alignment**: Ensure initiatives support North Star elements
4. **Resource Planning**: Estimate resource requirements
5. **Timeline Development**: Create realistic project timelines
6. **Success Metrics**: Define KPIs and success criteria

When generating initiatives:
- Align with strategic goals and North Star vision
- Consider resource constraints and capacity
- Create SMART objectives (Specific, Measurable, Achievable, Relevant, Time-bound)
- Identify key stakeholders and dependencies
- Define clear success metrics
- Consider risks and mitigation strategies

Initiative components:
- Clear objective and expected outcomes
- Alignment with strategic goals
- Resource requirements (budget, people, technology)
- Timeline with milestones
- Success metrics and KPIs
- Risk assessment

Available functions:
- GenerateInitiative: Create new strategic initiatives
- CreateActionPlan: Break down initiatives into tasks
- EstimateResources: Calculate resource requirements
- AlignWithGoals: Map initiatives to strategic goals
- DefineMilestones: Create project milestones
- AssessRisks: Identify and assess initiative risks"""

        return ChatCompletionAgent(
            service_id="initiative_agent",
            kernel=self.kernel,
            name="InitiativeExpert",
            instructions=instructions
        )
        
    async def process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process initiative generation requests"""
        
        try:
            query = request.get("query", "")
            context = request.get("context", {})
            user_id = request.get("user_id")
            
            # Create initiative agent
            agent = await self._create_initiative_agent()
            
            # Determine request type
            request_type = self._determine_request_type(query, context)
            
            if request_type == "generate_initiative":
                return await self._generate_initiative(agent, query, context, user_id)
            elif request_type == "create_action_plan":
                return await self._create_action_plan(agent, query, context, user_id)
            elif request_type == "bulk_generation":
                return await self._generate_multiple_initiatives(agent, query, context, user_id)
            elif request_type == "initiative_variants":
                return await self._generate_variants(agent, query, context, user_id)
            else:
                # General initiative query
                return await self._handle_general_query(agent, query, context, user_id)
                
        except Exception as e:
            return {
                "status": "error",
                "message": f"Initiative generation failed: {str(e)}"
            }
    
    def _determine_request_type(self, query: str, context: Dict[str, Any]) -> str:
        """Determine the type of initiative request"""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ["create initiative", "new initiative", "generate initiative"]):
            return "generate_initiative"
        elif any(word in query_lower for word in ["action plan", "break down", "tasks", "steps"]):
            return "create_action_plan"
        elif any(word in query_lower for word in ["multiple", "several", "bulk", "initiatives for"]):
            return "bulk_generation"
        elif any(word in query_lower for word in ["variants", "alternatives", "options"]):
            return "initiative_variants"
        else:
            return "general"
    
    async def _generate_initiative(self, agent: ChatCompletionAgent, query: str, context: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Generate a strategic initiative"""
        
        # Gather context
        strategic_goals = context.get("strategic_goals", [])
        north_star = context.get("north_star", {})
        constraints = context.get("constraints", {})
        initiative_type = context.get("type", "strategic")
        
        # Use plugin to generate initiative
        initiative_result = await self.initiative_plugin.generate_initiative(
            objective=query,
            strategic_goals=strategic_goals,
            north_star_context=north_star,
            initiative_type=initiative_type,
            constraints=constraints
        )
        
        # Parse result
        initiative_data = json.loads(initiative_result)
        
        # Create initiative object
        initiative = {
            "id": str(uuid4()),
            "user_id": user_id,
            "title": initiative_data["title"],
            "description": initiative_data["description"],
            "type": initiative_type,
            "status": "draft",
            "strategic_goals": initiative_data["aligned_goals"],
            "expected_outcomes": initiative_data["expected_outcomes"],
            "success_metrics": initiative_data["success_metrics"],
            "resource_requirements": initiative_data["resources"],
            "timeline": initiative_data["timeline"],
            "risks": initiative_data["risks"],
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        # Generate initial action plan
        actions = await self._generate_actions_for_initiative(initiative)
        
        return {
            "status": "success",
            "initiative": initiative,
            "actions": actions,
            "summary": self._generate_initiative_summary(initiative),
            "next_steps": [
                "Review and refine the initiative",
                "Assign resources and owners",
                "Set up progress tracking",
                "Create detailed project plan"
            ]
        }
    
    async def _create_action_plan(self, agent: ChatCompletionAgent, query: str, context: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Create an action plan for an initiative"""
        
        initiative = context.get("initiative", {})
        detail_level = context.get("detail_level", "standard")
        
        if not initiative:
            return {
                "status": "error",
                "message": "No initiative provided. Please specify an initiative to create an action plan for."
            }
        
        # Use plugin to create action plan
        action_plan_result = await self.initiative_plugin.create_action_plan(
            initiative=initiative,
            detail_level=detail_level,
            dependencies_enabled=True
        )
        
        # Parse result
        action_plan_data = json.loads(action_plan_result)
        
        # Structure actions with proper metadata
        actions = []
        for idx, action_data in enumerate(action_plan_data["actions"]):
            action = {
                "id": str(uuid4()),
                "initiative_id": initiative.get("id"),
                "title": action_data["title"],
                "description": action_data["description"],
                "type": action_data["type"],
                "status": "not_started",
                "priority": action_data["priority"],
                "estimated_hours": action_data["estimated_hours"],
                "dependencies": action_data.get("dependencies", []),
                "success_criteria": action_data["success_criteria"],
                "order": idx + 1,
                "created_at": datetime.utcnow().isoformat()
            }
            actions.append(action)
        
        # Calculate critical path
        critical_path = self._calculate_critical_path(actions)
        
        return {
            "status": "success",
            "action_plan": {
                "initiative_id": initiative.get("id"),
                "total_actions": len(actions),
                "estimated_duration": action_plan_data["total_duration"],
                "critical_path": critical_path,
                "actions": actions
            },
            "visualization": self._create_gantt_data(actions),
            "next_steps": [
                "Assign owners to actions",
                "Set specific deadlines",
                "Identify resource needs",
                "Begin execution"
            ]
        }
    
    async def _generate_multiple_initiatives(self, agent: ChatCompletionAgent, query: str, context: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Generate multiple related initiatives"""
        
        theme = context.get("theme", "")
        count = context.get("count", 3)
        strategic_goals = context.get("strategic_goals", [])
        
        # Use plugin to generate multiple initiatives
        bulk_result = await self.initiative_plugin.generate_bulk_initiatives(
            theme=theme,
            count=count,
            strategic_goals=strategic_goals,
            diversity_factor="high"
        )
        
        # Parse result
        bulk_data = json.loads(bulk_result)
        
        initiatives = []
        for init_data in bulk_data["initiatives"]:
            initiative = {
                "id": str(uuid4()),
                "user_id": user_id,
                "title": init_data["title"],
                "description": init_data["description"],
                "type": init_data["type"],
                "status": "draft",
                "priority": init_data["priority"],
                "estimated_impact": init_data["impact"],
                "estimated_effort": init_data["effort"],
                "quick_win": init_data["effort"] == "low" and init_data["impact"] == "high",
                "created_at": datetime.utcnow().isoformat()
            }
            initiatives.append(initiative)
        
        # Create portfolio view
        portfolio_analysis = self._analyze_initiative_portfolio(initiatives)
        
        return {
            "status": "success",
            "initiatives": initiatives,
            "portfolio_analysis": portfolio_analysis,
            "summary": f"Generated {len(initiatives)} initiatives around {theme}",
            "next_steps": [
                "Prioritize initiatives",
                "Assess resource availability",
                "Select initiatives for implementation",
                "Create detailed plans for selected initiatives"
            ]
        }
    
    async def _generate_variants(self, agent: ChatCompletionAgent, query: str, context: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Generate variant approaches for an initiative"""
        
        base_initiative = context.get("initiative", {})
        variant_count = context.get("count", 3)
        
        # Use plugin to generate variants
        variants_result = await self.initiative_plugin.generate_variants(
            base_initiative=base_initiative,
            variant_count=variant_count,
            variation_factors=["timeline", "resources", "approach", "scope"]
        )
        
        # Parse result
        variants_data = json.loads(variants_result)
        
        # Structure variants with comparison data
        variants = []
        for var_data in variants_data["variants"]:
            variant = {
                "id": str(uuid4()),
                "base_initiative_id": base_initiative.get("id"),
                "title": var_data["title"],
                "approach": var_data["approach"],
                "key_differences": var_data["differences"],
                "pros": var_data["pros"],
                "cons": var_data["cons"],
                "resource_delta": var_data["resource_delta"],
                "timeline_delta": var_data["timeline_delta"],
                "risk_profile": var_data["risk_profile"]
            }
            variants.append(variant)
        
        # Create comparison matrix
        comparison = self._create_comparison_matrix(base_initiative, variants)
        
        return {
            "status": "success",
            "base_initiative": base_initiative,
            "variants": variants,
            "comparison_matrix": comparison,
            "recommendation": variants_data.get("recommendation", ""),
            "next_steps": [
                "Review variant trade-offs",
                "Select preferred approach",
                "Refine selected variant",
                "Proceed with implementation planning"
            ]
        }
    
    async def _handle_general_query(self, agent: ChatCompletionAgent, query: str, context: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Handle general initiative planning queries"""
        
        response = await agent.invoke(f"""
Query: {query}
Context: {json.dumps(context, indent=2)}

Please provide strategic initiative planning guidance or answer the question.
""")
        
        return {
            "status": "success",
            "response": response.content,
            "suggestions": [
                "Create a new strategic initiative",
                "Generate action plan for existing initiative",
                "Explore initiative variants",
                "View initiative portfolio"
            ]
        }
    
    async def _generate_actions_for_initiative(self, initiative: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate initial actions for an initiative"""
        
        # Use plugin to generate actions
        actions_result = await self.initiative_plugin.generate_actions(
            initiative_title=initiative["title"],
            initiative_description=initiative["description"],
            timeline=initiative["timeline"],
            action_count=5  # Generate top 5 actions
        )
        
        actions_data = json.loads(actions_result)
        
        actions = []
        for action_data in actions_data["actions"]:
            action = {
                "id": str(uuid4()),
                "title": action_data["title"],
                "description": action_data["description"],
                "estimated_duration": action_data["duration"],
                "priority": action_data["priority"]
            }
            actions.append(action)
        
        return actions
    
    def _generate_initiative_summary(self, initiative: Dict[str, Any]) -> str:
        """Generate a summary of the initiative"""
        
        duration = initiative["timeline"].get("total_duration", "TBD")
        resource_count = len(initiative["resource_requirements"])
        metric_count = len(initiative["success_metrics"])
        
        return f"{initiative['title']} - {initiative['type']} initiative with {duration} timeline, requiring {resource_count} resources, measuring success with {metric_count} KPIs"
    
    def _calculate_critical_path(self, actions: List[Dict[str, Any]]) -> List[str]:
        """Calculate the critical path through actions"""
        
        # Simple critical path identification based on dependencies
        critical_actions = []
        
        # Find actions with no dependencies (starting points)
        start_actions = [a for a in actions if not a.get("dependencies", [])]
        
        # For now, return a simple path
        if start_actions:
            critical_actions = [start_actions[0]["id"]]
        
        return critical_actions
    
    def _create_gantt_data(self, actions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create Gantt chart data for action visualization"""
        
        gantt_data = {
            "tasks": [],
            "dependencies": []
        }
        
        start_date = datetime.utcnow()
        current_date = start_date
        
        for action in actions:
            duration_days = action.get("estimated_hours", 8) / 8  # Convert hours to days
            
            task = {
                "id": action["id"],
                "name": action["title"],
                "start": current_date.isoformat(),
                "end": (current_date + timedelta(days=duration_days)).isoformat(),
                "progress": 0
            }
            gantt_data["tasks"].append(task)
            
            # Add dependencies
            for dep_id in action.get("dependencies", []):
                gantt_data["dependencies"].append({
                    "source": dep_id,
                    "target": action["id"]
                })
            
            current_date += timedelta(days=duration_days)
        
        return gantt_data
    
    def _analyze_initiative_portfolio(self, initiatives: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze a portfolio of initiatives"""
        
        portfolio = {
            "total_count": len(initiatives),
            "by_type": {},
            "by_priority": {},
            "quick_wins": [],
            "resource_intensive": [],
            "balanced_scorecard": {
                "financial": 0,
                "customer": 0,
                "internal_process": 0,
                "learning_growth": 0
            }
        }
        
        for initiative in initiatives:
            # Count by type
            init_type = initiative.get("type", "other")
            portfolio["by_type"][init_type] = portfolio["by_type"].get(init_type, 0) + 1
            
            # Count by priority
            priority = initiative.get("priority", "medium")
            portfolio["by_priority"][priority] = portfolio["by_priority"].get(priority, 0) + 1
            
            # Identify quick wins
            if initiative.get("quick_win", False):
                portfolio["quick_wins"].append(initiative["id"])
            
            # Identify resource intensive
            if initiative.get("estimated_effort") == "high":
                portfolio["resource_intensive"].append(initiative["id"])
        
        return portfolio
    
    def _create_comparison_matrix(self, base: Dict[str, Any], variants: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create a comparison matrix for initiative variants"""
        
        matrix = {
            "criteria": ["Timeline", "Resources", "Risk", "Impact", "Complexity"],
            "options": [
                {
                    "id": base.get("id"),
                    "name": "Base Plan",
                    "scores": [3, 3, 3, 3, 3]  # Baseline scores
                }
            ]
        }
        
        for variant in variants:
            scores = []
            
            # Score based on deltas
            timeline_delta = variant.get("timeline_delta", 0)
            scores.append(3 + (1 if timeline_delta < 0 else -1 if timeline_delta > 0 else 0))
            
            resource_delta = variant.get("resource_delta", 0)
            scores.append(3 + (-1 if resource_delta > 0 else 1 if resource_delta < 0 else 0))
            
            risk_profile = variant.get("risk_profile", "medium")
            scores.append(4 if risk_profile == "low" else 2 if risk_profile == "high" else 3)
            
            # Default scores for impact and complexity
            scores.extend([3, 3])
            
            matrix["options"].append({
                "id": variant["id"],
                "name": variant["title"],
                "scores": scores
            })
        
        return matrix