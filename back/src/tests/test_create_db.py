import sqlite3
import os
import tempfile
import pytest
from datetime import datetime
import uuid
import sys
from pathlib import Path

# Add the src directory to the Python path
src_path = str(Path(__file__).parent.parent)
if src_path not in sys.path:
    sys.path.append(src_path)

# Import the functions to test
from src.db.create_db import create_timeseries_table, create_profiles_table, setup_databases

@pytest.fixture
def temp_timeseries_db():
    """Create a temporary database file for timeseries testing"""
    with tempfile.NamedTemporaryFile(suffix=".db") as tmp:
        yield tmp.name

@pytest.fixture
def temp_profiles_db():
    """Create a temporary database file for profiles testing"""
    with tempfile.NamedTemporaryFile(suffix=".db") as tmp:
        yield tmp.name

def test_create_timeseries_table(temp_timeseries_db):
    """Test if timeseries table is created correctly"""
    ### TEST PASSED
    create_timeseries_table(temp_timeseries_db)
    
    # Verify table exists
    conn = sqlite3.connect(temp_timeseries_db)
    cursor = conn.cursor()
    
    # Check if table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='timeseries'")
    assert cursor.fetchone() is not None
    
    # Check table structure
    cursor.execute("PRAGMA table_info(timeseries)")
    columns = cursor.fetchall()
    column_names = [col[1] for col in columns]
    
    expected_columns = [
        'id', 'timestamp', 'acne_severity_score', 'diet_sugar', 'diet_dairy',
        'diet_alcohol', 'sleep_hours', 'sleep_quality', 'menstrual_cycle_active',
        'menstrual_cycle_day', 'latitude', 'longitude', 'humidity', 'pollution',
        'stress', 'products_used', 'sunlight_exposure'
    ]
    
    assert all(col in column_names for col in expected_columns)
    conn.close()

def test_create_profiles_table(temp_profiles_db):
    """Test if profiles table is created correctly"""
    create_profiles_table(temp_profiles_db)
    
    # Verify table exists
    conn = sqlite3.connect(temp_profiles_db)
    cursor = conn.cursor()
    
    # Check if table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='profiles'")
    assert cursor.fetchone() is not None
    
    # Check table structure
    cursor.execute("PRAGMA table_info(profiles)")
    columns = cursor.fetchall()
    column_names = [col[1] for col in columns]
    

    
    expected_columns = [
        #         'id', 'name', 'age', 'skin_type', 'skin_concerns', 'allergies',
        # 'medications', 'created_at', 'updated_at'

        'user_id', 'name', 'dob', 'height', 'weight', 'gender'
    ]
    
    assert all(col in column_names for col in expected_columns)
    conn.close()

def test_setup_databases(temp_timeseries_db, temp_profiles_db):
    """Test if both databases are set up correctly"""
    ### TEST PASSED
    setup_databases(temp_timeseries_db, temp_profiles_db)
    
    # Check timeseries database
    conn_ts = sqlite3.connect(temp_timeseries_db)
    cursor_ts = conn_ts.cursor()
    
    cursor_ts.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='timeseries'")
    assert cursor_ts.fetchone() is not None
    
    # Check profiles database
    conn_prof = sqlite3.connect(temp_profiles_db)
    cursor_prof = conn_prof.cursor()
    
    cursor_prof.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='profiles'")
    assert cursor_prof.fetchone() is not None
    
    # Check if sample data was inserted
    cursor_ts.execute("SELECT COUNT(*) FROM timeseries")
    assert cursor_ts.fetchone()[0] > 0
    
    cursor_prof.execute("SELECT COUNT(*) FROM profiles")
    assert cursor_prof.fetchone()[0] > 0
    
    conn_ts.close()
    conn_prof.close() 