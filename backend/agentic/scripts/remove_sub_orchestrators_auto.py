#!/usr/bin/env python3
"""
Remove sub-orchestrator agents from Azure AI Agent Service (non-interactive version).

In Phase 1 Unified MAS architecture, we use a single Main Orchestrator
instead of multiple sub-orchestrators (routers).
"""

import asyncio
import os
import sys
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

# Sub-orchestrators to remove (not needed in Phase 1 Unified MAS)
SUB_ORCHESTRATORS_TO_REMOVE = [
    "StrategicContextRouter",
    "AnalysisOrchestrator", 
    "PlanningCoordinator"
]

async def remove_sub_orchestrators():
    """Remove sub-orchestrator agents from Azure AI Agent Service."""
    
    try:
        # Check required environment variables
        required_vars = [
            "AZURE_AI_AGENT_PROJECT_NAME",
            "AZURE_AI_AGENT_PROJECT_HUB_NAME",
            "AZURE_AI_AGENT_PROJECT_RESOURCE_GROUP",
            "AZURE_AI_AGENT_PROJECT_SUBSCRIPTION_ID",
            "AZURE_AI_AGENT_API_VERSION"
        ]
        
        logger.info("--- Checking required Azure AI Project context variables ---")
        for var_name in required_vars:
            val = os.getenv(var_name)
            if not val:
                logger.error(f"CRITICAL: Required environment variable '{var_name}' is not set.")
                sys.exit(1)
            logger.info(f"  {var_name}: '{val}'")
        
        # Initialize settings
        settings = AzureAIAgentSettings()
        logger.info(f"--- AzureAIAgentSettings initialized ---")
        logger.info(f"  Endpoint: {settings.endpoint}")
        logger.info(f"  API Version: {settings.api_version}")
        
        # Create credential
        credential = DefaultAzureCredential()
        
        # Create client using the same pattern as deploy script
        async with AzureAIAgent.create_client(credential=credential, settings=settings) as client:
            logger.info("Successfully connected to Azure AI Agent Service")
            
            # List all agents
            logger.info("\n📋 Listing all agents...")
            all_agents = []
            agents_to_remove = []
            
            async for agent in client.agents.list_agents():
                agent_info = {
                    "id": agent.id,
                    "name": agent.name,
                    "description": agent.description,
                    "model": agent.model,
                    "created_at": agent.created_at
                }
                all_agents.append(agent_info)
                
                # Check if this is a sub-orchestrator to remove
                if agent.name in SUB_ORCHESTRATORS_TO_REMOVE:
                    agents_to_remove.append(agent_info)
            
            logger.info(f"Total agents found: {len(all_agents)}")
            
            # Display current agents
            print("\n" + "="*80)
            print("CURRENT AGENTS IN AZURE AI AGENT SERVICE")
            print("="*80)
            
            # Separate StratOS agents from test agents
            stratos_agents = []
            test_agents = []
            
            for agent in all_agents:
                if any(agent['name'].startswith(prefix) for prefix in ['test', 'Test', 'demo', 'Chat', 'Calculator', 'Weather', 'Orchestrator']):
                    test_agents.append(agent)
                else:
                    stratos_agents.append(agent)
            
            print(f"\n✅ StratOS Agents ({len(stratos_agents)}):")
            for agent in stratos_agents:
                print(f"  • {agent['name']}")
                if agent['name'] in SUB_ORCHESTRATORS_TO_REMOVE:
                    print(f"    ⚠️  SUB-ORCHESTRATOR - TO BE REMOVED")
            
            if test_agents:
                print(f"\n🧪 Test/Demo Agents ({len(test_agents)}):")
                for agent in test_agents:
                    print(f"  • {agent['name']}")
            
            if not agents_to_remove:
                print("\n✅ No sub-orchestrators found to remove.")
                print("Phase 1 Unified MAS is ready with no conflicting sub-orchestrators.")
                return
            
            # Show agents to be removed
            print("\n" + "="*80)
            print("⚠️  SUB-ORCHESTRATORS TO REMOVE")
            print("="*80)
            print(f"\nThe following {len(agents_to_remove)} sub-orchestrators will be removed:")
            for agent in agents_to_remove:
                print(f"\n  • {agent['name']}")
                print(f"    ID: {agent['id']}")
                print(f"    Description: {agent['description']}")
                print(f"    Created: {agent['created_at']}")
            
            print("\nThese sub-orchestrators are not needed in Phase 1 Unified MAS architecture.")
            print("The Main Orchestrator will handle all routing.")
            
            # AUTO-PROCEED WITH DELETION
            print("\n🗑️  AUTO-DELETING sub-orchestrators...")
            success_count = 0
            failed_count = 0
            
            for agent in agents_to_remove:
                try:
                    logger.info(f"Deleting {agent['name']} (ID: {agent['id']})...")
                    await client.agents.delete_agent(agent['id'])
                    logger.info(f"✅ Successfully deleted {agent['name']}")
                    print(f"  ✅ Deleted: {agent['name']}")
                    success_count += 1
                except Exception as e:
                    logger.error(f"❌ Failed to delete {agent['name']}: {str(e)}")
                    print(f"  ❌ Failed: {agent['name']} - {str(e)}")
                    failed_count += 1
            
            # Summary
            print("\n" + "="*80)
            print("DELETION SUMMARY")
            print("="*80)
            print(f"Total sub-orchestrators found: {len(agents_to_remove)}")
            print(f"✅ Successfully deleted: {success_count}")
            if failed_count > 0:
                print(f"❌ Failed to delete: {failed_count}")
            
            # List remaining agents
            print("\n📋 Verifying remaining agents...")
            remaining_stratos_agents = []
            remaining_test_agents = []
            
            async for agent in client.agents.list_agents():
                if any(agent.name.startswith(prefix) for prefix in ['test', 'Test', 'demo', 'Chat', 'Calculator', 'Weather', 'Orchestrator']):
                    remaining_test_agents.append(agent.name)
                else:
                    remaining_stratos_agents.append(agent.name)
            
            print(f"\n✅ Remaining StratOS Agents ({len(remaining_stratos_agents)}):")
            for name in sorted(remaining_stratos_agents):
                print(f"  • {name}")
            
            if remaining_test_agents:
                print(f"\n🧪 Test/Demo Agents ({len(remaining_test_agents)}):")
                for name in sorted(remaining_test_agents):
                    print(f"  • {name}")
            
            print("\n✅ Phase 1 Unified MAS cleanup complete!")
            print("The Main Orchestrator will handle all routing without sub-orchestrators.")
            
    except Exception as e:
        logger.error(f"Error: {str(e)}", exc_info=True)
        sys.exit(1)
    finally:
        # Clean up credential
        await credential.close()

async def main():
    """Main entry point."""
    print("="*80)
    print("REMOVING SUB-ORCHESTRATOR AGENTS FROM AZURE AI AGENT SERVICE")
    print("Phase 1 uses a single Main Orchestrator instead of sub-orchestrators")
    print("AUTO-DELETE MODE - No confirmation required")
    print("="*80)
    
    await remove_sub_orchestrators()

if __name__ == "__main__":
    asyncio.run(main())