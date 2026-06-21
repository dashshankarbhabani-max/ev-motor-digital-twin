import pytest
from fastapi.testclient import TestClient

from api import app


client = TestClient(app)
payload = {
    "voltage_v": 400,
    "current_a": 100,
    "speed_rpm": 6000,
    "torque_nm": 200,
    "flux_estimate": 0.8,
}


@pytest.fixture(autouse=True)
def configured_test_key(monkeypatch):
    monkeypatch.setenv("APP_API_KEY", "test-secret-key")


def test_predict_rejects_missing_api_key():
    assert client.post("/predict", json=payload).status_code == 401


def test_predict_uses_local_model():
    response = client.post(
        "/predict",
        json=payload,
        headers={"X-API-Key": "test-secret-key"},
    )
    assert response.status_code == 200
    result = response.json()
    assert "motor_state" in result
    assert "ml_prediction" in result
    assert "fault_code" in result["ml_prediction"]


def test_predict_uses_live_thermal_state_for_fault_and_rul():
    hot_motor = {
        **payload,
        "stator_temp_c": 145,
        "rotor_temp_c": 110,
        "magnet_temp_c": 155,
        "bearing_temp_c": 105,
        "vibration_vel": 1,
    }
    response = client.post(
        "/predict",
        json=hot_motor,
        headers={"X-API-Key": "test-secret-key"},
    )
    assert response.status_code == 200
    result = response.json()
    assert result["motor_state"]["failure_probability"] >= 80
    assert result["motor_state"]["rul_hours"] < 5000
    assert result["ml_prediction"]["failure_probability"] >= 80
    assert result["ml_prediction"]["fault_code"] != "NONE"
    assert result["ml_prediction"]["diagnosis_source"] == "safety_rules"
