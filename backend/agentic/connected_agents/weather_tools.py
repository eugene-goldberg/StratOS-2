"""Weather function tools for the weather agent."""

from azure.ai.agents.models import FunctionTool
from typing import Annotated

async def get_weather(city: Annotated[str, "The US city name (e.g., 'Seattle', 'New York', 'Miami')"]) -> str:
    """Get current weather information for a US city from the National Weather Service API.
    
    This is a placeholder function. In a real implementation, this would:
    1. Make an API call to api.weather.gov
    2. Parse the weather data
    3. Return formatted weather information
    
    For now, it returns a message indicating the function was called.
    """
    return f"[Weather function called for {city}. Real implementation would fetch from api.weather.gov]"

def create_get_weather_tool():
    """Create a function tool for fetching weather data."""
    # FunctionTool expects a set of callable functions
    return FunctionTool(functions={get_weather})