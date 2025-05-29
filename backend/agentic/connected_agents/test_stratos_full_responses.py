#!/usr/bin/env python3
"""
Test StratOS agents to capture FULL responses including actual agent outputs.
This version ensures we collect the complete response including tool invocation results.
"""

import asyncio
import os
import logging
import json
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

# Import Azure SDK components
from azure.identity.aio import DefaultAzureCredential
from azure.ai.projects.aio import AIProjectClient
from semantic_kernel.agents import AzureAIAgent

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def test_with_full_responses():
    """Test StratOS agents and capture full responses including tool invocation results."""
    
    # Load deployment info
    deployment_file = Path(__file__).parent / "stratos" / "archive" / "stratos_deployment_info.json"
    if not deployment_file.exists():
        logger.error(f"Deployment info not found: {deployment_file}")
        return
        
    with open(deployment_file, 'r') as f:
        deployment_info = json.load(f)
    
    orchestrator_id = deployment_info["orchestrator"]["id"]
    endpoint = os.getenv("AZURE_AI_PROJECT_CONNECTION_STRING")
    
    if not endpoint:
        logger.error("AZURE_AI_PROJECT_CONNECTION_STRING not found")
        return
    
    logger.info("="*80)
    logger.info("STRATOS AGENTS - FULL RESPONSE TEST")
    logger.info("="*80)
    logger.info(f"Orchestrator: {orchestrator_id}")
    
    async with DefaultAzureCredential() as credential, \
               AIProjectClient(endpoint=endpoint, credential=credential) as client:
        
        # Get orchestrator
        orchestrator_def = await client.agents.get_agent(agent_id=orchestrator_id)
        logger.info(f"Orchestrator name: {orchestrator_def.name}")
        
        # Create agent instance
        orchestrator_agent = AzureAIAgent(
            client=client,
            definition=orchestrator_def
        )
        
        # Test case - CEO Log
        logger.info("\n" + "-"*60)
        logger.info("TEST: CEO Log Full Response")
        logger.info("-"*60)
        
        query = "Generate tags for this CEO log entry: 'Team meeting went well. Discussed Q2 roadmap and AI strategy.'"
        logger.info(f"Query: {query}")
        
        # Method 1: Collect all parts
        response_parts = []
        async for part in orchestrator_agent.invoke(messages=query):
            if hasattr(part, 'content') and part.content:
                response_parts.append(str(part.content))
                logger.info(f"Part received: {str(part.content)[:100]}...")
        
        full_response = "".join(response_parts)
        
        logger.info(f"\nFULL RESPONSE ({len(response_parts)} parts):")
        logger.info("-" * 60)
        logger.info(full_response)
        logger.info("-" * 60)
        
        # Analyze response structure
        logger.info("\nRESPONSE ANALYSIS:")
        if "I'll connect you with" in full_response:
            logger.info("✅ Delegation announcement found")
            
        # Check for actual agent response patterns
        agent_response_indicators = [
            "Tags:", "Generated tags:", "#", "Keywords:", "Topics:",
            "Strategic", "Meeting", "Roadmap", "AI", "Team"
        ]
        
        has_agent_response = any(indicator in full_response for indicator in agent_response_indicators)
        if has_agent_response:
            logger.info("✅ Agent response content detected")
        else:
            logger.info("❌ No agent response content found")
        
        # Test with longer wait between messages
        await asyncio.sleep(3)
        
        # Test case 2 - Direct question that should get a real response
        logger.info("\n" + "-"*60)
        logger.info("TEST: North Star Full Response")
        logger.info("-"*60)
        
        query2 = "Define our north star metric for customer retention"
        logger.info(f"Query: {query2}")
        
        # Create new thread for clean test
        thread = await client.agents.create_thread()
        await client.agents.create_message(
            thread_id=thread.id,
            role="user",
            content=query2
        )
        
        # Create run and wait for completion
        run = await client.agents.create_run(
            thread_id=thread.id,
            assistant_id=orchestrator_id
        )
        
        # Poll until completion
        while run.status in ["queued", "in_progress", "requires_action"]:
            await asyncio.sleep(1)
            run = await client.agents.get_run(thread_id=thread.id, run_id=run.id)
            logger.info(f"Run status: {run.status}")
        
        # Get all messages from the thread
        messages = await client.agents.list_messages(thread_id=thread.id)
        
        logger.info("\nTHREAD MESSAGES:")
        for msg in messages.data:
            if msg.role == "assistant":
                content = msg.content[0].text.value if msg.content else ""
                logger.info(f"Assistant: {content}")
        
        # Check run steps to see tool invocations
        steps = await client.agents.list_run_steps(thread_id=thread.id, run_id=run.id)
        
        logger.info("\nRUN STEPS:")
        for step in steps.data:
            logger.info(f"Step {step.id}: {step.type} - {step.status}")
            if hasattr(step, 'step_details') and hasattr(step.step_details, 'tool_calls'):
                for tool_call in step.step_details.tool_calls:
                    logger.info(f"  Tool call: {getattr(tool_call, 'type', 'unknown')}")
                    if hasattr(tool_call, 'connected_agent'):
                        logger.info(f"    Connected agent ID: {tool_call.connected_agent.assistant_id}")


async def test_direct_agent_invocation():
    """Test invoking an agent directly to see its actual response."""
    
    logger.info("\n" + "="*80)
    logger.info("DIRECT AGENT INVOCATION TEST")
    logger.info("="*80)
    
    # CEO Log Agent ID from deployment
    ceo_log_agent_id = "asst_nbyTtjWspeOEUH5RurvFPNOF"
    
    endpoint = os.getenv("AZURE_AI_PROJECT_CONNECTION_STRING")
    
    async with DefaultAzureCredential() as credential, \
               AIProjectClient(endpoint=endpoint, credential=credential) as client:
        
        # Get CEO Log agent directly
        ceo_agent_def = await client.agents.get_agent(agent_id=ceo_log_agent_id)
        logger.info(f"Direct agent: {ceo_agent_def.name}")
        
        # Create agent instance
        ceo_agent = AzureAIAgent(
            client=client,
            definition=ceo_agent_def
        )
        
        # Test direct invocation
        query = "Generate tags for: Team discussed new product launch timeline"
        logger.info(f"Direct query to CEO Log Agent: {query}")
        
        response = ""
        async for part in ceo_agent.invoke(messages=query):
            if hasattr(part, 'content') and part.content:
                response += str(part.content)
        
        logger.info(f"\nDIRECT AGENT RESPONSE:")
        logger.info("-" * 60)
        logger.info(response)
        logger.info("-" * 60)


if __name__ == "__main__":
    asyncio.run(test_with_full_responses())
    asyncio.run(test_direct_agent_invocation())