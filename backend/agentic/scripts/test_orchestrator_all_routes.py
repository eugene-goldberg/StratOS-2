#!/usr/bin/env python3
"""
Comprehensive test of the Main Orchestrator's routing to all 13 specialist agents.
Tests routing decisions for each agent with appropriate scenarios.
"""

import asyncio
import os
import json
from dotenv import load_dotenv
from azure.identity.aio import DefaultAzureCredential
from semantic_kernel.agents import AzureAIAgent, AzureAIAgentSettings

# Load environment
current_dir = os.path.dirname(os.path.abspath(__file__))
agentic_dir = os.path.dirname(current_dir)
env_path = os.path.join(agentic_dir, '.env')
load_dotenv(env_path)

async def test_single_routing(client, orchestrator_id, test_message):
    """Test a single routing scenario."""
    # Create thread
    thread = await client.agents.threads.create()
    thread_id = thread.id
    
    # Add message
    await client.agents.messages.create(
        thread_id=thread_id,
        role="user", 
        content=test_message
    )
    
    # Create run
    run = await client.agents.runs.create(
        thread_id=thread_id,
        agent_id=orchestrator_id
    )
    
    # Wait for completion
    while run.status in ["queued", "in_progress"]:
        await asyncio.sleep(1)
        run = await client.agents.runs.get(
            thread_id=thread_id,
            run_id=run.id
        )
    
    # Get the latest assistant message
    messages = client.agents.messages.list(thread_id=thread_id)
    
    routing_response = None
    async for msg in messages:
        if msg.role == "assistant" and msg.content:
            for content in msg.content:
                if hasattr(content, 'text'):
                    routing_response = content.text.value
                    break
            if routing_response:
                break
    
    # Clean up
    await client.agents.threads.delete(thread_id=thread_id)
    
    return routing_response

async def main():
    # Load orchestrator ID
    config_path = os.path.join(agentic_dir, "deployment_configs", "main_orchestrator_deployment.json")
    with open(config_path, 'r') as f:
        config = json.load(f)
        orchestrator_id = config['agent_id']
    
    print(f"Testing Main Orchestrator Routing: {orchestrator_id}")
    print("=" * 80)
    
    # Comprehensive test scenarios for each agent
    test_scenarios = [
        # Strategic Foundation & Insights System (5 agents)
        {
            "agent": "CEOLogAgent",
            "tests": [
                "I need to record my thoughts about the market downturn",
                "Let me log my observations from today's board meeting",
                "I want to capture my reflections on our company culture"
            ]
        },
        {
            "agent": "VisionMissionAgent", 
            "tests": [
                "What is our company's vision and mission?",
                "Help me refine our organizational purpose statement",
                "Show me our core values and strategic direction"
            ]
        },
        {
            "agent": "NorthStarGoalsAgent",
            "tests": [
                "Show me our strategic goals and objectives",
                "What are our key performance indicators?",
                "Display our long-term targets and milestones"
            ]
        },
        {
            "agent": "MemoryRecallAgent",
            "tests": [
                "I've done this before when launching in Europe",
                "What strategies worked in our last market expansion?",
                "Recall our previous approach to cost reduction"
            ]
        },
        {
            "agent": "PreferenceLearningAgent",
            "tests": [
                "I prefer data-driven decision making",
                "Remember that I like concise executive summaries",
                "My communication style is direct and analytical"
            ]
        },
        
        # Analysis & Intelligence System (4 agents)
        {
            "agent": "SWOTAnalysisAgent",
            "tests": [
                "Can you perform a SWOT analysis for our new product?",
                "Analyze our competitive position using SWOT",
                "What are our strengths and weaknesses?"
            ]
        },
        {
            "agent": "OpportunityIdentificationAgent",
            "tests": [
                "What opportunities exist in the Asian market?",
                "Identify growth opportunities in our industry",
                "Where can we expand our market share?"
            ]
        },
        {
            "agent": "RiskAssessmentAgent",
            "tests": [
                "Analyze the risks of expanding our product line",
                "What threats do we face from new regulations?",
                "Assess cybersecurity risks for our operations"
            ]
        },
        {
            "agent": "PerformanceAnalyticsAgent",
            "tests": [
                "How does our Q3 performance compare to last year?",
                "Show me revenue trends and analytics",
                "Analyze our operational efficiency metrics"
            ]
        },
        
        # Planning & Execution System (6 agents)
        {
            "agent": "StrategicPlanningAgent",
            "tests": [
                "Create a roadmap for our digital transformation",
                "Develop a strategic plan for market expansion",
                "Design a 5-year growth strategy"
            ]
        },
        {
            "agent": "ResourceAllocationAgent",
            "tests": [
                "How should we allocate resources for Q4?",
                "Optimize budget distribution across departments",
                "Plan resource allocation for new initiatives"
            ]
        },
        {
            "agent": "InitiativeDefinitionAgent",
            "tests": [
                "Define initiatives for improving customer satisfaction",
                "Create action items for sustainability goals",
                "Develop initiatives for employee engagement"
            ]
        },
        {
            "agent": "MilestoneTrackingAgent",
            "tests": [
                "Set milestones for the product launch",
                "Track progress on our transformation journey",
                "Define key checkpoints for project delivery"
            ]
        },
        {
            "agent": "ProgressMonitoringAgent",
            "tests": [
                "Monitor progress on our expansion project",
                "Show me the status of current initiatives",
                "Track completion of strategic objectives"
            ]
        },
        {
            "agent": "ReportingAgent",
            "tests": [
                "Generate a report on our strategic execution",
                "Create an executive summary of Q3 results",
                "Prepare a board presentation on progress"
            ]
        }
    ]
    
    settings = AzureAIAgentSettings()
    credential = DefaultAzureCredential()
    
    async with AzureAIAgent.create_client(credential=credential, settings=settings) as client:
        all_results = []
        agent_results = {}
        
        # Test each agent
        for agent_scenario in test_scenarios:
            agent_name = agent_scenario["agent"]
            agent_results[agent_name] = {"passed": 0, "failed": 0, "tests": []}
            
            print(f"\n{'='*60}")
            print(f"Testing routing to: {agent_name}")
            print(f"{'='*60}")
            
            for test_message in agent_scenario["tests"]:
                print(f"\nTest: \"{test_message}\"")
                
                try:
                    response = await test_single_routing(client, orchestrator_id, test_message)
                    
                    # Check if the response contains a routing decision
                    if response and "ROUTE TO:" in response:
                        # Extract the routed agent name
                        parts = response.split("ROUTE TO:")[1].split("-")
                        if parts:
                            routed_agent = parts[0].strip()
                            reason = response.split("REASON:")[1].strip() if "REASON:" in response else ""
                            
                            # Check if routing is correct
                            success = agent_name in routed_agent or routed_agent in agent_name
                            status = "✅ PASS" if success else "❌ FAIL"
                            
                            print(f"Result: {status}")
                            print(f"Routed to: {routed_agent}")
                            if reason and len(reason) < 100:
                                print(f"Reason: {reason}")
                            
                            # Track results
                            test_result = {
                                "test": test_message,
                                "expected": agent_name,
                                "routed_to": routed_agent,
                                "success": success,
                                "response": response
                            }
                            
                            agent_results[agent_name]["tests"].append(test_result)
                            if success:
                                agent_results[agent_name]["passed"] += 1
                            else:
                                agent_results[agent_name]["failed"] += 1
                            
                            all_results.append(test_result)
                    else:
                        print(f"Result: ❌ FAIL - Invalid response format")
                        print(f"Response: {response[:200] if response else 'No response'}...")
                        
                        test_result = {
                            "test": test_message,
                            "expected": agent_name,
                            "routed_to": "ERROR",
                            "success": False,
                            "response": response
                        }
                        
                        agent_results[agent_name]["tests"].append(test_result)
                        agent_results[agent_name]["failed"] += 1
                        all_results.append(test_result)
                        
                except Exception as e:
                    print(f"Result: ❌ ERROR - {str(e)}")
                    
                    test_result = {
                        "test": test_message,
                        "expected": agent_name,
                        "routed_to": "ERROR",
                        "success": False,
                        "response": str(e)
                    }
                    
                    agent_results[agent_name]["tests"].append(test_result)
                    agent_results[agent_name]["failed"] += 1
                    all_results.append(test_result)
                
                # Small delay between tests
                await asyncio.sleep(0.5)
        
        # Print comprehensive summary
        print("\n" + "=" * 80)
        print("ROUTING TEST SUMMARY")
        print("=" * 80)
        
        # Overall statistics
        total_tests = len(all_results)
        passed_tests = sum(1 for r in all_results if r["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"\nOverall Results:")
        print(f"  Total Tests: {total_tests}")
        print(f"  Passed: {passed_tests}")
        print(f"  Failed: {failed_tests}")
        print(f"  Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        # Per-agent summary
        print(f"\nPer-Agent Results:")
        print(f"{'Agent':<30} {'Tests':<8} {'Passed':<8} {'Failed':<8} {'Rate':<8}")
        print("-" * 70)
        
        for agent_name, results in agent_results.items():
            total = results["passed"] + results["failed"]
            rate = (results["passed"] / total * 100) if total > 0 else 0
            print(f"{agent_name:<30} {total:<8} {results['passed']:<8} {results['failed']:<8} {rate:<8.1f}%")
        
        # List all failures
        if failed_tests > 0:
            print(f"\nFailed Tests Details:")
            print("-" * 70)
            for r in all_results:
                if not r["success"]:
                    print(f"Test: \"{r['test']}\"")
                    print(f"  Expected: {r['expected']}")
                    print(f"  Got: {r['routed_to']}")
                    print()
    
    await credential.close()

if __name__ == "__main__":
    asyncio.run(main())