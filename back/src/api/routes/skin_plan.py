from fastapi import APIRouter, HTTPException
from typing import Dict, Optional
from src.api.core.exceptions import AnalysisError
from src.solutions.medllama import generate_skin_plan_from_json
import json

router = APIRouter(prefix="/skin-plan", tags=["skin-plan"])

@router.post("/generate")
async def generate_skin_plan(user_profile: Dict, timeseries_data: Optional[Dict] = None):
    """
    Generate a personalized skin treatment plan based on user profile and timeseries data.
    
    Args:
        user_profile: Dictionary containing user profile information
        timeseries_data: Optional dictionary containing timeseries data (not implemented yet)
    
    Returns:
        JSON response containing the generated skin plan
    """
    try:
        # For now, we'll only use the user profile data
        # TODO: Incorporate timeseries_data when implemented
        input_data = {
            "disease": "acne",  # Default for now, can be made dynamic later
            "severity_score": 50,  # Default for now, can be made dynamic later
            "sex": user_profile.get("gender", ""),
            "age": 25,  # Default for now, can be calculated from DOB later
            "weight": user_profile.get("weight", 70.0),
            "previous_treatment": "",  # Default for now
            "diet": "",  # Default for now
            "actual_date": "2024-05-03"  # Default for now, can be made dynamic
        }
        
        # Generate the skin plan
        plan_json = generate_skin_plan_from_json(input_data)
        
        # Parse the JSON string to ensure it's valid
        plan_data = json.loads(plan_json)
        
        return {
            "success": True,
            "message": "Skin plan generated successfully",
            "data": plan_data
        }
        
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"Error parsing generated plan: {str(e)}")
    except Exception as e:
        raise AnalysisError(f"Error generating skin plan: {str(e)}") 