#!/usr/bin/env python3
"""
End-to-End Test for CEO Log Agent → Azure Function → Cosmos DB
This script tests the full flow of the CEO Log Agent with Cosmos DB persistence
"""

import asyncio
import os
import sys
import json
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging
from dotenv import load_dotenv
from colorama import init, Fore, Style
import requests

# Load environment variables
load_dotenv()
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

# Initialize colorama for colored output
init(autoreset=True)

# Import Azure SDK components
from azure.identity.aio import DefaultAzureCredential
from azure.ai.projects.aio import AIProjectClient
from semantic_kernel.agents import AzureAIAgent
from azure.cosmos import CosmosClient
from azure.cosmos.exceptions import CosmosResourceNotFoundError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CEOLogE2ETestSuite:
    """End-to-End test suite for CEO Log Agent with Cosmos DB"""
    
    def __init__(self):
        """Initialize test suite with all required clients"""
        # CEO Log Agent ID from deployment
        self.ceo_agent_id = os.getenv("CEO_LOG_AGENT_ID", "asst_9UphrHMFGC2QihVXrtOHDcND")
        self.test_user_id = f"e2e_test_user_{int(time.time())}"
        self.test_results = []
        self.created_entries = []
        
        # Azure AI Project settings
        self.endpoint = os.getenv("AZURE_AI_PROJECT_CONNECTION_STRING")
        
        # Cosmos DB settings
        self.cosmos_endpoint = os.getenv("COSMOS_ENDPOINT")
        self.cosmos_key = os.getenv("COSMOS_KEY")
        self.database_name = "StratOS"
        self.container_name = "ceo_logs"
        
        # Azure Function endpoints
        self.function_base_url = os.getenv("AZURE_FUNCTION_BASE_URL", "https://ceo-log-functions.azurewebsites.net/api")
        self.function_code = os.getenv("AZURE_FUNCTION_CODE")
        
        # Initialize Cosmos client if credentials available
        self.cosmos_client = None
        self.database = None
        self.container = None
        
        if self.cosmos_endpoint and self.cosmos_key:
            try:
                self.cosmos_client = CosmosClient(self.cosmos_endpoint, self.cosmos_key)
                self.database = self.cosmos_client.get_database_client(self.database_name)
                self.container = self.database.get_container_client(self.container_name)
                logger.info("✅ Cosmos DB client initialized")
            except Exception as e:
                logger.error(f"❌ Failed to initialize Cosmos DB client: {e}")
    
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
    
    async def test_azure_function_health(self) -> Dict[str, Any]:
        """Test Azure Function health check"""
        test_name = "Azure Function Health Check"
        start_time = time.time()
        
        try:
            # Test CheckEnv function
            url = f"{self.function_base_url}/CheckEnv"
            if self.function_code:
                url += f"?code={self.function_code}"
            
            response = requests.get(url, timeout=10)
            duration = (time.time() - start_time) * 1000
            
            success = response.status_code == 200
            env_info = response.json() if success else {}
            
            self.print_test(
                test_name,
                "PASS" if success else "FAIL",
                f"Status: {response.status_code}, Duration: {duration:.0f}ms"
            )
            
            # Also test TestConnection function
            if success:
                conn_url = f"{self.function_base_url}/TestConnection"
                if self.function_code:
                    conn_url += f"?code={self.function_code}"
                
                conn_response = requests.get(conn_url, timeout=10)
                if conn_response.status_code == 200:
                    conn_info = conn_response.json()
                    print(f"   {Fore.GREEN}Cosmos DB Connection: {conn_info.get('status', 'Unknown')}{Style.RESET_ALL}")
            
            return {
                "test": test_name,
                "passed": success,
                "duration_ms": duration,
                "status_code": response.status_code,
                "environment": env_info
            }
            
        except Exception as e:
            self.print_test(test_name, "FAIL", str(e))
            return {
                "test": test_name,
                "passed": False,
                "duration_ms": (time.time() - start_time) * 1000,
                "error": str(e)
            }
    
    async def test_save_via_agent(self) -> Dict[str, Any]:
        """Test saving a log entry through the CEO Log Agent"""
        test_name = "Save Entry via Agent"
        start_time = time.time()
        
        try:
            async with DefaultAzureCredential() as credential, \
                       AIProjectClient(endpoint=self.endpoint, credential=credential) as client:
                
                # Get CEO Log Agent
                agent_def = await client.agents.get_agent(agent_id=self.ceo_agent_id)
                ceo_agent = AzureAIAgent(client=client, definition=agent_def)
                
                # Create test log entry
                test_entry = f"""Save this CEO log entry for user {self.test_user_id}:
                
                Today we reached a major milestone in our AI initiatives. The team successfully 
                deployed the connected agents architecture, enabling seamless orchestration between 
                specialized AI agents. This positions us well for rapid iteration and scaling.
                
                Key achievements:
                - All 15 agents deployed and operational
                - Azure Functions integration complete
                - Cosmos DB persistence layer working
                
                Concerns:
                - Need to monitor performance under load
                - Security review pending for production deployment
                - Consider redundancy for critical agents
                """
                
                logger.info(f"Sending save request to CEO Log Agent...")
                
                # Invoke agent
                response = ""
                async for part in ceo_agent.invoke(messages=test_entry):
                    if hasattr(part, 'content') and part.content:
                        response += str(part.content)
                
                duration = (time.time() - start_time) * 1000
                
                # Parse response for entry ID
                entry_id = None
                if "saved" in response.lower() and ("id" in response or "entryId" in response):
                    import re
                    # Try to extract entry ID from response
                    id_patterns = [
                        r'"entryId":\s*"([^"]+)"',
                        r'"id":\s*"([^"]+)"',
                        r'Entry ID:\s*([a-f0-9-]+)',
                        r'saved with ID:\s*([a-f0-9-]+)'
                    ]
                    for pattern in id_patterns:
                        match = re.search(pattern, response, re.IGNORECASE)
                        if match:
                            entry_id = match.group(1)
                            break
                
                if entry_id:
                    self.created_entries.append(entry_id)
                
                success = "saved" in response.lower() and ("successful" in response.lower() or "complete" in response.lower())
                
                self.print_test(
                    test_name,
                    "PASS" if success else "FAIL",
                    f"Duration: {duration:.0f}ms, Entry ID: {entry_id or 'Not found'}"
                )
                
                return {
                    "test": test_name,
                    "passed": success,
                    "duration_ms": duration,
                    "entry_id": entry_id,
                    "response": response[:300] + "..." if len(response) > 300 else response
                }
                
        except Exception as e:
            self.print_test(test_name, "FAIL", str(e))
            return {
                "test": test_name,
                "passed": False,
                "duration_ms": (time.time() - start_time) * 1000,
                "error": str(e)
            }
    
    async def test_azure_function_save(self) -> Dict[str, Any]:
        """Test saving directly through Azure Function"""
        test_name = "Azure Function Direct Save"
        start_time = time.time()
        
        try:
            url = f"{self.function_base_url}/SaveCEOLog"
            if self.function_code:
                url += f"?code={self.function_code}"
            
            # Create test payload
            payload = {
                "userId": self.test_user_id,
                "content": "Direct Azure Function test: Testing the save functionality",
                "tags": ["test", "azure-function", "e2e"],
                "metadata": {
                    "source": "e2e_test",
                    "test_run": datetime.utcnow().isoformat()
                }
            }
            
            response = requests.post(url, json=payload, timeout=10)
            duration = (time.time() - start_time) * 1000
            
            success = response.status_code == 200
            result = response.json() if success else {}
            
            if success and result.get("entryId"):
                self.created_entries.append(result["entryId"])
            
            self.print_test(
                test_name,
                "PASS" if success else "FAIL",
                f"Status: {response.status_code}, Duration: {duration:.0f}ms"
            )
            
            return {
                "test": test_name,
                "passed": success,
                "duration_ms": duration,
                "status_code": response.status_code,
                "entry_id": result.get("entryId"),
                "result": result
            }
            
        except Exception as e:
            self.print_test(test_name, "FAIL", str(e))
            return {
                "test": test_name,
                "passed": False,
                "duration_ms": (time.time() - start_time) * 1000,
                "error": str(e)
            }
    
    async def test_cosmos_verification(self) -> Dict[str, Any]:
        """Verify entries were saved to Cosmos DB"""
        test_name = "Cosmos DB Verification"
        start_time = time.time()
        
        try:
            if not self.container:
                self.print_test(test_name, "SKIP", "Cosmos DB client not initialized")
                return {
                    "test": test_name,
                    "passed": False,
                    "skipped": True,
                    "reason": "Cosmos DB client not initialized"
                }
            
            # Query for user's entries
            query = f"SELECT * FROM c WHERE c.userId = '{self.test_user_id}'"
            items = list(self.container.query_items(
                query=query,
                enable_cross_partition_query=True
            ))
            
            duration = (time.time() - start_time) * 1000
            
            # Verify we found entries
            found_count = len(items)
            expected_count = len(self.created_entries)
            
            # Check if specific entry IDs are present
            found_ids = {item['id'] for item in items}
            missing_ids = [eid for eid in self.created_entries if eid and eid not in found_ids]
            
            success = found_count > 0 and len(missing_ids) == 0
            
            self.print_test(
                test_name,
                "PASS" if success else "FAIL",
                f"Found {found_count} entries, Expected: {expected_count}, Duration: {duration:.0f}ms"
            )
            
            if missing_ids:
                print(f"   {Fore.YELLOW}Missing IDs: {missing_ids}{Style.RESET_ALL}")
            
            return {
                "test": test_name,
                "passed": success,
                "duration_ms": duration,
                "entries_found": found_count,
                "entries_expected": expected_count,
                "missing_ids": missing_ids,
                "sample_entry": items[0] if items else None
            }
            
        except Exception as e:
            self.print_test(test_name, "FAIL", str(e))
            return {
                "test": test_name,
                "passed": False,
                "duration_ms": (time.time() - start_time) * 1000,
                "error": str(e)
            }
    
    async def test_search_via_agent(self) -> Dict[str, Any]:
        """Test searching entries through the CEO Log Agent"""
        test_name = "Search Entries via Agent"
        start_time = time.time()
        
        try:
            async with DefaultAzureCredential() as credential, \
                       AIProjectClient(endpoint=self.endpoint, credential=credential) as client:
                
                # Get CEO Log Agent
                agent_def = await client.agents.get_agent(agent_id=self.ceo_agent_id)
                ceo_agent = AzureAIAgent(client=client, definition=agent_def)
                
                # Search for entries
                search_query = f"Search for all log entries for user {self.test_user_id} containing 'AI' or 'milestone'"
                
                logger.info(f"Sending search request to CEO Log Agent...")
                
                # Invoke agent
                response = ""
                async for part in ceo_agent.invoke(messages=search_query):
                    if hasattr(part, 'content') and part.content:
                        response += str(part.content)
                
                duration = (time.time() - start_time) * 1000
                
                # Check if results were found
                success = any([
                    "found" in response.lower(),
                    "result" in response.lower(),
                    "entries" in response.lower(),
                    "milestone" in response.lower()
                ])
                
                self.print_test(
                    test_name,
                    "PASS" if success else "FAIL",
                    f"Duration: {duration:.0f}ms, Cache: {'HIT' if duration < 150 else 'MISS'}"
                )
                
                return {
                    "test": test_name,
                    "passed": success,
                    "duration_ms": duration,
                    "cache_hit": duration < 150,
                    "response": response[:300] + "..." if len(response) > 300 else response
                }
                
        except Exception as e:
            self.print_test(test_name, "FAIL", str(e))
            return {
                "test": test_name,
                "passed": False,
                "duration_ms": (time.time() - start_time) * 1000,
                "error": str(e)
            }
    
    async def test_analysis_insights(self) -> Dict[str, Any]:
        """Test analysis and insights generation"""
        test_name = "Analysis & Insights"
        start_time = time.time()
        
        try:
            async with DefaultAzureCredential() as credential, \
                       AIProjectClient(endpoint=self.endpoint, credential=credential) as client:
                
                # Get CEO Log Agent
                agent_def = await client.agents.get_agent(agent_id=self.ceo_agent_id)
                ceo_agent = AzureAIAgent(client=client, definition=agent_def)
                
                # Request analysis
                analysis_query = f"Analyze the recent logs for user {self.test_user_id} and provide strategic insights"
                
                logger.info(f"Sending analysis request to CEO Log Agent...")
                
                # Invoke agent
                response = ""
                async for part in ceo_agent.invoke(messages=analysis_query):
                    if hasattr(part, 'content') and part.content:
                        response += str(part.content)
                
                duration = (time.time() - start_time) * 1000
                
                # Check for analysis content
                success = any([
                    "insight" in response.lower(),
                    "analysis" in response.lower(),
                    "recommend" in response.lower(),
                    "strategic" in response.lower()
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
                    "response": response[:300] + "..." if len(response) > 300 else response
                }
                
        except Exception as e:
            self.print_test(test_name, "FAIL", str(e))
            return {
                "test": test_name,
                "passed": False,
                "duration_ms": (time.time() - start_time) * 1000,
                "error": str(e)
            }
    
    async def test_azure_function_search(self) -> Dict[str, Any]:
        """Test search functionality through Azure Function"""
        test_name = "Azure Function Search"
        start_time = time.time()
        
        try:
            url = f"{self.function_base_url}/SearchCEOLogs"
            if self.function_code:
                url += f"?code={self.function_code}"
            
            # Search parameters
            params = {
                "userId": self.test_user_id,
                "keywords": "AI milestone",
                "limit": 10
            }
            
            response = requests.post(url, json=params, timeout=10)
            duration = (time.time() - start_time) * 1000
            
            success = response.status_code == 200
            result = response.json() if success else {}
            entries_found = len(result.get("entries", []))
            
            self.print_test(
                test_name,
                "PASS" if success and entries_found > 0 else "FAIL",
                f"Status: {response.status_code}, Entries: {entries_found}, Duration: {duration:.0f}ms"
            )
            
            return {
                "test": test_name,
                "passed": success and entries_found > 0,
                "duration_ms": duration,
                "status_code": response.status_code,
                "entries_found": entries_found,
                "cache_hit": result.get("cache_hit", False)
            }
            
        except Exception as e:
            self.print_test(test_name, "FAIL", str(e))
            return {
                "test": test_name,
                "passed": False,
                "duration_ms": (time.time() - start_time) * 1000,
                "error": str(e)
            }
    
    async def test_performance_benchmarks(self) -> Dict[str, Any]:
        """Test performance against target benchmarks"""
        test_name = "Performance Benchmarks"
        benchmarks = {
            "save_target_ms": 200,
            "search_target_ms": 300,
            "analysis_target_ms": 500
        }
        
        try:
            # Run performance tests
            save_times = []
            search_times = []
            
            # Multiple save operations
            for i in range(3):
                start = time.time()
                result = await self.test_save_via_agent()
                save_times.append(result.get("duration_ms", float('inf')))
                await asyncio.sleep(1)
            
            # Multiple search operations
            for i in range(3):
                start = time.time()
                result = await self.test_search_via_agent()
                search_times.append(result.get("duration_ms", float('inf')))
                await asyncio.sleep(1)
            
            # Calculate averages
            avg_save = sum(save_times) / len(save_times) if save_times else float('inf')
            avg_search = sum(search_times) / len(search_times) if search_times else float('inf')
            
            # Check against benchmarks
            results = {
                "save": {
                    "target_ms": benchmarks["save_target_ms"],
                    "actual_ms": avg_save,
                    "passed": avg_save < benchmarks["save_target_ms"]
                },
                "search": {
                    "target_ms": benchmarks["search_target_ms"],
                    "actual_ms": avg_search,
                    "passed": avg_search < benchmarks["search_target_ms"]
                }
            }
            
            all_passed = all(r["passed"] for r in results.values())
            
            self.print_test(
                test_name,
                "PASS" if all_passed else "FAIL",
                f"Save: {avg_save:.0f}ms (target: {benchmarks['save_target_ms']}ms), "
                f"Search: {avg_search:.0f}ms (target: {benchmarks['search_target_ms']}ms)"
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
    
    async def cleanup(self):
        """Cleanup test data from Cosmos DB"""
        if self.container and self.created_entries:
            try:
                logger.info("Cleaning up test data...")
                for entry_id in self.created_entries:
                    if entry_id:
                        try:
                            self.container.delete_item(
                                item=entry_id,
                                partition_key=self.test_user_id
                            )
                        except:
                            pass
                logger.info(f"Cleaned up {len(self.created_entries)} test entries")
            except Exception as e:
                logger.error(f"Cleanup error: {e}")
    
    async def run_all_tests(self):
        """Run all E2E tests"""
        self.print_header("CEO LOG E2E TEST SUITE (Agent → Azure Function → Cosmos DB)")
        
        # Check prerequisites
        if not self.endpoint:
            print(f"{Fore.RED}❌ AZURE_AI_PROJECT_CONNECTION_STRING not configured{Style.RESET_ALL}")
            return
        
        if not self.function_base_url:
            print(f"{Fore.RED}❌ AZURE_FUNCTION_BASE_URL not configured{Style.RESET_ALL}")
            return
        
        # Run tests in sequence
        self.print_header("RUNNING E2E TESTS")
        
        # 1. Test Azure Function health
        self.test_results.append(await self.test_azure_function_health())
        await asyncio.sleep(1)
        
        # 2. Test saving via agent
        self.test_results.append(await self.test_save_via_agent())
        await asyncio.sleep(2)
        
        # 3. Test direct Azure Function save
        self.test_results.append(await self.test_azure_function_save())
        await asyncio.sleep(1)
        
        # 4. Verify in Cosmos DB
        self.test_results.append(await self.test_cosmos_verification())
        await asyncio.sleep(1)
        
        # 5. Test search via agent
        self.test_results.append(await self.test_search_via_agent())
        await asyncio.sleep(1)
        
        # 6. Test Azure Function search
        self.test_results.append(await self.test_azure_function_search())
        await asyncio.sleep(1)
        
        # 7. Test analysis and insights
        self.test_results.append(await self.test_analysis_insights())
        await asyncio.sleep(1)
        
        # 8. Test performance benchmarks
        # self.test_results.append(await self.test_performance_benchmarks())
        
        # Print summary
        self.print_summary()
        
        # Cleanup
        await self.cleanup()
    
    def print_summary(self):
        """Print test summary"""
        self.print_header("E2E TEST SUMMARY")
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r.get("passed", False))
        failed_tests = total_tests - passed_tests
        skipped_tests = sum(1 for r in self.test_results if r.get("skipped", False))
        
        print(f"\n{Fore.CYAN}Total Tests: {total_tests}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}Passed: {passed_tests}{Style.RESET_ALL}")
        print(f"{Fore.RED}Failed: {failed_tests - skipped_tests}{Style.RESET_ALL}")
        if skipped_tests > 0:
            print(f"{Fore.YELLOW}Skipped: {skipped_tests}{Style.RESET_ALL}")
        
        # Component status
        print(f"\n{Fore.CYAN}Component Status:{Style.RESET_ALL}")
        
        # CEO Log Agent
        agent_tests = [r for r in self.test_results if "Agent" in r.get("test", "")]
        agent_passed = all(r.get("passed", False) for r in agent_tests)
        print(f"  CEO Log Agent: {Fore.GREEN if agent_passed else Fore.RED}{'✅ Working' if agent_passed else '❌ Issues'}{Style.RESET_ALL}")
        
        # Azure Functions
        func_tests = [r for r in self.test_results if "Azure Function" in r.get("test", "")]
        func_passed = all(r.get("passed", False) for r in func_tests)
        print(f"  Azure Functions: {Fore.GREEN if func_passed else Fore.RED}{'✅ Working' if func_passed else '❌ Issues'}{Style.RESET_ALL}")
        
        # Cosmos DB
        cosmos_test = next((r for r in self.test_results if r.get("test") == "Cosmos DB Verification"), None)
        cosmos_status = "✅ Working" if cosmos_test and cosmos_test.get("passed") else ("⚠️ Skipped" if cosmos_test and cosmos_test.get("skipped") else "❌ Issues")
        cosmos_color = Fore.GREEN if "✅" in cosmos_status else (Fore.YELLOW if "⚠️" in cosmos_status else Fore.RED)
        print(f"  Cosmos DB: {cosmos_color}{cosmos_status}{Style.RESET_ALL}")
        
        if failed_tests == 0:
            print(f"\n{Fore.GREEN}🎉 All tests passed! CEO Log → Azure Function → Cosmos DB integration is working correctly.{Style.RESET_ALL}")
        else:
            print(f"\n{Fore.YELLOW}⚠️  Some tests failed. Review the details above.{Style.RESET_ALL}")
        
        # Save detailed results
        results_file = f"ceo_log_e2e_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, "w") as f:
            json.dump({
                "test_run": datetime.now().isoformat(),
                "user_id": self.test_user_id,
                "summary": {
                    "total": total_tests,
                    "passed": passed_tests,
                    "failed": failed_tests - skipped_tests,
                    "skipped": skipped_tests
                },
                "component_status": {
                    "ceo_log_agent": agent_passed,
                    "azure_functions": func_passed,
                    "cosmos_db": cosmos_test.get("passed") if cosmos_test else False
                },
                "results": self.test_results
            }, f, indent=2)
        
        print(f"\n{Fore.CYAN}📄 Detailed results saved to: {results_file}{Style.RESET_ALL}")


async def main():
    """Main test execution"""
    test_suite = CEOLogE2ETestSuite()
    await test_suite.run_all_tests()


if __name__ == "__main__":
    print(f"\n{Fore.CYAN}🚀 Starting CEO Log End-to-End Tests (Agent → Azure Function → Cosmos DB)...{Style.RESET_ALL}\n")
    asyncio.run(main())