#!/usr/bin/env python3
"""Test SaveCEOLog with local analysis (no AI)"""

import requests
import json

# SaveCEOLog function URL
SAVE_URL = "https://stratos-ceo-log-functions.azurewebsites.net/api/saveceolog?code=I3c897PZMtJp1goBaxPwGlXa3Ni6ZsM09t1F7roTLVZeAzFu69TeKA=="
SEARCH_URL = "https://stratos-ceo-log-functions.azurewebsites.net/api/searchceologs?code=uXjWD5crSSJYH_7eL3IcQq_ebEqVqO9D2QaC24UKa_RNAzFuVD7gkg=="

def test_save_without_ai():
    """Test saving without AI analysis"""
    
    # First, let's test with a simple payload that should trigger local analysis
    payload = {
        "userId": "test-ceo-001",
        "content": "We achieved great success with our strategic plan. The team showed excellent performance and we identified new opportunities for growth. This is an urgent priority.",
        "category": "strategic_planning",
        "tags": ["test", "integration"],
        "metadata": {
            "source": "test",
            "device": "test-device",
            "isVoice": False
        }
    }
    
    print("=== Testing SaveCEOLog (should use local analysis) ===")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(SAVE_URL, json=payload, timeout=30)
        print(f"\nStatus Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 201:
            print("\n✅ Success! Entry saved.")
            entry_id = response.json().get('entryId')
            
            # Now search for it
            print("\n=== Searching for the saved entry ===")
            search_payload = {
                "userId": "test-ceo-001",
                "query": "strategic success"
            }
            
            search_response = requests.post(SEARCH_URL, json=search_payload, timeout=30)
            print(f"Search Status: {search_response.status_code}")
            print(f"Search Results: {json.dumps(search_response.json(), indent=2)}")
            
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    test_save_without_ai()