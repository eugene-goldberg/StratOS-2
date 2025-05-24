"""Base agent template following Semantic Kernel patterns.

Based on official Semantic Kernel Agent Framework:
https://learn.microsoft.com/en-us/semantic-kernel/frameworks/agent/
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from uuid import UUID
import asyncio
from semantic_kernel import Kernel
from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.agents.chat.chat_history_channel import ChatHistoryChannel


class BaseStratosAgent(ABC):
    """Base class for all StratOS agents following Semantic Kernel patterns."""
    
    def __init__(
        self,
        name: str,
        instructions: str,
        kernel: Kernel,
        description: Optional[str] = None,
        plugins: Optional[List[Any]] = None
    ):
        """Initialize base agent with Semantic Kernel components.
        
        Args:
            name: Agent name
            instructions: System instructions for the agent
            kernel: Semantic Kernel instance with AI service
            description: Optional agent description
            plugins: Optional list of plugins/skills
        """
        self.name = name
        self.instructions = instructions
        self.description = description or f"{name} agent"
        
        # Create ChatCompletionAgent following SK pattern
        self.agent = ChatCompletionAgent(
            kernel=kernel,
            name=name,
            instructions=instructions,
            description=description
        )
        
        # Add plugins if provided
        if plugins:
            for plugin in plugins:
                kernel.import_plugin(plugin)
    
    @abstractmethod
    async def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process agent-specific request.
        
        Args:
            request: Request data specific to agent type
            
        Returns:
            Response dictionary
        """
        pass
    
    async def invoke(
        self,
        message: str,
        history: Optional[ChatHistoryChannel] = None
    ) -> AsyncIterator[ChatMessageContent]:
        """Invoke agent with a message following SK pattern.
        
        Args:
            message: User message
            history: Optional chat history
            
        Yields:
            Chat message content chunks
        """
        async for response in self.agent.invoke(message, history):
            yield response
    
    async def invoke_stream(
        self,
        message: str,
        history: Optional[ChatHistoryChannel] = None
    ) -> AsyncIterator[str]:
        """Stream agent response.
        
        Args:
            message: User message
            history: Optional chat history
            
        Yields:
            Response content chunks
        """
        async for chunk in self.agent.invoke_stream(message, history):
            if chunk.content:
                yield chunk.content


class RouterAgent(BaseStratosAgent):
    """Base router agent for multi-agent systems."""
    
    def __init__(
        self,
        name: str,
        instructions: str,
        kernel: Kernel,
        specialized_agents: Dict[str, BaseStratosAgent],
        description: Optional[str] = None
    ):
        """Initialize router agent.
        
        Args:
            name: Router name
            instructions: Routing instructions
            kernel: Semantic Kernel instance
            specialized_agents: Dictionary of specialized agents
            description: Optional description
        """
        super().__init__(name, instructions, kernel, description)
        self.specialized_agents = specialized_agents
    
    @abstractmethod
    async def route_request(self, request: Dict[str, Any]) -> str:
        """Determine which agent should handle the request.
        
        Args:
            request: Incoming request
            
        Returns:
            Name of the agent to handle request
        """
        pass
    
    async def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process request by routing to appropriate agent.
        
        Args:
            request: Incoming request
            
        Returns:
            Response from specialized agent
        """
        # Determine which agent should handle
        agent_name = await self.route_request(request)
        
        if agent_name not in self.specialized_agents:
            return {
                "error": f"Unknown agent: {agent_name}",
                "available_agents": list(self.specialized_agents.keys())
            }
        
        # Delegate to specialized agent
        agent = self.specialized_agents[agent_name]
        return await agent.process_request(request)


def create_kernel_with_azure_openai(
    deployment_name: str,
    endpoint: str,
    api_key: str,
    api_version: str = "2024-02-15-preview"
) -> Kernel:
    """Create Semantic Kernel with Azure OpenAI service.
    
    Args:
        deployment_name: Azure OpenAI deployment name
        endpoint: Azure OpenAI endpoint
        api_key: API key
        api_version: API version
        
    Returns:
        Configured kernel
    """
    kernel = Kernel()
    
    # Add Azure OpenAI chat completion service
    service = AzureChatCompletion(
        deployment_name=deployment_name,
        endpoint=endpoint,
        api_key=api_key,
        api_version=api_version,
        service_id="chat-gpt"
    )
    
    kernel.add_service(service)
    return kernel