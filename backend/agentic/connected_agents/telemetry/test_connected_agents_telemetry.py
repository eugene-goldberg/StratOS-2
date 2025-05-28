#!/usr/bin/env python3
"""
Comprehensive telemetry test for connected agents system.
Demonstrates full telemetry tracking using TelemetryAgentClient.
"""

import asyncio
import os
import logging
from dotenv import load_dotenv
from datetime import datetime
import json
import sys

# Load environment variables
load_dotenv()

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# Import telemetry components
from services.telemetry_agent_client import TelemetryAgentClient
from core.telemetry import create_span_context, add_span_attributes, SpanNames

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ConnectedAgentsTelemetryTest:
    """Comprehensive telemetry test for connected agents."""
    
    def __init__(self):
        self.client = TelemetryAgentClient()
        self.test_results = []
    
    async def run_full_test_suite(self):
        """Run comprehensive test suite with telemetry."""
        
        # Main test suite span
        with create_span_context("connected_agents.test_suite", {
            "test.suite": "connected_agents_telemetry",
            "test.timestamp": datetime.utcnow().isoformat()
        }) as suite_span:
            
            logger.info("="*80)
            logger.info("CONNECTED AGENTS TELEMETRY TEST SUITE")
            logger.info("="*80)
            
            # Test 1: Orchestrator routing
            await self._test_orchestrator_routing()
            
            # Test 2: Direct agent invocation
            await self._test_direct_agent_invocation()
            
            # Test 3: Multi-hop delegation
            await self._test_multi_hop_delegation()
            
            # Test 4: Error handling
            await self._test_error_handling()
            
            # Test 5: Performance tracking
            await self._test_performance_tracking()
            
            # Summary
            add_span_attributes(suite_span, {
                "test.total_tests": len(self.test_results),
                "test.passed": sum(1 for r in self.test_results if r["success"]),
                "test.failed": sum(1 for r in self.test_results if not r["success"]),
                "test.completed": True
            })
            
            self._print_summary()
    
    async def _test_orchestrator_routing(self):
        """Test orchestrator routing with telemetry."""
        
        logger.info("\n" + "-"*60)
        logger.info("TEST 1: Orchestrator Routing with Telemetry")
        logger.info("-"*60)
        
        test_cases = [
            {
                "name": "greeting_routing",
                "message": "Hello, give me a warm welcome!",
                "expected_agent": "GreetingAgent",
                "expected_announcement": "greeting specialist"
            },
            {
                "name": "calculation_routing",
                "message": "Calculate 42 times 13 for me",
                "expected_agent": "CalculatorAgent",
                "expected_announcement": "calculation expert"
            },
            {
                "name": "weather_routing",
                "message": "What's the weather in Seattle?",
                "expected_agent": "WeatherAgent",
                "expected_announcement": "weather information specialist"
            }
        ]
        
        for test_case in test_cases:
            with create_span_context(f"test.orchestrator_routing.{test_case['name']}", {
                "test.case": test_case["name"],
                "expected.agent": test_case["expected_agent"]
            }) as span:
                
                try:
                    logger.info(f"\nTesting: {test_case['name']}")
                    
                    # Invoke orchestrator with telemetry
                    response = await self.client.invoke_orchestrator(
                        message=test_case["message"],
                        user_id="test_user_001"
                    )
                    
                    logger.info(f"Response: {response[:200]}...")
                    
                    # Verify routing
                    success = test_case["expected_announcement"] in response.lower()
                    
                    add_span_attributes(span, {
                        "routing.success": success,
                        "response.length": len(response),
                        "announcement.found": success
                    })
                    
                    self.test_results.append({
                        "test": test_case["name"],
                        "success": success,
                        "details": f"Found announcement: {success}"
                    })
                    
                except Exception as e:
                    logger.error(f"Test failed: {e}")
                    add_span_attributes(span, {
                        "error": str(e),
                        "error.type": type(e).__name__
                    })
                    self.test_results.append({
                        "test": test_case["name"],
                        "success": False,
                        "details": str(e)
                    })
                
                await asyncio.sleep(2)  # Rate limiting
    
    async def _test_direct_agent_invocation(self):
        """Test direct agent invocation with telemetry."""
        
        logger.info("\n" + "-"*60)
        logger.info("TEST 2: Direct Agent Invocation with Telemetry")
        logger.info("-"*60)
        
        # Get agent IDs from environment
        agents = [
            {
                "name": "CEOLogAgent",
                "id": os.getenv("CEO_LOG_AGENT_ID"),
                "message": "Log entry: Board meeting discussed AI strategy"
            },
            {
                "name": "NorthStarAgent",
                "id": os.getenv("NORTH_STAR_AGENT_ID"),
                "message": "What is our north star metric?"
            },
            {
                "name": "SWOTTOWSAgent",
                "id": os.getenv("SWOT_TOWS_AGENT_ID"),
                "message": "Analyze our competitive position"
            }
        ]
        
        for agent in agents:
            if not agent["id"]:
                logger.warning(f"Skipping {agent['name']} - no ID configured")
                continue
                
            with create_span_context(f"test.direct_invocation.{agent['name']}", {
                "agent.name": agent["name"],
                "agent.id": agent["id"]
            }) as span:
                
                try:
                    logger.info(f"\nInvoking: {agent['name']}")
                    
                    # Invoke agent with telemetry
                    response = await self.client.invoke_agent(
                        agent_id=agent["id"],
                        agent_name=agent["name"],
                        message=agent["message"]
                    )
                    
                    logger.info(f"Response: {response[:200]}...")
                    
                    success = len(response) > 0
                    
                    add_span_attributes(span, {
                        "invocation.success": success,
                        "response.length": len(response)
                    })
                    
                    self.test_results.append({
                        "test": f"direct_{agent['name']}",
                        "success": success,
                        "details": f"Response length: {len(response)}"
                    })
                    
                except Exception as e:
                    logger.error(f"Invocation failed: {e}")
                    add_span_attributes(span, {
                        "error": str(e),
                        "error.type": type(e).__name__
                    })
                    self.test_results.append({
                        "test": f"direct_{agent['name']}",
                        "success": False,
                        "details": str(e)
                    })
                
                await asyncio.sleep(2)  # Rate limiting
    
    async def _test_multi_hop_delegation(self):
        """Test multi-hop delegation with telemetry."""
        
        logger.info("\n" + "-"*60)
        logger.info("TEST 3: Multi-Hop Delegation with Telemetry")
        logger.info("-"*60)
        
        with create_span_context("test.multi_hop_delegation", {
            "test.type": "complex_delegation"
        }) as span:
            
            try:
                # Complex request that might involve multiple agents
                message = (
                    "I need a comprehensive analysis: "
                    "1. Greet me warmly, "
                    "2. Calculate the ROI if we invest $100,000 at 8% for 5 years, "
                    "3. Check the weather for our headquarters location"
                )
                
                logger.info(f"Complex request: {message}")
                
                response = await self.client.invoke_orchestrator(
                    message=message,
                    user_id="test_user_002"
                )
                
                logger.info(f"Response: {response[:300]}...")
                
                # Check for multiple delegations
                delegations_found = []
                if "greeting specialist" in response.lower():
                    delegations_found.append("greeting")
                if "calculation expert" in response.lower():
                    delegations_found.append("calculation")
                if "weather information specialist" in response.lower():
                    delegations_found.append("weather")
                
                success = len(delegations_found) >= 2  # At least 2 delegations
                
                add_span_attributes(span, {
                    "delegations.count": len(delegations_found),
                    "delegations.types": ",".join(delegations_found),
                    "multi_hop.success": success
                })
                
                self.test_results.append({
                    "test": "multi_hop_delegation",
                    "success": success,
                    "details": f"Delegations found: {delegations_found}"
                })
                
            except Exception as e:
                logger.error(f"Multi-hop test failed: {e}")
                add_span_attributes(span, {
                    "error": str(e),
                    "error.type": type(e).__name__
                })
                self.test_results.append({
                    "test": "multi_hop_delegation",
                    "success": False,
                    "details": str(e)
                })
    
    async def _test_error_handling(self):
        """Test error handling with telemetry."""
        
        logger.info("\n" + "-"*60)
        logger.info("TEST 4: Error Handling with Telemetry")
        logger.info("-"*60)
        
        with create_span_context("test.error_handling", {
            "test.type": "error_scenarios"
        }) as span:
            
            try:
                # Test with invalid agent ID
                logger.info("Testing invalid agent invocation...")
                
                try:
                    await self.client.invoke_agent(
                        agent_id="invalid_agent_id",
                        agent_name="NonExistentAgent",
                        message="This should fail"
                    )
                    success = False  # Should have failed
                except Exception as e:
                    logger.info(f"Expected error caught: {e}")
                    success = True  # Successfully caught error
                
                add_span_attributes(span, {
                    "error_handling.success": success,
                    "error_handling.type": "invalid_agent"
                })
                
                self.test_results.append({
                    "test": "error_handling",
                    "success": success,
                    "details": "Error handling working correctly"
                })
                
            except Exception as e:
                logger.error(f"Error handling test failed: {e}")
                add_span_attributes(span, {
                    "error": str(e),
                    "error.type": type(e).__name__
                })
                self.test_results.append({
                    "test": "error_handling",
                    "success": False,
                    "details": str(e)
                })
    
    async def _test_performance_tracking(self):
        """Test performance tracking with telemetry."""
        
        logger.info("\n" + "-"*60)
        logger.info("TEST 5: Performance Tracking with Telemetry")
        logger.info("-"*60)
        
        with create_span_context("test.performance_tracking", {
            "test.type": "performance_metrics"
        }) as span:
            
            try:
                # Run multiple quick requests and track timing
                start_time = datetime.utcnow()
                request_times = []
                
                for i in range(3):
                    req_start = datetime.utcnow()
                    
                    response = await self.client.invoke_orchestrator(
                        message=f"Quick test {i+1}: Say hello",
                        user_id="test_user_perf"
                    )
                    
                    req_duration = (datetime.utcnow() - req_start).total_seconds()
                    request_times.append(req_duration)
                    logger.info(f"Request {i+1} took {req_duration:.2f}s")
                    
                    await asyncio.sleep(1)  # Rate limiting
                
                total_duration = (datetime.utcnow() - start_time).total_seconds()
                avg_request_time = sum(request_times) / len(request_times)
                
                add_span_attributes(span, {
                    "performance.total_duration": total_duration,
                    "performance.avg_request_time": avg_request_time,
                    "performance.request_count": len(request_times),
                    "performance.min_time": min(request_times),
                    "performance.max_time": max(request_times)
                })
                
                success = avg_request_time < 5.0  # Should complete in < 5s average
                
                self.test_results.append({
                    "test": "performance_tracking",
                    "success": success,
                    "details": f"Avg response time: {avg_request_time:.2f}s"
                })
                
            except Exception as e:
                logger.error(f"Performance test failed: {e}")
                add_span_attributes(span, {
                    "error": str(e),
                    "error.type": type(e).__name__
                })
                self.test_results.append({
                    "test": "performance_tracking",
                    "success": False,
                    "details": str(e)
                })
    
    def _print_summary(self):
        """Print test summary."""
        
        logger.info("\n" + "="*80)
        logger.info("TEST RESULTS SUMMARY")
        logger.info("="*80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r["success"])
        failed_tests = total_tests - passed_tests
        
        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"Passed: {passed_tests} ✅")
        logger.info(f"Failed: {failed_tests} ❌")
        logger.info("")
        
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            logger.info(f"{status} {result['test']}: {result['details']}")
        
        logger.info("\n" + "="*80)
        logger.info("TELEMETRY VERIFICATION")
        logger.info("="*80)
        logger.info("To view detailed telemetry:")
        logger.info("1. Go to Azure Portal > Application Insights")
        logger.info("2. Navigate to Transaction Search")
        logger.info("3. Filter by operation name: 'connected_agents.test_suite'")
        logger.info("4. Explore the distributed traces to see:")
        logger.info("   - Orchestrator routing decisions")
        logger.info("   - Agent delegations")
        logger.info("   - Tool invocations")
        logger.info("   - Performance metrics")
        logger.info("   - Error tracking")
        logger.info("")
        logger.info("Key telemetry patterns to look for:")
        logger.info("- Span hierarchy: test_suite → test_case → agent_invocation")
        logger.info("- Custom attributes: agent.name, delegation.type, routing.success")
        logger.info("- Performance data: duration, response times")
        logger.info("- Error traces: exceptions and failures")
        logger.info("="*80)


async def main():
    """Run the comprehensive telemetry test."""
    
    # Verify Application Insights is configured
    app_insights_connection = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
    if not app_insights_connection:
        logger.error("❌ APPLICATIONINSIGHTS_CONNECTION_STRING not found!")
        logger.error("Telemetry will not be captured.")
        return
    
    logger.info("✅ Application Insights configured")
    logger.info(f"Connection: {app_insights_connection[:50]}...")
    
    # Run test suite
    test = ConnectedAgentsTelemetryTest()
    await test.run_full_test_suite()


if __name__ == "__main__":
    asyncio.run(main())