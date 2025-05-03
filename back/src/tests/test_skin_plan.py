import json
import pytest

from fastapi.testclient import TestClient

# Import your FastAPI app
from api import app

# Import modules so we can monkey-patch
import solutions.medllama
import skin_plan_route
import api.profile as profile_module

client = TestClient(app)

@pytest.fixture(autouse=True)
def stub_out_db_and_model(monkeypatch):
    # 1) Stub get_profile_from_db to return a fake user profile
    monkeypatch.setattr(
        profile_module,
        "get_profile_from_db",
        lambda user_id: {
            "user_id": user_id,
            "sex": "female",
            "age": 30,
            "weight": 60.0,
            "previous_treatment": "none",
            "diet": "balanced"
        }
    )

    # 2) Stub fetch_latest_severity to return a fake severity record
    monkeypatch.setattr(
        skin_plan_route,
        "fetch_latest_severity",
        lambda db_path, user_id: {
            "disease": "acne",
            "severity_score": 42,
            "previous_treatment": "topical",
            "diet": "low sugar",
            "date": "2025-05-01"
        }
    )

    # 3) Stub the model call so it returns a predictable JSON string
    dummy_plan = {
        "treatment_plan": [
            {"date": "2025-05-02", "treatment": "gentle cleanser"},
            {"date": "2025-05-03", "treatment": "moisturizer"}
        ],
        "lifestyle_advice": ["Drink more water", "Avoid dairy"]
    }
    monkeypatch.setattr(
        medllama,
        "generate_skin_plan_from_json",
        lambda payload: json.dumps(dummy_plan)  # :contentReference[oaicite:0]{index=0}:contentReference[oaicite:1]{index=1}
    )

    yield

def test_skin_plan_endpoint_success():
    # Act: hit the endpoint
    resp = client.get("/skin-plan/test_user_123")
    assert resp.status_code == 200

    data = resp.json()
    # Assert: structure matches what our stubbed model returned
    assert "treatment_plan" in data
    assert isinstance(data["treatment_plan"], list)
    assert data["treatment_plan"][0]["treatment"] == "gentle cleanser"
    assert data["lifestyle_advice"] == ["Drink more water", "Avoid dairy"]

def test_skin_plan_endpoint_returns_json():
    resp = client.get("/skin-plan/anyone")
    # make sure it's valid JSON
    try:
        _ = resp.json()
    except ValueError:
        pytest.fail("Response is not valid JSON")
