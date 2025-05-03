import datetime
import json
import os
import ollama
from typing import Dict, Optional
from datetime import datetime, date

def calculate_age(dob: str) -> int:
    """Calculate age from date of birth string (YYYY-MM-DD format)"""
    birth_date = datetime.strptime(dob, "%Y-%m-%d").date()
    today = date.today()
    age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
    return age

def generate_skin_plan(
    user_profile: Dict,
    timeseries_data: Optional[Dict] = None,
    model_name: str = 'medllama2'
) -> str:
    """
    Generates a treatment plan and lifestyle advice using Ollama's model based on user profile and timeseries data.

    Args:
        user_profile: Dictionary containing user profile information from the database
        timeseries_data: Optional dictionary containing the latest timeseries data
        model_name: Name of the Ollama model to use

    Returns:
        JSON-formatted string with keys:
        - treatment_plan: list of {date: str, treatment: str}
        - lifestyle_advice: list of advice strings
        - diet_recommendations: list of diet-specific recommendations
        - sleep_recommendations: list of sleep-specific recommendations
        - environmental_factors: list of environmental factor recommendations
    """
    # Extract and process user profile data
    age = calculate_age(user_profile.get("dob", ""))
    gender = user_profile.get("gender", "")
    weight = user_profile.get("weight", 0)
    height = user_profile.get("height", 0)
    
    # Process timeseries data if available
    severity_score = timeseries_data.get("acne_severity_score", 50) if timeseries_data else 50
    diet_sugar = timeseries_data.get("diet_sugar", 0) if timeseries_data else 0
    diet_dairy = timeseries_data.get("diet_dairy", 0) if timeseries_data else 0
    diet_alcohol = timeseries_data.get("diet_alcohol", 0) if timeseries_data else 0
    sleep_hours = timeseries_data.get("sleep_hours", 0) if timeseries_data else 0
    sleep_quality = timeseries_data.get("sleep_quality", "unknown") if timeseries_data else "unknown"
    stress = timeseries_data.get("stress", 0) if timeseries_data else 0
    products_used = timeseries_data.get("products_used", "") if timeseries_data else ""
    sunlight_exposure = timeseries_data.get("sunlight_exposure", 0) if timeseries_data else 0
    
    prompt = (
        f"You are a knowledgeable medical assistant specializing in dermatology. Given the patient data below, provide a JSON response with the following structure:\n"
        f"{{\n"
        f"  \"treatment_plan\": [{{\n"
        f"    \"date\": \"YYYY-MM-DD\",\n"
        f"    \"treatment\": \"treatment description\"\n"
        f"  }}],\n"
        f"  \"lifestyle_advice\": [\"advice 1\", \"advice 2\"],\n"
        f"  \"diet_recommendations\": [\"diet rec 1\", \"diet rec 2\"],\n"
        f"  \"sleep_recommendations\": [\"sleep rec 1\", \"sleep rec 2\"],\n"
        f"  \"environmental_factors\": [\"env factor 1\", \"env factor 2\"]\n"
        f"}}\n\n"
        f"Patient Data:\n"
        f"- Age: {age}\n"
        f"- Gender: {gender}\n"
        f"- Weight (kg): {weight}\n"
        f"- Height (cm): {height}\n"
        f"- Acne Severity Score (1-100): {severity_score}\n"
        f"- Current Diet Patterns:\n"
        f"  * Sugar intake: {diet_sugar}%\n"
        f"  * Dairy intake: {diet_dairy}%\n"
        f"  * Alcohol consumption: {diet_alcohol}%\n"
        f"- Sleep Patterns:\n"
        f"  * Hours: {sleep_hours}\n"
        f"  * Quality: {sleep_quality}\n"
        f"- Stress Level (1-10): {stress}\n"
        f"- Current Products Used: {products_used}\n"
        f"- Sunlight Exposure (hours/day): {sunlight_exposure}\n\n"
        f"Provide ONLY a valid JSON response with NO additional text or explanation."
    )

    try:
        response = ollama.chat(
            model=model_name,
            messages=[
                {'role': 'system', 'content': 'You are a dermatology expert. Always respond with valid JSON only.'},
                {'role': 'user', 'content': prompt}
            ],
            options={
                'temperature': 0.7,
                'top_p': 0.9,
                'max_tokens': 1024,
                'num_ctx': 2048
            }
        )
        
        # Get the response content
        content = response['message']['content']
        
        # Try to parse it as JSON to validate
        try:
            json.loads(content)
            return content
        except json.JSONDecodeError:
            # If parsing fails, create a default response
            default_response = {
                "treatment_plan": [
                    {
                        "date": datetime.now().strftime("%Y-%m-%d"),
                        "treatment": "Basic skincare routine: gentle cleanser, moisturizer, and sunscreen"
                    }
                ],
                "lifestyle_advice": [
                    "Stay hydrated",
                    "Get adequate sleep",
                    "Manage stress levels"
                ],
                "diet_recommendations": [
                    "Reduce sugar intake",
                    "Maintain a balanced diet",
                    "Consider reducing dairy consumption"
                ],
                "sleep_recommendations": [
                    "Aim for 7-9 hours of sleep",
                    "Maintain a consistent sleep schedule"
                ],
                "environmental_factors": [
                    "Protect skin from sun exposure",
                    "Keep environment clean and dust-free"
                ]
            }
            return json.dumps(default_response, indent=2)
            
    except Exception as e:
        # If there's any error with the model, return the default response
        default_response = {
            "treatment_plan": [
                {
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "treatment": "Basic skincare routine: gentle cleanser, moisturizer, and sunscreen"
                }
            ],
            "lifestyle_advice": [
                "Stay hydrated",
                "Get adequate sleep",
                "Manage stress levels"
            ],
            "diet_recommendations": [
                "Reduce sugar intake",
                "Maintain a balanced diet",
                "Consider reducing dairy consumption"
            ],
            "sleep_recommendations": [
                "Aim for 7-9 hours of sleep",
                "Maintain a consistent sleep schedule"
            ],
            "environmental_factors": [
                "Protect skin from sun exposure",
                "Keep environment clean and dust-free"
            ]
        }
        return json.dumps(default_response, indent=2)

def generate_skin_plan_from_json(input_json: dict) -> str:
    """
    Wrapper: Parses a JSON dict containing user profile and timeseries data and generates the skin plan.
    
    Args:
        input_json: Dictionary containing:
            - user_profile: Dictionary with user profile data
            - timeseries_data: Optional dictionary with latest timeseries data
            - model_name: Optional name of the Ollama model to use
    
    Returns:
        JSON-formatted string with the generated plan
    """
    if "user_profile" not in input_json:
        raise ValueError("Missing required key 'user_profile' in input JSON")
    
    user_profile = input_json["user_profile"]
    timeseries_data = input_json.get("timeseries_data")
    model_name = input_json.get("model_name", 'medllama2')

    return generate_skin_plan(
        user_profile=user_profile,
        timeseries_data=timeseries_data,
        model_name=model_name
    )

def test_generate_skin_plan():
    """
    Test using sample JSON with user profile and timeseries data.
    """
    sample_input = {
        "user_profile": {
            "user_id": "user_1",
            "name": "John Doe",
            "dob": "1995-05-03",
            "height": 180,
            "weight": 75,
            "gender": "Male"
        },
        "timeseries_data": {
            "acne_severity_score": 75.0,
            "diet_sugar": 20.0,
            "diet_dairy": 15.0,
            "diet_alcohol": 0.0,
            "sleep_hours": 7.0,
            "sleep_quality": "good",
            "stress": 5.0,
            "products_used": "cleanser,moisturizer",
            "sunlight_exposure": 2.0
        },
        "model_name": "medllama2"
    }

    print("Input JSON:")
    print(json.dumps(sample_input, indent=2))
    print("\nGenerated Plan:")
    plan = generate_skin_plan_from_json(sample_input)
    print(plan)

if __name__ == "__main__":
    test_generate_skin_plan()