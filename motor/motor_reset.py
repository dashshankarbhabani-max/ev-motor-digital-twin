from motor.motor_state import MotorState


def create_fresh_state():
    state = MotorState()

    state.voltage_v = 400.0
    state.current_a = 0.0
    state.speed_rpm = 0.0
    state.torque_nm = 0.0
    state.power_kw = 0.0
    state.efficiency = 0.0
    state.back_emf_v = 0.0

    state.stator_temp_c = 25.0
    state.rotor_temp_c = 25.0
    state.magnet_temp_c = 25.0
    state.bearing_temp_c = 25.0

    state.coolant_in_temp_c = 25.0
    state.coolant_out_temp_c = 25.0
    state.coolant_flow_rate = 1.0

    state.vibration_accel = 0.5
    state.vibration_vel = 1.0

    state.flux_estimate = 0.8

    state.overall_health = 100.0
    state.failure_probability = 0.0
    state.rul_hours = 200000.0

    state.filtered_torque = 0.0
    state.initialized = True

    return state