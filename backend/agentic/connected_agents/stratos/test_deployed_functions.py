#!/usr/bin/env python3
"""Test the deployed Azure Functions for CEO Log integration"""

import requests
import json
from datetime import datetime, timedelta

# Function URLs and keys
BASE_URL = "https://stratos-ceo-log-functions.azurewebsites.net/api"
FUNCTION_KEYS = {
    "SaveCEOLog": "I3c897PZMtJp1goBaxPwGlXa3Ni6ZsM09t1F7roTLVZeAzFu69TeKA==",
    "SearchCEOLogs": "uXjWD5crSSJYH_7eL3IcQq_ebEqVqO9D2QaC24UKa_RNAzFuVD7gkg==",
    "AnalyzeLogs": "1ALdM_XHFGwQ5XtC5BBsnJ-_j_w30lef9DsjGWVrpNJfAzFuEHzbmg==",
    "GetInsights": "Rx3WeFi1SoWXpbiZtsOCBVyswP06bUskqSYKK5HdntHBAzFuqJ56aw=="
}

def test_save_ceo_log():
    """Test saving a CEO log entry"""
    print("\n=== Testing SaveCEOLog Function ===")
    
    url = f"{BASE_URL}/saveceolog?code={FUNCTION_KEYS['SaveCEOLog']}"
    payload = {
        "userId": "test-ceo-001",
        "content": "The team has shown remarkable resilience during the product launch. We need to recognize their efforts and plan for scaling our success.",
        "category": "team_leadership",
        "tags": [],
        "metadata": {
            "source": "test",
            "device": "test-device",
            "isVoice": False
        }
    }
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.json() if response.status_code == 200 else None
    except Exception as e:
        print(f"Error: {str(e)}")
        return None

def test_search_logs():
    """Test searching CEO logs"""
    print("\n=== Testing SearchCEOLogs Function ===")
    
    url = f"{BASE_URL}/searchceologs?code={FUNCTION_KEYS['SearchCEOLogs']}"
    payload = {
        "userId": "test-ceo-001",
        "query": "team resilience",
        "category": "team_leadership"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.json() if response.status_code == 200 else None
    except Exception as e:
        print(f"Error: {str(e)}")
        return None

def test_analyze_logs():
    """Test analyzing CEO logs"""
    print("\n=== Testing AnalyzeLogs Function ===")
    
    url = f"{BASE_URL}/analyzelogs?code={FUNCTION_KEYS['AnalyzeLogs']}"
    payload = {
        "userId": "test-ceo-001",
        "focusArea": "team",
        "timeframe": "week"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.json() if response.status_code == 200 else None
    except Exception as e:
        print(f"Error: {str(e)}")
        return None

def test_get_insights():
    """Test getting insights"""
    print("\n=== Testing GetInsights Function ===")
    
    url = f"{BASE_URL}/getinsights?code={FUNCTION_KEYS['GetInsights']}&userId=test-ceo-001"
    
    try:
        response = requests.get(url, timeout=30)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.json() if response.status_code == 200 else None
    except Exception as e:
        print(f"Error: {str(e)}")
        return None

def main():
    """Run all tests"""
    print("Starting Azure Functions CEO Log Integration Tests")
    print("=" * 50)
    
    # Test 1: Save a log entry
    saved = test_save_ceo_log()
    
    # Test 2: Search for logs
    test_search_logs()
    
    # Test 3: Analyze logs
    test_analyze_logs()
    
    # Test 4: Get insights
    test_get_insights()
    
    print("\n" + "=" * 50)
    print("Tests completed!")

if __name__ == "__main__":
    main()