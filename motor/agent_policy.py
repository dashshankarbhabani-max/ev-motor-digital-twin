GUARDIAN_OFF = "Off"
GUARDIAN_MONITOR = "Monitor Mode"
GUARDIAN_ASSISTIVE = "Assistive Guardian Mode"
GUARDIAN_PROTECTIVE = "Protective Agent Mode"

GUARDIAN_MODES = [
    GUARDIAN_OFF,
    GUARDIAN_MONITOR,
    GUARDIAN_ASSISTIVE,
    GUARDIAN_PROTECTIVE,
]


def _action(action_type, severity, reason, value=None):
    return {
        "type": action_type,
        "severity": severity,
        "reason": reason,
        "value": value,
    }


def _max_temperature(state):
    return max(
        state.stator_temp_c,
        state.rotor_temp_c,
        state.magnet_temp_c,
        state.bearing_temp_c,
    )


def _thermal_risk_level(state):
    if (
        state.stator_temp_c >= 120
        or state.rotor_temp_c >= 115
        or state.magnet_temp_c >= 135
        or state.bearing_temp_c >= 95
    ):
        return "critical"
    if (
        state.stator_temp_c >= 95
        or state.rotor_temp_c >= 95
        or state.magnet_temp_c >= 115
        or state.bearing_temp_c >= 80
    ):
        return "hot"
    if _max_temperature(state) >= 80:
        return "warm"
    return "normal"


def _has_warning(driver_warnings, title):
    return any(warning.get("title") == title for warning in driver_warnings)


def plan_guardian_actions(state, driver_warnings, mode):
    """Plan actions for the deterministic Agentic EV Motor Guardian."""
    if mode == GUARDIAN_OFF:
        return []

    actions = []
    risk_level = _thermal_risk_level(state)
    critical_fault = state.fault_code != "NONE" or state.failure_probability >= 60

    if risk_level == "warm":
        actions.append(
            _action(
                "increase_cooling",
                "warning",
                "Motor temperature is rising above the preferred operating band.",
                1.6 if mode == GUARDIAN_ASSISTIVE else 1.8,
            )
        )
        if mode == GUARDIAN_PROTECTIVE:
            actions.append(
                _action(
                    "limit_torque_pct",
                    "warning",
                    "Protective mode is gently reducing torque to slow temperature rise.",
                    85,
                )
            )

    if risk_level == "hot":
        actions.extend(
            [
                _action(
                    "increase_cooling",
                    "critical",
                    "Motor temperature is high, so cooling is boosted.",
                    2.1 if mode == GUARDIAN_ASSISTIVE else 2.5,
                ),
                _action(
                    "limit_torque_pct",
                    "critical",
                    "Torque is reduced to prevent overheating.",
                    70 if mode == GUARDIAN_ASSISTIVE else 55,
                ),
                _action(
                    "limit_speed_kmph",
                    "warning",
                    "Speed is limited while the motor cools down.",
                    80 if mode == GUARDIAN_ASSISTIVE else 65,
                ),
            ]
        )

    if risk_level == "critical" or critical_fault:
        actions.extend(
            [
                _action(
                    "increase_cooling",
                    "critical",
                    "Critical risk detected, so cooling is set to maximum safe flow.",
                    2.7 if mode == GUARDIAN_ASSISTIVE else 3.0,
                ),
                _action(
                    "limit_torque_pct",
                    "critical",
                    "Critical risk detected, so motor torque is heavily derated.",
                    45 if mode == GUARDIAN_ASSISTIVE else 25,
                ),
                _action(
                    "limit_speed_kmph",
                    "critical",
                    "Vehicle speed is limited to protect the motor.",
                    55 if mode == GUARDIAN_ASSISTIVE else 35,
                ),
                _action(
                    "activate_limp_mode",
                    "critical",
                    "Limp mode is requested because the motor is at high damage risk.",
                    mode == GUARDIAN_PROTECTIVE,
                ),
            ]
        )

    if _has_warning(driver_warnings, "Accelerator and brake pressed together"):
        actions.append(
            _action(
                "block_acceleration_while_braking",
                "critical",
                "Acceleration is blocked while braking to avoid heat and wasted power.",
                True,
            )
        )

    if _has_warning(driver_warnings, "Harsh launch detected"):
        actions.append(
            _action(
                "limit_torque_pct",
                "warning",
                "Launch torque is limited to reduce current spikes.",
                82 if mode == GUARDIAN_ASSISTIVE else 62,
            )
        )

    if _has_warning(driver_warnings, "Heavy acceleration while motor is hot"):
        actions.extend(
            [
                _action(
                    "limit_torque_pct",
                    "critical",
                    "Hot motor acceleration is derated to prevent overheating.",
                    55 if mode == GUARDIAN_ASSISTIVE else 35,
                ),
                _action(
                    "increase_cooling",
                    "critical",
                    "Cooling is boosted because high accelerator demand was applied while hot.",
                    2.4 if mode == GUARDIAN_ASSISTIVE else 3.0,
                ),
            ]
        )

    if _has_warning(driver_warnings, "Hard braking at speed"):
        actions.append(
            _action(
                "limit_brake_pct",
                "warning",
                "Brake command is smoothed to reduce driveline shock.",
                78 if mode == GUARDIAN_ASSISTIVE else 65,
            )
        )

    if mode == GUARDIAN_MONITOR:
        for action in actions:
            action["monitor_only"] = True

    return actions
