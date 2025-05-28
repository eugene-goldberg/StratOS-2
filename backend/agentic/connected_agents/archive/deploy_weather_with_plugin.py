#!/usr/bin/env python3
"""
Deploy weather agent with weather plugin functions.
"""

import asyncio
import os
import logging
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import Azure and Semantic Kernel SDK components
from azure.identity.aio import DefaultAzureCredential
from azure.ai.projects.aio import AIProjectClient
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.agents import AzureAIAgent, AzureAIAgentSettings

# Import our weather plugin
from weather_plugin import WeatherPlugin

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def deploy_weather_agent_with_plugin():
    """Deploy weather agent with plugin functions."""
    
    weather_agent_id = None
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
            
            # First, remove the old weather agent if it exists
            old_weather_id = "asst_OmmrIuA3PfIfczyFtY9ui0xz"  # From previous deployment
            try:
                await client.agents.delete_agent(agent_id=old_weather_id)
                logger.info(f"Removed old weather agent: {old_weather_id}")
            except:
                logger.info("No old weather agent to remove")
            
            # Create a kernel and add the weather plugin
            kernel = Kernel()
            weather_plugin = WeatherPlugin()
            
            # Add plugin to kernel
            kernel.add_plugin(
                plugin=weather_plugin,
                plugin_name="WeatherPlugin"
            )
            
            # Get the functions from the plugin
            plugin_functions = []
            for function_name in ["GetWeather", "GetForecast", "CompareWeather"]:
                func = kernel.get_function("WeatherPlugin", function_name)
                if func:
                    plugin_functions.append({
                        "type": "function",
                        "function": {
                            "name": f"WeatherPlugin-{function_name}",
                            "description": func.metadata.description,
                            "parameters": {
                                "type": "object",
                                "properties": {},
                                "required": []
                            }
                        }
                    })
            
            logger.info(f"Prepared {len(plugin_functions)} plugin functions")
            
            # Create Weather Agent with plugin functions
            import weather_agent_config
            weather_agent_name = f"{weather_agent_config.AGENT_NAME_PREFIX}-Plugin-{os.urandom(4).hex()}"
            logger.info(f"Creating Weather Agent with plugins: {weather_agent_name}...")
            
            # Create agent with tools
            weather_agent_def = await client.agents.create_agent(
                model=model_deployment_name,
                name=weather_agent_name,
                instructions=weather_agent_config.AGENT_INSTRUCTIONS,
                tools=plugin_functions
            )
            weather_agent_id = weather_agent_def.id
            logger.info(f"Weather Agent '{weather_agent_name}' created with ID: {weather_agent_id}")
            logger.info(f"Agent has {len(weather_agent_def.tools)} tools")
            
            # Test the agent
            logger.info("\nTesting weather agent...")
            weather_agent = AzureAIAgent(
                client=client,
                definition=weather_agent_def,
                kernel=kernel  # Provide kernel with plugin
            )
            
            test_query = "What's the current weather in Seattle?"
            logger.info(f"Test query: {test_query}")
            
            response = ""
            async for part in weather_agent.invoke(messages=test_query):
                if hasattr(part, 'content') and part.content:
                    response += str(part.content)
            
            logger.info(f"Response: {response}")
            
            # Save to .env
            env_path = os.path.join(os.path.dirname(__file__), '.env')
            with open(env_path, 'r') as f:
                env_content = f.read()
            
            # Update weather agent ID
            if 'SPECIALIZED_WEATHER_AGENT_ID=' in env_content:
                lines = env_content.split('\n')
                for i, line in enumerate(lines):
                    if line.startswith('SPECIALIZED_WEATHER_AGENT_ID='):
                        lines[i] = f'SPECIALIZED_WEATHER_AGENT_ID={weather_agent_id}'
                        break
                env_content = '\n'.join(lines)
            else:
                env_content += f'\nSPECIALIZED_WEATHER_AGENT_ID={weather_agent_id}\n'
            
            with open(env_path, 'w') as f:
                f.write(env_content)
            
            logger.info("\n" + "="*60)
            logger.info("DEPLOYMENT SUCCESSFUL!")
            logger.info("="*60)
            logger.info(f"Weather Agent ID: {weather_agent_id}")
            logger.info(f"Agent has weather plugin functions")
            logger.info("="*60)
            
            return weather_agent_id
            
    except Exception as e:
        logger.error(f"Error during deployment: {e}", exc_info=True)
        
        # Cleanup on error
        if client_instance and weather_agent_id:
            try:
                await client_instance.agents.delete_agent(agent_id=weather_agent_id)
                logger.info(f"Cleaned up agent: {weather_agent_id}")
            except Exception as cleanup_error:
                logger.error(f"Error during cleanup: {cleanup_error}")

if __name__ == "__main__":
    asyncio.run(deploy_weather_agent_with_plugin())