#!/usr/bin/env python3
"""
StratOS orchestration using Semantic Kernel - following semantic_kernel_multi_agent pattern.
This implements proper function registration for all 15 specialist agents.
"""

import os
import sys
import asyncio
import json
from datetime import datetime
from typing import Dict, List, Any
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import semantic_kernel as sk
from semantic_kernel.functions import kernel_function, KernelPlugin
from semantic_kernel.agents import AzureAIAgent
# Load settings
current_dir = os.path.dirname(os.path.abspath(__file__))
agentic_dir = os.path.dirname(current_dir)
env_path = os.path.join(agentic_dir, '.env')
load_dotenv(env_path)

# Get Azure configuration from environment
AZURE_AI_PROJECT_ENDPOINT = os.getenv("AZURE_AI_PROJECT_ENDPOINT")
AZURE_SUBSCRIPTION_ID = os.getenv("AZURE_SUBSCRIPTION_ID")
AZURE_RESOURCE_GROUP = os.getenv("AZURE_RESOURCE_GROUP")
AZURE_AI_PROJECT_NAME = os.getenv("AZURE_AI_PROJECT_NAME")

class SpecialistAgentPlugin:
    """Plugin that provides access to all StratOS specialist agents."""
    
    def __init__(self, agents_config: Dict[str, str]):
        """Initialize with deployed agent configurations."""
        self.agents = agents_config
        self.client = None
        self._setup_client()
    
    def _setup_client(self):
        """Set up the Azure AI Project client."""
        from azure.ai.projects.aio import AIProjectClient
        from azure.identity import DefaultAzureCredential
        
        credential = DefaultAzureCredential()
        self.client = AIProjectClient(
            endpoint=AZURE_AI_PROJECT_ENDPOINT,
            subscription_id=AZURE_SUBSCRIPTION_ID,
            resource_group_name=AZURE_RESOURCE_GROUP,
            project_name=AZURE_AI_PROJECT_NAME,
            credential=credential
        )
    
    @kernel_function(
        description="Handle CEO's subjective inputs, notes, observations, and log entries",
        name="invoke_ceologagent"
    )
    async def invoke_ceologagent(self, request: str) -> str:
        """Invoke the CEO Log Agent."""
        return await self._invoke_agent("CEOLogAgent", request)
    
    @kernel_function(
        description="Manage company vision, mission, values, and strategic goals",
        name="invoke_northstaragent"
    )
    async def invoke_northstaragent(self, request: str) -> str:
        """Invoke the North Star Agent."""
        return await self._invoke_agent("NorthStarAgent", request)
    
    @kernel_function(
        description="Retrieve historical context, patterns, and past experiences",
        name="invoke_memoryrecallagent"
    )
    async def invoke_memoryrecallagent(self, request: str) -> str:
        """Invoke the Memory Recall Agent."""
        return await self._invoke_agent("MemoryRecallAgent", request)
    
    @kernel_function(
        description="Track and learn user preferences for personalized experiences",
        name="invoke_preferencelearningagent"
    )
    async def invoke_preferencelearningagent(self, request: str) -> str:
        """Invoke the Preference Learning Agent."""
        return await self._invoke_agent("PreferenceLearningAgent", request)
    
    @kernel_function(
        description="Route requests within the strategic foundation domain",
        name="invoke_strategiccontextrouter"
    )
    async def invoke_strategiccontextrouter(self, request: str) -> str:
        """Invoke the Strategic Context Router."""
        return await self._invoke_agent("StrategicContextRouter", request)
    
    @kernel_function(
        description="Perform SWOT analysis and generate TOWS strategies",
        name="invoke_swottowsagent"
    )
    async def invoke_swottowsagent(self, request: str) -> str:
        """Invoke the SWOT/TOWS Agent."""
        return await self._invoke_agent("SWOTTOWSAgent", request)
    
    @kernel_function(
        description="Identify and analyze risks and opportunities",
        name="invoke_riskopportunityagent"
    )
    async def invoke_riskopportunityagent(self, request: str) -> str:
        """Invoke the Risk/Opportunity Agent."""
        return await self._invoke_agent("RiskOpportunityAgent", request)
    
    @kernel_function(
        description="Link subjective insights with objective data",
        name="invoke_solinkageagent"
    )
    async def invoke_solinkageagent(self, request: str) -> str:
        """Invoke the SO Linkage Agent."""
        return await self._invoke_agent("SOLinkageAgent", request)
    
    @kernel_function(
        description="Orchestrate complex analysis workflows",
        name="invoke_analysisorchestrator"
    )
    async def invoke_analysisorchestrator(self, request: str) -> str:
        """Invoke the Analysis Orchestrator."""
        return await self._invoke_agent("AnalysisOrchestrator", request)
    
    @kernel_function(
        description="Create strategic initiatives and action plans",
        name="invoke_initiativegenerationagent"
    )
    async def invoke_initiativegenerationagent(self, request: str) -> str:
        """Invoke the Initiative Generation Agent."""
        return await self._invoke_agent("InitiativeGenerationAgent", request)
    
    @kernel_function(
        description="Optimize resource allocation and capacity planning",
        name="invoke_resourceoptimizationagent"
    )
    async def invoke_resourceoptimizationagent(self, request: str) -> str:
        """Invoke the Resource Optimization Agent."""
        return await self._invoke_agent("ResourceOptimizationAgent", request)
    
    @kernel_function(
        description="Develop detailed action plans for initiatives",
        name="invoke_actionplanningagent"
    )
    async def invoke_actionplanningagent(self, request: str) -> str:
        """Invoke the Action Planning Agent."""
        return await self._invoke_agent("ActionPlanningAgent", request)
    
    @kernel_function(
        description="Score alignment between initiatives and strategic goals",
        name="invoke_alignmentscoringagent"
    )
    async def invoke_alignmentscoringagent(self, request: str) -> str:
        """Invoke the Alignment Scoring Agent."""
        return await self._invoke_agent("AlignmentScoringAgent", request)
    
    @kernel_function(
        description="Handle visual strategic planning on canvas",
        name="invoke_canvasvisualizationagent"
    )
    async def invoke_canvasvisualizationagent(self, request: str) -> str:
        """Invoke the Canvas Visualization Agent."""
        return await self._invoke_agent("CanvasVisualizationAgent", request)
    
    @kernel_function(
        description="Coordinate planning activities across the system",
        name="invoke_planningcoordinator"
    )
    async def invoke_planningcoordinator(self, request: str) -> str:
        """Invoke the Planning Coordinator."""
        return await self._invoke_agent("PlanningCoordinator", request)
    
    async def _invoke_agent(self, agent_name: str, request: str) -> str:
        """Common method to invoke any specialist agent."""
        agent_id = self.agents.get(agent_name)
        if not agent_id:
            return f"Error: {agent_name} not found in configuration"
        
        try:
            # Get agent definition
            agent_def = await self.client.agents.get_agent(agent_id=agent_id)
            agent = AzureAIAgent(client=self.client, definition=agent_def)
            
            # Create thread
            thread = await self.client.agents.threads.create()
            thread_id = thread.id
            
            # Invoke agent
            response_text = ""
            async for chunk in agent.invoke(thread_id=thread_id, message=request):
                if hasattr(chunk, 'content') and chunk.content:
                    response_text += str(chunk.content)
            
            # Clean up thread
            await self.client.agents.threads.delete(thread_id=thread_id)
            
            return response_text or f"No response from {agent_name}"
            
        except Exception as e:
            return f"Error invoking {agent_name}: {str(e)}"

def load_agents_config() -> Dict[str, str]:
    """Load deployed agents configuration."""
    import json
    config_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "deployment_configs",
        "ai_project_agents_deployment.json"
    )
    
    with open(config_path, 'r') as f:
        data = json.load(f)
        return data.get("deployed_agents", {})

async def setup_kernel_with_specialists():
    """Set up kernel with all specialist agent functions."""
    # Create kernel
    kernel = sk.Kernel()
    
    # Load agents configuration
    agents_config = load_agents_config()
    print(f"📋 Loaded {len(agents_config)} agent configurations")
    
    # Create specialist agent plugin
    specialist_plugin = SpecialistAgentPlugin(agents_config)
    
    # Register plugin with kernel using from_object pattern
    plugin = KernelPlugin.from_object(
        "SpecialistAgents",
        specialist_plugin,
        description="Provides access to all StratOS specialist agents"
    )
    
    # Add plugin to kernel
    kernel.plugins["SpecialistAgents"] = plugin
    
    print(f"✅ Registered {len(plugin.functions)} specialist functions")
    
    return kernel, agents_config

async def invoke_orchestrator_with_kernel(kernel, orchestrator_id: str, user_message: str):
    """Invoke the Main Orchestrator with proper kernel integration."""
    from azure.ai.projects.aio import AIProjectClient
    from azure.identity import DefaultAzureCredential
    
    credential = DefaultAzureCredential()
    client = AIProjectClient(
        endpoint=AZURE_AI_PROJECT_ENDPOINT,
        subscription_id=AZURE_SUBSCRIPTION_ID,
        resource_group_name=AZURE_RESOURCE_GROUP,
        project_name=AZURE_AI_PROJECT_NAME,
        credential=credential
    )
    
    try:
        # Get orchestrator definition
        orchestrator_def = await client.agents.get_agent(agent_id=orchestrator_id)
        
        # Create orchestrator WITH kernel - THIS IS THE KEY
        orchestrator = AzureAIAgent(
            client=client,
            definition=orchestrator_def,
            kernel=kernel  # Pass kernel with registered specialist functions
        )
        
        # Create thread
        thread = await client.agents.threads.create()
        thread_id = thread.id
        
        print(f"\n🎯 Orchestrator Thread: {thread_id}")
        print(f"📤 User Message: {user_message}")
        
        # Invoke orchestrator
        response_text = ""
        function_calls = []
        
        async for chunk in orchestrator.invoke(thread_id=thread_id, message=user_message):
            if hasattr(chunk, 'content') and chunk.content:
                response_text += str(chunk.content)
            
            # Track function calls if any
            if hasattr(chunk, 'tool_calls'):
                for tool_call in chunk.tool_calls:
                    function_calls.append({
                        "function": tool_call.function.name,
                        "arguments": tool_call.function.arguments
                    })
        
        print(f"\n📊 Results:")
        print(f"Response length: {len(response_text)}")
        print(f"Function calls: {len(function_calls)}")
        
        if function_calls:
            print("\nFunction calls made:")
            for fc in function_calls:
                print(f"  - {fc['function']}")
        
        if response_text:
            print(f"\n💬 Orchestrator Response:")
            print("="*60)
            print(response_text)
            print("="*60)
        
        # Clean up
        await client.agents.threads.delete(thread_id=thread_id)
        
        return response_text, function_calls
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        if "missing from the kernel" in str(e):
            print("\n🔍 This indicates the orchestrator expects function tools.")
            print("   But they should be registered now!")
        raise

async def test_orchestration():
    """Test the complete orchestration flow."""
    print("\n" + "="*80)
    print("STRATOS ORCHESTRATION TEST - Following semantic_kernel_multi_agent Pattern")
    print("="*80)
    
    # Setup kernel with specialist functions
    kernel, agents_config = await setup_kernel_with_specialists()
    
    # Get orchestrator ID
    orch_config_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "deployment_configs",
        "main_orchestrator_tools_deployment.json"
    )
    
    with open(orch_config_path, 'r') as f:
        orch_data = json.load(f)
        orchestrator_id = orch_data['agent_id']
    
    print(f"\n🤖 Main Orchestrator ID: {orchestrator_id}")
    
    # Test messages
    test_messages = [
        "I need to log that we just closed a major partnership deal with Microsoft",
        "Perform a SWOT analysis for our expansion into the healthcare market",
        "What are the key risks in our supply chain?",
        "Create an action plan for improving customer satisfaction by 20%",
        "Show me our company's north star metrics"
    ]
    
    # Test each message
    for i, message in enumerate(test_messages, 1):
        print(f"\n{'='*60}")
        print(f"TEST {i}/{len(test_messages)}")
        print(f"{'='*60}")
        
        try:
            response, function_calls = await invoke_orchestrator_with_kernel(
                kernel, orchestrator_id, message
            )
            
            if response:
                print(f"✅ Orchestration successful!")
            else:
                print(f"❌ No response received")
                
        except Exception as e:
            print(f"❌ Test failed: {str(e)}")

async def main():
    """Main entry point."""
    try:
        await test_orchestration()
    except Exception as e:
        print(f"\n❌ Critical error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())