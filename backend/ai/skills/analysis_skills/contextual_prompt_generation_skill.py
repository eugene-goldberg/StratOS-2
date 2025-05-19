import json
from typing import List, Dict, Any
from semantic_kernel.skill_definition import sk_function, sk_function_context_parameter

class ContextualPromptGenerationSkill:
    """
    Semantic Kernel skill for generating contextual prompts for SWOT/TOWS analysis
    by dynamically creating LLM prompts and invoking the AI to generate guiding questions
    """
    
    @sk_function(
        description="Generates contextual prompts for a SWOT quadrant using LLM",
        name="generate_swot_quadrant_prompt"
    )
    @sk_function_context_parameter(
        name="topic",
        description="The topic of the SWOT analysis"
    )
    @sk_function_context_parameter(
        name="company_name",
        description="The company name"
    )
    @sk_function_context_parameter(
        name="category",
        description="The SWOT category (strength, weakness, opportunity, threat)"
    )
    @sk_function_context_parameter(
        name="strengths",
        description="List of existing strengths",
        default_value="[]"
    )
    @sk_function_context_parameter(
        name="weaknesses",
        description="List of existing weaknesses",
        default_value="[]"
    )
    @sk_function_context_parameter(
        name="opportunities",
        description="List of existing opportunities",
        default_value="[]"
    )
    @sk_function_context_parameter(
        name="threats",
        description="List of existing threats",
        default_value="[]"
    )
    @sk_function_context_parameter(
        name="subjective_data",
        description="Relevant subjective data from CEO logs",
        default_value=""
    )
    @sk_function_context_parameter(
        name="objective_data",
        description="Relevant objective data from business metrics",
        default_value=""
    )
    async def generate_swot_quadrant_prompt(self, context) -> str:
        """
        Generates contextual prompts for a SWOT quadrant by using an LLM to provide
        tailored guiding questions based on the current analysis context
        """
        try:
            from ..kernel_service import kernel_service
            
            # Extract context variables
            topic = context["topic"]
            company_name = context["company_name"]
            category = context["category"].lower()
            
            # Validate category
            valid_categories = ["strength", "weakness", "opportunity", "threat"]
            if category not in valid_categories:
                return json.dumps({"error": f"Invalid category. Must be one of: {', '.join(valid_categories)}"})
            
            # Parse SWOT items from context
            strengths = self._parse_items(context.get("strengths", "[]"))
            weaknesses = self._parse_items(context.get("weaknesses", "[]"))
            opportunities = self._parse_items(context.get("opportunities", "[]"))
            threats = self._parse_items(context.get("threats", "[]"))
            
            # Get contextual data
            subjective_data = context.get("subjective_data", "").strip()
            objective_data = context.get("objective_data", "").strip()
            
            # Create a dynamic LLM prompt that incorporates all context
            llm_prompt = self._create_swot_prompt(
                topic=topic,
                company_name=company_name,
                category=category,
                strengths=strengths,
                weaknesses=weaknesses,
                opportunities=opportunities,
                threats=threats,
                subjective_data=subjective_data,
                objective_data=objective_data
            )
            
            # Invoke the LLM to generate contextual guiding questions
            llm_response = await kernel_service.generate_completion(llm_prompt, max_tokens=800)
            
            # Process the LLM response and format it as JSON for the frontend
            category_name = self._get_category_full_name(category)
            
            completion_percentage = len(locals().get(f"{category}s", [])) / 5 * 100
            completion_percentage = min(completion_percentage, 100)
            
            # Format the response as JSON
            response = {
                "category": category,
                "category_name": category_name,
                "guiding_questions": llm_response.strip().split("\n"),
                "existing_items": {
                    "strengths": strengths,
                    "weaknesses": weaknesses,
                    "opportunities": opportunities,
                    "threats": threats
                },
                "guidance": {
                    "suggested_focus": f"Add at least 3-5 items to the {category_name} quadrant",
                    "completion": completion_percentage
                }
            }
            
            return json.dumps(response)
        except Exception as e:
            return json.dumps({"error": str(e)})
    
    def _create_swot_prompt(self, topic, company_name, category, strengths, weaknesses, 
                           opportunities, threats, subjective_data, objective_data) -> str:
        """
        Creates a detailed prompt for the LLM to generate guiding questions for a SWOT quadrant
        """
        category_name = self._get_category_full_name(category)
        
        # Build the prompt with all available context
        prompt = f"""You are an expert strategic advisor helping a CEO conduct a SWOT analysis for {company_name}.
        
Topic of analysis: {topic}
Current quadrant: {category_name.upper()}

Your task is to generate 5-7 thought-provoking guiding questions to help the CEO identify {category_name}s for {company_name} regarding {topic}.

"""
        
        # Add current SWOT state for context if items exist
        swot_context = ""
        if any([strengths, weaknesses, opportunities, threats]):
            swot_context += "Current SWOT Analysis state:\n"
            if strengths:
                swot_context += f"STRENGTHS: {self._format_items(strengths)}\n"
            if weaknesses:
                swot_context += f"WEAKNESSES: {self._format_items(weaknesses)}\n"
            if opportunities:
                swot_context += f"OPPORTUNITIES: {self._format_items(opportunities)}\n"
            if threats:
                swot_context += f"THREATS: {self._format_items(threats)}\n"
            
            prompt += f"{swot_context}\n"
        
        # Add subjective data if available
        if subjective_data:
            prompt += f"""
Relevant notes from CEO's Log:
{subjective_data}

"""
        
        # Add objective data if available
        if objective_data:
            prompt += f"""
Relevant business metrics and data:
{objective_data}

"""
        
        # Add specific instructions based on the category
        category_prompts = {
            "strength": """
Focus on INTERNAL, CURRENT POSITIVE factors that give the company an advantage:
- What does the company do exceptionally well?
- What unique resources, assets, or capabilities does the company possess?
- What advantages does the company have over competitors?
- What do customers or partners see as the company's strengths?
""",
            "weakness": """
Focus on INTERNAL, CURRENT NEGATIVE factors that place the company at a disadvantage:
- What areas could the company improve in?
- What necessary skills, resources, or technologies is the company lacking?
- What do competitors do better?
- What processes or activities might be limiting performance?
""",
            "opportunity": """
Focus on EXTERNAL, FUTURE POSITIVE factors that the company could capitalize on:
- What market trends or conditions could benefit the company?
- What changes in technology, policy, or society present new openings?
- What gaps exist in the market that the company could fill?
- What moves could open new markets or customer segments?
""",
            "threat": """
Focus on EXTERNAL, FUTURE NEGATIVE factors that could harm the company's position:
- What obstacles or challenges does the company face?
- What are competitors doing that could impact the company?
- What changing regulations or standards might cause problems?
- What negative market or economic trends could affect the company?
"""
        }
        
        prompt += category_prompts[category]
        
        # Add final instructions for response format
        prompt += f"""
Based on all this information, generate 5-7 specific, thought-provoking questions to help the CEO identify {category_name}s for {company_name} regarding {topic}.

Each question should:
1. Be specific to {company_name} and {topic}
2. Build on existing analysis data where relevant
3. Incorporate insights from the CEO's notes and business metrics when applicable
4. Help uncover {category_name}s that might not be immediately obvious

Format your response as a list of questions, one per line, without numbering or bullet points.
"""
        
        return prompt
    
    @sk_function(
        description="Generates contextual prompts for a TOWS cell using LLM",
        name="generate_tows_cell_prompt"
    )
    @sk_function_context_parameter(
        name="topic",
        description="The topic of the analysis"
    )
    @sk_function_context_parameter(
        name="company_name",
        description="The company name"
    )
    @sk_function_context_parameter(
        name="cell_type",
        description="The TOWS cell type (SO, WO, ST, WT)"
    )
    @sk_function_context_parameter(
        name="strengths",
        description="List of strengths",
        default_value="[]"
    )
    @sk_function_context_parameter(
        name="weaknesses",
        description="List of weaknesses",
        default_value="[]"
    )
    @sk_function_context_parameter(
        name="opportunities",
        description="List of opportunities",
        default_value="[]"
    )
    @sk_function_context_parameter(
        name="threats",
        description="List of threats",
        default_value="[]"
    )
    @sk_function_context_parameter(
        name="strategies",
        description="Existing TOWS strategies",
        default_value="[]"
    )
    async def generate_tows_cell_prompt(self, context) -> str:
        """
        Generates contextual prompts for a TOWS cell by using an LLM to provide
        tailored guiding questions based on the current analysis data
        """
        try:
            from ..kernel_service import kernel_service
            
            # Extract context variables
            topic = context["topic"]
            company_name = context["company_name"]
            cell_type = context["cell_type"].upper()
            
            # Validate cell type
            valid_cell_types = ["SO", "WO", "ST", "WT"]
            if cell_type not in valid_cell_types:
                return json.dumps({"error": f"Invalid cell type. Must be one of: {', '.join(valid_cell_types)}"})
            
            # Parse SWOT items and strategies from context
            strengths = self._parse_items(context.get("strengths", "[]"))
            weaknesses = self._parse_items(context.get("weaknesses", "[]"))
            opportunities = self._parse_items(context.get("opportunities", "[]"))
            threats = self._parse_items(context.get("threats", "[]"))
            strategies = self._parse_strategies(context.get("strategies", "[]"))
            
            # Filter strategies for the current cell type
            cell_strategies = [s for s in strategies if s.get("strategy_type") == cell_type]
            
            # Create a dynamic LLM prompt that incorporates all context
            llm_prompt = self._create_tows_prompt(
                topic=topic,
                company_name=company_name,
                cell_type=cell_type,
                strengths=strengths,
                weaknesses=weaknesses,
                opportunities=opportunities,
                threats=threats,
                cell_strategies=cell_strategies
            )
            
            # Invoke the LLM to generate contextual guiding questions
            llm_response = await kernel_service.generate_completion(llm_prompt, max_tokens=800)
            
            # Get the cell description
            cell_description = self._get_cell_description(cell_type)
            
            # Calculate completion percentage
            completion_percentage = len(cell_strategies) / 3 * 100
            completion_percentage = min(completion_percentage, 100)
            
            # Format the response as JSON
            response = {
                "cell_type": cell_type,
                "description": cell_description,
                "guiding_questions": llm_response.strip().split("\n"),
                "existing_items": {
                    "strengths": strengths,
                    "weaknesses": weaknesses,
                    "opportunities": opportunities,
                    "threats": threats
                },
                "existing_strategies": cell_strategies,
                "guidance": {
                    "suggested_focus": f"Add at least 2-3 strategies to the {cell_type} cell",
                    "completion": completion_percentage
                }
            }
            
            return json.dumps(response)
        except Exception as e:
            return json.dumps({"error": str(e)})
    
    def _create_tows_prompt(self, topic, company_name, cell_type, strengths, weaknesses, 
                            opportunities, threats, cell_strategies) -> str:
        """
        Creates a detailed prompt for the LLM to generate guiding questions for a TOWS cell
        """
        cell_description = self._get_cell_description(cell_type)
        
        # Determine which two SWOT components are relevant for this TOWS cell
        primary_component, secondary_component = self._get_tows_components(cell_type)
        primary_items = strengths if primary_component == "strengths" else weaknesses
        secondary_items = opportunities if secondary_component == "opportunities" else threats
        
        # Build the prompt with all available context
        prompt = f"""You are an expert strategic advisor helping a CEO develop a TOWS matrix based on their SWOT analysis for {company_name}.

Topic of analysis: {topic}
Current TOWS cell: {cell_type} - {cell_description}

Your task is to generate 5-7 thought-provoking guiding questions to help the CEO develop strategic actions for the {cell_type} cell of their TOWS matrix.

"""
        
        # Add current SWOT items for context
        prompt += "SWOT Analysis data:\n"
        if strengths:
            prompt += f"STRENGTHS: {self._format_items(strengths)}\n"
        else:
            prompt += "STRENGTHS: None identified yet\n"
            
        if weaknesses:
            prompt += f"WEAKNESSES: {self._format_items(weaknesses)}\n"
        else:
            prompt += "WEAKNESSES: None identified yet\n"
            
        if opportunities:
            prompt += f"OPPORTUNITIES: {self._format_items(opportunities)}\n"
        else:
            prompt += "OPPORTUNITIES: None identified yet\n"
            
        if threats:
            prompt += f"THREATS: {self._format_items(threats)}\n"
        else:
            prompt += "THREATS: None identified yet\n"
        
        # Add existing strategies for this cell if available
        if cell_strategies:
            prompt += f"\nExisting {cell_type} strategies:\n"
            for i, strategy in enumerate(cell_strategies, 1):
                prompt += f"{i}. {strategy.get('text', '')}\n"
        
        # Get the singular forms of the components
        primary_singular = primary_component[:-1] if primary_component.endswith("s") else primary_component
        secondary_singular = secondary_component[:-1] if secondary_component.endswith("s") else secondary_component
        
        # Add specific instructions based on the cell type
        cell_prompts = {
            "SO": f"""
For the SO cell (Strengths-Opportunities), I need questions that help the CEO identify strategies that use {company_name}'s strengths to capitalize on external opportunities.

Focus on how each strength can be leveraged to take advantage of specific opportunities:
- How can {company_name} use its internal advantages to exploit external possibilities?
- What capabilities can be directed toward emerging opportunities?
- How might existing strengths be enhanced to capitalize on market openings?
""",
            "WO": f"""
For the WO cell (Weaknesses-Opportunities), I need questions that help the CEO identify strategies to overcome {company_name}'s weaknesses by taking advantage of external opportunities.

Focus on how opportunities might help address or compensate for weaknesses:
- How can {company_name} use external opportunities to improve internal weaknesses?
- What market trends or conditions might provide resources or approaches to overcome limitations?
- How can emerging opportunities help transform weaknesses into strengths?
""",
            "ST": f"""
For the ST cell (Strengths-Threats), I need questions that help the CEO identify strategies that use {company_name}'s strengths to mitigate external threats.

Focus on how strengths can be used as shields or counters against threats:
- How can {company_name} leverage its internal advantages to reduce vulnerability to external threats?
- What strengths can be deployed to neutralize or minimize specific threats?
- How might existing capabilities be repurposed to address emerging challenges?
""",
            "WT": f"""
For the WT cell (Weaknesses-Threats), I need questions that help the CEO identify strategies to minimize {company_name}'s weaknesses and avoid external threats.

Focus on defensive approaches that address vulnerabilities and risks:
- How can {company_name} minimize exposure of weaknesses to threats?
- What defensive measures might reduce the combined impact of internal limitations and external challenges?
- What partnerships or restructuring could help address both weaknesses and threats simultaneously?
"""
        }
        
        prompt += cell_prompts[cell_type]
        
        # Add final instructions for response format
        prompt += f"""
Based on the specific {primary_component} and {secondary_component} from the SWOT analysis, generate 5-7 thought-provoking questions that will help the CEO develop strategic actions for the {cell_type} cell.

Each question should:
1. Connect specific {primary_component} with specific {secondary_component} where possible
2. Be tailored to {company_name} and {topic}
3. Build on existing {cell_type} strategies where relevant
4. Help uncover strategic approaches that might not be immediately obvious

Format your response as a list of questions, one per line, without numbering or bullet points.
"""
        
        return prompt
    
    def _parse_items(self, items_data) -> List[str]:
        """Parse SWOT items from context data which may be a string or a list"""
        if not items_data:
            return []
        
        if isinstance(items_data, str):
            try:
                items = json.loads(items_data)
                if isinstance(items, list):
                    # If items are objects with 'text' property, extract just the text
                    if items and isinstance(items[0], dict) and 'text' in items[0]:
                        return [item['text'] for item in items]
                    # If items are strings, return as is
                    if items and isinstance(items[0], str):
                        return items
                    # Default case
                    return items
            except json.JSONDecodeError:
                # If not valid JSON, treat as a single text item
                return [items_data]
        
        # If already a list
        if isinstance(items_data, list):
            # If items are objects with 'text' property, extract just the text
            if items_data and isinstance(items_data[0], dict) and 'text' in items_data[0]:
                return [item['text'] for item in items_data]
            # If items are strings, return as is
            if items_data and isinstance(items_data[0], str):
                return items_data
        
        # Default case
        return []
    
    def _parse_strategies(self, strategies_data) -> List[Dict[str, Any]]:
        """Parse TOWS strategies from context data which may be a string or a list"""
        if not strategies_data:
            return []
        
        if isinstance(strategies_data, str):
            try:
                strategies = json.loads(strategies_data)
                if isinstance(strategies, list):
                    return strategies
            except json.JSONDecodeError:
                return []
        
        # If already a list
        if isinstance(strategies_data, list):
            return strategies_data
        
        # Default case
        return []
    
    def _format_items(self, items: List[str]) -> str:
        """Format a list of items for inclusion in an LLM prompt"""
        if not items:
            return "None"
        return "; ".join(items)
    
    def _get_category_full_name(self, category: str) -> str:
        """Get the full name of a SWOT category"""
        category_names = {
            "strength": "Strength",
            "weakness": "Weakness",
            "opportunity": "Opportunity",
            "threat": "Threat"
        }
        return category_names.get(category, category)
    
    def _get_cell_description(self, cell_type: str) -> str:
        """Get the description of a TOWS cell"""
        cell_descriptions = {
            "SO": "Strengths-Opportunities (Using strengths to capitalize on opportunities)",
            "WO": "Weaknesses-Opportunities (Overcoming weaknesses by taking advantage of opportunities)",
            "ST": "Strengths-Threats (Using strengths to mitigate threats)",
            "WT": "Weaknesses-Threats (Minimizing weaknesses and avoiding threats)"
        }
        return cell_descriptions.get(cell_type, cell_type)
    
    def _get_tows_components(self, cell_type: str) -> tuple:
        """Get the two SWOT components that make up a TOWS cell"""
        components = {
            "SO": ("strengths", "opportunities"),
            "WO": ("weaknesses", "opportunities"),
            "ST": ("strengths", "threats"),
            "WT": ("weaknesses", "threats")
        }
        return components.get(cell_type, ("", ""))