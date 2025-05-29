#!/usr/bin/env python3
"""
Test CEO Log Agent Cosmos DB Integration
Comprehensive test suite for validating the CEO Log Agent with Azure Functions and Cosmos DB
"""

import os
import sys
import json
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any
import time
from openai import AzureOpenAI
from dotenv import load_dotenv
from colorama import init, Fore, Style

# Initialize colorama for colored output
init(autoreset=True)

# Load environment variables
load_dotenv()

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class CEOLogCosmosTestSuite:
    """Test suite for CEO Log Agent with Cosmos DB integration"""
    
    def __init__(self):
        """Initialize test suite"""
        self.client = AzureOpenAI(
            api_key=os.environ.get("AZURE_OPENAI_API_KEY"),
            api_version="2024-02-15-preview",
            azure_endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT")
        )
        self.assistant_id = None
        self.thread_id = None
        self.user_id = f"test_user_{int(time.time())}"
        self.test_results = []
        
    def print_header(self, text: str):
        """Print formatted header"""
        print(f"\n{Fore.CYAN}{'=' * 80}")
        print(f"{Fore.CYAN}{text.center(80)}")
        print(f"{Fore.CYAN}{'=' * 80}{Style.RESET_ALL}")
        
    def print_test(self, name: str, status: str, details: str = ""):
        """Print test result"""
        icon = "✅" if status == "PASS" else "❌"
        color = Fore.GREEN if status == "PASS" else Fore.RED
        print(f"{color}{icon} {name}: {status}{Style.RESET_ALL}")
        if details:
            print(f"   {Fore.YELLOW}{details}{Style.RESET_ALL}")
            
    async def setup(self):
        """Setup test environment"""
        self.print_header("SETTING UP TEST ENVIRONMENT")
        
        # Load assistant ID from deployment file
        try:
            with open("ceo_log_cosmos_deployment.json", "r") as f:
                deployment_info = json.load(f)
                self.assistant_id = deployment_info["assistant_id"]
                print(f"{Fore.GREEN}✅ Loaded assistant ID: {self.assistant_id}{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}❌ Failed to load deployment info: {str(e)}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}Run deploy_ceo_log_cosmos_agent.py first{Style.RESET_ALL}")
            return False
            
        # Create a thread
        try:
            thread = self.client.beta.threads.create()
            self.thread_id = thread.id
            print(f"{Fore.GREEN}✅ Created thread: {self.thread_id}{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}❌ Failed to create thread: {str(e)}{Style.RESET_ALL}")
            return False
            
        return True
        
    async def test_save_entry(self) -> Dict[str, Any]:
        """Test saving a CEO log entry"""
        test_name = "Save CEO Log Entry"
        start_time = time.time()
        
        try:
            # Create test message
            message = self.client.beta.threads.messages.create(
                thread_id=self.thread_id,
                role="user",
                content=f"Save this log entry for user {self.user_id}: We're seeing strong momentum in our AI initiatives. The team is energized and we've identified several opportunities for market expansion. However, I'm concerned about the competitive landscape evolving rapidly."
            )
            
            # Run assistant
            run = self.client.beta.threads.runs.create(
                thread_id=self.thread_id,
                assistant_id=self.assistant_id
            )
            
            # Wait for completion
            while run.status in ["queued", "in_progress"]:
                await asyncio.sleep(1)
                run = self.client.beta.threads.runs.retrieve(
                    thread_id=self.thread_id,
                    run_id=run.id
                )
                
            duration = (time.time() - start_time) * 1000
            
            if run.status == "completed":
                # Get response
                messages = self.client.beta.threads.messages.list(
                    thread_id=self.thread_id,
                    order="desc",
                    limit=1
                )
                
                response = messages.data[0].content[0].text.value
                
                # Verify response contains expected elements
                success = all([
                    "saved" in response.lower(),
                    "tags" in response.lower() or "tag" in response.lower(),
                    self.user_id in response or "entry" in response.lower()
                ])
                
                self.print_test(
                    test_name,
                    "PASS" if success else "FAIL",
                    f"Duration: {duration:.0f}ms"
                )
                
                # Extract entry ID if available
                entry_id = None
                if "entryId" in response or "id" in response:
                    # Try to extract ID from response
                    import re
                    id_match = re.search(r'"entryId":\s*"([^"]+)"', response)
                    if id_match:
                        entry_id = id_match.group(1)
                
                return {
                    "test": test_name,
                    "passed": success,
                    "duration_ms": duration,
                    "entry_id": entry_id,
                    "response": response[:200] + "..." if len(response) > 200 else response
                }
                
            else:
                self.print_test(test_name, "FAIL", f"Run status: {run.status}")
                return {
                    "test": test_name,
                    "passed": False,
                    "duration_ms": duration,
                    "error": f"Run failed with status: {run.status}"
                }
                
        except Exception as e:
            self.print_test(test_name, "FAIL", str(e))
            return {
                "test": test_name,
                "passed": False,
                "duration_ms": (time.time() - start_time) * 1000,
                "error": str(e)
            }
            
    async def test_search_entries(self) -> Dict[str, Any]:
        """Test searching CEO log entries"""
        test_name = "Search CEO Log Entries"
        start_time = time.time()
        
        try:
            # Search for entries
            message = self.client.beta.threads.messages.create(
                thread_id=self.thread_id,
                role="user",
                content=f"Search for all log entries for user {self.user_id} containing 'AI' or 'competitive'"
            )
            
            # Run assistant
            run = self.client.beta.threads.runs.create(
                thread_id=self.thread_id,
                assistant_id=self.assistant_id
            )
            
            # Wait for completion
            while run.status in ["queued", "in_progress"]:
                await asyncio.sleep(1)
                run = self.client.beta.threads.runs.retrieve(
                    thread_id=self.thread_id,
                    run_id=run.id
                )
                
            duration = (time.time() - start_time) * 1000
            
            if run.status == "completed":
                # Get response
                messages = self.client.beta.threads.messages.list(
                    thread_id=self.thread_id,
                    order="desc",
                    limit=1
                )
                
                response = messages.data[0].content[0].text.value
                
                # Verify response contains search results
                success = any([
                    "result" in response.lower(),
                    "found" in response.lower(),
                    "search" in response.lower(),
                    "entries" in response.lower()
                ])
                
                self.print_test(
                    test_name,
                    "PASS" if success else "FAIL",
                    f"Duration: {duration:.0f}ms, Cache: {'HIT' if duration < 100 else 'MISS'}"
                )
                
                return {
                    "test": test_name,
                    "passed": success,
                    "duration_ms": duration,
                    "cache_hit": duration < 100,
                    "response": response[:200] + "..." if len(response) > 200 else response
                }
                
            else:
                self.print_test(test_name, "FAIL", f"Run status: {run.status}")
                return {
                    "test": test_name,
                    "passed": False,
                    "duration_ms": duration,
                    "error": f"Run failed with status: {run.status}"
                }
                
        except Exception as e:
            self.print_test(test_name, "FAIL", str(e))
            return {
                "test": test_name,
                "passed": False,
                "duration_ms": (time.time() - start_time) * 1000,
                "error": str(e)
            }
            
    async def test_analyze_logs(self) -> Dict[str, Any]:
        """Test analyzing CEO log entries"""
        test_name = "Analyze CEO Logs"
        start_time = time.time()
        
        try:
            # Request analysis
            message = self.client.beta.threads.messages.create(
                thread_id=self.thread_id,
                role="user",
                content=f"Analyze the logs for user {self.user_id} from the past month, focusing on risks"
            )
            
            # Run assistant
            run = self.client.beta.threads.runs.create(
                thread_id=self.thread_id,
                assistant_id=self.assistant_id
            )
            
            # Wait for completion
            while run.status in ["queued", "in_progress"]:
                await asyncio.sleep(1)
                run = self.client.beta.threads.runs.retrieve(
                    thread_id=self.thread_id,
                    run_id=run.id
                )
                
            duration = (time.time() - start_time) * 1000
            
            if run.status == "completed":
                # Get response
                messages = self.client.beta.threads.messages.list(
                    thread_id=self.thread_id,
                    order="desc",
                    limit=1
                )
                
                response = messages.data[0].content[0].text.value
                
                # Verify response contains analysis
                success = any([
                    "insight" in response.lower(),
                    "analysis" in response.lower(),
                    "risk" in response.lower(),
                    "recommend" in response.lower()
                ])
                
                self.print_test(
                    test_name,
                    "PASS" if success else "FAIL",
                    f"Duration: {duration:.0f}ms"
                )
                
                return {
                    "test": test_name,
                    "passed": success,
                    "duration_ms": duration,
                    "response": response[:200] + "..." if len(response) > 200 else response
                }
                
            else:
                self.print_test(test_name, "FAIL", f"Run status: {run.status}")
                return {
                    "test": test_name,
                    "passed": False,
                    "duration_ms": duration,
                    "error": f"Run failed with status: {run.status}"
                }
                
        except Exception as e:
            self.print_test(test_name, "FAIL", str(e))
            return {
                "test": test_name,
                "passed": False,
                "duration_ms": (time.time() - start_time) * 1000,
                "error": str(e)
            }
            
    async def test_bulk_operations(self) -> Dict[str, Any]:
        """Test bulk save operations"""
        test_name = "Bulk Save Operations"
        start_time = time.time()
        results = []
        
        try:
            # Save multiple entries
            test_entries = [
                "Team morale is high after the successful product launch.",
                "Financial projections look strong for Q4, expecting 20% growth.",
                "Customer feedback on new features has been overwhelmingly positive.",
                "Need to address technical debt in the backend systems urgently.",
                "Exploring partnership opportunities with industry leaders."
            ]
            
            for i, entry in enumerate(test_entries):
                entry_start = time.time()
                
                message = self.client.beta.threads.messages.create(
                    thread_id=self.thread_id,
                    role="user",
                    content=f"Save for user {self.user_id}: {entry}"
                )
                
                run = self.client.beta.threads.runs.create(
                    thread_id=self.thread_id,
                    assistant_id=self.assistant_id
                )
                
                while run.status in ["queued", "in_progress"]:
                    await asyncio.sleep(0.5)
                    run = self.client.beta.threads.runs.retrieve(
                        thread_id=self.thread_id,
                        run_id=run.id
                    )
                    
                entry_duration = (time.time() - entry_start) * 1000
                results.append({
                    "entry": i + 1,
                    "success": run.status == "completed",
                    "duration_ms": entry_duration
                })
                
            total_duration = (time.time() - start_time) * 1000
            success_count = sum(1 for r in results if r["success"])
            avg_duration = sum(r["duration_ms"] for r in results) / len(results)
            
            success = success_count == len(test_entries) and total_duration < 10000
            
            self.print_test(
                test_name,
                "PASS" if success else "FAIL",
                f"Saved {success_count}/{len(test_entries)} entries, Total: {total_duration:.0f}ms, Avg: {avg_duration:.0f}ms"
            )
            
            return {
                "test": test_name,
                "passed": success,
                "duration_ms": total_duration,
                "entries_saved": success_count,
                "average_duration_ms": avg_duration,
                "details": results
            }
            
        except Exception as e:
            self.print_test(test_name, "FAIL", str(e))
            return {
                "test": test_name,
                "passed": False,
                "duration_ms": (time.time() - start_time) * 1000,
                "error": str(e)
            }
            
    async def test_performance_metrics(self) -> Dict[str, Any]:
        """Test performance against benchmarks"""
        test_name = "Performance Benchmarks"
        results = {}
        
        try:
            # Test save performance (should be < 200ms)
            save_result = await self.test_save_entry()
            results["save"] = {
                "target_ms": 200,
                "actual_ms": save_result.get("duration_ms", 0),
                "passed": save_result.get("duration_ms", float('inf')) < 200
            }
            
            # Test search performance (should be < 300ms without cache)
            search_result = await self.test_search_entries()
            results["search"] = {
                "target_ms": 300,
                "actual_ms": search_result.get("duration_ms", 0),
                "passed": search_result.get("duration_ms", float('inf')) < 300
            }
            
            # Test analytics performance (should be < 500ms)
            analyze_result = await self.test_analyze_logs()
            results["analytics"] = {
                "target_ms": 500,
                "actual_ms": analyze_result.get("duration_ms", 0),
                "passed": analyze_result.get("duration_ms", float('inf')) < 500
            }
            
            all_passed = all(r["passed"] for r in results.values())
            
            self.print_test(
                test_name,
                "PASS" if all_passed else "FAIL",
                f"Save: {results['save']['actual_ms']:.0f}ms, Search: {results['search']['actual_ms']:.0f}ms, Analytics: {results['analytics']['actual_ms']:.0f}ms"
            )
            
            return {
                "test": test_name,
                "passed": all_passed,
                "benchmarks": results
            }
            
        except Exception as e:
            self.print_test(test_name, "FAIL", str(e))
            return {
                "test": test_name,
                "passed": False,
                "error": str(e)
            }
            
    async def run_all_tests(self):
        """Run all tests in the suite"""
        self.print_header("CEO LOG COSMOS DB INTEGRATION TEST SUITE")
        
        # Setup
        if not await self.setup():
            print(f"{Fore.RED}❌ Setup failed. Exiting...{Style.RESET_ALL}")
            return
            
        # Run tests
        self.print_header("RUNNING TESTS")
        
        # Individual tests
        self.test_results.append(await self.test_save_entry())
        await asyncio.sleep(1)  # Brief pause between tests
        
        self.test_results.append(await self.test_search_entries())
        await asyncio.sleep(1)
        
        self.test_results.append(await self.test_analyze_logs())
        await asyncio.sleep(1)
        
        self.test_results.append(await self.test_bulk_operations())
        await asyncio.sleep(1)
        
        self.test_results.append(await self.test_performance_metrics())
        
        # Summary
        self.print_summary()
        
    def print_summary(self):
        """Print test summary"""
        self.print_header("TEST SUMMARY")
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r.get("passed", False))
        failed_tests = total_tests - passed_tests
        
        print(f"\n{Fore.CYAN}Total Tests: {total_tests}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}Passed: {passed_tests}{Style.RESET_ALL}")
        print(f"{Fore.RED}Failed: {failed_tests}{Style.RESET_ALL}")
        
        if failed_tests == 0:
            print(f"\n{Fore.GREEN}🎉 All tests passed! CEO Log Cosmos DB integration is working correctly.{Style.RESET_ALL}")
        else:
            print(f"\n{Fore.YELLOW}⚠️  Some tests failed. Review the details above.{Style.RESET_ALL}")
            
        # Save detailed results
        results_file = f"ceo_log_cosmos_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, "w") as f:
            json.dump({
                "test_run": datetime.now().isoformat(),
                "user_id": self.user_id,
                "summary": {
                    "total": total_tests,
                    "passed": passed_tests,
                    "failed": failed_tests
                },
                "results": self.test_results
            }, f, indent=2)
            
        print(f"\n{Fore.CYAN}📄 Detailed results saved to: {results_file}{Style.RESET_ALL}")


async def main():
    """Main test execution"""
    test_suite = CEOLogCosmosTestSuite()
    await test_suite.run_all_tests()


if __name__ == "__main__":
    print(f"\n{Fore.CYAN}🚀 Starting CEO Log Cosmos DB Integration Tests...{Style.RESET_ALL}\n")
    asyncio.run(main())