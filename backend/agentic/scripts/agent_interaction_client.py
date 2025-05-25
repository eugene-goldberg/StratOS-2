"""
Azure AI Agent Service Interaction Client for StratOS Agents
"""

import os
import json
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
from dotenv import load_dotenv

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.contents import ChatMessageContent, AuthorRole
from semantic_kernel.agents import Agent
from semantic_kernel.agents.open_ai import AzureAssistantAgent
from azure.identity import DefaultAzureCredential, get_bearer_token_provider

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

class StratosAgentClient:
    """Client for interacting with deployed StratOS agents."""
    
    def __init__(self):
        """Initialize the agent client with Azure credentials."""
        # Azure AI Agent Service settings
        self.endpoint = os.getenv("AZURE_AI_AGENT_ENDPOINT")
        self.api_version = os.getenv("AZURE_AI_AGENT_API_VERSION", "2024-12-01-preview")
        self.model_deployment = os.getenv("AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME", "gpt-35-turbo")
        
        # Authentication
        self.credential = DefaultAzureCredential()
        self.token_provider = get_bearer_token_provider(
            self.credential, 
            "https://cognitiveservices.azure.com/.default"
        )
        
        # Load deployed agent configurations
        self.agent_configs = self._load_agent_configs()
        
        # Initialize kernel
        self.kernel = self._create_kernel()
        
    def _load_agent_configs(self) -> Dict[str, str]:
        """Load agent IDs from deployment configuration."""
        config_path = os.path.join(
            os.path.dirname(__file__), 
            '..', 
            'deployment_configs', 
            'ai_project_agents_deployment.json'
        )
        
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                data = json.load(f)
                return data.get('agents', {})
        return {}
    
    def _create_kernel(self) -> Kernel:
        """Create a Semantic Kernel instance."""
        kernel = Kernel()
        
        # Add Azure OpenAI chat service
        service_id = "azure_openai_chat"
        kernel.add_service(
            AzureChatCompletion(
                service_id=service_id,
                deployment_name=self.model_deployment,
                endpoint=self.endpoint,
                api_version=self.api_version,
                ad_token_provider=self.token_provider
            )
        )
        
        return kernel
    
    async def get_agent(self, agent_name: str) -> Optional[AzureAssistantAgent]:
        """Get an agent instance by name."""
        if agent_name not in self.agent_configs:
            print(f"Agent '{agent_name}' not found in deployment configuration.")
            return None
            
        agent_id = self.agent_configs[agent_name]
        
        try:
            agent = await AzureAssistantAgent.retrieve(
                id=agent_id,
                endpoint=self.endpoint,
                api_version=self.api_version,
                kernel=self.kernel,
                ad_token_provider=self.token_provider
            )
            return agent
        except Exception as e:
            print(f"Error retrieving agent '{agent_name}': {e}")
            return None
    
    async def list_agents(self) -> List[str]:
        """List all available agents."""
        return list(self.agent_configs.keys())
    
    async def chat_with_agent(
        self, 
        agent_name: str, 
        message: str,
        thread_id: Optional[str] = None,
        stream: bool = False
    ) -> Dict[str, Any]:
        """Have a conversation with a specific agent."""
        agent = await self.get_agent(agent_name)
        if not agent:
            return {"error": f"Agent '{agent_name}' not found"}
        
        try:
            # Create or retrieve thread
            if thread_id:
                thread = await agent.get_thread(thread_id)
            else:
                thread = await agent.create_thread()
            
            # Add user message
            await thread.add_user_message(message)
            
            # Get agent response
            if stream:
                # Stream response
                response_text = ""
                async for content in thread.invoke_stream(agent):
                    if content.content:
                        response_text += content.content
                        yield {
                            "agent": agent_name,
                            "thread_id": thread.id,
                            "content": content.content,
                            "streaming": True
                        }
                
                return {
                    "agent": agent_name,
                    "thread_id": thread.id,
                    "response": response_text,
                    "timestamp": datetime.utcnow().isoformat()
                }
            else:
                # Get complete response
                messages = await thread.invoke(agent)
                
                # Extract assistant response
                assistant_messages = [
                    msg for msg in messages 
                    if msg.role == AuthorRole.ASSISTANT
                ]
                
                response_text = assistant_messages[-1].content if assistant_messages else ""
                
                return {
                    "agent": agent_name,
                    "thread_id": thread.id,
                    "response": response_text,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            return {
                "error": str(e),
                "agent": agent_name,
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def route_to_system(
        self, 
        system: str, 
        message: str,
        thread_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Route a message to the appropriate system router."""
        routers = {
            "strategic": "StrategicContextRouter",
            "analysis": "AnalysisOrchestrator",
            "planning": "PlanningCoordinator"
        }
        
        router_name = routers.get(system.lower())
        if not router_name:
            return {"error": f"Unknown system: {system}"}
        
        return await self.chat_with_agent(router_name, message, thread_id)
    
    async def get_agent_info(self, agent_name: str) -> Dict[str, Any]:
        """Get information about a specific agent."""
        agent = await self.get_agent(agent_name)
        if not agent:
            return {"error": f"Agent '{agent_name}' not found"}
        
        return {
            "name": agent.name,
            "id": agent.id,
            "description": agent.description,
            "instructions": agent.instructions,
            "model": agent.model,
            "created_at": agent.created_at,
            "metadata": agent.metadata
        }
    
    async def close(self):
        """Clean up resources."""
        # Any cleanup needed
        pass


# Example usage functions
async def test_agent_interaction():
    """Test basic agent interaction."""
    client = StratosAgentClient()
    
    # List all agents
    print("Available agents:")
    agents = await client.list_agents()
    for agent in agents:
        print(f"  - {agent}")
    
    # Test CEO Log Agent
    print("\n--- Testing CEO Log Agent ---")
    response = await client.chat_with_agent(
        "CEOLogAgent",
        "I had a great meeting with our biggest client today. They're interested in expanding our partnership."
    )
    print(f"Response: {response.get('response', response.get('error'))}")
    
    # Test Strategic Router
    print("\n--- Testing Strategic Context Router ---")
    response = await client.route_to_system(
        "strategic",
        "What are our company's core values?"
    )
    print(f"Response: {response.get('response', response.get('error'))}")
    
    await client.close()


if __name__ == "__main__":
    asyncio.run(test_agent_interaction())