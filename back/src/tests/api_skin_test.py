import requests
import json
from typing import Dict, Any
from datetime import datetime

def test_skin_plan_generation():
    """Test the skin plan generation API endpoint"""
    base_url = 'http://localhost:8000/api/v1'
    endpoint = f"{base_url}/skin-plan/generate"
    
    # Test case 1: Valid request with test user
    print("\nTest Case 1: Valid request with test user")
    params_1 = {
        "user_id": "test_user_1",  # Using the user we just added
        "model_name": "medllama2"
    }
    
    try:
        response = requests.post(endpoint, params=params_1)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except requests.exceptions.RequestException as e:
        print(f"Error in test case 1: {str(e)}")
    
    # Test case 2: Test with different model
    print("\nTest Case 2: Test with different model")
    params_2 = {
        "user_id": "test_user_1",
        "model_name": "llama2"  # Try a different model
    }
    
    try:
        response = requests.post(endpoint, params=params_2)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except requests.exceptions.RequestException as e:
        print(f"Error in test case 2: {str(e)}")
    
    # Test case 3: Test with non-existent user
    print("\nTest Case 3: Test with non-existent user")
    params_3 = {
        "user_id": "non_existent_user",
        "model_name": "medllama2"
    }
    
    try:
        response = requests.post(endpoint, params=params_3)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except requests.exceptions.RequestException as e:
        print(f"Error in test case 3: {str(e)}")

def check_api_health():
    """Check if the API is running and accessible"""
    base_url = 'http://localhost:8000'
    try:
        response = requests.get(base_url)
        if response.status_code == 200:
            print("\nAPI is running and accessible")
            return True
        else:
            print(f"\nAPI returned status code: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"\nAPI is not accessible: {str(e)}")
        return False

if __name__ == "__main__":
    print("Starting skin plan generation tests...")
    
    # First check if API is running
    if check_api_health():
        # Run the skin plan generation tests
        test_skin_plan_generation()
    else:
        print("Cannot run tests: API is not accessible")
