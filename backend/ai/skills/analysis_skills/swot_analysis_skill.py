import json
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional

from semantic_kernel.skill_definition import sk_function, sk_function_context_parameter

class SWOTAnalysisSkill:
    """
    Semantic Kernel skill for providing structure and guidance for SWOT/TOWS analyses.
    
    This skill works in conjunction with the AnalysisService, which is responsible
    for maintaining the state of active analysis sessions and persisting data.
    This skill focuses on providing guidance, structure, and recommendations
    for the analysis process.
    """
    
    def __init__(self):
        # The skill doesn't maintain state - that's handled by AnalysisService
        pass
    
    @sk_function(
        description="Provides structure and guidance for a new SWOT analysis session",
        name="create_swot_session"
    )
    @sk_function_context_parameter(
        name="user_id",
        description="The user ID creating the session"
    )
    @sk_function_context_parameter(
        name="company_name",
        description="The company name for the analysis"
    )
    @sk_function_context_parameter(
        name="topic",
        description="The topic of the SWOT analysis"
    )
    @sk_function_context_parameter(
        name="description",
        description="Optional description of the analysis"
    )
    def create_swot_session(self, context) -> str:
        """
        Provides structure and initial guidance for a new SWOT analysis session.
        The actual session state is managed by the AnalysisService.
        """
        try:
            user_id = context["user_id"]
            company_name = context["company_name"]
            topic = context["topic"]
            description = context.get("description", "")
            
            # Create guidance structure for the analysis
            guidance = {
                "current_step": "getting_started",
                "next_steps": [
                    "Add strengths",
                    "Add weaknesses",
                    "Add opportunities",
                    "Add threats"
                ],
                "progression": {
                    "swot_phase": 0,  # 0-100%
                    "tows_phase": 0,  # 0-100%
                    "overall": 0      # 0-100%
                },
                "tips": [
                    f"Start by identifying 3-5 key strengths for {company_name} related to {topic}",
                    "Consider internal capabilities, resources, and competitive advantages",
                    "Be specific and focus on factors that are relevant to the topic"
                ],
                "estimated_time": "15-20 minutes to complete SWOT analysis"
            }
            
            # Return structured guidance
            response = {
                "guidance": guidance,
                "schema": {
                    "strengths": [],
                    "weaknesses": [],
                    "opportunities": [],
                    "threats": [],
                    "tows_strategies": [],
                    "insights": []
                }
            }
            
            return json.dumps(response)
        except Exception as e:
            return json.dumps({"error": str(e)})
    
    @sk_function(
        description="Provides guidance for adding a point to a SWOT quadrant",
        name="add_swot_point"
    )
    @sk_function_context_parameter(
        name="session_id",
        description="The session ID"
    )
    @sk_function_context_parameter(
        name="category",
        description="The SWOT category (strength, weakness, opportunity, threat)"
    )
    @sk_function_context_parameter(
        name="text",
        description="The text of the SWOT point"
    )
    @sk_function_context_parameter(
        name="item_id",
        description="Unique ID for the item"
    )
    def add_swot_point(self, context) -> str:
        """
        Provides guidance and progress tracking for adding a point to a SWOT quadrant.
        The actual point storage is handled by the AnalysisService.
        """
        try:
            session_id = context["session_id"]
            category = context["category"].lower()
            text = context["text"]
            item_id = context.get("item_id", str(uuid.uuid4()))
            
            # Validate category
            valid_categories = ["strength", "weakness", "opportunity", "threat"]
            if category not in valid_categories:
                return json.dumps({"error": f"Invalid category. Must be one of: {', '.join(valid_categories)}"})
            
            # Generate appropriate guidance based on the category
            guidance = self._generate_guidance_for_category(category)
            
            # Determine next steps based on progress in each quadrant
            # This would typically use data from the session, but we're providing
            # generic guidance here as the AnalysisService manages the state
            next_steps = self._determine_next_steps(category)
            
            # Update progression estimate (the AnalysisService would use real counts)
            progression = {
                "swot_phase": 25,  # Placeholder - AnalysisService calculates this
                "tows_phase": 0,
                "overall": 12      # Placeholder - AnalysisService calculates this
            }
            
            # Create response
            response = {
                "item": {
                    "id": item_id,
                    "category": category,
                    "text": text
                },
                "guidance": {
                    "current_step": f"adding_{category}",
                    "next_steps": next_steps,
                    "progression": progression,
                    "tips": guidance["tips"],
                    "suggested_action": guidance["suggested_action"]
                }
            }
            
            return json.dumps(response)
        except Exception as e:
            return json.dumps({"error": str(e)})
    
    @sk_function(
        description="Provides guidance for adding an action to a TOWS cell",
        name="add_tows_action"
    )
    @sk_function_context_parameter(
        name="session_id",
        description="The session ID"
    )
    @sk_function_context_parameter(
        name="strategy_type",
        description="The TOWS strategy type (SO, WO, ST, WT)"
    )
    @sk_function_context_parameter(
        name="text",
        description="The text of the TOWS strategy"
    )
    @sk_function_context_parameter(
        name="strategy_id",
        description="Unique ID for the strategy"
    )
    def add_tows_action(self, context) -> str:
        """
        Provides guidance and progress tracking for adding a strategy to a TOWS cell.
        The actual strategy storage is handled by the AnalysisService.
        """
        try:
            session_id = context["session_id"]
            strategy_type = context["strategy_type"].upper()
            text = context["text"]
            strategy_id = context.get("strategy_id", str(uuid.uuid4()))
            
            # Validate strategy type
            valid_types = ["SO", "WO", "ST", "WT"]
            if strategy_type not in valid_types:
                return json.dumps({"error": f"Invalid strategy type. Must be one of: {', '.join(valid_types)}"})
            
            # Generate appropriate guidance based on the strategy type
            guidance = self._generate_guidance_for_tows_cell(strategy_type)
            
            # Determine next steps for TOWS phase
            next_steps = self._determine_next_steps_tows(strategy_type)
            
            # Update progression estimate (the AnalysisService would use real counts)
            progression = {
                "swot_phase": 100,  # Assuming SWOT is complete if user is on TOWS
                "tows_phase": 25,   # Placeholder - AnalysisService calculates this
                "overall": 60       # Placeholder - AnalysisService calculates this
            }
            
            # Create response
            response = {
                "strategy": {
                    "id": strategy_id,
                    "strategy_type": strategy_type,
                    "text": text
                },
                "guidance": {
                    "current_step": f"adding_tows_{strategy_type}",
                    "next_steps": next_steps,
                    "progression": progression,
                    "tips": guidance["tips"],
                    "suggested_action": guidance["suggested_action"]
                }
            }
            
            return json.dumps(response)
        except Exception as e:
            return json.dumps({"error": str(e)})
    
    @sk_function(
        description="Provides guidance based on the current SWOT data",
        name="get_swot_data"
    )
    @sk_function_context_parameter(
        name="session_id",
        description="The session ID"
    )
    @sk_function_context_parameter(
        name="strengths_count",
        description="Number of strengths added so far"
    )
    @sk_function_context_parameter(
        name="weaknesses_count",
        description="Number of weaknesses added so far"
    )
    @sk_function_context_parameter(
        name="opportunities_count",
        description="Number of opportunities added so far"
    )
    @sk_function_context_parameter(
        name="threats_count",
        description="Number of threats added so far"
    )
    def get_swot_data(self, context) -> str:
        """
        Provides guidance based on the current state of the SWOT analysis.
        The actual data retrieval is handled by the AnalysisService.
        """
        try:
            session_id = context["session_id"]
            
            # Get counts from context if provided
            strengths_count = int(context.get("strengths_count", 0))
            weaknesses_count = int(context.get("weaknesses_count", 0))
            opportunities_count = int(context.get("opportunities_count", 0))
            threats_count = int(context.get("threats_count", 0))
            
            # Calculate completion percentages
            target_count = 3  # Target number of items per quadrant
            completion = {
                "strengths": min(100, (strengths_count / target_count) * 100),
                "weaknesses": min(100, (weaknesses_count / target_count) * 100),
                "opportunities": min(100, (opportunities_count / target_count) * 100),
                "threats": min(100, (threats_count / target_count) * 100)
            }
            
            # Calculate overall SWOT completion
            swot_completion = sum(completion.values()) / 4
            
            # Determine which quadrant needs attention
            focus_area = self._determine_focus_area(
                strengths_count, weaknesses_count, 
                opportunities_count, threats_count
            )
            
            # Generate guidance based on completion status
            guidance = {
                "current_step": "reviewing_swot" if swot_completion >= 75 else f"adding_{focus_area}",
                "progression": {
                    "swot_phase": swot_completion,
                    "tows_phase": 0,
                    "overall": swot_completion / 2  # SWOT is half of the overall process
                },
                "completion": completion,
                "suggested_actions": [
                    f"Add more items to the {focus_area} quadrant" if swot_completion < 75 else "Review your SWOT analysis",
                    "Ensure each quadrant has at least 3 items",
                    "Move to TOWS matrix when SWOT is complete" if swot_completion >= 75 else "Continue building your SWOT analysis"
                ],
                "tips": self._generate_tips_for_swot_completion(swot_completion, focus_area)
            }
            
            return json.dumps(guidance)
        except Exception as e:
            return json.dumps({"error": str(e)})
    
    @sk_function(
        description="Provides guidance based on the current TOWS data",
        name="get_tows_data"
    )
    @sk_function_context_parameter(
        name="session_id",
        description="The session ID"
    )
    @sk_function_context_parameter(
        name="so_count",
        description="Number of SO strategies added so far"
    )
    @sk_function_context_parameter(
        name="wo_count",
        description="Number of WO strategies added so far"
    )
    @sk_function_context_parameter(
        name="st_count",
        description="Number of ST strategies added so far"
    )
    @sk_function_context_parameter(
        name="wt_count",
        description="Number of WT strategies added so far"
    )
    def get_tows_data(self, context) -> str:
        """
        Provides guidance based on the current state of the TOWS matrix.
        The actual data retrieval is handled by the AnalysisService.
        """
        try:
            session_id = context["session_id"]
            
            # Get counts from context if provided
            so_count = int(context.get("so_count", 0))
            wo_count = int(context.get("wo_count", 0))
            st_count = int(context.get("st_count", 0))
            wt_count = int(context.get("wt_count", 0))
            
            # Calculate completion percentages
            target_count = 2  # Target number of strategies per cell
            completion = {
                "SO": min(100, (so_count / target_count) * 100),
                "WO": min(100, (wo_count / target_count) * 100),
                "ST": min(100, (st_count / target_count) * 100),
                "WT": min(100, (wt_count / target_count) * 100)
            }
            
            # Calculate overall TOWS completion
            tows_completion = sum(completion.values()) / 4
            
            # Overall completion (assuming SWOT is complete if working on TOWS)
            overall_completion = 50 + (tows_completion / 2)  # SWOT=50%, TOWS=50%
            
            # Determine which cell needs attention
            focus_cell = self._determine_tows_focus_area(so_count, wo_count, st_count, wt_count)
            
            # Generate guidance based on completion status
            guidance = {
                "current_step": "reviewing_tows" if tows_completion >= 75 else f"adding_tows_{focus_cell}",
                "progression": {
                    "swot_phase": 100,  # Assuming SWOT is complete
                    "tows_phase": tows_completion,
                    "overall": overall_completion
                },
                "completion": completion,
                "suggested_actions": [
                    f"Add more strategies to the {focus_cell} cell" if tows_completion < 75 else "Review your TOWS matrix",
                    "Ensure each cell has at least 2 strategies",
                    "Generate insights when TOWS is complete" if tows_completion >= 75 else "Continue building your TOWS matrix"
                ],
                "tips": self._generate_tips_for_tows_completion(tows_completion, focus_cell)
            }
            
            return json.dumps(guidance)
        except Exception as e:
            return json.dumps({"error": str(e)})
    
    @sk_function(
        description="Provides guidance for finalizing an analysis",
        name="save_analysis"
    )
    @sk_function_context_parameter(
        name="session_id",
        description="The session ID"
    )
    def save_analysis(self, context) -> str:
        """
        Provides guidance for finalizing a SWOT/TOWS analysis.
        The actual saving is handled by the AnalysisService.
        """
        try:
            session_id = context["session_id"]
            
            # Generate guidance for final steps after saving
            next_steps = [
                "Review the full analysis",
                "Generate strategic insights",
                "Create an action plan based on TOWS strategies",
                "Share the analysis with stakeholders"
            ]
            
            response = {
                "success": True,
                "guidance": {
                    "next_steps": next_steps,
                    "tips": [
                        "Set a timeline for implementing the strategies identified in the TOWS matrix",
                        "Prioritize strategies based on impact and feasibility",
                        "Plan to review and update the analysis quarterly or when market conditions change",
                        "Use the insights to inform your strategic planning process"
                    ]
                }
            }
            
            return json.dumps(response)
        except Exception as e:
            return json.dumps({"error": str(e)})
    
    # ----- Helper methods for generating guidance -----
    
    def _generate_guidance_for_category(self, category: str) -> Dict[str, Any]:
        """Generate guidance specific to a SWOT category"""
        guidance = {
            "strength": {
                "tips": [
                    "Focus on unique capabilities that give your company an advantage",
                    "Consider your resources, expertise, and intellectual property",
                    "Think about what your customers see as your strengths",
                    "Be specific rather than general in your descriptions"
                ],
                "suggested_action": "Add at least 3-5 strengths before moving to weaknesses"
            },
            "weakness": {
                "tips": [
                    "Be honest about internal limitations or disadvantages",
                    "Consider areas where competitors outperform you",
                    "Look at resource constraints or capability gaps",
                    "Think about what could be improved in your operations"
                ],
                "suggested_action": "Add at least 3-5 weaknesses before moving to opportunities"
            },
            "opportunity": {
                "tips": [
                    "Look for external factors that could benefit your company",
                    "Consider market trends, technological advances, or regulatory changes",
                    "Think about unmet customer needs or emerging market segments",
                    "Consider how changes in the business environment create openings"
                ],
                "suggested_action": "Add at least 3-5 opportunities before moving to threats"
            },
            "threat": {
                "tips": [
                    "Identify external factors that could harm your position",
                    "Consider competitive threats, technological disruption, or market shifts",
                    "Think about regulatory changes or economic conditions",
                    "Look for potential obstacles to your success"
                ],
                "suggested_action": "Add at least 3-5 threats before moving to the TOWS matrix"
            }
        }
        
        return guidance.get(category, {"tips": [], "suggested_action": "Continue with your analysis"})
    
    def _generate_guidance_for_tows_cell(self, cell_type: str) -> Dict[str, Any]:
        """Generate guidance specific to a TOWS cell"""
        guidance = {
            "SO": {
                "tips": [
                    "Look for ways to use your strengths to capitalize on opportunities",
                    "Match specific strengths with specific opportunities",
                    "Create strategies that leverage internal capabilities to exploit external openings",
                    "Focus on actions that maximize your competitive advantage"
                ],
                "suggested_action": "Add at least 2-3 SO strategies before moving to the next cell"
            },
            "WO": {
                "tips": [
                    "Identify opportunities that could help overcome weaknesses",
                    "Look for external factors that might provide resources or capabilities you lack",
                    "Consider how market trends could help transform weaknesses into strengths",
                    "Focus on growth strategies that minimize internal limitations"
                ],
                "suggested_action": "Add at least 2-3 WO strategies before moving to the next cell"
            },
            "ST": {
                "tips": [
                    "Use your strengths to mitigate or avoid threats",
                    "Match specific strengths against specific threats",
                    "Look for ways your capabilities can neutralize external challenges",
                    "Focus on defensive strategies that leverage your advantages"
                ],
                "suggested_action": "Add at least 2-3 ST strategies before moving to the next cell"
            },
            "WT": {
                "tips": [
                    "Develop defensive strategies to minimize weaknesses and avoid threats",
                    "Consider partnerships or restructuring to address vulnerabilities",
                    "Look for ways to transform weaknesses or mitigate threats",
                    "Focus on risk management and contingency planning"
                ],
                "suggested_action": "Add at least 2-3 WT strategies to complete your TOWS matrix"
            }
        }
        
        return guidance.get(cell_type, {"tips": [], "suggested_action": "Continue with your analysis"})
    
    def _determine_next_steps(self, current_category: str) -> List[str]:
        """Determine appropriate next steps based on the current SWOT category"""
        category_sequence = ["strength", "weakness", "opportunity", "threat"]
        
        try:
            current_index = category_sequence.index(current_category)
            next_steps = []
            
            # Add options for proceeding to next quadrant if not on the last one
            if current_index < len(category_sequence) - 1:
                next_category = category_sequence[current_index + 1]
                next_steps.append(f"Move to {next_category}s")
            
            # Always allow adding more to current quadrant
            next_steps.append(f"Add more {current_category}s")
            
            # If on the last quadrant, suggest moving to TOWS
            if current_index == len(category_sequence) - 1:
                next_steps.append("Move to TOWS matrix")
            
            # Add review option
            next_steps.append("Review SWOT analysis")
            
            return next_steps
            
        except ValueError:
            # Fallback if category not found in sequence
            return [
                "Add strengths",
                "Add weaknesses",
                "Add opportunities",
                "Add threats",
                "Review SWOT analysis"
            ]
    
    def _determine_next_steps_tows(self, current_cell: str) -> List[str]:
        """Determine appropriate next steps based on the current TOWS cell"""
        cell_sequence = ["SO", "WO", "ST", "WT"]
        
        try:
            current_index = cell_sequence.index(current_cell)
            next_steps = []
            
            # Add options for proceeding to next cell if not on the last one
            if current_index < len(cell_sequence) - 1:
                next_cell = cell_sequence[current_index + 1]
                next_steps.append(f"Move to {next_cell} strategies")
            
            # Always allow adding more to current cell
            next_steps.append(f"Add more {current_cell} strategies")
            
            # If on the last cell, suggest generating insights
            if current_index == len(cell_sequence) - 1:
                next_steps.append("Generate strategic insights")
            
            # Add review option
            next_steps.append("Review TOWS matrix")
            
            return next_steps
            
        except ValueError:
            # Fallback if cell not found in sequence
            return [
                "Add SO strategies",
                "Add WO strategies",
                "Add ST strategies",
                "Add WT strategies",
                "Review TOWS matrix"
            ]
    
    def _determine_focus_area(self, s_count: int, w_count: int, o_count: int, t_count: int) -> str:
        """Determine which SWOT quadrant needs attention based on current counts"""
        counts = {
            "strength": s_count,
            "weakness": w_count,
            "opportunity": o_count,
            "threat": t_count
        }
        
        # Find the quadrant with the lowest count
        min_category = min(counts, key=counts.get)
        
        return min_category
    
    def _determine_tows_focus_area(self, so_count: int, wo_count: int, st_count: int, wt_count: int) -> str:
        """Determine which TOWS cell needs attention based on current counts"""
        counts = {
            "SO": so_count,
            "WO": wo_count,
            "ST": st_count,
            "WT": wt_count
        }
        
        # Find the cell with the lowest count
        min_cell = min(counts, key=counts.get)
        
        return min_cell
    
    def _generate_tips_for_swot_completion(self, completion: float, focus_area: str) -> List[str]:
        """Generate tips based on SWOT completion percentage"""
        if completion < 25:
            return [
                "Start by focusing on the basics of each quadrant",
                f"Add more items to the {focus_area} quadrant",
                "Be specific and concise in your descriptions",
                "Consider both internal and external factors"
            ]
        elif completion < 50:
            return [
                f"Continue adding items to the {focus_area} quadrant",
                "Look for patterns or themes emerging in your analysis",
                "Consider factors specific to your industry or market",
                "Think about both short-term and long-term considerations"
            ]
        elif completion < 75:
            return [
                "Your SWOT analysis is taking shape",
                f"Add a few more items to the {focus_area} quadrant",
                "Review existing items for clarity and specificity",
                "Ensure you have a balanced view across all quadrants"
            ]
        else:
            return [
                "Your SWOT analysis is nearly complete",
                "Review all quadrants for completeness",
                "Consider how items across quadrants relate to each other",
                "Prepare to move to the TOWS matrix to develop strategies"
            ]
    
    def _generate_tips_for_tows_completion(self, completion: float, focus_cell: str) -> List[str]:
        """Generate tips based on TOWS completion percentage"""
        if completion < 25:
            return [
                "Start by developing basic strategies for each cell",
                f"Focus on adding strategies to the {focus_cell} cell",
                "Be specific about actions you could take",
                "Connect specific SWOT elements in your strategies"
            ]
        elif completion < 50:
            return [
                f"Continue adding strategies to the {focus_cell} cell",
                "Make sure strategies are actionable and specific",
                "Think about both immediate and longer-term actions",
                "Consider resource implications of your strategies"
            ]
        elif completion < 75:
            return [
                "Your TOWS matrix is taking shape",
                f"Add a few more strategies to the {focus_cell} cell",
                "Review existing strategies for clarity and feasibility",
                "Ensure strategies align with your company's capabilities"
            ]
        else:
            return [
                "Your TOWS matrix is nearly complete",
                "Review all cells for comprehensive coverage",
                "Consider prioritizing strategies by impact and feasibility",
                "Prepare to generate strategic insights and finalize your analysis"
            ]