#!/usr/bin/env python3
"""
Direct test of CEO Log Agent using Azure AI Agent Service API.
This bypasses Semantic Kernel to test if the agent calls Azure Functions.
"""

import asyncio
import os
import logging
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

# Import Azure SDK components
from azure.identity.aio import DefaultAzureCredential
from azure.ai.projects.aio import AIProjectClient

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_ceo_log_direct():
    """Test CEO Log Agent directly using Azure AI API."""
    
    # Configuration
    endpoint = os.getenv("AZURE_AI_PROJECT_CONNECTION_STRING")
    ceo_agent_id = os.getenv("CEO_LOG_AGENT_ID", "asst_9UphrHMFGC2QihVXrtOHDcND")
    
    logger.info(f"Testing CEO Log Agent: {ceo_agent_id}")
    logger.info(f"Endpoint: {endpoint[:50]}...")
    
    # Test data
    test_timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    test_user_id = f"test_user_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Test message that should trigger function call
    test_message = f"""
Please save this CEO log entry using the call_ceo_function:

Content: "E2E Test Entry - {test_timestamp}: Our AI initiative has reached a critical milestone. 
The connected agents architecture is now fully deployed and operational. This positions us well 
for rapid scaling in Q1 2026."

Category: strategic_planning
Tags: ["ai", "milestone", "architecture", "e2e_test"]
User ID: {test_user_id}

Use operation="save_log" and include all the details above.
"""
    
    async with DefaultAzureCredential() as credential:
        async with AIProjectClient(endpoint=endpoint, credential=credential) as client:
            
            try:
                # 1. Create a thread
                logger.info("\n1. Creating thread...")
                thread = await client.agents.threads.create()
                logger.info(f"   ✓ Thread created: {thread.id}")
                
                # 2. Add message to thread
                logger.info("\n2. Adding message to thread...")
                message = await client.agents.threads.messages.create(
                    thread_id=thread.id,
                    role="user",
                    content=test_message
                )
                logger.info(f"   ✓ Message added: {message.id}")
                
                # 3. Create and process run
                logger.info("\n3. Creating run...")
                run = await client.agents.threads.runs.create(
                    thread_id=thread.id,
                    assistant_id=ceo_agent_id
                )
                logger.info(f"   ✓ Run created: {run.id}")
                logger.info(f"   Status: {run.status}")
                
                # 4. Wait for run to complete
                logger.info("\n4. Processing run...")
                max_attempts = 30
                attempt = 0
                
                while run.status in ["queued", "in_progress", "requires_action"] and attempt < max_attempts:
                    await asyncio.sleep(2)
                    run = await client.agents.threads.runs.get(thread_id=thread.id, run_id=run.id)
                    logger.info(f"   Status: {run.status}")
                    
                    # Check if function call is required
                    if run.status == "requires_action":
                        logger.info("\n   🎯 FUNCTION CALL DETECTED!")
                        if hasattr(run, 'required_action') and run.required_action:
                            tool_calls = run.required_action.submit_tool_outputs.tool_calls
                            for tool_call in tool_calls:
                                logger.info(f"   Function: {tool_call.function.name}")
                                logger.info(f"   Arguments: {tool_call.function.arguments}")
                                
                                # Parse arguments to show details
                                try:
                                    args = json.loads(tool_call.function.arguments)
                                    logger.info("   Parsed arguments:")
                                    for key, value in args.items():
                                        logger.info(f"     - {key}: {value}")
                                except:
                                    pass
                    
                    attempt += 1
                
                # 5. Get messages from thread
                logger.info("\n5. Getting agent response...")
                messages = client.agents.threads.messages.list(thread_id=thread.id)
                
                # Print all messages in reverse order (oldest first)
                all_messages = []
                async for msg in messages:
                    all_messages.append(msg)
                
                all_messages.reverse()
                
                for msg in all_messages:
                    if msg.role == "assistant":
                        logger.info(f"\n🤖 AGENT RESPONSE:")
                        if msg.content:
                            for content_item in msg.content:
                                if hasattr(content_item, 'text') and content_item.text:
                                    logger.info(f"{content_item.text.value}")
                
                # 6. Check run steps for more details
                logger.info("\n6. Checking run steps...")
                steps = client.agents.threads.runs.steps.list(thread_id=thread.id, run_id=run.id)
                
                step_count = 0
                async for step in steps:
                    step_count += 1
                    logger.info(f"\n   Step {step_count}:")
                    logger.info(f"   Type: {step.type}")
                    logger.info(f"   Status: {step.status}")
                    
                    if step.type == "tool_calls" and hasattr(step, 'step_details'):
                        if hasattr(step.step_details, 'tool_calls'):
                            for tool_call in step.step_details.tool_calls:
                                if hasattr(tool_call, 'code_interpreter'):
                                    logger.info("   Code Interpreter:")
                                    if hasattr(tool_call.code_interpreter, 'input'):
                                        logger.info(f"   Input: {tool_call.code_interpreter.input[:200]}...")
                                    if hasattr(tool_call.code_interpreter, 'outputs'):
                                        for output in tool_call.code_interpreter.outputs:
                                            if hasattr(output, 'logs'):
                                                logger.info(f"   Output: {output.logs[:200]}...")
                
                # Final status
                logger.info(f"\n7. Final run status: {run.status}")
                
                if run.status == "completed":
                    logger.info("   ✅ Run completed successfully!")
                elif run.status == "failed":
                    logger.info("   ❌ Run failed!")
                    if hasattr(run, 'last_error'):
                        logger.info(f"   Error: {run.last_error}")
                
                # Summary
                logger.info("\n" + "="*60)
                logger.info("TEST SUMMARY")
                logger.info("="*60)
                logger.info(f"Thread ID: {thread.id}")
                logger.info(f"Run ID: {run.id}")
                logger.info(f"Final Status: {run.status}")
                logger.info(f"Test User ID: {test_user_id}")
                logger.info(f"Test Timestamp: {test_timestamp}")
                
            except Exception as e:
                logger.error(f"\n❌ ERROR: {type(e).__name__}: {str(e)}")
                import traceback
                traceback.print_exc()

if __name__ == "__main__":
    print("\n🚀 Starting Direct CEO Log Agent Test...\n")
    asyncio.run(test_ceo_log_direct())