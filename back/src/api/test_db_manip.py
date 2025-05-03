import unittest
import requests
import json
import uuid

class TestApiEndpoints(unittest.TestCase):
    def setUp(self):
        """Set up before each test."""
        self.base_url = "http://localhost:8000"
        self.unique_id = str(uuid.uuid4())  # Generate a unique ID for each test run

    def test_api_endpoint(self, method, url, data=None, headers=None, expected_status=200, expected_response=None):
        """Test an API endpoint and assert the response."""
        try:
            if method.upper() == "POST":
                response = requests.post(url, json=data, headers=headers)
            elif method.upper() == "GET":
                response = requests.get(url, headers=headers)
            else:
                raise ValueError(f"Unsupported method: {method}")

            response.raise_for_status()  # Raise an exception for 4xx/5xx responses
            self.assertEqual(response.status_code, expected_status, f"Expected status {expected_status}, got {response.status_code}")
            response_data = response.json() if response.text else None
            if expected_response is not None:
                self.assertEqual(response_data, expected_response, f"Expected response {expected_response}, got {response_data}")
            return response_data
        except requests.exceptions.RequestException as e:
            self.fail(f"Request failed: {str(e)} - Response: {e.response.json() if e.response else str(e)}")

    def test_save_profile(self):
        """Test saving a new profile (POST /profile/)."""
        url = f"{self.base_url}/profile/"
        data = {
            "user_id": "user_3",
            "name": "Alex Smith",
            "dob": "1990-06-15",
            "height": 175,
            "weight": 70,
            "gender": "Male"
        }
        headers = {"Content-Type": "application/json"}
        expected_response = {"message": "Profile saved successfully"}
        result = self.test_api_endpoint("POST", url, data, headers, expected_response=expected_response)
        self.assertIn("message", result)

    def test_get_profile(self):
        """Test retrieving a profile (GET /profile/{user_id})."""
        url = f"{self.base_url}/profile/user_3"
        expected_response = {
            "user_id": "user_3",
            "name": "Alex Smith",
            "dob": "1990-06-15",
            "height": 175.0,  # Float due to SQLite/FastAPI conversion
            "weight": 70.0,   # Float due to SQLite/FastAPI conversion
            "gender": "Male"
        }
        result = self.test_api_endpoint("GET", url, expected_response=expected_response)
        self.assertEqual(result, expected_response)

    def test_insert_timeseries(self):
        """Test inserting a new time-series entry (POST /timeseries/)."""
        url = f"{self.base_url}/timeseries/"
        data = {
            "id": self.unique_id,  # Use unique ID to avoid duplicate constraint
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
        }
        headers = {"Content-Type": "application/json"}
        expected_response = {"message": "Time-series entry inserted successfully"}
        result = self.test_api_endpoint("POST", url, data, headers, expected_response=expected_response)
        self.assertIn("message", result)

    def test_get_timeseries(self):
        """Test retrieving time-series data (GET /timeseries/{user_id})."""
        url = f"{self.base_url}/timeseries/user_3"
        # Expected response includes the newly inserted entry; exact match is challenging due to existing data
        expected_entry = {
            "id": self.unique_id,
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
        }
        result = self.test_api_endpoint("GET", url)
        self.assertIsInstance(result, dict)
        self.assertIn("entries", result)
        self.assertTrue(any(entry["id"] == self.unique_id for entry in result["entries"]),
                       f"Expected entry with id {self.unique_id} not found in {result['entries']}")

    def tearDown(self):
        """Clean up after each test."""
        pass  # No cleanup needed for external API requests

if __name__ == "__main__":
    unittest.main()