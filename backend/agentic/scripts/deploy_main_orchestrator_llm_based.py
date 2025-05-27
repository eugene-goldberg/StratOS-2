#!/usr/bin/env python3
"""
Deploy Main Orchestrator to Azure AI Agent Service using LLM-based routing.
No hardcoded function tools - pure LLM understanding for routing decisions.
"""

import asyncio
import os
import sys
import json
import logging
from datetime import datetime, timezone
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [%(funcName)s] %(message)s')
logger = logging.getLogger(__name__)

# Add parent directories to path
current_dir = os.path.dirname(os.path.abspath(__file__))
agentic_dir = os.path.dirname(current_dir)
backend_dir = os.path.dirname(agentic_dir)
project_root = os.path.dirname(backend_dir)
sys.path.insert(0, project_root)

env_path = os.path.join(agentic_dir, '.env')
logger.info(f"Attempting to load .env file from: {env_path}")
if load_dotenv(env_path):
    logger.info(".env file loaded successfully.")

# Import required modules
try:
    from azure.identity.aio import DefaultAzureCredential
    from semantic_kernel.agents import AzureAIAgent, AzureAIAgentSettings
except ImportError as e:
    logger.error(f"Error importing required modules: {e}")
    sys.exit(1)

async def deploy_orchestrator():
    """Deploy the Main Orchestrator to Azure AI Agent Service with LLM-based routing."""
    
    try:
        # Check required environment variables
        settings = AzureAIAgentSettings()
        logger.info(f"Endpoint: {settings.endpoint}")
        logger.info(f"Model deployment: {settings.model_deployment_name}")
        
        # Create credential
        credential = DefaultAzureCredential()
        
        # Create client
        async with AzureAIAgent.create_client(credential=credential, settings=settings) as client:
            logger.info("Successfully connected to Azure AI Agent Service")
            
            # Define the orchestrator configuration with rich agent descriptions
            orchestrator_config = {
                "name": "MainOrchestrator",
                "instructions": (
                    "You are the Main Orchestrator for StratOS, a comprehensive strategy operating system. "
                    "Your role is to analyze incoming requests and determine which specialized agent should handle them.\n\n"
                    
                    "AVAILABLE SPECIALIST AGENTS:\n\n"
                    
                    "STRATEGIC FOUNDATION & INSIGHTS SYSTEM:\n"
                    "1. CEOLogAgent - Specialized in capturing and organizing CEO's thoughts, observations, strategic notes, "
                    "   concerns, ideas, and subjective inputs. Handles categorization of entries (strategic, operational, "
                    "   personal, market, team). Perfect for logging important decisions, observations, or thoughts.\n"
                    
                    "2. CEOMemoryAgent - Retrieves and recalls past CEO log entries, decisions, and strategic context. "
                    "   Can search through historical entries by date, category, or content. Use when user asks about "
                    "   'what did I say about...', 'my previous thoughts on...', or 'decisions from last quarter'.\n"
                    
                    "3. CEOPreferenceLearningAgent - Learns and tracks the CEO's preferences, patterns, and typical approaches "
                    "   to decision-making. Answers questions like 'what are my typical preferences for...', "
                    "   'how do I usually approach...', or personalization requests.\n"
                    
                    "4. NorthStarAgent - Manages the company's core strategic elements: Purpose, Vision, Mission, Values, "
                    "   and Strategic Goals. Handles questions about 'our north star metric', 'company vision', "
                    "   'strategic objectives', OKRs, and goal alignment.\n"
                    
                    "5. InsightSynthesisAgent - Synthesizes insights from multiple sources including strategic decisions, "
                    "   market analysis, and internal data. Use for requests like 'synthesize insights from...', "
                    "   'what patterns emerge from...', or 'key takeaways from our analysis'.\n\n"
                    
                    "ANALYSIS & INTELLIGENCE SYSTEM:\n"
                    "6. SWOTTOWSAgent - Performs comprehensive SWOT (Strengths, Weaknesses, Opportunities, Threats) analysis "
                    "   and generates TOWS strategies. Use for 'SWOT analysis', 'analyze our strengths and weaknesses', "
                    "   'strategic positioning', or 'TOWS matrix' requests.\n"
                    
                    "7. RiskOpportunityAgent - Dual-purpose agent that identifies and analyzes both risks AND opportunities. "
                    "   Handles 'identify risks', 'risk assessment', 'find opportunities', 'market opportunities', "
                    "   'potential threats', and impact analysis.\n"
                    
                    "8. StrategicContextRouter - Routes requests within the strategic foundation domain when the specific "
                    "   sub-agent isn't clear. Use for general strategic questions that need further routing.\n"
                    
                    "9. SOLinkageAgent - Links subjective insights (like CEO observations) with objective data. "
                    "   Correlates qualitative insights with quantitative metrics. Use for 'link my observation about...', "
                    "   'connect team morale to performance', or 'validate insight with data'.\n\n"
                    
                    "PLANNING & EXECUTION SYSTEM:\n"
                    "10. PlanningCoordinator - Coordinates complex planning activities across multiple domains. "
                    "    Use for 'create a comprehensive plan', 'coordinate planning for...', or multi-faceted planning requests.\n"
                    
                    "11. InitiativeGenerator - Creates strategic initiatives and action plans based on analysis and goals. "
                    "    Handles 'generate initiatives', 'create action plan', 'strategic initiatives based on...', "
                    "    or 'how to achieve goal X'.\n"
                    
                    "12. ResourceOptimizer - Optimizes resource allocation including budget, personnel, time, and equipment. "
                    "    Handles 'optimize resources', 'resource allocation', 'capacity planning', or 'budget optimization'.\n"
                    
                    "13. TimelineStrategist - Creates strategic timelines and roadmaps for initiatives and projects. "
                    "    Use for 'create timeline', 'product roadmap', 'milestone planning', or 'delivery schedule'.\n"
                    
                    "14. DependencyMapper - Maps and analyzes dependencies between initiatives, projects, and resources. "
                    "    Handles 'dependency analysis', 'what depends on...', 'critical path', or 'interdependencies'.\n"
                    
                    "15. ExecutionTracker - Tracks execution progress of strategic initiatives and milestones. "
                    "    Use for 'track progress', 'execution status', 'milestone updates', or 'initiative tracking'.\n\n"
                    
                    "ROUTING APPROACH:\n"
                    "1. Carefully read and understand the user's request\n"
                    "2. Consider the intent and context of the request\n"
                    "3. Match the request to the most appropriate specialist agent based on their capabilities\n"
                    "4. If multiple agents could handle it, choose the most specific one\n"
                    "5. Provide your routing decision in this format:\n"
                    "   ROUTE TO: [AgentName]\n"
                    "   REASON: [Your detailed reasoning for choosing this agent]\n\n"
                    
                    "IMPORTANT: Use your understanding of language and context to make intelligent routing decisions. "
                    "Don't rely on keyword matching - understand the intent behind the request. Your response should ONLY "
                    "contain the routing decision in the specified format, nothing else."
                ),
                "description": "Primary orchestrator for StratOS using LLM-based intelligent routing"
            }
            
            # Create the orchestrator
            logger.info("Creating Main Orchestrator with LLM-based routing...")
            
            agent_definition = await client.agents.create_agent(
                model=settings.model_deployment_name,
                name=orchestrator_config['name'],
                instructions=orchestrator_config['instructions'],
                description=orchestrator_config['description']
            )
            
            logger.info(f"✅ Main Orchestrator created successfully!")
            logger.info(f"  ID: {agent_definition.id}")
            logger.info(f"  Name: {agent_definition.name}")
            logger.info(f"  Model: {agent_definition.model}")
            
            # Save deployment info
            deployment_config_path = os.path.join(agentic_dir, "deployment_configs", "main_orchestrator_deployment.json")
            os.makedirs(os.path.dirname(deployment_config_path), exist_ok=True)
            
            deployment_info = {
                "agent_name": "MainOrchestrator",
                "agent_id": agent_definition.id,
                "deployment_time": datetime.now(timezone.utc).isoformat(),
                "deployment_type": "main_orchestrator_llm_based",
                "architecture": "llm_based_routing",
                "routing_method": "natural_language_understanding",
                "specialist_agents": 15,
                "notes": "Deployed with LLM-based routing - no hardcoded function tools, pure language understanding"
            }
            
            with open(deployment_config_path, 'w') as f:
                json.dump(deployment_info, f, indent=2)
            
            print("\n" + "="*80)
            print("DEPLOYMENT SUMMARY")
            print("="*80)
            print(f"✅ Main Orchestrator deployed successfully!")
            print(f"✅ Agent ID: {agent_definition.id}")
            print(f"✅ Architecture: LLM-based routing (no hardcoded tools)")
            print(f"✅ Routing: Natural language understanding with 15 specialist agents")
            print("\nNext Steps:")
            print("1. Test routing with test_llm_based_orchestration.py")
            print("2. The orchestrator will provide routing decisions with reasoning")
            print("3. Parse the routing decision and invoke the appropriate specialist")
            
            return agent_definition.id
            
    except Exception as e:
        logger.error(f"Error deploying orchestrator: {str(e)}", exc_info=True)
        sys.exit(1)
    finally:
        await credential.close()

async def main():
    """Main entry point."""
    print("="*80)
    print("DEPLOYING MAIN ORCHESTRATOR (LLM-BASED ROUTING)")
    print("No hardcoded function tools - pure language understanding")
    print("="*80)
    print(f"\nDeployment started at: {datetime.now(timezone.utc).isoformat()}")
    
    agent_id = await deploy_orchestrator()
    
    print(f"\nDeployment completed at: {datetime.now(timezone.utc).isoformat()}")

if __name__ == "__main__":
    asyncio.run(main())