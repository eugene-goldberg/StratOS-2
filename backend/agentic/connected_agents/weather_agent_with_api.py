"""Weather agent configuration with real API integration."""

import json
import aiohttp
import asyncio
from typing import Dict, Tuple, Optional

AGENT_NAME_PREFIX = "WeatherInformationAgent"

# Common US cities with coordinates (from weather_service.py)
COMMON_CITIES = {
    "seattle": (47.6062, -122.3321),
    "new york": (40.7128, -74.0060),
    "chicago": (41.8781, -87.6298),
    "los angeles": (34.0522, -118.2437),
    "san francisco": (37.7749, -122.4194),
    "miami": (25.7617, -80.1918),
    "dallas": (32.7767, -96.7970),
    "denver": (39.7392, -104.9903),
    "boston": (42.3601, -71.0589),
    "austin": (30.2672, -97.7431),
    "washington": (38.9072, -77.0369),
    "washington dc": (38.9072, -77.0369),
    "houston": (29.7604, -95.3698),
    "philadelphia": (39.9526, -75.1652),
    "phoenix": (33.4484, -112.0740),
    "atlanta": (33.7490, -84.3880),
    "portland": (45.5051, -122.6750),
    "las vegas": (36.1699, -115.1398),
    "san diego": (32.7157, -117.1611),
    "minneapolis": (44.9778, -93.2650),
    "detroit": (42.3314, -83.0458),
    "nashville": (36.1627, -86.7816),
    "baltimore": (39.2904, -76.6122),
    "charlotte": (35.2271, -80.8431),
    "raleigh": (35.7796, -78.6382),
    "cleveland": (41.4993, -81.6944),
    "pittsburgh": (40.4406, -79.9959)
}

class WeatherAPITool:
    """Tool for fetching real weather data from api.weather.gov"""
    
    def __init__(self):
        self.base_url = "https://api.weather.gov"
        self.headers = {
            "User-Agent": "StratOS Weather Agent (contact@stratos.ai)",
            "Accept": "application/geo+json"
        }
    
    async def get_weather(self, city: str) -> str:
        """Get weather for a city using the National Weather Service API."""
        try:
            # Get coordinates
            lat, lon = self._get_coordinates(city)
            if not lat or not lon:
                return f"Sorry, I couldn't find weather data for {city}. Please try a major US city."
            
            async with aiohttp.ClientSession() as session:
                # Get forecast URL
                points_url = f"{self.base_url}/points/{lat},{lon}"
                async with session.get(points_url, headers=self.headers) as response:
                    if response.status != 200:
                        return f"Unable to fetch weather data for {city}."
                    
                    data = await response.json()
                    forecast_url = data["properties"]["forecast"]
                
                # Get forecast data
                async with session.get(forecast_url, headers=self.headers) as response:
                    if response.status != 200:
                        return f"Unable to fetch forecast for {city}."
                    
                    forecast_data = await response.json()
                    periods = forecast_data["properties"]["periods"]
                    
                    if periods:
                        current = periods[0]
                        next_period = periods[1] if len(periods) > 1 else None
                        
                        weather_info = f"📍 Weather for {city.title()}:\n"
                        weather_info += f"🌡️ Current: {current['temperature']}°{current['temperatureUnit']}\n"
                        weather_info += f"☁️ Conditions: {current['shortForecast']}\n"
                        weather_info += f"💨 Wind: {current['windSpeed']} {current['windDirection']}\n"
                        weather_info += f"📊 {current['name']}: {current['detailedForecast']}\n"
                        
                        if next_period:
                            weather_info += f"\n🔮 {next_period['name']}: {next_period['shortForecast']}, {next_period['temperature']}°{next_period['temperatureUnit']}"
                        
                        weather_info += "\n\nSource: National Weather Service (api.weather.gov)"
                        return weather_info
                    else:
                        return f"No forecast data available for {city}."
                        
        except Exception as e:
            return f"Error fetching weather: {str(e)}"
    
    def _get_coordinates(self, city: str) -> Tuple[Optional[float], Optional[float]]:
        """Get coordinates for a city."""
        city_lower = city.lower().strip()
        
        # Check common cities
        for key, coords in COMMON_CITIES.items():
            if key in city_lower or city_lower in key:
                return coords
        
        # If not found, return None
        return None, None

# Create a global weather tool instance
weather_tool = WeatherAPITool()

# Function to generate agent instructions with current weather data
async def generate_agent_instructions():
    """Generate agent instructions with sample weather data."""
    # Fetch sample weather for a few cities
    sample_cities = ["New York", "Los Angeles", "Chicago"]
    weather_samples = []
    
    for city in sample_cities:
        try:
            weather = await weather_tool.get_weather(city)
            weather_samples.append(f"\nExample for {city}:\n{weather}")
        except:
            pass
    
    base_instructions = (
        "You are the 'Weather Information Specialist'! Your job is to provide accurate, real-time weather information. "
        "You have access to the National Weather Service API for US cities.\n\n"
        "When asked about weather:\n"
        "1. Extract the location from the user's query\n"
        "2. Use your weather tool to fetch real-time data\n"
        "3. Format the response clearly with emojis\n"
        "4. Always mention the data source (National Weather Service)\n"
        "5. If the city isn't available, suggest major US cities\n\n"
        "Available cities include: New York, Los Angeles, Chicago, Seattle, Miami, Denver, Boston, "
        "San Francisco, Dallas, Houston, Atlanta, Phoenix, Portland, Las Vegas, and many more major US cities.\n\n"
        "IMPORTANT: You must use the weather tool to get current data. Do not make up weather information.\n"
    )
    
    if weather_samples:
        base_instructions += "\nHere are some current examples:\n" + "\n".join(weather_samples)
    
    return base_instructions

# For backward compatibility with existing code
AGENT_INSTRUCTIONS = (
    "You are the 'Weather Information Specialist'! Your job is to provide accurate weather information. "
    "You have access to real-time weather data from the National Weather Service API.\n\n"
    "When asked about weather:\n"
    "1. Extract the location from the user's query\n"
    "2. Fetch real-time weather data for US cities\n"
    "3. Format the response clearly with emojis\n"
    "4. Always mention the data source (National Weather Service)\n"
    "5. If the city isn't available, explain you only have data for major US cities\n\n"
    "Available cities include major US cities like: New York, Los Angeles, Chicago, Seattle, Miami, "
    "Denver, Boston, San Francisco, Dallas, Houston, Atlanta, Phoenix, Portland, Las Vegas, and more.\n\n"
    "Use the exact format:\n"
    "📍 Weather for [City]:\n"
    "🌡️ Current: [temp]°F\n"
    "☁️ Conditions: [description]\n"
    "💨 Wind: [speed and direction]\n"
    "📊 [Period]: [detailed forecast]\n"
    "🔮 [Next period]: [next forecast]\n"
    "Source: National Weather Service (api.weather.gov)"
)