from fastapi import APIRouter
from src.api.models.schemas import AnalysisResponse
from src.api.core.exceptions import AnalysisError
from src.api.config.settings import DB_PATH
from src.correlation.analyse_acne_corr import analyze_acne_data
import os

router = APIRouter(prefix="/analyze", tags=["analysis"])

@router.get("/", response_model=AnalysisResponse)
async def analyze_data():
    if not os.path.exists(DB_PATH):
        raise AnalysisError(f"Database file not found at required path: {DB_PATH}")

    try:
        correlations, summary = analyze_acne_data(DB_PATH)
        return {"correlations": correlations, "summary": summary}
    except Exception as e:
        raise AnalysisError(str(e)) 