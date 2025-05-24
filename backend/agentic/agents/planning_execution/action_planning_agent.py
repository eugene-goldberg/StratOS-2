"""Action Planning Agent

Breaks down initiatives into actionable tasks, manages dependencies, and creates execution plans.
"""

import asyncio
import json
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from uuid import uuid4

from semantic_kernel import Kernel
from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.contents import ChatMessageContent, AuthorRole

from common.base_agent import BaseStratosAgent
from .plugins.action_plugin import ActionPlugin


class ActionPlanningAgent(BaseStratosAgent):
    """Agent responsible for breaking down initiatives into actionable tasks"""
    
    def __init__(self):
        super().__init__(
            name="Action Planning Agent",
            description="Creates detailed action plans with tasks, dependencies, and timelines",
            model="gpt-4"  # Use GPT-4 for complex task breakdown
        )
        
        # Initialize action plugin
        self.action_plugin = ActionPlugin()
        self.kernel.add_plugin(self.action_plugin, "ActionPlugin")
        
        # Action types and templates
        self.action_types = {
            "preparation": "Setup and planning tasks",
            "execution": "Core implementation tasks",
            "validation": "Testing and verification tasks",
            "deployment": "Rollout and launch tasks",
            "monitoring": "Ongoing tracking tasks"
        }
        
        # Dependency types
        self.dependency_types = {
            "finish_to_start": "Previous task must complete before this starts",
            "start_to_start": "Tasks must start together",
            "finish_to_finish": "Tasks must finish together",
            "start_to_finish": "Previous task must start before this finishes"
        }
        
    async def _create_action_agent(self) -> ChatCompletionAgent:
        """Create the action planning agent with specific instructions"""
        
        instructions = """You are an expert project planner specializing in breaking down strategic initiatives into executable tasks.

Your capabilities include:
1. **Task Breakdown**: Decompose initiatives into concrete, actionable tasks
2. **Dependency Mapping**: Identify and manage task dependencies
3. **Timeline Development**: Create realistic schedules with milestones
4. **Resource Assignment**: Match tasks with required skills and resources
5. **Risk Identification**: Spot potential execution risks in plans
6. **Progress Tracking**: Define success criteria and tracking mechanisms

When creating action plans:
- Use SMART criteria (Specific, Measurable, Achievable, Relevant, Time-bound)
- Consider dependencies and sequencing
- Balance workload across resources
- Build in buffers for uncertainty
- Define clear deliverables
- Include validation steps

Task planning principles:
- Right-size tasks (not too big, not too small)
- Clear ownership and accountability
- Measurable outcomes
- Realistic timelines
- Risk mitigation built-in

Available functions:
- BreakdownInitiative: Decompose initiative into tasks
- CreateDependencies: Map task relationships
- EstimateTimeline: Calculate durations and dates
- AssignResources: Match tasks to people/skills
- IdentifyRisks: Find execution risks
- GenerateGantt: Create visual timeline
- OptimizeSchedule: Improve task sequencing"""

        return ChatCompletionAgent(
            service_id="action_agent",
            kernel=self.kernel,
            name="ActionPlanner",
            instructions=instructions
        )
        
    async def process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process action planning requests"""
        
        try:
            query = request.get("query", "")
            context = request.get("context", {})
            user_id = request.get("user_id")
            
            # Create action agent
            agent = await self._create_action_agent()
            
            # Determine request type
            request_type = self._determine_request_type(query, context)
            
            if request_type == "breakdown":
                return await self._breakdown_initiative(agent, query, context, user_id)
            elif request_type == "dependencies":
                return await self._manage_dependencies(agent, query, context, user_id)
            elif request_type == "timeline":
                return await self._create_timeline(agent, query, context, user_id)
            elif request_type == "optimize":
                return await self._optimize_schedule(agent, query, context, user_id)
            elif request_type == "track":
                return await self._track_progress(agent, query, context, user_id)
            else:
                # General action planning query
                return await self._handle_general_query(agent, query, context, user_id)
                
        except Exception as e:
            return {
                "status": "error",
                "message": f"Action planning failed: {str(e)}"
            }
    
    def _determine_request_type(self, query: str, context: Dict[str, Any]) -> str:
        """Determine the type of action planning request"""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ["breakdown", "decompose", "tasks", "actions"]):
            return "breakdown"
        elif any(word in query_lower for word in ["dependencies", "sequence", "order", "prerequisite"]):
            return "dependencies"
        elif any(word in query_lower for word in ["timeline", "schedule", "duration", "dates"]):
            return "timeline"
        elif any(word in query_lower for word in ["optimize", "improve", "compress", "accelerate"]):
            return "optimize"
        elif any(word in query_lower for word in ["track", "progress", "status", "completion"]):
            return "track"
        else:
            return "general"
    
    async def _breakdown_initiative(self, agent: ChatCompletionAgent, query: str, context: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Break down an initiative into actionable tasks"""
        
        # Get initiative details
        initiative = context.get("initiative", {})
        breakdown_depth = context.get("depth", "detailed")
        include_templates = context.get("use_templates", True)
        
        # Use plugin to breakdown initiative
        breakdown_result = await self.action_plugin.breakdown_initiative(
            initiative=initiative,
            breakdown_level=breakdown_depth,
            include_subtasks=True,
            use_templates=include_templates
        )
        
        # Parse result
        breakdown_data = json.loads(breakdown_result)
        
        # Create structured action plan
        action_plan = {
            "id": str(uuid4()),
            "initiative_id": initiative.get("id"),
            "initiative_title": initiative.get("title"),
            "total_tasks": len(breakdown_data["tasks"]),
            "phases": {},
            "tasks": [],
            "milestones": [],
            "created_at": datetime.utcnow().isoformat()
        }
        
        # Organize tasks by phase
        for task_data in breakdown_data["tasks"]:
            phase = task_data.get("phase", "execution")
            if phase not in action_plan["phases"]:
                action_plan["phases"][phase] = []
            
            task = {
                "id": str(uuid4()),
                "title": task_data["title"],
                "description": task_data["description"],
                "type": task_data["type"],
                "phase": phase,
                "priority": task_data["priority"],
                "estimated_hours": task_data["estimated_hours"],
                "required_skills": task_data.get("required_skills", []),
                "deliverables": task_data.get("deliverables", []),
                "success_criteria": task_data.get("success_criteria", ""),
                "status": "not_started",
                "created_at": datetime.utcnow().isoformat()
            }
            
            action_plan["tasks"].append(task)
            action_plan["phases"][phase].append(task["id"])
        
        # Extract milestones
        for milestone in breakdown_data.get("milestones", []):
            action_plan["milestones"].append({
                "id": str(uuid4()),
                "name": milestone["name"],
                "target_date": milestone["date"],
                "criteria": milestone["criteria"],
                "phase": milestone.get("phase", "")
            })
        
        # Generate task statistics
        statistics = self._calculate_plan_statistics(action_plan)
        
        # Create work breakdown structure (WBS)
        wbs = self._create_wbs(action_plan)
        
        return {
            "status": "success",
            "action_plan": action_plan,
            "statistics": statistics,
            "work_breakdown_structure": wbs,
            "recommendations": breakdown_data.get("recommendations", []),
            "risks": breakdown_data.get("identified_risks", []),
            "next_steps": [
                "Review and refine task list",
                "Map task dependencies",
                "Assign resources to tasks",
                "Create project timeline"
            ]
        }
    
    async def _manage_dependencies(self, agent: ChatCompletionAgent, query: str, context: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Manage task dependencies and sequencing"""
        
        # Get tasks and existing dependencies
        tasks = context.get("tasks", [])
        existing_dependencies = context.get("dependencies", [])
        auto_detect = context.get("auto_detect", True)
        
        # Use plugin to manage dependencies
        dependency_result = await self.action_plugin.create_dependencies(
            tasks=tasks,
            existing_dependencies=existing_dependencies,
            auto_detect=auto_detect,
            validate_cycles=True
        )
        
        # Parse result
        dependency_data = json.loads(dependency_result)
        
        # Create dependency map
        dependency_map = {
            "dependencies": [],
            "critical_path": [],
            "parallel_tracks": [],
            "bottlenecks": []
        }
        
        # Structure dependencies
        for dep in dependency_data["dependencies"]:
            dependency = {
                "id": str(uuid4()),
                "from_task": dep["from_task"],
                "to_task": dep["to_task"],
                "type": dep["type"],
                "lag_time": dep.get("lag_time", 0),
                "constraint": dep.get("constraint", ""),
                "rationale": dep.get("rationale", "")
            }
            dependency_map["dependencies"].append(dependency)
        
        # Identify critical path
        dependency_map["critical_path"] = dependency_data.get("critical_path", [])
        
        # Find parallel execution opportunities
        dependency_map["parallel_tracks"] = dependency_data.get("parallel_tracks", [])
        
        # Identify bottlenecks
        for bottleneck in dependency_data.get("bottlenecks", []):
            dependency_map["bottlenecks"].append({
                "task_id": bottleneck["task"],
                "dependent_count": bottleneck["dependent_count"],
                "impact": bottleneck["impact"],
                "mitigation": bottleneck.get("mitigation", "")
            })
        
        # Generate network diagram data
        network_diagram = self._create_network_diagram(tasks, dependency_map["dependencies"])
        
        # Validation results
        validation = dependency_data.get("validation", {})
        
        return {
            "status": "success",
            "dependency_map": dependency_map,
            "network_diagram": network_diagram,
            "validation": validation,
            "optimization_opportunities": dependency_data.get("optimization_opportunities", []),
            "warnings": dependency_data.get("warnings", []),
            "next_steps": [
                "Review critical path",
                "Optimize bottlenecks",
                "Validate dependencies with team",
                "Update project schedule"
            ]
        }
    
    async def _create_timeline(self, agent: ChatCompletionAgent, query: str, context: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Create project timeline with realistic scheduling"""
        
        # Get timeline inputs
        tasks = context.get("tasks", [])
        dependencies = context.get("dependencies", [])
        constraints = context.get("constraints", {})
        start_date = context.get("start_date", datetime.utcnow().isoformat())
        
        # Use plugin to create timeline
        timeline_result = await self.action_plugin.estimate_timeline(
            tasks=tasks,
            dependencies=dependencies,
            start_date=start_date,
            constraints=constraints,
            include_buffers=True
        )
        
        # Parse result
        timeline_data = json.loads(timeline_result)
        
        # Create detailed schedule
        schedule = {
            "project_start": timeline_data["project_start"],
            "project_end": timeline_data["project_end"],
            "total_duration": timeline_data["total_duration"],
            "phases": [],
            "tasks": [],
            "milestones": []
        }
        
        # Schedule tasks
        for task_schedule in timeline_data["task_schedule"]:
            scheduled_task = {
                "task_id": task_schedule["task_id"],
                "task_name": task_schedule["task_name"],
                "start_date": task_schedule["start_date"],
                "end_date": task_schedule["end_date"],
                "duration_days": task_schedule["duration_days"],
                "float": task_schedule.get("float", 0),
                "is_critical": task_schedule.get("is_critical", False),
                "resources": task_schedule.get("assigned_resources", [])
            }
            schedule["tasks"].append(scheduled_task)
        
        # Add phase timeline
        for phase in timeline_data.get("phases", []):
            schedule["phases"].append({
                "name": phase["name"],
                "start_date": phase["start_date"],
                "end_date": phase["end_date"],
                "duration": phase["duration"],
                "task_count": phase["task_count"]
            })
        
        # Add milestones to timeline
        for milestone in timeline_data.get("milestones", []):
            schedule["milestones"].append({
                "name": milestone["name"],
                "date": milestone["date"],
                "phase": milestone["phase"],
                "dependencies": milestone.get("dependencies", [])
            })
        
        # Generate Gantt chart data
        gantt_data = self._create_gantt_chart(schedule)
        
        # Resource loading analysis
        resource_loading = timeline_data.get("resource_loading", {})
        
        return {
            "status": "success",
            "schedule": schedule,
            "gantt_chart": gantt_data,
            "resource_loading": resource_loading,
            "timeline_metrics": {
                "total_duration": timeline_data["total_duration"],
                "critical_path_length": timeline_data.get("critical_path_duration", ""),
                "resource_utilization": timeline_data.get("average_utilization", 0),
                "schedule_efficiency": timeline_data.get("efficiency_score", 0)
            },
            "risks": timeline_data.get("schedule_risks", []),
            "recommendations": timeline_data.get("recommendations", []),
            "next_steps": [
                "Review timeline with stakeholders",
                "Confirm resource availability",
                "Set up progress tracking",
                "Communicate schedule"
            ]
        }
    
    async def _optimize_schedule(self, agent: ChatCompletionAgent, query: str, context: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Optimize project schedule for efficiency"""
        
        # Get optimization inputs
        current_schedule = context.get("schedule", {})
        optimization_goals = context.get("goals", ["duration", "resource_leveling"])
        constraints = context.get("constraints", {})
        
        # Use plugin to optimize
        optimization_result = await self.action_plugin.optimize_schedule(
            schedule=current_schedule,
            optimization_goals=optimization_goals,
            constraints=constraints,
            preserve_dependencies=True
        )
        
        # Parse result
        optimization_data = json.loads(optimization_result)
        
        # Create optimization report
        optimization_report = {
            "original_metrics": optimization_data["original_metrics"],
            "optimized_metrics": optimization_data["optimized_metrics"],
            "improvements": {},
            "changes": [],
            "trade_offs": []
        }
        
        # Calculate improvements
        orig = optimization_data["original_metrics"]
        opt = optimization_data["optimized_metrics"]
        
        optimization_report["improvements"] = {
            "duration_reduction": f"{orig['duration'] - opt['duration']} days",
            "cost_savings": f"${orig.get('cost', 0) - opt.get('cost', 0)}",
            "resource_efficiency": f"{opt.get('efficiency', 0) - orig.get('efficiency', 0)}%"
        }
        
        # Document changes
        for change in optimization_data["changes"]:
            optimization_report["changes"].append({
                "type": change["type"],
                "description": change["description"],
                "impact": change["impact"],
                "tasks_affected": change.get("affected_tasks", [])
            })
        
        # Identify trade-offs
        optimization_report["trade_offs"] = optimization_data.get("trade_offs", [])
        
        # Create optimized schedule
        optimized_schedule = optimization_data["optimized_schedule"]
        
        # Sensitivity analysis
        sensitivity = optimization_data.get("sensitivity_analysis", {})
        
        return {
            "status": "success",
            "optimization_report": optimization_report,
            "optimized_schedule": optimized_schedule,
            "sensitivity_analysis": sensitivity,
            "implementation_plan": optimization_data.get("implementation_steps", []),
            "risks": optimization_data.get("optimization_risks", []),
            "approval_required": optimization_data.get("major_changes", False),
            "next_steps": [
                "Review optimization recommendations",
                "Validate with project team",
                "Approve changes",
                "Implement new schedule"
            ]
        }
    
    async def _track_progress(self, agent: ChatCompletionAgent, query: str, context: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Track action plan progress and completion"""
        
        # Get tracking inputs
        action_plan = context.get("action_plan", {})
        progress_updates = context.get("updates", [])
        as_of_date = context.get("as_of_date", datetime.utcnow().isoformat())
        
        # Use plugin to track progress
        tracking_result = await self.action_plugin.track_progress(
            action_plan=action_plan,
            progress_data=progress_updates,
            calculate_projections=True
        )
        
        # Parse result
        tracking_data = json.loads(tracking_result)
        
        # Create progress report
        progress_report = {
            "overall_progress": tracking_data["overall_progress"],
            "phase_progress": {},
            "task_status": {
                "completed": [],
                "in_progress": [],
                "blocked": [],
                "not_started": []
            },
            "milestone_status": [],
            "metrics": {}
        }
        
        # Phase-level progress
        for phase, data in tracking_data["phase_progress"].items():
            progress_report["phase_progress"][phase] = {
                "progress_percentage": data["percentage"],
                "tasks_completed": data["completed"],
                "tasks_total": data["total"],
                "on_track": data.get("on_track", True)
            }
        
        # Task status categorization
        for task in tracking_data["tasks"]:
            status = task["status"]
            task_info = {
                "id": task["id"],
                "name": task["name"],
                "progress": task.get("progress", 0),
                "due_date": task.get("due_date", ""),
                "owner": task.get("owner", "")
            }
            
            if status in progress_report["task_status"]:
                progress_report["task_status"][status].append(task_info)
        
        # Milestone tracking
        for milestone in tracking_data.get("milestones", []):
            progress_report["milestone_status"].append({
                "name": milestone["name"],
                "target_date": milestone["target_date"],
                "status": milestone["status"],
                "completion_percentage": milestone.get("completion", 0),
                "at_risk": milestone.get("at_risk", False)
            })
        
        # Key metrics
        progress_report["metrics"] = {
            "schedule_variance": tracking_data.get("schedule_variance", 0),
            "effort_variance": tracking_data.get("effort_variance", 0),
            "velocity": tracking_data.get("velocity", 0),
            "burn_rate": tracking_data.get("burn_rate", 0)
        }
        
        # Generate projections
        projections = tracking_data.get("projections", {})
        
        # Identify issues and risks
        issues = self._identify_progress_issues(tracking_data)
        
        # Create dashboard data
        dashboard = self._create_progress_dashboard(progress_report)
        
        return {
            "status": "success",
            "progress_report": progress_report,
            "projections": projections,
            "issues": issues,
            "dashboard": dashboard,
            "recommendations": tracking_data.get("recommendations", []),
            "alerts": tracking_data.get("alerts", []),
            "next_steps": [
                "Address blocked tasks",
                "Update resource allocations",
                "Communicate progress to stakeholders",
                "Adjust timeline if needed"
            ]
        }
    
    async def _handle_general_query(self, agent: ChatCompletionAgent, query: str, context: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Handle general action planning queries"""
        
        response = await agent.invoke(f"""
Query: {query}
Context: {json.dumps(context, indent=2)}

Please provide action planning guidance or answer the question.
""")
        
        return {
            "status": "success",
            "response": response.content,
            "suggestions": [
                "Break down initiative into tasks",
                "Create project timeline",
                "Optimize task schedule",
                "Track progress"
            ]
        }
    
    def _calculate_plan_statistics(self, action_plan: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate statistics for the action plan"""
        
        tasks = action_plan["tasks"]
        
        statistics = {
            "total_tasks": len(tasks),
            "total_effort_hours": sum(t.get("estimated_hours", 0) for t in tasks),
            "by_phase": {},
            "by_priority": {},
            "by_type": {},
            "complexity_score": 0
        }
        
        # Count by phase
        for phase, task_ids in action_plan["phases"].items():
            statistics["by_phase"][phase] = len(task_ids)
        
        # Count by priority and type
        for task in tasks:
            priority = task.get("priority", "medium")
            task_type = task.get("type", "execution")
            
            statistics["by_priority"][priority] = statistics["by_priority"].get(priority, 0) + 1
            statistics["by_type"][task_type] = statistics["by_type"].get(task_type, 0) + 1
        
        # Calculate complexity score
        statistics["complexity_score"] = min(100, len(tasks) * 2 + len(action_plan.get("milestones", [])) * 5)
        
        return statistics
    
    def _create_wbs(self, action_plan: Dict[str, Any]) -> Dict[str, Any]:
        """Create Work Breakdown Structure"""
        
        wbs = {
            "id": "root",
            "name": action_plan["initiative_title"],
            "type": "initiative",
            "children": []
        }
        
        # Create phase nodes
        for phase, task_ids in action_plan["phases"].items():
            phase_node = {
                "id": f"phase_{phase}",
                "name": phase.replace("_", " ").title(),
                "type": "phase",
                "children": []
            }
            
            # Add tasks to phase
            for task_id in task_ids:
                task = next((t for t in action_plan["tasks"] if t["id"] == task_id), None)
                if task:
                    task_node = {
                        "id": task_id,
                        "name": task["title"],
                        "type": "task",
                        "effort": task.get("estimated_hours", 0),
                        "priority": task.get("priority", "medium")
                    }
                    phase_node["children"].append(task_node)
            
            wbs["children"].append(phase_node)
        
        return wbs
    
    def _create_network_diagram(self, tasks: List[Dict[str, Any]], dependencies: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create network diagram data"""
        
        nodes = []
        edges = []
        
        # Create nodes for tasks
        for task in tasks:
            nodes.append({
                "id": task["id"],
                "label": task.get("title", task.get("name", "")),
                "type": task.get("type", "task"),
                "phase": task.get("phase", ""),
                "duration": task.get("estimated_hours", 0) / 8  # Convert to days
            })
        
        # Create edges for dependencies
        for dep in dependencies:
            edges.append({
                "id": dep["id"],
                "source": dep["from_task"],
                "target": dep["to_task"],
                "type": dep["type"],
                "label": dep.get("type", "").replace("_", " ")
            })
        
        return {
            "nodes": nodes,
            "edges": edges,
            "layout": "hierarchical"
        }
    
    def _create_gantt_chart(self, schedule: Dict[str, Any]) -> Dict[str, Any]:
        """Create Gantt chart visualization data"""
        
        gantt_data = {
            "rows": [],
            "milestones": []
        }
        
        # Add tasks to Gantt
        for task in schedule["tasks"]:
            gantt_data["rows"].append({
                "id": task["task_id"],
                "name": task["task_name"],
                "start": task["start_date"],
                "end": task["end_date"],
                "progress": 0,  # Would be updated with actual progress
                "dependencies": [],  # Would add dependency IDs
                "custom_class": "critical" if task.get("is_critical") else "normal"
            })
        
        # Add milestones
        for milestone in schedule["milestones"]:
            gantt_data["milestones"].append({
                "id": f"milestone_{milestone['name'].replace(' ', '_')}",
                "name": milestone["name"],
                "date": milestone["date"]
            })
        
        return gantt_data
    
    def _identify_progress_issues(self, tracking_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify issues in progress tracking"""
        
        issues = []
        
        # Check for blocked tasks
        blocked_tasks = [t for t in tracking_data.get("tasks", []) if t["status"] == "blocked"]
        if blocked_tasks:
            issues.append({
                "type": "blocked_tasks",
                "severity": "high",
                "count": len(blocked_tasks),
                "description": f"{len(blocked_tasks)} tasks are blocked",
                "action": "Resolve blockers immediately"
            })
        
        # Check for schedule variance
        schedule_variance = tracking_data.get("schedule_variance", 0)
        if schedule_variance < -10:  # More than 10% behind
            issues.append({
                "type": "schedule_delay",
                "severity": "medium",
                "variance": schedule_variance,
                "description": f"Project is {abs(schedule_variance)}% behind schedule",
                "action": "Review timeline and resource allocation"
            })
        
        # Check for at-risk milestones
        at_risk_milestones = [m for m in tracking_data.get("milestones", []) if m.get("at_risk", False)]
        if at_risk_milestones:
            issues.append({
                "type": "milestone_risk",
                "severity": "high",
                "count": len(at_risk_milestones),
                "description": f"{len(at_risk_milestones)} milestones at risk",
                "action": "Implement milestone recovery plan"
            })
        
        return issues
    
    def _create_progress_dashboard(self, progress_report: Dict[str, Any]) -> Dict[str, Any]:
        """Create progress dashboard visualization"""
        
        return {
            "summary_metrics": [
                {
                    "label": "Overall Progress",
                    "value": progress_report["overall_progress"],
                    "type": "percentage",
                    "trend": "up"
                },
                {
                    "label": "Tasks Completed",
                    "value": len(progress_report["task_status"]["completed"]),
                    "type": "count",
                    "total": sum(len(tasks) for tasks in progress_report["task_status"].values())
                },
                {
                    "label": "Schedule Variance",
                    "value": progress_report["metrics"]["schedule_variance"],
                    "type": "percentage",
                    "status": "warning" if progress_report["metrics"]["schedule_variance"] < -5 else "good"
                }
            ],
            "charts": [
                {
                    "type": "progress_bar",
                    "title": "Phase Progress",
                    "data": progress_report["phase_progress"]
                },
                {
                    "type": "pie",
                    "title": "Task Status Distribution",
                    "data": {k: len(v) for k, v in progress_report["task_status"].items()}
                },
                {
                    "type": "timeline",
                    "title": "Milestone Status",
                    "data": progress_report["milestone_status"]
                }
            ]
        }