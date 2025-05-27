"""Weather agent configuration with function tool for API access."""

from azure.ai.agents.models import FunctionTool
import json

AGENT_NAME_PREFIX = "WeatherInformationAgent"

AGENT_INSTRUCTIONS = (
    "You are the 'Weather Information Specialist'! Your job is to provide accurate, real-time weather information. "
    "You have access to a function tool called 'get_weather' that fetches current weather data from the National Weather Service API.\n\n"
    "When asked about weather:\n"
    "1. Extract the location from the user's query\n"
    "2. Call the get_weather function with the city name\n"
    "3. Format the response you receive in a user-friendly way\n"
    "4. If the function returns an error, explain that the city might not be available\n\n"
    "IMPORTANT: Always use the get_weather function to fetch real-time data. Do not make up weather information.\n"
    "The function supports major US cities like: New York, Los Angeles, Chicago, Seattle, Miami, Denver, Boston, etc."
)

# Define the weather function tool
def create_weather_function_tool():
    """Create a function tool for the weather agent."""
    return FunctionTool(
        name="get_weather",
        description="Get current weather for a US city from the National Weather Service API",
        parameters={
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "The city name (e.g., 'Seattle', 'New York', 'Los Angeles')"
                }
            },
            "required": ["city"]
        }
    )

# Weather API implementation that will be called by the function tool
WEATHER_API_CODE = '''
import aiohttp
import json

# Known US cities with coordinates
KNOWN_LOCATIONS = {
    "washington dc": {"lat": 38.8951, "lon": -77.0364, "name": "Washington, DC"},
    "washington": {"lat": 38.8951, "lon": -77.0364, "name": "Washington, DC"},
    "new york": {"lat": 40.7128, "lon": -74.0060, "name": "New York, NY"},
    "los angeles": {"lat": 34.0522, "lon": -118.2437, "name": "Los Angeles, CA"},
    "chicago": {"lat": 41.8781, "lon": -87.6298, "name": "Chicago, IL"},
    "seattle": {"lat": 47.6062, "lon": -122.3321, "name": "Seattle, WA"},
    "miami": {"lat": 25.7617, "lon": -80.1918, "name": "Miami, FL"},
    "denver": {"lat": 39.7392, "lon": -104.9903, "name": "Denver, CO"},
    "boston": {"lat": 42.3601, "lon": -71.0589, "name": "Boston, MA"},
    "san francisco": {"lat": 37.7749, "lon": -122.4194, "name": "San Francisco, CA"},
    "dallas": {"lat": 32.7767, "lon": -96.7970, "name": "Dallas, TX"},
    "houston": {"lat": 29.7604, "lon": -95.3698, "name": "Houston, TX"},
    "philadelphia": {"lat": 39.9526, "lon": -75.1652, "name": "Philadelphia, PA"},
    "phoenix": {"lat": 33.4484, "lon": -112.0740, "name": "Phoenix, AZ"},
    "atlanta": {"lat": 33.7490, "lon": -84.3880, "name": "Atlanta, GA"},
    "portland": {"lat": 45.5051, "lon": -122.6750, "name": "Portland, OR"},
    "las vegas": {"lat": 36.1699, "lon": -115.1398, "name": "Las Vegas, NV"},
    "san diego": {"lat": 32.7157, "lon": -117.1611, "name": "San Diego, CA"},
}

async def get_weather(city: str) -> str:
    """Fetch weather data from api.weather.gov for a given city."""
    try:
        # Normalize location input
        location_key = city.lower().strip()
        location_data = None
        
        # Check if location matches any known location
        for key, data in KNOWN_LOCATIONS.items():
            if key in location_key or location_key in key:
                location_data = data
                break
        
        if not location_data:
            return f"Sorry, I can only provide weather for major US cities. '{city}' is not in my database."
        
        async with aiohttp.ClientSession() as session:
            # Get the forecast office and grid coordinates
            points_url = f"https://api.weather.gov/points/{location_data['lat']},{location_data['lon']}"
            
            async with session.get(points_url, headers={"User-Agent": "StratOS Weather Agent"}) as response:
                if response.status != 200:
                    return f"Unable to fetch weather data for {location_data['name']}."
                
                points_data = await response.json()
                forecast_url = points_data['properties']['forecast']
                
            # Get the forecast
            async with session.get(forecast_url, headers={"User-Agent": "StratOS Weather Agent"}) as response:
                if response.status != 200:
                    return f"Unable to fetch forecast for {location_data['name']}."
                
                forecast_data = await response.json()
                periods = forecast_data['properties']['periods']
                
                if periods:
                    current = periods[0]
                    next_period = periods[1] if len(periods) > 1 else None
                    
                    weather_info = f"📍 Weather for {location_data['name']}:\\n"
                    weather_info += f"🌡️ Current: {current['temperature']}°{current['temperatureUnit']}\\n"
                    weather_info += f"☁️ Conditions: {current['shortForecast']}\\n"
                    weather_info += f"💨 Wind: {current['windSpeed']} {current['windDirection']}\\n"
                    weather_info += f"📊 {current['name']}: {current['detailedForecast']}\\n"
                    
                    if next_period:
                        weather_info += f"\\n🔮 {next_period['name']}: {next_period['shortForecast']}, {next_period['temperature']}°{next_period['temperatureUnit']}"
                    
                    weather_info += "\\n\\nSource: National Weather Service (api.weather.gov)"
                    return weather_info
                else:
                    return f"No forecast data available for {location_data['name']}."
                    
    except Exception as e:
        return f"Error fetching weather information: {str(e)}"
'''