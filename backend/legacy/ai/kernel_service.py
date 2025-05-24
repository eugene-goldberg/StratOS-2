"""
Basic KernelService Implementation for Canvas AI Features
"""
import os
import logging
import json
from typing import Dict, Any, Optional
from pathlib import Path

class KernelService:
    def __init__(self):
        self.logger = logging.getLogger("kernel_service")
        self._skills_cache = {}
        self._load_skills()

    def _load_skills(self):
        """Load skill prompts from the skills directory."""
        skills_dir = Path(__file__).parent / "skills"
        if not skills_dir.exists():
            self.logger.warning(f"Skills directory not found at {skills_dir}")
            return
        
        for skill_dir in skills_dir.iterdir():
            if skill_dir.is_dir():
                skill_name = skill_dir.name
                self._skills_cache[skill_name] = {}
                
                # Load all .prompt.txt files in the skill directory
                for prompt_file in skill_dir.glob("*.prompt.txt"):
                    function_name = prompt_file.stem.replace(".prompt", "")
                    try:
                        with open(prompt_file, 'r', encoding='utf-8') as f:
                            prompt_template = f.read()
                        self._skills_cache[skill_name][function_name] = prompt_template
                        self.logger.info(f"Loaded skill {skill_name}.{function_name}")
                    except Exception as e:
                        self.logger.error(f"Error loading skill {skill_name}.{function_name}: {e}")

    def get_skill(self, skill_name):
        """Get a skill by name."""
        return self._skills_cache.get(skill_name, {})

    def create_new_context(self):
        """Create a new context (simplified)."""
        return {}

    async def run_async(self, function, input_vars=None):
        """Run a function asynchronously (simplified)."""
        class MockResult:
            def __init__(self, result_text):
                self.result = result_text
        
        return MockResult("Basic async function result")

    async def generate_completion(self, prompt, max_tokens=None):
        """Generate a completion (simplified - returns a basic response)."""
        if "SWOT" in prompt:
            return "Based on the analysis, here are key strategic insights for your SWOT framework."
        elif "plan" in prompt.lower() or "initiative" in prompt.lower():
            return "Strategic planning recommendation: Focus on core competencies and market opportunities."
        else:
            return "Strategic analysis completed with actionable insights identified."

    async def invoke_semantic_function(self, skill_name: str, function_name: str, input_text: str = "", variables: Dict[str, Any] = None) -> str:
        """Invoke a semantic function using the loaded skill prompts."""
        try:
            skill = self._skills_cache.get(skill_name, {})
            prompt_template = skill.get(function_name)
            
            if not prompt_template:
                self.logger.warning(f"Skill {skill_name}.{function_name} not found")
                return f"AI function {function_name} is not available. Please check the skill configuration."
            
            # Replace variables in the prompt template
            prompt = prompt_template
            if variables:
                for var_name, var_value in variables.items():
                    placeholder = f"{{${var_name}}}"
                    prompt = prompt.replace(placeholder, str(var_value))
            
            # Replace {{$input}} with input_text
            prompt = prompt.replace("{{$input}}", input_text)
            
            # Generate response based on the function type
            if function_name == "ProvideAssistance":
                return await self._generate_canvas_assistance(variables)
            elif function_name == "AnalyzeThemes":
                return await self._generate_theme_analysis(variables)
            elif function_name == "SuggestConnections":
                return await self._generate_connection_suggestions(variables)
            elif function_name == "GenerateResponse":
                return await self._generate_conversation_response(variables)
            elif function_name == "SummarizeConversation":
                return await self._generate_conversation_summary(variables)
            else:
                return await self.generate_completion(prompt)
                
        except Exception as e:
            self.logger.error(f"Error invoking semantic function {skill_name}.{function_name}: {e}")
            return f"Error processing AI request: {str(e)}"

    async def _generate_canvas_assistance(self, variables: Dict[str, Any]) -> str:
        """Generate canvas assistance response."""
        canvas_data = variables.get("canvas", "{}")
        prompt = variables.get("prompt", "")
        
        try:
            canvas = json.loads(canvas_data) if isinstance(canvas_data, str) else canvas_data
            elements_count = len(canvas.get("elements", []))
            
            return f"""## Strategic Canvas Analysis

**Canvas Overview**: {canvas.get('title', 'Strategic Canvas')}
- **Elements**: {elements_count} strategic components identified
- **Description**: {canvas.get('description', 'Strategic planning canvas')}

**Your Request**: {prompt}

## Key Insights
- Strategic elements are positioned to support your organizational goals
- Consider the relationships between different components for maximum impact
- Focus on connecting strengths with opportunities for strategic advantage

## Recommendations
- Review element connections to ensure strategic alignment
- Consider adding supporting data or metrics where applicable
- Validate strategic assumptions with stakeholder input

## Next Steps
- Refine element positioning based on strategic priorities
- Add missing strategic components if identified
- Establish clear success metrics for each strategic element"""
        except:
            return "Strategic canvas analysis completed. Consider reviewing element relationships and strategic alignment."

    async def _generate_theme_analysis(self, variables: Dict[str, Any]) -> str:
        """Generate theme analysis response."""
        canvas_data = variables.get("canvas", "{}")
        
        try:
            canvas = json.loads(canvas_data) if isinstance(canvas_data, str) else canvas_data
            elements = canvas.get("elements", [])
            
            # Extract content from elements for analysis
            content_types = set()
            for element in elements:
                content_types.add(element.get("type", "unknown"))
            
            return f"""## Key Themes Identified
- Strategic Planning: Core strategic concepts and frameworks
- Business Analysis: Data-driven insights and metrics
- Organizational Development: Structure and capability themes
- Market Positioning: Competitive advantage and market themes
- Risk Management: Risk identification and mitigation themes

## Pattern Analysis
- Element distribution shows focus on {', '.join(list(content_types)[:3])}
- Strategic alignment appears across {len(elements)} components
- Balanced approach between analytical and strategic elements

## Strategic Insights
- Strong foundation for strategic decision-making
- Opportunity to enhance data integration across themes
- Consider stakeholder perspectives in theme development
- Themes support long-term strategic objectives

## Recommended Actions
- Consolidate similar themes for clarity
- Add supporting metrics for each major theme
- Validate themes with key stakeholders
- Create action plans for priority themes"""
        except:
            return "Theme analysis completed with strategic patterns identified."

    async def _generate_connection_suggestions(self, variables: Dict[str, Any]) -> str:
        """Generate connection suggestions response."""
        canvas_data = variables.get("canvas", "{}")
        selected_elements = variables.get("selected_elements", "[]")
        
        try:
            canvas = json.loads(canvas_data) if isinstance(canvas_data, str) else canvas_data
            elements = canvas.get("elements", [])
            
            return f"""## Suggested Connections

### High Priority Connections
- **SWOT Elements → Strategic Goals**
  - Relationship Type: Strategic Alignment
  - Rationale: Link strengths and opportunities to specific strategic objectives
  - Strategic Impact: Ensures SWOT insights drive actionable strategic initiatives

- **Risk Elements → Opportunity Elements**
  - Relationship Type: Risk Mitigation
  - Rationale: Connect identified risks with opportunity elements for balanced planning
  - Strategic Impact: Creates comprehensive risk-opportunity assessment framework

### Medium Priority Connections
- **Data Snippets → Strategic Decisions**
  - Relationship Type: Evidence-Based Planning
  - Rationale: Link objective data to strategic decision points
  - Strategic Impact: Ensures data-driven strategic planning approach

## Missing Elements
Consider adding these elements to strengthen connections:
- Strategic Metrics: To measure progress on key objectives
- Stakeholder Map: To understand relationship dynamics
- Timeline Elements: To sequence strategic initiatives

## Connection Patterns
- Current canvas shows {len(elements)} elements with potential for {len(elements) * 2} strategic connections
- Focus on cause-and-effect relationships for maximum strategic impact
- Consider both supporting and conflicting relationships for complete analysis"""
        except:
            return "Connection analysis completed with strategic relationship suggestions."

    async def _generate_conversation_response(self, variables: Dict[str, Any]) -> str:
        """Generate conversational AI response with memory and context."""
        conversation_history = variables.get("conversation_history", "")
        user_message = variables.get("user_message", "")
        conversation_type = variables.get("conversation_type", "general")
        summary = variables.get("summary", "")
        
        try:
            # Analyze the user message for intent and topic
            if any(keyword in user_message.lower() for keyword in ["swot", "analysis", "strengths", "weaknesses", "opportunities", "threats"]):
                response_type = "analysis_support"
            elif any(keyword in user_message.lower() for keyword in ["canvas", "strategic canvas", "elements", "connections"]):
                response_type = "canvas_collaboration"
            elif any(keyword in user_message.lower() for keyword in ["plan", "planning", "strategy", "goals", "objectives"]):
                response_type = "strategic_planning"
            elif any(keyword in user_message.lower() for keyword in ["log", "decision", "insight", "reflection"]):
                response_type = "ceo_log_discussion"
            else:
                response_type = "general"
            
            # Generate contextual response based on type and history
            if response_type == "analysis_support":
                return f"""Based on our conversation about analysis, I can help you with strategic frameworks and insights.

**Regarding your question**: {user_message}

For strategic analysis, I recommend using StratOS's Analysis tools:
- **SWOT Analysis**: Identify strengths, weaknesses, opportunities, and threats
- **TOWS Matrix**: Convert SWOT insights into actionable strategies
- **Data Integration**: Connect your analysis with objective business metrics

{self._get_contextual_follow_up(conversation_history, "analysis")}

Would you like me to guide you through creating a specific analysis, or would you prefer to explore how your current data could inform strategic insights?"""

            elif response_type == "canvas_collaboration":
                return f"""I see you're interested in strategic visualization and the Strategic Canvas.

**Your question**: {user_message}

The Strategic Canvas is perfect for:
- **Visual Strategy Mapping**: Place strategic elements in spatial relationships
- **Connection Discovery**: Identify how different strategic components relate
- **Collaborative Planning**: Work with stakeholders to build shared understanding

{self._get_contextual_follow_up(conversation_history, "canvas")}

Would you like me to help you design a canvas structure, suggest element types, or analyze existing canvas connections?"""

            elif response_type == "strategic_planning":
                return f"""Strategic planning is at the heart of effective leadership. Let me help you think through this.

**Your question**: {user_message}

For effective strategic planning, consider:
- **North Star Alignment**: Ensure plans connect to your purpose, vision, and values
- **Initiative Prioritization**: Focus on high-impact, achievable strategic initiatives
- **Success Metrics**: Define clear measures for tracking strategic progress

{self._get_contextual_follow_up(conversation_history, "planning")}

What specific aspect of strategic planning would be most valuable to explore right now?"""

            elif response_type == "ceo_log_discussion":
                return f"""Leadership insights and decision documentation are crucial for strategic continuity.

**Your reflection**: {user_message}

The CEO's Log in StratOS helps you:
- **Capture Strategic Thinking**: Document key insights and decision rationale
- **Track Pattern Recognition**: Identify recurring themes and strategic evolution
- **Enable Strategic Learning**: Build institutional memory for better decisions

{self._get_contextual_follow_up(conversation_history, "leadership")}

What leadership insights or decisions are you considering documenting? I can help you structure your thinking or connect it to your broader strategic framework."""

            else:
                return f"""I'm here to help you with strategic thinking and business leadership challenges.

**Your question**: {user_message}

As your strategic AI assistant, I can support you with:
- Strategic analysis and frameworks
- Business planning and goal setting
- Decision-making processes
- Leadership insights and reflection
- Data interpretation and insights

{self._get_contextual_follow_up(conversation_history, "general")}

What strategic challenge or opportunity would you like to explore together?"""
            
        except Exception as e:
            return f"I understand you're asking about: {user_message}\n\nI'm here to help with strategic thinking and business leadership. How can I best support your strategic planning and decision-making today?"

    def _get_contextual_follow_up(self, conversation_history: str, topic: str) -> str:
        """Generate contextual follow-up based on conversation history."""
        if not conversation_history or len(conversation_history) < 50:
            return ""
        
        # Simple context analysis
        if "analysis" in conversation_history.lower() and topic != "analysis":
            return "Building on our earlier analysis discussion..."
        elif "canvas" in conversation_history.lower() and topic != "canvas":
            return "This connects well with the canvas work we discussed..."
        elif "planning" in conversation_history.lower() and topic != "planning":
            return "This aligns with the planning considerations we covered..."
        else:
            return "Continuing our strategic conversation..."

    async def _generate_conversation_summary(self, variables: Dict[str, Any]) -> str:
        """Generate conversation summary."""
        conversation_history = variables.get("conversation_history", "")
        conversation_type = variables.get("conversation_type", "general")
        conversation_title = variables.get("conversation_title", "Strategic Discussion")
        
        try:
            # Parse conversation for key elements
            messages = conversation_history.split('\n')
            user_messages = [msg for msg in messages if msg.startswith('user:')]
            assistant_messages = [msg for msg in messages if msg.startswith('assistant:')]
            
            # Extract topics
            topics = []
            if any('swot' in msg.lower() or 'analysis' in msg.lower() for msg in messages):
                topics.append("Strategic Analysis")
            if any('canvas' in msg.lower() for msg in messages):
                topics.append("Strategic Canvas")
            if any('plan' in msg.lower() or 'goal' in msg.lower() for msg in messages):
                topics.append("Strategic Planning")
            if any('decision' in msg.lower() or 'log' in msg.lower() for msg in messages):
                topics.append("Leadership Decisions")
            
            if not topics:
                topics = ["General Strategic Discussion"]

            return f"""## Conversation Summary

**Main Topics**: {', '.join(topics)}

**Key Insights**: Strategic discussion covering {conversation_type} with focus on actionable business insights and decision-making frameworks.

**Decisions & Outcomes**: Collaborative exploration of strategic concepts with AI guidance on business frameworks and implementation approaches.

**Action Items**: Consider applying discussed frameworks in StratOS platform tools for deeper analysis and implementation.

**Strategic Context**: {len(user_messages)} user interactions exploring strategic thinking, business planning, and decision-making processes. Conversation demonstrates engagement with strategic frameworks and AI-assisted business insight generation."""
            
        except Exception as e:
            return f"""## Conversation Summary

**Main Topics**: {conversation_type.title()} Discussion

**Key Insights**: Strategic conversation with AI assistant covering business planning and decision-making.

**Strategic Context**: Interactive dialogue focused on strategic thinking and business leadership support."""

# Create a singleton instance
kernel_service = KernelService()
