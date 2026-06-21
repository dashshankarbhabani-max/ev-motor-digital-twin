MOTOR = {

    # =====================================
    # SYSTEM INFORMATION
    # =====================================
    "motor_type": "IPMSM",
    "vehicle_class": "Passenger EV",
    "cooling_type": "Liquid Cooled",

    # =====================================
    # ELECTRICAL SYSTEM
    # =====================================
    "voltage_nominal_v": 400,
    "voltage_min_v": 250,
    "voltage_max_v": 450,

    # =====================================
    # POWER
    # =====================================
    "power_nominal_kw": 150,
    "power_max_kw": 180,

    # =====================================
    # TORQUE
    # =====================================
    "torque_nominal_nm": 250,
    "torque_max_nm": 350,
    "torque_min_nm": -150,

    # =====================================
    # SPEED LIMITS
    # =====================================
    # Around 110 km/h with your wheel radius
    "speed_max_rpm": 1000,

    # =====================================
    # EFFICIENCY
    # =====================================
    "efficiency_min": 0.90,
    "efficiency_max": 0.97,

    # =====================================
    # MOTOR PARAMETERS
    # =====================================
    "pole_pairs": 4,

    "stator_resistance_ohm": 0.02,

    "ld_h": 0.0027,
    "lq_h": 0.0096,
    "magnet_flux_wb": 0.11,

    # =====================================
    # MECHANICAL PARAMETERS
    # =====================================
    # Increased for slower acceleration
    "inertia_kgm2": 0.15,

    # Increased damping
    "friction_coeff_nm_per_radps": 0.02,

    # =====================================
    # THERMAL LIMITS
    # =====================================
    "ambient_temp_c": 25.0,
    "stator_temp_max_c": 180.0,
    "magnet_temp_critical_c": 150.0,
    "bearing_temp_max_c": 120.0,

    # =====================================
    # COOLING
    # =====================================
    "coolant_nominal_flow": 1.0,
    "coolant_max_flow": 2.5,

    # =====================================
    # HEALTH MODEL
    # =====================================
    "initial_health": 100.0,
    "initial_rul_hours": 200000.0
}


if __name__ == "__main__":
    print("\n========== MOTOR PARAMETERS ==========\n")

    for key, value in MOTOR.items():
        print(f"{key:30} : {value}")

    print("\n======================================")