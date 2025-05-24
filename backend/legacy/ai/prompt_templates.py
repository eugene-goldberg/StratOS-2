"""
Centralized AI prompt templates module for StratOS.

This module provides a structured way to define, manage and use AI prompt templates
across the StratOS application. It supports dynamic context injection and few-shot
examples to improve the quality and consistency of AI-generated responses.

Each template is defined with:
1. A template string with placeholders for dynamic content
2. A set of few-shot examples showing expected input/output pairs
3. Optional metadata like description, version, etc.

Usage:
    from backend.ai.prompt_templates import render_template, TEMPLATES
    
    # Basic usage
    prompt = render_template(
        template_name="generate_tows",
        context={"input": "My SWOT analysis..."}
    )
    
    # Advanced usage with dynamic context
    prompt = render_template(
        template_name="generate_swot_quadrant",
        context={
            "topic": "Market Expansion",
            "company_name": "Acme Corp",
            "category": "strength",
            "strengths": ["Strong R&D team", "Patent portfolio"],
            "subjective_data": "Recent CEO log entries...",
            "objective_data": "Q3 KPIs show 15% growth in..."
        },
        include_examples=True  # Include few-shot examples
    )
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Union

# Define template structure with support for examples
class PromptTemplate:
    def __init__(
        self, 
        name: str,
        template: str,
        description: str = "",
        examples: List[Dict[str, str]] = None,
        version: str = "1.0"
    ):
        self.name = name
        self.template = template
        self.description = description
        self.examples = examples or []
        self.version = version
    
    def render(
        self, 
        context: Dict[str, Any], 
        include_examples: bool = False
    ) -> str:
        """
        Render the template with the provided context.
        
        Args:
            context: Dictionary containing values to be injected into the template
            include_examples: Whether to include few-shot examples in the prompt
            
        Returns:
            The rendered prompt string
        """
        # Start with the base template
        prompt = self.template
        
        # Replace placeholders using the {{$name}} syntax
        for key, value in context.items():
            placeholder = f"{{{{${key}}}}}"
            if placeholder in prompt:
                if isinstance(value, list):
                    # If value is a list, format it appropriately
                    formatted_value = "; ".join(str(item) for item in value)
                    prompt = prompt.replace(placeholder, formatted_value)
                else:
                    # Otherwise use the value directly
                    prompt = prompt.replace(placeholder, str(value))
        
        # Add examples if requested
        if include_examples and self.examples:
            examples_text = "\n\nHere are some examples to guide your response:\n\n"
            
            for i, example in enumerate(self.examples, 1):
                examples_text += f"Example {i}:\n"
                
                # Add input
                if "input" in example:
                    examples_text += f"Input:\n{example['input']}\n\n"
                
                # Add context if present
                if "context" in example:
                    examples_text += f"Context:\n{example['context']}\n\n"
                
                # Add output
                if "output" in example:
                    examples_text += f"Output:\n{example['output']}\n\n"
                
                examples_text += "---\n\n"
            
            # Insert examples before the final formatting instructions if they exist
            # Look for common markers of formatting instructions
            formatting_markers = [
                "Format your response as",
                "Your response should be formatted",
                "Please format your response"
            ]
            
            for marker in formatting_markers:
                if marker in prompt:
                    parts = prompt.split(marker, 1)
                    prompt = parts[0] + examples_text + marker + parts[1]
                    break
            else:
                # If no marker found, just append examples at the end
                prompt += examples_text
                
        return prompt


# Function to read prompt template files
def _read_template_file(file_path: Union[str, Path]) -> str:
    """Read a prompt template from a file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()


# Helper function to render templates
def render_template(
    template_name: str, 
    context: Dict[str, Any], 
    include_examples: bool = False
) -> str:
    """
    Render an AI prompt template with the provided context.
    
    Args:
        template_name: The name of the template to render
        context: Dictionary containing values to be injected into the template
        include_examples: Whether to include few-shot examples in the prompt
        
    Returns:
        The rendered prompt string
    """
    if template_name not in TEMPLATES:
        raise ValueError(f"Template '{template_name}' not found")
    
    template = TEMPLATES[template_name]
    return template.render(context, include_examples)


# Define few-shot examples for TOWS strategies
TOWS_EXAMPLES = [
    {
        "input": """STRENGTHS:
1. Experienced leadership team with industry expertise
2. Strong brand recognition in the market
3. Proprietary technology that increases efficiency

WEAKNESSES:
1. Limited marketing budget compared to competitors
2. Outdated IT infrastructure causing operational delays
3. High employee turnover in key departments

OPPORTUNITIES:
1. Growing market demand for eco-friendly products
2. Potential for international expansion
3. New digital marketing channels becoming cost-effective

THREATS:
1. New competitors entering the market with lower prices
2. Changing regulations that may increase compliance costs
3. Economic downturn affecting customer spending""",
        "output": """## S-O Strategies (Strengths-Opportunities)
1. Global Brand Expansion: Leverage the company's strong brand recognition to accelerate international expansion into growing markets, particularly those with increasing eco-friendly product demand.
2. Technology-Driven Green Products: Utilize proprietary efficiency technology to develop and market new eco-friendly product lines that align with growing market trends.
3. Expert-Led Digital Transformation: Deploy the experienced leadership team to drive adoption of new cost-effective digital marketing channels, maximizing ROI through their industry expertise.

## W-O Strategies (Weaknesses-Opportunities)
1. Budget-Friendly Digital Marketing: Overcome the limited marketing budget by strategically investing in emerging cost-effective digital marketing channels with targeted campaigns.
2. IT Modernization Initiative: Address outdated IT infrastructure by implementing new systems specifically designed to support international expansion and improve operational efficiency.
3. Retention Through Green Innovation: Reduce employee turnover by engaging key departments in exciting eco-friendly product initiatives, creating purpose-driven work opportunities.

## S-T Strategies (Strengths-Threats)
1. Premium Brand Positioning: Utilize strong brand recognition to maintain premium market position and avoid direct price competition with new low-cost market entrants.
2. Regulatory Navigation Task Force: Leverage the experienced leadership team's knowledge to proactively adapt to changing regulations, turning compliance into a competitive advantage.
3. Technology-Driven Cost Efficiency: Deploy proprietary technology to increase operational efficiency, creating buffer against economic downturns and maintaining healthy margins.

## W-T Strategies (Weaknesses-Threats)
1. Targeted IT Investment Plan: Prioritize upgrading IT infrastructure components that directly impact competitive capabilities and regulatory compliance to maximize limited resources.
2. Cross-Training Excellence Program: Implement comprehensive training programs to reduce dependency on single employees and decrease turnover while improving adaptability to market changes.
3. Lean Marketing Methodology: Develop a resource-efficient marketing strategy focused on customer retention and targeted acquisition to maximize limited budget during economic uncertainty."""
    }
]

# Define few-shot examples for SWOT quadrant prompt
SWOT_EXAMPLES = [
    {
        "context": {
            "topic": "Market Expansion",
            "company_name": "TechNova",
            "category": "opportunity",
            "strengths": ["Strong R&D capabilities", "Robust financial position", "Loyal customer base"],
            "weaknesses": ["Limited international presence", "Slow product development cycle"],
            "opportunities": ["Growing demand in Asian markets", "Potential strategic partnerships"],
            "threats": ["Increasing competition", "Rapidly changing technology landscape"],
            "subjective_data": "Our CEO recently visited Singapore and noticed significant interest in our products, especially in the financial technology sector.",
            "objective_data": "Q2 sales inquiries from Asian markets increased 45% year-over-year."
        },
        "output": """What specific market segments in Asia show the highest growth potential for our specific product offerings?
Which potential strategic partners in Asian markets could help accelerate our market entry and reduce cultural barriers?
How might we leverage our strong R&D capabilities to create market-specific adaptations for Asian consumers?
What regulatory opportunities exist in emerging Asian markets that could give us an advantage over established competitors?
How could we capitalize on our financial strength to make strategic acquisitions of local companies with established distribution networks?
What new business models might be viable in Asian markets that differ from our current approach?
Which of our current customers have operations in Asia that could serve as reference customers or entry points?"""
    }
]

# Define few-shot examples for strategic initiative generation
INITIATIVE_EXAMPLES = [
    {
        "context": {
            "strategic_goal": "Increase market share in the enterprise segment by 15% within the next fiscal year.",
            "company_why": "Purpose: To empower businesses with technology that enhances human potential.\nVision: To be the trusted partner in business transformation through innovative technology solutions.\nValues: Excellence, Customer-Centricity, Innovation, Integrity, Collaboration.",
            "insights": "SWOT Analysis highlights:\n- Strength: Strong technical support team with 98% satisfaction rating\n- Weakness: Limited enterprise-specific product features\n- Opportunity: Growing demand for integrated security solutions\n- Threat: Increasing competition from specialized providers\n\nRecent customer feedback indicates enterprise clients value seamless integration and customization capabilities above other features."
        },
        "output": """## Initiative Title
Enterprise Solution Integration Platform (ESIP)

## Description
The Enterprise Solution Integration Platform initiative will develop a comprehensive framework that enables seamless integration between our core products and enterprise clients' existing systems, with enhanced security features and customization capabilities. This initiative directly addresses our market share goals by delivering the integration capabilities enterprise customers demand while leveraging our technical support excellence and responding to security solution opportunities.

## Type
Strategic

## Alignment with WHY
This initiative embodies our purpose of empowering businesses with technology by creating solutions that respect and enhance their existing infrastructure investments. It reflects our vision of becoming a trusted transformation partner by solving key integration challenges. The customization aspects demonstrate our customer-centric values, while the security enhancements showcase our commitment to excellence and innovation.

## Key Actions
1. Conduct in-depth research with current enterprise customers to document integration pain points and requirements
2. Develop a modular integration architecture with standardized APIs for core enterprise systems
3. Create a security enhancement layer addressing enterprise-specific compliance requirements
4. Build a customization toolkit enabling technical teams to tailor solutions without code changes
5. Establish a dedicated enterprise integration consulting and support team

## Key Resources Needed
- Development Team: 3 senior developers, 2 integration specialists, 1 security expert
- Customer Research: Budget for interviews and workshops with 15-20 enterprise customers
- Technology: API management platform, security testing infrastructure
- Training: Enterprise solution architecture certification for support team

## Timeline
- Start: Q1 next fiscal year
- Duration: 9 months (3 months for research and design, 4 months for development, 2 months for testing and rollout)

## Success Metrics
1. Increase in enterprise segment market share by 15% by fiscal year end
2. 40% reduction in enterprise client onboarding time
3. 90%+ satisfaction rating for integration capabilities from enterprise clients

## Potential Risks
1. Integration complexity exceeds estimates: Mitigate by starting with modular approach and prioritizing most common integration scenarios
2. Security compliance challenges: Mitigate by involving security team early and establishing compliance review checkpoints
3. Resource allocation conflicts: Mitigate by securing dedicated team members not shared with other major initiatives"""
    }
]

# Define few-shot examples for insight generation
INSIGHTS_EXAMPLES = [
    {
        "input": """Today I had a meeting with our top three enterprise clients to discuss their experience with our latest product release. They all mentioned they appreciate the new user interface and improved performance, but expressed frustration with the limited customization options. Two of them specifically asked about API access to integrate our product with their internal systems. The banking client was particularly concerned about compliance features that seem to be lacking. On a positive note, our customer success team received praise from all three for their responsiveness and technical knowledge. I'm wondering if we should prioritize API development and compliance features in our next release cycle instead of the mobile app we had planned.""",
        "output": """The request for API access indicates a shift toward deeper integration that could differentiate us from competitors offering standalone solutions.
Enterprise clients' emphasis on compliance suggests an opportunity to develop a specialized compliance module as a premium offering.
Customer success team's strong performance represents a competitive advantage that could be marketed more prominently to enterprise prospects.
Postponing the mobile app in favor of integration and compliance features may better align with revenue opportunities in the enterprise segment."""
    }
]

# Load existing templates from text files
SKILLS_DIR = Path(__file__).parent / 'skills'

# Define the templates with examples
TEMPLATES = {
    "generate_tows": PromptTemplate(
        name="generate_tows",
        template=_read_template_file(SKILLS_DIR / 'analysis' / 'GenerateTOWS.prompt.txt'),
        description="Generates TOWS strategies based on a SWOT analysis",
        examples=TOWS_EXAMPLES,
        version="1.0"
    ),
    
    "generate_initiative": PromptTemplate(
        name="generate_initiative",
        template=_read_template_file(SKILLS_DIR / 'planning' / 'GenerateInitiative.prompt.txt'),
        description="Generates a strategic initiative based on goals and insights",
        examples=INITIATIVE_EXAMPLES,
        version="1.0"
    ),
    
    "generate_insights": PromptTemplate(
        name="generate_insights",
        template=_read_template_file(SKILLS_DIR / 'subjective_log' / 'GenerateInsights.prompt.txt'),
        description="Generates strategic insights from CEO log entries",
        examples=INSIGHTS_EXAMPLES,
        version="1.0"
    ),
    
    # Templates defined directly in the contextual_prompt_generation_skill.py file
    "generate_swot_quadrant": PromptTemplate(
        name="generate_swot_quadrant",
        template="""You are an expert strategic advisor helping a CEO conduct a SWOT analysis for {{$company_name}}.
        
Topic of analysis: {{$topic}}
Current quadrant: {{$category_name}}

Your task is to generate 5-7 thought-provoking guiding questions to help the CEO identify {{$category_name}}s for {{$company_name}} regarding {{$topic}}.

{% if swot_context %}
Current SWOT Analysis state:
{{$swot_context}}
{% endif %}

{% if subjective_data %}
Relevant notes from CEO's Log:
{{$subjective_data}}
{% endif %}

{% if objective_data %}
Relevant business metrics and data:
{{$objective_data}}
{% endif %}

{% if category == "strength" %}
Focus on INTERNAL, CURRENT POSITIVE factors that give the company an advantage:
- What does the company do exceptionally well?
- What unique resources, assets, or capabilities does the company possess?
- What advantages does the company have over competitors?
- What do customers or partners see as the company's strengths?
{% elif category == "weakness" %}
Focus on INTERNAL, CURRENT NEGATIVE factors that place the company at a disadvantage:
- What areas could the company improve in?
- What necessary skills, resources, or technologies is the company lacking?
- What do competitors do better?
- What processes or activities might be limiting performance?
{% elif category == "opportunity" %}
Focus on EXTERNAL, FUTURE POSITIVE factors that the company could capitalize on:
- What market trends or conditions could benefit the company?
- What changes in technology, policy, or society present new openings?
- What gaps exist in the market that the company could fill?
- What moves could open new markets or customer segments?
{% elif category == "threat" %}
Focus on EXTERNAL, FUTURE NEGATIVE factors that could harm the company's position:
- What obstacles or challenges does the company face?
- What are competitors doing that could impact the company?
- What changing regulations or standards might cause problems?
- What negative market or economic trends could affect the company?
{% endif %}

Based on all this information, generate 5-7 specific, thought-provoking questions to help the CEO identify {{$category_name}}s for {{$company_name}} regarding {{$topic}}.

Each question should:
1. Be specific to {{$company_name}} and {{$topic}}
2. Build on existing analysis data where relevant
3. Incorporate insights from the CEO's notes and business metrics when applicable
4. Help uncover {{$category_name}}s that might not be immediately obvious

Format your response as a list of questions, one per line, without numbering or bullet points.
""",
        description="Generates contextual prompts for SWOT analysis quadrants",
        examples=SWOT_EXAMPLES,
        version="1.0"
    ),
    
    "generate_tows_cell": PromptTemplate(
        name="generate_tows_cell",
        template="""You are an expert strategic advisor helping a CEO develop a TOWS matrix based on their SWOT analysis for {{$company_name}}.

Topic of analysis: {{$topic}}
Current TOWS cell: {{$cell_type}} - {{$cell_description}}

Your task is to generate 5-7 thought-provoking guiding questions to help the CEO develop strategic actions for the {{$cell_type}} cell of their TOWS matrix.

SWOT Analysis data:
STRENGTHS: {{$strengths}}
WEAKNESSES: {{$weaknesses}}
OPPORTUNITIES: {{$opportunities}}
THREATS: {{$threats}}

{% if cell_strategies %}
Existing {{$cell_type}} strategies:
{% for strategy in cell_strategies %}
{{$loop.index}}. {{strategy.text}}
{% endfor %}
{% endif %}

{% if cell_type == "SO" %}
For the SO cell (Strengths-Opportunities), I need questions that help the CEO identify strategies that use {{$company_name}}'s strengths to capitalize on external opportunities.

Focus on how each strength can be leveraged to take advantage of specific opportunities:
- How can {{$company_name}} use its internal advantages to exploit external possibilities?
- What capabilities can be directed toward emerging opportunities?
- How might existing strengths be enhanced to capitalize on market openings?
{% elif cell_type == "WO" %}
For the WO cell (Weaknesses-Opportunities), I need questions that help the CEO identify strategies to overcome {{$company_name}}'s weaknesses by taking advantage of external opportunities.

Focus on how opportunities might help address or compensate for weaknesses:
- How can {{$company_name}} use external opportunities to improve internal weaknesses?
- What market trends or conditions might provide resources or approaches to overcome limitations?
- How can emerging opportunities help transform weaknesses into strengths?
{% elif cell_type == "ST" %}
For the ST cell (Strengths-Threats), I need questions that help the CEO identify strategies that use {{$company_name}}'s strengths to mitigate external threats.

Focus on how strengths can be used as shields or counters against threats:
- How can {{$company_name}} leverage its internal advantages to reduce vulnerability to external threats?
- What strengths can be deployed to neutralize or minimize specific threats?
- How might existing capabilities be repurposed to address emerging challenges?
{% elif cell_type == "WT" %}
For the WT cell (Weaknesses-Threats), I need questions that help the CEO identify strategies to minimize {{$company_name}}'s weaknesses and avoid external threats.

Focus on defensive approaches that address vulnerabilities and risks:
- How can {{$company_name}} minimize exposure of weaknesses to threats?
- What defensive measures might reduce the combined impact of internal limitations and external challenges?
- What partnerships or restructuring could help address both weaknesses and threats simultaneously?
{% endif %}

Based on the specific {{$primary_component}} and {{$secondary_component}} from the SWOT analysis, generate 5-7 thought-provoking questions that will help the CEO develop strategic actions for the {{$cell_type}} cell.

Each question should:
1. Connect specific {{$primary_component}} with specific {{$secondary_component}} where possible
2. Be tailored to {{$company_name}} and {{$topic}}
3. Build on existing {{$cell_type}} strategies where relevant
4. Help uncover strategic approaches that might not be immediately obvious

Format your response as a list of questions, one per line, without numbering or bullet points.
""",
        description="Generates contextual prompts for TOWS matrix cells",
        examples=[],  # Will add examples later
        version="1.0"
    )
}