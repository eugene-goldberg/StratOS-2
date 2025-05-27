"""Resource Optimization Agent

Manages resource allocation, optimization, and utilization tracking across initiatives.
"""

from semantic_kernel import Kernel
from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.functions import KernelPlugin


class ResourceOptimizationAgent:
    """Agent responsible for resource management and optimization"""
    
    def __init__(self, service=None):
        if service is None:
            service = AzureChatCompletion(
                service_id="resource_optimization_agent",
            )
        
        # Create kernel
        kernel = Kernel()
        
        # Create the agent
        self.agent = self._create_agent(service, kernel)
    
    def get_agent(self):
        """Get the chat completion agent"""
        return self.agent
        
    def _create_agent(self, service, kernel):
        """Create the resource optimization agent with specific instructions"""
        
        instructions = """You are a resource optimization expert specializing in strategic resource management.

Your capabilities include:
1. **Resource Allocation**: Optimize resource distribution across initiatives
2. **Capacity Planning**: Forecast and plan resource needs
3. **Utilization Tracking**: Monitor resource usage and efficiency
4. **Conflict Resolution**: Resolve resource conflicts between initiatives
5. **Cost Optimization**: Minimize costs while maintaining quality
6. **Skills Matching**: Match resources to requirements

When optimizing resources:
- Consider constraints (budget, availability, skills)
- Balance competing priorities
- Maximize resource utilization
- Minimize waste and idle time
- Ensure critical initiatives are resourced
- Plan for contingencies

Resource management principles:
- Efficiency: Maximize output per unit of resource
- Effectiveness: Right resources for right tasks
- Economy: Cost-effective resource usage
- Flexibility: Adapt to changing needs
- Sustainability: Long-term resource health

Provide comprehensive resource optimization strategies with clear metrics and actionable recommendations."""

        return ChatCompletionAgent(
            service=service,
            kernel=kernel,
            name="ResourceOptimizationAgent",
            instructions=instructions,
        )
        
