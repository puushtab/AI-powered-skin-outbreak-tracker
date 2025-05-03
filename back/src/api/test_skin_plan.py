#!/usr/bin/env python3
import os
import sys
import tempfile
import sqlite3
import json

# ────────────────────────────────────────────────────────────────
# 2) Import your app and helpers
# ────────────────────────────────────────────────────────────────
from fastapi.testclient import TestClient
import api  # this is your api.py :contentReference[oaicite:0]{index=0}:contentReference[oaicite:1]{index=1}
from api import DB_PATH as ORIGINAL_DB_PATH

# ────────────────────────────────────────────────────────────────
# 3) Helper to create a temp SQLite DB with a severity_log table
# ────────────────────────────────────────────────────────────────
def create_temp_db(records):
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    conn = sqlite3.connect(path)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE severity_log (
            user_id TEXT,
            severity_score INTEGER,
            disease TEXT,
            previous_treatment TEXT,
            diet TEXT,
            date TEXT
        )
    """)
    for rec in records:
        cur.execute(
            "INSERT INTO severity_log (user_id,severity_score,disease,previous_treatment,diet,date) VALUES (?, ?, ?, ?, ?, ?)",
            (rec["user_id"], rec["severity_score"], rec["disease"], rec["previous_treatment"], rec["diet"], rec["date"])
        )
    conn.commit()
    conn.close()
    return path

# ────────────────────────────────────────────────────────────────
# 4) Monkey‐patch in-script (no pytest)
# ────────────────────────────────────────────────────────────────
def run_tests():
    # --- stub profile ---
    def fake_get_profile(user_id):
        return {
            "user_id": user_id,
            "dob": "1995-05-15",
            "weight": 70,
            "gender": "female"
        }
    api.get_profile_from_db = fake_get_profile

    # --- stub model call ---
    dummy_plan = {
        "treatment_plan": [
            {"date": "2025-05-04", "treatment": "gentle cleanser"},
            {"date": "2025-05-05", "treatment": "sunscreen"}
        ],
        "lifestyle_advice": ["Stay hydrated"]
    }
    import solutions.medllama as medllama
    medllama.generate_skin_plan_from_json = lambda payload: json.dumps(dummy_plan)

    # --- prepare a temp DB with one severity record ---
    user = "user123"
    records = [{
        "user_id": user,
        "severity_score": 30,
        "disease": None,                # will fall back to "acne"
        "previous_treatment": None,
        "diet": "balanced",
        "date": "2025-05-02"
    }]
    tmp_db = create_temp_db(records)
    api.DB_PATH = tmp_db   # redirect your route’s DB_PATH

    # --- fire up TestClient and call the endpoint ---
    client = TestClient(api.app)
    resp = client.get(f"/skin-plan/{user}")
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    data = resp.json()

    # --- validate response matches our dummy_plan ---
    assert "treatment_plan" in data, "Missing 'treatment_plan'"
    assert data["treatment_plan"][0]["treatment"] == "gentle cleanser"
    assert data["lifestyle_advice"] == ["Stay hydrated"]

    print("✔ /skin-plan endpoint returned expected payload")

    # cleanup
    os.unlink(tmp_db)
    api.DB_PATH = ORIGINAL_DB_PATH

if __name__ == "__main__":
    try:
        run_tests()
        print("All tests passed!")
    except AssertionError as e:
        print("TEST FAILED:", e)
        sys.exit(1)
