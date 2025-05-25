#!/usr/bin/env python3
"""
Deploy StratOS agents as Azure OpenAI Assistants using the OpenAI SDK directly.
This bypasses issues with the Semantic Kernel AzureAIAgent implementation.
"""

import os
import sys
import json
from datetime import datetime
from dotenv import load_dotenv

# Add parent directories to path
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
sys.path.insert(0, backend_dir)

# Load environment variables
env_path = os.path.join(backend_dir, '.env')
load_dotenv(env_path)

print("===== StratOS Agent Deployment to Azure OpenAI Assistants =====")
print(f"Deployment started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

try:
    from openai import AzureOpenAI
except ImportError:
    print("Installing openai package...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "openai"])
    from openai import AzureOpenAI

# Initialize the Azure OpenAI client
client = AzureOpenAI(
    azure_endpoint="https://sk-multi-agent-openai.openai.azure.com/",
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version="2024-05-01-preview"
)

print(f"\n✓ Connected to Azure OpenAI")
print(f"  Endpoint: https://sk-multi-agent-openai.openai.azure.com/")
print(f"  Model: gpt-35-turbo")

# Define all agents
agents_to_deploy = [
    # Strategic Foundation & Insights System
    {
        "name": "StrategicContextRouter",
        "instructions": (
            "You are the Strategic Context Router for StratOS. Your role is to analyze incoming requests and route them to "
            "the appropriate specialized agent within the Strategic Foundation & Insights System. You manage: "
            "1) CEO Log Agent for subjective inputs and voice transcriptions, "
            "2) North Star Agent for vision, values, and strategic goals, "
            "3) Memory & Recall Agent for context retrieval and pattern recognition, "
            "4) Preference Learning Agent for personalization."
        ),
        "description": "Routes requests within the Strategic Foundation system",
        "system": "Strategic Foundation & Insights"
    },
    {
        "name": "CEOLogAgent",
        "instructions": (
            "You are the CEO Log Agent for StratOS. You specialize in processing subjective inputs from the CEO including "
            "voice transcriptions, thoughts, observations, and strategic reflections. Your capabilities include: "
            "1) Processing voice-to-text transcriptions, 2) Generating relevant tags for entries, "
            "3) Creating concise summaries, 4) Extracting strategic insights from subjective content."
        ),
        "description": "Manages CEO's subjective inputs, voice transcriptions, and insights",
        "system": "Strategic Foundation & Insights"
    },
    {
        "name": "NorthStarAgent",
        "instructions": (
            "You are the North Star Agent for StratOS. You are the guardian of the organization's strategic foundation "
            "including Purpose, Vision, Values, and Strategic Goals. Your responsibilities include: "
            "1) Maintaining consistency across all strategic elements, 2) Managing hierarchical goal structures, "
            "3) Validating goal alignment with organizational values, 4) Providing guidance on strategic direction."
        ),
        "description": "Manages organizational purpose, vision, values, and strategic goals",
        "system": "Strategic Foundation & Insights"
    },
    {
        "name": "MemoryRecallAgent",
        "instructions": (
            "You are the Memory & Recall Agent for StratOS. You specialize in retrieving relevant strategic context "
            "and identifying patterns across the organization's history. Your capabilities include: "
            "1) Semantic search across all strategic documents and logs, 2) Pattern recognition in historical data, "
            "3) Context assembly for decision-making, 4) Trend identification over time."
        ),
        "description": "Provides strategic context retrieval and pattern recognition",
        "system": "Strategic Foundation & Insights"
    },
    {
        "name": "PreferenceLearningAgent",
        "instructions": (
            "You are the Preference Learning Agent for StratOS. You observe user interactions to learn preferences "
            "and personalize the experience. Your focus areas include: 1) Tracking accepted vs rejected suggestions, "
            "2) Learning communication style preferences, 3) Understanding decision-making patterns, "
            "4) Adapting responses based on user history."
        ),
        "description": "Learns and applies user preferences for personalization",
        "system": "Strategic Foundation & Insights"
    },
    # Analysis & Intelligence System
    {
        "name": "AnalysisOrchestrator",
        "instructions": (
            "You are the Analysis Orchestrator for StratOS. You coordinate all analytical activities within the "
            "Analysis & Intelligence System. You manage: 1) SWOT/TOWS Agent for strategic analysis, "
            "2) Risk/Opportunity Agent for threat and opportunity detection, "
            "3) S+O Linkage Agent for connecting subjective and objective data."
        ),
        "description": "Orchestrates complex analysis workflows",
        "system": "Analysis & Intelligence"
    },
    {
        "name": "SWOTTOWSAgent",
        "instructions": (
            "You are the SWOT/TOWS Agent for StratOS. You specialize in strategic analysis using SWOT "
            "(Strengths, Weaknesses, Opportunities, Threats) and TOWS matrix methodologies. Your process includes: "
            "1) Guiding users through comprehensive SWOT analysis, 2) Maintaining session state for multi-step analysis, "
            "3) Generating TOWS strategies by combining SWOT elements, 4) Providing contextual prompts."
        ),
        "description": "Performs SWOT analysis and generates TOWS strategies",
        "system": "Analysis & Intelligence"
    },
    {
        "name": "RiskOpportunityAgent",
        "instructions": (
            "You are the Risk/Opportunity Detection Agent for StratOS. You continuously monitor for potential risks "
            "and opportunities across all organizational data. Your capabilities include: "
            "1) Anomaly detection in patterns and metrics, 2) Risk assessment with severity levels, "
            "3) Opportunity identification with potential impact, 4) Alert generation with recommended actions."
        ),
        "description": "Detects and assesses risks and opportunities",
        "system": "Analysis & Intelligence"
    },
    {
        "name": "SOLinkageAgent",
        "instructions": (
            "You are the S+O Linkage Agent for StratOS. You specialize in discovering connections between subjective "
            "inputs (CEO thoughts, observations) and objective data (KPIs, metrics, market data). Your process includes: "
            "1) Pattern matching between qualitative and quantitative information, 2) Correlation analysis, "
            "3) Insight generation that bridges intuition and data."
        ),
        "description": "Links subjective insights with objective data",
        "system": "Analysis & Intelligence"
    },
    # Planning & Execution System
    {
        "name": "PlanningCoordinator",
        "instructions": (
            "You are the Planning Coordinator for StratOS. You orchestrate all planning and execution activities. "
            "You manage: 1) Initiative Generation Agent for creating strategic initiatives, "
            "2) Resource Optimization Agent for allocation decisions, 3) Canvas Visualization Agent for visual planning, "
            "4) Alignment Scoring Agent for strategic fit assessment, 5) Action Planning Agent for detailed execution plans."
        ),
        "description": "Coordinates planning and execution activities",
        "system": "Planning & Execution"
    },
    {
        "name": "InitiativeGenerationAgent",
        "instructions": (
            "You are the Initiative Generation Agent for StratOS. You create strategic initiatives that bridge the gap "
            "between high-level strategy and executable actions. Your process includes: "
            "1) Analyzing strategic goals and current state, 2) Generating initiative proposals with clear objectives, "
            "3) Defining measurable success metrics, 4) Creating milestone-based timelines."
        ),
        "description": "Creates strategic initiatives and action plans",
        "system": "Planning & Execution"
    },
    {
        "name": "ResourceOptimizationAgent",
        "instructions": (
            "You are the Resource Optimization Agent for StratOS. You ensure optimal allocation of resources "
            "(people, budget, time) across all strategic initiatives. Your capabilities include: "
            "1) Resource capacity analysis, 2) Allocation optimization based on strategic priorities, "
            "3) Cost-benefit analysis for resource decisions, 4) Utilization tracking and recommendations."
        ),
        "description": "Optimizes resource allocation across initiatives",
        "system": "Planning & Execution"
    },
    {
        "name": "CanvasVisualizationAgent",
        "instructions": (
            "You are the Canvas Visualization Agent for StratOS. You help users create and manage visual representations "
            "of their strategy using the Strategic Canvas. Your capabilities include: "
            "1) Structuring text into visual nodes, 2) Suggesting meaningful connections between elements, "
            "3) Identifying themes and patterns in canvas layouts, 4) Processing voice commands for canvas manipulation."
        ),
        "description": "Manages visual strategic planning on canvas",
        "system": "Planning & Execution"
    },
    {
        "name": "AlignmentScoringAgent",
        "instructions": (
            "You are the Alignment Scoring Agent for StratOS. You evaluate how well initiatives and actions align "
            "with strategic objectives. Your assessment includes: 1) Scoring initiatives against strategic goals, "
            "2) Identifying alignment gaps and conflicts, 3) Recommending adjustments for better fit, "
            "4) Tracking alignment trends over time."
        ),
        "description": "Assesses strategic alignment of initiatives",
        "system": "Planning & Execution"
    },
    {
        "name": "ActionPlanningAgent",
        "instructions": (
            "You are the Action Planning Agent for StratOS. You transform strategic initiatives into detailed, "
            "executable action plans. Your planning includes: 1) Task breakdown structures, "
            "2) Timeline creation with dependencies, 3) Responsibility assignment (RACI), "
            "4) Progress tracking mechanisms."
        ),
        "description": "Creates detailed execution plans for initiatives",
        "system": "Planning & Execution"
    }
]

# Deploy agents
deployed_agents = []
failed_agents = []

print(f"\n=== Deploying {len(agents_to_deploy)} StratOS Agents ===\n")

for i, agent_config in enumerate(agents_to_deploy, 1):
    print(f"[{i}/{len(agents_to_deploy)}] Deploying {agent_config['name']} ({agent_config['system']})...")
    
    try:
        # Check if assistant already exists
        existing_assistants = client.beta.assistants.list()
        existing = None
        for assistant in existing_assistants.data:
            if assistant.name == agent_config['name']:
                existing = assistant
                break
        
        if existing:
            print(f"    ✓ Agent already exists with ID: {existing.id}")
            deployed_agents.append({
                "name": agent_config['name'],
                "id": existing.id,
                "system": agent_config['system'],
                "status": "existing"
            })
        else:
            # Create new assistant
            assistant = client.beta.assistants.create(
                name=agent_config['name'],
                instructions=agent_config['instructions'],
                description=agent_config['description'],
                model="gpt-35-turbo",
                metadata={
                    "system": agent_config['system'],
                    "created_by": "StratOS Deployment Script",
                    "created_at": datetime.now().isoformat()
                }
            )
            print(f"    ✓ Successfully created with ID: {assistant.id}")
            deployed_agents.append({
                "name": agent_config['name'],
                "id": assistant.id,
                "system": agent_config['system'],
                "status": "created"
            })
            
    except Exception as e:
        print(f"    ✗ Failed to deploy: {e}")
        failed_agents.append({
            "name": agent_config['name'],
            "system": agent_config['system'],
            "error": str(e)
        })

# Summary
print(f"\n{'='*60}")
print(f"DEPLOYMENT SUMMARY")
print(f"{'='*60}")
print(f"Total agents: {len(agents_to_deploy)}")
print(f"Successfully deployed: {len(deployed_agents)}")
print(f"Failed: {len(failed_agents)}")

# Group by system
systems = {}
for agent in deployed_agents:
    system = agent['system']
    if system not in systems:
        systems[system] = []
    systems[system].append(agent)

print(f"\nDeployed Agents by System:")
for system, agents in systems.items():
    print(f"\n{system} ({len(agents)} agents):")
    for agent in agents:
        status = "✓" if agent['status'] == 'created' else "•"
        print(f"  {status} {agent['name']}: {agent['id']}")

if failed_agents:
    print(f"\nFailed Deployments:")
    for agent in failed_agents:
        print(f"  ✗ {agent['name']} ({agent['system']}): {agent['error']}")

# Save deployment information
deployment_info = {
    "deployment_time": datetime.now().isoformat(),
    "deployment_type": "azure_openai_assistants",
    "endpoint": "https://sk-multi-agent-openai.openai.azure.com/",
    "model": "gpt-35-turbo",
    "total_agents": len(agents_to_deploy),
    "deployed_count": len(deployed_agents),
    "failed_count": len(failed_agents),
    "deployed_agents": {agent['name']: agent['id'] for agent in deployed_agents},
    "failed_agents": failed_agents,
    "agents_by_system": systems
}

deployment_file = os.path.join(backend_dir, "deployment_configs", "stratos_assistants_deployment.json")
os.makedirs(os.path.dirname(deployment_file), exist_ok=True)

with open(deployment_file, "w") as f:
    json.dump(deployment_info, f, indent=2)

print(f"\n✓ Deployment info saved to: deployment_configs/stratos_assistants_deployment.json")
print(f"\n{'='*60}")
print("DEPLOYMENT COMPLETE!")
print(f"{'='*60}")
print(f"\nAll {len(deployed_agents)} StratOS agents are now available as Azure OpenAI Assistants.")
print("You can interact with them using the Azure OpenAI API or through the StratOS backend.")
print("\nNext steps:")
print("1. Update the FastAPI backend to use these assistant IDs")
print("2. Test agent interactions through the API")
print("3. Configure Connected Agents for multi-agent orchestration")