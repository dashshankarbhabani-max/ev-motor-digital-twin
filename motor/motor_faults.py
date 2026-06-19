from motor.motor_state import MotorState

def clamp(x, low=0.0, high=100.0):
    return max(low, min(high, x))

def update_faults(state: MotorState):
    fault_score = 0.0
    fault_code = "NONE"

    if state.stator_temp_c > 140:
        fault_score += 20
        fault_code = "M001_STATOR_OVERHEAT"

    if state.insulation_resistance_mohm < 500:
        fault_score += 25
        fault_code = "M004_INSULATION_BREAKDOWN"

    if state.current_harmonics > 5:
        fault_score += 15
        fault_code = "M005_CURRENT_IMBALANCE"

    if state.magnet_temp_c > 150:
        fault_score += 30
        fault_code = "M201_PARTIAL_DEMAGNETIZATION"

    if state.bearing_temp_c > 100 or state.vibration_vel > 4.5:
        fault_score += 30
        fault_code = "M301_BEARING_FAULT"

    if state.coolant_flow_rate < 0.5:
        fault_score += 25
        fault_code = "M401_COOLING_FAILURE"

    state.failure_probability = clamp(fault_score)
    state.fault_code = fault_code
    return state

if __name__ == "__main__":
    s = MotorState(
        stator_temp_c=145,
        magnet_temp_c=155,
        bearing_temp_c=105,
        vibration_vel=5.0,
        coolant_flow_rate=0.3,
        insulation_resistance_mohm=400,
        current_harmonics=6.0
    )
    s = update_faults(s)
    print(s)