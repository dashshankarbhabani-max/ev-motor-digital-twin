from motor.motor_state import MotorState


def clamp(x, low=0.0, high=100.0):
    return max(low, min(high, x))


def _risk(value, start, critical, weight):
    if value <= start:
        return 0.0
    span = max(critical - start, 1e-6)
    return min(1.0, (value - start) / span) * weight


def _set_fault(candidates, score, code):
    candidates.append((score, code))


def update_faults(state: MotorState):
    """Estimate failure probability continuously and assign hard fault codes."""
    risk_score = 0.0
    fault_candidates = []

    stator_risk = _risk(state.stator_temp_c, 80, 150, 26)
    rotor_risk = _risk(state.rotor_temp_c, 85, 135, 16)
    magnet_risk = _risk(state.magnet_temp_c, 95, 145, 26)
    bearing_risk = _risk(state.bearing_temp_c, 70, 110, 24)
    vibration_risk = _risk(state.vibration_vel, 1.5, 4.5, 20)
    cooling_risk = _risk(1.0 - state.coolant_flow_rate, 0.05, 0.65, 18)
    insulation_risk = _risk(1000 - state.insulation_resistance_mohm, 100, 550, 22)
    harmonic_risk = _risk(state.current_harmonics, 2.0, 6.0, 14)
    health_risk = _risk(100 - state.overall_health, 3.0, 35.0, 18)

    risk_score += (
        stator_risk
        + rotor_risk
        + magnet_risk
        + bearing_risk
        + vibration_risk
        + cooling_risk
        + insulation_risk
        + harmonic_risk
        + health_risk
    )

    # Operating stress raises risk before a fault becomes critical.
    risk_score += _risk(state.current_a, 180, 450, 8)
    risk_score += _risk(abs(state.torque_nm), 220, 340, 6)

    if state.stator_temp_c > 140:
        risk_score += 20
        _set_fault(fault_candidates, state.stator_temp_c, "M001_STATOR_OVERHEAT")

    if state.insulation_resistance_mohm < 500:
        risk_score += 25
        _set_fault(
            fault_candidates,
            1000 - state.insulation_resistance_mohm,
            "M004_INSULATION_BREAKDOWN",
        )

    if state.current_harmonics > 5:
        risk_score += 15
        _set_fault(
            fault_candidates,
            state.current_harmonics,
            "M005_CURRENT_IMBALANCE",
        )

    if state.magnet_temp_c > 140:
        risk_score += 25
        _set_fault(
            fault_candidates,
            state.magnet_temp_c,
            "M201_PARTIAL_DEMAGNETIZATION",
        )

    if state.bearing_temp_c > 100 or state.vibration_vel > 4.5:
        risk_score += 30
        _set_fault(
            fault_candidates,
            max(state.bearing_temp_c, state.vibration_vel * 25),
            "M301_BEARING_FAULT",
        )

    if state.coolant_flow_rate < 0.5:
        risk_score += 25
        _set_fault(fault_candidates, 1 - state.coolant_flow_rate, "M401_COOLING_FAILURE")

    state.failure_probability = clamp(risk_score)
    if fault_candidates:
        state.fault_code = max(fault_candidates, key=lambda item: item[0])[1]
    else:
        state.fault_code = "NONE"

    return state


if __name__ == "__main__":
    s = MotorState(
        stator_temp_c=95,
        bearing_temp_c=80,
        vibration_vel=2.0,
        coolant_flow_rate=1.0,
    )
    print(update_faults(s))
