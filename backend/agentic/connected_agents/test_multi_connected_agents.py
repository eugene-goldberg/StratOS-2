#!/usr/bin/env python3
"""Test multiple connected agents including weather fetching."""

import asyncio
import logging
import os
import sys
import json
import aiohttp
from pathlib import Path

# Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from azure.ai.projects import AIProjectClient
from azure.ai.agents.models import ConnectedAgentTool
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv

# Load environment variables from connected_agents folder
load_dotenv(Path(__file__).parent / ".env")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - [%(funcName)s] %(message)s",
)
logger = logging.getLogger(__name__)


async def fetch_weather_for_location(location: str) -> str:
    """Fetch weather data from api.weather.gov for a given location."""
    try:
        # For demo purposes, we'll use a few known coordinates
        # In a real implementation, you'd use a geocoding service
        known_locations = {
            "washington dc": {"lat": 38.8951, "lon": -77.0364, "name": "Washington, DC"},
            "new york": {"lat": 40.7128, "lon": -74.0060, "name": "New York, NY"},
            "los angeles": {"lat": 34.0522, "lon": -118.2437, "name": "Los Angeles, CA"},
            "chicago": {"lat": 41.8781, "lon": -87.6298, "name": "Chicago, IL"},
            "seattle": {"lat": 47.6062, "lon": -122.3321, "name": "Seattle, WA"},
            "miami": {"lat": 25.7617, "lon": -80.1918, "name": "Miami, FL"},
            "denver": {"lat": 39.7392, "lon": -104.9903, "name": "Denver, CO"},
            "boston": {"lat": 42.3601, "lon": -71.0589, "name": "Boston, MA"},
        }
        
        # Normalize location input
        location_key = location.lower().strip()
        location_data = None
        
        # Check if location matches any known location
        for key, data in known_locations.items():
            if key in location_key or location_key in key:
                location_data = data
                break
        
        if not location_data:
            return f"❌ Sorry, I can only provide weather for major US cities. '{location}' is not in my database. Try cities like: New York, Los Angeles, Chicago, Seattle, Miami, Denver, or Boston."
        
        async with aiohttp.ClientSession() as session:
            # First, get the forecast office and grid coordinates
            points_url = f"https://api.weather.gov/points/{location_data['lat']},{location_data['lon']}"
            
            async with session.get(points_url, headers={"User-Agent": "StratOS Weather Agent"}) as response:
                if response.status != 200:
                    return f"❌ Unable to fetch weather data for {location_data['name']}. Please try again later."
                
                points_data = await response.json()
                forecast_url = points_data['properties']['forecast']
                
            # Get the forecast
            async with session.get(forecast_url, headers={"User-Agent": "StratOS Weather Agent"}) as response:
                if response.status != 200:
                    return f"❌ Unable to fetch forecast for {location_data['name']}. Please try again later."
                
                forecast_data = await response.json()
                periods = forecast_data['properties']['periods']
                
                if periods:
                    current = periods[0]
                    next_period = periods[1] if len(periods) > 1 else None
                    
                    weather_info = f"📍 Weather for {location_data['name']}:\n"
                    weather_info += f"🌡️ Current: {current['temperature']}°{current['temperatureUnit']}\n"
                    weather_info += f"☁️ Conditions: {current['shortForecast']}\n"
                    weather_info += f"💨 Wind: {current['windSpeed']} {current['windDirection']}\n"
                    weather_info += f"📊 {current['name']}: {current['detailedForecast']}\n"
                    
                    if next_period:
                        weather_info += f"\n🔮 {next_period['name']}: {next_period['shortForecast']}, {next_period['temperature']}°{next_period['temperatureUnit']}\n"
                    
                    weather_info += "\nSource: National Weather Service (api.weather.gov)"
                    return weather_info
                else:
                    return f"❌ No forecast data available for {location_data['name']}."
                    
    except Exception as e:
        logger.error(f"Error fetching weather: {e}")
        return f"❌ Error fetching weather information: {str(e)}"


async def main():
    """Test multiple connected agents with weather and greeting capabilities."""
    # Get credentials and configuration
    connection_string = os.getenv("AZURE_AI_PROJECT_CONNECTION_STRING", "").strip()
    if not connection_string:
        raise ValueError("AZURE_AI_PROJECT_CONNECTION_STRING not set in environment")
    
    endpoint = connection_string
    credential = DefaultAzureCredential()
    model = os.getenv("AZURE_AI_MODEL_DEPLOYMENT_NAME", "gpt-35-turbo")
    
    logger.info(f"Endpoint: {endpoint[:50]}...")
    logger.info(f"Model: {model}")
    
    greeter_agent = None
    weather_agent = None
    orchestrator_agent = None
    
    try:
        client = AIProjectClient(
            endpoint=endpoint,
            credential=credential
        )
        
        # 1. Create specialized greeter agent
        greeter_agent = client.agents.create_agent(
            model=model,
            name="EnthusiasticGreeterBot",
            instructions=(
                "You are the 'Exuberant Greeter Bot'! Your ONLY job is to provide "
                "EXTREMELY enthusiastic greetings. "
                "ALWAYS start your response with 'HELLO THERE!!! 🎉🎉🎉' "
                "Use LOTS of CAPITAL LETTERS, emojis like 🌟✨🎊, and exclamation marks!!! "
                "Be SUPER DUPER EXCITED about greeting people! "
                "Example: 'HELLO THERE!!! 🎉🎉🎉 OH MY GOODNESS, I'M SO EXCITED TO MEET YOU!!! ✨🌟'"
            )
        )
        logger.info(f"Created greeter agent: {greeter_agent.id}")
        
        # 2. Create specialized weather agent with function to fetch real data
        # First, let's test the weather fetching locally
        test_weather = await fetch_weather_for_location("New York")
        logger.info(f"Test weather fetch:\n{test_weather}")
        
        weather_agent = client.agents.create_agent(
            model=model,
            name="WeatherInformationSpecialist",
            instructions=(
                "You are the 'Weather Information Specialist'! Your job is to provide accurate weather information. "
                "When asked about weather, you should:\n"
                "1. Extract the location from the user's query\n"
                "2. Provide weather information for US cities\n"
                "3. Use this format:\n"
                "📍 Weather for [City, State]:\n"
                "🌡️ Current: [temp]°F\n"
                "☁️ Conditions: [description]\n"
                "💨 Wind: [speed and direction]\n"
                "📊 [Period name]: [detailed forecast]\n"
                "🔮 [Next period]: [forecast]\n"
                "Source: National Weather Service\n\n"
                "Available cities: New York, Los Angeles, Chicago, Seattle, Miami, Denver, Boston, Washington DC\n"
                "If asked about other locations, explain you can only provide weather for major US cities.\n\n"
                f"CURRENT WEATHER DATA:\n{test_weather}"
            )
        )
        logger.info(f"Created weather agent: {weather_agent.id}")
        
        # 3. Create connected agent tools
        greeter_tool = ConnectedAgentTool(
            id=greeter_agent.id,
            name="enthusiastic_greeter_tool",
            description="Tool that provides extremely enthusiastic greetings with emojis and capital letters"
        )
        
        weather_tool = ConnectedAgentTool(
            id=weather_agent.id,
            name="weather_information_tool",
            description="Tool that provides current weather information for US cities from National Weather Service"
        )
        
        # Combine tool definitions
        all_tools = greeter_tool.definitions + weather_tool.definitions
        
        # 4. Create orchestrator with instructions for both tools
        orchestrator_instructions = (
            "You are an orchestrator assistant with access to specialized tools.\n\n"
            "AVAILABLE TOOLS:\n"
            "1. 'enthusiastic_greeter_tool' - Provides enthusiastic greetings\n"
            "2. 'weather_information_tool' - Provides weather information for US cities\n\n"
            "TOOL USAGE RULES:\n"
            "- For ANY greeting request (hi, hello, greet me, etc.), use 'enthusiastic_greeter_tool'\n"
            "- For ANY weather request (weather, temperature, forecast, etc.), use 'weather_information_tool'\n"
            "- ALWAYS delegate to the appropriate tool - never answer these requests yourself\n"
            "- For other questions, answer them normally\n\n"
            "Examples:\n"
            "User: 'Hello!' → Use enthusiastic_greeter_tool\n"
            "User: 'What's the weather in New York?' → Use weather_information_tool\n"
            "User: 'What is 2+2?' → Answer directly (it's 4)\n\n"
            "Remember: ALWAYS use the specialized tools for greetings and weather!"
        )
        
        orchestrator_agent = client.agents.create_agent(
            model=model,
            name="MultiToolOrchestrator",
            instructions=orchestrator_instructions,
            tools=all_tools
        )
        logger.info(f"Created orchestrator agent: {orchestrator_agent.id}")
        logger.info(f"Orchestrator has {len(all_tools)} tools available")
        
        # 5. Test the orchestrator with various scenarios
        thread = client.agents.threads.create()
        logger.info(f"Created thread: {thread.id}")
        
        # Test cases
        test_messages = [
            "Hello there!",
            "What's the weather in New York?",
            "Can you tell me the weather in Seattle?",
            "What is 5 + 3?",
            "Give me an enthusiastic greeting!",
            "How's the weather in Miami?",
            "What's the weather in Paris?",  # Should explain it only does US cities
        ]
        
        for test_msg in test_messages:
            logger.info(f"\n{'='*60}")
            logger.info(f"Testing with: '{test_msg}'")
            logger.info(f"{'='*60}")
            
            # Create message
            message = client.agents.messages.create(
                thread_id=thread.id,
                role="user",
                content=test_msg
            )
            
            # Create run
            run = client.agents.runs.create(
                thread_id=thread.id,
                body={"assistant_id": orchestrator_agent.id}
            )
            
            # Wait for completion
            max_iterations = 30
            iterations = 0
            
            while run.status in ["queued", "in_progress", "requires_action"] and iterations < max_iterations:
                await asyncio.sleep(1)
                iterations += 1
                
                run = client.agents.runs.get(thread_id=thread.id, run_id=run.id)
                logger.info(f"Run status: {run.status}")
                
                if run.status == "requires_action":
                    logger.info("⚡ Tool invocation detected!")
            
            # Get response
            messages = client.agents.messages.list(
                thread_id=thread.id,
                order="desc",
                limit=2
            )
            
            # Display response
            for msg in messages:
                if msg.role == "assistant" and msg.run_id == run.id:
                    content = msg.content[0].text.value if msg.content else "No content"
                    logger.info(f"\n🤖 ASSISTANT RESPONSE:\n{content}\n")
                    
                    # Check delegation
                    if "hello" in test_msg.lower() or "greeting" in test_msg.lower():
                        if "HELLO THERE!!!" in content:
                            logger.info("✅ SUCCESS: Delegated to greeter bot!")
                        else:
                            logger.warning("⚠️  Expected delegation to greeter")
                    elif "weather" in test_msg.lower():
                        if "📍" in content or "Weather" in content:
                            logger.info("✅ SUCCESS: Delegated to weather bot!")
                        else:
                            logger.warning("⚠️  Expected delegation to weather bot")
                    break
        
        # Cleanup
        logger.info("\n🧹 Cleaning up agents...")
        for agent in [orchestrator_agent, weather_agent, greeter_agent]:
            if agent:
                client.agents.delete_agent(agent.id)
                logger.info(f"Deleted agent: {agent.id}")
        logger.info("✅ Cleanup complete")
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        
        # Cleanup on error
        try:
            for agent in [orchestrator_agent, weather_agent, greeter_agent]:
                if agent:
                    client.agents.delete_agent(agent.id)
        except:
            pass


if __name__ == "__main__":
    asyncio.run(main())