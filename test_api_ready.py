import os

from fastapi.testclient import TestClient

from api import app


os.environ["APP_API_KEY"] = "test-secret-key"
client = TestClient(app)
payload = {
    "voltage_v": 400,
    "current_a": 100,
    "speed_rpm": 6000,
    "torque_nm": 200,
    "flux_estimate": 0.8,
}


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
