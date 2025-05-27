#!/usr/bin/env python3
"""Fix orchestrator with proven working instructions."""

import logging
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
import os
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [%(funcName)s] %(message)s')
logger = logging.getLogger(__name__)

# Environment variables
connection_string = os.getenv("AZURE_AI_PROJECT_CONNECTION_STRING")
model = os.getenv("AZURE_AI_MODEL_DEPLOYMENT_NAME", "gpt-35-turbo")

def main():
    """Update orchestrator with proven working instructions."""
    # Load deployment info
    with open("deployment_info.json", "r") as f:
        deployment_info = json.load(f)
    
    orchestrator_id = deployment_info["orchestrator_agent_id"]
    
    credential = DefaultAzureCredential()
    client = AIProjectClient(endpoint=connection_string, credential=credential)
    
    logger.info("Updating orchestrator with PROVEN WORKING instructions...")
    
    # Instructions that are PROVEN to work from test_connected_working.py
    working_instructions = (
        "You are an orchestrator assistant that has access to specialized tools.\n\n"
        "IMPORTANT TOOL USAGE RULES:\n"
        "1. You have a tool called 'enthusiastic_greeter_tool' that provides enthusiastic greetings.\n"
        "2. You have a tool called 'weather_information_tool' that provides weather information.\n"
        "3. When the user asks for ANY kind of greeting, hello, hi, or similar, you MUST:\n"
        "   - Use the 'enthusiastic_greeter_tool' to get the greeting\n"
        "   - Pass the greeting request to the tool\n"
        "   - Return the tool's response to the user\n"
        "4. When the user asks for weather, temperature, or forecast, you MUST:\n"
        "   - Use the 'weather_information_tool' to get weather data\n"
        "   - Pass the location to the tool\n"
        "   - Return the tool's response to the user\n"
        "5. DO NOT provide your own greetings or weather - ALWAYS use the tools.\n"
        "6. For non-greeting and non-weather questions, answer them normally.\n\n"
        "Example interactions:\n"
        "User: 'Hi there!'\n"
        "You: [Use enthusiastic_greeter_tool]\n"
        "Tool response: 'HELLO THERE!!! 🎉🎉🎉...'\n"
        "You: Return the tool's enthusiastic response\n\n"
        "User: 'What's the weather in Seattle?'\n"
        "You: [Use weather_information_tool]\n"
        "Tool response: '📍 Weather for Seattle...'\n"
        "You: Return the tool's weather response\n\n"
        "Remember: ALWAYS delegate greetings to enthusiastic_greeter_tool and weather to weather_information_tool!"
    )
    
    # Update the orchestrator
    updated_orchestrator = client.agents.update_agent(
        agent_id=orchestrator_id,
        instructions=working_instructions
    )
    
    logger.info(f"✅ Updated orchestrator: {orchestrator_id}")
    logger.info(f"Applied PROVEN WORKING instructions from test_connected_working.py")
    
    # Save updated info
    deployment_info["instructions_version"] = "proven_working_v1"
    with open("deployment_info.json", "w") as f:
        json.dump(deployment_info, f, indent=2)
    
    logger.info("\n✅ Orchestrator fixed with proven working instructions!")
    logger.info("These are the EXACT instructions that work in test_connected_working.py")
    logger.info("Run test_deployed_system.py to verify delegation now works")

if __name__ == "__main__":
    main()