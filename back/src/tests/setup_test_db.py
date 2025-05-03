import os
import sys
from pathlib import Path

# Add the parent directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from db.create_db import setup_databases, create_timeseries_table, create_profiles_table
from db.user_profile_db import save_profile_to_db, init_db

def setup_test_environment():
    """Set up the test environment with necessary databases and sample data"""
    try:
        # Create the databases in the correct location
        db_dir = Path(__file__).parent.parent / "db"
        timeseries_db_path = db_dir / "acne_tracker.db"
        profiles_db_path = db_dir / "user_profiles.db"
        
        # Create the databases
        setup_databases(str(timeseries_db_path), str(profiles_db_path))
        
        # Initialize the user_profiles table
        init_db(str(profiles_db_path))
        
        # Add test user
        test_user = {
            "user_id": "test_user_1",
            "name": "Test User One",
            "dob": "1995-05-03",
            "height": 175,
            "weight": 70,
            "gender": "Male"
        }
        
        save_profile_to_db(
            user_id=test_user["user_id"],
            name=test_user["name"],
            dob=test_user["dob"],
            height=test_user["height"],
            weight=test_user["weight"],
            gender=test_user["gender"],
            db_path=str(profiles_db_path)
        )
        
        print("Test environment setup completed successfully!")
        
    except Exception as e:
        print(f"Error setting up test environment: {e}")
        sys.exit(1)

if __name__ == "__main__":
    setup_test_environment() 