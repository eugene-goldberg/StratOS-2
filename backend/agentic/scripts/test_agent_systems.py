#!/usr/bin/env python3
"""
Test script for each StratOS agent system.
Tests Strategic Foundation, Analysis & Intelligence, and Planning & Execution systems.
"""

import os
import sys
import asyncio
import json
from datetime import datetime
from typing import Dict, List, Any
from colorama import init, Fore, Style

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.agent_interaction_client import StratosAgentClient

# Initialize colorama
init()

class AgentSystemTester:
    """Test harness for StratOS agent systems."""
    
    def __init__(self):
        self.client = StratosAgentClient()
        self.test_results = {
            "strategic_foundation": [],
            "analysis_intelligence": [],
            "planning_execution": []
        }
        
    def print_header(self, title: str):
        """Print a section header."""
        print(f"\n{Fore.CYAN}{'='*60}")
        print(f"{title}")
        print(f"{'='*60}{Style.RESET_ALL}\n")
        
    def print_test(self, test_name: str, agent: str):
        """Print test information."""
        print(f"{Fore.YELLOW}Test: {test_name}")
        print(f"Agent: {agent}{Style.RESET_ALL}")
        
    def print_result(self, success: bool, message: str):
        """Print test result."""
        if success:
            print(f"{Fore.GREEN}✓ Success: {message}{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}✗ Failed: {message}{Style.RESET_ALL}")
            
    async def test_strategic_foundation(self):
        """Test Strategic Foundation & Insights System."""
        self.print_header("Testing Strategic Foundation & Insights System")
        
        tests = [
            {
                "name": "Router - General Strategic Query",
                "agent": "StrategicContextRouter",
                "message": "What are the key strategic priorities for our company?",
                "expected": "route to appropriate agent"
            },
            {
                "name": "CEO Log - Entry Creation",
                "agent": "CEOLogAgent",
                "message": "Today we closed a major partnership deal with TechCorp. This will expand our market reach significantly.",
                "expected": "process log entry with tags and summary"
            },
            {
                "name": "North Star - Vision Query",
                "agent": "NorthStarAgent",
                "message": "What is our company's vision and core values?",
                "expected": "return vision and values information"
            },
            {
                "name": "Memory Recall - Pattern Recognition",
                "agent": "MemoryRecallAgent",
                "message": "What patterns have we seen in our customer feedback over the last quarter?",
                "expected": "recall and analyze patterns"
            },
            {
                "name": "Preference Learning - User Preferences",
                "agent": "PreferenceLearningAgent",
                "message": "I prefer concise executive summaries with bullet points rather than long paragraphs.",
                "expected": "learn and acknowledge preference"
            }
        ]
        
        for test in tests:
            self.print_test(test["name"], test["agent"])
            
            try:
                response = await self.client.chat_with_agent(
                    test["agent"],
                    test["message"]
                )
                
                if "error" in response:
                    self.print_result(False, response["error"])
                    self.test_results["strategic_foundation"].append({
                        "test": test["name"],
                        "agent": test["agent"],
                        "success": False,
                        "error": response["error"]
                    })
                else:
                    agent_response = response.get("response", "")
                    success = len(agent_response) > 0
                    self.print_result(success, f"Response length: {len(agent_response)} chars")
                    
                    # Show snippet of response
                    snippet = agent_response[:150] + "..." if len(agent_response) > 150 else agent_response
                    print(f"{Fore.CYAN}Response: {snippet}{Style.RESET_ALL}")
                    
                    self.test_results["strategic_foundation"].append({
                        "test": test["name"],
                        "agent": test["agent"],
                        "success": success,
                        "response_length": len(agent_response),
                        "thread_id": response.get("thread_id")
                    })
                    
            except Exception as e:
                self.print_result(False, str(e))
                self.test_results["strategic_foundation"].append({
                    "test": test["name"],
                    "agent": test["agent"],
                    "success": False,
                    "error": str(e)
                })
                
            print()  # Blank line between tests
            
    async def test_analysis_intelligence(self):
        """Test Analysis & Intelligence System."""
        self.print_header("Testing Analysis & Intelligence System")
        
        tests = [
            {
                "name": "Orchestrator - Analysis Request",
                "agent": "AnalysisOrchestrator",
                "message": "Analyze our competitive position in the market",
                "expected": "route to appropriate analysis agent"
            },
            {
                "name": "SWOT/TOWS - Strategic Analysis",
                "agent": "SWOTTOWSAgent",
                "message": "Perform a SWOT analysis for our cloud services division",
                "expected": "generate SWOT analysis"
            },
            {
                "name": "Risk/Opportunity - Risk Detection",
                "agent": "RiskOpportunityAgent",
                "message": "What are the key risks in our current expansion strategy?",
                "expected": "identify and analyze risks"
            },
            {
                "name": "S+O Linkage - Pattern Discovery",
                "agent": "SOLinkageAgent",
                "message": "How do our customer satisfaction scores relate to our revenue growth?",
                "expected": "discover linkage patterns"
            }
        ]
        
        for test in tests:
            self.print_test(test["name"], test["agent"])
            
            try:
                response = await self.client.chat_with_agent(
                    test["agent"],
                    test["message"]
                )
                
                if "error" in response:
                    self.print_result(False, response["error"])
                    self.test_results["analysis_intelligence"].append({
                        "test": test["name"],
                        "agent": test["agent"],
                        "success": False,
                        "error": response["error"]
                    })
                else:
                    agent_response = response.get("response", "")
                    success = len(agent_response) > 0
                    self.print_result(success, f"Response length: {len(agent_response)} chars")
                    
                    # Show snippet of response
                    snippet = agent_response[:150] + "..." if len(agent_response) > 150 else agent_response
                    print(f"{Fore.CYAN}Response: {snippet}{Style.RESET_ALL}")
                    
                    self.test_results["analysis_intelligence"].append({
                        "test": test["name"],
                        "agent": test["agent"],
                        "success": success,
                        "response_length": len(agent_response),
                        "thread_id": response.get("thread_id")
                    })
                    
            except Exception as e:
                self.print_result(False, str(e))
                self.test_results["analysis_intelligence"].append({
                    "test": test["name"],
                    "agent": test["agent"],
                    "success": False,
                    "error": str(e)
                })
                
            print()  # Blank line between tests
            
    async def test_planning_execution(self):
        """Test Planning & Execution System."""
        self.print_header("Testing Planning & Execution System")
        
        tests = [
            {
                "name": "Coordinator - Planning Request",
                "agent": "PlanningCoordinator",
                "message": "Create a plan to increase market share by 15% this year",
                "expected": "route to appropriate planning agent"
            },
            {
                "name": "Initiative Generation - New Initiative",
                "agent": "InitiativeGenerationAgent",
                "message": "Generate initiatives to improve customer retention",
                "expected": "generate strategic initiatives"
            },
            {
                "name": "Resource Optimization - Resource Planning",
                "agent": "ResourceOptimizationAgent",
                "message": "Optimize resource allocation for our Q2 projects",
                "expected": "optimize resource allocation"
            },
            {
                "name": "Canvas Visualization - Strategic View",
                "agent": "CanvasVisualizationAgent",
                "message": "Create a visual representation of our growth strategy",
                "expected": "generate canvas visualization"
            },
            {
                "name": "Alignment Scoring - Strategy Alignment",
                "agent": "AlignmentScoringAgent",
                "message": "Score the alignment between our IT initiatives and business goals",
                "expected": "calculate alignment scores"
            },
            {
                "name": "Action Planning - Task Breakdown",
                "agent": "ActionPlanningAgent",
                "message": "Break down the customer acquisition initiative into actionable tasks",
                "expected": "create detailed action plan"
            }
        ]
        
        for test in tests:
            self.print_test(test["name"], test["agent"])
            
            try:
                response = await self.client.chat_with_agent(
                    test["agent"],
                    test["message"]
                )
                
                if "error" in response:
                    self.print_result(False, response["error"])
                    self.test_results["planning_execution"].append({
                        "test": test["name"],
                        "agent": test["agent"],
                        "success": False,
                        "error": response["error"]
                    })
                else:
                    agent_response = response.get("response", "")
                    success = len(agent_response) > 0
                    self.print_result(success, f"Response length: {len(agent_response)} chars")
                    
                    # Show snippet of response
                    snippet = agent_response[:150] + "..." if len(agent_response) > 150 else agent_response
                    print(f"{Fore.CYAN}Response: {snippet}{Style.RESET_ALL}")
                    
                    self.test_results["planning_execution"].append({
                        "test": test["name"],
                        "agent": test["agent"],
                        "success": success,
                        "response_length": len(agent_response),
                        "thread_id": response.get("thread_id")
                    })
                    
            except Exception as e:
                self.print_result(False, str(e))
                self.test_results["planning_execution"].append({
                    "test": test["name"],
                    "agent": test["agent"],
                    "success": False,
                    "error": str(e)
                })
                
            print()  # Blank line between tests
            
    def generate_report(self):
        """Generate a summary report of all tests."""
        self.print_header("Test Summary Report")
        
        total_tests = 0
        total_passed = 0
        
        for system, results in self.test_results.items():
            system_name = system.replace("_", " ").title()
            passed = sum(1 for r in results if r.get("success", False))
            total = len(results)
            
            total_tests += total
            total_passed += passed
            
            success_rate = (passed / total * 100) if total > 0 else 0
            
            color = Fore.GREEN if success_rate >= 80 else Fore.YELLOW if success_rate >= 50 else Fore.RED
            print(f"{system_name}: {color}{passed}/{total} passed ({success_rate:.1f}%){Style.RESET_ALL}")
            
            # Show failed tests
            failed = [r for r in results if not r.get("success", False)]
            if failed:
                print(f"  {Fore.RED}Failed tests:{Style.RESET_ALL}")
                for f in failed:
                    print(f"    - {f['test']}: {f.get('error', 'No response')}")
                    
        print(f"\n{Fore.CYAN}Overall: {total_passed}/{total_tests} tests passed ({total_passed/total_tests*100:.1f}%){Style.RESET_ALL}")
        
        # Save detailed results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"test_results_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump({
                "timestamp": timestamp,
                "summary": {
                    "total_tests": total_tests,
                    "total_passed": total_passed,
                    "success_rate": total_passed/total_tests if total_tests > 0 else 0
                },
                "results": self.test_results
            }, f, indent=2)
            
        print(f"\n{Fore.GREEN}Detailed results saved to: {filename}{Style.RESET_ALL}")
        
    async def run_all_tests(self):
        """Run all system tests."""
        print(f"{Fore.CYAN}Starting StratOS Agent System Tests{Style.RESET_ALL}")
        print(f"Testing {len(await self.client.list_agents())} deployed agents\n")
        
        # Test each system
        await self.test_strategic_foundation()
        await asyncio.sleep(1)  # Brief pause between systems
        
        await self.test_analysis_intelligence()
        await asyncio.sleep(1)
        
        await self.test_planning_execution()
        
        # Generate report
        self.generate_report()
        
        await self.client.close()


async def main():
    """Main entry point."""
    tester = AgentSystemTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())