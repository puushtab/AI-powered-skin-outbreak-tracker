from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import date
import io
from PIL import Image
import uvicorn

app = FastAPI(title="Skin Outbreak Tracker API")

# CORS middleware to allow Streamlit frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501"],  # Streamlit default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage (replace with database in production)
users = {}
lifestyle_data = []

# Pydantic models for request validation
class UserProfile(BaseModel):
    name: str
    dob: date
    height: int
    weight: int
    gender: str

class LifestyleEntry(BaseModel):
    date: date
    sugar: int
    dairy: int
    sleep: float
    stress: int
    product: str
    sunlight: float
    menstrual: bool
    travel: str

# Endpoints
@app.post("/profile/")
async def save_profile(profile: UserProfile):
    user_id = "user_1"  # Mock user ID (use auth in production)
    users[user_id] = profile.dict()
    return {"message": "Profile saved", "user_id": user_id}

@app.get("/profile/{user_id}")
async def get_profile(user_id: str):
    if user_id not in users:
        raise HTTPException(status_code=404, detail="User not found")
    return users[user_id]

@app.post("/photo/")
async def upload_photo(file: UploadFile = File(...)):
    # Validate file type
    if file.content_type not in ["image/png", "image/jpeg"]:
        raise HTTPException(status_code=400, detail="Invalid file type. Use PNG or JPEG.")
    
    # Read and process image
    image_data = await file.read()
    image = Image.open(io.BytesIO(image_data))
    
    # Placeholder: AI severity analysis (replace with ResNet/YOLOv8 model)
    severity_score = 75  # Mock score
    return {"severity_score": severity_score, "message": "Photo processed"}

@app.post("/lifestyle/")
async def log_lifestyle(entry: LifestyleEntry):
    # Add mock severity score (replace with AI model output)
    entry_dict = entry.dict()
    entry_dict["severity"] = 75  # Mock score
    lifestyle_data.append(entry_dict)
    return {"message": "Lifestyle data logged"}

@app.get("/lifestyle/")
async def get_lifestyle():
    return lifestyle_data

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)