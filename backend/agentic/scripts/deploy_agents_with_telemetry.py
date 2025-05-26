#!/usr/bin/env python3
"""
Deploy all StratOS agents with OpenTelemetry tracing enabled.
This script updates existing agents to include telemetry configuration.
"""

import os
import sys
import json
import asyncio
from typing import Dict, List
from dotenv import load_dotenv
from openai import AsyncAzureOpenAI

# Add the agentic directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.telemetry import initialize_telemetry, SpanNames, trace_method


class AgentTelemetryDeployer:
    """Handles deployment of agents with telemetry configuration."""
    
    def __init__(self):
        load_dotenv()
        
        # Load from backend/agentic/.env
        backend_env = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
        load_dotenv(backend_env, override=True)
        
        # Use the Azure OpenAI credentials from comments
        self.client = AsyncAzureOpenAI(
            azure_endpoint="https://sk-multi-agent-openai.openai.azure.com/",
            api_key="b77c5b137db6465dabdbc34adb136e2c",
            api_version="2024-02-15-preview"
        )
        self.app_insights_connection_string = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
        
        # Initialize telemetry for the deployer
        initialize_telemetry(
            service_name="AgentTelemetryDeployer",
            service_version="1.0.0",
            connection_string=self.app_insights_connection_string
        )
    
    @trace_method("deployer.load_agent_configs")
    async def load_agent_configs(self) -> Dict[str, str]:
        """Load existing agent configurations."""
        deployment_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "deployment_configs",
            "ai_project_agents_deployment.json"
        )
        
        with open(deployment_path, 'r') as f:
            data = json.load(f)
            return data['deployed_agents']
    
    @trace_method("deployer.update_agent_instructions")
    def update_agent_instructions(self, original_instructions: str, agent_name: str) -> str:
        """Add telemetry instructions to agent."""
        telemetry_section = f"""

## Telemetry and Monitoring

This agent is configured with Azure Application Insights telemetry. All operations are automatically traced and logged.

When processing requests:
1. Each operation is traced with a unique span ID
2. Important attributes are logged (request type, category, outcomes)
3. Errors are automatically captured with stack traces
4. Performance metrics are collected

Service Name: {agent_name}
Deployment Environment: Production

Always include relevant context in your responses that can help with debugging and monitoring.
"""
        
        return original_instructions + telemetry_section
    
    @trace_method("deployer.update_agent")
    async def update_agent(self, agent_id: str, agent_name: str) -> bool:
        """Update a single agent with telemetry configuration."""
        try:
            # Get current agent configuration
            agent = await self.client.beta.assistants.retrieve(agent_id)
            
            # Update instructions with telemetry info
            updated_instructions = self.update_agent_instructions(
                agent.instructions,
                agent_name
            )
            
            # Update the agent
            await self.client.beta.assistants.update(
                assistant_id=agent_id,
                instructions=updated_instructions,
                metadata={
                    **agent.metadata,
                    "telemetry_enabled": "true",
                    "app_insights_configured": "true",
                    "service_name": agent_name,
                    "last_updated": "2025-05-26"
                }
            )
            
            print(f"✅ Updated {agent_name} with telemetry configuration")
            return True
            
        except Exception as e:
            print(f"❌ Failed to update {agent_name}: {e}")
            return False
    
    @trace_method("deployer.deploy_all_agents")
    async def deploy_all_agents(self):
        """Update all agents with telemetry configuration."""
        print("🚀 Updating all agents with telemetry configuration")
        print("=" * 60)
        
        # Load agent configurations
        agents = await self.load_agent_configs()
        
        # Update each agent
        results = []
        for agent_name, agent_id in agents.items():
            print(f"\nUpdating {agent_name}...")
            success = await self.update_agent(agent_id, agent_name)
            results.append((agent_name, success))
        
        # Update Main Orchestrator
        print("\nUpdating Main Orchestrator...")
        orch_config_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "deployment_configs",
            "main_orchestrator_tools_deployment.json"
        )
        
        with open(orch_config_path, 'r') as f:
            orch_data = json.load(f)
            orch_id = orch_data['agent_id']
        
        success = await self.update_agent(orch_id, "MainOrchestrator")
        results.append(("MainOrchestrator", success))
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 Deployment Summary:")
        successful = sum(1 for _, success in results if success)
        print(f"✅ Successfully updated: {successful}/{len(results)} agents")
        
        if successful < len(results):
            print("\n❌ Failed agents:")
            for agent_name, success in results:
                if not success:
                    print(f"  - {agent_name}")
        
        print("\n📝 Next Steps:")
        print("1. Test telemetry by running: python scripts/test_telemetry_integration.py")
        print("2. View traces in Azure Portal > Application Insights")
        print(f"3. Connection string is saved in .env file")


async def main():
    """Main entry point."""
    deployer = AgentTelemetryDeployer()
    await deployer.deploy_all_agents()


if __name__ == "__main__":
    asyncio.run(main())