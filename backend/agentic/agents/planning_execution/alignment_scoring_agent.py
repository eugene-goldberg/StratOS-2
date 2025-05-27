"""Alignment Scoring Agent

Evaluates strategic alignment between initiatives, goals, and North Star elements.
"""

from semantic_kernel import Kernel
from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.functions import KernelPlugin


class AlignmentScoringAgent:
    """Agent responsible for scoring and validating strategic alignment"""
    
    def __init__(self, service=None):
        if service is None:
            service = AzureChatCompletion(
                service_id="alignment_scoring_agent",
            )
        
        # Create kernel
        kernel = Kernel()
        
        # Create the agent
        self.agent = self._create_agent(service, kernel)
    
    def get_agent(self):
        """Get the chat completion agent"""
        return self.agent
        
    def _create_agent(self, service, kernel):
        """Create the alignment scoring agent with specific instructions"""
        
        instructions = """You are a strategic alignment expert specializing in evaluating organizational coherence.

Your capabilities include:
1. **Alignment Scoring**: Evaluate how well initiatives align with strategic objectives
2. **Gap Analysis**: Identify misalignments and strategic gaps
3. **Impact Assessment**: Measure potential impact on organizational goals
4. **Recommendation Generation**: Suggest improvements for better alignment
5. **Portfolio Optimization**: Balance initiative portfolio for maximum strategic value
6. **Risk Evaluation**: Assess alignment-related risks

When scoring alignment:
- Consider multiple dimensions (strategic, operational, market, financial)
- Use quantitative and qualitative factors
- Provide actionable feedback
- Highlight both strengths and gaps
- Consider interdependencies
- Think long-term sustainability

Scoring methodology:
- 0-100 scale for overall alignment
- Multi-dimensional assessment
- Evidence-based scoring
- Clear rationale for scores
- Improvement pathways

Provide comprehensive alignment analysis with actionable insights and recommendations."""

        return ChatCompletionAgent(
            service=service,
            kernel=kernel,
            name="AlignmentScoringAgent",
            instructions=instructions,
        )
        
