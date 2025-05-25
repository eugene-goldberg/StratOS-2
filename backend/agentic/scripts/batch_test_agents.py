#!/usr/bin/env python3
"""
Batch testing script for all StratOS agents.
Tests each agent with multiple scenarios and generates a comprehensive report.
"""

import os
import sys
import asyncio
import json
from datetime import datetime
from typing import Dict, List, Any, Tuple
from colorama import init, Fore, Style
import time

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.agent_interaction_client import StratosAgentClient

# Initialize colorama
init()

# Test scenarios for each agent
AGENT_TEST_SCENARIOS = {
    # Strategic Foundation & Insights System
    "StrategicContextRouter": [
        "What are our strategic priorities?",
        "Tell me about our company vision",
        "I need to log an important meeting outcome",
        "Show me patterns in our recent decisions"
    ],
    
    "CEOLogAgent": [
        "Met with the board today. Approved 20M funding for expansion.",
        "Customer feedback session revealed need for better mobile experience",
        "Team morale is high after successful product launch",
        "Considering strategic partnership with CloudTech Inc"
    ],
    
    "NorthStarAgent": [
        "What are our core values?",
        "Define our mission statement",
        "What is our 5-year vision?",
        "How do our values guide decision making?"
    ],
    
    "MemoryRecallAgent": [
        "What decisions did we make last quarter?",
        "Show patterns in customer feedback",
        "What were the key themes from recent meetings?",
        "Recall discussions about market expansion"
    ],
    
    "PreferenceLearningAgent": [
        "I prefer data visualizations over tables",
        "Always include executive summaries at the top",
        "Focus on ROI metrics in reports",
        "Use bullet points for key insights"
    ],
    
    # Analysis & Intelligence System
    "AnalysisOrchestrator": [
        "Analyze our market position",
        "What are our competitive advantages?",
        "Identify risks in our strategy",
        "Perform a comprehensive business analysis"
    ],
    
    "SWOTTOWSAgent": [
        "Create a SWOT analysis for our product line",
        "What are our main strengths and weaknesses?",
        "Generate TOWS strategies for market expansion",
        "Analyze opportunities in the AI market"
    ],
    
    "RiskOpportunityAgent": [
        "What are the top 5 risks we face?",
        "Identify opportunities in emerging markets",
        "Assess cybersecurity risks",
        "What market trends could impact us?"
    ],
    
    "SOLinkageAgent": [
        "How does employee satisfaction impact productivity?",
        "Link customer feedback to revenue trends",
        "Find patterns between market share and innovation",
        "Connect operational metrics to strategic goals"
    ],
    
    # Planning & Execution System
    "PlanningCoordinator": [
        "Create a growth plan for next year",
        "How should we allocate resources?",
        "Plan our product roadmap",
        "Coordinate cross-functional initiatives"
    ],
    
    "InitiativeGenerationAgent": [
        "Generate initiatives for customer retention",
        "Create innovation initiatives",
        "Propose cost reduction initiatives",
        "Develop employee engagement initiatives"
    ],
    
    "ResourceOptimizationAgent": [
        "Optimize budget allocation across departments",
        "Balance resources between projects",
        "Identify resource bottlenecks",
        "Plan resource needs for Q3"
    ],
    
    "CanvasVisualizationAgent": [
        "Visualize our strategic plan",
        "Create a business model canvas",
        "Show relationships between initiatives",
        "Map our value proposition"
    ],
    
    "AlignmentScoringAgent": [
        "Score alignment of IT projects with business goals",
        "Measure strategic initiative effectiveness",
        "Evaluate team goals against company objectives",
        "Rate our strategic coherence"
    ],
    
    "ActionPlanningAgent": [
        "Break down the market expansion initiative",
        "Create action items for product launch",
        "Plan implementation steps for new CRM",
        "Detail tasks for digital transformation"
    ]
}

class BatchAgentTester:
    """Batch testing framework for StratOS agents."""
    
    def __init__(self):
        self.client = StratosAgentClient()
        self.test_results = {}
        self.performance_metrics = {}
        
    def print_progress(self, current: int, total: int, agent: str):
        """Print progress bar."""
        progress = current / total
        bar_length = 40
        filled = int(bar_length * progress)
        bar = '█' * filled + '░' * (bar_length - filled)
        
        print(f"\r{Fore.CYAN}Testing agents: [{bar}] {current}/{total} - {agent}{Style.RESET_ALL}", 
              end='', flush=True)
        
    async def test_agent(self, agent_name: str, scenarios: List[str]) -> Dict[str, Any]:
        """Test a single agent with multiple scenarios."""
        agent_results = {
            "agent": agent_name,
            "total_scenarios": len(scenarios),
            "successful": 0,
            "failed": 0,
            "avg_response_time": 0,
            "scenarios": []
        }
        
        total_time = 0
        
        for scenario in scenarios:
            start_time = time.time()
            
            try:
                response = await self.client.chat_with_agent(
                    agent_name,
                    scenario
                )
                
                elapsed_time = time.time() - start_time
                total_time += elapsed_time
                
                if "error" in response:
                    agent_results["failed"] += 1
                    scenario_result = {
                        "scenario": scenario,
                        "success": False,
                        "error": response["error"],
                        "response_time": elapsed_time
                    }
                else:
                    agent_results["successful"] += 1
                    scenario_result = {
                        "scenario": scenario,
                        "success": True,
                        "response_length": len(response.get("response", "")),
                        "response_time": elapsed_time,
                        "thread_id": response.get("thread_id")
                    }
                    
            except Exception as e:
                elapsed_time = time.time() - start_time
                total_time += elapsed_time
                agent_results["failed"] += 1
                scenario_result = {
                    "scenario": scenario,
                    "success": False,
                    "error": str(e),
                    "response_time": elapsed_time
                }
                
            agent_results["scenarios"].append(scenario_result)
            
        # Calculate average response time
        agent_results["avg_response_time"] = total_time / len(scenarios) if scenarios else 0
        agent_results["success_rate"] = agent_results["successful"] / len(scenarios) if scenarios else 0
        
        return agent_results
        
    async def run_batch_tests(self):
        """Run tests for all agents."""
        print(f"{Fore.CYAN}{'='*60}")
        print("StratOS Agent Batch Testing")
        print(f"{'='*60}{Style.RESET_ALL}\n")
        
        agents = await self.client.list_agents()
        total_agents = len(agents)
        
        print(f"Found {total_agents} deployed agents\n")
        
        # Test each agent
        for i, agent_name in enumerate(agents):
            self.print_progress(i, total_agents, agent_name)
            
            # Get test scenarios for this agent
            scenarios = AGENT_TEST_SCENARIOS.get(agent_name, [
                "Hello, can you help me?",
                "What are your capabilities?",
                "Tell me about your role"
            ])
            
            # Test the agent
            results = await self.test_agent(agent_name, scenarios)
            self.test_results[agent_name] = results
            
            # Brief pause between agents to avoid rate limiting
            await asyncio.sleep(0.5)
            
        self.print_progress(total_agents, total_agents, "Complete")
        print("\n")  # New line after progress bar
        
    def generate_summary_report(self):
        """Generate a summary report of all tests."""
        print(f"\n{Fore.CYAN}{'='*60}")
        print("Test Summary Report")
        print(f"{'='*60}{Style.RESET_ALL}\n")
        
        # Group by system
        systems = {
            "Strategic Foundation & Insights": [],
            "Analysis & Intelligence": [],
            "Planning & Execution": []
        }
        
        # Categorize agents
        for agent_name, results in self.test_results.items():
            if agent_name in ["StrategicContextRouter", "CEOLogAgent", "NorthStarAgent", 
                             "MemoryRecallAgent", "PreferenceLearningAgent"]:
                systems["Strategic Foundation & Insights"].append((agent_name, results))
            elif agent_name in ["AnalysisOrchestrator", "SWOTTOWSAgent", 
                               "RiskOpportunityAgent", "SOLinkageAgent"]:
                systems["Analysis & Intelligence"].append((agent_name, results))
            else:
                systems["Planning & Execution"].append((agent_name, results))
                
        # Print system summaries
        total_tests = 0
        total_successful = 0
        
        for system_name, agents in systems.items():
            print(f"{Fore.YELLOW}{system_name}:{Style.RESET_ALL}")
            
            system_tests = 0
            system_successful = 0
            
            for agent_name, results in agents:
                success_rate = results["success_rate"] * 100
                avg_time = results["avg_response_time"]
                
                system_tests += results["total_scenarios"]
                system_successful += results["successful"]
                
                color = Fore.GREEN if success_rate >= 80 else Fore.YELLOW if success_rate >= 50 else Fore.RED
                
                print(f"  {agent_name}:")
                print(f"    Success Rate: {color}{success_rate:.1f}%{Style.RESET_ALL} "
                      f"({results['successful']}/{results['total_scenarios']})")
                print(f"    Avg Response Time: {avg_time:.2f}s")
                
                # Show any failures
                failures = [s for s in results["scenarios"] if not s["success"]]
                if failures:
                    print(f"    {Fore.RED}Failures:{Style.RESET_ALL}")
                    for f in failures[:2]:  # Show first 2 failures
                        print(f"      - {f['scenario'][:50]}...")
                        print(f"        Error: {f.get('error', 'Unknown')[:50]}...")
                        
            system_success_rate = (system_successful / system_tests * 100) if system_tests > 0 else 0
            print(f"\n  {Fore.CYAN}System Success Rate: {system_success_rate:.1f}%{Style.RESET_ALL}\n")
            
            total_tests += system_tests
            total_successful += system_successful
            
        # Overall summary
        overall_success_rate = (total_successful / total_tests * 100) if total_tests > 0 else 0
        
        print(f"{Fore.CYAN}{'='*60}")
        print(f"Overall Results:{Style.RESET_ALL}")
        print(f"  Total Tests: {total_tests}")
        print(f"  Successful: {total_successful}")
        print(f"  Failed: {total_tests - total_successful}")
        print(f"  Success Rate: {Fore.GREEN if overall_success_rate >= 80 else Fore.YELLOW}{overall_success_rate:.1f}%{Style.RESET_ALL}")
        
        # Performance summary
        avg_response_times = [r["avg_response_time"] for r in self.test_results.values()]
        if avg_response_times:
            print(f"\n{Fore.CYAN}Performance Metrics:{Style.RESET_ALL}")
            print(f"  Avg Response Time: {sum(avg_response_times)/len(avg_response_times):.2f}s")
            print(f"  Min Response Time: {min(avg_response_times):.2f}s")
            print(f"  Max Response Time: {max(avg_response_times):.2f}s")
            
    def save_detailed_results(self):
        """Save detailed test results to file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"batch_test_results_{timestamp}.json"
        
        report_data = {
            "timestamp": timestamp,
            "summary": {
                "total_agents": len(self.test_results),
                "total_tests": sum(r["total_scenarios"] for r in self.test_results.values()),
                "total_successful": sum(r["successful"] for r in self.test_results.values()),
                "total_failed": sum(r["failed"] for r in self.test_results.values())
            },
            "agent_results": self.test_results
        }
        
        with open(filename, 'w') as f:
            json.dump(report_data, f, indent=2)
            
        print(f"\n{Fore.GREEN}Detailed results saved to: {filename}{Style.RESET_ALL}")
        
    async def run(self):
        """Run the batch testing process."""
        try:
            await self.run_batch_tests()
            self.generate_summary_report()
            self.save_detailed_results()
        finally:
            await self.client.close()


async def main():
    """Main entry point."""
    tester = BatchAgentTester()
    await tester.run()


if __name__ == "__main__":
    asyncio.run(main())