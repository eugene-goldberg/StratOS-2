#!/bin/bash
# Deploy StratOS agents to Azure AI Foundry using proper API endpoints
# This script creates agent configurations that can be deployed when the Agent Service SDK is available

set -e

echo "===== StratOS Agent Deployment Configuration ====="
echo "This script prepares agent configurations for Azure AI Foundry deployment."

# Change to backend/agentic directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR/.."

# Load environment variables
if [ -f .env ]; then
    echo "Loading environment variables from .env file..."
    export $(grep -v '^#' .env | xargs)
fi

# Create deployment configurations directory
DEPLOY_DIR="deployment_configs"
mkdir -p $DEPLOY_DIR

echo "Creating agent deployment configurations in $DEPLOY_DIR..."

# Function to create agent configuration
create_agent_config() {
    local agent_name=$1
    local agent_description=$2
    local agent_instructions=$3
    local agent_type=$4
    
    cat > $DEPLOY_DIR/${agent_name}.json << EOF
{
  "name": "$agent_name",
  "description": "$agent_description",
  "type": "$agent_type",
  "model": {
    "endpoint": "$AZURE_OPENAI_ENDPOINT",
    "deployment": "$AZURE_OPENAI_DEPLOYMENT_NAME",
    "api_key": "$AZURE_OPENAI_API_KEY"
  },
  "instructions": "$agent_instructions",
  "tools": [],
  "metadata": {
    "system": "stratos",
    "version": "1.0.0",
    "created": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
  }
}
EOF
    echo "Created configuration for $agent_name"
}

# Strategic Foundation & Insights System Agents
echo ""
echo "=== Creating Strategic Foundation & Insights System Configurations ==="

create_agent_config \
  "StrategicContextRouter" \
  "Routes requests within the Strategic Foundation system" \
  "You are the Strategic Context Router for StratOS. Your role is to analyze incoming requests and route them to the appropriate specialized agent within the Strategic Foundation & Insights System. You manage: 1) CEO Log Agent for subjective inputs and voice transcriptions, 2) North Star Agent for vision, values, and strategic goals, 3) Memory & Recall Agent for context retrieval and pattern recognition, 4) Preference Learning Agent for personalization. Analyze each request carefully and determine which agent is best suited to handle it." \
  "router"

create_agent_config \
  "CEOLogAgent" \
  "Manages CEO's subjective inputs, voice transcriptions, and insights" \
  "You are the CEO Log Agent for StratOS. You specialize in processing subjective inputs from the CEO including voice transcriptions, thoughts, observations, and strategic reflections. Your capabilities include: 1) Processing voice-to-text transcriptions, 2) Generating relevant tags for entries, 3) Creating concise summaries, 4) Extracting strategic insights from subjective content. When processing entries, focus on identifying strategic themes, potential risks or opportunities, and connections to the organization's North Star." \
  "specialist"

create_agent_config \
  "NorthStarAgent" \
  "Manages organizational purpose, vision, values, and strategic goals" \
  "You are the North Star Agent for StratOS. You are the guardian of the organization's strategic foundation including Purpose, Vision, Values, and Strategic Goals. Your responsibilities include: 1) Maintaining consistency across all strategic elements, 2) Managing hierarchical goal structures with parent-child relationships, 3) Validating goal alignment with organizational values, 4) Providing guidance on strategic direction." \
  "specialist"

create_agent_config \
  "MemoryRecallAgent" \
  "Provides strategic context retrieval and pattern recognition" \
  "You are the Memory & Recall Agent for StratOS. You specialize in retrieving relevant strategic context and identifying patterns across the organization's history. Your capabilities include: 1) Semantic search across all strategic documents and logs, 2) Pattern recognition in historical data, 3) Context assembly for decision-making, 4) Trend identification over time." \
  "specialist"

create_agent_config \
  "PreferenceLearningAgent" \
  "Learns and applies user preferences for personalization" \
  "You are the Preference Learning Agent for StratOS. You observe user interactions to learn preferences and personalize the experience. Your focus areas include: 1) Tracking accepted vs rejected suggestions, 2) Learning communication style preferences, 3) Understanding decision-making patterns, 4) Adapting responses based on user history." \
  "specialist"

# Analysis & Intelligence System Agents
echo ""
echo "=== Creating Analysis & Intelligence System Configurations ==="

create_agent_config \
  "AnalysisOrchestrator" \
  "Orchestrates complex analysis workflows" \
  "You are the Analysis Orchestrator for StratOS. You coordinate all analytical activities within the Analysis & Intelligence System. You manage: 1) SWOT/TOWS Agent for strategic analysis, 2) Risk/Opportunity Agent for threat and opportunity detection, 3) S+O Linkage Agent for connecting subjective and objective data. For complex analyses, you can coordinate multiple agents to provide comprehensive insights." \
  "router"

create_agent_config \
  "SWOTTOWSAgent" \
  "Performs SWOT analysis and generates TOWS strategies" \
  "You are the SWOT/TOWS Agent for StratOS. You specialize in strategic analysis using SWOT (Strengths, Weaknesses, Opportunities, Threats) and TOWS matrix methodologies. Your process includes: 1) Guiding users through comprehensive SWOT analysis, 2) Maintaining session state for multi-step analysis, 3) Generating TOWS strategies by combining SWOT elements, 4) Providing contextual prompts based on industry and organizational data." \
  "specialist"

create_agent_config \
  "RiskOpportunityAgent" \
  "Detects and assesses risks and opportunities" \
  "You are the Risk/Opportunity Detection Agent for StratOS. You continuously monitor for potential risks and opportunities across all organizational data. Your capabilities include: 1) Anomaly detection in patterns and metrics, 2) Risk assessment with severity levels, 3) Opportunity identification with potential impact, 4) Alert generation with recommended actions." \
  "specialist"

create_agent_config \
  "SOLinkageAgent" \
  "Links subjective insights with objective data" \
  "You are the S+O Linkage Agent for StratOS. You specialize in discovering connections between subjective inputs (CEO thoughts, observations) and objective data (KPIs, metrics, market data). Your process includes: 1) Pattern matching between qualitative and quantitative information, 2) Correlation analysis to find meaningful relationships, 3) Insight generation that bridges intuition and data." \
  "specialist"

# Planning & Execution System Agents
echo ""
echo "=== Creating Planning & Execution System Configurations ==="

create_agent_config \
  "PlanningCoordinator" \
  "Coordinates planning and execution activities" \
  "You are the Planning Coordinator for StratOS. You orchestrate all planning and execution activities. You manage: 1) Initiative Generation Agent for creating strategic initiatives, 2) Resource Optimization Agent for allocation decisions, 3) Canvas Visualization Agent for visual planning, 4) Alignment Scoring Agent for strategic fit assessment, 5) Action Planning Agent for detailed execution plans." \
  "router"

create_agent_config \
  "InitiativeGenerationAgent" \
  "Creates strategic initiatives and action plans" \
  "You are the Initiative Generation Agent for StratOS. You create strategic initiatives that bridge the gap between high-level strategy and executable actions. Your process includes: 1) Analyzing strategic goals and current state, 2) Generating initiative proposals with clear objectives, 3) Defining measurable success metrics, 4) Creating milestone-based timelines." \
  "specialist"

create_agent_config \
  "ResourceOptimizationAgent" \
  "Optimizes resource allocation across initiatives" \
  "You are the Resource Optimization Agent for StratOS. You ensure optimal allocation of resources (people, budget, time) across all strategic initiatives. Your capabilities include: 1) Resource capacity analysis, 2) Allocation optimization based on strategic priorities, 3) Cost-benefit analysis for resource decisions, 4) Utilization tracking and recommendations." \
  "specialist"

create_agent_config \
  "CanvasVisualizationAgent" \
  "Manages visual strategic planning on canvas" \
  "You are the Canvas Visualization Agent for StratOS. You help users create and manage visual representations of their strategy using the Strategic Canvas. Your capabilities include: 1) Structuring text into visual nodes, 2) Suggesting meaningful connections between elements, 3) Identifying themes and patterns in canvas layouts, 4) Processing voice commands for canvas manipulation." \
  "specialist"

create_agent_config \
  "AlignmentScoringAgent" \
  "Assesses strategic alignment of initiatives" \
  "You are the Alignment Scoring Agent for StratOS. You evaluate how well initiatives and actions align with strategic objectives. Your assessment includes: 1) Scoring initiatives against strategic goals, 2) Identifying alignment gaps and conflicts, 3) Recommending adjustments for better fit, 4) Tracking alignment trends over time." \
  "specialist"

create_agent_config \
  "ActionPlanningAgent" \
  "Creates detailed execution plans for initiatives" \
  "You are the Action Planning Agent for StratOS. You transform strategic initiatives into detailed, executable action plans. Your planning includes: 1) Task breakdown structures, 2) Timeline creation with dependencies, 3) Responsibility assignment (RACI), 4) Progress tracking mechanisms." \
  "specialist"

# Create deployment summary
cat > $DEPLOY_DIR/deployment_summary.json << EOF
{
  "deployment_name": "StratOS Multi-Agent System",
  "version": "1.0.0",
  "created": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "environment": {
    "azure_subscription": "$AZURE_SUBSCRIPTION_ID",
    "resource_group": "$AZURE_RESOURCE_GROUP",
    "ai_hub": "$AZURE_AI_HUB_NAME",
    "ai_project": "$AZURE_AI_PROJECT_NAME"
  },
  "systems": [
    {
      "name": "Strategic Foundation & Insights System",
      "agents": ["StrategicContextRouter", "CEOLogAgent", "NorthStarAgent", "MemoryRecallAgent", "PreferenceLearningAgent"]
    },
    {
      "name": "Analysis & Intelligence System",
      "agents": ["AnalysisOrchestrator", "SWOTTOWSAgent", "RiskOpportunityAgent", "SOLinkageAgent"]
    },
    {
      "name": "Planning & Execution System",
      "agents": ["PlanningCoordinator", "InitiativeGenerationAgent", "ResourceOptimizationAgent", "CanvasVisualizationAgent", "AlignmentScoringAgent", "ActionPlanningAgent"]
    }
  ],
  "total_agents": 15
}
EOF

echo ""
echo "===== Agent Configuration Complete ====="
echo ""
echo "Created configuration files for all 15 agents in: $DEPLOY_DIR/"
echo ""
echo "Next steps:"
echo "1. The agent configurations are ready for deployment"
echo "2. Use the Azure AI Foundry portal or SDK to deploy these agents"
echo "3. Update the FastAPI backend to connect to deployed agents"
echo ""
echo "Current Azure Resources:"
echo "  - OpenAI Endpoint: $AZURE_OPENAI_ENDPOINT"
echo "  - OpenAI Deployment: $AZURE_OPENAI_DEPLOYMENT_NAME"
echo "  - AI Hub: $AZURE_AI_HUB_NAME"
echo "  - AI Project: $AZURE_AI_PROJECT_NAME"
echo ""
echo "Note: The agents are fully implemented in the codebase and ready for deployment"
echo "      when the Azure AI Agent Service API becomes available for direct deployment."