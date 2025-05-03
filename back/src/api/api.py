import sys
import os
import base64
import cv2
import sqlite3
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import date, datetime
import tempfile
import traceback
from typing import Optional, List, Dict

sys.path.append("..")
from tsa.analyse_acne_corr import analyze_acne_data
from detection.score import analyze_skin_image
from profile import init_db, save_profile_to_db, get_profile_from_db

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
# Database Connection Helpers
# ---------------------------

def get_db_connection(db_path: str):
    """Helper function to get a SQLite database connection."""
    try:
        conn = sqlite3.connect(db_path)
        return conn
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Failed to connect to database {db_path}: {str(e)}")

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

class TimeseriesEntry(BaseModel):
    id: str
    timestamp: datetime
    acne_severity_score: float
    diet_sugar: float
    diet_dairy: float
    diet_alcohol: float
    sleep_hours: float
    sleep_quality: str
    menstrual_cycle_active: int
    menstrual_cycle_day: int
    latitude: float
    longitude: float
    humidity: float
    pollution: float
    stress: float
    products_used: str
    sunlight_exposure: float

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

class TimeseriesResponse(BaseModel):
    entries: List[Dict]

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

@app.post("/timeseries/", summary="Insert a new time-series entry")
async def insert_timeseries(entry: TimeseriesEntry):
    """Insert a new time-series entry into the acne_tracker.db."""
    db_path = "../db/acne_tracker.db"
    try:
        conn = get_db_connection(db_path)
        cursor = conn.cursor()
        
        insert_sql = """
        INSERT INTO timeseries (
            id, timestamp, acne_severity_score, diet_sugar, diet_dairy, diet_alcohol,
            sleep_hours, sleep_quality, menstrual_cycle_active, menstrual_cycle_day,
            latitude, longitude, humidity, pollution, stress, products_used, sunlight_exposure
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        cursor.execute(insert_sql, (
            entry.id,
            entry.timestamp.isoformat(),
            entry.acne_severity_score,
            entry.diet_sugar,
            entry.diet_dairy,
            entry.diet_alcohol,
            entry.sleep_hours,
            entry.sleep_quality,
            entry.menstrual_cycle_active,
            entry.menstrual_cycle_day,
            entry.latitude,
            entry.longitude,
            entry.humidity,
            entry.pollution,
            entry.stress,
            entry.products_used,
            entry.sunlight_exposure
        ))
        
        conn.commit()
        return {"message": "Time-series entry inserted successfully"}
    
    except sqlite3.IntegrityError as e:
        raise HTTPException(status_code=400, detail=f"Failed to insert time-series entry: {str(e)} (possibly duplicate ID)")
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
    finally:
        if 'conn' in locals():
            conn.close()

@app.get("/timeseries/{user_id}", response_model=TimeseriesResponse, summary="Get time-series data for a user")
async def get_timeseries(user_id: str):
    """Retrieve time-series data for a specific user. Note: Assumes user_id is added to timeseries schema."""
    db_path = "../db/acne_tracker.db"
    try:
        conn = get_db_connection(db_path)
        cursor = conn.cursor()
        
        # Note: This assumes the timeseries table has a user_id column (not in current schema).
        # If user_id is not in the schema, you'll need to modify the query or schema.
        # For now, we'll fetch all entries as a placeholder.
        query = "SELECT * FROM timeseries"  # Modify to "WHERE user_id = ?" if schema updated
        cursor.execute(query)  # Add (user_id,) as params if WHERE clause is used
        
        columns = [description[0] for description in cursor.description]
        rows = cursor.fetchall()
        
        entries = [dict(zip(columns, row)) for row in rows]
        return {"entries": entries}
    
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
    finally:
        if 'conn' in locals():
            conn.close()

@app.get("/analyze/", response_model=AnalysisResponse)
async def analyze():
    try:
        correlations, summary = analyze_acne_data("../db/acne_tracker.db")
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
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_image_file:
            content = await file.read()
            temp_image_file.write(content)
            temp_image_path = temp_image_file.name
        print(f"Temporary image saved to: {temp_image_path}")

        # Call the analysis function from scoring_refactored.py
        analysis_results = analyze_skin_image(
            model_path=MODEL_WEIGHTS_PATH,
            image_path=temp_image_path
        )

    except Exception as e:
        print(f"Error during file handling or analysis call: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error processing image: {e}")
    finally:
        if 'temp_image_path' in locals() and os.path.exists(temp_image_path):
            os.remove(temp_image_path)
            print(f"Temporary image deleted: {temp_image_path}")

    # Process the results
    if not analysis_results or not analysis_results.get('success'):
        error_message = analysis_results.get('message', 'Unknown analysis error') if analysis_results else "Analysis function returned None"
        status_code = 400 if "not found" in error_message.lower() else 500
        raise HTTPException(status_code=status_code, detail=error_message)

    # Encode heatmap image to Base64 if it exists
    heatmap_base64 = None
    if analysis_results.get('heatmap_overlay_bgr') is not None:
        try:
            _, buffer = cv2.imencode('.png', analysis_results['heatmap_overlay_bgr'])
            heatmap_base64 = base64.b64encode(buffer).decode('utf-8')
            print("Heatmap image successfully encoded to Base64.")
        except Exception as e:
            print(f"Error encoding heatmap image to Base64: {e}")

    # Prepare the response
    response_data = DetectionResponse(
        success=True,
        message=analysis_results.get('message', 'Analysis successful.'),
        severity_score=analysis_results.get('severity_score'),
        percentage_area=analysis_results.get('percentage_area'),
        average_intensity=analysis_results.get('average_intensity'),
        lesion_count=analysis_results.get('lesion_count'),
        heatmap_image_base64=heatmap_base64,
        detections=[DetectionInfo(**det) for det in analysis_results.get('detections', [])],
        model_classes=analysis_results.get('model_classes')
    )

    return response_data