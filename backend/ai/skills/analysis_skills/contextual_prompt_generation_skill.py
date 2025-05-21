import json
from typing import List, Dict, Any
from semantic_kernel.functions import kernel_function # Updated import
# from semantic_kernel.orchestration.sk_context import SKContext # SKContext might be replaced by KernelArguments or direct params
from ...prompt_templates import render_template # Assuming this utility is available

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
