from fastapi import APIRouter, HTTPException
from typing import Dict, Optional
from src.api.core.exceptions import AnalysisError
from src.solutions.medllama import generate_skin_plan_from_json, build_search_query, search_products_google
from src.db.user_profile_db import get_profile_from_db
from src.db.create_db import get_latest_timeseries_data
import json
from datetime import datetime
from pathlib import Path
import os

router = APIRouter(prefix="/skin-plan", tags=["skin-plan"])

@router.post("/generate")
async def generate_skin_plan(user_id: str, model_name: Optional[str] = "llama2"):
    """
    Generate a personalized skin treatment plan based on user profile and timeseries data.
    
    Args:
        user_id: The ID of the user to generate the plan for
        model_name: Optional name of the Ollama model to use (defaults to llama2)
    
    Returns:
        JSON response containing the generated skin plan with:
        - treatment_plan: list of {date: str, treatment: str}
        - lifestyle_advice: list of advice strings
        - diet_recommendations: list of diet-specific recommendations
        - sleep_recommendations: list of sleep-specific recommendations
        - environmental_factors: list of environmental factor recommendations
        - product_recommendations: list of recommended products with details
    """
    try:
        # Set up database paths
        db_dir = Path(__file__).parent.parent.parent / "db"
        timeseries_db_path = str(db_dir / "acne_tracker.db")
        profiles_db_path = str(db_dir / "user_profiles.db")
        
        # Get user profile from database
        user_profile = get_profile_from_db(user_id, db_path=profiles_db_path)
        if not user_profile:
            raise HTTPException(status_code=404, detail=f"User profile not found for ID: {user_id}")
        
        # Get latest timeseries data
        timeseries_data = get_latest_timeseries_data(user_id, db_path=timeseries_db_path)
        
        # Prepare input data for the model
        input_data = {
            "user_profile": user_profile,
            "timeseries_data": timeseries_data,
            "model_name": model_name
        }
        
        # Generate the skin plan
        plan_json = generate_skin_plan_from_json(input_data)
        
        # Parse the JSON string to ensure it's valid
        plan_data = json.loads(plan_json)
        
        # Get product recommendations and search for products
        product_recommendations = plan_data.get("product_recommendations", [])
        recommended_products = []
        
        # Get SerpAPI key from environment
        serpapi_key = os.environ.get("SERPAPI_KEY")
        if not serpapi_key:
            raise HTTPException(status_code=500, detail="SERPAPI_KEY environment variable not set")
        
        # Search for products for each recommendation
        for rec in product_recommendations:
            search_query = build_search_query(rec)
            products = search_products_google(search_query, serpapi_key, num_results=4)
            recommended_products.extend(products)
        
        # Add product results to the plan data
        plan_data["recommended_products"] = recommended_products
        
        return {
            "success": True,
            "message": "Skin plan generated successfully",
            "data": plan_data
        }
        
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"Error parsing generated plan: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        raise AnalysisError(f"Error generating skin plan: {str(e)}") 