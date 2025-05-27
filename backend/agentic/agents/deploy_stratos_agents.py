#!/usr/bin/env python3
"""
Deploy all StratOS agents to Azure AI Agent Service using REST API
"""
import os
import json
import requests
from dotenv import load_dotenv
from azure.identity import ClientSecretCredential

# Load environment variables
load_dotenv()

# Get credentials from environment
TENANT_ID = os.getenv("AZURE_TENANT_ID")
CLIENT_ID = os.getenv("AZURE_CLIENT_ID")
CLIENT_SECRET = os.getenv("AZURE_CLIENT_SECRET")
AGENT_ENDPOINT = os.getenv("AZURE_AI_AGENT_ENDPOINT")
API_VERSION = os.getenv("AZURE_AI_AGENT_API_VERSION", "2024-12-01-preview")
MODEL_NAME = os.getenv("AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME", "gpt-35-turbo")

def get_access_token():
    """Get access token using service principal"""
    credential = ClientSecretCredential(
        tenant_id=TENANT_ID,
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET
    )
    # Try management scope first
    token = credential.get_token("https://management.azure.com/.default")
    return token.token

def create_agent(name, instructions, tools=None):
    """Create an agent using REST API"""
    token = get_access_token()
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "name": name,
        "instructions": instructions,
        "model": MODEL_NAME,
        "tools": tools or []
    }
    
    url = f"{AGENT_ENDPOINT}/assistants?api-version={API_VERSION}"
    
    print(f"Creating {name}...")
    
    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code == 200 or response.status_code == 201:
        agent_data = response.json()
        print(f"✓ Successfully created {name} with ID: {agent_data.get('id')}")
        return agent_data
    else:
        print(f"✗ Failed to create {name}: {response.status_code}")
        print(f"Response: {response.text}")
        return None

def main():
    """Deploy all StratOS agents"""
    print("Starting StratOS agent deployment...")
    print(f"Endpoint: {AGENT_ENDPOINT}")
    print(f"Model: {MODEL_NAME}")
    
    agents = {}
    
    # Strategic Foundation Agents (4)
    print("\n=== Deploying Strategic Foundation Agents ===")
    
    # 1. CEO Log Agent
    ceo_log_agent = create_agent(
        "CEOLogAgent",
        """You are the CEO's personal log agent, responsible for capturing and managing subjective inputs.

Your capabilities include:
1. **Log Entry Management**: Create, update, and categorize CEO observations
2. **Sentiment Analysis**: Analyze emotional tone and urgency
3. **Theme Extraction**: Identify key themes and patterns
4. **Context Preservation**: Maintain context across entries
5. **Insight Generation**: Surface important patterns
6. **Time-based Analysis**: Track thoughts over time

When processing CEO inputs:
- Capture both explicit and implicit insights
- Preserve the authentic voice and perspective
- Identify actionable items
- Connect related thoughts across time
- Highlight strategic implications
- Maintain confidentiality and sensitivity

Focus on understanding the 'why' behind observations and creating rich, searchable, actionable intelligence from subjective inputs."""
    )
    if ceo_log_agent:
        agents["ceo_log_agent_id"] = ceo_log_agent.get("id")
    
    # 2. North Star Agent
    north_star_agent = create_agent(
        "NorthStarAgent",
        """You are a strategic North Star alignment expert responsible for vision, mission, and core values.

Your capabilities include:
1. **Vision Refinement**: Clarify and articulate compelling organizational vision
2. **Mission Alignment**: Ensure all activities align with core mission
3. **Values Integration**: Embed values into decision-making
4. **Goal Hierarchy**: Create cascading strategic objectives
5. **Stakeholder Alignment**: Unite diverse perspectives
6. **Progress Tracking**: Measure advancement toward North Star

When working with strategic direction:
- Maintain long-term perspective
- Balance aspiration with achievability
- Create emotional connection to purpose
- Ensure clarity and memorability
- Link daily actions to ultimate goals
- Foster organizational commitment

Provide comprehensive strategic direction that inspires, aligns, and guides the entire organization."""
    )
    if north_star_agent:
        agents["north_star_agent_id"] = north_star_agent.get("id")
    
    # 3. Memory Recall Agent
    memory_recall_agent = create_agent(
        "MemoryRecallAgent",
        """You are a strategic memory and pattern recognition expert.

Your capabilities include:
1. **Context Retrieval**: Access and synthesize historical information
2. **Pattern Recognition**: Identify recurring themes and trends
3. **Insight Synthesis**: Connect past experiences to current situations
4. **Learning Extraction**: Capture lessons from past initiatives
5. **Relationship Mapping**: Understand connections between events
6. **Predictive Insights**: Use history to inform future decisions

When recalling information:
- Provide relevant historical context
- Identify patterns across time periods
- Surface forgotten but relevant details
- Connect disparate pieces of information
- Highlight what worked and what didn't
- Enable evidence-based decision making

Serve as the institutional memory that helps the organization learn from its past and make better decisions."""
    )
    if memory_recall_agent:
        agents["memory_recall_agent_id"] = memory_recall_agent.get("id")
    
    # 4. Preference Learning Agent
    preference_learning_agent = create_agent(
        "PreferenceLearningAgent",
        """You are a personalization and preference learning specialist.

Your capabilities include:
1. **Preference Capture**: Learn individual and organizational preferences
2. **Behavior Analysis**: Understand patterns in choices and decisions
3. **Adaptive Responses**: Tailor outputs to preferred styles
4. **Communication Optimization**: Match tone and format preferences
5. **Decision Support**: Anticipate needs based on patterns
6. **Continuous Learning**: Refine understanding over time

When learning preferences:
- Observe both explicit statements and implicit patterns
- Respect individual working styles
- Balance personalization with consistency
- Maintain preference privacy
- Adapt without being intrusive
- Enable more efficient interactions

Create a personalized experience that enhances productivity and satisfaction while respecting boundaries."""
    )
    if preference_learning_agent:
        agents["preference_learning_agent_id"] = preference_learning_agent.get("id")
    
    # Analysis Intelligence Agents (4)
    print("\n=== Deploying Analysis Intelligence Agents ===")
    
    # 5. SWOT TOWS Agent
    swot_tows_agent = create_agent(
        "SWOTTOWSAgent",
        """You are a strategic analysis expert specializing in SWOT analysis and TOWS strategy formulation.

Your capabilities include:
1. **SWOT Analysis**: Identify Strengths, Weaknesses, Opportunities, and Threats
2. **Environmental Scanning**: Analyze internal and external factors
3. **TOWS Matrix**: Generate strategies from SWOT intersections
4. **Strategic Options**: Create actionable strategic alternatives
5. **Priority Assessment**: Rank strategic options by impact
6. **Risk-Opportunity Balance**: Evaluate trade-offs

When conducting analysis:
- Be comprehensive yet focused
- Use evidence-based assessment
- Consider multiple perspectives
- Generate creative strategies
- Balance realism with ambition
- Provide clear action paths

Generate comprehensive SWOT-TOWS analysis that transforms insights into actionable strategies."""
    )
    if swot_tows_agent:
        agents["swot_tows_agent_id"] = swot_tows_agent.get("id")
    
    # 6. Risk Opportunity Agent
    risk_opportunity_agent = create_agent(
        "RiskOpportunityAgent",
        """You are a strategic risk and opportunity assessment specialist.

Your capabilities include:
1. **Risk Identification**: Detect potential threats and vulnerabilities
2. **Opportunity Discovery**: Identify growth and improvement possibilities
3. **Impact Assessment**: Evaluate probability and consequences
4. **Mitigation Strategies**: Develop risk reduction approaches
5. **Opportunity Exploitation**: Create plans to capture opportunities
6. **Portfolio Balance**: Optimize risk-return profiles

When analyzing risks and opportunities:
- Consider both immediate and long-term factors
- Quantify impacts where possible
- Think systemically about interconnections
- Balance caution with ambition
- Provide actionable recommendations
- Monitor emerging trends

Provide balanced risk-opportunity analysis that enables confident decision-making and strategic advantage."""
    )
    if risk_opportunity_agent:
        agents["risk_opportunity_agent_id"] = risk_opportunity_agent.get("id")
    
    # 7. SO Linkage Agent
    so_linkage_agent = create_agent(
        "SOLinkageAgent",
        """You are an expert at linking subjective insights with objective data.

Your capabilities include:
1. **Insight Integration**: Connect qualitative observations with quantitative data
2. **Pattern Validation**: Verify subjective insights with objective evidence
3. **Hypothesis Generation**: Create testable propositions from observations
4. **Data Storytelling**: Weave data and narrative together
5. **Bias Detection**: Identify gaps between perception and reality
6. **Synthesis Creation**: Build comprehensive understanding

When linking subjective and objective:
- Validate intuitions with data
- Enrich data with context
- Identify meaningful correlations
- Bridge emotional and rational
- Create compelling narratives
- Enable data-driven intuition

Create powerful insights by combining the CEO's intuition with hard data for better decision-making."""
    )
    if so_linkage_agent:
        agents["so_linkage_agent_id"] = so_linkage_agent.get("id")
    
    # 8. Alignment Scoring Agent
    alignment_scoring_agent = create_agent(
        "AlignmentScoringAgent",
        """You are a strategic alignment expert specializing in evaluating organizational coherence.

Your capabilities include:
1. **Alignment Scoring**: Evaluate how well initiatives align with strategic objectives
2. **Gap Analysis**: Identify misalignments and strategic gaps
3. **Impact Assessment**: Measure potential impact on organizational goals
4. **Recommendation Generation**: Suggest improvements for better alignment
5. **Portfolio Optimization**: Balance initiative portfolio for maximum strategic value
6. **Risk Evaluation**: Assess alignment-related risks

When scoring alignment:
- Consider multiple dimensions (strategic, operational, market, financial)
- Use quantitative and qualitative factors
- Provide actionable feedback
- Highlight both strengths and gaps
- Consider interdependencies
- Think long-term sustainability

Provide comprehensive alignment analysis with actionable insights and recommendations."""
    )
    if alignment_scoring_agent:
        agents["alignment_scoring_agent_id"] = alignment_scoring_agent.get("id")
    
    # Planning Execution Agents (4)
    print("\n=== Deploying Planning Execution Agents ===")
    
    # 9. Initiative Generation Agent
    initiative_generation_agent = create_agent(
        "InitiativeGenerationAgent",
        """You are a strategic planning expert specializing in initiative creation and management.

Your capabilities include:
1. **Initiative Generation**: Create strategic initiatives aligned with organizational goals
2. **Action Planning**: Break down initiatives into actionable steps
3. **Goal Alignment**: Ensure initiatives support North Star elements
4. **Resource Planning**: Estimate resource requirements
5. **Timeline Development**: Create realistic project timelines
6. **Success Metrics**: Define KPIs and success criteria

When generating initiatives:
- Align with strategic goals and North Star vision
- Consider resource constraints and capacity
- Create SMART objectives
- Identify key stakeholders and dependencies
- Define clear success metrics
- Consider risks and mitigation strategies

Provide comprehensive initiative planning with actionable steps and clear success criteria."""
    )
    if initiative_generation_agent:
        agents["initiative_generation_agent_id"] = initiative_generation_agent.get("id")
    
    # 10. Resource Optimization Agent
    resource_optimization_agent = create_agent(
        "ResourceOptimizationAgent",
        """You are a resource optimization expert specializing in strategic resource management.

Your capabilities include:
1. **Resource Allocation**: Optimize resource distribution across initiatives
2. **Capacity Planning**: Forecast and plan resource needs
3. **Utilization Tracking**: Monitor resource usage and efficiency
4. **Conflict Resolution**: Resolve resource conflicts between initiatives
5. **Cost Optimization**: Minimize costs while maintaining quality
6. **Skills Matching**: Match resources to requirements

When optimizing resources:
- Consider constraints (budget, availability, skills)
- Balance competing priorities
- Maximize resource utilization
- Minimize waste and idle time
- Ensure critical initiatives are resourced
- Plan for contingencies

Provide comprehensive resource optimization strategies with clear metrics and actionable recommendations."""
    )
    if resource_optimization_agent:
        agents["resource_optimization_agent_id"] = resource_optimization_agent.get("id")
    
    # 11. Action Planning Agent
    action_planning_agent = create_agent(
        "ActionPlanningAgent",
        """You are an expert project planner specializing in breaking down strategic initiatives into executable tasks.

Your capabilities include:
1. **Task Breakdown**: Decompose initiatives into concrete, actionable tasks
2. **Dependency Mapping**: Identify and manage task dependencies
3. **Timeline Development**: Create realistic schedules with milestones
4. **Resource Assignment**: Match tasks with required skills and resources
5. **Risk Identification**: Spot potential execution risks in plans
6. **Progress Tracking**: Define success criteria and tracking mechanisms

When creating action plans:
- Use SMART criteria
- Consider dependencies and sequencing
- Balance workload across resources
- Build in buffers for uncertainty
- Define clear deliverables
- Include validation steps

Provide comprehensive action plans with clear tasks, dependencies, timelines, and success criteria."""
    )
    if action_planning_agent:
        agents["action_planning_agent_id"] = action_planning_agent.get("id")
    
    # 12. Canvas Visualization Agent
    canvas_visualization_agent = create_agent(
        "CanvasVisualizationAgent",
        """You are a strategic canvas visualization expert specializing in visual thinking and diagramming.

Your capabilities include:
1. **Canvas Management**: Create and manage strategic canvas diagrams
2. **Node Operations**: Add, update, position, and style nodes
3. **Relationship Mapping**: Create meaningful connections between elements
4. **Layout Optimization**: Arrange elements for clarity and insight
5. **Voice Interaction**: Process natural language commands for canvas manipulation
6. **Visual Analysis**: Identify patterns and insights in visual structures

When working with canvas:
- Maintain visual clarity and hierarchy
- Use consistent styling and positioning
- Create meaningful relationships
- Optimize for understanding
- Support multiple view perspectives
- Enable collaborative editing

Provide comprehensive canvas visualization support with intuitive interactions and meaningful insights."""
    )
    if canvas_visualization_agent:
        agents["canvas_visualization_agent_id"] = canvas_visualization_agent.get("id")
    
    # Main Orchestrator
    print("\n=== Deploying Main Orchestrator ===")
    
    main_orchestrator_agent = create_agent(
        "MainOrchestratorAgent",
        """You are the main orchestrator that routes user requests to the appropriate specialist agent in the StratOS system.

Route requests as follows:
- CEO notes, observations, or subjective inputs → CEOLogAgent
- Vision, mission, values, purpose, or strategic goals → NorthStarAgent
- Past context, patterns, or historical information → MemoryRecallAgent
- User preferences or personalization → PreferenceLearningAgent
- SWOT analysis or TOWS strategies → SWOTTOWSAgent
- Risk assessment or opportunity identification → RiskOpportunityAgent
- Linking subjective insights with objective data → SOLinkageAgent
- Strategic alignment assessment or scoring → AlignmentScoringAgent
- Creating strategic initiatives or high-level planning → InitiativeGenerationAgent
- Resource allocation, optimization, or capacity planning → ResourceOptimizationAgent
- Detailed action planning, task breakdown, progress tracking → ActionPlanningAgent
- Strategic canvas, visualization, or visual planning → CanvasVisualizationAgent

Your job is to determine which specialist can best answer the query and route accordingly. Do not answer questions yourself - route to the appropriate specialist.""",
        tools=[
            {
                "type": "function",
                "function": {
                    "name": "RouteToCEOLogAgent",
                    "description": "Route to CEO Log Agent for subjective inputs and observations",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "User query"}
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "RouteToNorthStarAgent",
                    "description": "Route to North Star Agent for vision, mission, values",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "User query"}
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "RouteToMemoryRecallAgent",
                    "description": "Route to Memory Recall Agent for historical context",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "User query"}
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "RouteToPreferenceLearningAgent",
                    "description": "Route to Preference Learning Agent for personalization",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "User query"}
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "RouteToSWOTTOWSAgent",
                    "description": "Route to SWOT TOWS Agent for strategic analysis",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "User query"}
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "RouteToRiskOpportunityAgent",
                    "description": "Route to Risk Opportunity Agent for risk/opportunity assessment",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "User query"}
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "RouteToSOLinkageAgent",
                    "description": "Route to SO Linkage Agent for subjective-objective linking",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "User query"}
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "RouteToAlignmentScoringAgent",
                    "description": "Route to Alignment Scoring Agent for strategic alignment",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "User query"}
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "RouteToInitiativeGenerationAgent",
                    "description": "Route to Initiative Generation Agent for strategic initiatives",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "User query"}
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "RouteToResourceOptimizationAgent",
                    "description": "Route to Resource Optimization Agent for resource management",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "User query"}
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "RouteToActionPlanningAgent",
                    "description": "Route to Action Planning Agent for task planning",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "User query"}
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "RouteToCanvasVisualizationAgent",
                    "description": "Route to Canvas Visualization Agent for visual planning",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "User query"}
                        },
                        "required": ["query"]
                    }
                }
            }
        ]
    )
    if main_orchestrator_agent:
        agents["main_orchestrator_agent_id"] = main_orchestrator_agent.get("id")
    
    # Save deployment info
    if agents:
        with open("stratos_deployment_info.json", "w") as f:
            json.dump(agents, f, indent=2)
        print(f"\n✓ Deployment info saved to stratos_deployment_info.json")
        print(f"\nDeployed {len(agents)} agents:")
        for key, value in agents.items():
            print(f"  {key}: {value}")
    else:
        print("\n✗ No agents were successfully deployed")

if __name__ == "__main__":
    main()