from motor.action_executor import execute_guardian_actions
from motor.agent_policy import (
    GUARDIAN_ASSISTIVE,
    GUARDIAN_MODES,
    GUARDIAN_OFF,
    GUARDIAN_PROTECTIVE,
    plan_guardian_actions,
)
from motor.driving_behavior import analyze_driver_inputs
from motor.safety_guard import validate_guardian_actions


def _severity_rank(action):
    rank = {"critical": 0, "warning": 1, "normal": 2}
    return rank.get(action.get("severity", "normal"), 2)


def _summarize(mode, warnings, actions, controls):
    if mode == GUARDIAN_OFF:
        if warnings:
            return "Driving warnings detected, but Guardian Mode is OFF so no automatic correction was applied."
        return "Guardian Mode is OFF. The digital twin is running without automatic protection."

    allowed_actions = [action for action in actions if action.get("allowed", True)]
    advisory_actions = [action for action in actions if not action.get("allowed", True)]

    if not warnings and not allowed_actions and not advisory_actions:
        return "Guardian is observing normal motor behavior. No corrective action is needed."

    if allowed_actions:
        strongest = sorted(allowed_actions, key=_severity_rank)[0]
        return (
            f"{mode} applied protection: {strongest['reason']} "
            f"Effective accelerator {controls['effective_accelerator_pct']:.0f}%, "
            f"brake {controls['effective_brake_pct']:.0f}%, "
            f"torque limit {controls['torque_limit_pct']:.0f}%, "
            f"speed limit {controls['speed_limit_kmph']:.0f} km/h."
        )

    if advisory_actions:
        strongest = sorted(advisory_actions, key=_severity_rank)[0]
        return f"{mode} advisory: {strongest['reason']}"

    return f"{mode} warning: {warnings[0]['message']}"


def run_guardian_cycle(state, accelerator_pct, brake_pct, mode, dt_s):
    """Run one real-time Agentic EV Motor Guardian cycle."""
    if mode not in GUARDIAN_MODES:
        mode = GUARDIAN_ASSISTIVE

    warnings = analyze_driver_inputs(state, accelerator_pct, brake_pct, dt_s)
    proposed_actions = plan_guardian_actions(state, warnings, mode)
    safe_actions = validate_guardian_actions(proposed_actions)
    controls = execute_guardian_actions(state, accelerator_pct, brake_pct, safe_actions)

    explanation = _summarize(mode, warnings, safe_actions, controls)
    state.guardian_mode = mode
    state.driver_warnings = warnings
    state.guardian_actions = safe_actions
    state.guardian_explanation = explanation

    return {
        "mode": mode,
        "warnings": warnings,
        "actions": safe_actions,
        "controls": controls,
        "explanation": explanation,
    }


def guardian_mode_help(mode):
    if mode == GUARDIAN_OFF:
        return "Guardian is disabled. The dashboard still shows driver warnings, but no automatic protection is applied."
    if mode == GUARDIAN_PROTECTIVE:
        return "Protective Agent Mode can strongly derate torque, limit speed, boost cooling, and activate limp mode after safety validation."
    if mode == GUARDIAN_ASSISTIVE:
        return "Assistive Guardian Mode applies mild safe corrections such as torque derating, brake smoothing, speed limiting, and cooling boost."
    return "Monitor Mode explains risks and recommended actions without controlling the motor."
