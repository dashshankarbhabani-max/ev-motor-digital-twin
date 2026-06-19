from dataclasses import dataclass, field


@dataclass
class MotorState:
    voltage_v: float = 0.0
    current_a: float = 0.0
    speed_rpm: float = 0.0
    torque_nm: float = 0.0
    power_kw: float = 0.0
    efficiency: float = 0.0
    back_emf_v: float = 0.0

    stator_temp_c: float = 25.0
    rotor_temp_c: float = 25.0
    magnet_temp_c: float = 25.0
    bearing_temp_c: float = 25.0
    coolant_in_temp_c: float = 25.0
    coolant_out_temp_c: float = 25.0

    vibration_accel: float = 0.0
    vibration_vel: float = 0.0
    coolant_flow_rate: float = 1.0
    coolant_pressure: float = 1.0
    insulation_resistance_mohm: float = 1000.0
    partial_discharge: float = 0.0
    flux_estimate: float = 0.0
    current_harmonics: float = 0.0

    stator_health: float = 100.0
    rotor_health: float = 100.0
    magnet_health: float = 100.0
    bearing_health: float = 100.0
    cooling_health: float = 100.0
    shaft_health: float = 100.0
    overall_health: float = 100.0
    failure_probability: float = 0.0
    rul_hours: float = 0.0
    fault_code: str = "NONE"
    fault_flags: dict[str, bool] = field(default_factory=dict)


if __name__ == "__main__":
    state = MotorState()
    print(state)