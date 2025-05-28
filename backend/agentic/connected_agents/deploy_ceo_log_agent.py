#!/usr/bin/env python3
"""
Deploy CEO Log Agent as a Connected Agent
This script deploys the CEO Log Agent with its plugin to Azure AI Agent Service
"""

import asyncio
import logging
import os
import json
import uuid
from typing import Dict, Any
from datetime import datetime
from azure.ai.projects.aio import AIProjectClient
from azure.identity.aio import DefaultAzureCredential
from azure.ai.projects.models import (
    ToolSet, 
    FunctionTool,
    ToolDefinition,
    ToolSchema,
    FunctionToolDefinition
)
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel import Kernel
from semantic_kernel.functions import KernelPlugin
from dotenv import load_dotenv

# Import our CEO Log components
from ceo_log_plugin import CEOLogPlugin
from ceo_log_agent_config import AGENT_NAME_PREFIX, AGENT_INSTRUCTIONS, MODEL_NAME

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Agent and model configuration
AGENT_DESCRIPTION = "CEO Log Agent - Manages executive thoughts, observations, and strategic insights"


def kernel_function_to_function_tool(plugin_name: str, function) -> FunctionTool:
    """Convert a kernel function to a FunctionTool for agent deployment."""
    # Get function metadata
    metadata = function.metadata
    
    # Build parameters schema from kernel function parameters
    parameters = {
        "type": "object",
        "properties": {},
        "required": []
    }
    
    for param in metadata.parameters:
        param_schema = {
            "type": "string",  # Default to string, adjust based on annotation if needed
            "description": param.description if param.description else f"Parameter {param.name}"
        }
        
        # Add to properties
        parameters["properties"][param.name] = param_schema
        
        # Check if required (kernel functions don't explicitly mark required, so we'll assume all are required except Optional ones)
        if param.default_value is None and not param.is_required:
            parameters["required"].append(param.name)
    
    # Create the function tool
    return FunctionTool(
        name=metadata.name,
        description=metadata.description,
        parameters=parameters
    )


async def deploy_ceo_log_agent():
    """Deploy the CEO Log Agent with its plugin tools."""
    try:
        # Initialize the plugin
        logger.info("Initializing CEO Log Plugin...")
        ceo_log_plugin_instance = CEOLogPlugin()
        
        # Create kernel plugin from the instance
        kernel = Kernel()
        ceo_log_plugin = KernelPlugin.from_object(
            plugin_name="CEOLogPlugin",
            plugin_instance=ceo_log_plugin_instance,
            description="CEO Log management capabilities"
        )
        
        # Get all functions from the plugin
        tools = []
        for function_name, function in ceo_log_plugin.functions.items():
            logger.info(f"Converting function: {function_name}")
            tool = kernel_function_to_function_tool("CEOLogPlugin", function)
            tools.append(tool)
        
        logger.info(f"Prepared {len(tools)} tools for deployment")
        
        # Initialize Azure AI Project client
        logger.info("Initializing Azure AI Project client...")
        project_client = AIProjectClient(
            credential=DefaultAzureCredential(exclude_interactive_browser_credential=False),
            subscription_id=os.getenv("AZURE_SUBSCRIPTION_ID"),
            resource_group_name=os.getenv("AZURE_RESOURCE_GROUP"),
            project_name=os.getenv("AZURE_AI_PROJECT_NAME"),
            
        )
        
        # Generate unique name for this agent
        agent_name = f"{AGENT_NAME_PREFIX}-{uuid.uuid4()}"
        logger.info(f"Creating CEO Log Agent: {agent_name}...")
        
        # Create the agent with tools
        if tools:
            toolset = ToolSet(tools=tools)
            agent = await project_client.agents.create_agent(
                name=agent_name,
                model=MODEL_NAME,
                instructions=AGENT_INSTRUCTIONS,
                description=AGENT_DESCRIPTION,
                toolset=toolset
            )
        else:
            agent = await project_client.agents.create_agent(
                name=agent_name,
                model=MODEL_NAME,
                instructions=AGENT_INSTRUCTIONS,
                description=AGENT_DESCRIPTION
            )
        
        logger.info(f"CEO Log Agent '{agent_name}' created with ID: {agent.id}")
        
        # Save deployment info
        deployment_info = {
            "agent_type": "ceo_log",
            "agent_id": agent.id,
            "agent_name": agent_name,
            "model": MODEL_NAME,
            "tools": [tool.name for tool in tools],
            "deployed_at": datetime.now().isoformat(),
            "description": AGENT_DESCRIPTION
        }
        
        # Save to deployment info file
        deployment_file = "ceo_log_agent_deployment.json"
        with open(deployment_file, 'w') as f:
            json.dump(deployment_info, f, indent=2)
        
        logger.info(f"Deployment info saved to {deployment_file}")
        
        # Test the agent with a simple query
        logger.info("\nTesting CEO Log Agent...")
        
        # Create a thread
        thread = await project_client.agents.create_thread()
        logger.info(f"Created thread: {thread.id}")
        
        # Create a test message
        test_message = "Save this entry: We need to focus on AI innovation to stay ahead of competitors. The team is excited but we need more resources."
        message = await project_client.agents.create_message(
            thread_id=thread.id,
            role="user",
            content=test_message
        )
        
        # Run the agent
        run = await project_client.agents.create_and_process_run(
            thread_id=thread.id,
            assistant_id=agent.id
        )
        
        logger.info(f"Run completed with status: {run.status}")
        
        # Get the response
        messages = await project_client.agents.list_messages(thread_id=thread.id)
        async for msg in messages:
            if msg.role == "assistant":
                logger.info(f"\nAgent response: {msg.content[0].text.value}")
                break
        
        logger.info("\n" + "="*60)
        logger.info("CEO LOG AGENT DEPLOYMENT SUCCESSFUL!")
        logger.info("="*60)
        logger.info(f"Agent ID: {agent.id}")
        logger.info(f"Agent Name: {agent_name}")
        logger.info(f"Available Tools: {', '.join([tool.name for tool in tools])}")
        logger.info("="*60)
        
        # Close the client
        await project_client.close()
        
        return agent.id
        
    except Exception as e:
        logger.error(f"Error deploying CEO Log Agent: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise


async def cleanup_agent(agent_id: str):
    """Clean up a deployed agent."""
    try:
        project_client = AIProjectClient(
            credential=DefaultAzureCredential(exclude_interactive_browser_credential=False),
            subscription_id=os.getenv("AZURE_SUBSCRIPTION_ID"),
            resource_group_name=os.getenv("AZURE_RESOURCE_GROUP"),
            project_name=os.getenv("AZURE_AI_PROJECT_NAME"),
        )
        
        await project_client.agents.delete_agent(agent_id)
        logger.info(f"Cleaned up agent: {agent_id}")
        
        await project_client.close()
    except Exception as e:
        logger.error(f"Error cleaning up agent {agent_id}: {e}")


async def main():
    """Main function to deploy CEO Log Agent."""
    agent_id = None
    try:
        # Deploy the agent
        agent_id = await deploy_ceo_log_agent()
        
        # Optionally clean up (comment out to keep the agent deployed)
        # if agent_id:
        #     logger.info("\nCleaning up...")
        #     await cleanup_agent(agent_id)
        
    except KeyboardInterrupt:
        logger.info("\nDeployment interrupted by user")
        if agent_id:
            logger.info("Cleaning up...")
            await cleanup_agent(agent_id)
    except Exception as e:
        logger.error(f"Deployment failed: {e}")
        if agent_id:
            logger.info("Cleaning up due to error...")
            await cleanup_agent(agent_id)


if __name__ == "__main__":
    logger.info("Starting CEO Log Agent deployment...")
    asyncio.run(main())