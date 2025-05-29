"""
Test the updated orchestrator using thread-based approach to capture complete responses
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

from azure.ai.projects.aio import AIProjectClient
from azure.identity.aio import DefaultAzureCredential

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_thread_based_responses():
    """Test orchestrator using thread-based approach to see full conversation"""
    
    # Get connection string
    connection_string = os.getenv("AZURE_AI_PROJECT_CONNECTION_STRING")
    if not connection_string:
        logger.error("AZURE_AI_PROJECT_CONNECTION_STRING not found")
        return
    
    # Get orchestrator ID
    orchestrator_id = os.getenv("STRATOS_ORCHESTRATOR_ID", "asst_LVZnISMFNOuGcqlr4js5IDvb")
    
    try:
        async with DefaultAzureCredential() as credential:
            async with AIProjectClient(
                endpoint=connection_string,
                credential=credential
            ) as client:
                
                logger.info("="*80)
                logger.info("TESTING ORCHESTRATOR WITH THREAD-BASED APPROACH")
                logger.info("="*80)
                logger.info(f"Orchestrator ID: {orchestrator_id}")
                
                # Test queries
                test_queries = [
                    {
                        "name": "CEO Log Tag Generation",
                        "query": "Generate tags for this CEO log entry: 'Team meeting successful. Discussed Q2 roadmap and budget.'"
                    },
                    {
                        "name": "CEO Log Entry",
                        "query": "I need to log this: Board meeting went well. We approved the new expansion plan and budget allocation."
                    },
                    {
                        "name": "North Star Query",
                        "query": "What should our north star metric be for customer satisfaction?"
                    }
                ]
                
                for test in test_queries:
                    logger.info(f"\n{'='*60}")
                    logger.info(f"TEST: {test['name']}")
                    logger.info(f"{'='*60}")
                    logger.info(f"Query: {test['query']}")
                    
                    # Create thread
                    thread = await client.agents.threads.create()
                    logger.info(f"Thread created: {thread.id}")
                    
                    # Add message
                    await client.agents.create_message(
                        thread_id=thread.id,
                        role="user",
                        content=test['query']
                    )
                    
                    # Create run
                    run = await client.agents.create_run(
                        thread_id=thread.id,
                        assistant_id=orchestrator_id
                    )
                    logger.info(f"Run created: {run.id}")
                    
                    # Poll for completion
                    poll_count = 0
                    while run.status in ["queued", "in_progress", "requires_action"]:
                        await asyncio.sleep(1)
                        poll_count += 1
                        run = await client.agents.get_run(
                            thread_id=thread.id,
                            run_id=run.id
                        )
                        logger.info(f"Poll {poll_count}: Status = {run.status}")
                    
                    logger.info(f"Run completed with status: {run.status}")
                    
                    # Get all messages in thread
                    messages = await client.agents.list_messages(thread_id=thread.id)
                    
                    logger.info(f"\nCOMPLETE THREAD CONVERSATION:")
                    logger.info("-" * 60)
                    
                    # Display messages in chronological order
                    message_list = []
                    for msg in messages.data:
                        content = ""
                        if msg.content:
                            for content_part in msg.content:
                                if hasattr(content_part, 'text') and hasattr(content_part.text, 'value'):
                                    content = content_part.text.value
                                    break
                        
                        message_list.append({
                            "id": msg.id,
                            "role": msg.role,
                            "content": content,
                            "created_at": msg.created_at
                        })
                    
                    # Sort by creation time
                    message_list.sort(key=lambda x: x['created_at'])
                    
                    # Display messages
                    for msg in message_list:
                        logger.info(f"\n{msg['role'].upper()} (ID: {msg['id']}):")
                        logger.info(msg['content'])
                    
                    # Analyze assistant response
                    assistant_messages = [m for m in message_list if m['role'] == 'assistant']
                    if assistant_messages:
                        final_response = assistant_messages[-1]['content']
                        
                        logger.info(f"\nRESPONSE ANALYSIS:")
                        logger.info("-" * 60)
                        
                        # Check for delegation
                        has_delegation = "I'll connect you with" in final_response
                        logger.info(f"✓ Has delegation announcement: {'Yes' if has_delegation else 'No'}")
                        
                        # Check for DIRECTIVE structure
                        has_directive = "DIRECTIVE" in final_response
                        logger.info(f"✓ Has DIRECTIVE structure: {'Yes' if has_directive else 'No'}")
                        
                        # Check for tool output
                        tool_output_indicators = [
                            "has been saved", "has been logged", "Tags:", "Generated tags:",
                            "Entry saved", "category", "The CEO log entry", "recorded",
                            "#", "strategic", "planning", "budget", "roadmap"
                        ]
                        has_tool_output = any(indicator in final_response for indicator in tool_output_indicators)
                        logger.info(f"✓ Has tool output: {'Yes' if has_tool_output else 'No'}")
                        
                        # Check response length (tool outputs typically make responses longer)
                        logger.info(f"✓ Response length: {len(final_response)} characters")
                        
                        if has_delegation and has_tool_output:
                            logger.info("\n✅ SUCCESS! Response includes BOTH delegation AND tool output!")
                            # Find the tool output part
                            for indicator in tool_output_indicators:
                                if indicator in final_response:
                                    idx = final_response.find(indicator)
                                    logger.info(f"\nTool output detected at position {idx}:")
                                    logger.info(f"'{final_response[max(0, idx-20):idx+50]}...'")
                                    break
                        else:
                            logger.warning("\n⚠️  Response incomplete - only delegation announcement found")
                    
                    # Check run steps for tool invocations
                    steps = await client.agents.list_run_steps(
                        thread_id=thread.id,
                        run_id=run.id
                    )
                    
                    logger.info(f"\nRUN STEPS:")
                    logger.info("-" * 60)
                    for step in steps.data:
                        logger.info(f"Step {step.id}: {step.type} - {step.status}")
                        
                        if hasattr(step, 'step_details'):
                            if hasattr(step.step_details, 'tool_calls') and step.step_details.tool_calls:
                                for tool_call in step.step_details.tool_calls:
                                    logger.info(f"  Tool Call:")
                                    logger.info(f"    Type: {getattr(tool_call, 'type', 'unknown')}")
                                    
                                    # Check if it's a connected agent
                                    if hasattr(tool_call, 'type') and tool_call.type == 'connected_agent':
                                        logger.info(f"    ✓ Connected Agent invoked!")
                                        if hasattr(tool_call, 'connected_agent'):
                                            logger.info(f"      Assistant ID: {getattr(tool_call.connected_agent, 'assistant_id', 'Unknown')}")
                                    
                                    # Check for output
                                    if hasattr(tool_call, 'output'):
                                        logger.info(f"    Output: {tool_call.output}")
                    
                    # Small delay between tests
                    await asyncio.sleep(3)
                
                # Summary
                logger.info("\n\n" + "="*80)
                logger.info("SUMMARY")
                logger.info("="*80)
                logger.info("\nThe thread-based approach shows the complete conversation flow.")
                logger.info("If tool outputs are still not visible, this indicates:")
                logger.info("1. The connected agents may not be returning responses properly")
                logger.info("2. The orchestrator needs the STEP 2.3 instruction to be enforced")
                logger.info("3. May need to test agents directly to verify they work")
                
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_thread_based_responses())