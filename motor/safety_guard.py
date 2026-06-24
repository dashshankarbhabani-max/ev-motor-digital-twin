CONTROL_LIMITS = {
    "limit_torque_pct": (0.0, 100.0),
    "limit_brake_pct": (0.0, 100.0),
    "limit_speed_kmph": (20.0, 105.0),
    "increase_cooling": (1.0, 3.0),
}


def _clamp(value, low, high):
    return max(low, min(high, float(value)))


def validate_guardian_actions(actions):
    """Validate guardian actions before they can affect the simulation."""
    validated = []
    for action in actions:
        checked = dict(action)
        action_type = checked.get("type")
        checked["allowed"] = True

        if checked.get("monitor_only"):
            checked["allowed"] = False
            checked["blocked_reason"] = "Monitor Mode explains actions but does not control the motor."

        if action_type in CONTROL_LIMITS and checked.get("value") is not None:
            low, high = CONTROL_LIMITS[action_type]
            checked["value"] = _clamp(checked["value"], low, high)

        if action_type == "activate_limp_mode":
            checked["value"] = bool(checked.get("value"))
            if not checked["value"]:
                checked["allowed"] = False
                checked["blocked_reason"] = "Assistive mode can warn strongly but only Protective mode activates limp mode."

        if action_type == "block_acceleration_while_braking":
            checked["value"] = bool(checked.get("value"))

        validated.append(checked)

    return validated
