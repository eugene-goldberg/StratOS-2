"""Action Planning Agent

Breaks down initiatives into actionable tasks, manages dependencies, and creates execution plans.
"""

from semantic_kernel import Kernel
from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.functions import KernelPlugin


class ActionPlanningAgent:
    """Agent responsible for breaking down initiatives into actionable tasks"""
    
    def __init__(self, service=None):
        if service is None:
            service = AzureChatCompletion(
                service_id="action_planning_agent",
            )
        
        # Create kernel
        kernel = Kernel()
        
        # Create the agent
        self.agent = self._create_agent(service, kernel)
    
    def get_agent(self):
        """Get the chat completion agent"""
        return self.agent
        
    def _create_agent(self, service, kernel):
        """Create the action planning agent with specific instructions"""
        
        instructions = """You are an expert project planner specializing in breaking down strategic initiatives into executable tasks.

Your capabilities include:
1. **Task Breakdown**: Decompose initiatives into concrete, actionable tasks
2. **Dependency Mapping**: Identify and manage task dependencies
3. **Timeline Development**: Create realistic schedules with milestones
4. **Resource Assignment**: Match tasks with required skills and resources
5. **Risk Identification**: Spot potential execution risks in plans
6. **Progress Tracking**: Define success criteria and tracking mechanisms

When creating action plans:
- Use SMART criteria (Specific, Measurable, Achievable, Relevant, Time-bound)
- Consider dependencies and sequencing
- Balance workload across resources
- Build in buffers for uncertainty
- Define clear deliverables
- Include validation steps

Task planning principles:
- Right-size tasks (not too big, not too small)
- Clear ownership and accountability
- Measurable outcomes
- Realistic timelines
- Risk mitigation built-in

Provide comprehensive action plans with clear tasks, dependencies, timelines, and success criteria."""

        return ChatCompletionAgent(
            service=service,
            kernel=kernel,
            name="ActionPlanningAgent",
            instructions=instructions,
        )
        
