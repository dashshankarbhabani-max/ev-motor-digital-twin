from motor.motor_physics import update_motor_physics
from motor.motor_state import MotorState


def test_positive_torque_accelerates_motor_and_generates_power():
    state = MotorState(
        voltage_v=400,
        current_a=140,
        torque_nm=100,
        flux_estimate=0.8,
        battery_soc=100,
    )

    for _ in range(100):
        state = update_motor_physics(state, dt_s=0.1)

    assert state.filtered_torque > 0
    assert state.vehicle_speed_kmph > 0
    assert state.speed_rpm > 0
    assert state.power_kw > 0
    assert state.efficiency > 0
    assert state.battery_soc < 100


def test_top_speed_limiter_stops_positive_acceleration():
    state = MotorState(
        voltage_v=400,
        current_a=140,
        torque_nm=100,
        vehicle_speed_kmph=105,
        filtered_torque=100,
    )

    state = update_motor_physics(state, dt_s=0.1)

    assert state.vehicle_speed_kmph == 105
    assert state.filtered_torque == 0
