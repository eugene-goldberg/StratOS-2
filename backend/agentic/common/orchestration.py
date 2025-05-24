"""
Orchestration utilities for StratOS multi-agent system.
Adopted from semantic_kernel_multi_agent orchestrate_with_kernel.py pattern.

This module provides function calling and agent delegation capabilities.
"""

import json
from typing import Dict, Any, List, Optional
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion, AzureChatPromptExecutionSettings
from semantic_kernel.functions.kernel_arguments import KernelArguments
from ..config.settings import get_settings


class AgentOrchestrator:
    """
    Handles orchestration of agent interactions using function calling.
    Based on the pattern from semantic_kernel_multi_agent.
    """
    
    def __init__(self, kernel: Kernel):
        """
        Initialize the orchestrator.
        
        Args:
            kernel: Semantic Kernel instance with registered plugins
        """
        self.kernel = kernel
        self.settings = get_settings()
        self._setup_chat_service()
    
    def _setup_chat_service(self):
        """Set up Azure OpenAI chat service if not already configured."""
        if "chat" not in self.kernel.services:
            self.kernel.add_service(
                AzureChatCompletion(
                    service_id="chat",
                    deployment_name=self.settings.azure_openai_deployment_name,
                    endpoint=self.settings.azure_openai_endpoint,
                    api_key=self.settings.azure_openai_api_key,
                    api_version=self.settings.azure_openai_api_version
                )
            )
    
    async def orchestrate_with_function_calling(
        self,
        messages: List[Dict[str, Any]],
        available_functions: List[Dict[str, Any]],
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Orchestrate a conversation with function calling capabilities.
        
        Args:
            messages: Conversation history
            available_functions: List of function definitions for the model
            system_prompt: Optional system prompt to guide the model
            
        Returns:
            Dict containing the response and any function calls made
        """
        # Prepare messages with system prompt if provided
        current_messages = []
        if system_prompt:
            current_messages.append({"role": "system", "content": system_prompt})
        current_messages.extend(messages)
        
        # Get chat service
        chat_service = self.kernel.get_service("chat")
        if not chat_service:
            raise ValueError("Chat service 'chat' not found in kernel.")
        
        # Configure settings for function calling
        settings = AzureChatPromptExecutionSettings(
            tool_choice="auto",
            tools=available_functions
        )
        
        # Get initial response
        response_messages = await chat_service.complete_chat_async(
            messages=current_messages,
            settings=settings
        )
        
        if not response_messages:
            return {
                "content": "Sorry, I couldn't get a response.",
                "function_calls": []
            }
        
        assistant_message = response_messages[0]
        content = assistant_message.content
        processed_function_calls = []
        
        # Process function calls if any
        if assistant_message.tool_calls:
            for tool_call in assistant_message.tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                
                # Find and execute the function
                plugin_name, func_name = self._parse_function_name(function_name)
                if plugin_name and func_name:
                    result = await self._execute_function(
                        plugin_name, func_name, function_args
                    )
                    
                    processed_function_calls.append({
                        "name": function_name,
                        "arguments": function_args,
                        "result": result
                    })
                    
                    # Prepare follow-up messages
                    followup_messages = list(current_messages)
                    followup_messages.append(assistant_message.to_dict())
                    followup_messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": str(result)
                    })
                    
                    # Get final response incorporating function results
                    final_settings = AzureChatPromptExecutionSettings(tool_choice="none")
                    final_response = await chat_service.complete_chat_async(
                        messages=followup_messages,
                        settings=final_settings
                    )
                    
                    if final_response:
                        content = final_response[0].content
        
        return {
            "content": content,
            "function_calls": processed_function_calls
        }
    
    def _parse_function_name(self, function_name: str) -> tuple:
        """
        Parse function name into plugin and function components.
        
        Args:
            function_name: Name in format "PluginName.FunctionName" or "FunctionName"
            
        Returns:
            Tuple of (plugin_name, function_name)
        """
        if "." in function_name:
            parts = function_name.split(".", 1)
            return parts[0], parts[1]
        else:
            # Try to find the function in any plugin
            for plugin_name, plugin in self.kernel.plugins.items():
                if function_name in plugin:
                    return plugin_name, function_name
        return None, None
    
    async def _execute_function(
        self,
        plugin_name: str,
        function_name: str,
        arguments: Dict[str, Any]
    ) -> Any:
        """
        Execute a function from a plugin.
        
        Args:
            plugin_name: Name of the plugin
            function_name: Name of the function
            arguments: Function arguments
            
        Returns:
            Function result
        """
        plugin = self.kernel.plugins.get(plugin_name)
        if not plugin:
            raise ValueError(f"Plugin '{plugin_name}' not found in kernel.")
        
        function = plugin.get(function_name)
        if not function:
            raise ValueError(f"Function '{function_name}' not found in plugin '{plugin_name}'.")
        
        # Execute the function
        function_args = KernelArguments(**arguments)
        result = await self.kernel.invoke(function, arguments=function_args)
        
        return result.value if result else None
    
    def create_function_definition(
        self,
        name: str,
        description: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a function definition for use with Azure OpenAI.
        
        Args:
            name: Function name
            description: Function description
            parameters: Parameter schema
            
        Returns:
            Function definition dict
        """
        return {
            "type": "function",
            "function": {
                "name": name,
                "description": description,
                "parameters": parameters
            }
        }
    
    async def delegate_to_agent(
        self,
        agent_name: str,
        request: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Delegate a request to a specific agent.
        
        Args:
            agent_name: Name of the agent to delegate to
            request: Request to send to the agent
            context: Optional context information
            
        Returns:
            Agent response
        """
        # This would integrate with the agent's process_request method
        # For now, return a placeholder
        return {
            "agent": agent_name,
            "status": "delegated",
            "request": request,
            "response": "Agent delegation placeholder"
        }


class FunctionCallingMixin:
    """
    Mixin to add function calling capabilities to agents.
    Can be used by router agents to enable delegation.
    """
    
    def setup_function_calling(self, orchestrator: AgentOrchestrator):
        """Set up function calling with an orchestrator."""
        self.orchestrator = orchestrator
    
    def get_available_functions(self) -> List[Dict[str, Any]]:
        """
        Get list of available functions for this agent.
        Should be overridden by subclasses.
        
        Returns:
            List of function definitions
        """
        return []
    
    async def process_with_functions(
        self,
        request: str,
        chat_history: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Process a request with function calling capabilities.
        
        Args:
            request: User request
            chat_history: Optional conversation history
            
        Returns:
            Response with function call information
        """
        if not hasattr(self, 'orchestrator'):
            raise ValueError("Orchestrator not set up. Call setup_function_calling first.")
        
        messages = chat_history or []
        messages.append({"role": "user", "content": request})
        
        return await self.orchestrator.orchestrate_with_function_calling(
            messages=messages,
            available_functions=self.get_available_functions(),
            system_prompt=getattr(self, 'instructions', None)
        )