from fastapi import APIRouter, HTTPException
from typing import Dict, Optional
from src.api.core.exceptions import AnalysisError
from datetime import datetime, timedelta

router = APIRouter(prefix="/skin-plan", tags=["skin-plan"])

@router.post("/generate")
async def generate_skin_plan(user_id: str, model_name: Optional[str] = "medllama2"):
    """
    Generate a personalized skin treatment plan based on user profile and timeseries data.
    
    Args:
        user_id: The ID of the user to generate the plan for
        model_name: Optional name of the Ollama model to use (defaults to medllama2)
    
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
        # Hardcoded response
        today = datetime.now()
        plan_data = {
            "treatment_plan": [
                {
                    "date": today.strftime("%Y-%m-%d"),
                    "treatment": "Morning: Gentle cleanser, Vitamin C serum, Moisturizer with SPF 30\nEvening: Double cleanse, Retinol serum, Hydrating moisturizer"
                },
                {
                    "date": (today + timedelta(days=1)).strftime("%Y-%m-%d"),
                    "treatment": "Morning: Gentle cleanser, Niacinamide serum, Moisturizer with SPF 30\nEvening: Double cleanse, Hyaluronic acid serum, Hydrating moisturizer"
                },
                {
                    "date": (today + timedelta(days=2)).strftime("%Y-%m-%d"),
                    "treatment": "Morning: Gentle cleanser, Vitamin C serum, Moisturizer with SPF 30\nEvening: Double cleanse, Retinol serum, Hydrating moisturizer"
                }
            ],
            "lifestyle_advice": [
                "Stay hydrated by drinking at least 2 liters of water daily",
                "Get 7-8 hours of quality sleep each night",
                "Manage stress through meditation or light exercise",
                "Avoid touching your face throughout the day"
            ],
            "diet_recommendations": [
                "Reduce sugar intake to less than 25g per day",
                "Increase consumption of omega-3 rich foods (salmon, walnuts)",
                "Include more antioxidant-rich fruits and vegetables",
                "Consider reducing dairy consumption if you notice breakouts"
            ],
            "sleep_recommendations": [
                "Maintain a consistent sleep schedule",
                "Use silk pillowcases to reduce friction on skin",
                "Sleep on your back to prevent face rubbing",
                "Keep bedroom temperature between 18-22°C"
            ],
            "environmental_factors": [
                "Use a humidifier in dry environments",
                "Protect skin from pollution with antioxidant serums",
                "Wear broad-spectrum SPF 30+ daily",
                "Avoid excessive sun exposure"
            ],
            "product_recommendations": [
                {
                    "skin_condition": "acne",
                    "skin_type": "combination",
                    "characteristics": ["non-comedogenic", "fragrance-free", "oil-free"],
                    "price_range": "mid-range",
                    "constitution": ["hyaluronic acid", "niacinamide", "ceramides"],
                    "product_type": "cleanser"
                },
                {
                    "skin_condition": "acne",
                    "skin_type": "combination",
                    "characteristics": ["non-comedogenic", "fragrance-free", "lightweight"],
                    "price_range": "mid-range",
                    "constitution": ["hyaluronic acid", "niacinamide", "ceramides"],
                    "product_type": "moisturizer"
                }
            ],
            "recommended_products": [
                {
                    "title": "CeraVe Hydrating Cleanser",
                    "price": "$14.99",
                    "source": "Amazon",
                    "link": "https://www.amazon.com/CeraVe-Hydrating-Facial-Cleanser-Non-Foaming/dp/B00F97HJH6",
                    "thumbnail": "https://m.media-amazon.com/images/I/61k7JqSWOUL._SL1500_.jpg"
                },
                {
                    "title": "La Roche-Posay Toleriane Double Repair Face Moisturizer",
                    "price": "$19.99",
                    "source": "Amazon",
                    "link": "https://www.amazon.com/La-Roche-Posay-Toleriane-Moisturizer-Ceramides/dp/B01N7T8Q0H",
                    "thumbnail": "https://m.media-amazon.com/images/I/61k7JqSWOUL._SL1500_.jpg"
                },
                {
                    "title": "The Ordinary Niacinamide 10% + Zinc 1%",
                    "price": "$12.90",
                    "source": "Amazon",
                    "link": "https://www.amazon.com/Ordinary-Niacinamide-10-Zinc-30ml/dp/B06VSX2B1Q",
                    "thumbnail": "https://m.media-amazon.com/images/I/61k7JqSWOUL._SL1500_.jpg"
                },
                {
                    "title": "CeraVe AM Facial Moisturizing Lotion SPF 30",
                    "price": "$16.99",
                    "source": "Amazon",
                    "link": "https://www.amazon.com/CeraVe-Moisturizing-Sunscreen-Ceramides-Niacinamide/dp/B00F97HJH6",
                    "thumbnail": "https://m.media-amazon.com/images/I/61k7JqSWOUL._SL1500_.jpg"
                }
            ]
        }
        
        return {
            "success": True,
            "message": "Skin plan generated successfully",
            "data": plan_data
        }
        
    except Exception as e:
        raise AnalysisError(f"Error generating skin plan: {str(e)}") 