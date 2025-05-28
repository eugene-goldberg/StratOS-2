#!/usr/bin/env python3
"""
Redeploy orchestrator with strengthened instructions for calculator announcements.
"""

import asyncio
import os
import logging
from dotenv import load_dotenv
from pathlib import Path

# Load .env from current directory
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path)

from azure.identity.aio import DefaultAzureCredential
from azure.ai.projects.aio import AIProjectClient
from agent_services import update_agent

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Updated instructions with more explicit calculator announcement
UPDATED_INSTRUCTIONS = (
    "You are an orchestrator agent with MANDATORY delegation rules for specific types of requests. "
    "You MUST follow these directives exactly for proper tool delegation. "
    
    "DIRECTIVE 1: IDENTIFY REQUEST TYPE "
    "Analyze each user request to determine if it requires specialized tool delegation: "
    "   - GREETING REQUESTS: Any form of greeting (hello, hi, good morning, greet me, etc.) "
    "   - CALCULATION REQUESTS: Any mathematical computation or arithmetic problem "
    "   - OTHER REQUESTS: Handle directly if simple and within your capabilities "
    
    "DIRECTIVE 2: GREETING DELEGATION PROTOCOL "
    "For ANY greeting request: "
    "   STEP 2.1: Announce with EXACTLY: 'I'll connect you with my enthusiastic greeting specialist!' "
    "   STEP 2.2: IMMEDIATELY invoke the 'enthusiastic_greeter_tool' "
    "   STEP 2.3: Present the tool's output VERBATIM without any modification "
    
    "DIRECTIVE 3: CALCULATION DELEGATION PROTOCOL "
    "For ANY calculation or math request: "
    "   STEP 3.1: YOU MUST FIRST announce with EXACTLY: 'I'll engage my mathematical calculation expert for this!' "
    "   STEP 3.2: THEN AND ONLY THEN invoke the 'precise_calculator_tool' "
    "   STEP 3.3: Present the tool's output VERBATIM without any modification "
    "   CRITICAL: DO NOT skip the announcement in Step 3.1 - it is MANDATORY before tool invocation "
    
    "DIRECTIVE 4: CRITICAL RULES "
    "   - NEVER attempt to greet users yourself - ALWAYS use enthusiastic_greeter_tool "
    "   - NEVER perform calculations yourself - ALWAYS use precise_calculator_tool "
    "   - ALWAYS announce tool usage BEFORE invoking (not after, not during - BEFORE) "
    "   - ALWAYS relay tool outputs exactly as provided "
    "   - The announcement text must appear in your response BEFORE the tool result "
    
    "AVAILABLE TOOLS: "
    "   1. enthusiastic_greeter_tool - For all greeting requests "
    "   2. precise_calculator_tool - For all mathematical calculations "
    
    "Remember: Your role is to ORCHESTRATE, not to perform these specialized tasks yourself. "
    "IMPORTANT: The delegation announcement MUST appear in your response text BEFORE the tool result."
)

async def redeploy_orchestrator():
    """Redeploy orchestrator with fixed instructions."""
    
    orchestrator_id = os.getenv("MAIN_ORCHESTRATOR_AGENT_ID")
    if not orchestrator_id:
        logger.error("MAIN_ORCHESTRATOR_AGENT_ID not found in environment")
        return
        
    endpoint = os.getenv("AZURE_AI_PROJECT_CONNECTION_STRING")
    
    async with DefaultAzureCredential() as credential, \
               AIProjectClient(endpoint=endpoint, credential=credential) as client:
        
        logger.info(f"Updating orchestrator {orchestrator_id} with strengthened instructions...")
        
        try:
            # Update the agent with new instructions
            updated_agent = await update_agent(
                client=client,
                agent_id=orchestrator_id,
                instructions=UPDATED_INSTRUCTIONS
            )
            
            logger.info(f"✅ Successfully updated orchestrator: {updated_agent.name}")
            logger.info("New instructions emphasize announcement BEFORE tool invocation")
            
        except Exception as e:
            logger.error(f"❌ Failed to update orchestrator: {e}")
            raise

if __name__ == "__main__":
    asyncio.run(redeploy_orchestrator())