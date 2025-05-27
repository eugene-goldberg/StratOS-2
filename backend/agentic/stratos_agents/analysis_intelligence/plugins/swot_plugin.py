"""SWOT Analysis Plugin

Provides SWOT and TOWS analysis capabilities using Semantic Kernel functions.
"""

import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from uuid import uuid4

from semantic_kernel.functions import kernel_function
from semantic_kernel.kernel_pydantic import KernelBaseModel


class SwotPlugin(KernelBaseModel):
    """Plugin for SWOT analysis and TOWS strategy generation"""
    
    @kernel_function(
        description="Generate SWOT analysis items from input data",
        name="GenerateSWOT"
    )
    async def generate_swot(
        self,
        topic: str,
        subjective_data: str = "",
        objective_data: str = "",
        user_id: str = None
    ) -> str:
        """Generate SWOT analysis items based on provided data"""
        
        # Combine inputs for analysis
        combined_input = f"""
Topic: {topic}

Subjective Insights:
{subjective_data if subjective_data else "No subjective data provided"}

Objective Data:
{objective_data if objective_data else "No objective data provided"}

Instructions:
1. Analyze the provided information to identify strategic factors
2. Categorize each factor as Strength, Weakness, Opportunity, or Threat
3. Ensure items are specific, actionable, and relevant to the topic
4. Provide impact scores (1-10) and certainty scores (1-10) for each item
5. Reference source data where applicable
"""
        
        # This would normally call the LLM with the prompt template
        # For now, returning a structured example
        swot_items = {
            "items": [
                {
                    "id": str(uuid4()),
                    "category": "strength",
                    "content": "Strong customer loyalty with 85% retention rate",
                    "source": "objective",
                    "source_references": [{"type": "metric", "value": "85% retention"}],
                    "impact_score": 8,
                    "certainty_score": 9,
                    "created_at": datetime.utcnow().isoformat()
                },
                {
                    "id": str(uuid4()),
                    "category": "weakness",
                    "content": "Limited digital infrastructure compared to competitors",
                    "source": "combined",
                    "source_references": [{"type": "insight", "value": "CEO feedback on tech gaps"}],
                    "impact_score": 7,
                    "certainty_score": 8,
                    "created_at": datetime.utcnow().isoformat()
                },
                {
                    "id": str(uuid4()),
                    "category": "opportunity",
                    "content": "Emerging market demand for sustainable products",
                    "source": "objective",
                    "source_references": [{"type": "market_data", "value": "30% YoY growth"}],
                    "impact_score": 9,
                    "certainty_score": 7,
                    "created_at": datetime.utcnow().isoformat()
                },
                {
                    "id": str(uuid4()),
                    "category": "threat",
                    "content": "New regulations may increase operational costs by 15%",
                    "source": "objective",
                    "source_references": [{"type": "regulatory", "value": "Bill XYZ pending"}],
                    "impact_score": 6,
                    "certainty_score": 8,
                    "created_at": datetime.utcnow().isoformat()
                }
            ],
            "metadata": {
                "topic": topic,
                "generated_at": datetime.utcnow().isoformat(),
                "data_sources": {
                    "subjective": bool(subjective_data),
                    "objective": bool(objective_data)
                }
            }
        }
        
        return json.dumps(swot_items)
    
    @kernel_function(
        description="Generate TOWS strategies from SWOT analysis",
        name="GenerateTOWS"
    )
    async def generate_tows(
        self,
        strengths: List[str],
        weaknesses: List[str],
        opportunities: List[str],
        threats: List[str]
    ) -> str:
        """Generate TOWS matrix strategies"""
        
        # Format SWOT items for strategy generation
        swot_input = f"""
Strengths:
{chr(10).join(f"- {s}" for s in strengths)}

Weaknesses:
{chr(10).join(f"- {w}" for w in weaknesses)}

Opportunities:
{chr(10).join(f"- {o}" for o in opportunities)}

Threats:
{chr(10).join(f"- {t}" for t in threats)}

Generate strategic options using TOWS matrix:
1. SO Strategies (Maxi-Maxi): Use strengths to maximize opportunities
2. WO Strategies (Mini-Maxi): Minimize weaknesses by taking advantage of opportunities  
3. ST Strategies (Maxi-Mini): Use strengths to minimize threats
4. WT Strategies (Mini-Mini): Minimize weaknesses and avoid threats
"""
        
        # This would normally call the LLM
        # For now, returning example strategies
        tows_strategies = {
            "strategies": {
                "SO": [
                    {
                        "strategy": "Leverage strong customer loyalty to capture sustainable product market",
                        "strengths_used": ["Strong customer loyalty"],
                        "opportunities_captured": ["Emerging market demand for sustainable products"],
                        "priority": "high"
                    }
                ],
                "WO": [
                    {
                        "strategy": "Partner with tech companies to rapidly build digital infrastructure",
                        "weaknesses_addressed": ["Limited digital infrastructure"],
                        "opportunities_captured": ["Digital transformation trends"],
                        "priority": "high"
                    }
                ],
                "ST": [
                    {
                        "strategy": "Use customer relationships to advocate for favorable regulations",
                        "strengths_used": ["Strong customer loyalty"],
                        "threats_mitigated": ["New regulations"],
                        "priority": "medium"
                    }
                ],
                "WT": [
                    {
                        "strategy": "Automate processes to offset regulatory cost increases",
                        "weaknesses_addressed": ["Limited digital infrastructure"],
                        "threats_mitigated": ["Increased operational costs"],
                        "priority": "medium"
                    }
                ]
            },
            "metadata": {
                "generated_at": datetime.utcnow().isoformat(),
                "total_strategies": 4
            }
        }
        
        return json.dumps(tows_strategies)
    
    @kernel_function(
        description="Score SWOT items for impact and certainty",
        name="ScoreItems"
    )
    async def score_items(
        self,
        items: List[Dict[str, Any]],
        scoring_criteria: Optional[str] = None
    ) -> str:
        """Score SWOT items based on impact and certainty"""
        
        if not scoring_criteria:
            scoring_criteria = """
Impact Score (1-10):
- 9-10: Game-changing impact on business
- 7-8: Significant impact on major objectives
- 5-6: Moderate impact on operations
- 3-4: Minor impact on specific areas
- 1-2: Minimal impact

Certainty Score (1-10):
- 9-10: Verified with multiple data sources
- 7-8: Strong evidence supporting
- 5-6: Reasonable confidence
- 3-4: Some uncertainty
- 1-2: Highly speculative
"""
        
        scored_items = []
        for item in items:
            # This would normally use LLM to score
            # For now, using placeholder logic
            scored_item = item.copy()
            if "impact_score" not in scored_item:
                scored_item["impact_score"] = 7  # Default moderate-high impact
            if "certainty_score" not in scored_item:
                scored_item["certainty_score"] = 8  # Default high certainty
            
            scored_items.append(scored_item)
        
        return json.dumps({
            "scored_items": scored_items,
            "scoring_criteria": scoring_criteria
        })
    
    @kernel_function(
        description="Get guidance for guided analysis sessions",
        name="GetSessionGuidance"
    )
    async def get_session_guidance(
        self,
        session_type: str,
        current_step: str,
        session_data: Dict[str, Any],
        user_input: Optional[str] = None
    ) -> str:
        """Provide contextual guidance for analysis sessions"""
        
        guidance_map = {
            "swot": {
                "introduction": """Welcome to the guided SWOT analysis session!

I'll help you systematically identify your organization's:
• Strengths (internal advantages)
• Weaknesses (internal limitations)  
• Opportunities (external possibilities)
• Threats (external challenges)

Let's start by understanding your business context. What industry or market are you analyzing?""",
                
                "context": """Great! Now let's establish the scope of our analysis.

Consider:
• Time horizon (current state vs. 1-3 years ahead)
• Geographic scope (local, regional, global)
• Business units or products to include
• Key stakeholders to consider

What specific aspect would you like to focus on?""",
                
                "strengths": """Let's identify your strengths - internal factors that give you an advantage.

Think about:
• Core competencies and unique capabilities
• Strong brand, patents, or proprietary technology
• Skilled workforce or leadership
• Financial resources or cost advantages
• Strong customer relationships

What are your organization's key strengths?""",
                
                "weaknesses": """Now let's examine weaknesses - internal factors that may disadvantage you.

Consider:
• Resource limitations (financial, human, technological)
• Gaps in capabilities or expertise
• Poor location or facilities
• Weak brand or reputation issues
• Operational inefficiencies

What internal challenges do you face?""",
                
                "opportunities": """Let's explore opportunities - external factors you could exploit.

Look for:
• Market growth or emerging customer needs
• Technological advances you could leverage
• Changes in regulations that favor you
• Weaknesses in competitors
• Strategic partnerships or alliances

What external opportunities do you see?""",
                
                "threats": """Finally, let's identify threats - external factors that could harm you.

Consider:
• New competitors or substitute products
• Changing customer preferences
• Economic downturns or market volatility
• Unfavorable regulations or policies
• Supply chain disruptions

What external threats concern you?""",
                
                "review": """Excellent work! Here's a summary of your SWOT analysis.

Next steps:
1. Review and refine each item
2. Prioritize by impact and likelihood
3. Generate TOWS strategies
4. Create action plans

Would you like to proceed with TOWS strategy generation?"""
            },
            "tows": {
                "introduction": """Welcome to TOWS strategy generation!

We'll create strategic options by combining your SWOT factors:
• SO: Use strengths to capture opportunities
• WO: Overcome weaknesses to pursue opportunities
• ST: Use strengths to avoid threats
• WT: Minimize weaknesses and avoid threats

Ready to begin?""",
                
                "swot_review": """Let me review your SWOT analysis to ensure we have a complete picture.

[Display SWOT items]

Does this accurately represent your situation? Any items to add or modify?""",
                
                "so_strategies": """SO Strategies (Strength-Opportunity): Maxi-Maxi approach

How can you use your strengths to take advantage of opportunities?
Example: "Leverage our strong R&D team to develop products for the emerging sustainable market"

What SO strategies do you see?""",
                
                "wo_strategies": """WO Strategies (Weakness-Opportunity): Mini-Maxi approach

How can you overcome weaknesses to pursue opportunities?
Example: "Partner with tech firms to build digital capabilities for e-commerce growth"

What WO strategies would work?""",
                
                "st_strategies": """ST Strategies (Strength-Threat): Maxi-Mini approach

How can you use strengths to minimize threats?
Example: "Use our financial reserves to weather economic downturns better than competitors"

What ST strategies can you develop?""",
                
                "wt_strategies": """WT Strategies (Weakness-Threat): Mini-Mini approach

How can you minimize weaknesses and avoid threats?
Example: "Outsource non-core functions to reduce costs and regulatory burden"

What WT strategies are appropriate?""",
                
                "prioritization": """Let's prioritize your strategies based on:
• Impact potential (High/Medium/Low)
• Resource requirements
• Time to implement
• Risk level

Which strategies should be your top priorities?"""
            }
        }
        
        # Get appropriate guidance
        session_type_key = session_type.replace("guided_", "")
        if session_type_key in guidance_map and current_step in guidance_map[session_type_key]:
            base_guidance = guidance_map[session_type_key][current_step]
            
            # Add contextual information based on session data
            if user_input:
                base_guidance += f"\n\nYour input: {user_input}"
            
            if session_data and current_step != "introduction":
                base_guidance += "\n\nProgress so far:"
                for key, value in session_data.items():
                    if isinstance(value, list) and value:
                        base_guidance += f"\n• {key.title()}: {len(value)} items identified"
            
            return base_guidance
        else:
            return "Let's continue with your analysis. What would you like to explore next?"
    
    @kernel_function(
        description="Create a new guided analysis session",
        name="CreateSession"  
    )
    async def create_session(
        self,
        session_type: str,
        user_id: str,
        initial_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Initialize a new guided analysis session"""
        
        session = {
            "id": str(uuid4()),
            "user_id": user_id,
            "type": session_type,
            "status": "active",
            "current_step": "introduction",
            "progress": 0,
            "data": initial_context or {},
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        return json.dumps({
            "session": session,
            "message": f"Created new {session_type} session",
            "next_action": "Get initial guidance"
        })
    
    @kernel_function(
        description="Update an existing analysis session",
        name="UpdateSession"
    )
    async def update_session(
        self,
        session_id: str,
        step_completed: str,
        data_collected: Dict[str, Any],
        next_step: str
    ) -> str:
        """Update session progress and data"""
        
        update_result = {
            "session_id": session_id,
            "step_completed": step_completed,
            "data_added": len(data_collected),
            "next_step": next_step,
            "updated_at": datetime.utcnow().isoformat()
        }
        
        return json.dumps(update_result)