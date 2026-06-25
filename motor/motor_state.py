from dataclasses import dataclass, field


@dataclass
class MotorState:
    # =========================
    # ELECTRICAL
    # =========================
    voltage_v: float = 0.0
    current_a: float = 0.0
    speed_rpm: float = 0.0
    torque_nm: float = 0.0

    power_kw: float = 0.0
    efficiency: float = 0.0
    back_emf_v: float = 0.0

    copper_loss_w: float = 0.0
    iron_loss_w: float = 0.0
    mechanical_loss_w: float = 0.0
    total_loss_w: float = 0.0

    # =========================
    # VEHICLE
    # =========================
    vehicle_speed_kmph: float = 0.0
    battery_soc: float = 100.0

    # =========================
    # THERMAL
    # =========================
    stator_temp_c: float = 25.0
    rotor_temp_c: float = 25.0
    magnet_temp_c: float = 25.0
    bearing_temp_c: float = 25.0

    coolant_in_temp_c: float = 25.0
    coolant_out_temp_c: float = 25.0
    coolant_flow_rate: float = 1.0

    # =========================
    # VIBRATION
    # =========================
    vibration_accel: float = 0.0
    vibration_vel: float = 0.0

    # =========================
    # ELECTRICAL HEALTH
    # =========================
    flux_estimate: float = 0.6
    current_harmonics: float = 0.0
    insulation_resistance_mohm: float = 1000.0
    partial_discharge: float = 0.0

    # =========================
    # HEALTH
    # =========================
    stator_health: float = 100.0
    rotor_health: float = 100.0
    magnet_health: float = 100.0
    bearing_health: float = 100.0
    cooling_health: float = 100.0
    shaft_health: float = 100.0
    overall_health: float = 100.0

    failure_probability: float = 0.0
    rul_hours: float = 200000.0

    # =========================
    # FAULTS
    # =========================
    fault_code: str = "NONE"
    fault_flags: dict = field(default_factory=dict)

    # =========================
    # AGENTIC GUARDIAN
    # =========================
    guardian_mode: str = "ON"
    guardian_explanation: str = "Agentic AI is ready."
    driver_warnings: list = field(default_factory=list)
    guardian_actions: list = field(default_factory=list)
    limp_mode_active: bool = False
    torque_limit_pct: float = 100.0
    speed_limit_kmph: float = 150.0
    cooling_boost_active: bool = False
    effective_accelerator_pct: float = 0.0
    effective_brake_pct: float = 0.0
    last_accelerator_pct: float = 0.0
    last_brake_pct: float = 0.0
    thermal_shutdown_active: bool = False
    thermal_shutdown_complete: bool = False
    thermal_shutdown_elapsed_s: float = 0.0
    thermal_shutdown_start_speed_kmph: float = 0.0
    thermal_shutdown_target_speed_kmph: float = 150.0
    thermal_shutdown_reminder: str = ""

    # =========================
    # INTERNAL STATES
    # =========================
    filtered_torque: float = 0.0
    initialized: bool = True
