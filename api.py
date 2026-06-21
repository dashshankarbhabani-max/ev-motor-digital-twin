import os
import secrets

from fastapi import (
    FastAPI,
    Depends,
    Header,
    HTTPException,
    status
)

from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from motor_service import run_motor_twin


# ====================================================
# APP
# ====================================================
app = FastAPI(
    title="EV Motor Digital Twin API",
    version="2.0.0"
)


# ====================================================
# CORS
# ====================================================
app.add_middleware(
    CORSMiddleware,

    # Development mode
    allow_origins=["*"],

    allow_credentials=False,

    allow_methods=["*"],

    allow_headers=["*"],

    expose_headers=["*"]
)


# ====================================================
# INPUT MODEL
# ====================================================
class MotorInput(BaseModel):

    voltage_v: float = Field(400.0, ge=0)

    current_a: float = Field(0.0, ge=0)

    speed_rpm: float = Field(0.0, ge=0)

    torque_nm: float = Field(0.0)

    flux_estimate: float = Field(0.8, ge=0)

    vehicle_speed_kmph: float = Field(0.0, ge=0)

    battery_soc: float = Field(
        100.0,
        ge=0,
        le=100
    )

    coolant_flow_rate: float = Field(
        1.0,
        ge=0
    )

    vibration_accel: float = Field(
        0.5,
        ge=0
    )

    vibration_vel: float = Field(
        1.0,
        ge=0
    )

    current_harmonics: float = Field(
        0.0,
        ge=0
    )

    insulation_resistance_mohm: float = Field(
        1000.0,
        ge=0
    )

    partial_discharge: float = Field(
        0.0,
        ge=0
    )

    rul_hours: float = Field(
        20000.0,
        ge=0
    )


# ====================================================
# API KEY SECURITY
# ====================================================
def require_api_key(
    x_api_key: str | None = Header(
        default=None,
        alias="X-API-Key"
    )
):

    expected_key = os.getenv(
        "APP_API_KEY"
    )

    if not expected_key:

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="APP_API_KEY is not configured on server"
        )

    if (
        not x_api_key
        or not secrets.compare_digest(
            x_api_key,
            expected_key
        )
    ):

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key"
        )


# ====================================================
# ROOT
# ====================================================
@app.get("/")
def home():

    return {

        "status":
        "EV Motor Digital Twin API is running",

        "version":
        "2.0.0"
    }


# ====================================================
# HEALTH
# ====================================================
@app.get("/health")
def health():

    return {

        "status":
        "healthy"
    }


# ====================================================
# PREDICT
# ====================================================
@app.post(
    "/predict",
    dependencies=[Depends(require_api_key)]
)
def predict(
    data: MotorInput
):

    result = run_motor_twin(
        **data.model_dump()
    )

    return result


# ====================================================
# INFO
# ====================================================
@app.get("/info")
def info():

    return {

        "name":
        "EV Motor Digital Twin API",

        "version":
        "2.0.0",

        "authentication":
        "X-API-Key header required",

        "endpoint":
        "/predict"
    }
