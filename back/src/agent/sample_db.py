import sqlite3
from datetime import datetime, timedelta
import uuid

# Connect to SQLite database
conn = sqlite3.connect('acne_tracker.db')
c = conn.cursor()

# Create timeseries table
c.execute('''
    CREATE TABLE IF NOT EXISTS timeseries (
        id TEXT PRIMARY KEY,
        timestamp TEXT,
        acne_severity_score REAL,
        diet_sugar REAL,
        diet_dairy REAL,
        diet_alcohol REAL,
        sleep_hours REAL,
        sleep_quality TEXT,
        menstrual_cycle_active INTEGER,
        menstrual_cycle_day INTEGER,
        latitude REAL,
        longitude REAL,
        humidity REAL,
        pollution REAL,
        stress REAL,
        products_used TEXT,
        sunlight_exposure REAL
    )
''')

# Insert sample data (14 days, 1 entry per day)
base_date = datetime.now() - timedelta(days=14)
sample_data = [
    # Week 1: Lower acne severity, varying factors
    (str(uuid.uuid4()), (base_date + timedelta(days=i)).isoformat(), 
     3.0 + i * 0.2,  # Increasing acne severity
     20 + i,  # Sugar (grams)
     50 + i * 2,  # Dairy (grams)
     i % 3,  # Alcohol (units)
     7 - i * 0.1,  # Sleep hours
     'average',  # Sleep quality
     1 if i % 2 == 0 else 0,  # Menstrual cycle active
     (i % 28) + 1,  # Menstrual cycle day
     40.71, -74.01,  # New York coordinates
     60 + i * 2,  # Humidity (%)
     50 + i,  # Pollution (AQI)
     4 + i * 0.5,  # Stress (0-10)
     'sunscreen,face wash',  # Products used
     2 + i * 0.2)  # Sunlight exposure (hours)
    for i in range(14)
]

# Insert data
c.executemany('''
    INSERT INTO timeseries VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
''', sample_data)

conn.commit()
conn.close()
print("Sample database created and populated.")