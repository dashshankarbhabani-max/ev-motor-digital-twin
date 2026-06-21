import os
import secrets

from fastapi import Depends, FastAPI, Header, HTTPException, status
from pydantic import BaseModel, Field

from motor_service import run_motor_twin


app = FastAPI(title="EV Motor Digital Twin API", version="2.0.0")


class MotorInput(BaseModel):
    voltage_v: float = Field(400.0, ge=0)
    current_a: float = Field(0.0, ge=0)
    speed_rpm: float = Field(0.0, ge=0)
    torque_nm: float = 0.0
    flux_estimate: float = Field(0.8, ge=0)
    vehicle_speed_kmph: float = Field(0.0, ge=0)
    battery_soc: float = Field(100.0, ge=0, le=100)
    coolant_flow_rate: float = Field(1.0, ge=0)
    vibration_accel: float = Field(0.5, ge=0)
    vibration_vel: float = Field(1.0, ge=0)
    current_harmonics: float = Field(0.0, ge=0)
    insulation_resistance_mohm: float = Field(1000.0, ge=0)
    partial_discharge: float = Field(0.0, ge=0)
    stator_temp_c: float = 25.0
    rotor_temp_c: float = 25.0
    magnet_temp_c: float = 25.0
    bearing_temp_c: float = 25.0
    coolant_in_temp_c: float = 25.0
    coolant_out_temp_c: float = 25.0
    rul_hours: float = Field(20000.0, ge=0)


def require_api_key(x_api_key: str | None = Header(default=None, alias="X-API-Key")):
    expected_key = os.getenv("APP_API_KEY")
    if not expected_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="APP_API_KEY is not configured on the server",
        )
    if not x_api_key or not secrets.compare_digest(x_api_key, expected_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )


@app.get("/")
def home():
    return {"status": "EV Motor Digital Twin API is running", "version": "2.0.0"}


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/predict", dependencies=[Depends(require_api_key)])
def predict(data: MotorInput):
    return run_motor_twin(**data.model_dump())
