from fastapi import FastAPI
from pydantic import BaseModel
from motor_service import run_motor_twin

app = FastAPI(
    title="EV Motor Digital Twin API",
    version="1.0"
)

class MotorInput(BaseModel):
    voltage_v: float
    current_a: float
    speed_rpm: float
    torque_nm: float
    flux_estimate: float

@app.get("/")
def home():
    return {"status": "Motor Digital Twin Running"}

@app.post("/predict")
def predict(data: MotorInput):

    return run_motor_twin(
        voltage_v=data.voltage_v,
        current_a=data.current_a,
        speed_rpm=data.speed_rpm,
        torque_nm=data.torque_nm,
        flux_estimate=data.flux_estimate
    )