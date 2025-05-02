# back/api/api.py

import sys

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import date
from typing import Optional

from profile import init_db, save_profile_to_db, get_profile_from_db

sys.path.append("..")
from tsa.analyse_acne_corr import analyze_acne_data

app = FastAPI(title="Acne Tracker Analysis API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database on startup
init_db()

# ---------------------------
# Pydantic Models
# ---------------------------

class Profile(BaseModel):
    user_id: str = "user_1"
    name: str
    dob: date
    height: float
    weight: float
    gender: Optional[str] = "Not Specified"

class AnalysisResponse(BaseModel):
    correlations: dict
    summary: str

# ---------------------------
# API Endpoints
# ---------------------------

@app.post("/profile/")
async def save_profile(profile: Profile):
    try:
        save_profile_to_db(
            user_id=profile.user_id,
            name=profile.name,
            dob=profile.dob.isoformat(),
            height=profile.height,
            weight=profile.weight,
            gender=profile.gender
        )
        return {"message": "Profile saved successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save profile: {str(e)}")


@app.get("/profile/{user_id}")
async def get_profile(user_id: str):
    try:
        profile = get_profile_from_db(user_id)
        if profile:
            return profile
        else:
            raise HTTPException(status_code=404, detail="Profile not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch profile: {str(e)}")


@app.get("/analyze/", response_model=AnalysisResponse)
async def analyze():
    try:
        correlations, summary = analyze_acne_data("../tsa/acne_tracker.db")
        return {"correlations": correlations, "summary": summary}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
