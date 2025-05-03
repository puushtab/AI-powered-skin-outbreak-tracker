#!/usr/bin/env python3
import os
import sqlite3
import tempfile
import json
#!/usr/bin/env python3
import os
import sys

from api import fetch_latest_severity, DB_PATH as ORIGINAL_DB_PATH


def create_temp_db(records):
    """
    Create a temporary SQLite DB with a severity_log table,
    insert `records`, and return the path to the file.
    Each record is a dict with keys:
      user_id, severity_score, disease, previous_treatment, diet, date
    """
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
            "INSERT INTO severity_log (user_id, severity_score, disease, previous_treatment, diet, date) VALUES (?, ?, ?, ?, ?, ?)",
            (rec["user_id"], rec["severity_score"], rec["disease"], rec["previous_treatment"], rec["diet"], rec["date"])
        )
    conn.commit()
    conn.close()
    return path

def run_tests():
    # 1) Test with existing records
    user = "test_user"
    records = [
        {"user_id": user, "severity_score": 5, "disease": "eczema",    "previous_treatment": "cream", "diet": "high sugar", "date": "2025-01-01"},
        {"user_id": user, "severity_score": 8, "disease": None,        "previous_treatment": None,    "diet": "low carb",   "date": "2025-04-01"},
    ]
    tmp_db = create_temp_db(records)
    # Redirect the module's DB_PATH to our temp file
    import api
    api.DB_PATH = tmp_db

    result = fetch_latest_severity(user)
    # Assertions:
    assert result["severity_score"] == 8,             f"Expected 8, got {result['severity_score']}"
    assert result["disease"] == "acne",               f"Expected fallback 'acne', got {result['disease']}"
    assert result["previous_treatment"] == "",        f"Expected '', got {result['previous_treatment']}"
    assert result["diet"] == "low carb",              f"Expected 'low carb', got {result['diet']}"
    print("✔ fetch_latest_severity with records: PASS")
    os.unlink(tmp_db)

    # 2) Test with no records
    tmp_db2 = create_temp_db([])
    api.DB_PATH = tmp_db2

    result2 = fetch_latest_severity("no_such_user")
    expected = {"severity_score": 50, "disease": "acne", "previous_treatment": "", "diet": ""}
    assert result2 == expected, f"Expected defaults {expected}, got {result2}"
    print("✔ fetch_latest_severity with no records: PASS")
    os.unlink(tmp_db2)

    # Restore original DB_PATH
    api.DB_PATH = ORIGINAL_DB_PATH

if __name__ == "__main__":
    try:
        run_tests()
        print("\nAll tests passed!")
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        exit(1)
