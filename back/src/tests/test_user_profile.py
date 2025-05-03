import sqlite3
import os
import tempfile
import pytest
from datetime import datetime
import sys
from pathlib import Path

# Add the src directory to the Python path
src_path = str(Path(__file__).parent.parent)
if src_path not in sys.path:
    sys.path.append(src_path)

# Import the database module
from src.db.user_profile_db import init_db, save_profile_to_db, get_profile_from_db, ValidationError

@pytest.fixture
def temp_db():
    """Create a temporary database file for testing"""
    with tempfile.NamedTemporaryFile(suffix=".db") as tmp:
        # Initialize the database with the temporary file
        init_db(tmp.name)
        yield tmp.name

def test_init_db(temp_db):
    """Test if the user_profiles table is created correctly"""
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()
    
    # Check if table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_profiles'")
    assert cursor.fetchone() is not None
    
    # Check table structure
    cursor.execute("PRAGMA table_info(user_profiles)")
    columns = cursor.fetchall()
    column_names = [col[1] for col in columns]
    
    expected_columns = ['user_id', 'name', 'dob', 'height', 'weight', 'gender']
    assert all(col in column_names for col in expected_columns)
    
    conn.close()

def test_save_and_get_profile(temp_db):
    """Test saving and retrieving a user profile"""
    # Test data
    test_profile = {
        "user_id": "test_user_1",
        "name": "Test User",
        "dob": "1990-01-01",
        "height": 175.5,
        "weight": 70.0,
        "gender": "Female"
    }
    
    # Save profile
    save_profile_to_db(db_path=temp_db, **test_profile)
    
    # Retrieve profile
    retrieved_profile = get_profile_from_db(test_profile["user_id"], db_path=temp_db)
    
    # Verify retrieved data matches test data
    assert retrieved_profile is not None
    for key, value in test_profile.items():
        assert retrieved_profile[key] == value

def test_get_nonexistent_profile(temp_db):
    """Test retrieving a profile that doesn't exist"""
    retrieved_profile = get_profile_from_db("nonexistent_user", db_path=temp_db)
    assert retrieved_profile is None

def test_update_existing_profile(temp_db):
    """Test updating an existing profile"""
    # Initial profile
    initial_profile = {
        "user_id": "test_user_2",
        "name": "Initial Name",
        "dob": "1995-02-02",
        "height": 180.0,
        "weight": 75.0,
        "gender": "Male"
    }
    
    # Save initial profile
    save_profile_to_db(db_path=temp_db, **initial_profile)
    
    # Updated profile with same user_id
    updated_profile = initial_profile.copy()
    updated_profile.update({
        "name": "Updated Name",
        "weight": 78.0
    })
    
    # Save updated profile
    save_profile_to_db(db_path=temp_db, **updated_profile)
    
    # Retrieve and verify updated profile
    retrieved_profile = get_profile_from_db(initial_profile["user_id"], db_path=temp_db)
    assert retrieved_profile is not None
    assert retrieved_profile["name"] == "Updated Name"
    assert retrieved_profile["weight"] == 78.0
    assert retrieved_profile["height"] == initial_profile["height"]  # Unchanged field

def test_save_profile_with_null_values(temp_db):
    """Test saving a profile with null values for optional fields"""
    profile = {
        "user_id": "test_user_3",
        "name": "Null Test User",
        "dob": "2000-01-01",
        "height": None,
        "weight": None,
        "gender": None
    }
    
    save_profile_to_db(db_path=temp_db, **profile)
    retrieved_profile = get_profile_from_db(profile["user_id"], db_path=temp_db)
    
    assert retrieved_profile is not None
    assert retrieved_profile["user_id"] == profile["user_id"]
    assert retrieved_profile["name"] == profile["name"]
    assert retrieved_profile["dob"] == profile["dob"]
    assert retrieved_profile["height"] is None
    assert retrieved_profile["weight"] is None
    assert retrieved_profile["gender"] is None

def test_save_profile_with_invalid_data(temp_db):
    """Test saving a profile with invalid data types"""
    # Test invalid user_id
    with pytest.raises(ValidationError):
        save_profile_to_db(
            user_id="",  # Empty string
            name="Test User",
            dob="2000-01-01",
            height=175.5,
            weight=70.0,
            gender="Male"
        )
    
    # Test invalid name
    with pytest.raises(ValidationError):
        save_profile_to_db(
            user_id="test_user_4",
            name=123,  # Invalid type
            dob="2000-01-01",
            height=175.5,
            weight=70.0,
            gender="Male"
        )
    
    # Test invalid dob format
    with pytest.raises(ValidationError):
        save_profile_to_db(
            user_id="test_user_5",
            name="Test User",
            dob="01-01-2000",  # Wrong format
            height=175.5,
            weight=70.0,
            gender="Male"
        )
    
    # Test invalid height
    with pytest.raises(ValidationError):
        save_profile_to_db(
            user_id="test_user_6",
            name="Test User",
            dob="2000-01-01",
            height="not_a_number",  # Invalid type
            weight=70.0,
            gender="Male"
        )
    
    # Test invalid weight
    with pytest.raises(ValidationError):
        save_profile_to_db(
            user_id="test_user_7",
            name="Test User",
            dob="2000-01-01",
            height=175.5,
            weight=-70.0,  # Negative value
            gender="Male"
        ) 