"""Action Planning Plugin

Provides task breakdown, dependency mapping, and timeline management capabilities.
"""

import json
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from uuid import uuid4

from semantic_kernel.functions import kernel_function
from semantic_kernel.kernel_pydantic import KernelBaseModel


class ActionPlugin(KernelBaseModel):
    """Plugin for action planning and task management"""
    
    @kernel_function(
        description="Create detailed action plan from initiative",
        name="CreateActionPlan"
    )
    async def create_action_plan(
        self,
        initiative: Dict[str, Any],
        approach: str = "waterfall",
        breakdown_depth: int = 2,
        include_buffers: bool = True
    ) -> str:
        """Break down initiative into actionable tasks with timeline"""
        
        # Extract initiative details
        initiative_title = initiative.get("title", "Initiative")
        initiative_scope = initiative.get("description", "")
        timeline = initiative.get("timeline", {})
        
        # This would use AI to generate contextual actions
        # For now, creating structured example
        actions = []
        
        # Phase 1: Planning & Setup
        planning_actions = [
            {
                "title": "Conduct stakeholder analysis",
                "description": "Identify and analyze all stakeholders, their interests, and influence",
                "type": "research",
                "priority": "high",
                "effort_hours": 16,
                "duration_days": 3,
                "dependencies": [],
                "deliverables": ["Stakeholder matrix", "Engagement plan"],
                "success_criteria": "All key stakeholders identified with engagement strategies",
                "skills_required": ["Business analysis", "Communication"]
            },
            {
                "title": "Define detailed requirements",
                "description": "Gather and document comprehensive requirements from stakeholders",
                "type": "research",
                "priority": "critical",
                "effort_hours": 40,
                "duration_days": 5,
                "dependencies": ["stakeholder_analysis"],
                "deliverables": ["Requirements document", "Acceptance criteria"],
                "success_criteria": "Requirements approved by stakeholders",
                "skills_required": ["Business analysis", "Domain expertise"]
            },
            {
                "title": "Create solution design",
                "description": "Design technical and business solution architecture",
                "type": "design",
                "priority": "high",
                "effort_hours": 60,
                "duration_days": 8,
                "dependencies": ["requirements"],
                "deliverables": ["Solution architecture", "Design specifications"],
                "success_criteria": "Design reviewed and approved",
                "skills_required": ["Solution architecture", "Technical design"]
            }
        ]
        
        # Phase 2: Implementation
        implementation_actions = [
            {
                "title": "Set up development environment",
                "description": "Configure development, testing, and staging environments",
                "type": "development",
                "priority": "high",
                "effort_hours": 24,
                "duration_days": 3,
                "dependencies": ["solution_design"],
                "deliverables": ["Configured environments", "Access documentation"],
                "success_criteria": "All environments operational",
                "skills_required": ["DevOps", "Infrastructure"]
            },
            {
                "title": "Develop core functionality",
                "description": "Build the main features and capabilities",
                "type": "development",
                "priority": "critical",
                "effort_hours": 160,
                "duration_days": 20,
                "dependencies": ["dev_environment"],
                "deliverables": ["Core features", "Unit tests", "Documentation"],
                "success_criteria": "Features meet requirements with 90% test coverage",
                "skills_required": ["Software development", "Testing"]
            },
            {
                "title": "Integrate with existing systems",
                "description": "Connect solution with current infrastructure and systems",
                "type": "development",
                "priority": "high",
                "effort_hours": 80,
                "duration_days": 10,
                "dependencies": ["core_development"],
                "deliverables": ["Integration points", "API documentation"],
                "success_criteria": "Successful data flow between systems",
                "skills_required": ["Integration", "API development"]
            }
        ]
        
        # Phase 3: Testing & Deployment
        deployment_actions = [
            {
                "title": "Conduct system testing",
                "description": "Perform comprehensive testing including functional, performance, and security",
                "type": "testing",
                "priority": "critical",
                "effort_hours": 60,
                "duration_days": 8,
                "dependencies": ["integration"],
                "deliverables": ["Test results", "Bug reports", "Performance metrics"],
                "success_criteria": "All critical tests pass, no high-severity bugs",
                "skills_required": ["QA testing", "Test automation"]
            },
            {
                "title": "Prepare deployment package",
                "description": "Create deployment artifacts and documentation",
                "type": "deployment",
                "priority": "high",
                "effort_hours": 20,
                "duration_days": 3,
                "dependencies": ["system_testing"],
                "deliverables": ["Deployment package", "Release notes"],
                "success_criteria": "Deployment package validated",
                "skills_required": ["DevOps", "Release management"]
            },
            {
                "title": "Deploy to production",
                "description": "Execute production deployment with rollback plan",
                "type": "deployment",
                "priority": "critical",
                "effort_hours": 16,
                "duration_days": 2,
                "dependencies": ["deployment_package"],
                "deliverables": ["Live system", "Deployment report"],
                "success_criteria": "System operational in production",
                "skills_required": ["DevOps", "Operations"]
            }
        ]
        
        # Phase 4: Transition & Support
        transition_actions = [
            {
                "title": "Conduct user training",
                "description": "Train end users and administrators on the new system",
                "type": "training",
                "priority": "high",
                "effort_hours": 40,
                "duration_days": 5,
                "dependencies": ["production_deployment"],
                "deliverables": ["Training materials", "Certified users"],
                "success_criteria": "80% of users certified",
                "skills_required": ["Training", "Communication"]
            },
            {
                "title": "Establish support processes",
                "description": "Set up ongoing support and maintenance procedures",
                "type": "deployment",
                "priority": "medium",
                "effort_hours": 20,
                "duration_days": 3,
                "dependencies": ["user_training"],
                "deliverables": ["Support documentation", "SLAs"],
                "success_criteria": "Support team ready",
                "skills_required": ["Support", "Documentation"]
            }
        ]
        
        # Combine all actions
        if approach == "waterfall":
            actions = planning_actions + implementation_actions + deployment_actions + transition_actions
        elif approach == "agile":
            # For agile, mix planning with iterative development
            actions = planning_actions[:2] + implementation_actions[:1] + [planning_actions[2]] + implementation_actions[1:] + deployment_actions + transition_actions
        
        # Add timing and buffers
        current_date = datetime.utcnow()
        for i, action in enumerate(actions):
            if i == 0:
                action["start_date"] = current_date.isoformat()
            else:
                # Calculate based on dependencies
                deps = action.get("dependencies", [])
                if deps:
                    # Start after dependencies complete
                    action["start_date"] = (current_date + timedelta(days=i*5)).isoformat()
                else:
                    action["start_date"] = (current_date + timedelta(days=i*3)).isoformat()
            
            # Add buffer if requested
            duration = action["duration_days"]
            if include_buffers:
                duration = int(duration * 1.2)  # 20% buffer
            
            action["end_date"] = (datetime.fromisoformat(action["start_date"]) + timedelta(days=duration)).isoformat()
        
        # Calculate total duration
        total_duration = (datetime.fromisoformat(actions[-1]["end_date"]) - current_date).days if actions else 0
        
        # Resource summary
        resource_summary = {
            "total_effort_hours": sum(a["effort_hours"] for a in actions),
            "skills_needed": list(set(skill for a in actions for skill in a.get("skills_required", []))),
            "peak_resources": 5  # Would calculate based on overlap
        }
        
        # Risk assessment
        risks = [
            {
                "phase": "Implementation",
                "risk": "Technical complexity higher than estimated",
                "probability": "medium",
                "impact": "high",
                "mitigation": "Allocate senior developers, plan for technical spikes"
            },
            {
                "phase": "Deployment",
                "risk": "Production environment differences",
                "probability": "low",
                "impact": "high",
                "mitigation": "Thorough environment validation, staged rollout"
            }
        ]
        
        result = {
            "actions": actions,
            "total_duration": total_duration,
            "resource_summary": resource_summary,
            "risks": risks,
            "approach": approach
        }
        
        return json.dumps(result)
    
    @kernel_function(
        description="Update existing action plan with changes",
        name="UpdateActionPlan"
    )
    async def update_action_plan(
        self,
        current_actions: List[Dict[str, Any]],
        updates: Dict[str, Any],
        reoptimize: bool = True
    ) -> str:
        """Update action plan based on changes"""
        
        # Track changes
        added = []
        modified = []
        removed = []
        
        # Process updates
        if "add_actions" in updates:
            for new_action in updates["add_actions"]:
                action = {
                    "id": str(uuid4()),
                    "title": new_action["title"],
                    "description": new_action.get("description", ""),
                    "type": new_action.get("type", "development"),
                    "priority": new_action.get("priority", "medium"),
                    "effort_hours": new_action.get("effort_hours", 20),
                    "duration_days": new_action.get("duration_days", 3),
                    "dependencies": new_action.get("dependencies", []),
                    "status": "not_started"
                }
                added.append(action)
        
        if "modify_actions" in updates:
            for mod in updates["modify_actions"]:
                action_id = mod["id"]
                changes = mod["changes"]
                modified.append({
                    "id": action_id,
                    "changes": changes
                })
        
        if "remove_actions" in updates:
            for action_id in updates["remove_actions"]:
                removed.append({"id": action_id})
        
        # Calculate timeline changes
        timeline_changes = {}
        if reoptimize:
            # Would recalculate optimal timeline
            timeline_changes = {
                "original_end": "2025-08-01",
                "new_end": "2025-08-15",
                "delta_days": 14,
                "reason": "Added actions extend timeline"
            }
        
        # Analyze impact
        impact = "Timeline extended by 2 weeks due to additional requirements" if added else "Minor adjustments to existing plan"
        
        result = {
            "added": added,
            "modified": modified,
            "removed": removed,
            "timeline_changes": timeline_changes,
            "impact": impact,
            "reoptimization_applied": reoptimize
        }
        
        return json.dumps(result)
    
    @kernel_function(
        description="Optimize action plan timeline",
        name="OptimizeTimeline"
    )
    async def optimize_timeline(
        self,
        actions: List[Dict[str, Any]],
        optimization_goal: str = "duration",
        constraints: Dict[str, Any] = None,
        allow_parallel: bool = True
    ) -> str:
        """Optimize timeline for efficiency"""
        
        constraints = constraints or {}
        
        # This would use scheduling algorithms
        # For now, creating example optimization
        optimized_actions = actions.copy()
        
        # Strategies applied
        strategies_applied = []
        
        # Strategy 1: Parallelize independent tasks
        if allow_parallel:
            # Find tasks that can run in parallel
            parallel_groups = []
            for i, action in enumerate(optimized_actions):
                if not action.get("dependencies"):
                    # Can start immediately
                    if i > 0:
                        optimized_actions[i]["parallel_with"] = optimized_actions[0]["id"]
                        strategies_applied.append("Parallelized independent tasks")
        
        # Strategy 2: Fast-track critical path
        critical_actions = [a for a in optimized_actions if a.get("priority") == "critical"]
        if critical_actions:
            strategies_applied.append("Fast-tracked critical path activities")
        
        # Strategy 3: Resource leveling
        if optimization_goal == "resource":
            strategies_applied.append("Applied resource leveling")
        
        # Calculate optimized metrics
        original_duration = sum(a.get("duration_days", 0) for a in actions)
        optimized_duration = int(original_duration * 0.8)  # 20% improvement
        time_saved = original_duration - optimized_duration
        
        # Resource utilization
        resource_utilization = {
            "before": {"average": 0.65, "peak": 0.95},
            "after": {"average": 0.80, "peak": 0.85}
        }
        
        # Cost impact
        cost_impact = -5000 if optimization_goal == "cost" else 2000  # Negative means savings
        
        # Recommendations
        recommendations = [
            "Consider adding 10% buffer to critical path",
            "Ensure resource availability for parallel activities",
            "Plan for integration checkpoints"
        ]
        
        # Trade-offs
        trade_offs = [
            {"benefit": "Reduced timeline", "risk": "Increased coordination complexity"},
            {"benefit": "Better resource utilization", "risk": "Less flexibility for changes"}
        ]
        
        result = {
            "optimized_actions": optimized_actions,
            "original_duration": original_duration,
            "new_duration": optimized_duration,
            "time_saved": time_saved,
            "strategies_applied": strategies_applied,
            "resource_utilization": resource_utilization,
            "cost_impact": cost_impact,
            "recommendations": recommendations,
            "trade_offs": trade_offs
        }
        
        return json.dumps(result)
    
    @kernel_function(
        description="Track progress of action plan execution",
        name="TrackProgress"
    )
    async def track_progress(
        self,
        actions: List[Dict[str, Any]],
        progress_data: List[Dict[str, Any]],
        as_of_date: str,
        include_forecasts: bool = True
    ) -> str:
        """Track and analyze action plan progress"""
        
        # Calculate progress metrics
        total_actions = len(actions)
        completed_count = 0
        in_progress_count = 0
        not_started_count = 0
        delayed_count = 0
        
        # Analyze each action
        for action in actions:
            status = action.get("status", "not_started")
            if status == "completed":
                completed_count += 1
            elif status == "in_progress":
                in_progress_count += 1
            elif status == "not_started":
                not_started_count += 1
            
            # Check for delays
            if action.get("end_date") and datetime.fromisoformat(action["end_date"]) < datetime.fromisoformat(as_of_date):
                if status != "completed":
                    delayed_count += 1
        
        # Calculate percentages
        overall_completion = (completed_count / total_actions * 100) if total_actions > 0 else 0
        on_track_percentage = ((completed_count + in_progress_count) / total_actions * 100) if total_actions > 0 else 0
        
        # Identify blocked actions
        blocked_actions = []
        for action in actions:
            if action.get("status") == "blocked":
                blocked_actions.append({
                    "id": action["id"],
                    "title": action["title"],
                    "blocker": action.get("blocker_description", "Unknown")
                })
        
        # Forecasting
        projected_completion_date = None
        forecast_confidence = 0.8
        delay_risk = "low"
        
        if include_forecasts:
            # Simple linear projection
            if completed_count > 0:
                days_elapsed = 30  # Would calculate from actual data
                completion_rate = completed_count / days_elapsed
                remaining_actions = total_actions - completed_count
                days_to_complete = remaining_actions / completion_rate if completion_rate > 0 else 999
                projected_completion_date = (datetime.fromisoformat(as_of_date) + timedelta(days=int(days_to_complete))).isoformat()
                
                if delayed_count > 2:
                    delay_risk = "high"
                    forecast_confidence = 0.6
                elif delayed_count > 0:
                    delay_risk = "medium"
                    forecast_confidence = 0.7
        
        # Critical path status
        critical_path_status = "at_risk" if delayed_count > 0 else "on_track"
        
        # Milestone status
        milestone_status = [
            {"name": "Phase 1", "status": "completed"},
            {"name": "Phase 2", "status": "in_progress"},
            {"name": "Phase 3", "status": "not_started"}
        ]
        
        # Recommendations
        recommendations = []
        if delayed_count > 0:
            recommendations.append("Address delayed actions immediately")
        if blocked_actions:
            recommendations.append("Resolve blockers to maintain progress")
        if overall_completion < 50 and total_actions > 10:
            recommendations.append("Consider additional resources to accelerate")
        
        # Progress trends (for visualization)
        planned_progress = [20, 40, 60, 80, 100]
        actual_progress = [15, 30, 45, overall_completion, overall_completion]
        
        result = {
            "overall_completion": round(overall_completion, 1),
            "on_track_percentage": round(on_track_percentage, 1),
            "completed_count": completed_count,
            "in_progress_count": in_progress_count,
            "not_started_count": not_started_count,
            "delayed_count": delayed_count,
            "blocked_actions": blocked_actions,
            "projected_completion_date": projected_completion_date,
            "forecast_confidence": forecast_confidence,
            "delay_risk": delay_risk,
            "critical_path_status": critical_path_status,
            "milestone_status": milestone_status,
            "recommendations": recommendations,
            "planned_progress": planned_progress,
            "actual_progress": actual_progress
        }
        
        return json.dumps(result)
    
    @kernel_function(
        description="Identify risks in action plan",
        name="IdentifyRisks"
    )
    async def identify_risks(
        self,
        actions: List[Dict[str, Any]],
        risk_categories: List[str] = None,
        include_mitigation: bool = True
    ) -> str:
        """Identify and assess risks in action plan"""
        
        risk_categories = risk_categories or ["schedule", "resource", "technical", "dependency"]
        risks = []
        
        # Schedule risks
        if "schedule" in risk_categories:
            # Check for tight timelines
            critical_actions = [a for a in actions if a.get("priority") == "critical"]
            if len(critical_actions) > 3:
                risks.append({
                    "id": str(uuid4()),
                    "category": "schedule",
                    "description": "Multiple critical path activities may cause delays",
                    "probability": "medium",
                    "impact": "high",
                    "severity": "high",
                    "affected_actions": [a["id"] for a in critical_actions[:3]],
                    "mitigation": "Add schedule buffers and consider parallel execution" if include_mitigation else None
                })
            
            # Check for sequential dependencies
            long_chains = []
            for action in actions:
                if len(action.get("dependencies", [])) > 2:
                    long_chains.append(action)
            
            if long_chains:
                risks.append({
                    "id": str(uuid4()),
                    "category": "schedule",
                    "description": "Long dependency chains create schedule risk",
                    "probability": "high",
                    "impact": "medium",
                    "severity": "medium",
                    "affected_actions": [a["id"] for a in long_chains[:2]],
                    "mitigation": "Review dependencies and identify opportunities to parallelize" if include_mitigation else None
                })
        
        # Resource risks
        if "resource" in risk_categories:
            # Check for resource conflicts
            high_effort_actions = [a for a in actions if a.get("effort_hours", 0) > 100]
            if len(high_effort_actions) > 2:
                risks.append({
                    "id": str(uuid4()),
                    "category": "resource",
                    "description": "High resource demand may cause conflicts",
                    "probability": "medium",
                    "impact": "medium",
                    "severity": "medium",
                    "affected_actions": [a["id"] for a in high_effort_actions[:2]],
                    "mitigation": "Plan resource allocation carefully and consider hiring" if include_mitigation else None
                })
            
            # Check for skill gaps
            unique_skills = set()
            for action in actions:
                unique_skills.update(action.get("skills_required", []))
            
            if len(unique_skills) > 10:
                risks.append({
                    "id": str(uuid4()),
                    "category": "resource",
                    "description": "Wide variety of skills needed may be hard to source",
                    "probability": "medium",
                    "impact": "medium",
                    "severity": "medium",
                    "affected_actions": [],
                    "mitigation": "Start recruitment early or plan for training" if include_mitigation else None
                })
        
        # Technical risks
        if "technical" in risk_categories:
            # Check for integration complexity
            integration_actions = [a for a in actions if "integration" in a.get("title", "").lower()]
            if integration_actions:
                risks.append({
                    "id": str(uuid4()),
                    "category": "technical",
                    "description": "System integration complexity may cause issues",
                    "probability": "medium",
                    "impact": "high",
                    "severity": "high",
                    "affected_actions": [a["id"] for a in integration_actions],
                    "mitigation": "Plan integration testing early and often" if include_mitigation else None
                })
        
        # Dependency risks
        if "dependency" in risk_categories:
            # Check for external dependencies
            external_deps = [a for a in actions if "external" in str(a.get("dependencies", [])).lower()]
            if external_deps:
                risks.append({
                    "id": str(uuid4()),
                    "category": "dependency",
                    "description": "External dependencies may cause delays",
                    "probability": "low",
                    "impact": "high",
                    "severity": "medium",
                    "affected_actions": [a["id"] for a in external_deps],
                    "mitigation": "Establish SLAs and have contingency plans" if include_mitigation else None
                })
        
        # Calculate overall risk score
        risk_scores = {"high": 3, "medium": 2, "low": 1}
        total_score = sum(risk_scores.get(r["severity"], 0) for r in risks)
        max_score = len(risks) * 3
        overall_risk_score = (total_score / max_score * 10) if max_score > 0 else 0
        
        # Identify high-risk actions
        high_risk_actions = list(set(
            action_id 
            for risk in risks 
            if risk["severity"] == "high"
            for action_id in risk.get("affected_actions", [])
        ))
        
        # Contingency recommendations
        contingencies = []
        if overall_risk_score > 7:
            contingencies.append("Develop comprehensive risk response plan")
            contingencies.append("Increase management reserve by 20%")
        elif overall_risk_score > 5:
            contingencies.append("Regular risk review meetings")
            contingencies.append("Maintain 10% schedule buffer")
        
        # Monitoring plan
        monitoring_plan = {
            "frequency": "weekly" if overall_risk_score > 5 else "bi-weekly",
            "metrics": ["Schedule variance", "Resource utilization", "Risk triggers"],
            "escalation": "Project steering committee"
        }
        
        result = {
            "risks": risks,
            "overall_risk_score": round(overall_risk_score, 1),
            "high_risk_actions": high_risk_actions,
            "contingencies": contingencies,
            "monitoring_plan": monitoring_plan
        }
        
        return json.dumps(result)
    
    @kernel_function(
        description="Calculate critical path through actions",
        name="CalculateCriticalPath"
    )
    async def calculate_critical_path(
        self,
        actions: List[Dict[str, Any]],
        include_slack: bool = True
    ) -> str:
        """Calculate critical path using CPM algorithm"""
        
        # This would implement full CPM algorithm
        # For now, simplified version
        
        # Build dependency graph
        action_map = {a["id"]: a for a in actions}
        
        # Find actions with no dependencies (start nodes)
        start_actions = [a for a in actions if not a.get("dependencies", [])]
        
        # Find actions that no other actions depend on (end nodes)
        all_deps = set()
        for action in actions:
            all_deps.update(action.get("dependencies", []))
        
        end_actions = [a for a in actions if a["id"] not in all_deps]
        
        # Simple path finding (would use proper algorithm)
        critical_path = []
        
        # Start with longest duration path
        if start_actions and end_actions:
            # Find path with maximum duration
            current = start_actions[0]
            critical_path.append(current["id"])
            
            # Follow dependencies
            while current["id"] not in [e["id"] for e in end_actions]:
                # Find next action
                next_actions = [
                    a for a in actions 
                    if current["id"] in a.get("dependencies", [])
                ]
                if next_actions:
                    # Choose action with longest duration
                    current = max(next_actions, key=lambda x: x.get("duration_days", 0))
                    critical_path.append(current["id"])
                else:
                    break
        
        # Calculate slack for non-critical actions
        slack_times = {}
        if include_slack:
            for action in actions:
                if action["id"] not in critical_path:
                    # Simplified slack calculation
                    slack_times[action["id"]] = 5  # Days of slack
        
        # Critical path metrics
        critical_duration = sum(
            action_map[aid].get("duration_days", 0) 
            for aid in critical_path 
            if aid in action_map
        )
        
        total_duration = sum(a.get("duration_days", 0) for a in actions)
        
        result = {
            "critical_path": critical_path,
            "critical_duration": critical_duration,
            "total_duration": total_duration,
            "path_percentage": round(critical_duration / total_duration * 100, 1) if total_duration > 0 else 0,
            "slack_times": slack_times,
            "critical_actions_count": len(critical_path),
            "total_actions_count": len(actions)
        }
        
        return json.dumps(result)
    
    @kernel_function(
        description="Generate Gantt chart data for timeline visualization",
        name="GenerateGantt"
    )
    async def generate_gantt(
        self,
        actions: List[Dict[str, Any]],
        view_type: str = "standard",
        group_by: str = "phase"
    ) -> str:
        """Generate Gantt chart visualization data"""
        
        # Group actions
        groups = {}
        if group_by == "phase":
            # Group by project phase
            phase_size = max(1, len(actions) // 4)
            for i, action in enumerate(actions):
                phase = f"Phase {i // phase_size + 1}"
                if phase not in groups:
                    groups[phase] = []
                groups[phase].append(action)
        elif group_by == "type":
            # Group by action type
            for action in actions:
                action_type = action.get("type", "other")
                if action_type not in groups:
                    groups[action_type] = []
                groups[action_type].append(action)
        
        # Create Gantt data
        gantt_data = {
            "tasks": [],
            "dependencies": [],
            "milestones": [],
            "resources": []
        }
        
        # Add tasks
        for action in actions:
            task = {
                "id": action["id"],
                "name": action["title"],
                "start": action.get("start_date", ""),
                "end": action.get("end_date", ""),
                "progress": action.get("progress", 0),
                "group": self._get_action_group(action, group_by),
                "color": self._get_action_color(action),
                "resource": action.get("assigned_to", "Unassigned")
            }
            gantt_data["tasks"].append(task)
            
            # Add dependencies
            for dep in action.get("dependencies", []):
                gantt_data["dependencies"].append({
                    "source": dep,
                    "target": action["id"],
                    "type": "finish-to-start",
                    "lag": 0
                })
        
        # Add milestones
        milestone_actions = [a for a in actions if a.get("priority") == "critical"]
        for action in milestone_actions[:5]:  # Top 5 critical actions as milestones
            gantt_data["milestones"].append({
                "id": f"milestone_{action['id']}",
                "name": f"{action['title']} Complete",
                "date": action.get("end_date", ""),
                "description": "Critical milestone"
            })
        
        # Resource allocation
        resource_map = {}
        for action in actions:
            resource = action.get("assigned_to", "Unassigned")
            if resource not in resource_map:
                resource_map[resource] = []
            resource_map[resource].append({
                "task_id": action["id"],
                "hours": action.get("effort_hours", 0)
            })
        
        gantt_data["resources"] = [
            {"name": name, "tasks": tasks}
            for name, tasks in resource_map.items()
        ]
        
        # View configuration
        view_config = {
            "zoom_level": "days" if view_type == "detailed" else "weeks",
            "show_dependencies": True,
            "show_progress": True,
            "show_resources": view_type == "resource",
            "critical_path_highlight": True
        }
        
        result = {
            "gantt_data": gantt_data,
            "groups": list(groups.keys()),
            "view_config": view_config,
            "summary": {
                "total_tasks": len(actions),
                "total_dependencies": len(gantt_data["dependencies"]),
                "total_milestones": len(gantt_data["milestones"]),
                "resources_count": len(resource_map)
            }
        }
        
        return json.dumps(result)
    
    def _get_action_group(self, action: Dict[str, Any], group_by: str) -> str:
        """Get group for action based on grouping criteria"""
        
        if group_by == "phase":
            # Simple phase assignment based on action type
            if action.get("type") in ["research", "design"]:
                return "Phase 1: Planning"
            elif action.get("type") in ["development"]:
                return "Phase 2: Implementation"
            elif action.get("type") in ["testing", "deployment"]:
                return "Phase 3: Delivery"
            else:
                return "Phase 4: Support"
        elif group_by == "type":
            return action.get("type", "other").title()
        else:
            return "Default"
    
    def _get_action_color(self, action: Dict[str, Any]) -> str:
        """Get color for action based on type or priority"""
        
        priority_colors = {
            "critical": "#d32f2f",  # Red
            "high": "#f57c00",      # Orange
            "medium": "#388e3c",    # Green
            "low": "#1976d2"        # Blue
        }
        
        type_colors = {
            "research": "#9c27b0",   # Purple
            "design": "#2196f3",     # Blue
            "development": "#4caf50", # Green
            "testing": "#ff9800",    # Orange
            "deployment": "#f44336", # Red
            "training": "#00bcd4"    # Cyan
        }
        
        # Priority takes precedence
        if action.get("priority") in priority_colors:
            return priority_colors[action["priority"]]
        elif action.get("type") in type_colors:
            return type_colors[action["type"]]
        else:
            return "#9e9e9e"  # Grey default