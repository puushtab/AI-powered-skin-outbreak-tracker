from fastapi import APIRouter, HTTPException
from typing import List, Dict, Optional
from datetime import datetime
from src.api.core.exceptions import DatabaseError
from src.db.create_db import get_latest_timeseries_data, create_timeseries_table
from src.correlation.analyse_acne_corr import analyze_acne_data
import sqlite3
import os
from pathlib import Path
import uuid

router = APIRouter(prefix="/timeseries", tags=["timeseries"])

def save_timeseries_data(entry: Dict) -> bool:
    """
    Save a new timeseries entry to the database.
    
    Args:
        entry: Dictionary containing timeseries data
        
    Returns:
        bool: True if successful, False otherwise
    """
    conn = None
    try:
        # Get the absolute path to the database
        db_dir = Path(__file__).parent.parent.parent / "db"
        db_dir.mkdir(parents=True, exist_ok=True)  # Create directory if it doesn't exist
        db_path = str(db_dir / "acne_tracker.db")
        
        # Ensure database and table exist
        create_timeseries_table(db_path)
        
        # Connect to SQLite with timeout
        conn = sqlite3.connect(db_path, timeout=30)
        cursor = conn.cursor()
        
        # Add id if not present
        if 'id' not in entry:
            entry['id'] = str(uuid.uuid4())
            
        # Ensure timestamp is in ISO format
        if 'timestamp' in entry:
            try:
                # Try to parse the timestamp and convert to ISO format
                timestamp = datetime.fromisoformat(entry['timestamp'].replace('Z', '+00:00'))
                entry['timestamp'] = timestamp.isoformat()
            except ValueError:
                # If parsing fails, use current time
                entry['timestamp'] = datetime.now().isoformat()
        
        # Prepare the SQL query
        columns = ', '.join(entry.keys())
        placeholders = ', '.join(['?' for _ in entry])
        query = f"INSERT INTO timeseries ({columns}) VALUES ({placeholders})"
        
        # Execute the query
        cursor.execute(query, list(entry.values()))
        
        # Commit changes
        conn.commit()
        return True
        
    except sqlite3.OperationalError as e:
        print(f"Database operational error: {e}")
        return False
    except sqlite3.IntegrityError as e:
        print(f"Database integrity error: {e}")
        return False
    except Exception as e:
        print(f"Error saving timeseries data: {e}")
        return False
    finally:
        if conn:
            try:
                conn.close()
            except Exception as e:
                print(f"Error closing database connection: {e}")

@router.get("/{user_id}")
async def get_timeseries(user_id: str):
    """
    Get timeseries data for a specific user.
    
    Args:
        user_id: The ID of the user to get data for
        
    Returns:
        Dictionary containing:
        - success: bool
        - message: str
        - data: List of timeseries entries
    """
    try:
        db_dir = Path(__file__).parent.parent.parent / "db"
        db_path = str(db_dir / "acne_tracker.db")
        
        data = get_latest_timeseries_data(user_id, db_path)
        if not data:
            raise HTTPException(status_code=404, detail=f"No timeseries data found for user: {user_id}")
        
        return {
            "success": True,
            "message": "Timeseries data retrieved successfully",
            "data": data
        }
    except HTTPException:
        raise
    except Exception as e:
        raise DatabaseError(str(e))

@router.post("/")
async def save_timeseries(entry: Dict):
    """
    Save a new timeseries entry.
    
    Args:
        entry: Dictionary containing timeseries data with fields:
            - user_id: str (required)
            - timestamp: str (required, ISO format)
            - acne_severity_score: float (optional, default 0)
            - diet_sugar: float (optional, default 0)
            - diet_dairy: float (optional, default 0)
            - diet_alcohol: float (optional, default 0)
            - sleep_hours: float (optional, default 0)
            - sleep_quality: str (optional, default 'unknown')
            - menstrual_cycle_active: int (optional, default 0)
            - menstrual_cycle_day: int (optional, default 0)
            - latitude: float (optional, default 0)
            - longitude: float (optional, default 0)
            - humidity: float (optional, default 0)
            - pollution: float (optional, default 0)
            - stress: float (optional, default 0)
            - products_used: str (optional, default '')
            - sunlight_exposure: float (optional, default 0)
            
    Returns:
        Dictionary containing:
        - success: bool
        - message: str
    """
    try:
        # Validate required fields
        required_fields = ["user_id", "timestamp"]
        
        for field in required_fields:
            if field not in entry:
                raise HTTPException(
                    status_code=400,
                    detail=f"Missing required field: {field}"
                )
        
        # Add default values for optional fields
        defaults = {
            "acne_severity_score": 0,
            "diet_sugar": 0,
            "diet_dairy": 0,
            "diet_alcohol": 0,
            "sleep_hours": 0,
            "sleep_quality": "unknown",
            "menstrual_cycle_active": 0,
            "menstrual_cycle_day": 0,
            "latitude": 0,
            "longitude": 0,
            "humidity": 0,
            "pollution": 0,
            "stress": 0,
            "products_used": "",
            "sunlight_exposure": 0
        }
        
        # Add id field
        entry["id"] = str(uuid.uuid4())
        
        # Update entry with defaults for missing fields
        for key, default_value in defaults.items():
            if key not in entry or entry[key] is None:
                entry[key] = default_value
        
        # Save the entry
        if save_timeseries_data(entry):
            return {
                "success": True,
                "message": "Timeseries entry saved successfully"
            }
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to save timeseries entry"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise DatabaseError(str(e))

@router.get("/summary/{user_id}")
async def get_summary(user_id: str):
    """
    Get a summary of acne severity trends and correlations for a specific user.
    
    Args:
        user_id: The ID of the user to get the summary for
        
    Returns:
        Dictionary containing:
        - success: bool
        - message: str
        - summary: str
        - correlations: dict
    """
    try:
        db_dir = Path(__file__).parent.parent.parent / "db"
        db_path = str(db_dir / "acne_tracker.db")
        
        # Get correlations and summary
        correlations, summary = analyze_acne_data(db_path, user_id)
        
        return {
            "success": True,
            "message": "Summary generated successfully",
            "summary": summary,
            "correlations": correlations
        }
    except Exception as e:
        raise DatabaseError(str(e)) 