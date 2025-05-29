"""
Redeploy orchestrator with proven working instructions that include tool outputs
Based on successful configuration from CEO_TELEMETRY_EVIDENCE.json
"""

import os
import asyncio
from openai import AsyncAzureOpenAI
from datetime import datetime
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Azure OpenAI configuration
api_key = os.getenv("AZURE_OPENAI_API_KEY", "f3c3d913dc4f42d78b5b6ad6bfd3de49")
endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "https://sk-multi-agent-openai.openai.azure.com/")
deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o")

# Working orchestrator instructions based on CEO_TELEMETRY_EVIDENCE
PROVEN_WORKING_INSTRUCTIONS = """You are the StratOS Main Orchestrator, responsible for coordinating strategic planning activities by delegating to specialized agents.

DIRECTIVE 1: IDENTIFY REQUEST TYPE
Analyze each user request to determine which specialized agent to engage:
- CEO LOG REQUESTS: Managing executive thoughts, insights, log entries, tags, summaries
- NORTH STAR REQUESTS: Vision, goals, metrics, strategic direction
- MEMORY RECALL REQUESTS: Historical information, past decisions, organizational memory
- PREFERENCE LEARNING REQUESTS: User preferences, communication styles, leadership patterns

DIRECTIVE 2: DELEGATION PROTOCOL
For ANY request requiring a specialist:
   STEP 2.1: First announce EXACTLY which specialist you're connecting them with
   STEP 2.2: Then invoke the appropriate connected_agent tool
   STEP 2.3: Present the tool's output as provided

CRITICAL RULES:
- ALWAYS announce delegation BEFORE invoking tools (not after, not during - BEFORE)
- ALWAYS relay tool outputs exactly as provided
- The announcement text must appear in your response BEFORE the tool result
- Your response MUST include BOTH the delegation announcement AND the tool's actual response

AVAILABLE SPECIALISTS:
1. CEO Log Specialist (ceo_log_specialist) - For all CEO log and executive insight requests
2. North Star Specialist (north_star_specialist) - For vision and goal alignment
3. Memory Recall Specialist (memory_recall_specialist) - For retrieving historical information
4. Preference Learning Specialist (preference_learning_specialist) - For learning and adapting to preferences

EXAMPLE RESPONSE FORMAT:
"DIRECTIVE 1: IDENTIFY REQUEST TYPE

This is a [type] request.

I'll connect you with the [Specialist Name] specialist!

[Tool invocation happens here]

[TOOL OUTPUT APPEARS HERE - you must include it in your response]"

REMEMBER: Your response MUST include the tool's output. Do not end with just the delegation announcement."""

async def redeploy_orchestrator():
    """Redeploy orchestrator with proven working instructions"""
    
    try:
        openai_client = AsyncAzureOpenAI(
            api_key=api_key,
            azure_endpoint=endpoint,
            api_version="2024-10-01-preview"
        )
        
        orchestrator_id = "asst_DvAoA85m6eCsWdOT2bsTxE6i"
        
        logger.info(f"Updating orchestrator {orchestrator_id} with proven working instructions...")
        
        # Update the assistant with new instructions
        updated = await openai_client.beta.assistants.update(
            assistant_id=orchestrator_id,
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
        logger.info(f"ID: {updated.id}")
        logger.info(f"Name: {updated.name}")
        logger.info(f"Instructions updated: Yes")
        logger.info(f"Based on: Proven working configuration")
        
        # Verify the tools are still configured
        if hasattr(updated, 'tools') and updated.tools:
            logger.info(f"\nTools configured: {len(updated.tools)}")
            for i, tool in enumerate(updated.tools):
                if hasattr(tool, 'type') and tool.type == 'connected_agent':
                    logger.info(f"  Tool {i+1}: Connected Agent")
                    if hasattr(tool, 'connected_agent'):
                        logger.info(f"    Agent ID: {getattr(tool.connected_agent, 'id', 'Unknown')}")
        else:
            logger.warning("⚠️  No tools found on orchestrator - may need to reconfigure connected agents")
        
        # Save update info
        update_info = {
            "orchestrator_id": updated.id,
            "update_time": datetime.now().isoformat(),
            "instructions_updated": True,
            "based_on": "CEO_TELEMETRY_EVIDENCE.json working example",
            "key_changes": [
                "Added DIRECTIVE structure from working example",
                "Added explicit STEP 2.3: Present the tool's output as provided",
                "Added example response format showing tool output inclusion",
                "Emphasized that response MUST include tool output"
            ]
        }
        
        with open("orchestrator_fix_deployment.json", "w") as f:
            json.dump(update_info, f, indent=2)
        
        logger.info("\n📄 Update info saved to orchestrator_fix_deployment.json")
        
        # Test the updated orchestrator
        logger.info("\n" + "="*60)
        logger.info("TESTING UPDATED ORCHESTRATOR")
        logger.info("="*60)
        
        test_query = "Generate tags for this CEO log entry: 'Team meeting successful. Discussed Q2 roadmap and budget.'"
        logger.info(f"\nTest query: {test_query}")
        
        # Create a thread to test
        thread = await openai_client.beta.threads.create()
        
        # Add message
        await openai_client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=test_query
        )
        
        # Run the assistant
        run = await openai_client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=orchestrator_id
        )
        
        # Wait for completion
        logger.info("Waiting for response...")
        while run.status in ["queued", "in_progress", "requires_action"]:
            await asyncio.sleep(1)
            run = await openai_client.beta.threads.runs.retrieve(
                thread_id=thread.id,
                run_id=run.id
            )
        
        logger.info(f"Run completed with status: {run.status}")
        
        # Get messages
        messages = await openai_client.beta.threads.messages.list(thread_id=thread.id)
        
        # Find assistant response
        for msg in messages.data:
            if msg.role == "assistant":
                for content in msg.content:
                    if hasattr(content, 'text') and hasattr(content.text, 'value'):
                        response = content.text.value
                        logger.info(f"\nOrchestrator response:")
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
                        else:
                            logger.warning("\n⚠️  Still not showing complete responses. May need to check tool configuration.")
                        
                        break
                break
        
        await openai_client.close()
        
    except Exception as e:
        logger.error(f"Error updating orchestrator: {str(e)}")
        logger.info("\nTroubleshooting suggestions:")
        logger.info("1. Check if the API key is correct")
        logger.info("2. Verify the orchestrator ID exists")
        logger.info("3. Ensure you have permission to update the assistant")

if __name__ == "__main__":
    asyncio.run(redeploy_orchestrator())