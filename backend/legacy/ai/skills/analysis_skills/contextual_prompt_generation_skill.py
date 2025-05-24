import json
from typing import List, Dict, Any, Optional
from uuid import UUID
from semantic_kernel.functions import kernel_function
from ...prompt_templates import render_template

class ContextualPromptGenerationSkill:
    """
    Semantic Kernel skill for generating contextual prompts for SWOT/TOWS analysis
    by dynamically creating LLM prompts and invoking the AI to generate guiding questions.
    """
    
    @kernel_function(
        description="Generates contextual prompts for a SWOT quadrant using LLM.",
        name="generate_swot_quadrant_prompt"
    )
    async def generate_swot_quadrant_prompt(
        self,
        topic: str,
        company_name: str,
        category: str,
        strengths: str = "[]", # JSON string list
        weaknesses: str = "[]", # JSON string list
        opportunities: str = "[]", # JSON string list
        threats: str = "[]", # JSON string list
        subjective_data: str = "",
        objective_data: str = ""
        # context: SKContext # Old way of passing context
    ) -> str:
        """
        Generates contextual prompts for a SWOT quadrant by using an LLM.
        :param topic: The topic of the SWOT analysis.
        :param company_name: The company name.
        :param category: The SWOT category (strength, weakness, opportunity, threat).
        :param strengths: JSON string list of existing strengths.
        :param weaknesses: JSON string list of existing weaknesses.
        :param opportunities: JSON string list of existing opportunities.
        :param threats: JSON string list of existing threats.
        :param subjective_data: Relevant subjective data from CEO logs.
        :param objective_data: Relevant objective data from business metrics.
        :return: JSON string with guiding questions and analysis context.
        """
        try:
            # kernel_service is imported locally to avoid circular dependencies at module load time
            # This is a common pattern if skills need to call back into the main kernel service.
            # Ideally, the kernel instance or a way to get services would be injected.
            from ..kernel_service import kernel_service 
            
            category_internal = category.lower()
            
            valid_categories = ["strength", "weakness", "opportunity", "threat"]
            if category_internal not in valid_categories:
                return json.dumps({"error": f"Invalid category. Must be one of: {', '.join(valid_categories)}"})
            
            parsed_strengths = self._parse_items(strengths)
            parsed_weaknesses = self._parse_items(weaknesses)
            parsed_opportunities = self._parse_items(opportunities)
            parsed_threats = self._parse_items(threats)
            
            llm_prompt = self._create_swot_prompt(
                topic=topic,
                company_name=company_name,
                category=category_internal,
                strengths=parsed_strengths,
                weaknesses=parsed_weaknesses,
                opportunities=parsed_opportunities,
                threats=parsed_threats,
                subjective_data=subjective_data.strip(),
                objective_data=objective_data.strip()
            )
            
            llm_response = await kernel_service.generate_completion(llm_prompt, max_tokens=800)
            
            category_name_full = self._get_category_full_name(category_internal)
            
            current_items_for_category = locals().get(f"parsed_{category_internal}s", []) # e.g. parsed_strengths
            completion_percentage = len(current_items_for_category) / 5 * 100 # Assuming target of 5 items
            completion_percentage = min(completion_percentage, 100)
            
            response = {
                "category": category_internal,
                "category_name": category_name_full,
                "guiding_questions": llm_response.strip().split("\n") if llm_response else [],
                "existing_items": {
                    "strengths": parsed_strengths,
                    "weaknesses": parsed_weaknesses,
                    "opportunities": parsed_opportunities,
                    "threats": parsed_threats
                },
                "guidance": {
                    "suggested_focus": f"Add at least 3-5 items to the {category_name_full} quadrant",
                    "completion": completion_percentage
                }
            }
            
            return json.dumps(response)
        except Exception as e:
            # Log the exception
            return json.dumps({"error": str(e)})
    
    def _create_swot_prompt(self, topic, company_name, category, strengths, weaknesses, 
                           opportunities, threats, subjective_data, objective_data) -> str:
        category_name_full = self._get_category_full_name(category)
        
        swot_context_parts = []
        if strengths: swot_context_parts.append(f"STRENGTHS: {self._format_items(strengths)}")
        if weaknesses: swot_context_parts.append(f"WEAKNESSES: {self._format_items(weaknesses)}")
        if opportunities: swot_context_parts.append(f"OPPORTUNITIES: {self._format_items(opportunities)}")
        if threats: swot_context_parts.append(f"THREATS: {self._format_items(threats)}")
        swot_context_str = "\n".join(swot_context_parts) if swot_context_parts else "No SWOT items identified yet."

        template_context = {
            "topic": topic,
            "company_name": company_name,
            "category": category,
            "category_name": category_name_full,
            "swot_context": swot_context_str,
            "subjective_data": subjective_data if subjective_data else "No subjective data provided.",
            "objective_data": objective_data if objective_data else "No objective data provided."
        }
        return render_template("generate_swot_quadrant", template_context)
    
    @kernel_function(
        description="Generates contextual prompts for a TOWS cell using LLM.",
        name="generate_tows_cell_prompt"
    )
    async def generate_tows_cell_prompt(
        self,
        topic: str,
        company_name: str,
        cell_type: str, # SO, WO, ST, WT
        strengths: str = "[]", # JSON string list
        weaknesses: str = "[]", # JSON string list
        opportunities: str = "[]", # JSON string list
        threats: str = "[]", # JSON string list
        strategies: str = "[]" # JSON string list of existing strategies
        # context: SKContext # Old way
    ) -> str:
        """
        Generates contextual prompts for a TOWS cell.
        :param topic: The topic of the analysis.
        :param company_name: The company name.
        :param cell_type: The TOWS cell type (SO, WO, ST, WT).
        :param strengths: JSON string list of strengths.
        :param weaknesses: JSON string list of weaknesses.
        :param opportunities: JSON string list of opportunities.
        :param threats: JSON string list of threats.
        :param strategies: JSON string list of existing TOWS strategies.
        :return: JSON string with guiding questions and TOWS context.
        """
        try:
            from ..kernel_service import kernel_service
            
            cell_type_upper = cell_type.upper()
            valid_cell_types = ["SO", "WO", "ST", "WT"]
            if cell_type_upper not in valid_cell_types:
                return json.dumps({"error": f"Invalid cell type. Must be one of: {', '.join(valid_cell_types)}"})
            
            parsed_strengths = self._parse_items(strengths)
            parsed_weaknesses = self._parse_items(weaknesses)
            parsed_opportunities = self._parse_items(opportunities)
            parsed_threats = self._parse_items(threats)
            parsed_strategies = self._parse_strategies(strategies)
            
            cell_strategies_filtered = [s for s in parsed_strategies if s.get("strategy_type") == cell_type_upper]
            
            llm_prompt = self._create_tows_prompt(
                topic=topic,
                company_name=company_name,
                cell_type=cell_type_upper,
                strengths=parsed_strengths,
                weaknesses=parsed_weaknesses,
                opportunities=parsed_opportunities,
                threats=parsed_threats,
                cell_strategies=cell_strategies_filtered
            )
            
            llm_response = await kernel_service.generate_completion(llm_prompt, max_tokens=800)
            
            cell_description_full = self._get_cell_description(cell_type_upper)
            completion_percentage = len(cell_strategies_filtered) / 3 * 100 # Assuming target of 3 strategies
            completion_percentage = min(completion_percentage, 100)
            
            response = {
                "cell_type": cell_type_upper,
                "description": cell_description_full,
                "guiding_questions": llm_response.strip().split("\n") if llm_response else [],
                "existing_items": {
                    "strengths": parsed_strengths,
                    "weaknesses": parsed_weaknesses,
                    "opportunities": parsed_opportunities,
                    "threats": parsed_threats
                },
                "existing_strategies": cell_strategies_filtered,
                "guidance": {
                    "suggested_focus": f"Add at least 2-3 strategies to the {cell_type_upper} cell",
                    "completion": completion_percentage
                }
            }
            return json.dumps(response)
        except Exception as e:
            # Log the exception
            return json.dumps({"error": str(e)})

    def _create_tows_prompt(self, topic, company_name, cell_type, strengths, weaknesses, 
                            opportunities, threats, cell_strategies) -> str:
        cell_description_full = self._get_cell_description(cell_type)
        primary_component, secondary_component = self._get_tows_components(cell_type)
        
        strengths_f = self._format_items(strengths) if strengths else "None identified yet"
        weaknesses_f = self._format_items(weaknesses) if weaknesses else "None identified yet"
        opportunities_f = self._format_items(opportunities) if opportunities else "None identified yet" 
        threats_f = self._format_items(threats) if threats else "None identified yet"
        
        template_context = {
            "topic": topic,
            "company_name": company_name,
            "cell_type": cell_type,
            "cell_description": cell_description_full,
            "strengths": strengths_f,
            "weaknesses": weaknesses_f,
            "opportunities": opportunities_f,
            "threats": threats_f,
            "cell_strategies": cell_strategies, # Assumes this is a list of strategy strings or dicts
            "primary_component": primary_component,
            "secondary_component": secondary_component
        }
        return render_template("generate_tows_cell", template_context, include_examples=True)
    
    def _parse_items(self, items_data: str) -> List[str]:
        try:
            items = json.loads(items_data)
            if isinstance(items, list):
                # Handle list of strings or list of dicts with 'text' or 'content'
                processed_items = []
                for item in items:
                    if isinstance(item, str):
                        processed_items.append(item)
                    elif isinstance(item, dict):
                        processed_items.append(item.get("text", item.get("content", "")))
                return [str(pi) for pi in processed_items if pi] # Ensure all are strings
            return [str(items)] # If not a list, treat as single item
        except (json.JSONDecodeError, TypeError):
            return [str(items_data)] if items_data else [] # Fallback for non-JSON string

    def _parse_strategies(self, strategies_data: str) -> List[Dict[str, Any]]:
        try:
            strategies = json.loads(strategies_data)
            return strategies if isinstance(strategies, list) else []
        except (json.JSONDecodeError, TypeError):
            return []

    def _format_items(self, items: List[str]) -> str:
        return "; ".join(items) if items else "None"
    
    def _get_category_full_name(self, category: str) -> str:
        return {"strength": "Strength", "weakness": "Weakness", "opportunity": "Opportunity", "threat": "Threat"}.get(category, category)
    
    def _get_cell_description(self, cell_type: str) -> str:
        return {
            "SO": "Strengths-Opportunities (Using strengths to capitalize on opportunities)",
            "WO": "Weaknesses-Opportunities (Overcoming weaknesses by taking advantage of opportunities)",
            "ST": "Strengths-Threats (Using strengths to mitigate threats)",
            "WT": "Weaknesses-Threats (Minimizing weaknesses and avoiding threats)"
        }.get(cell_type, cell_type)
    
    def _get_tows_components(self, cell_type: str) -> tuple:
        return {
            "SO": ("strengths", "opportunities"), "WO": ("weaknesses", "opportunities"),
            "ST": ("strengths", "threats"), "WT": ("weaknesses", "threats")
        }.get(cell_type, ("", ""))
    
    @kernel_function(
        description="Generates session-aware contextual guidance for guided SWOT/TOWS analysis",
        name="generate_session_guidance"
    )
    async def generate_session_guidance(
        self,
        session_id: str,
        user_id: str,
        step_id: str,
        topic: str,
        company_name: str = "",
        session_type: str = "guided_swot",
        current_items: str = "[]",  # JSON string of current items
        strategic_context: str = "{}",  # JSON string of North Star context
        subjective_data: str = "",
        objective_data: str = ""
    ) -> str:
        """
        Generate contextual guidance for a specific step in a guided analysis session.
        
        Args:
            session_id: ID of the analysis session
            user_id: ID of the user conducting the analysis
            step_id: Current step (e.g., "swot_strengths", "tows_so_cell")
            topic: Topic of the analysis
            company_name: Company name for context
            session_type: Type of analysis session (guided_swot, guided_tows)
            current_items: JSON string of items already identified
            strategic_context: JSON string containing North Star elements
            subjective_data: Relevant subjective data from CEO logs
            objective_data: Relevant objective data and metrics
            
        Returns:
            JSON string with comprehensive guidance response
        """
        try:
            from ...kernel_service import kernel_service
            
            # Parse inputs
            parsed_items = self._parse_items(current_items)
            parsed_strategic_context = self._parse_strategic_context(strategic_context)
            
            # Determine guidance type and parameters
            guidance_type, primary_focus = self._determine_guidance_type(step_id)
            
            # Build enhanced context for guidance generation
            enhanced_context = {
                "session_id": session_id,
                "user_id": user_id,
                "step_id": step_id,
                "topic": topic,
                "company_name": company_name,
                "session_type": session_type,
                "guidance_type": guidance_type,
                "primary_focus": primary_focus,
                "current_items": parsed_items,
                "strategic_context": parsed_strategic_context,
                "subjective_data": subjective_data.strip() if subjective_data else "",
                "objective_data": objective_data.strip() if objective_data else ""
            }
            
            # Generate context-aware guidance prompt
            guidance_prompt = self._create_session_guidance_prompt(enhanced_context)
            
            # Get AI guidance
            ai_response = await kernel_service.generate_completion(guidance_prompt, max_tokens=1000)
            
            # Parse and structure the response
            guidance_response = self._structure_guidance_response(
                enhanced_context, 
                ai_response,
                parsed_items
            )
            
            return json.dumps(guidance_response)
            
        except Exception as e:
            return json.dumps({"error": f"Error generating session guidance: {str(e)}"})
    
    def _parse_strategic_context(self, strategic_context_str: str) -> Dict[str, Any]:
        """Parse strategic context (North Star) from JSON string"""
        try:
            context = json.loads(strategic_context_str) if strategic_context_str else {}
            return {
                "purpose": context.get("purpose", {}).get("statement", ""),
                "vision": context.get("vision", {}).get("statement", ""),
                "values": [v.get("name", "") for v in context.get("values", [])],
                "strategic_goals": [g.get("title", "") for g in context.get("strategic_goals", [])]
            }
        except (json.JSONDecodeError, TypeError, AttributeError):
            return {"purpose": "", "vision": "", "values": [], "strategic_goals": []}
    
    def _determine_guidance_type(self, step_id: str) -> tuple:
        """Determine the type of guidance needed based on step ID"""
        if step_id.startswith("swot_"):
            category = step_id.replace("swot_", "")
            return "swot_quadrant", category
        elif step_id.startswith("tows_"):
            cell_type = step_id.replace("tows_", "").upper()
            return "tows_cell", cell_type
        else:
            return "general", step_id
    
    def _create_session_guidance_prompt(self, context: Dict[str, Any]) -> str:
        """Create an enhanced guidance prompt with strategic context"""
        
        guidance_type = context["guidance_type"]
        
        if guidance_type == "swot_quadrant":
            return self._create_enhanced_swot_prompt(context)
        elif guidance_type == "tows_cell":
            return self._create_enhanced_tows_prompt(context)
        else:
            return self._create_general_guidance_prompt(context)
    
    def _create_enhanced_swot_prompt(self, context: Dict[str, Any]) -> str:
        """Create enhanced SWOT guidance prompt with strategic context"""
        
        category = context["primary_focus"]
        category_name = self._get_category_full_name(category)
        
        strategic_context_text = self._format_strategic_context(context["strategic_context"])
        
        prompt = f"""You are an expert strategic advisor helping a CEO conduct a guided SWOT analysis.

ANALYSIS CONTEXT:
Company: {context['company_name']}
Topic: {context['topic']}
Current Focus: {category_name} identification
Session ID: {context['session_id']}

STRATEGIC FOUNDATION:
{strategic_context_text}

CURRENT PROGRESS:
Items already identified in {category_name}: {len(context['current_items'])}
{self._format_items(context['current_items']) if context['current_items'] else 'None yet'}

"""

        if context["subjective_data"]:
            prompt += f"""
RELEVANT CEO INSIGHTS:
{context['subjective_data']}
"""

        if context["objective_data"]:
            prompt += f"""
RELEVANT BUSINESS DATA:
{context['objective_data']}
"""

        prompt += f"""
GUIDANCE REQUEST:
Generate 5-7 strategic guiding questions to help the CEO identify additional {category_name}s that align with their strategic foundation and leverage their existing insights.

Focus on {category} factors that are:
"""

        if category == "strength":
            prompt += """- Internal capabilities that support the company's purpose and vision
- Resources or advantages that could help achieve strategic goals
- Areas where company values are reflected in superior performance"""
        elif category == "weakness":
            prompt += """- Internal limitations that might hinder achieving the vision
- Gaps between current capabilities and strategic goal requirements
- Areas where company values are not fully realized"""
        elif category == "opportunity":
            prompt += """- External possibilities that align with the company's purpose
- Market trends that could accelerate strategic goal achievement
- Ways to expand the company's impact on its mission"""
        elif category == "threat":
            prompt += """- External factors that could undermine the company's purpose
- Competitive or market forces that threaten strategic goal achievement
- Risks to the company's ability to deliver on its vision"""

        prompt += f"""

Each question should:
1. Connect to the company's strategic foundation (purpose, vision, values, goals)
2. Build on existing analysis and insights
3. Be specific and actionable for {context['company_name']}
4. Help uncover {category_name}s that might not be immediately obvious
5. Encourage strategic thinking beyond surface-level observations

Format as a numbered list of questions."""

        return prompt
    
    def _create_enhanced_tows_prompt(self, context: Dict[str, Any]) -> str:
        """Create enhanced TOWS guidance prompt with strategic context"""
        
        cell_type = context["primary_focus"]
        cell_description = self._get_cell_description(cell_type)
        strategic_context_text = self._format_strategic_context(context["strategic_context"])
        
        prompt = f"""You are an expert strategic advisor helping a CEO develop TOWS strategies.

ANALYSIS CONTEXT:
Company: {context['company_name']}
Topic: {context['topic']}
Current Focus: {cell_type} cell - {cell_description}
Session ID: {context['session_id']}

STRATEGIC FOUNDATION:
{strategic_context_text}

CURRENT PROGRESS:
Strategies already identified for {cell_type}: {len(context['current_items'])}
{self._format_items(context['current_items']) if context['current_items'] else 'None yet'}

"""

        if context["subjective_data"]:
            prompt += f"""
RELEVANT CEO INSIGHTS:
{context['subjective_data']}
"""

        if context["objective_data"]:
            prompt += f"""
RELEVANT BUSINESS DATA:
{context['objective_data']}
"""

        prompt += f"""
GUIDANCE REQUEST:
Generate 5-7 strategic questions to help the CEO develop {cell_type} strategies that align with their strategic foundation and leverage their existing insights.

For {cell_type} strategies, focus on approaches that:
- Align with the company's purpose and support the vision
- Reflect company values in their implementation
- Contribute to achieving specific strategic goals
- Are realistic given the company's current context

Each question should:
1. Connect specific SWOT elements in creative ways
2. Ensure strategic alignment with the company's foundation
3. Build on existing insights and data
4. Be actionable and specific to {context['company_name']}
5. Encourage innovative strategic thinking

Format as a numbered list of questions."""

        return prompt
    
    def _create_general_guidance_prompt(self, context: Dict[str, Any]) -> str:
        """Create general guidance prompt for non-standard steps"""
        
        prompt = f"""You are an expert strategic advisor providing guidance for a strategic analysis session.

CONTEXT:
Company: {context['company_name']}
Topic: {context['topic']}
Session Type: {context['session_type']}
Current Step: {context['step_id']}

Provide 3-5 helpful guidance points for this step of the analysis process.

Format as a numbered list."""

        return prompt
    
    def _format_strategic_context(self, strategic_context: Dict[str, Any]) -> str:
        """Format strategic context for prompt inclusion"""
        
        context_parts = []
        
        if strategic_context.get("purpose"):
            context_parts.append(f"Purpose: {strategic_context['purpose']}")
        
        if strategic_context.get("vision"):
            context_parts.append(f"Vision: {strategic_context['vision']}")
        
        if strategic_context.get("values"):
            values_str = ", ".join(strategic_context["values"])
            context_parts.append(f"Values: {values_str}")
        
        if strategic_context.get("strategic_goals"):
            goals_str = "; ".join(strategic_context["strategic_goals"])
            context_parts.append(f"Strategic Goals: {goals_str}")
        
        return "\n".join(context_parts) if context_parts else "No strategic foundation defined yet."
    
    def _structure_guidance_response(
        self, 
        context: Dict[str, Any], 
        ai_response: str,
        current_items: List[str]
    ) -> Dict[str, Any]:
        """Structure the AI response into a comprehensive guidance response"""
        
        # Extract questions from AI response
        questions = self._extract_questions_from_response(ai_response)
        
        # Calculate progress metrics
        target_count = 5 if context["guidance_type"] == "swot_quadrant" else 3
        completion_percentage = min((len(current_items) / target_count) * 100, 100)
        
        # Generate next steps
        next_steps = self._generate_next_steps(context, current_items, target_count)
        
        # Estimate time remaining
        estimated_time = self._estimate_time_remaining(context, current_items, target_count)
        
        return {
            "session_id": context["session_id"],
            "step_id": context["step_id"],
            "guidance_type": context["guidance_type"],
            "primary_focus": context["primary_focus"],
            "guiding_questions": questions,
            "suggestions": self._generate_suggestions(context, current_items),
            "examples": self._generate_examples(context),
            "next_steps": next_steps,
            "completion_guidance": self._generate_completion_guidance(context, current_items, target_count),
            "estimated_time_remaining": estimated_time,
            "progress": {
                "current_count": len(current_items),
                "target_count": target_count,
                "completion_percentage": completion_percentage
            },
            "strategic_alignment": {
                "purpose_connection": self._assess_purpose_alignment(context, current_items),
                "vision_support": self._assess_vision_alignment(context, current_items),
                "values_reflection": self._assess_values_alignment(context, current_items)
            }
        }
    
    def _extract_questions_from_response(self, ai_response: str) -> List[str]:
        """Extract numbered questions from AI response"""
        questions = []
        lines = ai_response.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Look for numbered questions (1., 2., etc.) or bulleted questions
            if any(line.startswith(f"{i}.") for i in range(1, 10)) or line.startswith('-') or line.startswith('•'):
                # Clean up the question
                question = line
                # Remove numbering and bullets
                for i in range(1, 10):
                    if question.startswith(f"{i}."):
                        question = question[2:].strip()
                        break
                if question.startswith('-') or question.startswith('•'):
                    question = question[1:].strip()
                
                if question and question.endswith('?'):
                    questions.append(question)
        
        return questions[:7]  # Limit to 7 questions
    
    def _generate_suggestions(self, context: Dict[str, Any], current_items: List[str]) -> List[str]:
        """Generate specific suggestions based on context"""
        suggestions = []
        
        if context["guidance_type"] == "swot_quadrant":
            category = context["primary_focus"]
            if len(current_items) < 3:
                suggestions.append(f"Start with the most obvious {category}s, then dive deeper")
                suggestions.append(f"Consider how {category}s relate to your strategic goals")
            else:
                suggestions.append(f"Look for subtle or overlooked {category}s")
                suggestions.append(f"Consider {category}s specific to your topic: {context['topic']}")
        
        elif context["guidance_type"] == "tows_cell":
            cell_type = context["primary_focus"]
            suggestions.append(f"Focus on strategies that combine specific elements from both categories")
            suggestions.append(f"Think about implementation timeline for {cell_type} strategies")
        
        return suggestions
    
    def _generate_examples(self, context: Dict[str, Any]) -> List[str]:
        """Generate relevant examples based on context"""
        examples = []
        
        if context["guidance_type"] == "swot_quadrant":
            category = context["primary_focus"]
            if category == "strength":
                examples.append("Strong brand reputation in the market")
                examples.append("Experienced leadership team")
            elif category == "weakness":
                examples.append("Limited marketing budget")
                examples.append("Outdated technology infrastructure")
            elif category == "opportunity":
                examples.append("Growing demand in new markets")
                examples.append("Potential strategic partnerships")
            elif category == "threat":
                examples.append("Increased competition")
                examples.append("Changing regulations")
        
        return examples[:3]  # Limit to 3 examples
    
    def _generate_next_steps(self, context: Dict[str, Any], current_items: List[str], target_count: int) -> List[str]:
        """Generate recommended next steps"""
        next_steps = []
        
        if len(current_items) < target_count:
            remaining = target_count - len(current_items)
            next_steps.append(f"Identify {remaining} more item(s) to complete this section")
            next_steps.append("Use the guiding questions to explore different angles")
        else:
            next_steps.append("Review and refine your current items")
            next_steps.append("Move to the next section of the analysis")
        
        return next_steps
    
    def _generate_completion_guidance(self, context: Dict[str, Any], current_items: List[str], target_count: int) -> Optional[str]:
        """Generate guidance on completion status"""
        if len(current_items) >= target_count:
            return f"Great! You've identified {len(current_items)} items. Consider if you want to add more or move to the next section."
        else:
            remaining = target_count - len(current_items)
            return f"You need {remaining} more item(s) to reach the recommended minimum of {target_count}."
    
    def _estimate_time_remaining(self, context: Dict[str, Any], current_items: List[str], target_count: int) -> int:
        """Estimate time remaining in minutes"""
        if len(current_items) >= target_count:
            return 2  # Just review time
        else:
            remaining = target_count - len(current_items)
            return remaining * 3  # Estimate 3 minutes per item
    
    def _assess_purpose_alignment(self, context: Dict[str, Any], current_items: List[str]) -> str:
        """Assess alignment with company purpose"""
        if context["strategic_context"].get("purpose"):
            return f"Consider how each item relates to your purpose: {context['strategic_context']['purpose']}"
        return "Define your company purpose to improve strategic alignment"
    
    def _assess_vision_alignment(self, context: Dict[str, Any], current_items: List[str]) -> str:
        """Assess alignment with company vision"""
        if context["strategic_context"].get("vision"):
            return f"Ensure items support your vision: {context['strategic_context']['vision']}"
        return "Define your company vision to improve strategic alignment"
    
    def _assess_values_alignment(self, context: Dict[str, Any], current_items: List[str]) -> str:
        """Assess alignment with company values"""
        if context["strategic_context"].get("values"):
            values_str = ", ".join(context["strategic_context"]["values"])
            return f"Check if items reflect your values: {values_str}"
        return "Define your company values to improve strategic alignment"
