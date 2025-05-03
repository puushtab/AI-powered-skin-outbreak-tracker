import sqlite3
from sqlite3 import Error as SQLiteError
from datetime import datetime
import uuid
import os
from typing import Optional, Dict

def create_timeseries_table(db_path="acne_tracker.db"):
    """Create the timeseries table in the SQLite database."""
    ### TEST PASSED
    try:
        # Check if database file is accessible
        if os.path.exists(db_path) and not os.access(db_path, os.W_OK):
            raise PermissionError(f"Cannot write to database file '{db_path}'.")
        
        # Connect to SQLite
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create timeseries table
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS timeseries (
            id TEXT PRIMARY KEY,
            timestamp TEXT NOT NULL,
            acne_severity_score REAL NOT NULL,
            diet_sugar REAL NOT NULL,
            diet_dairy REAL NOT NULL,
            diet_alcohol REAL NOT NULL,
            sleep_hours REAL NOT NULL,
            sleep_quality TEXT NOT NULL,
            menstrual_cycle_active INTEGER NOT NULL CHECK(menstrual_cycle_active IN (0, 1)),
            menstrual_cycle_day INTEGER NOT NULL CHECK(menstrual_cycle_day >= 0),
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            humidity REAL NOT NULL,
            pollution REAL NOT NULL,
            stress REAL NOT NULL,
            products_used TEXT NOT NULL,
            sunlight_exposure REAL NOT NULL
        );
        """
        cursor.execute(create_table_sql)
        
        # Insert sample data
        sample_data = [
            (
                str(uuid.uuid4()),
                datetime.now().isoformat(),
                75.0,
                20.0,
                15.0,
                0.0,
                7.0,
                "good",
                0,
                0,
                48.8566,
                2.3522,
                60.0,
                30.0,
                5.0,
                "cleanser,moisturizer",
                2.0
            )
        ]
        
        insert_sql = """
        INSERT INTO timeseries (
            id, timestamp, acne_severity_score, diet_sugar, diet_dairy, diet_alcohol,
            sleep_hours, sleep_quality, menstrual_cycle_active, menstrual_cycle_day,
            latitude, longitude, humidity, pollution, stress, products_used, sunlight_exposure
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        try:
            cursor.executemany(insert_sql, sample_data)
            conn.commit()
            print(f"Inserted {len(sample_data)} rows into 'timeseries' table in '{db_path}'.")
        except sqlite3.IntegrityError as e:
            print(f"Warning: Integrity error while inserting sample data into 'timeseries': {e}")
        
    except SQLiteError as e:
        raise SQLiteError(f"Failed to create or modify 'timeseries' table in '{db_path}': {e}")
    except PermissionError as e:
        raise PermissionError(e)
    except Exception as e:
        raise RuntimeError(f"Unexpected error while setting up 'timeseries' table: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

def create_profiles_table(db_path="user_profiles.db"):
    """Create the profiles table in the SQLite database."""
    try:
        # Check if database file is accessible
        if os.path.exists(db_path) and not os.access(db_path, os.W_OK):
            raise PermissionError(f"Cannot write to database file '{db_path}'.")
        
        # Connect to SQLite
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create profiles table
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS profiles (
            user_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            dob TEXT NOT NULL,
            height INTEGER NOT NULL CHECK(height >= 0),
            weight INTEGER NOT NULL CHECK(weight >= 0),
            gender TEXT NOT NULL
        );
        """
        cursor.execute(create_table_sql)
        
        # Insert sample data
        sample_data = [
            (
                "user_1",
                "Amine Maazizi",
                "2025-05-03",
                180,
                90,
                "Male"
            )
        ]
        
        insert_sql = """
        INSERT INTO profiles (
            user_id, name, dob, height, weight, gender
        ) VALUES (?, ?, ?, ?, ?, ?)
        """
        
        try:
            cursor.executemany(insert_sql, sample_data)
            conn.commit()
            print(f"Inserted {len(sample_data)} rows into 'profiles' table in '{db_path}'.")
        except sqlite3.IntegrityError as e:
            print(f"Warning: Integrity error while inserting sample data into 'profiles': {e}")
        
    except SQLiteError as e:
        raise SQLiteError(f"Failed to create or modify 'profiles' table in '{db_path}': {e}")
    except PermissionError as e:
        raise PermissionError(e)
    except Exception as e:
        raise RuntimeError(f"Unexpected error while setting up 'profiles' table: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

def setup_databases(timeseries_db_path="acne_tracker.db", profiles_db_path="user_profiles.db"):
    """Set up both timeseries and profiles SQLite databases."""
    try:
        # Create timeseries table
        create_timeseries_table(timeseries_db_path)
        
        # Create profiles table
        create_profiles_table(profiles_db_path)
        
        print("SQLite database setup completed successfully.")
        
    except SQLiteError as e:
        raise SQLiteError(f"SQLite error during database setup: {e}")
    except PermissionError as e:
        raise PermissionError(f"Permission error during database setup: {e}")
    except Exception as e:
        raise RuntimeError(f"Unexpected error during database setup: {e}")

def get_latest_timeseries_data(user_id: str, db_path: str = "acne_tracker.db") -> Optional[Dict]:
    """
    Get the most recent timeseries data for a given user.
    
    Args:
        user_id: The ID of the user to fetch data for
        db_path: Path to the SQLite database file
        
    Returns:
        Dictionary containing the latest timeseries data, or None if no data exists
    """
    try:
        # Check if database file exists
        if not os.path.exists(db_path):
            raise FileNotFoundError(f"Database file '{db_path}' not found")
        
        # Connect to SQLite
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get the latest timeseries entry for the user
        query = """
        SELECT 
            timestamp, acne_severity_score, diet_sugar, diet_dairy, diet_alcohol,
            sleep_hours, sleep_quality, menstrual_cycle_active, menstrual_cycle_day,
            latitude, longitude, humidity, pollution, stress, products_used, sunlight_exposure
        FROM timeseries
        WHERE id LIKE ?
        ORDER BY timestamp DESC
        LIMIT 1
        """
        
        cursor.execute(query, (f"{user_id}%",))
        row = cursor.fetchone()
        
        if not row:
            return None
            
        # Convert row to dictionary
        timeseries_data = {
            "timestamp": row[0],
            "acne_severity_score": row[1],
            "diet_sugar": row[2],
            "diet_dairy": row[3],
            "diet_alcohol": row[4],
            "sleep_hours": row[5],
            "sleep_quality": row[6],
            "menstrual_cycle_active": bool(row[7]),
            "menstrual_cycle_day": row[8],
            "latitude": row[9],
            "longitude": row[10],
            "humidity": row[11],
            "pollution": row[12],
            "stress": row[13],
            "products_used": row[14],
            "sunlight_exposure": row[15]
        }
        
        return timeseries_data
        
    except SQLiteError as e:
        raise SQLiteError(f"Failed to fetch timeseries data: {e}")
    except Exception as e:
        raise RuntimeError(f"Unexpected error while fetching timeseries data: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    try:
        setup_databases()
    except Exception as e:
        print(f"Error during database setup: {e}")