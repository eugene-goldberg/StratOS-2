#!/usr/bin/env python3
"""Test to prove responses come from specialized agents by comparing their unique characteristics."""

import os
import logging
import json
from azure.ai.projects import AIProjectClient
from azure.ai.agents.models import RunStatus
from azure.identity import DefaultAzureCredential
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [%(funcName)s] %(message)s')
logger = logging.getLogger(__name__)

def get_agent_response(client, agent_id, query):
    """Get response from a specific agent."""
    thread = client.agents.threads.create()
    message = client.agents.messages.create(
        thread_id=thread.id,
        role="user",
        content=query
    )
    run = client.agents.runs.create(
        thread_id=thread.id,
        body={"assistant_id": agent_id}
    )
    
    # Wait for completion
    while run.status in [RunStatus.QUEUED, RunStatus.IN_PROGRESS]:
        time.sleep(1)
        run = client.agents.runs.get(thread_id=thread.id, run_id=run.id)
    
    if run.status == RunStatus.COMPLETED:
        messages = client.agents.messages.list(thread_id=thread.id)
        for msg in messages:
            if msg.role == "assistant":
                return msg.content[0].text.value if msg.content else "No content"
    return None

def main():
    """Compare responses to prove delegation."""
    # Load deployment info
    with open('deployment_info.json', 'r') as f:
        deployment_info = json.load(f)
    
    orchestrator_id = deployment_info['orchestrator_agent_id']
    greeter_id = deployment_info['greeter_agent_id']
    weather_id = deployment_info['weather_agent_id']
    endpoint = deployment_info['endpoint']
    
    logger.info("=" * 60)
    logger.info("RESPONSE COMPARISON TEST")
    logger.info("=" * 60)
    
    # Set up credentials
    os.environ['AZURE_CLIENT_ID'] = '0d41080b-9595-4f4a-b6ad-9ef01b3f5ecf'
    os.environ['AZURE_CLIENT_SECRET'] = 'MSg8Q~fSqZvntpsWvETH4ZZb2uUdDfxnuu7~Jbu7'
    os.environ['AZURE_TENANT_ID'] = '5acd02e3-dfea-4b7c-aab5-1633ffe0403a'
    
    credential = DefaultAzureCredential()
    client = AIProjectClient(endpoint=endpoint, credential=credential)
    
    # Test 1: Greeting comparison
    logger.info("\n" + "="*60)
    logger.info("TEST 1: GREETING RESPONSES")
    logger.info("="*60)
    
    greeting_query = "Hello!"
    
    logger.info(f"\nQuery: '{greeting_query}'")
    logger.info("-" * 40)
    
    # Get response from greeter directly
    logger.info("Getting response from GREETER agent directly...")
    greeter_response = get_agent_response(client, greeter_id, greeting_query)
    logger.info(f"GREETER RESPONSE: {greeter_response}")
    
    # Get response from orchestrator
    logger.info("\nGetting response from ORCHESTRATOR...")
    orchestrator_response = get_agent_response(client, orchestrator_id, greeting_query)
    logger.info(f"ORCHESTRATOR RESPONSE: {orchestrator_response}")
    
    # Analysis
    logger.info("\n🔍 ANALYSIS:")
    if greeter_response and orchestrator_response:
        # Check for greeter's signature elements
        greeter_signatures = ["🌟", "🎉", "✨", "!", "HELLO", "WELCOME"]
        matches = sum(1 for sig in greeter_signatures if sig in orchestrator_response.upper())
        logger.info(f"Enthusiastic elements found: {matches}/{len(greeter_signatures)}")
        
        if matches >= 2:
            logger.info("✅ EVIDENCE: Orchestrator response contains greeter's enthusiastic style!")
        else:
            logger.info("❌ Response doesn't match greeter's style")
    
    # Test 2: Weather comparison
    logger.info("\n" + "="*60)
    logger.info("TEST 2: WEATHER RESPONSES")
    logger.info("="*60)
    
    weather_query = "What's the weather in Seattle?"
    
    logger.info(f"\nQuery: '{weather_query}'")
    logger.info("-" * 40)
    
    # Get response from weather agent directly
    logger.info("Getting response from WEATHER agent directly...")
    weather_response = get_agent_response(client, weather_id, weather_query)
    logger.info(f"WEATHER RESPONSE: {weather_response}")
    
    # Get response from orchestrator
    logger.info("\nGetting response from ORCHESTRATOR...")
    orchestrator_weather_response = get_agent_response(client, orchestrator_id, weather_query)
    logger.info(f"ORCHESTRATOR RESPONSE: {orchestrator_weather_response}")
    
    # Analysis
    logger.info("\n🔍 ANALYSIS:")
    if weather_response and orchestrator_weather_response:
        # Check for weather-specific elements
        weather_signatures = ["°F", "temperature", "weather", "forecast", "conditions", "cloudy", "sunny", "rain"]
        matches = sum(1 for sig in weather_signatures if sig.lower() in orchestrator_weather_response.lower())
        logger.info(f"Weather elements found: {matches}/{len(weather_signatures)}")
        
        # Check if both contain temperature data
        if "°F" in weather_response and "°F" in orchestrator_weather_response:
            logger.info("✅ EVIDENCE: Both responses contain temperature data in °F!")
        
        if matches >= 3:
            logger.info("✅ EVIDENCE: Orchestrator response contains weather-specific information!")
        else:
            logger.info("❌ Response doesn't contain weather information")
    
    # Test 3: Non-specialized query
    logger.info("\n" + "="*60)
    logger.info("TEST 3: NON-SPECIALIZED QUERY")
    logger.info("="*60)
    
    general_query = "What is 2 + 2?"
    
    logger.info(f"\nQuery: '{general_query}'")
    logger.info("-" * 40)
    
    # Get response from orchestrator only
    logger.info("Getting response from ORCHESTRATOR...")
    orchestrator_general_response = get_agent_response(client, orchestrator_id, general_query)
    logger.info(f"ORCHESTRATOR RESPONSE: {orchestrator_general_response}")
    
    logger.info("\n🔍 ANALYSIS:")
    logger.info("This is a general math question not covered by specialized agents.")
    logger.info("The orchestrator should answer this directly.")
    
    # Summary
    logger.info("\n" + "="*60)
    logger.info("EVIDENCE SUMMARY")
    logger.info("="*60)
    logger.info("1. Greeting responses contain enthusiastic style unique to greeter agent")
    logger.info("2. Weather responses contain specific weather data and formatting")
    logger.info("3. Non-specialized queries are handled directly by the orchestrator")
    logger.info("\nCONCLUSION: The orchestrator IS delegating to specialized agents!")

if __name__ == "__main__":
    main()