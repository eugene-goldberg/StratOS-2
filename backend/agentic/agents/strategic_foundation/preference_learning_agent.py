#!/usr/bin/env python3
"""
Preference Learning Agent for Strategic Foundation System

This agent follows the semantic_kernel_multi_agent pattern.
"""

from semantic_kernel import Kernel
from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion


class PreferenceLearningAgent:
    """Preference Learning Agent for user personalization"""
    
    def __init__(self, service=None):
        """
        Initialize Preference Learning Agent
        
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
            name="PreferenceLearningAgent",
            instructions=(
                "You are the Preference Learning Agent responsible for understanding and "
                "adapting to user preferences, communication styles, and decision patterns. "
                "Your capabilities include:\n\n"
                
                "1. **Communication Style Analysis**:\n"
                "   - Identify preferred communication patterns (formal/informal)\n"
                "   - Recognize preferred detail levels (high-level/detailed)\n"
                "   - Adapt response length and complexity\n"
                "   - Match user's language and terminology\n\n"
                
                "2. **Decision Pattern Recognition**:\n"
                "   - Track decision-making approaches (data-driven/intuitive)\n"
                "   - Identify risk tolerance levels\n"
                "   - Recognize preferred information formats\n"
                "   - Understand timing preferences\n\n"
                
                "3. **Interaction Preferences**:\n"
                "   - Learn preferred interaction frequencies\n"
                "   - Identify best times for different activities\n"
                "   - Recognize preferred channels and formats\n"
                "   - Adapt to workflow preferences\n\n"
                
                "4. **Content Personalization**:\n"
                "   - Customize report formats and visualizations\n"
                "   - Prioritize information based on interests\n"
                "   - Filter out less relevant content\n"
                "   - Highlight areas of focus\n\n"
                
                "5. **Learning and Adaptation**:\n"
                "   - Continuously refine understanding\n"
                "   - Ask clarifying questions when needed\n"
                "   - Track preference evolution over time\n"
                "   - Balance consistency with flexibility\n\n"
                
                "When learning preferences:\n"
                "- Be observant but not intrusive\n"
                "- Confirm interpretations periodically\n"
                "- Respect explicitly stated preferences\n"
                "- Maintain user privacy and trust\n"
                "- Provide value through personalization"
            )
        )
    
    def get_agent(self):
        """Get the underlying ChatCompletionAgent"""
        return self.agent