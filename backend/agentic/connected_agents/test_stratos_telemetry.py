#!/usr/bin/env python3
"""
Test StratOS agents with telemetry tracking.
Tests the full delegation flow from orchestrator to specialized agents.
"""

import asyncio
import os
import logging
from dotenv import load_dotenv
from datetime import datetime
import json
import sys
from pathlib import Path

# Load environment variables
load_dotenv()

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# Import Azure SDK components
from azure.identity.aio import DefaultAzureCredential
from azure.ai.projects.aio import AIProjectClient

# Import telemetry components
from core.telemetry import create_span_context, add_span_attributes, SpanNames

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class StratOSTelemetryTest:
    """Test StratOS agents with telemetry tracking."""
    
    def __init__(self):
        # Load deployment info
        deployment_file = Path(__file__).parent / "stratos_deployment_info.json"
        if not deployment_file.exists():
            # Try parent directory
            deployment_file = Path(__file__).parent.parent / "stratos_deployment_info.json"
        if not deployment_file.exists():
            raise FileNotFoundError(f"Deployment info not found: {deployment_file}")
            
        with open(deployment_file, 'r') as f:
            self.deployment_info = json.load(f)
        
        self.orchestrator_id = self.deployment_info.get("main_orchestrator_agent_id")
        if not self.orchestrator_id:
            raise ValueError("main_orchestrator_agent_id not found in deployment info")
            
        self.endpoint = os.getenv("AZURE_AI_PROJECT_CONNECTION_STRING")
        
        if not self.endpoint:
            raise ValueError("AZURE_AI_PROJECT_CONNECTION_STRING not found in environment")
        
        self.test_results = []
    
    async def run_telemetry_tests(self):
        """Run full test suite with telemetry."""
        
        # Main test suite span
        with create_span_context("stratos.test_suite", {
            "test.suite": "stratos_telemetry",
            "test.timestamp": datetime.utcnow().isoformat(),
            "orchestrator.id": self.orchestrator_id
        }) as suite_span:
            
            logger.info("="*80)
            logger.info("STRATOS AGENTS TELEMETRY TEST SUITE")
            logger.info("="*80)
            logger.info(f"Orchestrator: {self.orchestrator_id}")
            logger.info(f"Deployed Agents: {len([k for k in self.deployment_info.keys() if k.endswith('_agent_id')])}")
            
            async with DefaultAzureCredential() as credential, \
                       AIProjectClient(endpoint=self.endpoint, credential=credential) as client:
                
                # Test 1: CEO Log delegation
                await self._test_ceo_log_delegation(client)
                
                # Test 2: North Star delegation
                await self._test_north_star_delegation(client)
                
                # Test 3: Memory Recall delegation
                await self._test_memory_recall_delegation(client)
                
                # Test 4: Preference Learning delegation
                await self._test_preference_learning_delegation(client)
                
                # Test 5: Complex multi-hop query
                await self._test_multi_hop_delegation(client)
                
                # Summary
                add_span_attributes(suite_span, {
                    "test.total_tests": len(self.test_results),
                    "test.passed": sum(1 for r in self.test_results if r["success"]),
                    "test.failed": sum(1 for r in self.test_results if not r["success"]),
                    "test.completed": True
                })
                
                self._print_summary()
    
    async def _test_ceo_log_delegation(self, client):
        """Test CEO Log Agent delegation with telemetry."""
        
        logger.info("\n" + "-"*60)
        logger.info("TEST 1: CEO Log Agent Delegation")
        logger.info("-"*60)
        
        with create_span_context("stratos.delegation.ceo_log", {
            "delegation.type": "ceo_log",
            "target.agent": "CEOLogAgent"
        }) as span:
            
            try:
                # Create thread
                thread = await client.agents.create_thread()
                
                # Test message
                message = "I need to log this: Board meeting discussed AI strategy expansion"
                
                add_span_attributes(span, {
                    "request.message": message,
                    "thread.id": thread.id
                })
                
                # Send message
                await client.agents.create_message(
                    thread_id=thread.id,
                    role="user",
                    content=message
                )
                
                # Create run
                run = await client.agents.create_run(
                    thread_id=thread.id,
                    assistant_id=self.orchestrator_id
                )
                
                # Wait for completion
                while run.status in ["queued", "in_progress"]:
                    await asyncio.sleep(1)
                    run = await client.agents.get_run(
                        thread_id=thread.id,
                        run_id=run.id
                    )
                
                # Get response
                messages = []
                async for msg in client.agents.list_messages(thread_id=thread.id):
                    if msg.role == "assistant":
                        messages.append(msg.content[0].text.value if msg.content else "")
                
                response = messages[0] if messages else "No response"
                logger.info(f"Response: {response[:200]}...")
                
                # Check for delegation
                success = "ceo log" in response.lower() or "logging" in response.lower()
                
                add_span_attributes(span, {
                    "response.length": len(response),
                    "delegation.detected": success,
                    "run.status": run.status
                })
                
                self.test_results.append({
                    "test": "ceo_log_delegation",
                    "success": success,
                    "details": f"Delegation detected: {success}"
                })
                
            except Exception as e:
                logger.error(f"CEO Log test failed: {e}")
                add_span_attributes(span, {
                    "error": str(e),
                    "error.type": type(e).__name__
                })
                self.test_results.append({
                    "test": "ceo_log_delegation",
                    "success": False,
                    "details": str(e)
                })
    
    async def _test_north_star_delegation(self, client):
        """Test North Star Agent delegation with telemetry."""
        
        logger.info("\n" + "-"*60)
        logger.info("TEST 2: North Star Agent Delegation")
        logger.info("-"*60)
        
        with create_span_context("stratos.delegation.north_star", {
            "delegation.type": "north_star",
            "target.agent": "NorthStarAgent"
        }) as span:
            
            try:
                # Create thread
                thread = await client.agents.create_thread()
                
                # Test message
                message = "What is our north star metric?"
                
                add_span_attributes(span, {
                    "request.message": message,
                    "thread.id": thread.id
                })
                
                # Send message
                await client.agents.create_message(
                    thread_id=thread.id,
                    role="user",
                    content=message
                )
                
                # Create run
                run = await client.agents.create_run(
                    thread_id=thread.id,
                    assistant_id=self.orchestrator_id
                )
                
                # Wait for completion
                while run.status in ["queued", "in_progress"]:
                    await asyncio.sleep(1)
                    run = await client.agents.get_run(
                        thread_id=thread.id,
                        run_id=run.id
                    )
                
                # Get response
                messages = []
                async for msg in client.agents.list_messages(thread_id=thread.id):
                    if msg.role == "assistant":
                        messages.append(msg.content[0].text.value if msg.content else "")
                
                response = messages[0] if messages else "No response"
                logger.info(f"Response: {response[:200]}...")
                
                # Check for delegation
                success = "north star" in response.lower() or "metric" in response.lower()
                
                add_span_attributes(span, {
                    "response.length": len(response),
                    "delegation.detected": success,
                    "run.status": run.status
                })
                
                self.test_results.append({
                    "test": "north_star_delegation",
                    "success": success,
                    "details": f"Delegation detected: {success}"
                })
                
            except Exception as e:
                logger.error(f"North Star test failed: {e}")
                add_span_attributes(span, {
                    "error": str(e),
                    "error.type": type(e).__name__
                })
                self.test_results.append({
                    "test": "north_star_delegation",
                    "success": False,
                    "details": str(e)
                })
    
    async def _test_memory_recall_delegation(self, client):
        """Test Memory Recall Agent delegation with telemetry."""
        
        logger.info("\n" + "-"*60)
        logger.info("TEST 3: Memory Recall Agent Delegation")
        logger.info("-"*60)
        
        with create_span_context("stratos.delegation.memory_recall", {
            "delegation.type": "memory_recall",
            "target.agent": "MemoryRecallAgent"
        }) as span:
            
            try:
                # Create thread
                thread = await client.agents.create_thread()
                
                # Test message
                message = "What did we discuss in previous strategic planning sessions?"
                
                add_span_attributes(span, {
                    "request.message": message,
                    "thread.id": thread.id
                })
                
                # Send message
                await client.agents.create_message(
                    thread_id=thread.id,
                    role="user",
                    content=message
                )
                
                # Create run
                run = await client.agents.create_run(
                    thread_id=thread.id,
                    assistant_id=self.orchestrator_id
                )
                
                # Wait for completion
                while run.status in ["queued", "in_progress"]:
                    await asyncio.sleep(1)
                    run = await client.agents.get_run(
                        thread_id=thread.id,
                        run_id=run.id
                    )
                
                # Get response
                messages = []
                async for msg in client.agents.list_messages(thread_id=thread.id):
                    if msg.role == "assistant":
                        messages.append(msg.content[0].text.value if msg.content else "")
                
                response = messages[0] if messages else "No response"
                logger.info(f"Response: {response[:200]}...")
                
                # Check for delegation
                success = "memory" in response.lower() or "recall" in response.lower()
                
                add_span_attributes(span, {
                    "response.length": len(response),
                    "delegation.detected": success,
                    "run.status": run.status
                })
                
                self.test_results.append({
                    "test": "memory_recall_delegation",
                    "success": success,
                    "details": f"Delegation detected: {success}"
                })
                
            except Exception as e:
                logger.error(f"Memory Recall test failed: {e}")
                add_span_attributes(span, {
                    "error": str(e),
                    "error.type": type(e).__name__
                })
                self.test_results.append({
                    "test": "memory_recall_delegation",
                    "success": False,
                    "details": str(e)
                })
    
    async def _test_preference_learning_delegation(self, client):
        """Test Preference Learning Agent delegation with telemetry."""
        
        logger.info("\n" + "-"*60)
        logger.info("TEST 4: Preference Learning Agent Delegation")
        logger.info("-"*60)
        
        with create_span_context("stratos.delegation.preference_learning", {
            "delegation.type": "preference_learning",
            "target.agent": "PreferenceLearningAgent"
        }) as span:
            
            try:
                # Create thread
                thread = await client.agents.create_thread()
                
                # Test message
                message = "Learn this preference: I prefer data-driven decisions with visual dashboards"
                
                add_span_attributes(span, {
                    "request.message": message,
                    "thread.id": thread.id
                })
                
                # Send message
                await client.agents.create_message(
                    thread_id=thread.id,
                    role="user",
                    content=message
                )
                
                # Create run
                run = await client.agents.create_run(
                    thread_id=thread.id,
                    assistant_id=self.orchestrator_id
                )
                
                # Wait for completion
                while run.status in ["queued", "in_progress"]:
                    await asyncio.sleep(1)
                    run = await client.agents.get_run(
                        thread_id=thread.id,
                        run_id=run.id
                    )
                
                # Get response
                messages = []
                async for msg in client.agents.list_messages(thread_id=thread.id):
                    if msg.role == "assistant":
                        messages.append(msg.content[0].text.value if msg.content else "")
                
                response = messages[0] if messages else "No response"
                logger.info(f"Response: {response[:200]}...")
                
                # Check for delegation
                success = "preference" in response.lower() or "learning" in response.lower()
                
                add_span_attributes(span, {
                    "response.length": len(response),
                    "delegation.detected": success,
                    "run.status": run.status
                })
                
                self.test_results.append({
                    "test": "preference_learning_delegation",
                    "success": success,
                    "details": f"Delegation detected: {success}"
                })
                
            except Exception as e:
                logger.error(f"Preference Learning test failed: {e}")
                add_span_attributes(span, {
                    "error": str(e),
                    "error.type": type(e).__name__
                })
                self.test_results.append({
                    "test": "preference_learning_delegation",
                    "success": False,
                    "details": str(e)
                })
    
    async def _test_multi_hop_delegation(self, client):
        """Test complex multi-hop delegation with telemetry."""
        
        logger.info("\n" + "-"*60)
        logger.info("TEST 5: Multi-Hop Delegation")
        logger.info("-"*60)
        
        with create_span_context("stratos.delegation.multi_hop", {
            "delegation.type": "multi_hop",
            "test.complexity": "high"
        }) as span:
            
            try:
                # Create thread
                thread = await client.agents.create_thread()
                
                # Complex message that might involve multiple agents
                message = (
                    "I need a comprehensive update: "
                    "1. Log that we're starting Q2 planning, "
                    "2. Review our north star metric, "
                    "3. Recall what we discussed last quarter"
                )
                
                add_span_attributes(span, {
                    "request.message": message,
                    "thread.id": thread.id,
                    "request.parts": 3
                })
                
                # Send message
                await client.agents.create_message(
                    thread_id=thread.id,
                    role="user",
                    content=message
                )
                
                # Create run
                run = await client.agents.create_run(
                    thread_id=thread.id,
                    assistant_id=self.orchestrator_id
                )
                
                # Wait for completion
                while run.status in ["queued", "in_progress"]:
                    await asyncio.sleep(1)
                    run = await client.agents.get_run(
                        thread_id=thread.id,
                        run_id=run.id
                    )
                
                # Get response
                messages = []
                async for msg in client.agents.list_messages(thread_id=thread.id):
                    if msg.role == "assistant":
                        messages.append(msg.content[0].text.value if msg.content else "")
                
                response = messages[0] if messages else "No response"
                logger.info(f"Response: {response[:300]}...")
                
                # Check for multiple delegations
                delegations_found = []
                if "log" in response.lower():
                    delegations_found.append("ceo_log")
                if "north star" in response.lower():
                    delegations_found.append("north_star")
                if "memory" in response.lower() or "recall" in response.lower():
                    delegations_found.append("memory_recall")
                
                success = len(delegations_found) >= 2  # At least 2 delegations
                
                add_span_attributes(span, {
                    "response.length": len(response),
                    "delegations.count": len(delegations_found),
                    "delegations.types": ",".join(delegations_found),
                    "multi_hop.success": success,
                    "run.status": run.status
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
        logger.info("3. Filter by operation name: 'stratos.test_suite'")
        logger.info("4. Explore the distributed traces to see:")
        logger.info("   - Orchestrator routing decisions")
        logger.info("   - Agent delegations (CEO Log, North Star, Memory, Preferences)")
        logger.info("   - Response times and performance")
        logger.info("   - Error tracking")
        logger.info("")
        logger.info("Key telemetry patterns:")
        logger.info("- Span hierarchy: test_suite → delegation.* → agent responses")
        logger.info("- Custom attributes: agent.name, delegation.type, response.length")
        logger.info("- Performance data: duration, completion status")
        logger.info("="*80)


async def main():
    """Run the StratOS telemetry test."""
    
    # Verify Application Insights is configured
    app_insights_connection = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
    if not app_insights_connection:
        logger.error("❌ APPLICATIONINSIGHTS_CONNECTION_STRING not found!")
        logger.error("Please set this environment variable to enable telemetry.")
        logger.error("Example: InstrumentationKey=xxx;IngestionEndpoint=https://xxx.applicationinsights.azure.com/")
        return
    
    logger.info("✅ Application Insights configured")
    logger.info(f"Connection: {app_insights_connection[:50]}...")
    
    # Run test suite
    test = StratOSTelemetryTest()
    await test.run_telemetry_tests()


if __name__ == "__main__":
    asyncio.run(main())