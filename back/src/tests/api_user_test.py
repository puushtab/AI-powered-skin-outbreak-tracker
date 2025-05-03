import requests
import json
from typing import Dict, Any
from datetime import datetime

def add_user(user_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Add a new user to the database via the API.
    
    Args:
        user_data: Dictionary containing user information
            {
                "user_id": str,
                "name": str,
                "dob": str (YYYY-MM-DD),
                "height": int,
                "weight": int,
                "gender": str
            }
    
    Returns:
        Dictionary containing the API response
    """
    base_url = 'http://localhost:8000/api/v1'
    endpoint = f"{base_url}/profile"
    
    try:
        response = requests.post(endpoint, json=user_data)
        return {
            "status_code": response.status_code,
            "response": response.json() if response.status_code == 200 else response.text
        }
    except requests.exceptions.RequestException as e:
        return {
            "status_code": 500,
            "response": f"Error making request: {str(e)}"
        }

def test_add_user():
    """Test adding a new user to the database"""
    # Test case 1: Valid user data
    print("\nTest Case 1: Adding valid user")
    test_user_1 = {
        "user_id": "test_user_1",
        "name": "Test User One",
        "dob": "1995-05-03",
        "height": 175,
        "weight": 70,
        "gender": "Male"
    }
    
    result = add_user(test_user_1)
    print(f"Status Code: {result['status_code']}")
    print(f"Response: {json.dumps(result['response'], indent=2)}")
    
    # Test case 2: Invalid date format
    print("\nTest Case 2: Invalid date format")
    test_user_2 = {
        "user_id": "test_user_2",
        "name": "Test User Two",
        "dob": "03-05-1995",  # Wrong format
        "height": 165,
        "weight": 60,
        "gender": "Female"
    }
    
    result = add_user(test_user_2)
    print(f"Status Code: {result['status_code']}")
    print(f"Response: {json.dumps(result['response'], indent=2)}")
    
    # Test case 3: Missing required field
    print("\nTest Case 3: Missing required field")
    test_user_3 = {
        "user_id": "test_user_3",
        "name": "Test User Three",
        "dob": "1995-05-03",
        "height": 180,
        # Missing weight
        "gender": "Male"
    }
    
    result = add_user(test_user_3)
    print(f"Status Code: {result['status_code']}")
    print(f"Response: {json.dumps(result['response'], indent=2)}")

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
    print("Starting user management tests...")
    
    # First check if API is running
    if check_api_health():
        # Run the user management tests
        test_add_user()
    else:
        print("Cannot run tests: API is not accessible") 