import datetime
import json
import os
import ollama
from typing import Dict, Optional
from datetime import datetime, date
import requests
import psutil
import gc

def limit_memory_usage(max_memory_percent=70):
    """
    Limit memory usage by forcing garbage collection and monitoring system memory.
    
    Args:
        max_memory_percent: Maximum allowed memory usage percentage
    """
    # Force garbage collection
    gc.collect()
    
    # Get current memory usage
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    memory_percent = process.memory_percent()
    
    # If memory usage is too high, force garbage collection and wait
    if memory_percent > max_memory_percent:
        gc.collect()
        import time
        time.sleep(2)  # Increased wait time from 1 to 2 seconds
        
        # If still high, try to free more memory
        if process.memory_percent() > max_memory_percent:
            gc.collect()
            time.sleep(2)

def calculate_age(dob: str) -> int:
    """Calculate age from date of birth string (YYYY-MM-DD format)"""
    birth_date = datetime.strptime(dob, "%Y-%m-%d").date()
    today = date.today()
    age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
    return age

def check_system_memory():
    """
    Check if system has enough memory to run the model.
    Returns True if enough memory is available, False otherwise.
    """
    # Get system memory info
    memory = psutil.virtual_memory()
    available_gb = memory.available / (1024 * 1024 * 1024)  # Convert to GB
    
    # We need at least 11.3 GB for the model
    required_gb = 11.3
    
    if available_gb < required_gb:
        print(f"Warning: Only {available_gb:.1f}GB available, but {required_gb}GB required")
        return False
    return True

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
        - product_recommendations: list of product recommendations with:
            - skin_condition: str
            - skin_type: str
            - characteristics: list of str
            - price_range: str
            - constitution: list of str
            - product_type: str
    """
    # Check system memory before proceeding
    if not check_system_memory():
        raise MemoryError("Insufficient system memory to run the model")
    
    # Monitor memory usage before processing
    limit_memory_usage()
    
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
        f"  \"treatment_plan\": {{\n"
        f"    \"date\": \"YYYY-MM-DD\",\n"
        f"    \"morning_routine\": [\"step 1\", \"step 2\"],\n"
        f"    \"evening_routine\": [\"step 1\", \"step 2\"],\n"
        f"    \"notes\": \"Additional instructions or warnings\"\n"
        f"  }},\n"
        f"  \"lifestyle_advice\": [\"advice 1\", \"advice 2\"],\n"
        f"  \"diet_recommendations\": [\"diet rec 1\", \"diet rec 2\"],\n"
        f"  \"sleep_recommendations\": [\"sleep rec 1\", \"sleep rec 2\"],\n"
        f"  \"environmental_factors\": [\"env factor 1\", \"env factor 2\"],\n"
        f"  \"product_recommendations\": [{{\n"
        f"    \"skin_condition\": \"acne/rosacea/dryness/etc\",\n"
        f"    \"skin_type\": \"oily/dry/combination/sensitive\",\n"
        f"    \"characteristics\": [\"non-comedogenic\", \"fragrance-free\", etc],\n"
        f"    \"price_range\": \"budget/mid-range/premium\",\n"
        f"    \"constitution\": [\"oil-free\", \"alcohol-free\", etc],\n"
        f"    \"product_type\": \"cleanser/moisturizer/serum/etc\"\n"
        f"  }}]\n"
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
        f"Provide a single day's treatment plan with specific morning and evening routines. "
        f"Make sure to include any warnings or special instructions in the notes field. "
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
                'num_ctx': 2048,
                'num_thread': 2,
                'num_batch': 1,
                'num_gpu': 0,
                'num_keep': 0,
                'num_predict': 1024,
                'repeat_penalty': 1.0,
                'stop': [],
                'num_parallel': 1,
                'num_ctx_keep': 0,
                'num_ctx_keep_ratio': 0.0
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
            today = datetime.now()
            default_response = {
                "treatment_plan": {
                    "date": today.strftime("%Y-%m-%d"),
                    "morning_routine": [
                        "Gentle cleanser",
                        "Moisturizer",
                        "Sunscreen SPF 30+"
                    ],
                    "evening_routine": [
                        "Gentle cleanser",
                        "Moisturizer",
                        "Prescribed treatment (if any)"
                    ],
                    "notes": "Be consistent with the routine and avoid touching your face"
                },
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
                ],
                "product_recommendations": [
                    {
                        "skin_condition": "acne",
                        "skin_type": "combination",
                        "characteristics": ["non-comedogenic", "fragrance-free"],
                        "price_range": "mid-range",
                        "constitution": ["oil-free", "alcohol-free"],
                        "product_type": "cleanser"
                    }
                ]
            }
            return json.dumps(default_response, indent=2)
            
    except Exception as e:
        # If there's any error with the model, return the default response
        today = datetime.now()
        default_response = {
            "treatment_plan": {
                "date": today.strftime("%Y-%m-%d"),
                "morning_routine": [
                    "Gentle cleanser",
                    "Moisturizer",
                    "Sunscreen SPF 30+"
                ],
                "evening_routine": [
                    "Gentle cleanser",
                    "Moisturizer",
                    "Prescribed treatment (if any)"
                ],
                "notes": "Be consistent with the routine and avoid touching your face"
            },
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
            ],
            "product_recommendations": [
                {
                    "skin_condition": "acne",
                    "skin_type": "combination",
                    "characteristics": ["non-comedogenic", "fragrance-free"],
                    "price_range": "mid-range",
                    "constitution": ["oil-free", "alcohol-free"],
                    "product_type": "cleanser"
                }
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

def build_search_query(product_recommendation: Dict) -> str:
    """
    Builds a search query string from product recommendation data.
    
    Args:
        product_recommendation: Dictionary containing:
            - skin_condition: str
            - skin_type: str
            - characteristics: list of str
            - price_range: str
            - constitution: list of str
            - product_type: str
            
    Returns:
        Formatted search query string
    """
    characteristics = " ".join(product_recommendation["characteristics"])
    constitution = " ".join(product_recommendation["constitution"])
    
    return f"{product_recommendation['product_type']} for {product_recommendation['skin_condition']} for {product_recommendation['skin_type']} skin under {product_recommendation['price_range']} with {constitution} {characteristics}"

def search_products_google(query, api_key, num_results=5):
    params = {
        "engine": "google_shopping",
        "q": query,
        "api_key": api_key,
        "hl": "en",
        "gl": "us"
    }
    response = requests.get("https://serpapi.com/search", params=params)
    results = response.json()
    # print(json.dumps(results.get("shopping_results", []), indent=2))

    products = []
    for item in results.get("shopping_results", [])[:num_results]:
        products.append({
            "title": item.get("title"),
            "price": item.get("price"),
            "link": item.get("product_link"),
            "source": item.get("source"),
            "thumbnail": item.get("thumbnail")
        })
    return products

if __name__ == "__main__":
    test_generate_skin_plan()

        # Test the product search
    print("\n--- Testing search_products_google ---")
    # Example: build a query for a cleanser for acne-prone combination skin
    example_product_rec = {
        "skin_condition": "acne",
        "skin_type": "combination",
        "characteristics": ["non-comedogenic", "fragrance-free"],
        "price_range": "mid-range",
        "constitution": ["oil-free", "alcohol-free"],
        "product_type": "cleanser"
    }
    search_query = build_search_query(example_product_rec)
    print(f"Search query: {search_query}")

    # Replace with your actual SerpAPI key
    serpapi_key = os.environ.get("SERPAPI_KEY")
    if not serpapi_key:
        raise ValueError("Please set the SERPAPI_KEY environment variable.")
    products = search_products_google(search_query, serpapi_key, num_results=3)
    print("Top products found:")
    for idx, product in enumerate(products, 1):
        print(f"{idx}. {product['title']} - {product['price']} ({product['source']})")
        print(f"   Link: {product['link']}")
        if product.get("thumbnail"):
            print(f"   Image: {product['thumbnail']}")