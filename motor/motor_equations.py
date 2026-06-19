import math

def clamp(x, lo, hi):
    return max(lo, min(hi, x))

def back_emf(speed_rpm, ke=0.6):
    omega = speed_rpm * 2 * math.pi / 60.0
    return ke * omega

def current_from_voltage(voltage_v, speed_rpm, resistance_ohm=2.5, ke=0.6):
    eb = back_emf(speed_rpm, ke)
    return max((voltage_v - eb) / resistance_ohm, 0.0)

def torque_from_current(current_a, kt=1.0):
    return kt * current_a

def speed_from_voltage(voltage_v, current_a, resistance_ohm=2.5, ke=0.6):
    eb = max(voltage_v - current_a * resistance_ohm, 0.0)
    omega = eb / ke if ke > 0 else 0.0
    return omega * 60.0 / (2 * math.pi)

def copper_loss(current_a, resistance_ohm=2.5):
    return current_a * current_a * resistance_ohm

def mechanical_power(torque_nm, speed_rpm):
    omega = speed_rpm * 2 * math.pi / 60.0
    return torque_nm * omega

def thermal_step(temp_c, loss_w, ambient_c=25.0, thermal_mass=5000.0, cooling_coeff=8.0, dt=1.0):
    heat_in = loss_w * dt / thermal_mass
    heat_out = cooling_coeff * max(temp_c - ambient_c, 0.0) * dt / thermal_mass
    return max(temp_c + heat_in - heat_out, ambient_c)

def vibration_level(speed_rpm, bearing_health=100.0, imbalance=1.0):
    health_factor = 1.0 - clamp(bearing_health / 100.0, 0.0, 1.0)
    return 0.02 + 0.0000015 * speed_rpm + 0.12 * health_factor + 0.01 * imbalance

def electrical_efficiency(voltage_v, current_a, speed_rpm, resistance_ohm=2.5, kt=1.0):
    torque = torque_from_current(current_a, kt)
    pin = voltage_v * current_a
    pout = mechanical_power(torque, speed_rpm)
    return 0.0 if pin <= 0 else clamp(pout / pin, 0.0, 1.0)