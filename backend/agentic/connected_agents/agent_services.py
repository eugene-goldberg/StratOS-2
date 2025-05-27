# agent_services.py

import uuid
import logging

# Import configurations
import specialized_agent_config
import orchestrator_agent_config

# Import necessary SDK components
from azure.ai.agents.models import ConnectedAgentTool

logger = logging.getLogger(__name__)

async def create_specialized_agent(client, model_deployment_name):
    """
    Creates the specialized agent in Azure AI Agent Service.
    """
    agent_name = f"{specialized_agent_config.AGENT_NAME_PREFIX}-{uuid.uuid4()}"
    logger.info(f"Creating Specialized Agent: {agent_name}...")
    
    agent_definition = await client.agents.create_agent(
        model=model_deployment_name,
        name=agent_name,
        instructions=specialized_agent_config.AGENT_INSTRUCTIONS,
    )
    logger.info(f"Specialized Agent '{agent_name}' created with ID: {agent_definition.id}")
    return agent_definition

def define_connected_tool(specialized_agent_id, tool_name, tool_description):
    """
    Defines a ConnectedAgentTool object for the specialized agent.
    """
    logger.info(f"Defining ConnectedAgentTool '{tool_name}' for agent ID {specialized_agent_id}...")
    connected_tool = ConnectedAgentTool(
        id=specialized_agent_id,
        name=tool_name,
        description=tool_description
    )
    logger.info(f"ConnectedAgentTool '{tool_name}' defined.")
    return connected_tool

async def create_orchestrator_agent(client, model_deployment_name, connected_tools_definitions):
    """
    Creates the main orchestrator agent in Azure AI Agent Service.
    """
    agent_name = f"{orchestrator_agent_config.AGENT_NAME_PREFIX}-{uuid.uuid4()}"
    logger.info(f"Creating Main Orchestrator Agent: {agent_name}...")

    agent_definition = await client.agents.create_agent(
        model=model_deployment_name,
        name=agent_name,
        instructions=orchestrator_agent_config.AGENT_INSTRUCTIONS,
        tools=connected_tools_definitions # Expects a list of tool definitions
    )
    logger.info(f"Main Orchestrator Agent '{agent_name}' created with ID: {agent_definition.id}")
    return agent_definition