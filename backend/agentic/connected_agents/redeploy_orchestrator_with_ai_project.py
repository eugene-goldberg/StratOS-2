"""
Redeploy orchestrator using AIProjectClient with proven working instructions
Based on successful configuration from CEO_TELEMETRY_EVIDENCE.json
"""

import os
import asyncio
import sys
from pathlib import Path
from datetime import datetime
import json
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv(Path(__file__).parent / '.env')

# Add stratos to path for agent configs
sys.path.insert(0, str(Path(__file__).parent / 'stratos'))

from azure.ai.projects.aio import AIProjectClient
from azure.identity.aio import DefaultAzureCredential

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Working orchestrator instructions based on CEO_TELEMETRY_EVIDENCE
PROVEN_WORKING_INSTRUCTIONS = """You are the StratOS Main Orchestrator, responsible for coordinating strategic planning activities by delegating to specialized agents.

DIRECTIVE 1: IDENTIFY REQUEST TYPE
Analyze each user request to determine which specialized agent to engage:
- CEO LOG REQUESTS: Managing executive thoughts, insights, log entries, tags, summaries
- NORTH STAR REQUESTS: Vision, goals, metrics, strategic direction
- MEMORY RECALL REQUESTS: Historical information, past decisions, organizational memory
- PREFERENCE LEARNING REQUESTS: User preferences, communication styles, leadership patterns

DIRECTIVE 2: CEO LOG DELEGATION PROTOCOL
For ANY CEO log, executive entry, or strategic insight request:
   STEP 2.1: First say EXACTLY: 'I'll connect you with the CEO Log specialist for strategic insights!'
   STEP 2.2: Then invoke the 'ceo_log_specialist' tool
   STEP 2.3: Present the tool's output as provided

DIRECTIVE 3: NORTH STAR DELEGATION PROTOCOL
For ANY vision, goal, or metric request:
   STEP 3.1: First say EXACTLY: 'I'll connect you with the North Star specialist!'
   STEP 3.2: Then invoke the 'north_star_specialist' tool
   STEP 3.3: Present the tool's output as provided

DIRECTIVE 4: MEMORY RECALL DELEGATION PROTOCOL
For ANY historical or past decision request:
   STEP 4.1: First say EXACTLY: 'I'll connect you with the Memory Recall specialist!'
   STEP 4.2: Then invoke the 'memory_recall_specialist' tool
   STEP 4.3: Present the tool's output as provided

DIRECTIVE 5: PREFERENCE LEARNING DELEGATION PROTOCOL
For ANY preference or learning request:
   STEP 5.1: First say EXACTLY: 'I'll connect you with the Preference Learning specialist!'
   STEP 5.2: Then invoke the 'preference_learning_specialist' tool
   STEP 5.3: Present the tool's output as provided

CRITICAL RULES:
- NEVER process requests yourself - ALWAYS use the appropriate specialist
- ALWAYS announce tool usage BEFORE invoking (not after, not during - BEFORE)
- ALWAYS relay tool outputs exactly as provided
- The announcement text must appear in your response BEFORE the tool result
- Your response MUST include BOTH the delegation announcement AND the tool's actual response

AVAILABLE TOOLS:
1. ceo_log_specialist - For all CEO log and executive insight requests
2. north_star_specialist - For vision and goal alignment
3. memory_recall_specialist - For retrieving historical information
4. preference_learning_specialist - For learning and adapting to preferences

IMPORTANT: Your announcement MUST appear in the response text BEFORE the tool result.
When you invoke a tool, the tool's response MUST be included in your output."""

async def redeploy_orchestrator_fixed():
    """Redeploy orchestrator with proven working instructions using AIProjectClient"""
    
    # Get connection string
    connection_string = os.getenv("AZURE_AI_PROJECT_CONNECTION_STRING")
    if not connection_string:
        logger.error("AZURE_AI_PROJECT_CONNECTION_STRING not found in environment")
        logger.info("Please set this in your .env file")
        return
    
    # Get model deployment name
    model_deployment_name = os.getenv("MODEL_DEPLOYMENT_NAME", "gpt-35-turbo")
    
    try:
        async with DefaultAzureCredential() as credential:
            async with AIProjectClient(
                endpoint=connection_string,
                credential=credential
            ) as client:
                
                orchestrator_id = "asst_DvAoA85m6eCsWdOT2bsTxE6i"
                
                logger.info(f"Fetching current orchestrator configuration...")
                
                # Get current orchestrator
                try:
                    current_orchestrator = await client.agents.get_agent(agent_id=orchestrator_id)
                    logger.info(f"Found orchestrator: {current_orchestrator.name}")
                    
                    # Log current tools
                    if hasattr(current_orchestrator, 'tools') and current_orchestrator.tools:
                        logger.info(f"Current tools: {len(current_orchestrator.tools)}")
                        tools = current_orchestrator.tools
                    else:
                        logger.warning("No tools found on current orchestrator")
                        tools = []
                    
                except Exception as e:
                    logger.error(f"Error fetching orchestrator: {str(e)}")
                    logger.info("The orchestrator ID may not exist or you may not have access")
                    return
                
                # Delete existing orchestrator
                logger.info(f"\nDeleting existing orchestrator to redeploy with fixed instructions...")
                try:
                    await client.agents.delete_agent(agent_id=orchestrator_id)
                    logger.info("✅ Existing orchestrator deleted")
                except Exception as e:
                    logger.warning(f"Could not delete orchestrator: {str(e)}")
                
                # Create new orchestrator with same ID (if possible) or new one
                logger.info("\nCreating new orchestrator with proven working instructions...")
                
                # Prepare tools in the correct format
                formatted_tools = []
                if tools:
                    for tool in tools:
                        if hasattr(tool, 'type') and tool.type == 'connected_agent':
                            formatted_tools.append({
                                "type": "connected_agent",
                                "connected_agent": {
                                    "assistant_id": tool.connected_agent.assistant_id if hasattr(tool.connected_agent, 'assistant_id') else None
                                }
                            })
                
                # If no tools found, add the known agent IDs
                if not formatted_tools:
                    logger.info("Adding known StratOS agent tools...")
                    known_agents = {
                        "ceo_log": "asst_T01KHUc5FoIupJR2C7RCxOhO",
                        "north_star": "asst_mGfN5IYqsL17Jx7s6hEGlnQA",
                        "memory_recall": "asst_qbgCLx2XgO9E4W9vJCHAWoQw",
                        "preference_learning": "asst_JxEgAcYJN42LIXKT8X1Jvz60"
                    }
                    
                    for name, agent_id in known_agents.items():
                        formatted_tools.append({
                            "type": "connected_agent",
                            "connected_agent": {
                                "assistant_id": agent_id
                            }
                        })
                
                # Create new orchestrator
                new_orchestrator = await client.agents.create_agent(
                    model=model_deployment_name,
                    name="StratOS Main Orchestrator (Fixed)",
                    instructions=PROVEN_WORKING_INSTRUCTIONS,
                    tools=formatted_tools,
                    metadata={
                        "type": "orchestrator",
                        "fixed_response_handling": "true",
                        "version": "3.0",
                        "deployment_time": datetime.now().isoformat(),
                        "based_on": "CEO_TELEMETRY_EVIDENCE working example"
                    }
                )
                
                logger.info(f"\n✅ New orchestrator created successfully!")
                logger.info(f"ID: {new_orchestrator.id}")
                logger.info(f"Name: {new_orchestrator.name}")
                logger.info(f"Tools configured: {len(formatted_tools)}")
                
                # Save deployment info
                deployment_info = {
                    "old_orchestrator_id": orchestrator_id,
                    "new_orchestrator_id": new_orchestrator.id,
                    "deployment_time": datetime.now().isoformat(),
                    "instructions_based_on": "CEO_TELEMETRY_EVIDENCE.json",
                    "tools_configured": len(formatted_tools),
                    "key_features": [
                        "DIRECTIVE structure from working example",
                        "Explicit STEP X.3: Present the tool's output as provided",
                        "Clear delegation protocols for each agent",
                        "Emphasis on including tool outputs in response"
                    ]
                }
                
                with open("orchestrator_redeployment_info.json", "w") as f:
                    json.dump(deployment_info, f, indent=2)
                
                logger.info("\n📄 Deployment info saved to orchestrator_redeployment_info.json")
                
                # Update .env file with new orchestrator ID
                env_path = Path(__file__).parent / '.env'
                if env_path.exists():
                    with open(env_path, 'r') as f:
                        env_content = f.read()
                    
                    # Update or add orchestrator ID
                    if 'STRATOS_ORCHESTRATOR_ID=' in env_content:
                        lines = env_content.split('\n')
                        for i, line in enumerate(lines):
                            if line.startswith('STRATOS_ORCHESTRATOR_ID='):
                                lines[i] = f'STRATOS_ORCHESTRATOR_ID={new_orchestrator.id}'
                        env_content = '\n'.join(lines)
                    else:
                        env_content += f'\nSTRATOS_ORCHESTRATOR_ID={new_orchestrator.id}\n'
                    
                    with open(env_path, 'w') as f:
                        f.write(env_content)
                    
                    logger.info(f"✅ Updated .env file with new orchestrator ID: {new_orchestrator.id}")
                
                logger.info("\n" + "="*60)
                logger.info("DEPLOYMENT COMPLETE!")
                logger.info("="*60)
                logger.info(f"New Orchestrator ID: {new_orchestrator.id}")
                logger.info("\nNext steps:")
                logger.info("1. Test with: python test_stratos_agents_telemetry.py")
                logger.info("2. Verify responses include tool outputs")
                logger.info("3. Update any scripts using the old orchestrator ID")
                
    except Exception as e:
        logger.error(f"Error during redeployment: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(redeploy_orchestrator_fixed())