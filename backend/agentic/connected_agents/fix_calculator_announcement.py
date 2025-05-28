#!/usr/bin/env python3
"""
Fix calculator announcement by redeploying the orchestrator.
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

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def main():
    """Remove and redeploy the orchestrator with fixed instructions."""
    
    # Get current orchestrator ID
    orchestrator_id = os.getenv("MAIN_ORCHESTRATOR_AGENT_ID")
    greeter_id = os.getenv("SPECIALIZED_GREETER_AGENT_ID")
    calculator_id = os.getenv("SPECIALIZED_CALCULATOR_AGENT_ID")
    
    if not all([orchestrator_id, greeter_id, calculator_id]):
        logger.error("Missing agent IDs in environment")
        return
        
    endpoint = os.getenv("AZURE_AI_PROJECT_CONNECTION_STRING")
    model_name = os.getenv("AZURE_AI_MODEL_DEPLOYMENT_NAME", "gpt-35-turbo")
    
    async with DefaultAzureCredential() as credential, \
               AIProjectClient(endpoint=endpoint, credential=credential) as client:
        
        # Step 1: Delete current orchestrator
        logger.info(f"Deleting current orchestrator {orchestrator_id}...")
        try:
            await client.agents.delete_agent(agent_id=orchestrator_id)
            logger.info("✅ Deleted current orchestrator")
        except Exception as e:
            logger.error(f"Failed to delete: {e}")
            
        # Step 2: Create new orchestrator with fixed instructions
        logger.info("Creating new orchestrator with fixed instructions...")
        
        # Fixed instructions that ensure announcement
        fixed_instructions = """You are an orchestrator agent with MANDATORY delegation rules for specific types of requests.

CRITICAL PROTOCOL FOR ALL DELEGATIONS:
1. You MUST announce your delegation BEFORE invoking any tool
2. The announcement text MUST appear in your response
3. DO NOT skip announcements - they are MANDATORY

GREETING DELEGATION:
For ANY greeting request (hello, hi, good morning, etc.):
   1. First say EXACTLY: "I'll connect you with my enthusiastic greeting specialist!"
   2. Then invoke the enthusiastic_greeter_tool
   3. Present the tool's output as provided

CALCULATION DELEGATION:
For ANY mathematical request (calculate, compute, what is X + Y, etc.):
   1. First say EXACTLY: "I'll engage my mathematical calculation expert for this!"
   2. Then invoke the precise_calculator_tool
   3. Present the tool's output as provided

IMPORTANT: Your announcement MUST appear in the response text BEFORE the tool result. Do not skip the announcement!"""

        # Create tools list
        tools = []
        
        # Add greeter tool
        tools.append({
            "type": "connected_agent",
            "connected_agent": {
                "id": greeter_id,
                "name": "enthusiastic_greeter_tool",
                "description": "A specialized greeting expert that provides enthusiastic welcomes"
            }
        })
        
        # Add calculator tool
        tools.append({
            "type": "connected_agent",
            "connected_agent": {
                "id": calculator_id,
                "name": "precise_calculator_tool",
                "description": "A mathematical calculation expert for all arithmetic problems"
            }
        })
        
        # Create new orchestrator
        new_orchestrator = await client.agents.create_agent(
            model=model_name,
            name=f"FixedMultiToolOrchestrator-{os.urandom(4).hex()}",
            instructions=fixed_instructions,
            tools=tools
        )
        
        logger.info(f"✅ Created new orchestrator: {new_orchestrator.id}")
        logger.info(f"Name: {new_orchestrator.name}")
        
        # Update .env file
        logger.info("Updating .env file with new orchestrator ID...")
        
        env_content = env_path.read_text()
        new_env_content = env_content.replace(
            f'MAIN_ORCHESTRATOR_AGENT_ID="{orchestrator_id}"',
            f'MAIN_ORCHESTRATOR_AGENT_ID="{new_orchestrator.id}"'
        )
        env_path.write_text(new_env_content)
        
        logger.info("✅ Updated .env file")
        
        # Test the fix
        logger.info("\n" + "="*60)
        logger.info("TESTING NEW ORCHESTRATOR")
        logger.info("="*60)
        
        from semantic_kernel.agents import AzureAIAgent
        
        orchestrator_agent = AzureAIAgent(
            client=client,
            definition=new_orchestrator
        )
        
        logger.info("\nTest 1: Calculation Request")
        logger.info("USER: What is 42 + 58?")
        logger.info("-" * 40)
        
        response = ""
        async for part in orchestrator_agent.invoke(messages="What is 42 + 58?"):
            if hasattr(part, 'content') and part.content:
                content = str(part.content)
                response += content
                
        logger.info(f"RESPONSE: {response}")
        
        if "mathematical calculation expert" in response.lower():
            logger.info("✅ SUCCESS: Calculator announcement found!")
        else:
            logger.info("❌ WARNING: Calculator announcement not found")

if __name__ == "__main__":
    asyncio.run(main())