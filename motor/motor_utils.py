import joblib
import os
from motor.motor_state import MotorState

BASE_DIR = os.path.dirname(__file__)
feature_columns = joblib.load(os.path.join(BASE_DIR, "..", "models", "feature_columns.pkl"))


def extract_features(state: MotorState):

    feature_map = {
        "voltage_v": state.voltage_v,
        "current_a": state.current_a,
        "speed_rpm": state.speed_rpm,
        "torque_nm": state.torque_nm,
        "power_kw": state.power_kw,
        "efficiency": state.efficiency,
        "back_emf_v": state.back_emf_v,

        "stator_temp_c": state.stator_temp_c,
        "rotor_temp_c": state.rotor_temp_c,
        "magnet_temp_c": state.magnet_temp_c,
        "bearing_temp_c": state.bearing_temp_c,

        "coolant_flow_rate": state.coolant_flow_rate,
        "vibration_accel": state.vibration_accel,
        "vibration_vel": state.vibration_vel,

        "insulation_resistance_mohm": state.insulation_resistance_mohm,
        "partial_discharge": state.partial_discharge,
        "flux_estimate": state.flux_estimate,
        "current_harmonics": state.current_harmonics,

        "stator_health": state.stator_health,
        "rotor_health": state.rotor_health,
        "magnet_health": state.magnet_health,
        "bearing_health": state.bearing_health,
        "overall_health": state.overall_health,

        "failure_probability": state.failure_probability,
        "rul_hours": state.rul_hours
    }

    # 🔥 ALIGN TO TRAINING ORDER
    return [feature_map[col] for col in feature_columns if col in feature_map]