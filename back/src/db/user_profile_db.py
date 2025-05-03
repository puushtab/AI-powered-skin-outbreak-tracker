import sqlite3
from typing import Optional, Dict, Union
import os
from datetime import datetime

## ALL TESTS PASSED

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "tsa", "acne_tracker.db")

class ValidationError(Exception):
    """Custom exception for validation errors"""
    pass

def validate_profile_data(user_id: str, name: str, dob: str, height: Union[float, None], 
                        weight: Union[float, None], gender: Union[str, None]) -> None:
    """Validate profile data before saving to database"""
    # Validate user_id
    if not isinstance(user_id, str) or not user_id:
        raise ValidationError("user_id must be a non-empty string")
    
    # Validate name
    if not isinstance(name, str) or not name:
        raise ValidationError("name must be a non-empty string")
    
    # Validate dob
    if not isinstance(dob, str) or not dob:
        raise ValidationError("dob must be a non-empty string")
    try:
        datetime.strptime(dob, "%Y-%m-%d")
    except ValueError:
        raise ValidationError("dob must be in YYYY-MM-DD format")
    
    # Validate height
    if height is not None:
        try:
            height = float(height)
            if height <= 0:
                raise ValidationError("height must be positive")
        except (ValueError, TypeError):
            raise ValidationError("height must be a positive number")
    
    # Validate weight
    if weight is not None:
        try:
            weight = float(weight)
            if weight <= 0:
                raise ValidationError("weight must be positive")
        except (ValueError, TypeError):
            raise ValidationError("weight must be a positive number")
    
    # Validate gender
    if gender is not None and not isinstance(gender, str):
        raise ValidationError("gender must be a string")

def get_db_connection(db_path: str = DB_PATH) -> sqlite3.Connection:
    """Get a database connection with the specified path"""
    return sqlite3.connect(db_path)

def init_db(db_path: str = DB_PATH):
    """Initialize the database with the user_profiles table"""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_profiles (
            user_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            dob TEXT NOT NULL,
            height REAL,
            weight REAL,
            gender TEXT
        )
    ''')
    conn.commit()
    conn.close()

def save_profile_to_db(user_id: str, name: str, dob: str, height: float, weight: float, gender: str, db_path: str = DB_PATH):
    """Save or update a user profile in the database"""
    # Validate data before saving
    validate_profile_data(user_id, name, dob, height, weight, gender)
    
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO user_profiles (user_id, name, dob, height, weight, gender)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            name=excluded.name,
            dob=excluded.dob,
            height=excluded.height,
            weight=excluded.weight,
            gender=excluded.gender
    ''', (user_id, name, dob, height, weight, gender))
    conn.commit()
    conn.close()

def get_profile_from_db(user_id: str, db_path: str = DB_PATH) -> Optional[Dict]:
    """Retrieve a user profile from the database"""
    if not isinstance(user_id, str) or not user_id:
        raise ValidationError("user_id must be a non-empty string")
        
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, name, dob, height, weight, gender FROM user_profiles WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            "user_id": row[0],
            "name": row[1],
            "dob": row[2],
            "height": row[3],
            "weight": row[4],
            "gender": row[5]
        }
    return None 