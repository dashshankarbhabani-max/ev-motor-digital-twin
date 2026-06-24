from motor.agent_policy import AGENTIC_AI_ON
from motor.genai_supervisor import run_guardian_cycle
from motor.motor_faults import update_faults
from motor.motor_health import update_motor_health
from motor.motor_physics import update_motor_physics
from motor.motor_rul import update_rul
from motor.motor_state import MotorState
from motor.motor_thermal import update_motor_thermal


def test_hot_motor_cools_when_cooling_flow_is_high_and_load_is_low():
    state = MotorState(
        stator_temp_c=130,
        rotor_temp_c=110,
        magnet_temp_c=125,
        bearing_temp_c=90,
        coolant_flow_rate=3.0,
    )

    for _ in range(10):
        state = update_motor_thermal(state, loss_w=500, dt_s=1.0)

    assert state.stator_temp_c < 125
    assert state.rotor_temp_c < 108
    assert state.bearing_temp_c < 86


def test_agentic_ai_reduces_temperature_during_overheating():
    state = MotorState(
        voltage_v=400,
        battery_soc=100,
        stator_temp_c=130,
        rotor_temp_c=115,
        magnet_temp_c=135,
        bearing_temp_c=95,
        coolant_flow_rate=1.0,
        vehicle_speed_kmph=60,
        failure_probability=75,
        fault_code="M001_STATOR_OVERHEAT",
    )
    starting_temp = state.stator_temp_c

    for _ in range(20):
        guardian = run_guardian_cycle(state, 100, 0, AGENTIC_AI_ON, 1.0)
        state.torque_nm += (
            guardian["controls"]["target_torque_nm"] - state.torque_nm
        ) * 0.28
        state = update_motor_physics(state, dt_s=1.0)
        state = update_motor_thermal(state, state.total_loss_w, dt_s=1.0)
        state = update_motor_health(state)
        state = update_faults(state)
        state = update_rul(state, dt_hours=1.0 / 3600)

    assert state.coolant_flow_rate > 2.5
    assert state.torque_limit_pct <= 45
    assert state.stator_temp_c < starting_temp - 15
