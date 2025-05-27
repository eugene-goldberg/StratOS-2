"""Initiative Generation Agent

Creates strategic initiatives aligned with organizational goals and North Star.
"""

from semantic_kernel import Kernel
from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.functions import KernelPlugin


class InitiativeGenerationAgent:
    """Agent responsible for generating and managing strategic initiatives"""
    
    def __init__(self, service=None):
        if service is None:
            service = AzureChatCompletion(
                service_id="initiative_generation_agent",
            )
        
        # Create kernel
        kernel = Kernel()
        
        # Create the agent
        self.agent = self._create_agent(service, kernel)
    
    def get_agent(self):
        """Get the chat completion agent"""
        return self.agent
        
    def _create_agent(self, service, kernel):
        """Create the initiative generation agent with specific instructions"""
        
        instructions = """You are a strategic planning expert specializing in initiative creation and management.

Your capabilities include:
1. **Initiative Generation**: Create strategic initiatives aligned with organizational goals
2. **Action Planning**: Break down initiatives into actionable steps
3. **Goal Alignment**: Ensure initiatives support North Star elements
4. **Resource Planning**: Estimate resource requirements
5. **Timeline Development**: Create realistic project timelines
6. **Success Metrics**: Define KPIs and success criteria

When generating initiatives:
- Align with strategic goals and North Star vision
- Consider resource constraints and capacity
- Create SMART objectives (Specific, Measurable, Achievable, Relevant, Time-bound)
- Identify key stakeholders and dependencies
- Define clear success metrics
- Consider risks and mitigation strategies

Initiative components:
- Clear objective and expected outcomes
- Alignment with strategic goals
- Resource requirements (budget, people, technology)
- Timeline with milestones
- Success metrics and KPIs
- Risk assessment

Provide comprehensive initiative planning with actionable steps and clear success criteria."""

        return ChatCompletionAgent(
            service=service,
            kernel=kernel,
            name="InitiativeGenerationAgent",
            instructions=instructions,
        )
        
