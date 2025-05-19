import json
from typing import Dict, List, Any
from semantic_kernel.skill_definition import sk_function, sk_function_context_parameter
from semantic_kernel import SKContext

class SubjectiveObjectiveLinkageSkill:
    """
    Semantic Kernel skill for finding potential linkages between subjective insights and objective data
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

    @sk_function(
        description="Finds potential linkages between subjective insights and objective data snippets.",
        name="FindPotentialLinkages"
    )
    async def find_potential_linkages(self, context: SKContext) -> str:
        """
        Find potential linkages between subjective and objective data snippets
        
        Args:
            context: Semantic Kernel context containing the following variables:
                - topic_context: The strategic topic context
                - subjective_snippets_json: JSON array of subjective snippets
                - objective_snippets_json: JSON array of objective snippets
                
        Returns:
            JSON array string of potential linkages
        """
        # In a production implementation using SemanticKernel, the prompt execution 
        # would be handled by the kernel. This is a placeholder for the functionality.
        pass

    async def process_llm_response(self, llm_response: str) -> List[Dict[str, Any]]:
        """
        Process the LLM's response to extract linkages
        
        Args:
            llm_response: Raw response from the LLM
            
        Returns:
            List of linkage objects
        """
        try:
            # Try to parse the response as JSON
            linkages = json.loads(llm_response)
            
            # Validate the structure of each linkage
            validated_linkages = []
            for linkage in linkages:
                # Check required fields
                if not all(key in linkage for key in ["subjective_ref_id", "objective_ref_id", 
                                                      "linkage_type", "ai_summary_of_linkage", 
                                                      "ai_prompt_for_ceo"]):
                    continue
                
                # Validate linkage_type
                if linkage["linkage_type"] not in ["correlation", "contradiction", "emerging_theme"]:
                    linkage["linkage_type"] = "correlation"  # Default to correlation if invalid
                
                validated_linkages.append(linkage)
            
            return validated_linkages
        except json.JSONDecodeError:
            # If the response is not valid JSON, try to extract structured data from text
            return self._fallback_response_parser(llm_response)
    
    def _fallback_response_parser(self, text: str) -> List[Dict[str, Any]]:
        """
        Fallback parser for when the LLM's response is not valid JSON
        
        Args:
            text: Raw text response from the LLM
            
        Returns:
            List of linkage objects (may be empty if parsing fails)
        """
        # Simple fallback parsing - look for patterns in the text
        linkages = []
        
        # Split into sections that might contain linkages
        sections = text.split("\n\n")
        
        for section in sections:
            try:
                lines = section.strip().split("\n")
                
                # Look for lines that might contain the required fields
                linkage = {}
                
                for line in lines:
                    line = line.strip()
                    
                    if line.startswith("subjective_ref_id") or line.startswith('"subjective_ref_id"'):
                        linkage["subjective_ref_id"] = line.split(":", 1)[1].strip().strip('",')
                    elif line.startswith("objective_ref_id") or line.startswith('"objective_ref_id"'):
                        linkage["objective_ref_id"] = line.split(":", 1)[1].strip().strip('",')
                    elif line.startswith("linkage_type") or line.startswith('"linkage_type"'):
                        linkage_type = line.split(":", 1)[1].strip().strip('",').lower()
                        if linkage_type in ["correlation", "contradiction", "emerging_theme"]:
                            linkage["linkage_type"] = linkage_type
                        else:
                            linkage["linkage_type"] = "correlation"
                    elif line.startswith("ai_summary") or line.startswith('"ai_summary'):
                        linkage["ai_summary_of_linkage"] = line.split(":", 1)[1].strip().strip('",')
                    elif line.startswith("ai_prompt") or line.startswith('"ai_prompt'):
                        linkage["ai_prompt_for_ceo"] = line.split(":", 1)[1].strip().strip('",')
                
                # Check if we found all required fields
                if all(key in linkage for key in ["subjective_ref_id", "objective_ref_id", "linkage_type", 
                                                  "ai_summary_of_linkage", "ai_prompt_for_ceo"]):
                    linkages.append(linkage)
            except Exception:
                # Skip this section if parsing fails
                continue
        
        return linkages