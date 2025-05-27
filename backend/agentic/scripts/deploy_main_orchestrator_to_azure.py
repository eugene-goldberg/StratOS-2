#!/usr/bin/env python3
"""
Deploy MainOrchestratorAgent to Azure AI Agent Service with connected_agent tools
for all 15 specialist agents.
"""

import asyncio
import os
import sys
import logging
from typing import List, Dict, Any
from datetime import datetime, timezone
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [%(funcName)s] %(message)s')
logger = logging.getLogger(__name__)

# Add parent directories to path
current_dir = os.path.dirname(os.path.abspath(__file__))
agentic_dir = os.path.dirname(current_dir)
sys.path.insert(0, agentic_dir)

# Load environment
env_path = os.path.join(agentic_dir, '.env')
logger.info(f"Loading .env from: {env_path}")
load_dotenv(env_path)

from azure.identity.aio import DefaultAzureCredential
from semantic_kernel.agents import AzureAIAgent, AzureAIAgentSettings

# Specialist agent configurations with their deployed IDs
SPECIALIST_AGENTS = [
    # Strategic Foundation & Insights System (5 agents)
    {
        "name": "CEOLogAgent",
        "agent_id": "asst_N5azTOnrhdlm4K9wC6i9OtHA",
        "description": "Handles CEO's subjective inputs, notes, observations, and concerns. Captures strategic thinking and decisions."
    },
    {
        "name": "NorthStarAgent",
        "agent_id": "asst_JRJqOxzgJGCAm6vT1JUxglJa",
        "description": "Manages Purpose, Vision, Values, and Strategic Goals. Defines the organization's direction and aspirations."
    },
    {
        "name": "InsightSynthesisAgent",
        "agent_id": "asst_s4BQq86uPMhXGt5rmIqUHj5M",
        "description": "Synthesizes insights from various data sources, identifies patterns, and generates strategic recommendations."
    },
    {
        "name": "CEOMemoryAgent",
        "agent_id": "asst_ZV2p9TPa2l6XASy0nzl6O1hb",
        "description": "Retrieves context, patterns, and historical information from CEO's memory. Recalls past decisions and learnings."
    },
    {
        "name": "CEOPreferenceLearningAgent",
        "agent_id": "asst_t3B2YUPgg9Fq9KS6fLQMASFX",
        "description": "Learns and tracks CEO's preferences, communication style, and decision patterns to provide personalized assistance."
    },
    
    # Analysis & Intelligence System (4 agents)
    {
        "name": "SWOTTOWSAgent",
        "agent_id": "asst_g6qgPv2Ke8YcJZ7qBnf7NLFP",
        "description": "Performs SWOT analysis and generates TOWS strategies. Analyzes strengths, weaknesses, opportunities, and threats."
    },
    {
        "name": "RiskOpportunityAgent",
        "agent_id": "asst_HYttqPOdNXlVC7NkgEXCq5MQ",
        "description": "Identifies and analyzes risks and opportunities. Provides risk mitigation strategies and opportunity exploitation plans."
    },
    {
        "name": "StrategicContextRouter",
        "agent_id": "asst_xo3fBCcBHNV0Fc7GUMSaVOVa",
        "description": "Routes strategic context and analysis requests to appropriate specialized agents. Coordinates analytical workflows."
    },
    {
        "name": "SOLinkageAgent",
        "agent_id": "asst_9xKPvtFVA70P5Y1AvdJ2Y69d",
        "description": "Links subjective insights to objective data. Connects CEO's observations with measurable outcomes and KPIs."
    },
    
    # Planning & Execution System (6 agents)
    {
        "name": "PlanningCoordinator",
        "agent_id": "asst_TJJvOiJzblHg17rV6ogI9pTR",
        "description": "Coordinates overall planning activities, ensures alignment between strategic goals and tactical plans."
    },
    {
        "name": "InitiativeGenerator",
        "agent_id": "asst_iWTKVDG4xrXja8xhSKq2QDAK",
        "description": "Generates strategic initiatives and action plans based on goals and analysis. Creates detailed implementation roadmaps."
    },
    {
        "name": "ResourceOptimizer",
        "agent_id": "asst_LCi9P7YMdeeKzN8nES8xgEUP",
        "description": "Optimizes resource allocation across initiatives. Manages budgets, human resources, and other organizational assets."
    },
    {
        "name": "TimelineStrategist",
        "agent_id": "asst_sWPe2cMx4eF2mqXVhVo7kFMq",
        "description": "Develops strategic timelines and schedules. Manages project timelines and milestone planning."
    },
    {
        "name": "DependencyMapper",
        "agent_id": "asst_kGQZGft8ItT0VjBvLtP1VhJd",
        "description": "Maps dependencies between initiatives, resources, and timelines. Identifies critical paths and bottlenecks."
    },
    {
        "name": "ExecutionTracker",
        "agent_id": "asst_M8fmaDQIdUCUeP6HM9x02FRX",
        "description": "Tracks execution progress of strategic initiatives. Monitors KPIs, milestones, and deliverables."
    }
]

def create_orchestrator_instructions() -> str:
    """Create comprehensive instructions for the MainOrchestratorAgent."""
    
    # Build agent descriptions for the prompt
    agent_descriptions = []
    for agent in SPECIALIST_AGENTS:
        agent_descriptions.append(f"- {agent['name']}: {agent['description']}")
    
    agent_list = "\n".join(agent_descriptions)
    
    instructions = f"""You are the Main Orchestrator for StratOS, a comprehensive strategy operating system. Your role is to analyze incoming requests and delegate them to the most appropriate specialized agent.

AVAILABLE SPECIALIST AGENTS:
{agent_list}

ROUTING APPROACH:
1. Analyze the user's request to understand their intent.
2. Based on the descriptions above and the routing guidelines below, identify which single specialized agent is best suited.
3. Call the appropriate specialist agent using the connected_agent tool.
4. Return the specialized agent's response to the user.

ROUTING GUIDELINES:
STRATEGIC FOUNDATION & INSIGHTS:
- For CEO notes, observations, strategic decisions, or log entries → Route to CEOLogAgent
- For questions about vision, mission, values, strategic goals → Route to NorthStarAgent
- For insight synthesis, pattern recognition, strategic recommendations → Route to InsightSynthesisAgent
- For retrieving past context, decisions, or patterns from memory → Route to CEOMemoryAgent
- For learning preferences, communication style, decision patterns → Route to CEOPreferenceLearningAgent

ANALYSIS & INTELLIGENCE:
- For SWOT analysis or TOWS strategy generation → Route to SWOTTOWSAgent
- For risk identification, analysis, or mitigation strategies → Route to RiskOpportunityAgent
- For opportunity identification or exploitation strategies → Route to RiskOpportunityAgent
- For routing strategic analysis requests → Route to StrategicContextRouter
- For linking subjective insights to objective data/KPIs → Route to SOLinkageAgent

PLANNING & EXECUTION:
- For overall planning coordination or alignment → Route to PlanningCoordinator
- For generating initiatives, action plans, or roadmaps → Route to InitiativeGenerator
- For resource optimization, allocation, or budgeting → Route to ResourceOptimizer
- For timeline development, scheduling, or milestones → Route to TimelineStrategist
- For dependency analysis or critical path identification → Route to DependencyMapper
- For tracking execution progress, KPIs, or deliverables → Route to ExecutionTracker

Do not try to answer questions yourself. Your primary function is to accurately route the request to the correct specialist agent. Always explain briefly which agent you are routing to and why before presenting its response.

When you receive a user request:
1. Identify the core need or intent
2. Select the most appropriate specialist agent based on the guidelines
3. Explain your routing decision briefly (e.g., "I'll route this to the CEOLogAgent to capture your strategic decision.")
4. Call the specialist agent and return its response"""
    
    return instructions

def create_connected_agent_tools() -> List[Dict[str, Any]]:
    """Create the connected_agent tool definitions for the orchestrator."""
    tools = []
    
    for agent in SPECIALIST_AGENTS:
        tool = {
            "type": "connected_agent",
            "connected_agent": {
                "assistant_id": agent["agent_id"]
            },
            "name": agent["name"],
            "description": agent["description"]
        }
        tools.append(tool)
    
    return tools

async def deploy_orchestrator():
    """Deploy the MainOrchestratorAgent with connected_agent tools."""
    logger.info("Starting deployment of MainOrchestratorAgent...")
    
    try:
        # Initialize credentials and settings
        credential = DefaultAzureCredential()
        settings = AzureAIAgentSettings()
        
        # Check settings
        if not settings.model_deployment_name:
            logger.error("AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME is not set")
            return None
            
        logger.info(f"Using endpoint: {settings.endpoint}")
        logger.info(f"Using model: {settings.model_deployment_name}")
        
        # Create client
        async with AzureAIAgent.create_client(credential=credential, settings=settings) as client:
            # Prepare orchestrator configuration
            orchestrator_name = "MainOrchestrator"
            orchestrator_instructions = create_orchestrator_instructions()
            tools = create_connected_agent_tools()
            
            logger.info(f"Deploying {orchestrator_name} with {len(tools)} connected_agent tools...")
            
            # Deploy the orchestrator
            assistant_response = await client.agents.create_agent(
                name=orchestrator_name,
                instructions=orchestrator_instructions,
                tools=tools,
                model=settings.model_deployment_name
            )
            
            agent_id = assistant_response.id
            logger.info(f"✅ Successfully deployed {orchestrator_name}")
            logger.info(f"   Agent ID: {agent_id}")
            logger.info(f"   Model: {assistant_response.model}")
            logger.info(f"   Tools: {len(assistant_response.tools)} connected agents")
            
            # Print tool summary
            logger.info("\nConnected Specialist Agents:")
            for i, tool in enumerate(assistant_response.tools):
                if hasattr(tool, 'connected_agent') and hasattr(tool.connected_agent, 'assistant_id'):
                    specialist_name = SPECIALIST_AGENTS[i]['name'] if i < len(SPECIALIST_AGENTS) else f"Tool {i}"
                    logger.info(f"   - {specialist_name}: {tool.connected_agent.assistant_id}")
            
            return agent_id
            
    except Exception as e:
        logger.error(f"Error deploying orchestrator: {str(e)}", exc_info=True)
        return None
    finally:
        await credential.close()

async def test_deployed_orchestrator(agent_id: str):
    """Test the deployed orchestrator with a sample request."""
    logger.info(f"\nTesting deployed orchestrator (ID: {agent_id})...")
    
    try:
        credential = DefaultAzureCredential()
        settings = AzureAIAgentSettings()
        
        async with AzureAIAgent.create_client(credential=credential, settings=settings) as client:
            # Get agent definition
            agent_def = await client.agents.get_agent(assistant_id=agent_id)
            sk_agent = AzureAIAgent(client=client, definition=agent_def)
            
            # Create thread
            thread_response = await client.agents.threads.create()
            thread_id = thread_response.id
            
            # Test request
            test_request = "I need to record a strategic decision about expanding into the Asian market"
            logger.info(f"\nTest Request: {test_request}")
            
            # Invoke orchestrator
            response = ""
            async for message in sk_agent.invoke(message=test_request, thread_id=thread_id):
                if hasattr(message, 'content') and message.content:
                    response += message.content
                elif isinstance(message, list) and message and hasattr(message[0], 'content'):
                    response += message[0].content
            
            logger.info(f"\nOrchestrator Response:")
            logger.info(response)
            
            # Cleanup
            await client.agents.threads.delete(thread_id=thread_id)
            
    except Exception as e:
        logger.error(f"Error testing orchestrator: {str(e)}", exc_info=True)
    finally:
        await credential.close()

async def main():
    """Main deployment function."""
    # Deploy orchestrator
    agent_id = await deploy_orchestrator()
    
    if agent_id:
        # Save the agent ID for reference
        logger.info(f"\n{'='*80}")
        logger.info("DEPLOYMENT SUCCESSFUL!")
        logger.info(f"{'='*80}")
        logger.info(f"MainOrchestratorAgent ID: {agent_id}")
        logger.info("\nTo interact with the orchestrator, run:")
        logger.info(f"python3 backend/agentic/scripts/interact_with_ai_project_agent.py")
        logger.info(f"Then enter the Agent ID: {agent_id}")
        
        # Test the orchestrator
        await test_deployed_orchestrator(agent_id)
    else:
        logger.error("Failed to deploy orchestrator")

if __name__ == "__main__":
    asyncio.run(main())