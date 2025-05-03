import sqlite3
import pytest
from contextlib import contextmanager
from pathlib import Path
import sys

# Add the src directory to the Python path
src_path = str(Path(__file__).parent.parent)
if src_path not in sys.path:
    sys.path.append(src_path)

@contextmanager
def mock_db_connection():
    """Create an in-memory SQLite database connection"""
    conn = sqlite3.connect(':memory:')
    try:
        yield conn
    finally:
        conn.close()

@pytest.fixture
def mock_db():
    """Fixture that provides a clean in-memory database for each test"""
    with mock_db_connection() as conn:
        # Create tables
        conn.execute('''
            CREATE TABLE IF NOT EXISTS user_profiles (
                user_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                dob TEXT NOT NULL,
                height REAL,
                weight REAL,
                gender TEXT
            )
        ''')
        
        conn.execute('''
            CREATE TABLE IF NOT EXISTS skin_plans (
                plan_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                plan_name TEXT NOT NULL,
                start_date TEXT NOT NULL,
                end_date TEXT,
                FOREIGN KEY (user_id) REFERENCES user_profiles(user_id)
            )
        ''')
        
        conn.execute('''
            CREATE TABLE IF NOT EXISTS acne_tracker (
                entry_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                date TEXT NOT NULL,
                severity INTEGER,
                location TEXT,
                notes TEXT,
                image_path TEXT,
                FOREIGN KEY (user_id) REFERENCES user_profiles(user_id)
            )
        ''')
        
        conn.commit()
        yield conn 