#!/usr/bin/env python3
"""
Test interaction with every deployed StratOS agent.
"""

import asyncio
import os
import json
from datetime import datetime
from dotenv import load_dotenv

from azure.identity.aio import DefaultAzureCredential
from semantic_kernel.agents import AzureAIAgent, AzureAIAgentSettings

# Load environment
current_dir = os.path.dirname(os.path.abspath(__file__))
agentic_dir = os.path.dirname(current_dir) 
load_dotenv(os.path.join(agentic_dir, '.env'))

# Test messages for each agent
AGENT_TEST_MESSAGES = {
    # Strategic Foundation & Insights System
    "StrategicContextRouter": "What are our key strategic priorities and how should we approach them?",
    "CEOLogAgent": "Had a productive meeting with investors today. They're impressed with our Q4 results and want to discuss expansion opportunities.",
    "NorthStarAgent": "What is our company's mission, vision, and core values?",
    "MemoryRecallAgent": "What important decisions have we made in the past month?",
    "PreferenceLearningAgent": "I prefer concise summaries with bullet points and actionable insights.",
    
    # Analysis & Intelligence System
    "AnalysisOrchestrator": "Analyze our current market position and competitive landscape.",
    "SWOTTOWSAgent": "Perform a SWOT analysis for our cloud services division.",
    "RiskOpportunityAgent": "What are the top risks and opportunities we should be aware of?",
    "SOLinkageAgent": "How do our customer satisfaction metrics relate to revenue growth?",
    
    # Planning & Execution System
    "PlanningCoordinator": "Create a strategic plan for expanding into new markets.",
    "InitiativeGenerationAgent": "Generate initiatives to improve customer retention by 20%.",
    "ResourceOptimizationAgent": "How should we optimize resource allocation across our projects?",
    "CanvasVisualizationAgent": "Create a visual representation of our growth strategy.",
    "AlignmentScoringAgent": "Score the alignment between our IT projects and business goals.",
    "ActionPlanningAgent": "Break down our market expansion initiative into actionable tasks."
}

async def test_all_agents():
    """Test interaction with all deployed agents."""
    
    print(f"Testing All Deployed StratOS Agents")
    print(f"{'='*70}")
    print(f"Started at: {datetime.now().isoformat()}\n")
    
    # Load agent configurations
    config_path = os.path.join(
        os.path.dirname(__file__), 
        '..', 
        'deployment_configs', 
        'ai_project_agents_deployment.json'
    )
    
    with open(config_path, 'r') as f:
        data = json.load(f)
        deployed_agents = data.get('deployed_agents', {})
    
    print(f"Found {len(deployed_agents)} deployed agents\n")
    
    # Track results
    results = {
        "successful": [],
        "failed": [],
        "empty_response": []
    }
    
    try:
        # Create settings and client
        settings = AzureAIAgentSettings()
        
        async with DefaultAzureCredential(exclude_interactive_browser_credential=False) as credential:
            async with AzureAIAgent.create_client(credential=credential, settings=settings) as client:
                print("✓ Connected to Azure AI Agent Service\n")
                
                # Test each agent
                for agent_name, agent_id in deployed_agents.items():
                    print(f"{'-'*70}")
                    print(f"Testing: {agent_name}")
                    print(f"Agent ID: {agent_id}")
                    
                    try:
                        # Get agent
                        agent_def = await client.agents.get_agent(agent_id=agent_id)
                        print(f"✓ Retrieved agent definition")
                        
                        # Create SK agent
                        agent = AzureAIAgent(client=client, definition=agent_def)
                        
                        # Get test message
                        test_message = AGENT_TEST_MESSAGES.get(agent_name, "Hello, can you tell me about your capabilities?")
                        print(f"\nUser: {test_message}")
                        
                        # Invoke agent
                        print(f"\n{agent_name}: ", end="", flush=True)
                        
                        response_text = ""
                        chunk_count = 0
                        
                        async for chunk in agent.invoke(message=test_message):
                            chunk_count += 1
                            if hasattr(chunk, 'content') and chunk.content:
                                chunk_text = str(chunk.content)
                                print(chunk_text, end="", flush=True)
                                response_text += chunk_text
                        
                        print()  # New line after response
                        
                        # Categorize result
                        if response_text:
                            results["successful"].append(agent_name)
                            print(f"\n✓ Success: Received {len(response_text)} characters in {chunk_count} chunks")
                        else:
                            results["empty_response"].append(agent_name)
                            print(f"\n⚠ Warning: Agent returned empty response after {chunk_count} chunks")
                            
                    except Exception as e:
                        results["failed"].append((agent_name, str(e)))
                        print(f"\n✗ Error: {type(e).__name__}: {str(e)}")
                    
                    print()  # Blank line between agents
                    
                    # Brief pause to avoid rate limiting
                    await asyncio.sleep(1)
                
                # Print summary
                print(f"\n{'='*70}")
                print(f"SUMMARY REPORT")
                print(f"{'='*70}")
                
                total = len(deployed_agents)
                successful = len(results["successful"])
                empty = len(results["empty_response"])
                failed = len(results["failed"])
                
                print(f"\nTotal Agents Tested: {total}")
                print(f"✓ Successful Responses: {successful} ({successful/total*100:.1f}%)")
                print(f"⚠ Empty Responses: {empty} ({empty/total*100:.1f}%)")
                print(f"✗ Failed: {failed} ({failed/total*100:.1f}%)")
                
                if results["successful"]:
                    print(f"\n✓ Agents with Successful Responses ({successful}):")
                    for agent in sorted(results["successful"]):
                        print(f"  - {agent}")
                
                if results["empty_response"]:
                    print(f"\n⚠ Agents with Empty Responses ({empty}):")
                    for agent in sorted(results["empty_response"]):
                        print(f"  - {agent}")
                
                if results["failed"]:
                    print(f"\n✗ Failed Agents ({failed}):")
                    for agent, error in results["failed"]:
                        print(f"  - {agent}: {error}")
                
                # System breakdown
                print(f"\n{'='*70}")
                print("RESULTS BY SYSTEM")
                print(f"{'='*70}")
                
                systems = {
                    "Strategic Foundation & Insights": ["StrategicContextRouter", "CEOLogAgent", "NorthStarAgent", "MemoryRecallAgent", "PreferenceLearningAgent"],
                    "Analysis & Intelligence": ["AnalysisOrchestrator", "SWOTTOWSAgent", "RiskOpportunityAgent", "SOLinkageAgent"],
                    "Planning & Execution": ["PlanningCoordinator", "InitiativeGenerationAgent", "ResourceOptimizationAgent", "CanvasVisualizationAgent", "AlignmentScoringAgent", "ActionPlanningAgent"]
                }
                
                for system_name, system_agents in systems.items():
                    system_successful = sum(1 for agent in system_agents if agent in results["successful"])
                    system_empty = sum(1 for agent in system_agents if agent in results["empty_response"])
                    system_failed = sum(1 for agent in system_agents if any(agent == f[0] for f in results["failed"]))
                    system_total = len(system_agents)
                    
                    print(f"\n{system_name}:")
                    print(f"  Total: {system_total}")
                    print(f"  ✓ Successful: {system_successful}")
                    print(f"  ⚠ Empty: {system_empty}")
                    print(f"  ✗ Failed: {system_failed}")
                
                print(f"\n{'='*70}")
                print(f"Completed at: {datetime.now().isoformat()}")
                
    except Exception as e:
        print(f"\n✗ Fatal Error: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("\nStarting comprehensive agent testing...\n")
    asyncio.run(test_all_agents())