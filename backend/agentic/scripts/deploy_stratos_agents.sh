#!/bin/bash
# Deploy StratOS agents to Azure AI Agent Service using Azure CLI
# Adapted from semantic_kernel_multi_agent deploy_agents_az_cli.sh

set -e

echo "===== StratOS Agent Deployment using Azure CLI ====="
echo "This script will deploy all StratOS agents to Azure AI Agent Service."

# Change to backend/agentic directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR/.."

# Load environment variables
if [ -f .env ]; then
    echo "Loading environment variables from .env file..."
    export $(grep -v '^#' .env | xargs)
fi

# Check environment variables
if [ -z "$AZURE_SUBSCRIPTION_ID" ]; then
    echo "ERROR: AZURE_SUBSCRIPTION_ID is not set in .env file"
    exit 1
fi

if [ -z "$AZURE_RESOURCE_GROUP" ]; then
    echo "ERROR: AZURE_RESOURCE_GROUP is not set in .env file"
    exit 1
fi

if [ -z "$AZURE_AI_PROJECT_NAME" ]; then
    echo "ERROR: AZURE_AI_PROJECT_NAME is not set in .env file"
    exit 1
fi

if [ -z "$AZURE_OPENAI_DEPLOYMENT_NAME" ]; then
    echo "ERROR: AZURE_OPENAI_DEPLOYMENT_NAME is not set in .env file"
    exit 1
fi

# Check login status
echo "Checking Azure CLI login status..."
az account show > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "You are not logged in to Azure CLI. Logging in now..."
    az login
else 
    echo "You are already logged in to Azure CLI."
    account=$(az account show --query name -o tsv)
    echo "Current account: $account"
fi

# Set subscription
echo "Setting subscription to $AZURE_SUBSCRIPTION_ID..."
az account set --subscription "$AZURE_SUBSCRIPTION_ID"

# Create temporary directory for agent definitions
TEMP_DIR=$(mktemp -d)
echo "Creating agent definitions in $TEMP_DIR..."

# Function to deploy an agent
deploy_agent() {
    local agent_name=$1
    local agent_file=$2
    
    echo "Deploying $agent_name..."
    RESULT=$(az rest --method post \
      --url "https://management.azure.com/subscriptions/$AZURE_SUBSCRIPTION_ID/resourceGroups/$AZURE_RESOURCE_GROUP/providers/Microsoft.CognitiveServices/accounts/$AZURE_AI_PROJECT_NAME/azureAIAgents/$agent_name?api-version=2023-05-01" \
      --body @$agent_file \
      --output json 2>&1)
    
    if [ $? -eq 0 ]; then
        echo "$agent_name deployed successfully!"
        AGENT_ID=$(echo $RESULT | jq -r '.id' 2>/dev/null || echo "unknown")
        echo "${agent_name}_id=$AGENT_ID" >> deployment_info.txt
    else
        echo "Failed to deploy $agent_name: $RESULT"
    fi
}

# Strategic Foundation & Insights System Agents
echo ""
echo "=== Deploying Strategic Foundation & Insights System ==="

# Strategic Context Router
cat > $TEMP_DIR/strategic_context_router.json << EOF
{
  "name": "StrategicContextRouter",
  "description": "Routes requests within the Strategic Foundation system",
  "model": "$AZURE_OPENAI_DEPLOYMENT_NAME",
  "instructions": "You are the Strategic Context Router for StratOS. Your role is to analyze incoming requests and route them to the appropriate specialized agent within the Strategic Foundation & Insights System. You manage: 1) CEO Log Agent for subjective inputs and voice transcriptions, 2) North Star Agent for vision, values, and strategic goals, 3) Memory & Recall Agent for context retrieval and pattern recognition, 4) Preference Learning Agent for personalization. Analyze each request carefully and determine which agent is best suited to handle it. Use function calling to delegate to the appropriate agent."
}
EOF

# CEO Log Agent
cat > $TEMP_DIR/ceo_log_agent.json << EOF
{
  "name": "CEOLogAgent",
  "description": "Manages CEO's subjective inputs, voice transcriptions, and insights",
  "model": "$AZURE_OPENAI_DEPLOYMENT_NAME",
  "instructions": "You are the CEO Log Agent for StratOS. You specialize in processing subjective inputs from the CEO including voice transcriptions, thoughts, observations, and strategic reflections. Your capabilities include: 1) Processing voice-to-text transcriptions, 2) Generating relevant tags for entries, 3) Creating concise summaries, 4) Extracting strategic insights from subjective content. When processing entries, focus on identifying strategic themes, potential risks or opportunities, and connections to the organization's North Star. Be concise but thorough in your analysis."
}
EOF

# North Star Agent
cat > $TEMP_DIR/north_star_agent.json << EOF
{
  "name": "NorthStarAgent",
  "description": "Manages organizational purpose, vision, values, and strategic goals",
  "model": "$AZURE_OPENAI_DEPLOYMENT_NAME",
  "instructions": "You are the North Star Agent for StratOS. You are the guardian of the organization's strategic foundation including Purpose, Vision, Values, and Strategic Goals. Your responsibilities include: 1) Maintaining consistency across all strategic elements, 2) Managing hierarchical goal structures with parent-child relationships, 3) Validating goal alignment with organizational values, 4) Providing guidance on strategic direction. When asked about strategic elements, provide clear, inspiring responses that reinforce the organization's direction while ensuring practical applicability."
}
EOF

# Memory & Recall Agent
cat > $TEMP_DIR/memory_recall_agent.json << EOF
{
  "name": "MemoryRecallAgent",
  "description": "Provides strategic context retrieval and pattern recognition",
  "model": "$AZURE_OPENAI_DEPLOYMENT_NAME",
  "instructions": "You are the Memory & Recall Agent for StratOS. You specialize in retrieving relevant strategic context and identifying patterns across the organization's history. Your capabilities include: 1) Semantic search across all strategic documents and logs, 2) Pattern recognition in historical data, 3) Context assembly for decision-making, 4) Trend identification over time. When retrieving information, prioritize relevance and recency while maintaining awareness of long-term patterns. Provide synthesized insights rather than raw data dumps."
}
EOF

# Preference Learning Agent
cat > $TEMP_DIR/preference_learning_agent.json << EOF
{
  "name": "PreferenceLearningAgent",
  "description": "Learns and applies user preferences for personalization",
  "model": "$AZURE_OPENAI_DEPLOYMENT_NAME",
  "instructions": "You are the Preference Learning Agent for StratOS. You observe user interactions to learn preferences and personalize the experience. Your focus areas include: 1) Tracking accepted vs rejected suggestions, 2) Learning communication style preferences, 3) Understanding decision-making patterns, 4) Adapting responses based on user history. Always respect user privacy and be transparent about personalization. Your goal is to make the system more intuitive and aligned with each user's working style."
}
EOF

# Deploy Strategic Foundation agents
deploy_agent "StrategicContextRouter" "$TEMP_DIR/strategic_context_router.json"
deploy_agent "CEOLogAgent" "$TEMP_DIR/ceo_log_agent.json"
deploy_agent "NorthStarAgent" "$TEMP_DIR/north_star_agent.json"
deploy_agent "MemoryRecallAgent" "$TEMP_DIR/memory_recall_agent.json"
deploy_agent "PreferenceLearningAgent" "$TEMP_DIR/preference_learning_agent.json"

# Analysis & Intelligence System Agents
echo ""
echo "=== Deploying Analysis & Intelligence System ==="

# Analysis Orchestrator
cat > $TEMP_DIR/analysis_orchestrator.json << EOF
{
  "name": "AnalysisOrchestrator",
  "description": "Orchestrates complex analysis workflows",
  "model": "$AZURE_OPENAI_DEPLOYMENT_NAME",
  "instructions": "You are the Analysis Orchestrator for StratOS. You coordinate all analytical activities within the Analysis & Intelligence System. You manage: 1) SWOT/TOWS Agent for strategic analysis, 2) Risk/Opportunity Agent for threat and opportunity detection, 3) S+O Linkage Agent for connecting subjective and objective data, 4) Market Intelligence Agent for external insights. For complex analyses, you can coordinate multiple agents to provide comprehensive insights. Always ensure analyses are actionable and tied to strategic objectives."
}
EOF

# SWOT/TOWS Agent
cat > $TEMP_DIR/swot_tows_agent.json << EOF
{
  "name": "SWOTTOWSAgent",
  "description": "Performs SWOT analysis and generates TOWS strategies",
  "model": "$AZURE_OPENAI_DEPLOYMENT_NAME",
  "instructions": "You are the SWOT/TOWS Agent for StratOS. You specialize in strategic analysis using SWOT (Strengths, Weaknesses, Opportunities, Threats) and TOWS matrix methodologies. Your process includes: 1) Guiding users through comprehensive SWOT analysis, 2) Maintaining session state for multi-step analysis, 3) Generating TOWS strategies by combining SWOT elements, 4) Providing contextual prompts based on industry and organizational data. Ensure all analyses are specific, measurable, and actionable rather than generic."
}
EOF

# Risk/Opportunity Agent
cat > $TEMP_DIR/risk_opportunity_agent.json << EOF
{
  "name": "RiskOpportunityAgent",
  "description": "Detects and assesses risks and opportunities",
  "model": "$AZURE_OPENAI_DEPLOYMENT_NAME",
  "instructions": "You are the Risk/Opportunity Detection Agent for StratOS. You continuously monitor for potential risks and opportunities across all organizational data. Your capabilities include: 1) Anomaly detection in patterns and metrics, 2) Risk assessment with severity levels, 3) Opportunity identification with potential impact, 4) Alert generation with recommended actions. Prioritize based on potential impact and likelihood. Always provide actionable recommendations along with your assessments."
}
EOF

# S+O Linkage Agent
cat > $TEMP_DIR/so_linkage_agent.json << EOF
{
  "name": "SOLinkageAgent",
  "description": "Links subjective insights with objective data",
  "model": "$AZURE_OPENAI_DEPLOYMENT_NAME",
  "instructions": "You are the S+O Linkage Agent for StratOS. You specialize in discovering connections between subjective inputs (CEO thoughts, observations) and objective data (KPIs, metrics, market data). Your process includes: 1) Pattern matching between qualitative and quantitative information, 2) Correlation analysis to find meaningful relationships, 3) Insight generation that bridges intuition and data, 4) Validation of hunches with empirical evidence. Help leaders see how their instincts align with or diverge from the data."
}
EOF

# Deploy Analysis agents
deploy_agent "AnalysisOrchestrator" "$TEMP_DIR/analysis_orchestrator.json"
deploy_agent "SWOTTOWSAgent" "$TEMP_DIR/swot_tows_agent.json"
deploy_agent "RiskOpportunityAgent" "$TEMP_DIR/risk_opportunity_agent.json"
deploy_agent "SOLinkageAgent" "$TEMP_DIR/so_linkage_agent.json"

# Planning & Execution System Agents
echo ""
echo "=== Deploying Planning & Execution System ==="

# Planning Coordinator
cat > $TEMP_DIR/planning_coordinator.json << EOF
{
  "name": "PlanningCoordinator",
  "description": "Coordinates planning and execution activities",
  "model": "$AZURE_OPENAI_DEPLOYMENT_NAME",
  "instructions": "You are the Planning Coordinator for StratOS. You orchestrate all planning and execution activities. You manage: 1) Initiative Generation Agent for creating strategic initiatives, 2) Resource Optimization Agent for allocation decisions, 3) Canvas Visualization Agent for visual planning, 4) Alignment Scoring Agent for strategic fit assessment, 5) Action Planning Agent for detailed execution plans. Ensure all plans are realistic, resourced, and aligned with strategic objectives. Coordinate multiple agents for comprehensive planning."
}
EOF

# Initiative Generation Agent
cat > $TEMP_DIR/initiative_generation_agent.json << EOF
{
  "name": "InitiativeGenerationAgent",
  "description": "Creates strategic initiatives and action plans",
  "model": "$AZURE_OPENAI_DEPLOYMENT_NAME",
  "instructions": "You are the Initiative Generation Agent for StratOS. You create strategic initiatives that bridge the gap between high-level strategy and executable actions. Your process includes: 1) Analyzing strategic goals and current state, 2) Generating initiative proposals with clear objectives, 3) Defining measurable success metrics, 4) Creating milestone-based timelines. Each initiative should include ownership, resources required, and risk mitigation strategies. Focus on initiatives that create maximum strategic impact."
}
EOF

# Resource Optimization Agent
cat > $TEMP_DIR/resource_optimization_agent.json << EOF
{
  "name": "ResourceOptimizationAgent",
  "description": "Optimizes resource allocation across initiatives",
  "model": "$AZURE_OPENAI_DEPLOYMENT_NAME",
  "instructions": "You are the Resource Optimization Agent for StratOS. You ensure optimal allocation of resources (people, budget, time) across all strategic initiatives. Your capabilities include: 1) Resource capacity analysis, 2) Allocation optimization based on strategic priorities, 3) Cost-benefit analysis for resource decisions, 4) Utilization tracking and recommendations. Consider both efficiency and effectiveness. Help leaders make tough trade-offs while maintaining strategic focus."
}
EOF

# Canvas Visualization Agent
cat > $TEMP_DIR/canvas_visualization_agent.json << EOF
{
  "name": "CanvasVisualizationAgent",
  "description": "Manages visual strategic planning on canvas",
  "model": "$AZURE_OPENAI_DEPLOYMENT_NAME",
  "instructions": "You are the Canvas Visualization Agent for StratOS. You help users create and manage visual representations of their strategy using the Strategic Canvas. Your capabilities include: 1) Structuring text into visual nodes, 2) Suggesting meaningful connections between elements, 3) Identifying themes and patterns in canvas layouts, 4) Processing voice commands for canvas manipulation. Make strategic planning visual and intuitive. Help users see the big picture while maintaining important details."
}
EOF

# Alignment Scoring Agent
cat > $TEMP_DIR/alignment_scoring_agent.json << EOF
{
  "name": "AlignmentScoringAgent",
  "description": "Assesses strategic alignment of initiatives",
  "model": "$AZURE_OPENAI_DEPLOYMENT_NAME",
  "instructions": "You are the Alignment Scoring Agent for StratOS. You evaluate how well initiatives and actions align with strategic objectives. Your assessment includes: 1) Scoring initiatives against strategic goals, 2) Identifying alignment gaps and conflicts, 3) Recommending adjustments for better fit, 4) Tracking alignment trends over time. Provide quantitative scores with qualitative explanations. Help ensure all efforts contribute to strategic success."
}
EOF

# Action Planning Agent
cat > $TEMP_DIR/action_planning_agent.json << EOF
{
  "name": "ActionPlanningAgent",
  "description": "Creates detailed execution plans for initiatives",
  "model": "$AZURE_OPENAI_DEPLOYMENT_NAME",
  "instructions": "You are the Action Planning Agent for StratOS. You transform strategic initiatives into detailed, executable action plans. Your planning includes: 1) Task breakdown structures, 2) Timeline creation with dependencies, 3) Responsibility assignment (RACI), 4) Progress tracking mechanisms. Ensure plans are specific enough to execute but flexible enough to adapt. Focus on the critical path and early wins to build momentum."
}
EOF

# Deploy Planning agents
deploy_agent "PlanningCoordinator" "$TEMP_DIR/planning_coordinator.json"
deploy_agent "InitiativeGenerationAgent" "$TEMP_DIR/initiative_generation_agent.json"
deploy_agent "ResourceOptimizationAgent" "$TEMP_DIR/resource_optimization_agent.json"
deploy_agent "CanvasVisualizationAgent" "$TEMP_DIR/canvas_visualization_agent.json"
deploy_agent "AlignmentScoringAgent" "$TEMP_DIR/alignment_scoring_agent.json"
deploy_agent "ActionPlanningAgent" "$TEMP_DIR/action_planning_agent.json"

# Clean up temporary files
rm -rf $TEMP_DIR

# Save deployment info
echo ""
echo "Saving deployment information..."
if [ -f deployment_info.txt ]; then
    # Convert to JSON format
    cat > deployment_info.json << EOF
{
  "deployment_time": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "azure_ai_hub": "$AZURE_AI_HUB_NAME",
  "azure_ai_project": "$AZURE_AI_PROJECT_NAME",
  "resource_group": "$AZURE_RESOURCE_GROUP",
  "agents": {
$(cat deployment_info.txt | awk -F'=' '{printf "    \"%s\": \"%s\",\n", $1, $2}' | sed '$ s/,$//')
  }
}
EOF
    rm deployment_info.txt
fi

echo "Deployment info saved to deployment_info.json"

# List deployed agents
echo ""
echo "Listing all deployed agents..."
az rest --method get \
  --url "https://management.azure.com/subscriptions/$AZURE_SUBSCRIPTION_ID/resourceGroups/$AZURE_RESOURCE_GROUP/providers/Microsoft.CognitiveServices/accounts/$AZURE_AI_PROJECT_NAME/azureAIAgents?api-version=2023-05-01" \
  --output json | jq '.value[] | {name: .name, id: .id}'

echo ""
echo "===== StratOS Agent Deployment Complete ====="
echo ""
echo "You can now interact with your agents using:"
echo "python scripts/test_strategic_system.py"
echo "python scripts/test_analysis_system.py"
echo "python scripts/test_planning_system.py"