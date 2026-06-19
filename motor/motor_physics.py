import math
from motor.motor_params import MOTOR
from motor.motor_state import MotorState

def mechanical_power_kw(torque_nm, speed_rpm):
    omega = 2 * math.pi * speed_rpm / 60
    return (torque_nm * omega) / 1000

def back_emf_v(speed_rpm, ke=0.1):
    omega = 2 * math.pi * speed_rpm / 60
    return ke * omega

def copper_loss_w(current_a, resistance_ohm):
    return 3 * (current_a ** 2) * resistance_ohm

def iron_loss_w(flux, freq_hz):
    return 0.5 * (flux ** 2) * freq_hz

def mechanical_loss_w(speed_rpm, friction_coeff):
    omega = 2 * math.pi * speed_rpm / 60
    return friction_coeff * omega ** 2

def efficiency(pin_kw, pout_kw):
    if pin_kw <= 0:
        return 0.0
    return max(0.0, min(1.0, pout_kw / pin_kw))

def update_motor_physics(state: MotorState, dt_s: float = 0.1):
    state.power_kw = mechanical_power_kw(state.torque_nm, state.speed_rpm)
    eb = back_emf_v(state.speed_rpm)
    pcopper = copper_loss_w(state.current_a, MOTOR["stator_resistance_ohm"])
    piron = iron_loss_w(state.flux_estimate, max(state.speed_rpm / 60, 1))
    pmech = mechanical_loss_w(state.speed_rpm, MOTOR["friction_coeff_nm_per_radps"])
    total_loss_w = pcopper + piron + pmech
    pin_kw = state.power_kw + total_loss_w / 1000
    state.efficiency = efficiency(pin_kw, state.power_kw)
    return {
        "back_emf_v": eb,
        "pcopper_w": pcopper,
        "piron_w": piron,
        "pmech_w": pmech,
        "total_loss_w": total_loss_w,
        "pin_kw": pin_kw
    }

if __name__ == "__main__":
    s = MotorState(voltage_v=400, current_a=100, speed_rpm=6000, torque_nm=200, flux_estimate=0.8)
    result = update_motor_physics(s)
    print(s)
    print(result)