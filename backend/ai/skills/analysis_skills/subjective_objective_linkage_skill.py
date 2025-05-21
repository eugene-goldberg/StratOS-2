import json
import re # Added re import
from typing import Dict, List, Any
from semantic_kernel.functions import kernel_function # Updated import
# from semantic_kernel.orchestration.sk_context import SKContext # Old way

class SubjectiveObjectiveLinkageSkill:
    """
    Semantic Kernel skill for finding potential linkages between subjective insights and objective data.
    """
    
    # Prompt template for finding potential linkages between subjective and objective data
    PROMPT_TEMPLATE = """System:
You are an AI strategic analysis assistant. Your task is to identify meaningful connections (correlations, contradictions, or emerging themes) between a CEO's subjective insights and available objective data related to a specific strategic topic.

Strategic Topic Context: "{{$topic_context}}"

Provided Subjective Insights (S) from CEO's Log (JSON format: [{"id": "...", "text": "..."}]):
{{$subjective_snippets_json}}

Provided Objective Data Snippets (O) (JSON format: [{"id": "...", "title": "...", "text": "..."}]):
{{$objective_snippets_json}}

Instructions:
Analyze the provided Subjective (S) and Objective (O) snippets. Identify up to 3-5 of the most significant potential linkages.
For each linkage found, provide:
1.  `subjective_ref_id`: The ID of the subjective snippet involved.
2.  `objective_ref_id`: The ID of the objective snippet involved.
3.  `linkage_type`: Classify the linkage as "correlation" (data supports insight), "contradiction" (data challenges insight), or "emerging_theme" (a new theme arises from combining S and O).
4.  `ai_summary_of_linkage`: A concise explanation (1-2 sentences) describing the connection you found between the specific S and O items.
5.  `ai_prompt_for_ceo`: A thought-provoking question for the CEO based on this linkage, designed to stimulate further strategic thinking or action.

Format your entire output as a single JSON array of linkage objects. Ensure the JSON is valid.

JSON Array of Linkages:
"""

    @kernel_function(
        description="Finds potential linkages between subjective insights and objective data snippets.",
        name="FindPotentialLinkages"
    )
    async def find_potential_linkages(
        self,
        topic_context: str,
        subjective_snippets_json: str, # JSON array of subjective snippets
        objective_snippets_json: str  # JSON array of objective snippets
    ) -> str:
        """
        Find potential linkages between subjective and objective data snippets.
        
        :param topic_context: The strategic topic context.
        :param subjective_snippets_json: JSON array string of subjective snippets.
        :param objective_snippets_json: JSON array string of objective snippets.
        :return: JSON array string of potential linkages.
        """
        try:
            from ..kernel_service import kernel_service # Local import

            # Format the prompt with the provided context
            # Using f-strings or a more robust templating if available in kernel_service or SK
            # For now, direct replacement for simplicity, assuming $ are part of the key
            # A better way would be to pass these as variables to a semantic function if this were one.
            # Since this is a native function calling an LLM, we build the prompt manually.
            
            # This manual replacement is fragile. If kernel_service.generate_completion
            # can take variables, that's preferred. Assuming it takes a raw prompt for now.
            prompt = self.PROMPT_TEMPLATE
            prompt = prompt.replace("{{$topic_context}}", str(topic_context))
            prompt = prompt.replace("{{$subjective_snippets_json}}", str(subjective_snippets_json))
            prompt = prompt.replace("{{$objective_snippets_json}}", str(objective_snippets_json))
            
            llm_response = await kernel_service.generate_completion(prompt, max_tokens=1024) # Increased max_tokens

            linkages = await self.process_llm_response(llm_response)
            return json.dumps(linkages)
        except Exception as e:
            # Log exception e
            return json.dumps({"error": str(e)})

    async def process_llm_response(self, llm_response: str) -> List[Dict[str, Any]]:
        try:
            linkages = json.loads(llm_response)
            validated_linkages = []
            if isinstance(linkages, list): # Ensure it's a list
                for linkage in linkages:
                    if not isinstance(linkage, dict): continue # Skip non-dict items
                    if not all(key in linkage for key in ["subjective_ref_id", "objective_ref_id", 
                                                          "linkage_type", "ai_summary_of_linkage", 
                                                          "ai_prompt_for_ceo"]):
                        continue
                    if linkage["linkage_type"] not in ["correlation", "contradiction", "emerging_theme"]:
                        linkage["linkage_type"] = "correlation" 
                    validated_linkages.append(linkage)
            return validated_linkages
        except json.JSONDecodeError:
            return self._fallback_response_parser(llm_response)
    
    def _fallback_response_parser(self, text: str) -> List[Dict[str, Any]]:
        linkages = []
        # Simplified fallback: assumes each linkage might be a JSON object on its own line or separated
        # This is very basic and might need significant improvement based on actual LLM outputs.
        try:
            # Attempt to find JSON objects within the text if the whole thing isn't valid JSON array
            # This could happen if LLM adds introductory text.
            json_objects_match = re.findall(r'{.*?}', text, re.DOTALL)
            for obj_str in json_objects_match:
                try:
                    linkage = json.loads(obj_str)
                    if isinstance(linkage, dict) and all(key in linkage for key in ["subjective_ref_id", "objective_ref_id", "linkage_type", "ai_summary_of_linkage", "ai_prompt_for_ceo"]):
                        if linkage["linkage_type"] not in ["correlation", "contradiction", "emerging_theme"]:
                            linkage["linkage_type"] = "correlation"
                        linkages.append(linkage)
                except json.JSONDecodeError:
                    continue # Skip if individual object isn't valid JSON
            if linkages: return linkages # Return if we found some objects
        except Exception:
            pass # Fall through if regex or other parsing fails

        # Original fallback if the above doesn't work (less likely to be useful if not a list of dicts)
        sections = text.split("\n\n") # Or some other delimiter if LLM uses it
        for section in sections:
            try:
                lines = section.strip().split("\n")
                linkage_cand = {}
                for line in lines:
                    line = line.strip()
                    if line.startswith("subjective_ref_id") or line.startswith('"subjective_ref_id"'):
                        linkage_cand["subjective_ref_id"] = line.split(":", 1)[1].strip().strip('",')
                    elif line.startswith("objective_ref_id") or line.startswith('"objective_ref_id"'):
                        linkage_cand["objective_ref_id"] = line.split(":", 1)[1].strip().strip('",')
                    elif line.startswith("linkage_type") or line.startswith('"linkage_type"'):
                        linkage_type_val = line.split(":", 1)[1].strip().strip('",').lower()
                        linkage_cand["linkage_type"] = linkage_type_val if linkage_type_val in ["correlation", "contradiction", "emerging_theme"] else "correlation"
                    elif line.startswith("ai_summary") or line.startswith('"ai_summary'): # Flexible start
                        linkage_cand["ai_summary_of_linkage"] = line.split(":", 1)[1].strip().strip('",')
                    elif line.startswith("ai_prompt") or line.startswith('"ai_prompt'): # Flexible start
                        linkage_cand["ai_prompt_for_ceo"] = line.split(":", 1)[1].strip().strip('",')
                
                if all(key in linkage_cand for key in ["subjective_ref_id", "objective_ref_id", "linkage_type", "ai_summary_of_linkage", "ai_prompt_for_ceo"]):
                    linkages.append(linkage_cand)
            except Exception:
                continue
        return linkages
