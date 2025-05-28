"""
Base Test Class for StratOS Connected Agents
Provides common functionality for agent testing with telemetry
"""

import os
import json
import asyncio
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
from dotenv import load_dotenv
from azure.ai.projects.aio import AIProjectClient
from azure.identity.aio import DefaultAzureCredential
from semantic_kernel.agents import AzureAIAgent
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from telemetry.telemetry_capture import TelemetryCapture

# Load environment variables
load_dotenv(Path(__file__).parent.parent.parent / '.env')

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class BaseAgentTest(ABC):
    """Base class for testing StratOS connected agents"""
    
    def __init__(self, agent_name: str):
        """
        Initialize base test
        
        Args:
            agent_name: Name of the agent being tested
        """
        self.agent_name = agent_name
        self.logger = logging.getLogger(self.__class__.__name__)
        self.telemetry = TelemetryCapture(agent_name)
        self.deployment_info = None
        self.orchestrator_id = None
        self.agent_id = None
        self.connection_string = os.getenv("AZURE_AI_PROJECT_CONNECTION_STRING")
        
        if not self.connection_string:
            raise ValueError("AZURE_AI_PROJECT_CONNECTION_STRING not found in environment")
    
    def load_deployment_info(self) -> Dict[str, Any]:
        """Load deployment info from archive"""
        archive_dir = Path(__file__).parent.parent / "archive"
        deployment_file = archive_dir / "stratos_deployment_info.json"
        
        if not deployment_file.exists():
            self.logger.error(f"Deployment file not found: {deployment_file}")
            raise FileNotFoundError(f"Deployment file not found: {deployment_file}")
        
        with open(deployment_file, 'r') as f:
            self.deployment_info = json.load(f)
        
        # Extract IDs
        self.orchestrator_id = self.deployment_info["orchestrator"]["id"]
        
        # Log deployment info
        self.telemetry.capture_event("deployment_loaded", {
            "orchestrator_id": self.orchestrator_id,
            "agents": list(self.deployment_info["agents"].keys())
        })
        
        return self.deployment_info
    
    async def get_orchestrator_definition(self, client: AIProjectClient) -> Any:
        """
        Get orchestrator definition and capture telemetry
        
        Args:
            client: AI Project client
            
        Returns:
            Orchestrator definition
        """
        # Fetch orchestrator
        self.telemetry.capture_event("orchestrator_fetch_start", {
            "orchestrator_id": self.orchestrator_id
        })
        
        orchestrator_def = await client.agents.get_agent(agent_id=self.orchestrator_id)
        
        # Extract tool info
        tools_info = []
        if hasattr(orchestrator_def, 'tools') and orchestrator_def.tools:
            for tool in orchestrator_def.tools:
                if hasattr(tool, 'connected_agent'):
                    tools_info.append({
                        "name": tool.connected_agent.name,
                        "id": tool.connected_agent.id
                    })
        
        self.telemetry.capture_orchestrator_info(
            orchestrator_id=self.orchestrator_id,
            tools=tools_info
        )
        
        return orchestrator_def
    
    async def invoke_agent(self, agent: AzureAIAgent, query: str, scenario: Optional[str] = None) -> str:
        """
        Invoke agent with query and capture telemetry
        
        Args:
            agent: Agent instance
            query: Query to send
            scenario: Optional scenario name
            
        Returns:
            Agent response
        """
        # Capture query
        self.telemetry.capture_query(
            query=query,
            target=self.agent_name,
            function=scenario
        )
        
        # Invoke agent
        response = ""
        async for part in agent.invoke(messages=query):
            if hasattr(part, 'content') and part.content:
                response += str(part.content)
        
        # Capture response and check delegation
        delegation_detected = self.telemetry.capture_response(response, scenario)
        
        if delegation_detected:
            self.logger.info(f"✅ Delegation detected for scenario: {scenario or 'general'}")
        else:
            self.logger.warning(f"⚠️ No delegation detected for scenario: {scenario or 'general'}")
        
        return response
    
    @abstractmethod
    def get_test_scenarios(self) -> List[Dict[str, str]]:
        """
        Get test scenarios for the agent
        
        Returns:
            List of test scenario dictionaries with 'name', 'query', and optionally 'expected_function'
        """
        pass
    
    async def run_simple_test(self) -> bool:
        """
        Run a simple smoke test with one query
        
        Returns:
            True if test passed
        """
        self.logger.info(f"=== {self.agent_name} Simple Test ===")
        
        try:
            # Load deployment info
            self.load_deployment_info()
            
            # Get first test scenario
            scenarios = self.get_test_scenarios()
            if not scenarios:
                raise ValueError("No test scenarios defined")
            
            test_scenario = scenarios[0]
            
            # Create client and run test
            async with DefaultAzureCredential() as credential:
                async with AIProjectClient(
                    endpoint=self.connection_string,
                    credential=credential
                ) as client:
                    # Get orchestrator definition
                    orchestrator_def = await self.get_orchestrator_definition(client)
                    
                    # Create agent instance
                    orchestrator_agent = AzureAIAgent(
                        client=client,
                        definition=orchestrator_def
                    )
                    
                    self.logger.info(f"\n📤 Query: {test_scenario['query']}")
                    
                    response = await self.invoke_agent(
                        orchestrator_agent,
                        test_scenario['query'],
                        test_scenario.get('name')
                    )
                    
                    self.logger.info(f"\n📥 Response: {response[:300]}...")
                    
                    # Check for success
                    success = self.telemetry.get_summary()['delegations_confirmed'] > 0
                    
                    if success:
                        self.logger.info(f"\n✅ {self.agent_name} simple test passed!")
                    else:
                        self.logger.error(f"\n❌ {self.agent_name} simple test failed - no delegation detected")
                    
                    return success
                    
        except Exception as e:
            self.logger.error(f"❌ Test failed: {str(e)}")
            self.telemetry.capture_error(str(e))
            return False
    
    async def run_comprehensive_test(self) -> bool:
        """
        Run comprehensive test with all scenarios
        
        Returns:
            True if all tests passed
        """
        self.logger.info(f"=== {self.agent_name} Comprehensive Test ===")
        
        try:
            # Load deployment info
            self.load_deployment_info()
            
            # Get all test scenarios
            scenarios = self.get_test_scenarios()
            
            # Create client
            async with DefaultAzureCredential() as credential:
                async with AIProjectClient(
                    endpoint=self.connection_string,
                    credential=credential
                ) as client:
                    # Get orchestrator definition
                    orchestrator_def = await self.get_orchestrator_definition(client)
                    
                    # Create agent instance
                    orchestrator_agent = AzureAIAgent(
                        client=client,
                        definition=orchestrator_def
                    )
                    
                    # Run all scenarios
                    for scenario in scenarios:
                        self.logger.info(f"\n{'='*60}")
                        self.logger.info(f"📤 Testing: {scenario['name']}")
                        self.logger.info(f"Query: {scenario['query']}")
                        
                        response = await self.invoke_agent(
                            orchestrator_agent,
                            scenario['query'],
                            scenario['name']
                        )
                        
                        self.logger.info(f"\n📥 Response preview: {response[:200]}...")
                        
                        # Longer pause between tests to avoid rate limits
                        self.logger.info("⏳ Waiting 10 seconds before next test to avoid rate limits...")
                        await asyncio.sleep(10)
                    
                    # Capture test completion
                    summary = self.telemetry.get_summary()
                    self.telemetry.capture_test_complete(
                        tests_run=len(scenarios),
                        delegations=summary['delegations_confirmed']
                    )
                    
                    # Save telemetry
                    telemetry_file = self.telemetry.save()
                    
                    # Print summary
                    self.telemetry.print_summary()
                    
                    # Check success
                    success = summary['delegations_confirmed'] == len(scenarios)
                    
                    if success:
                        self.logger.info(f"\n✅ All {len(scenarios)} tests passed!")
                    else:
                        self.logger.warning(f"\n⚠️ Only {summary['delegations_confirmed']}/{len(scenarios)} tests showed delegation")
                    
                    self.logger.info(f"\n📁 Telemetry saved to: {telemetry_file}")
                    
                    return success
                    
        except Exception as e:
            self.logger.error(f"❌ Test failed: {str(e)}")
            self.telemetry.capture_error(str(e))
            return False