import requests
import json

def test_api_endpoint(method, url, data=None, headers=None):
    """Test an API endpoint and return the response or error."""
    try:
        if method.upper() == "POST":
            response = requests.post(url, json=data, headers=headers)
        elif method.upper() == "GET":
            response = requests.get(url, headers=headers)
        else:
            raise ValueError(f"Unsupported method: {method}")

        response.raise_for_status()  # Raise an exception for 4xx/5xx responses
        print(f"Response Status Code: {response.status_code}")
        try:
            return response.json()
        except json.JSONDecodeError:
            return response.text
    except requests.exceptions.RequestException as e:
        print(f"Request Error: {str(e)}")
        try:
            return e.response.json() if e.response is not None else {"detail": str(e)}
        except (json.JSONDecodeError, AttributeError):
            return {"detail": str(e)}

# Define the four test endpoints
test_cases = [
    # 1. Test Saving a Profile (POST /profile/)
    {
        "method": "POST",
        "url": "http://localhost:8000/profile/",
        "data": {
            "user_id": "user_3",
            "name": "Alex Smith",
            "dob": "1990-06-15",
            "height": 175,
            "weight": 70,
            "gender": "Male"
        },
        "headers": {"Content-Type": "application/json"}
    },
    
    # 2. Test Retrieving a Profile (GET /profile/{user_id})
    {
        "method": "GET",
        "url": "http://localhost:8000/profile/user_3",
        "data": None,
        "headers": None
    },
    
    # 3. Test Inserting a Time-series Entry (POST /timeseries/)
    {
        "method": "POST",
        "url": "http://localhost:8000/timeseries/",
        "data": {
            "id": "entry-001",
            "timestamp": "2025-05-03T14:30:00",
            "acne_severity_score": 80.0,
            "diet_sugar": 25.0,
            "diet_dairy": 10.0,
            "diet_alcohol": 5.0,
            "sleep_hours": 6.5,
            "sleep_quality": "poor",
            "menstrual_cycle_active": 0,
            "menstrual_cycle_day": 0,
            "latitude": 40.7128,
            "longitude": -74.0060,
            "humidity": 55.0,
            "pollution": 40.0,
            "stress": 7.0,
            "products_used": "cleanser,toner",
            "sunlight_exposure": 1.5
        },
        "headers": {"Content-Type": "application/json"}
    },
    
    # 4. Test Retrieving Time-series Data (GET /timeseries/{user_id})
    {
        "method": "GET",
        "url": "http://localhost:8000/timeseries/user_3",
        "data": None,
        "headers": None
    }
]

# Execute each test case and print results
print("Starting database function tests...\n")
for i, test_case in enumerate(test_cases, 1):
    print(f"Test {i}: {test_case['method']} {test_case['url']}")
    response = test_api_endpoint(test_case["method"], test_case["url"], test_case["data"], test_case["headers"])
    print(f"Test {i} Result: {response}\n")

print("All tests completed.")