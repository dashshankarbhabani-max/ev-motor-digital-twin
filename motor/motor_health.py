# This file will convert:
"""
temperature,
vibration,
insulation condition,
cooling health,
and operating stress
into health scores.
"""
from motor.motor_params import MOTOR
from motor.motor_state import MotorState

def clamp(x, low=0.0, high=100.0):
    return max(low, min(high, x))

def update_motor_health(state: MotorState):
    stator_penalty = max(0, state.stator_temp_c - 80) * 0.2 + max(0, 1000 - state.insulation_resistance_mohm) * 0.01
    rotor_penalty = max(0, state.rotor_temp_c - 90) * 0.15 + state.current_harmonics * 2.0
    magnet_penalty = max(0, state.magnet_temp_c - 120) * 0.5
    bearing_penalty = max(0, state.bearing_temp_c - 70) * 0.1 + state.vibration_vel * 5.0
    cooling_penalty = max(0, 1.0 - state.coolant_flow_rate) * 30 + max(0, state.coolant_out_temp_c - state.coolant_in_temp_c) * 2.0
    shaft_penalty = max(0, state.vibration_accel - 1.0) * 3.0

    state.stator_health = clamp(100 - stator_penalty)
    state.rotor_health = clamp(100 - rotor_penalty)
    state.magnet_health = clamp(100 - magnet_penalty)
    state.bearing_health = clamp(100 - bearing_penalty)
    state.cooling_health = clamp(100 - cooling_penalty)
    state.shaft_health = clamp(100 - shaft_penalty)

    state.overall_health = (
        0.25 * state.stator_health +
        0.15 * state.rotor_health +
        0.15 * state.magnet_health +
        0.20 * state.bearing_health +
        0.15 * state.cooling_health +
        0.10 * state.shaft_health
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
        current_harmonics=3.0
    )
    s = update_motor_health(s)
    print(s)