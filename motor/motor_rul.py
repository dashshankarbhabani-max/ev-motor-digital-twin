from motor.motor_state import MotorState


def update_rul(state: MotorState, dt_hours=1 / 3600):
    """
    Realistic EV motor RUL model.

    Healthy motor:
        15,000–20,000 hours.

    RUL decreases slowly with:
        - high temperatures
        - vibration
        - poor health
        - faults
    """

    # initialize once
    if state.rul_hours <= 0:
        state.rul_hours = 20000.0

    degradation = 0.001

    # temperature stress
    if state.stator_temp_c > 90:
        degradation += 0.02

    if state.bearing_temp_c > 80:
        degradation += 0.02

    # vibration stress
    if state.vibration_vel > 5:
        degradation += 0.03

    # health stress
    degradation += (100 - state.overall_health) * 0.0005

    # fault stress
    degradation += state.failure_probability * 0.001

    # reduce slowly
    state.rul_hours -= degradation * dt_hours

    if state.rul_hours < 0:
        state.rul_hours = 0

    return state