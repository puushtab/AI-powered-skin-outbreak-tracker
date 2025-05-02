import sqlite3
from typing import Optional, Tuple, Dict
from datetime import date
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "../tsa/acne_tracker.db")


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_profiles (
            user_id TEXT PRIMARY KEY,
            name TEXT,
            dob TEXT,
            height REAL,
            weight REAL,
            gender TEXT
        )
    ''')
    conn.commit()
    conn.close()


def save_profile_to_db(user_id: str, name: str, dob: str, height: float, weight: float, gender: str):
    conn = sqlite3.connect(DB_PATH)
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


def get_profile_from_db(user_id: str) -> Optional[Dict]:
    conn = sqlite3.connect(DB_PATH)
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
