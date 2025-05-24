"""Agent Group Chat implementation following Semantic Kernel patterns.

Based on official examples:
https://learn.microsoft.com/en-us/semantic-kernel/frameworks/agent/agent-chat
"""

from typing import List, Optional, Dict, Any
from semantic_kernel.agents import AgentGroupChat, ChatCompletionAgent
from semantic_kernel.agents.strategies import (
    SelectionStrategy,
    TerminationStrategy,
    KernelFunctionSelectionStrategy,
    KernelFunctionTerminationStrategy
)
from semantic_kernel import Kernel
from semantic_kernel.functions import KernelFunctionFromPrompt
from semantic_kernel.agents.group_chat import ChatHistoryTruncationReducer


class StratosAgentGroupChat:
    """Wrapper for Semantic Kernel AgentGroupChat with StratOS patterns."""
    
    def __init__(
        self,
        agents: List[ChatCompletionAgent],
        selection_strategy: Optional[SelectionStrategy] = None,
        termination_strategy: Optional[TerminationStrategy] = None,
        max_iterations: int = 10
    ):
        """Initialize agent group chat.
        
        Args:
            agents: List of agents to participate
            selection_strategy: Strategy for selecting next agent
            termination_strategy: Strategy for terminating chat
            max_iterations: Maximum chat iterations
        """
        self.agents = agents
        self.max_iterations = max_iterations
        
        # Create group chat with strategies
        self.group_chat = AgentGroupChat(
            agents=agents,
            selection_strategy=selection_strategy,
            termination_strategy=termination_strategy
        )
    
    async def run(self, initial_message: str) -> List[Dict[str, Any]]:
        """Run the group chat.
        
        Args:
            initial_message: Initial message to start chat
            
        Returns:
            List of messages from the chat
        """
        messages = []
        
        # Start the conversation
        await self.group_chat.add_chat_message(
            agent_name="user",
            content=initial_message
        )
        
        # Run the chat
        async for message in self.group_chat.invoke():
            messages.append({
                "agent": message.name,
                "content": message.content,
                "role": message.role
            })
        
        return messages


def create_selection_strategy(
    kernel: Kernel,
    initial_agent_name: str,
    agent_names: List[str]
) -> KernelFunctionSelectionStrategy:
    """Create a kernel function-based selection strategy.
    
    Args:
        kernel: Semantic Kernel instance
        initial_agent_name: Name of agent to start
        agent_names: List of all agent names
        
    Returns:
        Selection strategy
    """
    # Create selection prompt
    agent_list = "\n".join([f"- {name}" for name in agent_names])
    
    selection_function = KernelFunctionFromPrompt(
        function_name="select_agent",
        prompt=f"""
You are a routing coordinator. Based on the conversation history and the last message,
determine which participant should take the next turn in the conversation.

Available agents:
{agent_list}

RULES:
1. Only respond with the exact name of ONE agent from the list above
2. Consider the expertise and role of each agent
3. Route based on the content and intent of the last message
4. Ensure logical conversation flow

CONVERSATION HISTORY:
{{{{$history}}}}

LAST MESSAGE:
{{{{$lastmessage}}}}

State only the name of the participant to take the next turn:
""",
        kernel=kernel
    )
    
    # History reducer to manage context window
    history_reducer = ChatHistoryTruncationReducer(target_count=10)
    
    return KernelFunctionSelectionStrategy(
        initial_agent=initial_agent_name,
        function=selection_function,
        kernel=kernel,
        result_parser=lambda result: str(result.value[0]).strip() if result.value[0] else initial_agent_name,
        history_variable_name="history",
        history_reducer=history_reducer
    )


def create_termination_strategy(
    kernel: Kernel,
    termination_agents: List[str],
    termination_keyword: str = "completed",
    max_iterations: int = 20
) -> KernelFunctionTerminationStrategy:
    """Create a kernel function-based termination strategy.
    
    Args:
        kernel: Semantic Kernel instance
        termination_agents: List of agents that can terminate
        termination_keyword: Keyword to trigger termination
        max_iterations: Maximum iterations before forced termination
        
    Returns:
        Termination strategy
    """
    termination_function = KernelFunctionFromPrompt(
        function_name="check_termination",
        prompt=f"""
Examine the conversation and determine if the task has been completed.
If the task is complete, respond with: {termination_keyword}
If the task is not complete, respond with: continue

CONVERSATION HISTORY:
{{{{$history}}}}

LAST MESSAGE:
{{{{$lastmessage}}}}

Decision (respond with ONLY '{termination_keyword}' or 'continue'):
""",
        kernel=kernel
    )
    
    history_reducer = ChatHistoryTruncationReducer(target_count=5)
    
    return KernelFunctionTerminationStrategy(
        agents=termination_agents,
        function=termination_function,
        kernel=kernel,
        result_parser=lambda result: termination_keyword in str(result.value[0]).lower() if result.value[0] else False,
        history_variable_name="history",
        maximum_iterations=max_iterations,
        history_reducer=history_reducer
    )


class ApprovalTerminationStrategy(TerminationStrategy):
    """Custom termination strategy for approval-based workflows."""
    
    def __init__(self, approval_keywords: List[str] = None, max_iterations: int = 10):
        """Initialize approval termination strategy.
        
        Args:
            approval_keywords: Keywords indicating approval
            max_iterations: Maximum iterations
        """
        self.approval_keywords = approval_keywords or ["approved", "accepted", "confirmed"]
        self.max_iterations = max_iterations
        self.current_iteration = 0
    
    async def should_agent_terminate(self, agent, history) -> bool:
        """Check if agent should terminate based on approval.
        
        Args:
            agent: Current agent
            history: Chat history
            
        Returns:
            True if should terminate
        """
        self.current_iteration += 1
        
        # Check max iterations
        if self.current_iteration >= self.max_iterations:
            return True
        
        # Check for approval keywords in last message
        if history and len(history) > 0:
            last_message = history[-1].content.lower()
            return any(keyword in last_message for keyword in self.approval_keywords)
        
        return False