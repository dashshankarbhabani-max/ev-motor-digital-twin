from dataclasses import asdict

from motor.feature_extractor import extract_features
from motor.motor_ai import predict_motor_health
from motor.motor_faults import update_faults
from motor.motor_health import update_motor_health
from motor.motor_physics import update_motor_physics
from motor.motor_rul import update_rul
from motor.motor_state import MotorState
from motor.motor_thermal import update_motor_thermal


def run_motor_twin(**values):
    state = MotorState(**values)
    state = update_motor_physics(state, dt_s=0.1)
    state = update_motor_thermal(state, state.total_loss_w, dt_s=0.1)
    state = update_motor_health(state)
    state = update_faults(state)
    state = update_rul(state, dt_hours=0.1 / 3600)
    prediction = predict_motor_health(extract_features(state))

    return {"motor_state": asdict(state), "ml_prediction": prediction}
