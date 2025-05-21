import json
from typing import List, Dict, Any
from semantic_kernel.skill_definition import sk_function, sk_function_context_parameter
from ...prompt_templates import render_template

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
        
        # Format the SWOT context for the template
        swot_context = ""
        if any([strengths, weaknesses, opportunities, threats]):
            if strengths:
                swot_context += f"STRENGTHS: {self._format_items(strengths)}\n"
            if weaknesses:
                swot_context += f"WEAKNESSES: {self._format_items(weaknesses)}\n"
            if opportunities:
                swot_context += f"OPPORTUNITIES: {self._format_items(opportunities)}\n"
            if threats:
                swot_context += f"THREATS: {self._format_items(threats)}\n"
        
        # Create a context dictionary for the template
        template_context = {
            "topic": topic,
            "company_name": company_name,
            "category": category,
            "category_name": category_name,
            "swot_context": swot_context.strip(),
            "subjective_data": subjective_data,
            "objective_data": objective_data
        }
        
        # Render the template with context
        return render_template("generate_swot_quadrant", template_context)
    
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
            
            # Create a dynamic LLM prompt that incorporates all context and few-shot examples
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
        
        # Format empty lists with appropriate message
        strengths_formatted = self._format_items(strengths) if strengths else "None identified yet"
        weaknesses_formatted = self._format_items(weaknesses) if weaknesses else "None identified yet"
        opportunities_formatted = self._format_items(opportunities) if opportunities else "None identified yet" 
        threats_formatted = self._format_items(threats) if threats else "None identified yet"
        
        # Create a context dictionary for the template
        template_context = {
            "topic": topic,
            "company_name": company_name,
            "cell_type": cell_type,
            "cell_description": cell_description,
            "strengths": strengths_formatted,
            "weaknesses": weaknesses_formatted,
            "opportunities": opportunities_formatted,
            "threats": threats_formatted,
            "cell_strategies": cell_strategies,
            "primary_component": primary_component,
            "secondary_component": secondary_component
        }
        
        # Use few-shot examples to improve response quality
        include_examples = True
        
        # Render the template with context and examples
        return render_template("generate_tows_cell", template_context, include_examples)
    
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