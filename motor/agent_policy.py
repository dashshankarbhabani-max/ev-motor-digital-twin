AGENTIC_AI_OFF = "OFF"
AGENTIC_AI_ON = "ON"

AGENTIC_AI_OPTIONS = [AGENTIC_AI_OFF, AGENTIC_AI_ON]

AGENTIC_DECISION_RULES = [
    {
        "situation": "Early thermal rise",
        "condition": "Any motor temperature enters the watch band.",
        "agent_action": "Boost cooling and warn the driver to drive smoothly.",
    },
    {
        "situation": "High thermal load",
        "condition": "Stator, rotor, magnet, or bearing temperature is high.",
        "agent_action": "Boost cooling, reduce torque, and limit vehicle speed.",
    },
    {
        "situation": "Critical overheating risk",
        "condition": "Temperature reaches the critical protection band.",
        "agent_action": "Maximum cooling, heavy torque derating, speed limit, and limp mode.",
    },
    {
        "situation": "Cooling failure",
        "condition": "Coolant flow is weak or cooling-failure fault is detected.",
        "agent_action": "Request maximum cooling, reduce torque, and cap speed until cooling recovers.",
    },
    {
        "situation": "Bearing/vibration risk",
        "condition": "Bearing temperature is high or vibration is excessive.",
        "agent_action": "Reduce torque, limit speed, and activate limp mode to reduce mechanical stress.",
    },
    {
        "situation": "Magnet protection",
        "condition": "Rotor magnet temperature is high.",
        "agent_action": "Boost cooling, reduce torque, and limit speed to avoid magnet weakening.",
    },
    {
        "situation": "Electrical protection",
        "condition": "Insulation resistance is low or current harmonics are high.",
        "agent_action": "Reduce torque/current demand, limit speed, and warn for inspection.",
    },
    {
        "situation": "Bad pedal usage",
        "condition": "Accelerator and brake are pressed together.",
        "agent_action": "Block acceleration while braking.",
    },
    {
        "situation": "Harsh launch or hot acceleration",
        "condition": "High accelerator demand at low speed or while hot.",
        "agent_action": "Derate torque and boost cooling to prevent heat spikes.",
    },
    {
        "situation": "High failure probability",
        "condition": "Failure probability is high or health is degraded.",
        "agent_action": "Prioritize damage prevention with torque/speed limits and limp mode if needed.",
    },
]


def _action(action_type, severity, reason, value=None, situation=None):
    return {
        "type": action_type,
        "severity": severity,
        "situation": situation or "Motor protection",
        "reason": reason,
        "value": value,
    }


def _has_warning(driver_warnings, title):
    return any(warning.get("title") == title for warning in driver_warnings)


def _highest_temperature(state):
    return max(
        state.stator_temp_c,
        state.rotor_temp_c,
        state.magnet_temp_c,
        state.bearing_temp_c,
    )


def _thermal_stage(state):
    """Classify motor thermal condition for supervisory protection."""
    if (
        state.stator_temp_c >= 120
        or state.rotor_temp_c >= 115
        or state.magnet_temp_c >= 135
        or state.bearing_temp_c >= 95
    ):
        return "critical"
    if (
        state.stator_temp_c >= 100
        or state.rotor_temp_c >= 100
        or state.magnet_temp_c >= 120
        or state.bearing_temp_c >= 85
    ):
        return "hot"
    if (
        state.stator_temp_c >= 85
        or state.rotor_temp_c >= 85
        or state.magnet_temp_c >= 105
        or state.bearing_temp_c >= 75
    ):
        return "watch"
    return "normal"


def plan_guardian_actions(state, driver_warnings, agentic_ai_enabled):
    """Plan safe deterministic actions for Agentic AI ON/OFF control."""
    if not agentic_ai_enabled:
        return []

    actions = []
    thermal_stage = _thermal_stage(state)

    if thermal_stage == "watch":
        actions.extend(
            [
                _action(
                    "increase_cooling",
                    "warning",
                    "Temperature is rising, so coolant flow is increased early.",
                    1.7,
                    "Early thermal rise",
                ),
                _action(
                    "alert_driver",
                    "warning",
                    "Motor is warming up. Drive smoothly and avoid sudden acceleration.",
                    True,
                    "Early thermal rise",
                ),
            ]
        )

    if thermal_stage == "hot":
        actions.extend(
            [
                _action(
                    "increase_cooling",
                    "critical",
                    "Motor temperature is high, so cooling is boosted.",
                    2.4,
                    "High thermal load",
                ),
                _action(
                    "limit_torque_pct",
                    "critical",
                    "Torque is reduced to lower current and copper losses.",
                    60,
                    "High thermal load",
                ),
                _action(
                    "limit_speed_kmph",
                    "warning",
                    "Speed is limited while the motor cools.",
                    70,
                    "High thermal load",
                ),
            ]
        )

    if thermal_stage == "critical":
        actions.extend(
            [
                _action(
                    "increase_cooling",
                    "critical",
                    "Critical temperature detected, so cooling is set to maximum safe flow.",
                    3.0,
                    "Critical overheating risk",
                ),
                _action(
                    "limit_torque_pct",
                    "critical",
                    "Torque is heavily derated to prevent winding, magnet, or bearing damage.",
                    25,
                    "Critical overheating risk",
                ),
                _action(
                    "limit_speed_kmph",
                    "critical",
                    "Vehicle speed is limited to limp-home range.",
                    35,
                    "Critical overheating risk",
                ),
                _action(
                    "activate_limp_mode",
                    "critical",
                    "Limp mode is activated because the motor is at high damage risk.",
                    True,
                    "Critical overheating risk",
                ),
            ]
        )

    if state.coolant_flow_rate < 0.5 or state.fault_code == "M401_COOLING_FAILURE":
        actions.extend(
            [
                _action(
                    "increase_cooling",
                    "critical",
                    "Cooling flow is weak, so the guardian requests maximum coolant flow.",
                    3.0,
                    "Cooling failure",
                ),
                _action(
                    "limit_torque_pct",
                    "critical",
                    "Torque is reduced until the cooling system recovers.",
                    30,
                    "Cooling failure",
                ),
                _action(
                    "limit_speed_kmph",
                    "critical",
                    "Speed is limited because cooling cannot remove heat normally.",
                    40,
                    "Cooling failure",
                ),
            ]
        )

    if state.bearing_temp_c >= 90 or state.vibration_vel >= 4.5 or state.fault_code == "M301_BEARING_FAULT":
        actions.extend(
            [
                _action(
                    "limit_torque_pct",
                    "critical",
                    "Bearing heat or vibration suggests mechanical stress, so torque is reduced.",
                    35,
                    "Bearing/vibration risk",
                ),
                _action(
                    "limit_speed_kmph",
                    "critical",
                    "Speed is limited to reduce bearing load and vibration.",
                    45,
                    "Bearing/vibration risk",
                ),
                _action(
                    "activate_limp_mode",
                    "critical",
                    "Limp mode protects the bearing from further damage.",
                    True,
                    "Bearing/vibration risk",
                ),
            ]
        )

    if state.magnet_temp_c >= 125 or state.fault_code == "M201_PARTIAL_DEMAGNETIZATION":
        actions.extend(
            [
                _action(
                    "increase_cooling",
                    "critical",
                    "Rotor magnet temperature is high, so cooling is boosted.",
                    2.8,
                    "Magnet protection",
                ),
                _action(
                    "limit_torque_pct",
                    "critical",
                    "Torque is reduced to prevent permanent magnet weakening.",
                    40,
                    "Magnet protection",
                ),
                _action(
                    "limit_speed_kmph",
                    "warning",
                    "Speed is limited while magnet temperature recovers.",
                    60,
                    "Magnet protection",
                ),
            ]
        )

    if (
        state.insulation_resistance_mohm < 700
        or state.current_harmonics > 4
        or state.fault_code in {"M004_INSULATION_BREAKDOWN", "M005_CURRENT_IMBALANCE"}
    ):
        actions.extend(
            [
                _action(
                    "limit_torque_pct",
                    "critical",
                    "Electrical stress is high, so current demand is reduced through torque derating.",
                    35,
                    "Electrical protection",
                ),
                _action(
                    "limit_speed_kmph",
                    "warning",
                    "Speed is limited until electrical readings return to normal.",
                    55,
                    "Electrical protection",
                ),
                _action(
                    "alert_driver",
                    "critical",
                    "Electrical health risk detected. Stop soon and inspect wiring, inverter, and insulation.",
                    True,
                    "Electrical protection",
                ),
            ]
        )

    if state.failure_probability >= 70:
        actions.extend(
            [
                _action(
                    "limit_torque_pct",
                    "critical",
                    "Failure probability is high, so the guardian prioritizes damage prevention.",
                    30,
                    "High failure probability",
                ),
                _action(
                    "limit_speed_kmph",
                    "critical",
                    "Speed is limited because overall failure risk is high.",
                    40,
                    "High failure probability",
                ),
                _action(
                    "activate_limp_mode",
                    "critical",
                    "Limp mode is activated because failure probability is high.",
                    True,
                    "High failure probability",
                ),
            ]
        )
    elif state.failure_probability >= 35 or state.overall_health < 80:
        actions.extend(
            [
                _action(
                    "increase_cooling",
                    "warning",
                    "Health degradation is detected, so cooling is raised.",
                    2.0,
                    "Health degradation",
                ),
                _action(
                    "limit_torque_pct",
                    "warning",
                    "Torque is mildly reduced while the motor is degraded.",
                    65,
                    "Health degradation",
                ),
                _action(
                    "limit_speed_kmph",
                    "warning",
                    "Speed is capped until health improves.",
                    75,
                    "Health degradation",
                ),
            ]
        )

    if _has_warning(driver_warnings, "Accelerator and brake pressed together"):
        actions.append(
            _action(
                "block_acceleration_while_braking",
                "critical",
                "Acceleration is blocked while braking to avoid heat, stress, and wasted energy.",
                True,
                "Bad pedal usage",
            )
        )

    if _has_warning(driver_warnings, "Harsh launch detected"):
        actions.append(
            _action(
                "limit_torque_pct",
                "warning",
                "Launch torque is limited to reduce current spikes and heat generation.",
                60,
                "Harsh launch",
            )
        )

    if _has_warning(driver_warnings, "Heavy acceleration while motor is hot"):
        actions.extend(
            [
                _action(
                    "limit_torque_pct",
                    "critical",
                    "Hot-motor acceleration is derated to prevent overheating.",
                    35,
                    "Hot acceleration",
                ),
                _action(
                    "increase_cooling",
                    "critical",
                    "Cooling is boosted because high accelerator demand was applied while hot.",
                    3.0,
                    "Hot acceleration",
                ),
            ]
        )

    if _has_warning(driver_warnings, "Hard braking at speed"):
        actions.append(
            _action(
                "limit_brake_pct",
                "warning",
                "Brake command is smoothed to reduce driveline shock.",
                70,
                "Harsh braking",
            )
        )

    if _highest_temperature(state) < 70 and state.failure_probability < 10 and state.overall_health > 90:
        actions.append(
            _action(
                "alert_driver",
                "normal",
                "Motor state is healthy. Agentic AI is monitoring without intervention.",
                True,
                "Normal operation",
            )
        )

    return actions
