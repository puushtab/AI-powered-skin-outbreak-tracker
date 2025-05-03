# back/api/api.py

import sys
import os
import base64
import cv2
from fastapi import FastAPI, HTTPException,UploadFile,File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import date
import tempfile
import traceback
from typing import Optional,List, Optional, Dict
from profile import init_db, save_profile_to_db, get_profile_from_db

sys.path.append("..")
from tsa.analyse_acne_corr import analyze_acne_data
from detection.score import analyze_skin_image
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
MODEL_WEIGHTS_PATH = r'../detection/best.pt'

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

class DetectionInfo(BaseModel):
    class_name: str
    confidence: float

class DetectionResponse(BaseModel):
    success: bool
    message: str
    severity_score: Optional[float] = None
    percentage_area: Optional[float] = None
    average_intensity: Optional[float] = None
    lesion_count: Optional[int] = None
    heatmap_image_base64: Optional[str] = None 
    detections: Optional[List[DetectionInfo]] = None
    model_classes: Optional[Dict[int, str]] = None


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

@app.post("/detect/", response_model=DetectionResponse, summary="Detect skin conditions and score severity")
async def detect_skin_conditions(file: UploadFile = File(..., description="Image file for analysis (JPEG, PNG)")):
    """
    Accepts an image file, performs skin condition detection using a YOLOv8 model,
    calculates a severity score, generates a heatmap, and returns the results.
    """
    if analyze_skin_image is None:
         raise HTTPException(status_code=500, detail="Analysis function not loaded. Check server logs.")

    # Validate file type (basic check)
    if file.content_type not in ["image/jpeg", "image/png", "image/bmp"]:
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload JPG, PNG, or BMP.")

    # Create a temporary file to store the uploaded image
    # Using tempfile is safer as it handles cleanup
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_image_file:
            content = await file.read()
            temp_image_file.write(content)
            temp_image_path = temp_image_file.name # Get the path to the temporary file
        print(f"Temporary image saved to: {temp_image_path}")

        # Call the analysis function from scoring_refactored.py
        analysis_results = analyze_skin_image(
            model_path=MODEL_WEIGHTS_PATH,
            image_path=temp_image_path
            # You can add arguments here to override defaults from scoring_refactored if needed:
            # conf_threshold=0.3,
            # heatmap_sigma=100,
            # etc.
        )

    except Exception as e:
        print(f"Error during file handling or analysis call: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error processing image: {e}")
    finally:
        # Ensure temporary file is deleted even if analysis fails
        if 'temp_image_path' in locals() and os.path.exists(temp_image_path):
            os.remove(temp_image_path)
            print(f"Temporary image deleted: {temp_image_path}")

    # Process the results
    if not analysis_results or not analysis_results.get('success'):
        error_message = analysis_results.get('message', 'Unknown analysis error') if analysis_results else "Analysis function returned None"
        # Decide status code based on message if possible, otherwise default to 500
        status_code = 400 if "not found" in error_message.lower() else 500
        raise HTTPException(status_code=status_code, detail=error_message)

    # Encode heatmap image to Base64 if it exists
    heatmap_base64 = None
    if analysis_results.get('heatmap_overlay_bgr') is not None:
        try:
            # Encode the image to PNG format in memory
            _, buffer = cv2.imencode('.png', analysis_results['heatmap_overlay_bgr'])
            # Encode the buffer to Base64
            heatmap_base64 = base64.b64encode(buffer).decode('utf-8')
            print("Heatmap image successfully encoded to Base64.")
        except Exception as e:
            print(f"Error encoding heatmap image to Base64: {e}")
            # Proceed without heatmap if encoding fails, but log it
            # Or raise an HTTPException if heatmap is critical

    # Prepare the response using the Pydantic model structure
    response_data = DetectionResponse(
        success=True,
        message=analysis_results.get('message', 'Analysis successful.'),
        severity_score=analysis_results.get('severity_score'),
        percentage_area=analysis_results.get('percentage_area'),
        average_intensity=analysis_results.get('average_intensity'),
        lesion_count=analysis_results.get('lesion_count'),
        heatmap_image_base64=heatmap_base64,
        detections=[DetectionInfo(**det) for det in analysis_results.get('detections', [])], # Convert dicts to Pydantic models
        model_classes=analysis_results.get('model_classes')
    )

    return response_data

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api:app",     # module path to your FastAPI app
        host="0.0.0.0",         # listen on all interfaces
        port=8000,              # or any port you prefer
        reload=True            # auto-reload on code changes
    )