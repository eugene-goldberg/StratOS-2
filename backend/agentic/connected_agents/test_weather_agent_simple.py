#!/usr/bin/env python3
"""Simple test of weather agent fetching real data from api.weather.gov."""

import asyncio
import logging
import os
import sys
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


async def fetch_weather_data():
    """Fetch weather data for multiple cities to embed in agent instructions."""
    weather_data = {}
    
    locations = {
        "new york": {"lat": 40.7128, "lon": -74.0060, "name": "New York, NY"},
        "los angeles": {"lat": 34.0522, "lon": -118.2437, "name": "Los Angeles, CA"},
        "chicago": {"lat": 41.8781, "lon": -87.6298, "name": "Chicago, IL"},
        "seattle": {"lat": 47.6062, "lon": -122.3321, "name": "Seattle, WA"},
        "miami": {"lat": 25.7617, "lon": -80.1918, "name": "Miami, FL"},
    }
    
    async with aiohttp.ClientSession() as session:
        for key, location in locations.items():
            try:
                # Get forecast office and grid coordinates
                points_url = f"https://api.weather.gov/points/{location['lat']},{location['lon']}"
                
                async with session.get(points_url, headers={"User-Agent": "StratOS Weather Agent"}) as response:
                    if response.status == 200:
                        points_data = await response.json()
                        forecast_url = points_data['properties']['forecast']
                        
                        # Get the forecast
                        async with session.get(forecast_url, headers={"User-Agent": "StratOS Weather Agent"}) as forecast_response:
                            if forecast_response.status == 200:
                                forecast_data = await forecast_response.json()
                                periods = forecast_data['properties']['periods']
                                
                                if periods:
                                    current = periods[0]
                                    weather_data[location['name']] = {
                                        'temperature': f"{current['temperature']}°{current['temperatureUnit']}",
                                        'conditions': current['shortForecast'],
                                        'wind': f"{current['windSpeed']} {current['windDirection']}",
                                        'detailed': current['detailedForecast']
                                    }
                                    logger.info(f"Fetched weather for {location['name']}")
            except Exception as e:
                logger.error(f"Error fetching weather for {location['name']}: {e}")
    
    return weather_data


async def main():
    """Test weather agent with real-time data."""
    # Get credentials and configuration
    connection_string = os.getenv("AZURE_AI_PROJECT_CONNECTION_STRING", "").strip()
    if not connection_string:
        raise ValueError("AZURE_AI_PROJECT_CONNECTION_STRING not set in environment")
    
    endpoint = connection_string
    credential = DefaultAzureCredential()
    model = os.getenv("AZURE_AI_MODEL_DEPLOYMENT_NAME", "gpt-35-turbo")
    
    logger.info(f"Endpoint: {endpoint[:50]}...")
    logger.info(f"Model: {model}")
    
    weather_agent = None
    orchestrator_agent = None
    
    try:
        # Fetch current weather data
        logger.info("Fetching current weather data...")
        weather_data = await fetch_weather_data()
        
        # Format weather data for agent instructions
        weather_info = "CURRENT WEATHER DATA:\n\n"
        for city, data in weather_data.items():
            weather_info += f"{city}:\n"
            weather_info += f"  Temperature: {data['temperature']}\n"
            weather_info += f"  Conditions: {data['conditions']}\n"
            weather_info += f"  Wind: {data['wind']}\n"
            weather_info += f"  Details: {data['detailed']}\n\n"
        
        client = AIProjectClient(
            endpoint=endpoint,
            credential=credential
        )
        
        # Create weather specialist agent with real-time data
        weather_agent = client.agents.create_agent(
            model=model,
            name="WeatherSpecialist",
            instructions=(
                "You are a Weather Information Specialist with access to real-time weather data. "
                "Your job is to provide accurate, current weather information.\n\n"
                f"{weather_info}"
                "When asked about weather:\n"
                "1. Look up the city in the current weather data above\n"
                "2. Provide the information in a clear, formatted way\n"
                "3. Always mention this is from the National Weather Service\n"
                "4. If the city isn't in your data, explain you only have data for: "
                "New York, Los Angeles, Chicago, Seattle, and Miami\n\n"
                "Format your response like this:\n"
                "📍 Weather for [City]:\n"
                "🌡️ Temperature: [temp]\n"
                "☁️ Conditions: [conditions]\n"
                "💨 Wind: [wind]\n"
                "📊 Forecast: [details]\n"
                "Source: National Weather Service (api.weather.gov)"
            )
        )
        logger.info(f"Created weather agent: {weather_agent.id}")
        
        # Create connected agent tool
        weather_tool = ConnectedAgentTool(
            id=weather_agent.id,
            name="realtime_weather_tool",
            description="Tool that provides real-time weather data from National Weather Service"
        )
        
        # Create orchestrator with very explicit instructions
        orchestrator_agent = client.agents.create_agent(
            model=model,
            name="WeatherOrchestrator",
            instructions=(
                "You are an orchestrator that helps users with weather information.\n\n"
                "IMPORTANT: You have access to the 'realtime_weather_tool' which provides current weather data.\n\n"
                "RULES:\n"
                "1. For ANY question about weather, temperature, forecast, or conditions, "
                "you MUST use the 'realtime_weather_tool'\n"
                "2. Do NOT answer weather questions yourself - ALWAYS use the tool\n"
                "3. Pass the user's question directly to the tool\n"
                "4. Return the tool's response to the user\n"
                "5. For non-weather questions, answer them normally\n\n"
                "The tool has real-time data for: New York, Los Angeles, Chicago, Seattle, and Miami"
            ),
            tools=weather_tool.definitions
        )
        logger.info(f"Created orchestrator: {orchestrator_agent.id}")
        
        # Test the system
        thread = client.agents.threads.create()
        logger.info(f"Created thread: {thread.id}")
        
        test_queries = [
            "What's the weather in Chicago?",
            "Tell me about the temperature in Seattle",
            "How's the weather in New York right now?",
            "What's the forecast for Miami?",
            "Can you check the weather in London?",  # Not available
        ]
        
        for query in test_queries:
            logger.info(f"\n{'='*60}")
            logger.info(f"Query: '{query}'")
            logger.info(f"{'='*60}")
            
            # Send message
            message = client.agents.messages.create(
                thread_id=thread.id,
                role="user",
                content=query
            )
            
            # Run orchestrator
            run = client.agents.runs.create(
                thread_id=thread.id,
                body={"assistant_id": orchestrator_agent.id}
            )
            
            # Wait for completion
            max_wait = 30
            waited = 0
            while run.status in ["queued", "in_progress", "requires_action"] and waited < max_wait:
                await asyncio.sleep(1)
                waited += 1
                run = client.agents.runs.get(thread_id=thread.id, run_id=run.id)
                
                if run.status == "requires_action":
                    logger.info("🔧 Tool invocation required")
            
            # Get response
            messages = client.agents.messages.list(
                thread_id=thread.id,
                order="desc",
                limit=1
            )
            
            for msg in messages:
                if msg.role == "assistant" and msg.run_id == run.id:
                    content = msg.content[0].text.value if msg.content else "No content"
                    logger.info(f"\n📨 Response:\n{content}")
                    
                    # Check if it used real data
                    if "📍" in content and "Source: National Weather Service" in content:
                        logger.info("\n✅ Successfully used weather tool with real data!")
                    else:
                        logger.warning("\n⚠️  Response doesn't appear to use the weather tool")
                    break
        
        # Cleanup
        logger.info("\n🧹 Cleaning up...")
        client.agents.delete_agent(orchestrator_agent.id)
        client.agents.delete_agent(weather_agent.id)
        logger.info("✅ Cleanup complete")
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        
        # Cleanup on error
        try:
            if orchestrator_agent:
                client.agents.delete_agent(orchestrator_agent.id)
            if weather_agent:
                client.agents.delete_agent(weather_agent.id)
        except:
            pass


if __name__ == "__main__":
    asyncio.run(main())