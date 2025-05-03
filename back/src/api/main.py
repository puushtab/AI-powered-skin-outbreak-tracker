from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.config.settings import ALLOWED_ORIGINS, API_PREFIX
from src.api.routes import profile, detection, analysis, skin_plan
from src.db.user_profile_db import init_db

app = FastAPI(
    title="Acne Tracker Analysis API",
    description="API for skin condition detection and analysis",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database
init_db()

# Include routers
app.include_router(profile.router, prefix=API_PREFIX)
app.include_router(detection.router, prefix=API_PREFIX)
app.include_router(analysis.router, prefix=API_PREFIX)
app.include_router(skin_plan.router, prefix=API_PREFIX)

@app.get("/")
async def root():
    return {
        "message": "Acne Tracker Analysis API is running",
        "docs_url": "/docs",
        "redoc_url": "/redoc"
    } 