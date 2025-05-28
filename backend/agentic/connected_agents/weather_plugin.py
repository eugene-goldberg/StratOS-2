"""
Weather Plugin for Connected Agents
Provides real-time weather information using weather.gov API
"""

import json
import urllib.request
from typing import Optional, Dict, Any
from datetime import datetime
from semantic_kernel.functions import kernel_function
from semantic_kernel.kernel_pydantic import KernelBaseModel


class WeatherPlugin(KernelBaseModel):
    """Plugin that provides weather functionality using weather.gov API."""
    
    cities: Dict[str, Dict[str, Any]] = {
            "new york": {"lat": 40.7128, "lon": -74.0060, "state": "NY"},
            "los angeles": {"lat": 34.0522, "lon": -118.2437, "state": "CA"},
            "chicago": {"lat": 41.8781, "lon": -87.6298, "state": "IL"},
            "houston": {"lat": 29.7604, "lon": -95.3698, "state": "TX"},
            "phoenix": {"lat": 33.4484, "lon": -112.0740, "state": "AZ"},
            "seattle": {"lat": 47.6062, "lon": -122.3321, "state": "WA"},
            "san francisco": {"lat": 37.7749, "lon": -122.4194, "state": "CA"},
            "boston": {"lat": 42.3601, "lon": -71.0589, "state": "MA"},
            "miami": {"lat": 25.7617, "lon": -80.1918, "state": "FL"},
            "denver": {"lat": 39.7392, "lon": -104.9903, "state": "CO"}
    }
    
    @kernel_function(
        description="Get current weather for a US city",
        name="GetWeather"
    )
    def get_weather(self, city: str) -> str:
        """
        Get current weather conditions for a US city using weather.gov API.
        
        Args:
            city (str): The city name (e.g., "Seattle", "New York")
            
        Returns:
            str: JSON string with weather information
        """
        city_key = city.lower().strip()
        
        # Check if city is in our database
        if city_key not in self.cities:
            return json.dumps({
                "error": f"City '{city}' not found. Available cities: {', '.join(self.cities.keys())}",
                "success": False
            }, indent=2)
        
        city_info = self.cities[city_key]
        lat = city_info["lat"]
        lon = city_info["lon"]
        state = city_info["state"]
        
        try:
            # Get grid point data from weather.gov
            url = f"https://api.weather.gov/points/{lat},{lon}"
            req = urllib.request.Request(url, headers={'User-Agent': 'StratOS-WeatherBot/1.0'})
            
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())
            
            # Get forecast URL
            forecast_url = data['properties']['forecast']
            
            # Get forecast data
            req2 = urllib.request.Request(forecast_url, headers={'User-Agent': 'StratOS-WeatherBot/1.0'})
            with urllib.request.urlopen(req2, timeout=10) as response2:
                forecast = json.loads(response2.read().decode())
            
            # Current conditions (first period)
            current = forecast['properties']['periods'][0]
            
            # Convert temperature to Celsius
            temp_f = current['temperature']
            temp_c = round((temp_f - 32) * 5/9, 1)
            
            # Determine weather emoji
            conditions_lower = current['shortForecast'].lower()
            if 'sunny' in conditions_lower or 'clear' in conditions_lower:
                emoji = "☀️"
            elif 'rain' in conditions_lower:
                emoji = "🌧️"
            elif 'snow' in conditions_lower:
                emoji = "❄️"
            elif 'storm' in conditions_lower:
                emoji = "⛈️"
            elif 'cloud' in conditions_lower:
                emoji = "☁️"
            else:
                emoji = "🌤️"
            
            return json.dumps({
                "success": True,
                "city": city.title(),
                "state": state,
                "temperature_f": temp_f,
                "temperature_c": temp_c,
                "conditions": current['shortForecast'],
                "wind": f"{current['windSpeed']} {current['windDirection']}",
                "detailed_forecast": current['detailedForecast'],
                "emoji": emoji,
                "period": current['name'],
                "is_daytime": current['isDaytime'],
                "timestamp": datetime.now().isoformat()
            }, indent=2)
            
        except Exception as e:
            # Provide fallback weather data
            return json.dumps({
                "success": False,
                "error": str(e),
                "city": city.title(),
                "state": state,
                "fallback_data": True,
                "temperature_f": 72,
                "temperature_c": 22,
                "conditions": "Partly Cloudy",
                "wind": "10 mph W",
                "detailed_forecast": "Typical weather conditions for this time of year.",
                "emoji": "🌤️",
                "timestamp": datetime.now().isoformat()
            }, indent=2)
    
    @kernel_function(
        description="Get weather forecast for multiple days",
        name="GetForecast"
    )
    def get_forecast(self, city: str, days: Optional[int] = 3) -> str:
        """
        Get weather forecast for a US city.
        
        Args:
            city (str): The city name
            days (int): Number of days to forecast (max 7)
            
        Returns:
            str: JSON string with forecast information
        """
        city_key = city.lower().strip()
        
        if city_key not in self.cities:
            return json.dumps({
                "error": f"City '{city}' not found",
                "success": False
            }, indent=2)
        
        city_info = self.cities[city_key]
        lat = city_info["lat"]
        lon = city_info["lon"]
        
        try:
            # Get grid point data
            url = f"https://api.weather.gov/points/{lat},{lon}"
            req = urllib.request.Request(url, headers={'User-Agent': 'StratOS-WeatherBot/1.0'})
            
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())
            
            # Get forecast URL
            forecast_url = data['properties']['forecast']
            
            # Get forecast data
            req2 = urllib.request.Request(forecast_url, headers={'User-Agent': 'StratOS-WeatherBot/1.0'})
            with urllib.request.urlopen(req2, timeout=10) as response2:
                forecast = json.loads(response2.read().decode())
            
            # Get requested number of periods
            periods = forecast['properties']['periods'][:min(days * 2, 14)]  # 2 periods per day
            
            forecast_data = []
            for period in periods:
                forecast_data.append({
                    "period": period['name'],
                    "temperature": period['temperature'],
                    "temperature_unit": period['temperatureUnit'],
                    "conditions": period['shortForecast'],
                    "wind": f"{period['windSpeed']} {period['windDirection']}",
                    "is_daytime": period['isDaytime']
                })
            
            return json.dumps({
                "success": True,
                "city": city.title(),
                "state": city_info["state"],
                "forecast_days": days,
                "periods": forecast_data,
                "timestamp": datetime.now().isoformat()
            }, indent=2)
            
        except Exception as e:
            return json.dumps({
                "success": False,
                "error": str(e),
                "city": city.title(),
                "message": "Unable to fetch forecast data"
            }, indent=2)
    
    @kernel_function(
        description="Compare weather between two cities",
        name="CompareWeather"
    )
    def compare_weather(self, city1: str, city2: str) -> str:
        """
        Compare current weather between two US cities.
        
        Args:
            city1 (str): First city name
            city2 (str): Second city name
            
        Returns:
            str: JSON string with weather comparison
        """
        # Get weather for both cities
        weather1_json = self.get_weather(city1)
        weather2_json = self.get_weather(city2)
        
        weather1 = json.loads(weather1_json)
        weather2 = json.loads(weather2_json)
        
        if not weather1.get("success") or not weather2.get("success"):
            return json.dumps({
                "success": False,
                "error": "Failed to get weather for one or both cities"
            }, indent=2)
        
        # Calculate differences
        temp_diff_f = abs(weather1["temperature_f"] - weather2["temperature_f"])
        temp_diff_c = abs(weather1["temperature_c"] - weather2["temperature_c"])
        
        # Determine which is warmer
        warmer_city = city1 if weather1["temperature_f"] > weather2["temperature_f"] else city2
        
        return json.dumps({
            "success": True,
            "comparison": {
                "city1": {
                    "name": weather1["city"],
                    "temperature_f": weather1["temperature_f"],
                    "temperature_c": weather1["temperature_c"],
                    "conditions": weather1["conditions"],
                    "emoji": weather1["emoji"]
                },
                "city2": {
                    "name": weather2["city"],
                    "temperature_f": weather2["temperature_f"],
                    "temperature_c": weather2["temperature_c"],
                    "conditions": weather2["conditions"],
                    "emoji": weather2["emoji"]
                },
                "temperature_difference_f": temp_diff_f,
                "temperature_difference_c": temp_diff_c,
                "warmer_city": warmer_city.title()
            },
            "timestamp": datetime.now().isoformat()
        }, indent=2)