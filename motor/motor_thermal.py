import math
from motor.motor_params import MOTOR
from motor.motor_state import MotorState

def update_motor_thermal(state: MotorState, loss_w: float, dt_s: float = 0.1):
    ambient = MOTOR["ambient_temp_c"]
    thermal_mass = 800.0
    cooling_coeff = 0.04

    temp_rise = (loss_w / thermal_mass) * dt_s
    cooling_drop = cooling_coeff * (state.coolant_flow_rate + 1.0) * dt_s

    state.stator_temp_c += temp_rise - cooling_drop
    state.rotor_temp_c += 0.7 * temp_rise - 0.5 * cooling_drop
    state.magnet_temp_c += 0.6 * temp_rise - 0.3 * cooling_drop
    state.bearing_temp_c += 0.5 * temp_rise - 0.2 * cooling_drop

    state.coolant_in_temp_c = ambient + 2.0
    state.coolant_out_temp_c = ambient + 2.0 + loss_w / 10000.0

    state.stator_temp_c = max(ambient, state.stator_temp_c)
    state.rotor_temp_c = max(ambient, state.rotor_temp_c)
    state.magnet_temp_c = max(ambient, state.magnet_temp_c)
    state.bearing_temp_c = max(ambient, state.bearing_temp_c)

    return state

if __name__ == "__main__":
    s = MotorState(coolant_flow_rate=1.0)
    s = update_motor_thermal(s, 12000)
    print(s)