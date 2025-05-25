#!/usr/bin/env python3
"""
Deploy StratOS agents to Azure OpenAI Assistants using API key authentication.
"""

import asyncio
import os
import sys
import json
import logging
from datetime import datetime
from dotenv import load_dotenv

# Add parent directories to path
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
sys.path.insert(0, backend_dir)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
env_path = os.path.join(backend_dir, '.env')
load_dotenv(env_path)
logger.info(f"Loading .env file from: {env_path}")

# Import required modules
try:
    from semantic_kernel.agents import AzureAIAgent, AzureAIAgentSettings
    from azure.core.credentials import AzureKeyCredential
except ImportError as e:
    logger.error(f"Error importing required modules: {e}")
    logger.error("Please ensure 'semantic-kernel[azure]' is installed.")
    sys.exit(1)

async def deploy_agent(
    agent_name: str,
    agent_instructions: str,
    agent_description: str,
    settings: AzureAIAgentSettings,
    credential
) -> tuple[AzureAIAgent | None, str | None]:
    """
    Deploys an agent using the configured Azure OpenAI endpoint.
    """
    try:
        async with AzureAIAgent.create_client(credential=credential, settings=settings) as client:
            logger.info(f"Deploying agent: {agent_name}")
            
            # Try to create new agent directly
            try:
                agent_definition = await client.agents.create_agent(
                    model=settings.model_deployment_name,
                    name=agent_name,
                    instructions=agent_instructions,
                    description=agent_description
                )
                logger.info(f"Agent '{agent_name}' created successfully with ID: {agent_definition.id}")
                
                # Create Semantic Kernel agent instance
                sk_agent = AzureAIAgent(
                    client=client,
                    definition=agent_definition,
                )
                
                return sk_agent, agent_definition.id
                
            except Exception as create_error:
                logger.error(f"Failed to create agent '{agent_name}': {create_error}")
                raise

    except Exception as e:
        logger.error(f"Failed to deploy agent '{agent_name}': {e}")
        raise

async def main():
    """Main deployment function"""
    logger.info("===== StratOS Agent Deployment using API Key =====")
    logger.info(f"Deployment started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Get credentials from environment
        endpoint = "https://sk-multi-agent-openai.openai.azure.com/"
        api_key = os.getenv("AZURE_OPENAI_API_KEY")
        
        if not api_key:
            logger.error("AZURE_OPENAI_API_KEY not found in environment")
            sys.exit(1)
            
        # Set environment variables for AzureAIAgentSettings
        os.environ["AZURE_AI_AGENT_ENDPOINT"] = endpoint
        os.environ["AZURE_AI_AGENT_API_KEY"] = api_key
        os.environ["AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME"] = "gpt-35-turbo"
        os.environ["AZURE_AI_AGENT_API_VERSION"] = "2024-05-01-preview"
        
        logger.info(f"Using endpoint: {endpoint}")
        logger.info(f"Using deployment: gpt-35-turbo")
        logger.info("Using API key authentication")
        
        # Create settings
        settings = AzureAIAgentSettings()
        
        # Create credential
        credential = AzureKeyCredential(api_key)
        
        # Try to deploy a single test agent first
        try:
            agent, agent_id = await deploy_agent(
                agent_name="TestAgent",
                agent_instructions="You are a test agent for StratOS deployment verification.",
                agent_description="Test agent to verify deployment capability",
                settings=settings,
                credential=credential
            )
            
            logger.info(f"\n✅ SUCCESS! Test agent deployed with ID: {agent_id}")
            logger.info("\nThe Azure OpenAI Assistants API is working correctly.")
            logger.info("You can now proceed to deploy all StratOS agents.")
            
            # Save test deployment info
            deployment_info = {
                "deployment_time": datetime.now().isoformat(),
                "deployment_type": "azure_openai_assistant_test",
                "endpoint": endpoint,
                "model_deployment": "gpt-35-turbo",
                "test_agent_id": agent_id,
                "status": "success"
            }
            
            deployment_file = os.path.join(backend_dir, "deployment_configs", "test_deployment.json")
            os.makedirs(os.path.dirname(deployment_file), exist_ok=True)
            
            with open(deployment_file, "w") as f:
                json.dump(deployment_info, f, indent=2)
                
            logger.info(f"Test deployment info saved to: {deployment_file}")
            
        except Exception as e:
            logger.error(f"Test deployment failed: {e}")
            logger.error("\nPossible issues:")
            logger.error("1. The Assistants API might not be available in your region")
            logger.error("2. Your Azure OpenAI resource might need to be in a supported region")
            logger.error("3. The API version might need to be different")
            logger.error("4. Check if your subscription has access to the Assistants feature")
            
    except Exception as e:
        logger.error(f"Setup failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())