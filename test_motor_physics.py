from motor.motor_physics import MAX_SPEED_KMPH, update_motor_physics
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
        vehicle_speed_kmph=MAX_SPEED_KMPH,
        filtered_torque=100,
    )

    state = update_motor_physics(state, dt_s=0.1)

    assert state.vehicle_speed_kmph == MAX_SPEED_KMPH
    assert state.filtered_torque == 0


def test_peak_power_is_capped_like_real_ev_motor():
    state = MotorState(
        voltage_v=400,
        current_a=250,
        torque_nm=340,
        vehicle_speed_kmph=100,
        speed_rpm=7000,
        filtered_torque=340,
        battery_soc=100,
    )

    state = update_motor_physics(state, dt_s=0.5)

    assert state.power_kw <= 160.01
    assert state.current_a > 0
    assert 360 <= state.voltage_v <= 410


def test_full_acceleration_reaches_100_kmph_in_realistic_time_window():
    state = MotorState(voltage_v=400, battery_soc=100)
    elapsed_s = 0.0

    while state.vehicle_speed_kmph < 100 and elapsed_s < 20:
        state.torque_nm += (340 - state.torque_nm) * 0.28
        state = update_motor_physics(state, dt_s=0.5)
        elapsed_s += 0.5

    assert 6.0 <= elapsed_s <= 12.0
    assert state.vehicle_speed_kmph >= 100
    assert state.power_kw <= 160.01
