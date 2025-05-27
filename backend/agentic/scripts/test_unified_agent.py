#!/usr/bin/env python3
"""
Test script for the Unified StratOS Agent.
This script tests direct tool execution without routing.
"""

import asyncio
import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [%(funcName)s] %(message)s')
logger = logging.getLogger(__name__)

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

# Load environment variables
env_path = Path(__file__).parent.parent / '.env'
logger.info(f"Loading .env from: {env_path}")
load_dotenv(env_path)

from azure.identity.aio import DefaultAzureCredential
from azure.ai.projects.aio import AIProjectClient

def _generate_tool_output(tool_name, arguments):
    """Generate mock tool outputs for testing."""
    import json
    
    try:
        args = json.loads(arguments) if arguments else {}
    except:
        args = {}
    
    # Generate relevant mock outputs for each tool
    tool_outputs = {
        "manage_ceo_log": {
            "status": "success",
            "entry_id": "log_12345",
            "message": "CEO log entry recorded successfully. Market downturn analysis and Q3 projections captured.",
            "timestamp": "2025-05-27T12:00:00Z",
            "sentiment": "concerned but optimistic",
            "key_topics": ["market downturn", "Q3 projections", "revenue impact", "cost optimization"]
        },
        "define_north_star": {
            "status": "success",
            "vision": "To revolutionize strategic planning through AI-powered insights and automation",
            "mission": "Empowering organizations to make data-driven decisions with confidence",
            "values": ["Innovation", "Transparency", "Customer Success", "Continuous Learning"],
            "alignment_score": 0.85,
            "market_trends": ["AI adoption", "Digital transformation", "Strategic automation"]
        },
        "perform_swot_analysis": {
            "status": "success",
            "strengths": ["Advanced AI capabilities", "First-mover advantage", "Strong technical team"],
            "weaknesses": ["Limited market presence", "High initial investment required"],
            "opportunities": ["Growing AI market", "Enterprise demand", "Partnership potential"],
            "threats": ["Competition from tech giants", "Regulatory uncertainty", "Market education needed"],
            "recommendations": ["Focus on differentiation", "Build strategic partnerships", "Invest in marketing"]
        },
        "recall_memory": {
            "status": "success",
            "relevant_memories": [
                {"date": "2025-05-20", "context": "CEO discussed market volatility concerns"},
                {"date": "2025-05-15", "context": "Strategic review of North Star goals"},
                {"date": "2025-05-10", "context": "Resource optimization initiative launched"}
            ],
            "insights": "Recent focus on market adaptation and efficiency improvements"
        },
        "generate_initiatives": {
            "status": "success",
            "initiatives": [
                {
                    "title": "Customer Retention Excellence Program",
                    "timeline": "3 months",
                    "resources": ["Customer Success Team", "Data Analytics", "Product Team"],
                    "milestones": ["Week 1-2: Analysis", "Week 3-6: Implementation", "Week 7-12: Optimization"],
                    "alignment_score": 0.92
                }
            ],
            "strategic_fit": "High alignment with growth objectives and customer-centric values"
        }
    }
    
    # Return the appropriate tool output or a generic one
    return json.dumps(tool_outputs.get(tool_name, {
        "status": "success",
        "message": f"Tool {tool_name} executed successfully",
        "data": args
    }))

async def test_unified_agent():
    """Test the Unified StratOS Agent with various requests."""
    
    # Get agent ID
    agent_id = os.getenv("STRATOS_UNIFIED_AGENT_ID")
    if not agent_id:
        logger.error("STRATOS_UNIFIED_AGENT_ID not found in .env")
        return
    
    # Hardcode endpoint since SDK discovery isn't working
    endpoint = "https://ai.azure.com/api/eastus/agents/v1.0/subscriptions/514bd6d3-2c02-45c6-a86f-29cf262a379a/resourceGroups/semantic-kernel-multi-agent-rg/providers/Microsoft.MachineLearningServices/workspaces/sk-multi-agent-project"
    
    logger.info(f"Testing Unified Agent ID: {agent_id}")
    logger.info(f"Using endpoint: {endpoint}")
    
    # Test cases that would have required multiple agents before
    test_cases = [
        {
            "name": "CEO Log Entry",
            "message": "I need to record my thoughts about the market downturn and its effect on Q3 projections. I'm concerned about revenue impact but see opportunities in cost optimization."
        },
        {
            "name": "Strategic Vision",
            "message": "What is our company's core vision statement and how does it align with current market trends?"
        },
        {
            "name": "SWOT Analysis",
            "message": "Perform a SWOT analysis for our new AI product launch, focusing on competitive advantages and market risks."
        },
        {
            "name": "Combined Analysis",
            "message": "Based on recent CEO observations about market conditions, generate strategic initiatives that align with our North Star goals and include resource optimization recommendations."
        },
        {
            "name": "Action Planning",
            "message": "Create a detailed action plan for improving customer retention, including timeline, resources needed, and alignment with strategic goals."
        }
    ]
    
    # Create credential
    credential = DefaultAzureCredential()
    
    try:
        # Create AI Project client
        async with AIProjectClient(
            endpoint=endpoint,
            credential=credential,
            api_version="2024-12-01-preview"
        ) as client:
            logger.info("Successfully connected to Azure AI Agent Service")
            
            # Get agent definition
            try:
                agent = await client.agents.get_agent(agent_id=agent_id)
                logger.info(f"Found agent: {agent.name}")
                logger.info(f"Tools available: {len(agent.tools) if hasattr(agent, 'tools') else 0}")
            except Exception as e:
                logger.error(f"Failed to get agent definition: {e}")
                return
            
            # Run test cases
            for i, test_case in enumerate(test_cases, 1):
                print("\n" + "="*80)
                print(f"TEST CASE {i}: {test_case['name']}")
                print("="*80)
                print(f"User: {test_case['message']}")
                print("-"*80)
                
                # Create a thread for this test
                thread = await client.agents.threads.create()
                logger.info(f"Created thread: {thread.id}")
                
                try:
                    # Add message to thread
                    await client.agents.messages.create(
                        thread_id=thread.id,
                        role="user",
                        content=test_case['message']
                    )
                    
                    # Create a run and wait for completion
                    logger.info(f"Creating run with thread_id={thread.id}, agent_id={agent_id}")
                    run = await client.agents.runs.create(
                        thread_id=thread.id,
                        body={"assistant_id": agent_id}
                    )
                    
                    print("Agent Response:")
                    tool_calls = []
                    
                    # Poll for run completion
                    while run.status in ["queued", "in_progress", "requires_action"]:
                        await asyncio.sleep(1)
                        run = await client.agents.runs.get(
                            thread_id=thread.id,
                            run_id=run.id
                        )
                        
                        if run.status == "requires_action":
                            # Handle tool calls
                            if hasattr(run, 'required_action') and hasattr(run.required_action, 'submit_tool_outputs'):
                                tool_outputs = []
                                
                                for tool_call in run.required_action.submit_tool_outputs.tool_calls:
                                    tool_calls.append(tool_call.function.name)
                                    logger.info(f"Tool called: {tool_call.function.name} with args: {tool_call.function.arguments}")
                                    
                                    # Generate mock tool outputs based on the tool name
                                    tool_output = {
                                        "tool_call_id": tool_call.id,
                                        "output": _generate_tool_output(tool_call.function.name, tool_call.function.arguments)
                                    }
                                    tool_outputs.append(tool_output)
                                
                                # Submit tool outputs
                                logger.info(f"Submitting {len(tool_outputs)} tool outputs")
                                run = await client.agents.runs.submit_tool_outputs(
                                    thread_id=thread.id,
                                    run_id=run.id,
                                    body={"tool_outputs": tool_outputs}
                                )
                                # Continue polling after submitting tool outputs
                                continue
                    
                    # Get messages after run completes
                    if run.status == "completed":
                        messages = client.agents.messages.list(
                            thread_id=thread.id,
                            order="desc",
                            limit=1
                        )
                        
                        # AsyncItemPaged needs to be iterated
                        async for message in messages:
                            # Get the first assistant message
                            if message.role == "assistant":
                                for content in message.content:
                                    if content.type == "text":
                                        print(content.text.value)
                                break
                    
                    continue  # Skip the streaming loop
                    
                    async for event in []:
                        # Handle different event types
                        if event.event == "thread.message.delta" and event.data.delta.content:
                            for content in event.data.delta.content:
                                if content.type == "text" and content.text.value:
                                    print(content.text.value, end="", flush=True)
                        
                        elif event.event == "thread.run.requires_action":
                            # Log tool calls
                            if hasattr(event.data, 'required_action') and hasattr(event.data.required_action, 'tool_calls'):
                                for tool_call in event.data.required_action.tool_calls:
                                    tool_calls.append(tool_call.function.name)
                                    logger.info(f"Tool called: {tool_call.function.name}")
                        
                        elif event.event == "thread.run.completed":
                            logger.info("Run completed successfully")
                        
                        elif event.event == "thread.run.failed":
                            logger.error(f"Run failed: {event.data}")
                    
                    print("\n" + "-"*80)
                    if tool_calls:
                        print(f"Tools used: {', '.join(tool_calls)}")
                    
                except Exception as e:
                    logger.error(f"Error during test case {i}: {e}")
                    print(f"\nError: {e}")
                    import traceback
                    traceback.print_exc()
                
                finally:
                    # Cleanup thread
                    try:
                        await client.agents.threads.delete(thread_id=thread.id)
                        logger.info(f"Deleted thread: {thread.id}")
                    except Exception as e:
                        logger.error(f"Error deleting thread: {e}")
                
                # Pause between tests
                if i < len(test_cases):
                    await asyncio.sleep(2)
            
            print("\n" + "="*80)
            print("ALL TESTS COMPLETED")
            print("="*80)
            
    except Exception as e:
        logger.error(f"Error testing unified agent: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("\n" + "="*80)
    print("TESTING STRATOS UNIFIED AGENT")
    print("="*80)
    print("This test demonstrates the unified agent handling requests")
    print("that would have required multiple agents and routing before.")
    print("="*80 + "\n")
    
    asyncio.run(test_unified_agent())