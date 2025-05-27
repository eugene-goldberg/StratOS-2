#!/usr/bin/env python3
"""
Test the StratOS orchestrator locally using plugin-based architecture
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Add paths
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.contents import ChatMessageContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.agents import ChatCompletionAgent

# Import orchestrator
from agents.main_orchestrator.main_orchestrator import MainOrchestratorAgent

async def test_orchestrator():
    """Test the orchestrator with various queries"""
    # Load environment variables
    load_dotenv(os.path.join(current_dir, '.env'))
    
    # Create Azure OpenAI service
    service = AzureChatCompletion(
        deployment_name=os.getenv('AZURE_OPENAI_CHAT_DEPLOYMENT_NAME', 'gpt-35-turbo'),
        endpoint=os.getenv('AZURE_OPENAI_ENDPOINT'),
        api_key=os.getenv('AZURE_OPENAI_API_KEY')
    )
    
    print(f"Using endpoint: {os.getenv('AZURE_OPENAI_ENDPOINT')}")
    print(f"Using deployment: {os.getenv('AZURE_OPENAI_CHAT_DEPLOYMENT_NAME')}")
    
    # Create orchestrator
    print("\nCreating Main Orchestrator...")
    orchestrator = MainOrchestratorAgent(service=service)
    agent = orchestrator.get_agent()
    
    # Test queries
    test_queries = [
        "What is our company vision and mission?",
        "I noticed our customer satisfaction scores are dropping this quarter",
        "Perform a SWOT analysis for our new product line",
        "Create an initiative to improve customer experience",
        "What resources do we need for our Q2 projects?"
    ]
    
    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"Query: {query}")
        print(f"{'='*60}")
        
        try:
            # Get agent to process the query
            # The orchestrator should use its plugins to route to appropriate agents
            
            # Create a thread/conversation
            thread = []
            thread.append(ChatMessageContent(role=AuthorRole.USER, content=query))
            
            # Since we're using local plugins, the orchestrator will simulate routing
            # In a real deployment, it would call the actual deployed agents
            
            print("\nProcessing with orchestrator...")
            
            # The orchestrator should analyze the query and determine routing
            # For now, let's just get the orchestrator's analysis
            settings = agent._kernel.create_chat_prompt_execution_settings(
                service_id=agent._service_id,
                temperature=0.7
            )
            
            response = await agent._kernel.invoke_prompt(
                prompt=f"""You are the Main Orchestrator. Analyze this query and determine which specialist agent should handle it:
                
Query: {query}

Available agents:
- CEOLogAgent: Personal observations and insights
- NorthStarAgent: Vision, mission, values
- MemoryRecallAgent: Historical context
- PreferenceLearningAgent: Personalization
- SWOTTOWSAgent: Strategic analysis
- RiskOpportunityAgent: Risk assessment
- SOLinkageAgent: Subjective-objective linking
- AlignmentScoringAgent: Strategic alignment
- InitiativeGenerationAgent: Strategic initiatives
- ResourceOptimizationAgent: Resource management
- ActionPlanningAgent: Task planning
- CanvasVisualizationAgent: Visual planning

Determine which agent should handle this query and explain why.""",
                settings=settings
            )
            
            print(f"\nOrchestrator Analysis:\n{response}")
            
        except Exception as e:
            print(f"Error: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_orchestrator())