from motor.agent_policy import AGENTIC_AI_OFF, AGENTIC_AI_ON
from motor.genai_supervisor import run_guardian_cycle
from motor.motor_physics import update_motor_physics
from motor.motor_state import MotorState
from motor.motor_thermal import update_motor_thermal


def test_simultaneous_accelerator_and_brake_warns_and_blocks_acceleration():
    state = MotorState(vehicle_speed_kmph=30, coolant_flow_rate=1.0)

    result = run_guardian_cycle(
        state,
        accelerator_pct=60,
        brake_pct=35,
        agentic_ai_selection=AGENTIC_AI_ON,
        dt_s=0.1,
    )

    warning_titles = {warning["title"] for warning in result["warnings"]}
    action_types = {action["type"] for action in result["actions"] if action["allowed"]}

    assert "Accelerator and brake pressed together" in warning_titles
    assert "block_acceleration_while_braking" in action_types
    assert result["controls"]["effective_accelerator_pct"] == 0
    assert result["controls"]["target_torque_nm"] < 0


def test_protective_guardian_prevents_overheating_with_derating_and_cooling():
    state = MotorState(
        stator_temp_c=130,
        rotor_temp_c=118,
        magnet_temp_c=138,
        bearing_temp_c=96,
        coolant_flow_rate=1.0,
        vehicle_speed_kmph=70,
        failure_probability=75,
        fault_code="M001_STATOR_OVERHEAT",
    )

    result = run_guardian_cycle(
        state,
        accelerator_pct=100,
        brake_pct=0,
        agentic_ai_selection=AGENTIC_AI_ON,
        dt_s=0.1,
    )

    assert result["controls"]["torque_limit_pct"] <= 25
    assert result["controls"]["coolant_flow_rate"] > 1.0
    assert result["controls"]["speed_limit_kmph"] <= 35
    assert result["controls"]["target_torque_nm"] <= 50
    assert result["controls"]["limp_mode_active"] is True


def test_agentic_ai_off_warns_without_applying_control():
    state = MotorState(stator_temp_c=130, coolant_flow_rate=1.0)

    result = run_guardian_cycle(
        state,
        accelerator_pct=100,
        brake_pct=0,
        agentic_ai_selection=AGENTIC_AI_OFF,
        dt_s=0.1,
    )

    assert result["warnings"]
    assert result["actions"] == []
    assert result["controls"]["torque_limit_pct"] == 100
    assert result["controls"]["speed_limit_kmph"] == 150


def test_thermal_emergency_stop_gives_reminder_and_ramps_speed_down():
    state = MotorState(
        vehicle_speed_kmph=80,
        stator_temp_c=155,
        rotor_temp_c=130,
        magnet_temp_c=140,
        bearing_temp_c=100,
    )

    first = run_guardian_cycle(state, 100, 0, AGENTIC_AI_ON, 1.0)
    first_target = state.thermal_shutdown_target_speed_kmph
    second = run_guardian_cycle(state, 100, 0, AGENTIC_AI_ON, 1.0)

    action_types = {action["type"] for action in second["actions"] if action["allowed"]}

    assert state.thermal_shutdown_active is True
    assert "thermal_emergency_stop" in action_types
    assert "Thermal emergency" in state.thermal_shutdown_reminder
    assert state.thermal_shutdown_target_speed_kmph < first_target
    assert second["controls"]["effective_accelerator_pct"] == 0
    assert second["controls"]["effective_brake_pct"] > 0


def test_thermal_emergency_stop_finally_stops_the_car():
    state = MotorState(
        voltage_v=400,
        battery_soc=100,
        vehicle_speed_kmph=80,
        stator_temp_c=155,
        rotor_temp_c=130,
        magnet_temp_c=140,
        bearing_temp_c=100,
        coolant_flow_rate=1.0,
    )

    for _ in range(30):
        guardian = run_guardian_cycle(state, 100, 0, AGENTIC_AI_ON, 1.0)
        state.torque_nm += (
            guardian["controls"]["target_torque_nm"] - state.torque_nm
        ) * 0.28
        state = update_motor_physics(state, dt_s=1.0)
        state = update_motor_thermal(state, state.total_loss_w, dt_s=1.0)

    assert state.vehicle_speed_kmph == 0
    assert state.thermal_shutdown_complete is True
    assert state.thermal_shutdown_target_speed_kmph == 0
