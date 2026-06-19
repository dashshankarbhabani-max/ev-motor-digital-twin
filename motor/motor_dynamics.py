import math
from motor.motor_state import MotorState
from motor.motor_equations import (
    clamp,
    back_emf,
    current_from_voltage,
    torque_from_current,
    copper_loss,
    thermal_step,
    vibration_level,
    electrical_efficiency,
)


def update_health_from_state(state: MotorState):
    temp_avg = (
        state.stator_temp_c
        + state.rotor_temp_c
        + state.magnet_temp_c
        + state.bearing_temp_c
    ) / 4.0

    stator_health = clamp(
        100.0
        - max(state.stator_temp_c - 95.0, 0.0) * 0.10
        - max(state.current_harmonics - 5.0, 0.0) * 0.25,
        0.0,
        100.0,
    )

    rotor_health = clamp(
        100.0 - max(state.rotor_temp_c - 100.0, 0.0) * 0.08,
        0.0,
        100.0,
    )

    magnet_health = clamp(
        100.0 - max(state.magnet_temp_c - 120.0, 0.0) * 0.10,
        0.0,
        100.0,
    )

    bearing_health = clamp(
        100.0
        - max(state.bearing_temp_c - 85.0, 0.0) * 0.10
        - max(state.vibration_accel - 0.2, 0.0) * 8.0,
        0.0,
        100.0,
    )

    cooling_health = clamp(
        100.0
        - max(temp_avg - 90.0, 0.0) * 0.08
        - max(1.0 - state.coolant_flow_rate, 0.0) * 8.0,
        0.0,
        100.0,
    )

    shaft_health = clamp(
        100.0 - max(state.vibration_vel - 1.5, 0.0) * 1.2,
        0.0,
        100.0,
    )

    overall_health = (
        0.25 * stator_health
        + 0.15 * rotor_health
        + 0.15 * magnet_health
        + 0.20 * bearing_health
        + 0.15 * cooling_health
        + 0.10 * shaft_health
    )

    failure_probability = clamp((100.0 - overall_health) / 100.0, 0.0, 1.0)
    rul_hours = max(overall_health * 6.0, 0.0)

    state.stator_health = stator_health
    state.rotor_health = rotor_health
    state.magnet_health = magnet_health
    state.bearing_health = bearing_health
    state.cooling_health = cooling_health
    state.shaft_health = shaft_health
    state.overall_health = overall_health
    state.failure_probability = failure_probability
    state.rul_hours = rul_hours

    if bearing_health < 40:
        state.fault_code = "BEARING_FAULT"
    elif magnet_health < 40:
        state.fault_code = "MAGNET_FAULT"
    elif stator_health < 40:
        state.fault_code = "STATOR_FAULT"
    elif cooling_health < 40:
        state.fault_code = "COOLING_FAULT"
    else:
        state.fault_code = "NONE"


def update_motor_state(state: MotorState, load_fraction=0.5, dt=1.0, ambient_c=25.0):
    load_fraction = clamp(load_fraction, 0.0, 1.2)

    ke = 0.6
    kt = 1.0
    resistance = 2.5
    max_current = 220.0
    inertia = 22.0
    damping = 0.03

    speed = max(state.speed_rpm, 0.0)
    current_est = current_from_voltage(state.voltage_v, speed, resistance_ohm=resistance, ke=ke)
    target_current = clamp(current_est + load_fraction * 30.0, 0.0, max_current)

    if state.current_a > 0:
        current_a = 0.85 * state.current_a + 0.15 * target_current
    else:
        current_a = target_current

    torque_nm = torque_from_current(current_a, kt=kt)
    emf_v = back_emf(speed, ke=ke)

    load_torque = 25.0 + 120.0 * load_fraction
    accel = (torque_nm - load_torque - damping * speed) / inertia
    new_speed = max(speed + accel * dt, 0.0)
    state.speed_rpm = 0.95 * speed + 0.05 * new_speed

    state.current_a = current_a
    state.torque_nm = torque_nm
    state.back_emf_v = emf_v
    state.power_kw = (state.voltage_v * state.current_a) / 1000.0
    state.efficiency = electrical_efficiency(
        state.voltage_v,
        state.current_a,
        state.speed_rpm,
        resistance_ohm=resistance,
        kt=kt,
    )

    copper = copper_loss(state.current_a, resistance_ohm=resistance)
    mech_loss = max(
        state.torque_nm * state.speed_rpm * 2 * math.pi / 60.0 * (1.0 - state.efficiency),
        0.0,
    )

    state.stator_temp_c = thermal_step(
        state.stator_temp_c,
        copper * 0.12 + mech_loss * 0.03,
        ambient_c=ambient_c,
        cooling_coeff=35.0,
        thermal_mass=18000.0,
        dt=dt,
    )
    state.rotor_temp_c = thermal_step(
        state.rotor_temp_c,
        copper * 0.07 + mech_loss * 0.02,
        ambient_c=ambient_c,
        cooling_coeff=30.0,
        thermal_mass=20000.0,
        dt=dt,
    )
    state.magnet_temp_c = thermal_step(
        state.magnet_temp_c,
        copper * 0.04 + mech_loss * 0.015,
        ambient_c=ambient_c,
        cooling_coeff=26.0,
        thermal_mass=22000.0,
        dt=dt,
    )
    state.bearing_temp_c = thermal_step(
        state.bearing_temp_c,
        copper * 0.03 + mech_loss * 0.01,
        ambient_c=ambient_c,
        cooling_coeff=22.0,
        thermal_mass=24000.0,
        dt=dt,
    )

    state.coolant_out_temp_c = ambient_c + (state.stator_temp_c - ambient_c) * 0.04
    state.vibration_accel = vibration_level(state.speed_rpm, state.bearing_health, imbalance=1.0)
    state.vibration_vel = state.vibration_accel * 8.0

    temp_stress = max(state.stator_temp_c - 80.0, 0.0)
    load_stress = max(load_fraction - 0.7, 0.0)
    vib_stress = max(state.vibration_accel - 0.05, 0.0)

    state.insulation_resistance_mohm = max(
        state.insulation_resistance_mohm - (temp_stress * 0.03 + load_stress * 0.10) * dt,
        1.0,
    )

    state.partial_discharge = max(
        state.partial_discharge + (temp_stress * 0.0004 + load_stress * 0.002 + vib_stress * 0.01) * dt,
        0.0,
    )

    flux_drop = max(state.magnet_temp_c - 60.0, 0.0) * 0.00003
    state.flux_estimate = max(
        0.0,
        min(1.0, 0.92 - flux_drop - load_stress * 0.005),
    )

    state.current_harmonics = max(
        0.0,
        state.current_harmonics + max(state.current_a - 120.0, 0.0) * 0.0008 * dt,
    )

    update_health_from_state(state)
    return state


if __name__ == "__main__":
    s = MotorState(
        voltage_v=400.0,
        current_a=0.0,
        speed_rpm=1000.0,
        coolant_flow_rate=1.0,
        bearing_health=90.0,
    )
    for i in range(5):
        s = update_motor_state(s, load_fraction=0.6, dt=1.0)
        print(s)
        