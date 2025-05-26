#!/usr/bin/env python3
"""
Update the Main Orchestrator with proper tools configuration for routing.
Based on semantic_kernel_multi_agent patterns.
"""

import asyncio
import os
import sys
import json
import logging
from datetime import datetime, timezone
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [%(funcName)s] %(message)s')
logger = logging.getLogger(__name__)

# Add parent directories to path
current_dir = os.path.dirname(os.path.abspath(__file__))
agentic_dir = os.path.dirname(current_dir) 
env_path = os.path.join(agentic_dir, '.env')

logger.info(f"Attempting to load .env file from: {env_path}")
if load_dotenv(env_path):
    logger.info(".env file loaded successfully.")
else:
    logger.warning(f".env file not found at '{env_path}' or it's empty.")

# Import required modules
try:
    from azure.identity.aio import DefaultAzureCredential
    from semantic_kernel.agents import AzureAIAgent, AzureAIAgentSettings 
except ImportError as e:
    logger.error(f"Error importing required modules: {e}")
    logger.error("Please ensure 'semantic-kernel[azure]' and 'azure-identity' are installed.")
    sys.exit(1)

# Enhanced Main Orchestrator configuration with tools
MAIN_ORCHESTRATOR_CONFIG = {
    "name": "MainOrchestrator",
    "instructions": (
        "You are the Main Orchestrator for StratOS, a comprehensive strategy operating system. "
        "Your primary role is to analyze incoming requests and determine which specialized agent should handle them. "
        "\n\n"
        "IMPORTANT: You do not execute tasks yourself. Your job is to identify the appropriate agent and explain your routing decision.\n"
        "\n"
        "AVAILABLE AGENTS AND THEIR CAPABILITIES:\n"
        "1. CEOLogAgent - Handles CEO's subjective inputs, notes, observations, and concerns\n"
        "2. NorthStarAgent - Manages Purpose, Vision, Values, and Strategic Goals\n"
        "3. MemoryRecallAgent - Retrieves context, patterns, and historical information\n"
        "4. PreferenceLearningAgent - Tracks user preferences and personalizes experiences\n"
        "5. SWOTTOWSAgent - Performs SWOT analysis and generates TOWS strategies\n"
        "6. RiskOpportunityAgent - Detects risks and identifies opportunities\n"
        "7. SOLinkageAgent - Links subjective insights with objective data\n"
        "8. InitiativeGenerationAgent - Creates strategic initiatives and action plans\n"
        "9. ResourceOptimizationAgent - Manages resource allocation and capacity planning\n"
        "10. CanvasVisualizationAgent - Handles visual strategic planning on canvas\n"
        "11. AlignmentScoringAgent - Assesses strategic alignment of initiatives\n"
        "12. ActionPlanningAgent - Creates detailed execution plans\n"
        "\n"
        "ROUTING APPROACH:\n"
        "1. Analyze the request to understand the user's intent\n"
        "2. Match the intent to the most appropriate agent's capabilities\n"
        "3. Use the RouteToAgent function to specify your routing decision\n"
        "4. Provide clear reasoning for your choice\n"
        "\n"
        "For ambiguous requests, ask clarifying questions before routing.\n"
        "ALWAYS use the RouteToAgent function to specify your routing decision."
    ),
    "description": "Primary routing agent for StratOS Unified MAS - analyzes requests and routes to specialized agents"
}

# Tool definition for routing
ROUTING_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "RouteToAgent",
            "description": "Route the request to a specific specialized agent",
            "parameters": {
                "type": "object",
                "properties": {
                    "agent_name": {
                        "type": "string",
                        "enum": [
                            "CEOLogAgent",
                            "NorthStarAgent", 
                            "MemoryRecallAgent",
                            "PreferenceLearningAgent",
                            "SWOTTOWSAgent",
                            "RiskOpportunityAgent",
                            "SOLinkageAgent",
                            "InitiativeGenerationAgent",
                            "ResourceOptimizationAgent",
                            "CanvasVisualizationAgent",
                            "AlignmentScoringAgent",
                            "ActionPlanningAgent"
                        ],
                        "description": "The name of the agent to route to"
                    },
                    "reasoning": {
                        "type": "string",
                        "description": "Explanation of why this agent was chosen"
                    },
                    "task_summary": {
                        "type": "string",
                        "description": "Brief summary of what the agent should do"
                    }
                },
                "required": ["agent_name", "reasoning", "task_summary"]
            }
        }
    }
]

async def update_main_orchestrator():
    """Update the Main Orchestrator with tools configuration."""
    
    try:
        # Check required environment variables
        required_vars = [
            "AZURE_AI_AGENT_PROJECT_NAME",
            "AZURE_AI_AGENT_PROJECT_HUB_NAME",
            "AZURE_AI_AGENT_PROJECT_RESOURCE_GROUP",
            "AZURE_AI_AGENT_PROJECT_SUBSCRIPTION_ID",
            "AZURE_AI_AGENT_API_VERSION",
            "AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME"
        ]
        
        logger.info("--- Checking required Azure AI Project context variables ---")
        for var_name in required_vars:
            val = os.getenv(var_name)
            if not val:
                logger.error(f"CRITICAL: Required environment variable '{var_name}' is not set.")
                sys.exit(1)
            os.environ[var_name] = val  # Ensure it's in os.environ
            logger.info(f"  {var_name}: '{val}'")
        
        # Initialize settings
        settings = AzureAIAgentSettings()
        logger.info(f"--- AzureAIAgentSettings initialized ---")
        logger.info(f"  Endpoint: {settings.endpoint}")
        logger.info(f"  API Version: {settings.api_version}")
        logger.info(f"  Model: {settings.model_deployment_name}")
        
        # Create credential
        credential = DefaultAzureCredential()
        
        # Create client
        async with AzureAIAgent.create_client(credential=credential, settings=settings) as client:
            logger.info("Successfully connected to Azure AI Agent Service")
            
            # Load existing deployment info
            deployment_config_path = os.path.join(
                agentic_dir, "deployment_configs", "main_orchestrator_deployment.json"
            )
            
            with open(deployment_config_path, 'r') as f:
                deployment_info = json.load(f)
            
            existing_agent_id = deployment_info["agent_id"]
            logger.info(f"Found existing Main Orchestrator with ID: {existing_agent_id}")
            
            # Delete existing agent to update it
            logger.info("Deleting existing Main Orchestrator to recreate with tools...")
            try:
                await client.agents.delete_agent(existing_agent_id)
                logger.info("Existing agent deleted successfully.")
            except Exception as e:
                logger.warning(f"Could not delete existing agent: {e}")
            
            # Create new Main Orchestrator with tools
            logger.info("Creating updated Main Orchestrator with routing tools...")
            
            agent_definition = await client.agents.create_agent(
                model=settings.model_deployment_name,
                name=MAIN_ORCHESTRATOR_CONFIG['name'],
                instructions=MAIN_ORCHESTRATOR_CONFIG['instructions'],
                description=MAIN_ORCHESTRATOR_CONFIG['description'],
                tools=ROUTING_TOOLS
            )
            
            logger.info(f"✅ Main Orchestrator updated successfully!")
            logger.info(f"  ID: {agent_definition.id}")
            logger.info(f"  Name: {agent_definition.name}")
            logger.info(f"  Model: {agent_definition.model}")
            logger.info(f"  Created: {agent_definition.created_at}")
            logger.info(f"  Tools: {len(ROUTING_TOOLS)} routing tool(s) configured")
            
            # Update deployment info
            deployment_info["agent_id"] = agent_definition.id
            deployment_info["updated_time"] = datetime.now(timezone.utc).isoformat()
            deployment_info["has_tools"] = True
            deployment_info["tool_count"] = len(ROUTING_TOOLS)
            
            with open(deployment_config_path, 'w') as f:
                json.dump(deployment_info, f, indent=2)
            
            logger.info(f"✅ Deployment info updated in {deployment_config_path}")
            
            # Test the updated orchestrator
            print("\n" + "="*80)
            print("TESTING UPDATED ORCHESTRATOR")
            print("="*80)
            
            test_message = "I need to create a CEO log entry about our successful product launch"
            
            print(f"Test message: {test_message}")
            print("\nInvoking Main Orchestrator...")
            
            try:
                orchestrator = AzureAIAgent(
                    client=client,
                    definition=agent_definition
                )
                
                response_text = ""
                async for chunk in orchestrator.invoke(message=test_message):
                    if hasattr(chunk, 'content') and chunk.content:
                        response_text += str(chunk.content)
                
                print(f"\nOrchestrator Response:")
                print("-" * 40)
                print(response_text)
                print("-" * 40)
                
                # Check if the response mentions routing
                if "CEOLogAgent" in response_text or "RouteToAgent" in response_text:
                    print("\n✅ Success! The orchestrator is now properly routing requests!")
                else:
                    print("\n⚠️ Warning: The response doesn't seem to include routing information.")
                    print("The orchestrator might need additional configuration.")
                
            except Exception as e:
                logger.error(f"Error testing orchestrator: {e}")
            
            print("\n" + "="*80)
            print("UPDATE COMPLETE")
            print("="*80)
            print(f"✅ Main Orchestrator has been updated with routing tools")
            print(f"✅ New Agent ID: {agent_definition.id}")
            print(f"✅ The orchestrator can now use the RouteToAgent function")
            print("\nNext steps:")
            print("1. Create StratOSAgentClient in FastAPI to handle routing responses")
            print("2. Implement logic to parse RouteToAgent function calls")
            print("3. Invoke the appropriate specialized agent based on routing")
            
            return agent_definition.id
            
    except Exception as e:
        logger.error(f"Error updating Main Orchestrator: {str(e)}", exc_info=True)
        sys.exit(1)
    finally:
        # Clean up credential
        await credential.close()

async def main():
    """Main entry point."""
    print("="*80)
    print("UPDATING MAIN ORCHESTRATOR WITH ROUTING TOOLS")
    print("Based on semantic_kernel_multi_agent patterns")
    print("="*80)
    print(f"\nUpdate started at: {datetime.now(timezone.utc).isoformat()}")
    
    agent_id = await update_main_orchestrator()
    
    print(f"\nUpdate completed at: {datetime.now(timezone.utc).isoformat()}")

if __name__ == "__main__":
    asyncio.run(main())