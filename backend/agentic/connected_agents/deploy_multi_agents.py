#!/usr/bin/env python3
"""Deploy multiple connected agents with proper orchestrator configuration."""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from azure.ai.projects import AIProjectClient
from azure.ai.agents.models import ConnectedAgentTool
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv

# Import agent configurations
import specialized_agent_config
import weather_agent_config
from multi_agent_orchestrator_config import generate_orchestrator_instructions

# Load environment variables from connected_agents folder
load_dotenv(Path(__file__).parent / ".env")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - [%(funcName)s] %(message)s",
)
logger = logging.getLogger(__name__)


async def main():
    """Deploy connected agents with proper orchestrator configuration."""
    # Get credentials and configuration
    connection_string = os.getenv("AZURE_AI_PROJECT_CONNECTION_STRING", "").strip()
    if not connection_string:
        raise ValueError("AZURE_AI_PROJECT_CONNECTION_STRING not set in environment")
    
    endpoint = connection_string
    credential = DefaultAzureCredential()
    model = os.getenv("AZURE_AI_MODEL_DEPLOYMENT_NAME", "gpt-35-turbo")
    
    logger.info(f"Endpoint: {endpoint[:50]}...")
    logger.info(f"Model: {model}")
    
    deployed_agents = []
    
    try:
        client = AIProjectClient(
            endpoint=endpoint,
            credential=credential
        )
        
        logger.info("\n" + "="*60)
        logger.info("DEPLOYING CONNECTED AGENTS")
        logger.info("="*60 + "\n")
        
        # 1. Deploy Enthusiastic Greeter Agent
        logger.info("1. Deploying Enthusiastic Greeter Agent...")
        greeter_agent = client.agents.create_agent(
            model=model,
            name=specialized_agent_config.AGENT_NAME_PREFIX,
            instructions=specialized_agent_config.AGENT_INSTRUCTIONS
        )
        deployed_agents.append(greeter_agent)
        logger.info(f"✅ Deployed Greeter Agent: {greeter_agent.id}")
        
        # 2. Deploy Weather Information Agent
        logger.info("\n2. Deploying Weather Information Agent...")
        weather_agent = client.agents.create_agent(
            model=model,
            name=weather_agent_config.AGENT_NAME_PREFIX,
            instructions=weather_agent_config.AGENT_INSTRUCTIONS
        )
        deployed_agents.append(weather_agent)
        logger.info(f"✅ Deployed Weather Agent: {weather_agent.id}")
        
        # 3. Create Connected Agent Tools
        logger.info("\n3. Creating Connected Agent Tools...")
        
        greeter_tool = ConnectedAgentTool(
            id=greeter_agent.id,
            name="enthusiastic_greeter_tool",
            description="Tool that provides extremely enthusiastic greetings with emojis and capital letters"
        )
        logger.info("✅ Created greeter tool")
        
        weather_tool = ConnectedAgentTool(
            id=weather_agent.id,
            name="weather_information_tool",
            description="Tool that provides weather information for US cities"
        )
        logger.info("✅ Created weather tool")
        
        # Combine tool definitions
        all_tools = greeter_tool.definitions + weather_tool.definitions
        logger.info(f"✅ Combined {len(all_tools)} tool definitions")
        
        # 4. Generate orchestrator instructions using the dynamic configuration
        logger.info("\n4. Generating Orchestrator Instructions...")
        agents_config = [
            (
                "enthusiastic_greeter_tool",
                "Provides extremely enthusiastic greetings with emojis and excitement",
                ["greeting", "hello", "hi", "hey", "greet"],
                {"user": "Hello there!"}
            ),
            (
                "weather_information_tool", 
                "Provides weather information for US cities",
                ["weather", "temperature", "forecast", "climate", "rain", "snow", "sunny"],
                {"user": "What's the weather in New York?"}
            )
        ]
        
        orchestrator_instructions = generate_orchestrator_instructions(agents_config)
        logger.info("✅ Generated dynamic orchestrator instructions")
        
        # 5. Deploy Main Orchestrator
        logger.info("\n5. Deploying Main Orchestrator...")
        orchestrator_agent = client.agents.create_agent(
            model=model,
            name="MainOrchestratorAgent",
            instructions=orchestrator_instructions,
            tools=all_tools
        )
        deployed_agents.append(orchestrator_agent)
        logger.info(f"✅ Deployed Orchestrator Agent: {orchestrator_agent.id}")
        
        # 6. Summary
        logger.info("\n" + "="*60)
        logger.info("DEPLOYMENT COMPLETE")
        logger.info("="*60)
        logger.info(f"\nDeployed Agents:")
        logger.info(f"1. Greeter Agent: {greeter_agent.id}")
        logger.info(f"2. Weather Agent: {weather_agent.id}")
        logger.info(f"3. Orchestrator Agent: {orchestrator_agent.id}")
        logger.info(f"\nThe orchestrator has access to {len(all_tools)} specialized tools.")
        logger.info("\nYou can now test the orchestrator with:")
        logger.info("- Greeting requests: 'Hello!', 'Hi there!', 'Give me a greeting'")
        logger.info("- Weather requests: 'What's the weather in Seattle?', 'Temperature in Miami?'")
        logger.info("- Other questions: 'What is 2+2?', 'Tell me about Python'")
        
        # Save deployment info
        deployment_info = {
            "greeter_agent_id": greeter_agent.id,
            "weather_agent_id": weather_agent.id,
            "orchestrator_agent_id": orchestrator_agent.id,
            "endpoint": endpoint,
            "model": model
        }
        
        import json
        with open(Path(__file__).parent / "deployment_info.json", "w") as f:
            json.dump(deployment_info, f, indent=2)
        logger.info("\n✅ Deployment info saved to deployment_info.json")
        
    except Exception as e:
        logger.error(f"❌ Error during deployment: {e}")
        import traceback
        traceback.print_exc()
        
        # Cleanup on error
        logger.info("\n🧹 Cleaning up due to error...")
        for agent in deployed_agents:
            try:
                client.agents.delete_agent(agent.id)
                logger.info(f"Deleted agent: {agent.id}")
            except:
                pass
        raise


if __name__ == "__main__":
    asyncio.run(main())