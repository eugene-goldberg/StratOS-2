#!/usr/bin/env python3
"""
Test the full multi-agent orchestration flow with tool calling
"""

import os
import asyncio
import aiohttp
import json
import logging
from datetime import datetime
from dotenv import load_dotenv
from azure.identity.aio import DefaultAzureCredential

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
current_dir = os.path.dirname(os.path.abspath(__file__))
agentic_dir = os.path.dirname(current_dir)
env_path = os.path.join(agentic_dir, '.env')
load_dotenv(env_path)

async def test_multi_agent_orchestration():
    """Test the MainOrchestratorAgent with full tool calling to specialist agents"""
    
    # Configuration
    orchestrator_id = "asst_PkBVaNwenBlxV3rfPuiunywU"
    endpoint = os.getenv("AZURE_AI_AGENT_ENDPOINT")
    api_version = os.getenv("AZURE_AI_AGENT_API_VERSION", "2024-12-01-preview")
    
    # Load specialist agent IDs
    specialist_agents = {
        "CEOLogAgent": os.getenv("CEO_LOG_AGENT_ID"),
        "NorthStarAgent": os.getenv("NORTH_STAR_AGENT_ID"),
        "SWOTTOWSAgent": os.getenv("SWOT_TOWS_AGENT_ID"),
        "MemoryRecallAgent": os.getenv("MEMORY_RECALL_AGENT_ID"),
        "PreferenceLearningAgent": os.getenv("PREFERENCE_LEARNING_AGENT_ID"),
        "RiskOpportunityAgent": os.getenv("RISK_OPPORTUNITY_AGENT_ID"),
        "SOLinkageAgent": os.getenv("SO_LINKAGE_AGENT_ID"),
        "InitiativeGenerationAgent": os.getenv("INITIATIVE_GENERATION_AGENT_ID"),
        "ResourceOptimizationAgent": os.getenv("RESOURCE_OPTIMIZATION_AGENT_ID"),
        "ActionPlanningAgent": os.getenv("ACTION_PLANNING_AGENT_ID"),
        "CanvasVisualizationAgent": os.getenv("CANVAS_VISUALIZATION_AGENT_ID"),
        "AlignmentScoringAgent": os.getenv("ALIGNMENT_SCORING_AGENT_ID")
    }
    
    # Test cases
    test_cases = [
        {
            "name": "CEO Log Entry",
            "message": "I need to record my thoughts about the market downturn and its effect on Q3 projections.",
            "expected_agent": "CEOLogAgent"
        },
        {
            "name": "Vision Query",
            "message": "What is our company's core vision statement?",
            "expected_agent": "NorthStarAgent"
        },
        {
            "name": "SWOT Analysis",
            "message": "Perform a SWOT analysis for the new Alpha project.",
            "expected_agent": "SWOTTOWSAgent"
        }
    ]
    
    if not endpoint:
        logger.error("AZURE_AI_AGENT_ENDPOINT not set")
        return
        
    logger.info(f"Using endpoint: {endpoint}")
    logger.info(f"Testing orchestrator: {orchestrator_id}")
    
    try:
        # Get credential
        async with DefaultAzureCredential() as credential:
            # Get token
            token = await credential.get_token("https://management.azure.com/.default")
            
            headers = {
                "Authorization": f"Bearer {token.token}",
                "Content-Type": "application/json"
            }
            
            async with aiohttp.ClientSession() as session:
                for test_case in test_cases:
                    print(f"\n{'='*80}")
                    print(f"TEST: {test_case['name']}")
                    print(f"{'='*80}")
                    print(f"User: {test_case['message']}")
                    
                    # Create thread
                    thread_url = f"{endpoint}/threads?api-version={api_version}"
                    async with session.post(thread_url, headers=headers, json={}) as response:
                        if response.status != 200:
                            error = await response.text()
                            logger.error(f"Failed to create thread: {response.status} - {error}")
                            continue
                        thread_data = await response.json()
                        thread_id = thread_data["id"]
                        logger.info(f"Created thread: {thread_id}")
                    
                    # Add message
                    message_url = f"{endpoint}/threads/{thread_id}/messages?api-version={api_version}"
                    message_data = {
                        "role": "user",
                        "content": test_case["message"]
                    }
                    async with session.post(message_url, headers=headers, json=message_data) as response:
                        if response.status != 200:
                            error = await response.text()
                            logger.error(f"Failed to add message: {response.status} - {error}")
                            continue
                        logger.info("Message added successfully")
                    
                    # Create run
                    run_url = f"{endpoint}/threads/{thread_id}/runs?api-version={api_version}"
                    run_data = {
                        "assistant_id": orchestrator_id
                    }
                    async with session.post(run_url, headers=headers, json=run_data) as response:
                        if response.status != 200:
                            error = await response.text()
                            logger.error(f"Failed to create run: {response.status} - {error}")
                            continue
                        run_response = await response.json()
                        run_id = run_response["id"]
                        logger.info(f"Created run: {run_id}")
                    
                    # Poll for completion or tool calls
                    run_status_url = f"{endpoint}/threads/{thread_id}/runs/{run_id}?api-version={api_version}"
                    max_iterations = 30
                    iteration = 0
                    
                    while iteration < max_iterations:
                        async with session.get(run_status_url, headers=headers) as response:
                            if response.status != 200:
                                error = await response.text()
                                logger.error(f"Failed to get run status: {response.status} - {error}")
                                break
                            
                            run_status = await response.json()
                            status = run_status["status"]
                            logger.info(f"Run status: {status}")
                            
                            if status == "completed":
                                logger.info("✅ Run completed successfully")
                                break
                                
                            elif status == "requires_action":
                                # Handle tool calls
                                logger.info("🔧 Orchestrator is making tool calls...")
                                required_action = run_status.get("required_action", {})
                                tool_calls = required_action.get("submit_tool_outputs", {}).get("tool_calls", [])
                                
                                tool_outputs = []
                                for tool_call in tool_calls:
                                    tool_call_id = tool_call["id"]
                                    function = tool_call["function"]
                                    function_name = function["name"]
                                    arguments = json.loads(function["arguments"])
                                    
                                    logger.info(f"Tool call: {function_name}")
                                    logger.info(f"Arguments: {arguments}")
                                    
                                    # Check if it's routing to a specialist
                                    if function_name == "route_to_specialist":
                                        specialist_name = arguments.get("specialist_agent_name")
                                        user_request = arguments.get("user_request")
                                        
                                        print(f"\n🎯 Orchestrator routing to: {specialist_name}")
                                        if specialist_name == test_case["expected_agent"]:
                                            print(f"✅ Correct routing!")
                                        else:
                                            print(f"❌ Expected {test_case['expected_agent']}, got {specialist_name}")
                                        
                                        # Get specialist agent ID
                                        specialist_id = specialist_agents.get(specialist_name)
                                        if specialist_id:
                                            # Call the specialist agent
                                            specialist_response = await call_specialist_agent(
                                                session, headers, endpoint, api_version,
                                                specialist_id, specialist_name, user_request
                                            )
                                            
                                            tool_outputs.append({
                                                "tool_call_id": tool_call_id,
                                                "output": specialist_response
                                            })
                                        else:
                                            tool_outputs.append({
                                                "tool_call_id": tool_call_id,
                                                "output": f"Error: Specialist agent {specialist_name} not found"
                                            })
                                
                                # Submit tool outputs
                                if tool_outputs:
                                    submit_url = f"{endpoint}/threads/{thread_id}/runs/{run_id}/submit_tool_outputs?api-version={api_version}"
                                    submit_data = {"tool_outputs": tool_outputs}
                                    
                                    async with session.post(submit_url, headers=headers, json=submit_data) as response:
                                        if response.status != 200:
                                            error = await response.text()
                                            logger.error(f"Failed to submit tool outputs: {response.status} - {error}")
                                        else:
                                            logger.info("Tool outputs submitted successfully")
                                
                            elif status in ["failed", "cancelled", "expired"]:
                                logger.error(f"❌ Run failed with status: {status}")
                                if "last_error" in run_status:
                                    logger.error(f"Error: {run_status['last_error']}")
                                break
                        
                        await asyncio.sleep(2)
                        iteration += 1
                    
                    # Get final messages
                    messages_url = f"{endpoint}/threads/{thread_id}/messages?api-version={api_version}"
                    async with session.get(messages_url, headers=headers) as response:
                        if response.status == 200:
                            messages_data = await response.json()
                            
                            # Find orchestrator's final response
                            for message in messages_data.get("data", []):
                                if message["role"] == "assistant":
                                    content = message.get("content", [])
                                    if content and len(content) > 0:
                                        text = content[0].get("text", {}).get("value", "")
                                        print(f"\nOrchestrator: {text}")
                                        break
                    
                    # Clean up thread
                    delete_url = f"{endpoint}/threads/{thread_id}?api-version={api_version}"
                    async with session.delete(delete_url, headers=headers) as response:
                        if response.status == 204:
                            logger.info("Thread deleted successfully")
                            
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)

async def call_specialist_agent(session, headers, endpoint, api_version, agent_id, agent_name, user_request):
    """Call a specialist agent and get its response"""
    logger.info(f"Calling specialist agent {agent_name} (ID: {agent_id})")
    
    try:
        # Create thread for specialist
        thread_url = f"{endpoint}/threads?api-version={api_version}"
        async with session.post(thread_url, headers=headers, json={}) as response:
            if response.status != 200:
                return f"Error creating thread for {agent_name}"
            thread_data = await response.json()
            thread_id = thread_data["id"]
        
        # Add message
        message_url = f"{endpoint}/threads/{thread_id}/messages?api-version={api_version}"
        message_data = {"role": "user", "content": user_request}
        async with session.post(message_url, headers=headers, json=message_data) as response:
            if response.status != 200:
                return f"Error adding message for {agent_name}"
        
        # Create run
        run_url = f"{endpoint}/threads/{thread_id}/runs?api-version={api_version}"
        run_data = {"assistant_id": agent_id}
        async with session.post(run_url, headers=headers, json=run_data) as response:
            if response.status != 200:
                return f"Error creating run for {agent_name}"
            run_response = await response.json()
            run_id = run_response["id"]
        
        # Wait for completion
        run_status_url = f"{endpoint}/threads/{thread_id}/runs/{run_id}?api-version={api_version}"
        for _ in range(15):
            async with session.get(run_status_url, headers=headers) as response:
                if response.status == 200:
                    run_status = await response.json()
                    if run_status["status"] == "completed":
                        break
            await asyncio.sleep(1)
        
        # Get response
        messages_url = f"{endpoint}/threads/{thread_id}/messages?api-version={api_version}"
        async with session.get(messages_url, headers=headers) as response:
            if response.status == 200:
                messages_data = await response.json()
                for message in messages_data.get("data", []):
                    if message["role"] == "assistant":
                        content = message.get("content", [])
                        if content and len(content) > 0:
                            specialist_response = content[0].get("text", {}).get("value", "")
                            logger.info(f"{agent_name} responded (length: {len(specialist_response)})")
                            print(f"\n📝 {agent_name}: {specialist_response[:200]}...")
                            return specialist_response
        
        # Clean up
        delete_url = f"{endpoint}/threads/{thread_id}?api-version={api_version}"
        await session.delete(delete_url, headers=headers)
        
        return f"{agent_name} completed but no response found"
        
    except Exception as e:
        logger.error(f"Error calling {agent_name}: {e}")
        return f"Error calling {agent_name}: {str(e)}"

if __name__ == "__main__":
    print("🚀 Testing StratOS Multi-Agent Orchestration with Tool Calling")
    print("="*80)
    asyncio.run(test_multi_agent_orchestration())