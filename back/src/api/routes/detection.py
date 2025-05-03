<<<<<<< HEAD
import os
import base64
import cv2
import numpy as np
from fastapi import APIRouter, UploadFile, File
from src.api.models.schemas import DetectionResponse, DetectionInfo
from src.api.core.exceptions import ModelNotAvailableError, InvalidFileTypeError, AnalysisError
from src.api.config.settings import MODEL_WEIGHTS_PATH, ALLOWED_FILE_TYPES
from src.detection.score import analyze_skin_image
import tempfile

router = APIRouter(tags=["detection"])

@router.post("/analyze-image", response_model=DetectionResponse)
async def detect_skin_conditions(file: UploadFile = File(...)):
    if file.content_type not in ALLOWED_FILE_TYPES:
        raise InvalidFileTypeError(file.content_type)

    if not os.path.exists(MODEL_WEIGHTS_PATH):
        raise ModelNotAvailableError()

    temp_image_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_file:
            content = await file.read()
            if not content:
                raise AnalysisError("Received empty file content")
            temp_file.write(content)
            temp_image_path = temp_file.name

        analysis_results = analyze_skin_image(
            model_path=MODEL_WEIGHTS_PATH,
            image_path=temp_image_path
        )

        if not analysis_results or not analysis_results.get('success'):
            raise AnalysisError(analysis_results.get('message', 'Unknown analysis error'))

        # Process heatmap image
        heatmap_base64 = None
        heatmap_data = analysis_results.get('heatmap_overlay_bgr')
        if heatmap_data is not None and isinstance(heatmap_data, np.ndarray):
            success, buffer = cv2.imencode('.png', heatmap_data)
            if success:
                heatmap_base64 = base64.b64encode(buffer).decode('utf-8')

        return DetectionResponse(
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

    except Exception as e:
        raise AnalysisError(str(e))
    finally:
        if temp_image_path and os.path.exists(temp_image_path):
            try:
                os.remove(temp_image_path)
            except OSError:
=======
import os
import base64
import cv2
import numpy as np
from fastapi import APIRouter, UploadFile, File
from src.api.models.schemas import DetectionResponse, DetectionInfo
from src.api.core.exceptions import ModelNotAvailableError, InvalidFileTypeError, AnalysisError
from src.api.config.settings import MODEL_WEIGHTS_PATH, ALLOWED_FILE_TYPES
from src.detection.score import analyze_skin_image
import tempfile

router = APIRouter(prefix="/detect", tags=["detection"])

@router.post("/", response_model=DetectionResponse)
async def detect_skin_conditions(file: UploadFile = File(...)):
    if file.content_type not in ALLOWED_FILE_TYPES:
        raise InvalidFileTypeError(file.content_type)

    if not os.path.exists(MODEL_WEIGHTS_PATH):
        raise ModelNotAvailableError()

    temp_image_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_file:
            content = await file.read()
            if not content:
                raise AnalysisError("Received empty file content")
            temp_file.write(content)
            temp_image_path = temp_file.name

        analysis_results = analyze_skin_image(
            model_path=MODEL_WEIGHTS_PATH,
            image_path=temp_image_path
        )

        if not analysis_results or not analysis_results.get('success'):
            raise AnalysisError(analysis_results.get('message', 'Unknown analysis error'))

        # Process heatmap image
        heatmap_base64 = None
        heatmap_data = analysis_results.get('heatmap_overlay_bgr')
        if heatmap_data is not None and isinstance(heatmap_data, np.ndarray):
            success, buffer = cv2.imencode('.png', heatmap_data)
            if success:
                heatmap_base64 = base64.b64encode(buffer).decode('utf-8')

        return DetectionResponse(
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

    except Exception as e:
        raise AnalysisError(str(e))
    finally:
        if temp_image_path and os.path.exists(temp_image_path):
            try:
                os.remove(temp_image_path)
            except OSError:
>>>>>>> db3d0e43c34f55f836fe76ef74d70e9f40d0c7d1
                pass 