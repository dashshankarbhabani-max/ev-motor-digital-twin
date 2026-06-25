from motor.motor_state import MotorState


def clamp(x, low=0.0, high=100.0):
    return max(low, min(high, x))


def _temp_penalty(temp_c, warm_c, hot_c, warm_weight, hot_weight):
    warm_penalty = max(0.0, temp_c - warm_c) * warm_weight
    hot_penalty = max(0.0, temp_c - hot_c) * hot_weight
    return warm_penalty + hot_penalty


def update_motor_health(state: MotorState):
    """Convert operating stress into subsystem health scores.

    This model is intentionally continuous: health starts moving before a
    hard fault trips, which makes the dashboard behave more like a live EV
    monitoring system instead of a binary threshold alarm.
    """
    current_stress = max(0.0, state.current_a - 180) * 0.035
    torque_stress = max(0.0, abs(state.torque_nm) - 220) * 0.018
    speed_stress = max(0.0, state.speed_rpm - 8000) * 0.0012
    cooling_delta = max(0.0, state.coolant_out_temp_c - state.coolant_in_temp_c)
    weak_cooling_penalty = max(0.0, 1.0 - state.coolant_flow_rate) * 30.0

    stator_penalty = (
        _temp_penalty(state.stator_temp_c, 65, 105, 0.18, 0.55)
        + max(0.0, 1000 - state.insulation_resistance_mohm) * 0.012
        + current_stress
        + torque_stress
    )
    rotor_penalty = (
        _temp_penalty(state.rotor_temp_c, 70, 105, 0.16, 0.45)
        + state.current_harmonics * 2.4
        + speed_stress
    )
    magnet_penalty = (
        _temp_penalty(state.magnet_temp_c, 85, 120, 0.20, 0.80)
        + current_stress * 0.35
    )
    bearing_penalty = (
        _temp_penalty(state.bearing_temp_c, 60, 85, 0.22, 0.75)
        + state.vibration_vel * 5.0
        + max(0.0, state.vibration_accel - 0.8) * 4.0
        + speed_stress * 0.6
    )
    cooling_penalty = (
        weak_cooling_penalty
        + cooling_delta * 1.6
        + max(0.0, state.stator_temp_c - 90) * 0.10
    )
    shaft_penalty = (
        max(0.0, state.vibration_accel - 0.8) * 5.0
        + max(0.0, abs(state.torque_nm) - 250) * 0.012
    )

    state.stator_health = clamp(100 - stator_penalty)
    state.rotor_health = clamp(100 - rotor_penalty)
    state.magnet_health = clamp(100 - magnet_penalty)
    state.bearing_health = clamp(100 - bearing_penalty)
    state.cooling_health = clamp(100 - cooling_penalty)
    state.shaft_health = clamp(100 - shaft_penalty)

    state.overall_health = clamp(
        0.25 * state.stator_health
        + 0.15 * state.rotor_health
        + 0.15 * state.magnet_health
        + 0.20 * state.bearing_health
        + 0.15 * state.cooling_health
        + 0.10 * state.shaft_health
    )

    return state


if __name__ == "__main__":
    s = MotorState(
        stator_temp_c=120,
        rotor_temp_c=100,
        magnet_temp_c=130,
        bearing_temp_c=85,
        coolant_flow_rate=0.4,
        coolant_in_temp_c=27,
        coolant_out_temp_c=45,
        vibration_accel=1.5,
        vibration_vel=2.0,
        insulation_resistance_mohm=800,
        current_harmonics=3.0,
    )
    s = update_motor_health(s)
    print(s)
