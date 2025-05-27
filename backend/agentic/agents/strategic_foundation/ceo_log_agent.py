#!/usr/bin/env python3
"""
CEO Log Agent - Handles CEO log entries and related operations.

This agent follows the semantic_kernel_multi_agent pattern.
"""

from semantic_kernel import Kernel
from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion


class CEOLogAgent:
    """CEO Log Agent for handling subjective inputs"""
    
    def __init__(self, service=None):
        """
        Initialize CEO Log Agent
        
        Args:
            service: An optional pre-configured service
        """
        if service is None:
            # Create a new service if none is provided
            service = AzureChatCompletion()
        
        # Create a kernel with filters for debugging
        kernel = Kernel()
        
        self.agent = ChatCompletionAgent(
            service=service,
            kernel=kernel,
            name="CEOLogAgent",
            instructions=(
                "You are the CEO Log Agent responsible for processing executive log entries. "
                "Your capabilities include:\n"
                "- Processing voice transcriptions\n"
                "- Generating relevant tags for entries\n"
                "- Creating concise summaries\n"
                "- Extracting strategic insights\n"
                "- Maintaining context across entries\n\n"
                
                "When processing entries, focus on:\n"
                "1. Strategic implications\n"
                "2. Key decisions or concerns\n"
                "3. Action items or follow-ups\n"
                "4. Emotional tone and urgency\n"
                "5. Connections to organizational goals\n\n"
                
                "For tag generation:\n"
                "- Use consistent naming conventions\n"
                "- Include strategic themes (growth, risk, innovation)\n"
                "- Add functional areas (sales, product, operations)\n"
                "- Mark priority levels when evident\n\n"
                
                "For summaries:\n"
                "- Keep them under 100 words\n"
                "- Highlight the main point first\n"
                "- Include key metrics if mentioned\n"
                "- Preserve the CEO's voice and intent\n\n"
                
                "For insights:\n"
                "- Connect to broader patterns\n"
                "- Identify emerging themes\n"
                "- Suggest potential actions\n"
                "- Flag risks or opportunities"
            )
        )
    
    def get_agent(self):
        """Get the underlying ChatCompletionAgent"""
        return self.agent