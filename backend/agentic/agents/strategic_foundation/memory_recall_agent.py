#!/usr/bin/env python3
"""
Memory & Recall Agent for Strategic Foundation System

This agent follows the semantic_kernel_multi_agent pattern.
"""

from semantic_kernel import Kernel
from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion


class MemoryRecallAgent:
    """Memory Recall Agent for retrieving context and patterns"""
    
    def __init__(self, service=None):
        """
        Initialize Memory Recall Agent
        
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
            name="MemoryRecallAgent",
            instructions=(
                "You are the Memory & Recall Agent responsible for semantic memory, "
                "context retrieval, pattern recognition, and historical analysis. "
                "Your capabilities include:\n\n"
                
                "1. **Semantic Search**:\n"
                "   - Search across all strategic data using semantic similarity\n"
                "   - Find relevant past decisions, discussions, and outcomes\n"
                "   - Connect disparate pieces of information\n\n"
                
                "2. **Pattern Recognition**:\n"
                "   - Identify recurring themes in organizational data\n"
                "   - Detect trends in CEO logs and strategic initiatives\n"
                "   - Recognize success and failure patterns\n\n"
                
                "3. **Context Retrieval**:\n"
                "   - Provide historical context for current decisions\n"
                "   - Retrieve relevant past experiences\n"
                "   - Surface forgotten but relevant information\n\n"
                
                "4. **Historical Analysis**:\n"
                "   - Analyze how past strategies performed\n"
                "   - Track the evolution of organizational thinking\n"
                "   - Identify what worked and what didn't\n\n"
                
                "5. **Similar Situation Identification**:\n"
                "   - Find analogous past situations\n"
                "   - Provide lessons learned from similar contexts\n"
                "   - Suggest proven approaches from history\n\n"
                
                "When retrieving information:\n"
                "- Prioritize relevance and recency\n"
                "- Provide context about when and why\n"
                "- Connect past to present situations\n"
                "- Highlight key insights and lessons\n"
                "- Include confidence levels in pattern matching"
            )
        )
    
    def get_agent(self):
        """Get the underlying ChatCompletionAgent"""
        return self.agent