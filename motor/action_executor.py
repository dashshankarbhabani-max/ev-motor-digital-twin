MAX_DRIVE_TORQUE_NM = 200.0
MAX_BRAKE_TORQUE_NM = 80.0
DEFAULT_SPEED_LIMIT_KMPH = 105.0
DEFAULT_COOLANT_FLOW = 1.0


def _allowed(actions):
    return [action for action in actions if action.get("allowed", True)]


def _min_action_value(actions, action_type, default):
    values = [
        float(action["value"])
        for action in _allowed(actions)
        if action.get("type") == action_type and action.get("value") is not None
    ]
    return min(values) if values else default


def _max_action_value(actions, action_type, default):
    values = [
        float(action["value"])
        for action in _allowed(actions)
        if action.get("type") == action_type and action.get("value") is not None
    ]
    return max(values) if values else default


def _has_allowed(actions, action_type):
    return any(action.get("type") == action_type for action in _allowed(actions))


def execute_guardian_actions(state, accelerator_pct, brake_pct, actions):
    """Apply validated guardian actions to the driver command."""
    effective_accelerator = float(accelerator_pct)
    effective_brake = float(brake_pct)

    if _has_allowed(actions, "block_acceleration_while_braking") and effective_brake > 10:
        effective_accelerator = 0.0

    torque_limit_pct = _min_action_value(actions, "limit_torque_pct", 100.0)
    brake_limit_pct = _min_action_value(actions, "limit_brake_pct", 100.0)
    speed_limit_kmph = _min_action_value(
        actions,
        "limit_speed_kmph",
        DEFAULT_SPEED_LIMIT_KMPH,
    )
    coolant_flow_target = _max_action_value(
        actions,
        "increase_cooling",
        DEFAULT_COOLANT_FLOW,
    )

    if effective_brake > brake_limit_pct:
        effective_brake = brake_limit_pct

    if state.vehicle_speed_kmph >= speed_limit_kmph and effective_accelerator > 0:
        effective_accelerator = 0.0

    target_torque_nm = (
        effective_accelerator
        / 100.0
        * MAX_DRIVE_TORQUE_NM
        * torque_limit_pct
        / 100.0
    )

    if effective_brake > 0:
        target_torque_nm = -MAX_BRAKE_TORQUE_NM * (effective_brake / 100.0)

    if state.vehicle_speed_kmph > speed_limit_kmph + 2:
        target_torque_nm = min(target_torque_nm, -35.0)

    limp_mode_active = _has_allowed(actions, "activate_limp_mode")
    if limp_mode_active:
        target_torque_nm = min(target_torque_nm, MAX_DRIVE_TORQUE_NM * 0.25)

    state.torque_limit_pct = torque_limit_pct
    state.speed_limit_kmph = speed_limit_kmph
    state.cooling_boost_active = coolant_flow_target > DEFAULT_COOLANT_FLOW
    state.limp_mode_active = limp_mode_active
    state.effective_accelerator_pct = effective_accelerator
    state.effective_brake_pct = effective_brake

    state.coolant_flow_rate += (coolant_flow_target - state.coolant_flow_rate) * 0.35

    return {
        "effective_accelerator_pct": effective_accelerator,
        "effective_brake_pct": effective_brake,
        "target_torque_nm": target_torque_nm,
        "torque_limit_pct": torque_limit_pct,
        "speed_limit_kmph": speed_limit_kmph,
        "coolant_flow_rate": state.coolant_flow_rate,
        "limp_mode_active": limp_mode_active,
    }
