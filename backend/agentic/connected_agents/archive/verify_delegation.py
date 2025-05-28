#!/usr/bin/env python3
"""
Script to verify if the orchestrator is actually delegating to connected agents.
"""

import asyncio
import os
import logging
from dotenv import load_dotenv
from azure.identity.aio import DefaultAzureCredential
from azure.ai.projects.aio import AIProjectClient
from semantic_kernel.agents import AzureAIAgent

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def check_delegation():
    """Check if orchestrator properly delegates to connected agents."""
    
    # Get the orchestrator ID from environment
    orchestrator_id = os.getenv("MAIN_ORCHESTRATOR_AGENT_ID")
    if not orchestrator_id:
        logger.error("MAIN_ORCHESTRATOR_AGENT_ID not found in environment")
        return
        
    logger.info(f"Testing orchestrator: {orchestrator_id}")
    
    # Create client
    endpoint = os.getenv("AZURE_AI_PROJECT_CONNECTION_STRING")
    async with DefaultAzureCredential() as credential, \
               AIProjectClient(endpoint=endpoint, credential=credential) as client:
        
        # Create agent instance
        orchestrator_agent = AzureAIAgent(
            client=client,
            definition={
                "model": os.getenv("AZURE_AI_MODEL_DEPLOYMENT_NAME", "gpt-35-turbo"),
                "id": orchestrator_id
            }
        )
        
        # Test greeting delegation
        logger.info("\n=== Testing Greeting Delegation ===")
        response = ""
        async for part in orchestrator_agent.invoke(messages="Hello!"):
            if hasattr(part, 'content') and part.content:
                response += str(part.content)
                
        logger.info(f"Response: {response}")
        
        # Check for delegation indicators
        delegation_indicators = [
            "woohoo",
            "magnificent human", 
            "joy to greet you",
            "thousand welcomes",
            "✨🎉✨"
        ]
        
        found_indicators = [ind for ind in delegation_indicators if ind.lower() in response.lower()]
        
        if found_indicators:
            logger.info(f"✅ DELEGATION CONFIRMED! Found specialized greeting indicators: {found_indicators}")
            logger.info("The orchestrator successfully delegated to the enthusiastic_greeter_tool")
        else:
            logger.warning("❌ NO DELEGATION DETECTED! The orchestrator appears to be responding directly")
            logger.warning("Expected specialized greeting content but got generic response")
            
        # Check if orchestrator mentioned using the tool
        if "enthusiastic_greeter_tool" in response.lower() or "greeting expert" in response.lower():
            logger.info("✅ Orchestrator explicitly mentioned using the tool")
        else:
            logger.info("ℹ️  Orchestrator did not explicitly mention tool usage")

if __name__ == "__main__":
    asyncio.run(check_delegation())