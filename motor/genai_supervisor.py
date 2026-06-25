from motor.action_executor import execute_guardian_actions
from motor.agent_policy import (
    AGENTIC_AI_OFF,
    AGENTIC_AI_ON,
    AGENTIC_AI_OPTIONS,
    plan_guardian_actions,
)
from motor.driving_behavior import analyze_driver_inputs
from motor.safety_guard import validate_guardian_actions


def _severity_rank(action):
    rank = {"critical": 0, "warning": 1, "normal": 2}
    return rank.get(action.get("severity", "normal"), 2)


def _enabled(selection):
    return str(selection).upper() == AGENTIC_AI_ON


def _summarize(selection, warnings, actions, controls):
    if not _enabled(selection):
        if warnings:
            return "Agentic AI is OFF. Driving warnings are shown, but the system is not taking control."
        return "Agentic AI is OFF. Real-time simulation is running without automatic protection."

    allowed_actions = [action for action in actions if action.get("allowed", True)]
    if not warnings and not allowed_actions:
        return "Agentic AI is ON and monitoring normal behavior. No control action is needed."

    protective_actions = [
        action for action in allowed_actions if action.get("type") != "alert_driver"
    ]
    if protective_actions:
        strongest = sorted(protective_actions, key=_severity_rank)[0]
        return (
            f"Agentic AI took control for {strongest.get('situation', 'motor protection')}: "
            f"{strongest['reason']} Effective accelerator {controls['effective_accelerator_pct']:.0f}%, "
            f"brake {controls['effective_brake_pct']:.0f}%, "
            f"torque limit {controls['torque_limit_pct']:.0f}%, "
            f"speed limit {controls['speed_limit_kmph']:.0f} km/h."
        )

    if allowed_actions:
        strongest = sorted(allowed_actions, key=_severity_rank)[0]
        return f"Agentic AI is ON and monitoring: {strongest['reason']}"

    if warnings:
        return f"Agentic AI warning: {warnings[0]['message']}"

    return "Agentic AI is ON and monitoring."


def run_guardian_cycle(state, accelerator_pct, brake_pct, agentic_ai_selection, dt_s):
    """Run one real-time Agentic AI supervisor cycle."""
    selection = str(agentic_ai_selection).upper()
    if selection not in AGENTIC_AI_OPTIONS:
        selection = AGENTIC_AI_ON

    warnings = analyze_driver_inputs(state, accelerator_pct, brake_pct, dt_s)
    proposed_actions = plan_guardian_actions(state, warnings, _enabled(selection), dt_s)
    safe_actions = validate_guardian_actions(proposed_actions)
    controls = execute_guardian_actions(state, accelerator_pct, brake_pct, safe_actions)

    explanation = _summarize(selection, warnings, safe_actions, controls)
    state.guardian_mode = selection
    state.driver_warnings = warnings
    state.guardian_actions = safe_actions
    state.guardian_explanation = explanation

    return {
        "mode": selection,
        "warnings": warnings,
        "actions": safe_actions,
        "controls": controls,
        "explanation": explanation,
    }


def guardian_mode_help(selection):
    if _enabled(selection):
        return (
            "ON: Agentic AI observes the real-time motor state and can take safe control "
            "by reducing torque, limiting speed, boosting cooling, smoothing pedals, "
            "and activating limp mode when damage risk is high."
        )
    return (
        "OFF: The dashboard still warns about unsafe driving or motor risk, "
        "but Agentic AI will not control torque, speed, braking, or cooling."
    )
