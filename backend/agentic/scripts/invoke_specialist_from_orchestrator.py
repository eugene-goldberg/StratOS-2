#!/usr/bin/env python3
"""
Parse orchestrator routing decisions and invoke the appropriate specialist agent.
Handles the LLM-based routing responses from the Main Orchestrator.
"""

import asyncio
import os
import sys
import re
import logging
from typing import Tuple, Optional
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
load_dotenv(env_path)

from azure.identity.aio import DefaultAzureCredential
from semantic_kernel.agents import AzureAIAgent, AzureAIAgentSettings

# Agent mapping from names to deployed IDs
AGENT_MAPPING = {
    "CEOLogAgent": "asst_N5azTOnrhdlm4K9wC6i9OtHA",
    "CEOMemoryAgent": "asst_ZV2p9TPa2l6XASy0nzl6O1hb",
    "CEOPreferenceLearningAgent": "asst_t3B2YUPgg9Fq9KS6fLQMASFX",
    "NorthStarAgent": "asst_JRJqOxzgJGCAm6vT1JUxglJa",
    "InsightSynthesisAgent": "asst_s4BQq86uPMhXGt5rmIqUHj5M",
    "SWOTTOWSAgent": "asst_g6qgPv2Ke8YcJZ7qBnf7NLFP",
    "RiskOpportunityAgent": "asst_HYttqPOdNXlVC7NkgEXCq5MQ",
    "StrategicContextRouter": "asst_xo3fBCcBHNV0Fc7GUMSaVOVa",
    "SOLinkageAgent": "asst_9xKPvtFVA70P5Y1AvdJ2Y69d",
    "PlanningCoordinator": "asst_TJJvOiJzblHg17rV6ogI9pTR",
    "InitiativeGenerator": "asst_iWTKVDG4xrXja8xhSKq2QDAK",
    "ResourceOptimizer": "asst_LCi9P7YMdeeKzN8nES8xgEUP",
    "TimelineStrategist": "asst_sWPe2cMx4eF2mqXVhVo7kFMq",
    "DependencyMapper": "asst_kGQZGft8ItT0VjBvLtP1VhJd",
    "ExecutionTracker": "asst_M8fmaDQIdUCUeP6HM9x02FRX"
}

def parse_orchestrator_response(response: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Parse the orchestrator's routing decision.
    Returns: (agent_name, reasoning)
    
    Expected format:
    ROUTE TO: [AgentName]
    REASON: [reasoning]
    
    But we'll be flexible to handle variations.
    """
    
    # Try to extract using the expected format
    route_match = re.search(r'ROUTE TO:\s*([^\n]+)', response, re.IGNORECASE)
    reason_match = re.search(r'REASON:\s*([^\n]+)', response, re.IGNORECASE)
    
    if route_match and reason_match:
        agent_name = route_match.group(1).strip()
        reasoning = reason_match.group(1).strip()
        
        # Clean up agent name (remove any extra punctuation)
        agent_name = agent_name.strip('[]().,;:')
        
        logger.info(f"Parsed routing decision: {agent_name} - {reasoning}")
        return agent_name, reasoning
    
    # If exact format not found, try to extract agent name from common patterns
    # Like "I would route this to CEOLogAgent" or "This should go to the NorthStarAgent"
    agent_patterns = [
        r'route.*?to\s+(?:the\s+)?(\w+Agent)',
        r'send.*?to\s+(?:the\s+)?(\w+Agent)',
        r'delegate.*?to\s+(?:the\s+)?(\w+Agent)',
        r'(\w+Agent)\s+(?:would|should|can)\s+handle',
        r'best handled by\s+(?:the\s+)?(\w+Agent)',
    ]
    
    for pattern in agent_patterns:
        match = re.search(pattern, response, re.IGNORECASE)
        if match:
            agent_name = match.group(1)
            # Try to extract reasoning from the context
            reasoning = response.strip()
            logger.info(f"Extracted routing from natural language: {agent_name}")
            return agent_name, reasoning
    
    logger.warning(f"Could not parse routing decision from: {response}")
    return None, response

async def invoke_specialist_agent(agent_name: str, user_request: str) -> str:
    """
    Invoke the actual specialist agent based on orchestrator's decision.
    """
    
    # Get agent ID from mapping
    agent_id = AGENT_MAPPING.get(agent_name)
    
    if not agent_id:
        logger.error(f"Unknown agent: {agent_name}")
        return f"Error: Unknown agent '{agent_name}'. Available agents: {', '.join(AGENT_MAPPING.keys())}"
    
    logger.info(f"Invoking specialist agent: {agent_name} (ID: {agent_id})")
    
    try:
        # Initialize settings and credential
        settings = AzureAIAgentSettings()
        credential = DefaultAzureCredential()
        
        # Create client and invoke agent
        async with AzureAIAgent.create_client(credential=credential, settings=settings) as client:
            # Create a thread for the conversation
            thread = await client.agents.threads.create()
            thread_id = thread.id
            
            # Add the user message
            await client.agents.messages.create(
                thread_id=thread_id,
                role="user",
                content=user_request
            )
            
            # Create a run with the specialist agent
            run = await client.agents.runs.create(
                thread_id=thread_id,
                agent_id=agent_id
            )
            
            # Wait for completion
            while run.status in ["queued", "in_progress", "requires_action"]:
                await asyncio.sleep(1)
                run = await client.agents.runs.get(
                    thread_id=thread_id,
                    run_id=run.id
                )
            
            if run.status == "completed":
                # Get the assistant's response
                messages = await client.agents.messages.list(
                    thread_id=thread_id,
                    order="desc",
                    limit=1
                )
                
                if messages.value:
                    response = messages.value[0]
                    if hasattr(response, 'content') and response.content:
                        content = response.content[0]
                        if hasattr(content, 'text') and hasattr(content.text, 'value'):
                            return content.text.value
                
                return "No response from agent"
            else:
                return f"Agent run failed with status: {run.status}"
                
    except Exception as e:
        logger.error(f"Error invoking specialist agent: {str(e)}", exc_info=True)
        return f"Error invoking agent: {str(e)}"
    finally:
        await credential.close()

async def orchestrate_and_invoke(user_request: str) -> dict:
    """
    Complete orchestration flow:
    1. Send request to orchestrator
    2. Parse routing decision
    3. Invoke specialist agent
    4. Return complete response
    """
    
    logger.info(f"Starting orchestration for request: {user_request}")
    
    try:
        # Initialize settings and credential
        settings = AzureAIAgentSettings()
        credential = DefaultAzureCredential()
        
        # Get orchestrator ID from deployment config
        orchestrator_id = "asst_FsaGvKkfDn4mCEqfWQW9XMHW"  # From the deployment output
        
        # First, get routing decision from orchestrator
        async with AzureAIAgent.create_client(credential=credential, settings=settings) as client:
            # Create thread for orchestrator
            thread = await client.agents.threads.create()
            thread_id = thread.id
            
            # Send request to orchestrator
            await client.agents.messages.create(
                thread_id=thread_id,
                role="user",
                content=user_request
            )
            
            # Run orchestrator
            run = await client.agents.runs.create(
                thread_id=thread_id,
                agent_id=orchestrator_id
            )
            
            # Wait for orchestrator response
            while run.status in ["queued", "in_progress"]:
                await asyncio.sleep(1)
                run = await client.agents.runs.get(
                    thread_id=thread_id,
                    run_id=run.id
                )
            
            if run.status == "completed":
                # Get orchestrator's routing decision
                messages = await client.agents.messages.list(
                    thread_id=thread_id,
                    order="desc",
                    limit=1
                )
                
                if messages.value:
                    orchestrator_response = messages.value[0]
                    if hasattr(orchestrator_response, 'content') and orchestrator_response.content:
                        content = orchestrator_response.content[0]
                        if hasattr(content, 'text') and hasattr(content.text, 'value'):
                            routing_decision = content.text.value
                            
                            # Parse routing decision
                            agent_name, reasoning = parse_orchestrator_response(routing_decision)
                            
                            if agent_name:
                                # Invoke specialist agent
                                specialist_response = await invoke_specialist_agent(agent_name, user_request)
                                
                                return {
                                    "success": True,
                                    "routing_decision": {
                                        "agent": agent_name,
                                        "reasoning": reasoning,
                                        "raw_response": routing_decision
                                    },
                                    "specialist_response": specialist_response
                                }
                            else:
                                return {
                                    "success": False,
                                    "error": "Could not parse routing decision",
                                    "orchestrator_response": routing_decision
                                }
                
                return {
                    "success": False,
                    "error": "No response from orchestrator"
                }
            else:
                return {
                    "success": False,
                    "error": f"Orchestrator run failed with status: {run.status}"
                }
                
    except Exception as e:
        logger.error(f"Error in orchestration: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": f"Orchestration error: {str(e)}"
        }
    finally:
        await credential.close()

async def main():
    """Test the orchestration and invocation flow."""
    
    # Test request
    test_request = "I need to record a strategic decision about expanding into the Asian market"
    
    print("="*80)
    print("TESTING ORCHESTRATION AND INVOCATION")
    print("="*80)
    print(f"Request: {test_request}")
    print()
    
    result = await orchestrate_and_invoke(test_request)
    
    if result["success"]:
        print("✅ Orchestration successful!")
        print(f"\nRouting Decision:")
        print(f"  Agent: {result['routing_decision']['agent']}")
        print(f"  Reasoning: {result['routing_decision']['reasoning']}")
        print(f"\nSpecialist Response:")
        print(f"  {result['specialist_response']}")
    else:
        print("❌ Orchestration failed!")
        print(f"Error: {result.get('error', 'Unknown error')}")
        if 'orchestrator_response' in result:
            print(f"\nOrchestrator Response:")
            print(result['orchestrator_response'])

if __name__ == "__main__":
    asyncio.run(main())