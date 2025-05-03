from datetime import date
from typing import Optional, List, Dict
from pydantic import BaseModel

class Profile(BaseModel):
    user_id: str = "user_1"
    name: str
    dob: date
    height: float
    weight: float
    gender: Optional[str] = "Not Specified"

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

class AnalysisResponse(BaseModel):
    correlations: dict
    summary: str 