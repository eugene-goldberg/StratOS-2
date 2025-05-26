#!/usr/bin/env python3
"""
Update the Main Orchestrator with correct agent names based on actual deployments.
"""

import asyncio
import os
import json
import sys
from datetime import datetime
from dotenv import load_dotenv

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
agentic_dir = os.path.dirname(current_dir)
backend_dir = os.path.dirname(agentic_dir)
project_root = os.path.dirname(backend_dir)
sys.path.insert(0, project_root)

# Load environment variables
env_path = os.path.join(agentic_dir, '.env')
load_dotenv(env_path)

# Import required modules
from azure.identity.aio import DefaultAzureCredential
from semantic_kernel.agents import AzureAIAgent, AzureAIAgentSettings

async def update_orchestrator():
    """Update the Main Orchestrator with correct agent names."""
    
    # Load current orchestrator ID
    config_path = os.path.join(agentic_dir, "deployment_configs", "main_orchestrator_deployment.json")
    with open(config_path, 'r') as f:
        config = json.load(f)
        orchestrator_id = config['agent_id']
    
    print(f"Updating Main Orchestrator: {orchestrator_id}")
    
    # Load deployment summary to get actual agent names
    summary_path = os.path.join(agentic_dir, "deployment_configs", "deployment_summary.json")
    with open(summary_path, 'r') as f:
        deployment_summary = json.load(f)
    
    # Create updated instructions with correct agent names
    instructions = (
        "You are the Main Orchestrator for StratOS, a comprehensive strategy operating system. "
        "Your role is to analyze incoming requests and determine which specialized agent should handle them.\n\n"
        
        "AVAILABLE SPECIALIST AGENTS:\n"
        "Strategic Foundation & Insights System:\n"
        "1. CEOLogAgent - Handles CEO's subjective inputs, notes, observations, and concerns\n"
        "2. NorthStarAgent - Manages Purpose, Vision, Values, and Strategic Goals\n"
        "3. MemoryRecallAgent - Retrieves context, patterns, and historical information\n"
        "4. PreferenceLearningAgent - Tracks user preferences and personalizes experiences\n"
        "5. StrategicContextRouter - Routes requests within strategic foundation context\n\n"
        
        "Analysis & Intelligence System:\n"
        "6. SWOTTOWSAgent - Performs SWOT analysis and generates TOWS strategies\n"
        "7. RiskOpportunityAgent - Identifies opportunities and analyzes risks\n"
        "8. SOLinkageAgent - Links subjective insights to objective data\n"
        "9. AnalysisOrchestrator - Orchestrates complex analysis workflows\n\n"
        
        "Planning & Execution System:\n"
        "10. InitiativeGenerationAgent - Creates strategic initiatives and action plans\n"
        "11. ResourceOptimizationAgent - Manages resource allocation and capacity planning\n"
        "12. ActionPlanningAgent - Develops detailed action plans for initiatives\n"
        "13. AlignmentScoringAgent - Scores alignment of initiatives with strategic goals\n"
        "14. CanvasVisualizationAgent - Handles visual strategic planning on canvas\n"
        "15. PlanningCoordinator - Coordinates planning activities across the system\n\n"
        
        "ROUTING APPROACH:\n"
        "1. Analyze the user's request to understand their intent\n"
        "2. Identify which specialized agent is best suited to handle the request\n"
        "3. Provide a routing decision with the agent name and reasoning\n"
        "4. Format your response as: 'ROUTE TO: [AgentName] - REASON: [Your reasoning]'\n\n"
        
        "ROUTING GUIDELINES:\n"
        "- For CEO notes, observations, or log entries → CEOLogAgent\n"
        "- For questions about vision, mission, values, or north star goals → NorthStarAgent\n"
        "- For SWOT analysis or TOWS strategies → SWOTTOWSAgent\n"
        "- For risk assessment or opportunity identification → RiskOpportunityAgent\n"
        "- For linking subjective insights to data → SOLinkageAgent\n"
        "- For complex analysis orchestration → AnalysisOrchestrator\n"
        "- For creating initiatives or strategic plans → InitiativeGenerationAgent\n"
        "- For resource allocation or optimization → ResourceOptimizationAgent\n"
        "- For detailed action planning → ActionPlanningAgent\n"
        "- For initiative-goal alignment → AlignmentScoringAgent\n"
        "- For strategic canvas or visualization → CanvasVisualizationAgent\n"
        "- For planning coordination → PlanningCoordinator\n"
        "- For retrieving past context or patterns → MemoryRecallAgent\n"
        "- For user preference tracking → PreferenceLearningAgent\n"
        "- For strategic context routing → StrategicContextRouter\n\n"
        
        "Always provide clear routing decisions. Do not try to answer questions yourself."
    )
    
    try:
        # Create settings and credential
        settings = AzureAIAgentSettings()
        credential = DefaultAzureCredential()
        
        async with AzureAIAgent.create_client(credential=credential, settings=settings) as client:
            print("Connected to Azure AI Agent Service")
            
            # Update the orchestrator
            print("Updating orchestrator instructions...")
            
            updated_agent = await client.agents.update_agent(
                agent_id=orchestrator_id,
                instructions=instructions
            )
            
            print(f"✅ Main Orchestrator updated successfully!")
            print(f"  ID: {updated_agent.id}")
            print(f"  Name: {updated_agent.name}")
            print(f"  Updated: {datetime.now().isoformat()}")
            
            # Update deployment config
            config['last_updated'] = datetime.now().isoformat()
            config['update_notes'] = "Updated agent names to match actual deployments"
            
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
            
            print("\n✅ Deployment config updated")
            
    except Exception as e:
        print(f"❌ Error updating orchestrator: {e}")
        raise
    
    await credential.close()

if __name__ == "__main__":
    asyncio.run(update_orchestrator())