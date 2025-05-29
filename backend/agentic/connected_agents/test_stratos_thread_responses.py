#!/usr/bin/env python3
"""
Test StratOS agents using thread-based approach to get full responses.
This approach properly captures tool invocation results.
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

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def test_thread_based_responses():
    """Test using thread-based approach to get complete responses."""
    
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
    logger.info("STRATOS AGENTS - THREAD-BASED RESPONSE TEST")
    logger.info("="*80)
    logger.info(f"Orchestrator: {orchestrator_id}")
    
    async with DefaultAzureCredential() as credential, \
               AIProjectClient(endpoint=endpoint, credential=credential) as client:
        
        # Test cases
        test_cases = [
            {
                "name": "CEO Log Tag Generation",
                "query": "Generate tags for this CEO log entry: 'Team meeting successful. Discussed Q2 roadmap, AI strategy, and budget allocation.'"
            },
            {
                "name": "North Star Definition",
                "query": "What should our north star metric be for customer retention in SaaS?"
            },
            {
                "name": "Memory Recall",
                "query": "What key decisions did we make in our last quarterly review?"
            }
        ]
        
        for test in test_cases:
            logger.info(f"\n{'='*80}")
            logger.info(f"TEST: {test['name']}")
            logger.info(f"{'='*80}")
            logger.info(f"Query: {test['query']}")
            
            # Create thread
            thread = await client.agents.create_thread()
            logger.info(f"Thread created: {thread.id}")
            
            # Add message
            message = await client.agents.create_message(
                thread_id=thread.id,
                role="user",
                content=test['query']
            )
            logger.info(f"Message added: {message.id}")
            
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
                run = await client.agents.get_run(thread_id=thread.id, run_id=run.id)
                logger.info(f"Poll {poll_count}: Status = {run.status}")
                
                # Handle tool calls if needed
                if run.status == "requires_action" and hasattr(run, 'required_action'):
                    logger.info("Tool call required - this shouldn't happen with connected agents")
            
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
                    "role": msg.role,
                    "content": content,
                    "created_at": msg.created_at
                })
            
            # Sort by creation time
            message_list.sort(key=lambda x: x['created_at'])
            
            for msg in message_list:
                logger.info(f"\n{msg['role'].upper()}:")
                logger.info(msg['content'])
            
            # Analyze response
            assistant_messages = [m for m in message_list if m['role'] == 'assistant']
            if assistant_messages:
                final_response = assistant_messages[-1]['content']
                
                logger.info(f"\nRESPONSE ANALYSIS:")
                logger.info("-" * 60)
                
                # Check for delegation
                if "I'll connect you with" in final_response:
                    logger.info("✅ Delegation announcement found")
                else:
                    logger.info("❌ No delegation announcement")
                
                # Check for actual content
                content_indicators = {
                    "CEO Log": ["Tags:", "Generated tags:", "#", "Keywords:", "Themes:"],
                    "North Star": ["metric", "measure", "KPI", "indicator", "goal"],
                    "Memory Recall": ["decision", "discussed", "agreed", "concluded", "outcome"]
                }
                
                test_type = test['name'].split()[0] + " " + test['name'].split()[1]
                relevant_indicators = content_indicators.get(test_type, [])
                
                has_content = any(indicator in final_response for indicator in relevant_indicators)
                if has_content:
                    logger.info("✅ Specialist response content detected")
                else:
                    logger.info("❌ No specialist response content found")
                    logger.info(f"   (Looked for: {relevant_indicators})")
            
            # Check run steps for debugging
            steps = await client.agents.list_run_steps(thread_id=thread.id, run_id=run.id)
            
            logger.info(f"\nRUN STEPS:")
            logger.info("-" * 60)
            for step in steps.data:
                logger.info(f"Step {step.id}: {step.type} - {step.status}")
                
                if hasattr(step, 'step_details'):
                    if hasattr(step.step_details, 'tool_calls') and step.step_details.tool_calls:
                        for tool_call in step.step_details.tool_calls:
                            logger.info(f"  Tool: {getattr(tool_call, 'type', 'unknown')}")
                            
                            # Check for connected agent details
                            if hasattr(tool_call, 'connected_agent'):
                                logger.info(f"    Connected Agent ID: {tool_call.connected_agent.assistant_id}")
                                
                            # Check for code interpreter (which shouldn't be there)
                            if hasattr(tool_call, 'code_interpreter'):
                                logger.info(f"    Code Interpreter: {tool_call.code_interpreter}")
            
            # Small delay between tests
            await asyncio.sleep(3)


if __name__ == "__main__":
    asyncio.run(test_thread_based_responses())