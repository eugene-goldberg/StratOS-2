#!/usr/bin/env python3
"""
Test weather plugin locally to verify it works.
"""

import json
from weather_plugin import WeatherPlugin

def test_weather_plugin():
    """Test the weather plugin functions."""
    
    plugin = WeatherPlugin()
    
    print("Testing WeatherPlugin locally...")
    print("="*60)
    
    # Test 1: Get weather for Seattle
    print("\nTest 1: Get weather for Seattle")
    result = plugin.get_weather("Seattle")
    data = json.loads(result)
    print(f"Success: {data.get('success')}")
    if data.get('success'):
        print(f"Temperature: {data['temperature_f']}°F ({data['temperature_c']}°C)")
        print(f"Conditions: {data['conditions']}")
        print(f"Wind: {data['wind']}")
    else:
        print(f"Error: {data.get('error')}")
    
    # Test 2: Get weather for New York
    print("\n" + "="*60)
    print("Test 2: Get weather for New York")
    result = plugin.get_weather("New York")
    data = json.loads(result)
    print(f"Success: {data.get('success')}")
    if data.get('success'):
        print(f"Temperature: {data['temperature_f']}°F ({data['temperature_c']}°C)")
        print(f"Conditions: {data['conditions']}")
    
    # Test 3: Compare weather
    print("\n" + "="*60)
    print("Test 3: Compare Seattle and Miami weather")
    result = plugin.compare_weather("Seattle", "Miami")
    data = json.loads(result)
    if data.get('success'):
        comp = data['comparison']
        print(f"{comp['city1']['name']}: {comp['city1']['temperature_f']}°F {comp['city1']['emoji']}")
        print(f"{comp['city2']['name']}: {comp['city2']['temperature_f']}°F {comp['city2']['emoji']}")
        print(f"Temperature difference: {comp['temperature_difference_f']}°F")
        print(f"Warmer city: {comp['warmer_city']}")
    
    # Test 4: Invalid city
    print("\n" + "="*60)
    print("Test 4: Invalid city")
    result = plugin.get_weather("London")
    data = json.loads(result)
    print(f"Success: {data.get('success')}")
    print(f"Error: {data.get('error')}")

if __name__ == "__main__":
    test_weather_plugin()