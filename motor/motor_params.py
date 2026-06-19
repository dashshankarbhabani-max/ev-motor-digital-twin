MOTOR = {
    "motor_type": "IPMSM",
    "vehicle_class": "Passenger EV",
    "voltage_nominal_v": 400,
    "voltage_min_v": 200,
    "voltage_max_v": 900,
    "power_nominal_kw": 150,
    "power_min_kw": 50,
    "power_max_kw": 400,
    "torque_nominal_nm": 300,
    "torque_min_nm": 0,
    "torque_max_nm": 800,
    "speed_max_rpm": 20000,
    "efficiency_min": 0.90,
    "efficiency_max": 0.97,
    "cooling_type": "Liquid cooled",
    "pole_pairs": 4,
    "stator_resistance_ohm": 0.389,
    "ld_h": 0.0027,
    "lq_h": 0.0096,
    "magnet_flux_wb": 0.11,
    "inertia_kgm2": 0.0036,
    "friction_coeff_nm_per_radps": 0.001,
    "ambient_temp_c": 25.0,
    "stator_temp_max_c": 180.0,
    "magnet_temp_critical_c": 150.0,
    "bearing_temp_max_c": 120.0
}

if __name__ == "__main__":
    for k, v in MOTOR.items():
        print(f"{k}: {v}")