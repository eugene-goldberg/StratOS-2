#!/usr/bin/env python3
"""
Deploy multiple connected agents (greeter and calculator) with an orchestrator.
"""

import asyncio
import os
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import Azure and Semantic Kernel SDK components
from azure.identity.aio import DefaultAzureCredential
from azure.ai.projects.aio import AIProjectClient
from semantic_kernel.agents import AzureAIAgent, AzureAIAgentSettings

# Import our service functions and configs
import agent_services
import specialized_agent_config
import calculator_agent_config
import weather_agent_config
import multi_tool_orchestrator_config

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def deploy_multi_tool_system():
    """Deploy greeter agent, calculator agent, weather agent, and orchestrator."""
    
    greeter_agent_id = None
    calculator_agent_id = None
    weather_agent_id = None
    orchestrator_agent_id = None
    client_instance = None
    
    try:
        # Get settings
        ai_agent_settings = AzureAIAgentSettings(
            model_deployment_name=os.getenv("AZURE_AI_MODEL_DEPLOYMENT_NAME", "gpt-35-turbo"),
            endpoint=os.getenv("AZURE_AI_PROJECT_CONNECTION_STRING")
        )
        
        if not ai_agent_settings.endpoint:
            logger.error("AZURE_AI_PROJECT_CONNECTION_STRING is not set")
            return
            
        model_deployment_name = ai_agent_settings.model_deployment_name
        project_connection_string = str(ai_agent_settings.endpoint)
        
        # Create client
        async with DefaultAzureCredential() as credential, \
                   AIProjectClient(endpoint=project_connection_string, credential=credential) as client:
            
            client_instance = client
            logger.info("Successfully created Azure AI Agent Service client.")
            
            # 1. Create Greeter Agent
            greeter_agent_def = await agent_services.create_specialized_agent(
                client, 
                model_deployment_name
            )
            greeter_agent_id = greeter_agent_def.id
            
            # 2. Create Calculator Agent
            calculator_agent_name = f"{calculator_agent_config.AGENT_NAME_PREFIX}-{os.urandom(4).hex()}"
            logger.info(f"Creating Calculator Agent: {calculator_agent_name}...")
            
            calculator_agent_def = await client.agents.create_agent(
                model=model_deployment_name,
                name=calculator_agent_name,
                instructions=calculator_agent_config.AGENT_INSTRUCTIONS,
            )
            calculator_agent_id = calculator_agent_def.id
            logger.info(f"Calculator Agent '{calculator_agent_name}' created with ID: {calculator_agent_id}")
            
            # 3. Create Weather Agent
            weather_agent_name = f"{weather_agent_config.AGENT_NAME_PREFIX}-{os.urandom(4).hex()}"
            logger.info(f"Creating Weather Agent: {weather_agent_name}...")
            
            weather_agent_def = await client.agents.create_agent(
                model=model_deployment_name,
                name=weather_agent_name,
                instructions=weather_agent_config.AGENT_INSTRUCTIONS,
                tools=weather_agent_config.TOOLS if hasattr(weather_agent_config, 'TOOLS') else None
            )
            weather_agent_id = weather_agent_def.id
            logger.info(f"Weather Agent '{weather_agent_name}' created with ID: {weather_agent_id}")
            
            # 4. Define tool descriptions
            greeter_tool_description = (
                "A specialized greeting expert that provides enthusiastic, over-the-top welcomes. "
                "Use this tool for ANY greeting request. It generates unique, energetic greetings."
            )
            
            calculator_tool_description = (
                "A mathematical calculation expert that performs accurate computations. "
                "Use this tool for ANY mathematical calculation or arithmetic problem. "
                "It handles basic math, percentages, and shows step-by-step work."
            )
            
            weather_tool_description = (
                "A weather information specialist that provides current weather conditions. "
                "Use this tool for ANY weather-related inquiry, including temperature, conditions, "
                "humidity, wind, and forecasts. Provides detailed weather information for any location."
            )
            
            # 5. Create Orchestrator with all three tools
            orchestrator_name = f"{multi_tool_orchestrator_config.AGENT_NAME_PREFIX}-{os.urandom(4).hex()}"
            logger.info(f"Creating Multi-Tool Orchestrator: {orchestrator_name}...")
            
            # Convert tools to format expected by API
            tools = []
            
            # Add greeter tool
            tools.append({
                "type": "connected_agent",
                "connected_agent": {
                    "id": greeter_agent_id,
                    "name": "enthusiastic_greeter_tool",
                    "description": greeter_tool_description
                }
            })
            
            # Add calculator tool
            tools.append({
                "type": "connected_agent",
                "connected_agent": {
                    "id": calculator_agent_id,
                    "name": "precise_calculator_tool",
                    "description": calculator_tool_description
                }
            })
            
            # Add weather tool
            tools.append({
                "type": "connected_agent",
                "connected_agent": {
                    "id": weather_agent_id,
                    "name": "weather_information_tool",
                    "description": weather_tool_description
                }
            })
            
            logger.info(f"Attaching {len(tools)} tools to orchestrator")
            
            orchestrator_def = await client.agents.create_agent(
                model=model_deployment_name,
                name=orchestrator_name,
                instructions=multi_tool_orchestrator_config.AGENT_INSTRUCTIONS,
                tools=tools
            )
            orchestrator_agent_id = orchestrator_def.id
            logger.info(f"Multi-Tool Orchestrator created with ID: {orchestrator_agent_id}")
            
            # 6. Save deployment info
            deployment_info = {
                "greeter_agent_id": greeter_agent_id,
                "calculator_agent_id": calculator_agent_id,
                "weather_agent_id": weather_agent_id,
                "orchestrator_agent_id": orchestrator_agent_id,
                "deployment_time": str(asyncio.get_event_loop().time())
            }
            
            # Update .env with orchestrator ID
            env_path = os.path.join(os.path.dirname(__file__), '.env')
            with open(env_path, 'r') as f:
                env_content = f.read()
            
            # Update or add the orchestrator ID
            if 'MAIN_ORCHESTRATOR_AGENT_ID=' in env_content:
                lines = env_content.split('\n')
                for i, line in enumerate(lines):
                    if line.startswith('MAIN_ORCHESTRATOR_AGENT_ID='):
                        lines[i] = f'MAIN_ORCHESTRATOR_AGENT_ID={orchestrator_agent_id}'
                        break
                env_content = '\n'.join(lines)
            else:
                env_content += f'\nMAIN_ORCHESTRATOR_AGENT_ID={orchestrator_agent_id}\n'
            
            with open(env_path, 'w') as f:
                f.write(env_content)
            
            logger.info("\n" + "="*60)
            logger.info("DEPLOYMENT SUCCESSFUL!")
            logger.info("="*60)
            logger.info(f"Greeter Agent ID: {greeter_agent_id}")
            logger.info(f"Calculator Agent ID: {calculator_agent_id}")
            logger.info(f"Weather Agent ID: {weather_agent_id}")
            logger.info(f"Orchestrator Agent ID: {orchestrator_agent_id}")
            logger.info("="*60)
            
            return deployment_info
            
    except Exception as e:
        logger.error(f"Error during deployment: {e}", exc_info=True)
        
    finally:
        # Cleanup on error
        if client_instance and any([greeter_agent_id, calculator_agent_id, weather_agent_id, orchestrator_agent_id]):
            logger.info("\nCleaning up agents...")
            for agent_id in [orchestrator_agent_id, weather_agent_id, calculator_agent_id, greeter_agent_id]:
                if agent_id:
                    try:
                        await client_instance.agents.delete_agent(agent_id=agent_id)
                        logger.info(f"Deleted agent: {agent_id}")
                    except Exception as e:
                        logger.error(f"Error deleting agent {agent_id}: {e}")

if __name__ == "__main__":
    asyncio.run(deploy_multi_tool_system())