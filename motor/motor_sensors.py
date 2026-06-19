import math
import random
from motor.motor_state import MotorState

random.seed(42)


def clamp(x, lo, hi):
    return max(lo, min(hi, x))


def add_noise(value, pct):
    sigma = max(abs(value) * pct, 1e-9)
    return value + random.gauss(0, sigma)


def back_emf(speed_rpm, ke=0.6):
    omega = speed_rpm * 2 * math.pi / 60.0
    return ke * omega


def estimated_current(voltage_v, speed_rpm, resistance_ohm=2.5, ke=0.6):
    eb = back_emf(speed_rpm, ke)
    return max((voltage_v - eb) / resistance_ohm, 0.0)


def estimated_torque(current_a, kt=1.0):
    return kt * current_a


def estimated_vibration(bearing_health, speed_rpm, imbalance=1.0):
    base = 0.02 + 0.0000015 * speed_rpm
    wear_factor = (1.0 - clamp(bearing_health / 100.0, 0.0, 1.0)) * 0.12
    return base + wear_factor + 0.01 * imbalance


def estimated_temperature(prev_temp_c, loss_w, ambient_c=25.0, thermal_mass=5000.0, cooling_coeff=8.0, dt=1.0):
    heat_in = loss_w * dt / thermal_mass
    heat_out = cooling_coeff * max(prev_temp_c - ambient_c, 0.0) * dt / thermal_mass
    return max(prev_temp_c + heat_in - heat_out, ambient_c)


def simulate_sensors(state: MotorState):
    current_true = estimated_current(state.voltage_v, state.speed_rpm)
    torque_true = estimated_torque(current_true)
    emf_true = back_emf(state.speed_rpm)
    vib_true = estimated_vibration(state.bearing_health, state.speed_rpm)

    stator_loss = 0.45 * current_true * current_true * 2.5
    rotor_loss = 0.20 * current_true * current_true * 2.5
    magnet_loss = 0.10 * current_true * current_true * 2.5
    bearing_loss = 0.05 * current_true * current_true * 2.5

    stator_temp = estimated_temperature(state.stator_temp_c, stator_loss, cooling_coeff=18.0, thermal_mass=7000.0)
    rotor_temp = estimated_temperature(state.rotor_temp_c, rotor_loss, cooling_coeff=16.0, thermal_mass=8000.0)
    magnet_temp = estimated_temperature(state.magnet_temp_c, magnet_loss, cooling_coeff=14.0, thermal_mass=9000.0)
    bearing_temp = estimated_temperature(state.bearing_temp_c, bearing_loss, cooling_coeff=12.0, thermal_mass=10000.0)

    voltage_meas = max(add_noise(state.voltage_v, 0.003), 0.0)
    current_meas = max(add_noise(current_true, 0.01), 0.0)
    speed_meas = max(add_noise(state.speed_rpm, 0.002), 0.0)
    torque_meas = max(add_noise(torque_true, 0.01), 0.0)
    emf_meas = max(add_noise(emf_true, 0.01), 0.0)

    power_kw = max((voltage_meas * current_meas) / 1000.0, 0.0)
    mech_power = torque_meas * speed_meas * 2 * math.pi / 60.0
    efficiency = 0.0 if voltage_meas * current_meas <= 0 else clamp(mech_power / (voltage_meas * current_meas), 0.0, 1.0)

    return {
        "voltage_v": voltage_meas,
        "current_a": current_meas,
        "speed_rpm": speed_meas,
        "torque_nm": torque_meas,
        "power_kw": power_kw,
        "efficiency": efficiency,
        "back_emf_v": emf_meas,
        "stator_temp_c": max(add_noise(stator_temp, 0.003), 25.0),
        "rotor_temp_c": max(add_noise(rotor_temp, 0.003), 25.0),
        "magnet_temp_c": max(add_noise(magnet_temp, 0.003), 25.0),
        "bearing_temp_c": max(add_noise(bearing_temp, 0.003), 25.0),
        "coolant_in_temp_c": max(add_noise(state.coolant_in_temp_c, 0.002), 0.0),
        "coolant_out_temp_c": max(add_noise(state.coolant_out_temp_c, 0.002), 0.0),
        "vibration_accel": max(add_noise(vib_true, 0.02), 0.0),
        "vibration_vel": max(add_noise(vib_true * 10.0, 0.02), 0.0),
        "coolant_flow_rate": max(add_noise(state.coolant_flow_rate, 0.01), 0.0),
        "coolant_pressure": max(add_noise(state.coolant_pressure, 0.01), 0.0),
        "insulation_resistance_mohm": max(add_noise(state.insulation_resistance_mohm, 0.02), 0.0),
        "partial_discharge": max(add_noise(state.partial_discharge, 0.05), 0.0),
        "flux_estimate": max(add_noise(state.flux_estimate, 0.01), 0.0),
        "current_harmonics": max(add_noise(state.current_harmonics, 0.02), 0.0),
    }


if __name__ == "__main__":
    s = MotorState(
        voltage_v=400.0,
        current_a=0.0,
        speed_rpm=1000.0,
        stator_temp_c=40.0,
        rotor_temp_c=38.0,
        magnet_temp_c=36.0,
        bearing_temp_c=35.0,
        coolant_in_temp_c=25.0,
        coolant_out_temp_c=25.0,
        coolant_flow_rate=1.0,
        coolant_pressure=2.5,
        bearing_health=90.0
    )
    print(simulate_sensors(s))