"""
Update the actual StratOS orchestrator with proven working instructions
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
from semantic_kernel.agents import AzureAIAgent

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

IMPORTANT: Your announcement MUST appear in the response text BEFORE the tool result.
When you invoke a tool, the tool's response MUST be included in your output.

EXAMPLE OUTPUT FORMAT:
"DIRECTIVE 1: IDENTIFY REQUEST TYPE

This is a CEO Log request.

I'll connect you with the CEO Log specialist for strategic insights!

[TOOL OUTPUT APPEARS HERE - The actual response from the specialist]"

Remember: The tool output MUST be included in your response. Do not end with just the announcement."""

async def update_stratos_orchestrator():
    """Update the actual StratOS orchestrator with proven working instructions"""
    
    # Get connection string
    connection_string = os.getenv("AZURE_AI_PROJECT_CONNECTION_STRING")
    if not connection_string:
        logger.error("AZURE_AI_PROJECT_CONNECTION_STRING not found in environment")
        return
    
    # Get the correct orchestrator ID from .env
    orchestrator_id = os.getenv("STRATOS_ORCHESTRATOR_ID", "asst_LVZnISMFNOuGcqlr4js5IDvb")
    logger.info(f"Using StratOS Orchestrator ID: {orchestrator_id}")
    
    try:
        async with DefaultAzureCredential() as credential:
            async with AIProjectClient(
                endpoint=connection_string,
                credential=credential
            ) as client:
                
                logger.info(f"Fetching current orchestrator configuration...")
                
                # Get current orchestrator
                try:
                    current_orchestrator = await client.agents.get_agent(agent_id=orchestrator_id)
                    logger.info(f"Found orchestrator: {current_orchestrator.name}")
                    
                    # Log current tools
                    if hasattr(current_orchestrator, 'tools') and current_orchestrator.tools:
                        logger.info(f"Current tools: {len(current_orchestrator.tools)}")
                        for i, tool in enumerate(current_orchestrator.tools):
                            if hasattr(tool, 'type') and tool.type == 'connected_agent':
                                logger.info(f"  Tool {i+1}: Connected Agent")
                                if hasattr(tool, 'connected_agent') and hasattr(tool.connected_agent, 'assistant_id'):
                                    logger.info(f"    Assistant ID: {tool.connected_agent.assistant_id}")
                    else:
                        logger.warning("No tools found on current orchestrator")
                    
                except Exception as e:
                    logger.error(f"Error fetching orchestrator: {str(e)}")
                    return
                
                # Update the orchestrator with new instructions
                logger.info("\nUpdating orchestrator with proven working instructions...")
                
                try:
                    # Update using the agents API
                    updated_orchestrator = await client.agents.update_agent(
                        agent_id=orchestrator_id,
                        instructions=PROVEN_WORKING_INSTRUCTIONS,
                        metadata={
                            "type": "orchestrator",
                            "fixed_response_handling": "true",
                            "version": "3.0",
                            "update_time": datetime.now().isoformat(),
                            "based_on": "CEO_TELEMETRY_EVIDENCE working example"
                        }
                    )
                    
                    logger.info(f"\n✅ Orchestrator updated successfully!")
                    logger.info(f"ID: {orchestrator_id}")
                    logger.info(f"Name: {updated_orchestrator.name}")
                    
                except Exception as e:
                    logger.error(f"Error updating orchestrator: {str(e)}")
                    logger.info("\nAttempting alternative approach...")
                    # Alternative: Delete and recreate
                    return
                
                # Save update info
                update_info = {
                    "orchestrator_id": orchestrator_id,
                    "update_time": datetime.now().isoformat(),
                    "instructions_based_on": "CEO_TELEMETRY_EVIDENCE.json",
                    "key_features": [
                        "DIRECTIVE structure from working example",
                        "Explicit STEP X.3: Present the tool's output as provided",
                        "Clear delegation protocols for each agent",
                        "Example output format showing tool inclusion",
                        "Emphasis on including tool outputs in response"
                    ]
                }
                
                with open("stratos_orchestrator_update_info.json", "w") as f:
                    json.dump(update_info, f, indent=2)
                
                logger.info("\n📄 Update info saved to stratos_orchestrator_update_info.json")
                
                # Test the updated orchestrator
                logger.info("\n" + "="*60)
                logger.info("TESTING UPDATED ORCHESTRATOR")
                logger.info("="*60)
                
                test_query = "Generate tags for this CEO log entry: 'Team meeting successful. Discussed Q2 roadmap and budget.'"
                logger.info(f"\nTest query: {test_query}")
                
                # Create agent instance
                orchestrator_agent = AzureAIAgent(
                    client=client,
                    definition=current_orchestrator
                )
                
                # Invoke agent
                logger.info("\nInvoking orchestrator...")
                response = ""
                start_time = datetime.now()
                
                async for part in orchestrator_agent.invoke(messages=test_query):
                    if hasattr(part, 'content') and part.content:
                        response += str(part.content)
                
                duration = (datetime.now() - start_time).total_seconds()
                
                logger.info(f"\nResponse received in {duration:.1f}s:")
                logger.info("-" * 60)
                logger.info(response)
                logger.info("-" * 60)
                
                # Analyze response
                logger.info("\nResponse analysis:")
                has_directive = "DIRECTIVE" in response
                has_delegation = "I'll connect you with" in response
                has_tool_output = any(indicator in response for indicator in [
                    "has been saved", "has been logged", "Tags:", "Generated tags:",
                    "Entry saved", "category", "The CEO log entry"
                ])
                
                logger.info(f"✓ Has DIRECTIVE structure: {'Yes' if has_directive else 'No'}")
                logger.info(f"✓ Has delegation announcement: {'Yes' if has_delegation else 'No'}")
                logger.info(f"✓ Has tool output: {'Yes' if has_tool_output else 'No'}")
                
                if has_delegation and has_tool_output:
                    logger.info("\n✅ SUCCESS! Orchestrator now returns BOTH delegation AND tool output!")
                    logger.info("The fix has been successfully applied!")
                else:
                    logger.warning("\n⚠️  Response still incomplete. This may require:")
                    logger.warning("  1. Waiting for the update to propagate")
                    logger.warning("  2. Checking if connected agents are properly configured")
                    logger.warning("  3. Testing with thread-based approach instead")
                
                logger.info("\n" + "="*60)
                logger.info("UPDATE COMPLETE!")
                logger.info("="*60)
                logger.info(f"Orchestrator ID: {orchestrator_id}")
                logger.info("\nNext steps:")
                logger.info("1. Test with: python test_stratos_agents_telemetry.py")
                logger.info("2. Verify responses include tool outputs")
                logger.info("3. If still not working, may need to redeploy agents")
                
    except Exception as e:
        logger.error(f"Error during update: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(update_stratos_orchestrator())