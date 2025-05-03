from fastapi import APIRouter, HTTPException
from typing import Optional
from src.api.models.schemas import Profile
from src.api.core.exceptions import DatabaseError
from src.db.user_profile_db import save_profile_to_db, get_profile_from_db

router = APIRouter(prefix="/profile", tags=["profile"])

@router.post("/")
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
        raise DatabaseError(str(e))

@router.get("/{user_id}")
async def get_profile(user_id: str):
    try:
        profile_data = get_profile_from_db(user_id)
        if not profile_data:
            raise HTTPException(status_code=404, detail="Profile not found")
        return profile_data
    except HTTPException:
        raise
    except Exception as e:
        raise DatabaseError(str(e)) 